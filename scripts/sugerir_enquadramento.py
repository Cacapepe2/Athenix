"""Sugestões de enquadramento por IA para as obrigações em "Verificar enquadramento" sem sugestão de regra.

Uso:
  python scripts/sugerir_enquadramento.py                         # só estima o custo; nenhuma chamada
  python scripts/sugerir_enquadramento.py --confirmo-custo-usd X  # chama, se X cobrir o custo máximo

Sem chamada paga sem confirmação: a execução só chama o provedor com ATHENIX_AI_MODE=live (modelo, chave,
preço com fonte e data e teto ATHENIX_RUN_BUDGET_USD, como em llm.modo) e com --confirmo-custo-usd
maior ou igual ao custo máximo estimado, que por sua vez tem de caber no teto. A soma do custo real
(pelo uso informado pelo provedor) para a execução se passar do teto.

Corpus: a RN 1.137/2025 processada por regras com o perfil ilustrativo (o mesmo da demo).
shortcut: só a demo; ler o banco do usuário quando houver mais normas processadas.
Grava athenix/data/sugestoes_enquadramento_ia.json. Nada é confirmado: a tela de impacto mostra as
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
# shortcut: palpites, calibrar com o uso real da 1ª chamada.
SAIDA_ESPERADA = 300
SAIDA_ESPERADA_RACIOCINIO = 1500


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
    # e o limite de saída inteiro. Esperado: ~3 bytes por token e SAIDA_ESPERADA por chamada.
    entrada = sum(len(json.dumps(p, ensure_ascii=False).encode()) + 2048 for p in payloads)
    entrada_esperada = sum(len(json.dumps(p, ensure_ascii=False).encode()) // 3 for p in payloads)
    saida_esperada = (SAIDA_ESPERADA_RACIOCINIO if raciocinio else SAIDA_ESPERADA) * len(payloads)
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


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirmo-custo-usd")
    parser.add_argument("--saida", default=str(enquadramento.SUGESTOES_IA))
    parser.add_argument("--limite", type=int, help="processa só as N primeiras (teste)")
    args = parser.parse_args()
    carregar_env()  # .env local; nunca impresso
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
