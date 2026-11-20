"""Sugestões de enquadramento por IA para as obrigações em "Verificar enquadramento" sem sugestão de regra.

Uso:
  python scripts/sugerir_enquadramento.py                         # só estima o custo; nenhuma chamada
  python scripts/sugerir_enquadramento.py --confirmo-custo-usd X  # chama, se X cobrir o custo máximo

Sem chamada paga sem confirmação: a execução só chama o provedor com ATHENIX_AI_MODE=live (modelo, chave,
preço com fonte e data e teto ATHENIX_RUN_BUDGET_USD, como em llm.modo) e com --confirmo-custo-usd
maior ou igual ao custo máximo estimado, que por sua vez tem de caber no teto. A soma do custo real
(pelo uso informado pelo provedor) para a execução se passar do teto.

Corpus: a RN 1.137/2025 processada por regras com o perfil ilustrativo (o mesmo da demo) ou, com
--arquivo, outra norma versionada (PDF ou HTML), só os DEVERES da distribuidora do plano. Com --arquivo
grava também o cache do plano (athenix/data/ia_cache_<norma>.json), só com a 1ª sugestão (a mais
provável) de cada obrigação. Grava athenix/data/sugestoes_enquadramento_ia.json. Nada é confirmado: a tela de impacto mostra as
sugestões com as duas citações e uma pessoa confirma ou rejeita.
"""

import argparse
import hashlib
import json
import sys
import tempfile
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient  # noqa: E402

from athenix import enquadramento, impacto, llm  # noqa: E402
from athenix.app import create_app  # noqa: E402
from athenix.config import Settings, carregar_env  # noqa: E402
from athenix.db import digest  # noqa: E402
from athenix.demo import USUARIO, preparar  # noqa: E402

# Saída esperada por chamada (até 3 justificativas curtas); com raciocínio, soma o pensamento.
# Calibrado em 17/11/2026 com 2 chamadas reais (gpt-5-mini, Azure v1, mesma obrigação): entrada de
# 5.843 tokens para ~24,4 KB de pedido (~4 bytes por token); saída de 302 tokens com raciocínio low
# e 1.393 com medium. shortcut: uma obrigação só; recalibrar com o uso da execução completa.
BYTES_POR_TOKEN = 4
SAIDA_ESPERADA = 300
SAIDA_ESPERADA_RACIOCINIO = {"minimal": 300, "low": 400, "medium": 1500, "high": 3000}


def pendentes(params, rows, regras):
    """Obrigações em "Verificar enquadramento" que nenhuma regra curada cobre."""
    demo = impacto.perfil_ilustrativo()
    perfil = impacto.perfil({k: demo[k] for k in ("segmento", "base", "data_referencia")})
    verificar = impacto.avaliar(params, rows, perfil)["verificar"]
    return [
        i["row"]
        for i in verificar
        if enquadramento.citacao_obrigacao(i["row"])
        and not enquadramento.sugestoes(params, i["row"], regras)
    ]


def estimar(settings, params, rows):
    raciocinio = enquadramento.raciocinio(settings)
    payloads = [enquadramento.payload_ia(settings.model, params, r, raciocinio) for r in rows]
    saida = sum(p["max_completion_tokens"] for p in payloads)
    # Máximo: mesma heurística conservadora de llm.estimate (bytes do pedido + margem por chamada)
    # e o limite de saída inteiro. Esperado: calibração acima (BYTES_POR_TOKEN, SAIDA_ESPERADA*).
    entrada = sum(len(json.dumps(p, ensure_ascii=False).encode()) + 2048 for p in payloads)
    entrada_esperada = sum(
        len(json.dumps(p, ensure_ascii=False).encode()) // BYTES_POR_TOKEN for p in payloads
    )
    saida_esperada = SAIDA_ESPERADA_RACIOCINIO.get(raciocinio, SAIDA_ESPERADA) * len(payloads)
    precos = llm.price_config(settings)
    centavos = Decimal("0.01")
    return {
        "chamadas": len(payloads),
        "modelo": settings.model or None,
        "azure": bool(settings.azure_endpoint),
        "raciocinio": raciocinio,
        "tokens_entrada_maximo": entrada,
        "tokens_saida_maximo": saida,
        "tokens_entrada_esperado": entrada_esperada,
        "tokens_saida_esperado": saida_esperada,
        "preco": precos,
        "custo_maximo_usd": str(llm.cost(precos, entrada, saida).quantize(centavos)) if precos else None,
        "custo_esperado_usd": str(llm.cost(precos, entrada_esperada, saida_esperada).quantize(centavos))
        if precos
        else None,
    }  # fmt: skip


def custo_real(precos, raw):
    uso = (raw or {}).get("usage") or {}
    return llm.cost(precos, uso.get("prompt_tokens", 0), uso.get("completion_tokens", 0))


def executar(settings, params, rows, confirmo, saida, call=llm.call_model):
    est = estimar(settings, params, rows)
    print(json.dumps(est, ensure_ascii=False, indent=1))
    modo = llm.modo(settings)
    if modo["efetivo"] != "live":
        print(f"Só estimativa: IA em {modo['efetivo']} ({modo['motivo']}). Nenhuma chamada feita.")
        return None
    try:
        teto, confirmado = Decimal(settings.run_budget_usd), Decimal(confirmo or "")
    except InvalidOperation:
        print("Sem --confirmo-custo-usd válido: nenhuma chamada feita.")
        return None
    maximo = Decimal(est["custo_maximo_usd"])
    if confirmado < maximo or maximo > teto:
        print(f"Custo máximo US$ {maximo}: confirmado US$ {confirmado}, teto US$ {teto}. Nenhuma chamada feita.")  # fmt: skip
        return None
    sugestoes, falhas, gasto = {}, [], Decimal(0)
    for row in rows:
        if gasto > teto:
            falhas.append({"chave": enquadramento.chave(row), "motivo": "teto de custo atingido"})
            continue
        payload = enquadramento.payload_ia(
            settings.model, params, row, enquadramento.raciocinio(settings)
        )
        record = call(settings, payload)
        gasto += custo_real(est["preco"], record.get("raw"))
        validas, erro = enquadramento.validar_ia(params, record)
        if erro:
            falhas.append({"chave": enquadramento.chave(row), "motivo": erro})
        sugestoes[enquadramento.chave(row)] = validas
    resultado = {
        "nota": "Sugestões de IA, não decisões. Cada uma só vale depois de confirmada por uma pessoa na tela de impacto.",
        "modelo": settings.model,
        "prompt_version": enquadramento.PROMPT_VERSION,
        "prompt_hash": digest(enquadramento.PROMPT.encode()),
        "parametros_sha256": hashlib.sha256(impacto.PARAMETROS.read_bytes()).hexdigest(),
        "preco": est["preco"],
        "gerado_em": date.today().isoformat(),
        "custo_usd": str(gasto.quantize(Decimal("0.0001"))),
        "chamadas": len(rows),
        "falhas": falhas,
        "sugestoes": sugestoes,
    }  # fmt: skip
    Path(saida).write_text(json.dumps(resultado, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")  # fmt: skip
    print(f"{len(rows)} chamadas, custo US$ {resultado['custo_usd']}, {len(falhas)} falhas. Gravado em {saida}.")  # fmt: skip
    return resultado


def alvo_da_norma(arquivo):
    """Deveres da distribuidora de uma norma (o mesmo corte do plano) que nenhuma regra curada enquadra."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import exportar_plano_demo as exp

    arquivo = Path(arquivo)
    rows, extraction, params = exp.processar(arquivo)
    resultado, _ = exp.avaliar(rows, params, 5e9, "2026-11-17")
    out, _, _ = exp.montar(
        5e9, "2026-11-17", processado=(rows, extraction, params), arquivo=arquivo
    )
    no_plano = {o["id"] for o in out["obrigacoes"]}
    regras = enquadramento.carregar_regras()
    return params, [
        i["row"]
        for i in resultado["verificar"]
        if enquadramento.chave(i["row"]) in no_plano
        and enquadramento.citacao_obrigacao(i["row"])
        and not enquadramento.sugestoes(params, i["row"], regras)
    ]


def chamar_com_tempo_longo(settings, payload, tempo=240):
    """Uma chamada (sem repetir): como llm.call_model, mas com tempo de espera longo (modelo de raciocínio
    medium passa de 45 s) e sem exceção: timeout vira "unknown_result" com o pior caso de custo, porque a
    chamada pode ter sido cobrada. Só roda em modo live (llm.modo)."""
    import httpx

    if llm.modo(settings)["efetivo"] != "live":
        raise RuntimeError("IA fora do modo live: nenhuma chamada de rede é feita.")
    url, headers = llm.target(settings)
    try:
        r = httpx.post(url, headers=headers, json=payload, timeout=tempo, follow_redirects=False)
    except httpx.TimeoutException:
        pior = {"usage": {"prompt_tokens": len(json.dumps(payload, ensure_ascii=False).encode()) // 3, "completion_tokens": payload["max_completion_tokens"]}}  # fmt: skip
        return {"status": "unknown_result", "motivo": "timeout", "raw": pior}
    if r.status_code != 200:
        return {"status": "provider_error", "http_status": r.status_code, "raw": None}
    try:
        raw = r.json()
    except ValueError:
        return {"status": "invalid_response", "raw": None}
    escolha = raw.get("choices", [{}])[0]
    ok = escolha.get("finish_reason") == "stop" and not escolha.get("message", {}).get("refusal")
    return {"status": "complete" if ok else "incomplete", "raw": raw}


def executar_arquivo(settings, params, rows, confirmo, saida, parcial):
    """Uma obrigação por chamada, com progresso gravado a cada chamada em `parcial` (retoma de onde
    parou sem repetir chamada já feita) e custo real somado; para antes de passar do teto."""
    est = estimar(settings, params, rows)
    print(json.dumps(est, ensure_ascii=False, indent=1), flush=True)
    modo = llm.modo(settings)
    if modo["efetivo"] != "live":
        print(f"Só estimativa: IA em {modo['efetivo']} ({modo['motivo']}). Nenhuma chamada feita.")
        return None
    try:
        teto, confirmado = Decimal(settings.run_budget_usd), Decimal(confirmo or "")
    except InvalidOperation:
        print("Sem --confirmo-custo-usd válido: nenhuma chamada feita.")
        return None
    maximo = Decimal(est["custo_maximo_usd"])
    if confirmado < maximo or maximo > teto:
        print(f"Custo máximo US$ {maximo}: confirmado US$ {confirmado}, teto US$ {teto}. Nenhuma chamada feita.")  # fmt: skip
        return None
    parcial = Path(
        parcial
    )  # reserva inicial de US$ 0,10 por chamadas de uma 1ª tentativa interrompida por timeout (custo não registrado)
    estado = json.loads(parcial.read_text(encoding="utf-8")) if parcial.exists() else {"sugestoes": {}, "falhas": {}, "gasto": "0.10"}  # fmt: skip
    gasto = Decimal(estado["gasto"])
    feitas = set(estado["sugestoes"]) | set(
        estado["falhas"]
    )  # falha pode ter sido cobrada: não repete
    for n, row in enumerate(rows, start=1):
        chave = enquadramento.chave(row)
        if chave in feitas:
            continue
        por_chamada = maximo / max(len(rows), 1)  # custo máximo estimado de UMA chamada
        if gasto + por_chamada > teto:
            print(
                f"Teto de US$ {teto} no limite (gasto US$ {gasto:.4f} + US$ {por_chamada:.4f} da próxima); parando."
            )
            break
        payload = enquadramento.payload_ia(settings.model, params, row, enquadramento.raciocinio(settings))  # fmt: skip
        record = chamar_com_tempo_longo(settings, payload)
        gasto += custo_real(est["preco"], record.get("raw"))
        validas, erro = enquadramento.validar_ia(params, record)
        if erro:
            estado["falhas"][chave] = erro
        else:
            estado["sugestoes"][chave] = validas
            estado["falhas"].pop(chave, None)
        estado["gasto"] = str(gasto)
        parcial.write_text(json.dumps(estado, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")  # fmt: skip
        print(f"{n}/{len(rows)} · {len(validas)} sugestão(ões) · gasto US$ {gasto:.4f}" + (f" · falha: {erro}" if erro else ""), flush=True)  # fmt: skip
    resultado = {
        "nota": "Sugestões de IA, não decisões.",
        "modelo": settings.model,
        "prompt_version": enquadramento.PROMPT_VERSION,
        "prompt_hash": digest(enquadramento.PROMPT.encode()),
        "parametros_sha256": hashlib.sha256(impacto.PARAMETROS.read_bytes()).hexdigest(),
        "preco": est["preco"],
        "gerado_em": date.today().isoformat(),
        "custo_usd": str(gasto.quantize(Decimal("0.0001"))),
        "chamadas": len(estado["sugestoes"]) + len(estado["falhas"]),
        "falhas": [{"chave": k, "motivo": v} for k, v in estado["falhas"].items()],
        "sugestoes": estado["sugestoes"],
    }
    Path(saida).write_text(json.dumps(resultado, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")  # fmt: skip
    print(f"{resultado['chamadas']} chamadas, custo US$ {resultado['custo_usd']}, {len(resultado['falhas'])} falhas. Gravado em {saida}.")  # fmt: skip
    return resultado


def cache_do_plano(resultado, params, arquivo):
    """Formato lido por plano.carregar_ia: só a 1ª sugestão (a mais provável) de cada obrigação."""
    validas = enquadramento.infracoes_validas(params)
    enquadramentos = {
        chave: {
            "dispositivo": lista[0]["dispositivo"],
            "grupo": validas[lista[0]["dispositivo"]]["grupo"],
            "justificativa": lista[0]["justificativa"],
            "duvida": "D1" if lista[0]["dispositivo"] == "Art. 11, XXIII" else None,
        }
        for chave, lista in resultado["sugestoes"].items()
        if lista
    }
    return {
        "aviso": "Sugestões da IA. Aguardam revisão humana. No modo só identificados no texto não entram no cálculo; no cenário preliminar entram no valor do tema, sempre marcadas como sugeridas.",
        "modelo": resultado["modelo"],
        "reasoning": enquadramento.raciocinio(Settings()),
        "gerado_por": f"scripts/sugerir_enquadramento.py --arquivo {Path(arquivo).as_posix()}",
        "gerado_em": resultado["gerado_em"],
        "preco_usd_por_milhao": resultado["preco"],
        "nota_preco": "Preço informado pelo fundador (tabela de preço do Azure para gpt-5-mini); a confirmar no portal.",
        "custo_usd": resultado["custo_usd"],
        "criterio_titulos": "Sem títulos de IA para esta norma.",
        "criterio_enquadramentos": "Só a primeira sugestão (a mais provável) de cada obrigação, com dispositivo da lista e justificativa não vazia; nada é confirmado.",
        "titulos": {},
        "enquadramentos": enquadramentos,
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirmo-custo-usd")
    parser.add_argument("--saida", default=str(enquadramento.SUGESTOES_IA))
    parser.add_argument("--limite", type=int, help="processa só as N primeiras (teste)")
    parser.add_argument("--arquivo", help="outra norma versionada (PDF ou HTML) em vez da RN 1.137")
    args = parser.parse_args()
    carregar_env()  # .env local; nunca impresso
    if args.arquivo:
        params, alvo = alvo_da_norma(args.arquivo)
        alvo = alvo[: args.limite]
        saida = Path(args.saida)
        if args.saida == str(
            enquadramento.SUGESTOES_IA
        ):  # não sobrescreve as sugestões da RN 1.137
            saida = ROOT / "athenix" / "data" / f"sugestoes_{Path(args.arquivo).stem}.json"
        parcial = ROOT / ".local" / f"sugestoes_{Path(args.arquivo).stem}.parcial.json"
        parcial.parent.mkdir(exist_ok=True)
        resultado = executar_arquivo(
            Settings(), params, alvo, args.confirmo_custo_usd, saida, parcial
        )
        if resultado:
            cache = ROOT / "athenix" / "data" / f"ia_cache_{Path(args.arquivo).stem}.json"
            cache.write_text(
                json.dumps(
                    cache_do_plano(resultado, params, args.arquivo), ensure_ascii=False, indent=1
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            print(f"Cache do plano gravado em {cache}.")
        return
    params = impacto.carregar()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        demo = Settings(model="", api_key="", ai_mode="off")  # a norma é processada só por regras
        senha = preparar(demo, banco=Path(tmp) / "demo.db")
        with TestClient(create_app(demo)) as client:
            client.post("/api/login", json={"username": USUARIO, "password": senha})
            rows = client.get("/api/obligations").json()["items"]
    alvo = pendentes(params, rows, enquadramento.carregar_regras())[: args.limite]
    executar(Settings(), params, alvo, args.confirmo_custo_usd, args.saida)


if __name__ == "__main__":
    main()
