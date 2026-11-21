"""Tipo por IA só das obrigações que ficaram em "A definir" (a regra não achou tipo e a IA ainda não opinou).

Hoje: REN 1.174 (o cache da RN 1.137 já foi gerado). Grava o resultado no mesmo cache de tipos
(athenix/data/tipos_ia_cache.json, chave = id estável da obrigação) e a área sai marcada "área sugerida (IA)".

CHAMADA PAGA. Só roda com --executar e `--confirmo-custo-usd` maior ou igual ao pior caso estimado, com o gate
de llm.modo (live, preço com fonte e data, teto ATHENIX_RUN_BUDGET_USD). Preço real configurado (não o teto
conservador do script antigo). Sem --executar, só estima.

Uso: python scripts/classificar_tipos_a_definir.py                       # só estima
     python scripts/classificar_tipos_a_definir.py --executar --confirmo-custo-usd 0.20
"""

import argparse
import json
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from athenix import llm, tipos_ia  # noqa: E402
from athenix.config import Settings, carregar_env  # noqa: E402
from athenix.normalizacao import espacos  # noqa: E402

PLANOS = [ROOT / "landing/src/content/plano-ren1174.json"]


def itens_a_definir():
    cache = tipos_ia.carregar_cache()
    itens = []
    for caminho in PLANOS:
        plano = json.loads(caminho.read_text(encoding="utf-8"))
        for o in plano["obrigacoes"]:
            if o.get("area") == "A definir" and o["id"] not in cache:
                itens.append({"id": o["id"], "texto": espacos(o["trecho"] or o["titulo_completo"])})
    return itens


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--executar", action="store_true")
    ap.add_argument("--confirmo-custo-usd")
    a = ap.parse_args()
    carregar_env()
    settings = Settings()
    itens = itens_a_definir()
    lotes = tipos_ia.montar_lotes(itens, tamanho=12)
    precos = llm.price_config(settings)
    if not precos:
        raise SystemExit("Sem preço configurado com fonte e data: não executo.")
    preco = {"entrada": float(precos["input"]), "saida": float(precos["output"])}
    pior = sum(
        (tipos_ia.estimar_tokens(lt["sistema"] + lt["usuario"]) * preco["entrada"]
         + tipos_ia.LIMITE_SAIDA_RACIOCINIO * preco["saida"]) / 1e6
        for lt in lotes
    )  # fmt: skip
    print(
        json.dumps(
            {
                "obrigacoes": len(itens),
                "chamadas": len(lotes),
                "preco": precos,
                "custo_maximo_usd": round(pior, 4),
            },
            ensure_ascii=False,
            indent=1,
        )
    )
    if not a.executar:
        print("Só estimativa (sem --executar): nenhuma chamada feita.")
        return
    modo = llm.modo(settings)
    if modo["efetivo"] != "live":
        print(f"Só estimativa: IA em {modo['efetivo']} ({modo['motivo']}). Nenhuma chamada feita.")
        return
    try:
        teto, confirmado = Decimal(settings.run_budget_usd), Decimal(a.confirmo_custo_usd or "")
    except InvalidOperation:
        print("Sem --confirmo-custo-usd válido: nenhuma chamada feita.")
        return
    if confirmado < Decimal(str(round(pior, 4))) or Decimal(str(pior)) > teto:
        print(
            f"Pior caso US$ {pior:.4f}: confirmado US$ {confirmado}, teto US$ {teto}. Nenhuma chamada feita."
        )
        return
    r = tipos_ia.rodar(lotes, settings, preco, float(teto))
    bruto = json.loads(tipos_ia.CACHE.read_text(encoding="utf-8"))
    bruto["tipos"].update(r["tipos"])
    bruto["a_definir"] = {
        "gerado_em": date.today().isoformat(),
        "obrigacoes": len(itens),
        "gravados": len(r["tipos"]),
        "uso": r["uso"],
        "falhas": r["falhas"],
        "nota": "Tipos sugeridos pela IA só para quem ficou em A definir; aguardam revisão humana.",
    }
    tipos_ia.CACHE.write_text(
        json.dumps(bruto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {"uso": r["uso"], "falhas": r["falhas"], "tipos_gravados": len(r["tipos"])},
            ensure_ascii=False,
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
