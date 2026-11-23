"""Área sugerida (IA) para os deveres em "A definir", com trecho literal conferido (athenix/areas_ia.py).

CHAMADA PAGA. Só roda com --executar e `--confirmo-custo-usd` maior ou igual ao custo máximo estimado, com o
gate de llm.modo (live, preço com fonte e data, teto ATHENIX_RUN_BUDGET_USD). Sem --executar, só estima.
Grava athenix/data/areas_ia_cache.json; o export (python scripts/exportar_plano_demo.py) aplica e confere de novo.

Uso: python scripts/sugerir_areas_ia.py                                    # só estima
     python scripts/sugerir_areas_ia.py --executar --confirmo-custo-usd 0.10
"""

import argparse
import json
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import recomendar_acoes as ra  # noqa: E402
import sugerir_enquadramento as se  # noqa: E402

from athenix import areas, areas_ia, llm  # noqa: E402
from athenix.config import Settings, carregar_env  # noqa: E402
from athenix.db import digest  # noqa: E402
from athenix.normalizacao import espacos  # noqa: E402

TAMANHO_DO_LOTE = 12
SAIDA_MAXIMA = 5000  # por chamada: JSON + raciocínio


def bloco(o):
    contexto = f' contexto="{espacos(o["contexto"])}"' if o.get("contexto") else ""
    return f'<obrigacao id="{o["id"]}" dispositivo="{o["dispositivo"] or ""}"{contexto}>{espacos(o["trecho"])}</obrigacao>'  # fmt: skip


def itens_a_definir(cache):
    cfg = areas.carregar()
    itens = []
    for caminho in ra.NORMAS.values():
        plano = json.loads(caminho.read_text(encoding="utf-8"))
        for o in plano["obrigacoes"]:
            if o.get("area") == cfg["padrao"] and o["id"] not in cache["areas"] and o["id"] not in cache["reprovados"]:  # fmt: skip
                itens.append(o)
    return itens


def montar_lotes(itens, cfg):
    lista = "Áreas: " + "; ".join(areas_ia.opcoes(cfg)) + "."
    return [
        {
            "itens": itens[i : i + TAMANHO_DO_LOTE],
            "usuario": lista + "\n" + "\n".join(bloco(o) for o in itens[i : i + TAMANHO_DO_LOTE]),
        }  # fmt: skip
        for i in range(0, len(itens), TAMANHO_DO_LOTE)
    ]


def payload(settings, lote, cfg):
    p = {
        "model": settings.model,
        "messages": [{"role": "system", "content": areas_ia.INSTRUCOES}, {"role": "user", "content": lote["usuario"]}],
        "response_format": {"type": "json_schema", "json_schema": {"name": "areas", "strict": True, "schema": areas_ia.schema(cfg)}},
        "max_completion_tokens": SAIDA_MAXIMA,
    }  # fmt: skip
    if settings.reasoning_effort:
        p["reasoning_effort"] = settings.reasoning_effort
    else:
        p["store"] = False
    return p


def estimar(settings, lotes, cfg):
    precos = llm.price_config(settings)
    entrada = sum(ra.estimar_tokens(areas_ia.INSTRUCOES + lt["usuario"] + json.dumps(areas_ia.schema(cfg))) + 300 for lt in lotes)  # fmt: skip
    saida_max = len(lotes) * SAIDA_MAXIMA
    saida_esp = len(lotes) * 1500
    q = Decimal("0.0001")
    return {
        "obrigacoes": sum(len(lt["itens"]) for lt in lotes),
        "chamadas": len(lotes),
        "modelo": settings.model or None,
        "raciocinio": settings.reasoning_effort,
        "tokens_entrada": entrada,
        "tokens_saida_maximo": saida_max,
        "preco": precos,
        "custo_esperado_usd": str(llm.cost(precos, entrada, saida_esp).quantize(q))
        if precos
        else None,
        "custo_maximo_usd": str(llm.cost(precos, entrada, saida_max).quantize(q))
        if precos
        else None,
    }


def gravar(cache, settings, est, gasto, falhas):
    areas_ia.CACHE.write_text(
        json.dumps(
            {
                "aviso": "Áreas sugeridas pela IA (área sugerida (IA)) para deveres em A definir; aguardam revisão humana.",
                "modelo": settings.model,
                "versao_do_prompt": areas_ia.VERSAO_PROMPT,
                "prompt_hash": digest(
                    (areas_ia.INSTRUCOES + json.dumps(areas_ia.schema())).encode()
                ),
                "gerado_em": date.today().isoformat(),
                "preco_usd_por_milhao": est["preco"],
                "custo_total_da_execucao_usd": str(gasto.quantize(Decimal("0.0001"))),
                "falhas": falhas,
                "areas": cache["areas"],
                "reprovados": cache["reprovados"],
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def executar(settings, lotes, confirmo, est, cache, cfg):
    modo = llm.modo(settings)
    if modo["efetivo"] != "live":
        print(f"Só estimativa: IA em {modo['efetivo']} ({modo['motivo']}). Nenhuma chamada feita.")
        return
    try:
        teto, confirmado = Decimal(settings.run_budget_usd), Decimal(confirmo or "")
    except InvalidOperation:
        print("Sem --confirmo-custo-usd válido: nenhuma chamada feita.")
        return
    maximo = Decimal(est["custo_maximo_usd"])
    if confirmado < maximo or maximo > teto:
        print(f"Custo máximo US$ {maximo}: confirmado US$ {confirmado}, teto US$ {teto}. Nenhuma chamada feita.")  # fmt: skip
        return
    gasto, falhas = Decimal(0), []
    por_chamada = maximo / max(len(lotes), 1)
    for n, lote in enumerate(lotes, start=1):
        if gasto + por_chamada > teto:
            falhas.append({"lote": n, "motivo": "teto no limite"})
            break
        record = se.chamar_com_tempo_longo(settings, payload(settings, lote, cfg))
        gasto += se.custo_real(est["preco"], record.get("raw"))
        try:
            if record.get("status") != "complete":
                raise ValueError(record.get("status"))
            itens = json.loads(record["raw"]["choices"][0]["message"]["content"])["itens"]
        except (ValueError, KeyError, TypeError, IndexError) as e:
            falhas.append({"lote": n, "motivo": str(e)})
            print(f"lote {n}/{len(lotes)}: falha · gasto US$ {gasto:.4f}", flush=True)
            continue
        por_id = {x.get("id"): x for x in itens if isinstance(x, dict)}
        for o in lote["itens"]:
            x = por_id.get(o["id"]) or {}
            area, trecho, motivo = areas_ia.validar(
                x.get("area"), x.get("trecho"), o["trecho"], cfg
            )
            if area:
                cache["areas"][o["id"]] = {"area": area, "trecho": trecho}
            else:
                cache["reprovados"][o["id"]] = (
                    motivo if x else "a IA não respondeu sobre este dever"
                )
        print(f"lote {n}/{len(lotes)} · gasto US$ {gasto:.4f}", flush=True)
    gravar(cache, settings, est, gasto, falhas)
    print(f"{len(cache['areas'])} áreas sugeridas, {len(cache['reprovados'])} reprovadas; custo US$ {gasto:.4f}, {len(falhas)} falhas.")  # fmt: skip


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--executar", action="store_true")
    ap.add_argument("--confirmo-custo-usd")
    a = ap.parse_args()
    carregar_env()
    settings = Settings()
    cfg = areas.carregar()
    cache = areas_ia.carregar()
    lotes = montar_lotes(itens_a_definir(cache), cfg)
    est = estimar(settings, lotes, cfg)
    print(json.dumps(est, ensure_ascii=False, indent=1))
    if not a.executar:
        print("Só estimativa (sem --executar): nenhuma chamada feita.")
        return
    executar(settings, lotes, a.confirmo_custo_usd, est, cache, cfg)


if __name__ == "__main__":
    main()
