"""Classifica por IA o tipo de cada obrigação da RN 1.137 (lotes de 12) e grava o cache local
athenix/data/tipos_ia_cache.json, que a demo usa para a concordância regra x IA.

CHAMADA PAGA. Só roda com --executar e com o teto de custo em ATHENIX_RUN_BUDGET_USD. O preço usado é
um TETO conservador autorizado pelo fundador (US$ 2,50 por milhão de entrada e US$ 10 por milhão de
saída), NÃO o preço real do deployment. O script nunca passa do orçamento: confere o pior caso de cada
chamada antes de fazê-la. Não guarda a resposta bruta; só o tipo validado por obrigação.
Uso: python scripts/classificar_tipos_ia.py [--executar]
"""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import relatorio_tipos as rt  # noqa: E402

from athenix import enquadramento, tipos_ia  # noqa: E402
from athenix.config import Settings, carregar_env  # noqa: E402

PRECO_TETO = {"entrada": 2.5, "saida": 10.0}
NOTA_PRECO = (
    "Teto conservador autorizado pelo fundador em 18/11/2026; não é o preço real do deployment."
)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--executar", action="store_true", help="faz as chamadas pagas")
    a = ap.parse_args()
    carregar_env()  # .env local; nunca impresso
    settings = Settings()
    rows, extraction = rt.processar()
    por_id = {r["id"]: r for r in rows}
    itens = []
    for i in rt.analisar(rows, extraction):
        itens.append({"id": enquadramento.chave(por_id[i["id"]]), "texto": i["texto"]})
    ids = [i["id"] for i in itens]
    assert len(set(ids)) == len(ids), "chave de obrigação repetida"
    lotes = tipos_ia.montar_lotes(itens, tamanho=12)
    orcamento = float(os.getenv("ATHENIX_RUN_BUDGET_USD", "0"))
    pior = sum(
        (tipos_ia.estimar_tokens(lt["sistema"] + lt["usuario"]) * PRECO_TETO["entrada"]
         + tipos_ia.LIMITE_SAIDA_RACIOCINIO * PRECO_TETO["saida"]) / 1e6
        for lt in lotes
    )  # fmt: skip
    print(
        f"{len(itens)} obrigações, {len(lotes)} chamadas; pior caso ao preço teto: US$ {pior:.2f}; orçamento: US$ {orcamento}"
    )
    if not a.executar:
        print("Simulação (sem --executar): nenhuma chamada feita.")
        return
    faltam = [
        n
        for n, v in (("ATHENIX_MODEL", settings.model), ("ATHENIX_API_KEY", settings.api_key))
        if not v
    ]
    if faltam or orcamento <= 0 or pior > orcamento:
        raise SystemExit(
            f"Não executo: faltam {faltam}; orçamento {orcamento}; pior caso {pior:.2f}"
        )
    r = tipos_ia.rodar(lotes, settings, PRECO_TETO, orcamento)
    cache = {
        "aviso": "Interpretação da IA · aguarda revisão humana. Só o tipo validado; sem resposta bruta.",
        "modelo": settings.model,
        "gerado_em": date.today().isoformat(),
        "prompt_versao": tipos_ia.VERSAO_PROMPT,
        "preco_teto_usd_por_milhao": PRECO_TETO,
        "nota_preco": NOTA_PRECO,
        "uso": r["uso"],
        "falhas": r["falhas"],
        "tipos": r["tipos"],
    }
    tipos_ia.CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")  # fmt: skip
    print(json.dumps({"uso": r["uso"], "falhas": r["falhas"], "tipos_gravados": len(r["tipos"])}, ensure_ascii=False, indent=1))  # fmt: skip


if __name__ == "__main__":
    main()
