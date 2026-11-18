"""Estimativa de custo (sem chamar a IA) de classificar as obrigações da RN 1.137 e comparação com as
regras a partir do cache local (athenix/data/tipos_ia_cache.json, que só existe depois de uma execução
autorizada). Uso: python scripts/estimar_tipos_ia.py [--md docs/tipos_obrigacao_ia.md]
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import relatorio_tipos as rt  # noqa: E402

from athenix import enquadramento, tipos_ia  # noqa: E402
from athenix.config import Settings  # noqa: E402

PRECOS_ILUSTRATIVOS = [
    (0.15, 0.60),
    (1.0, 4.0),
    (2.5, 10.0),
]  # US$ por 1 milhão de tokens (entrada, saída)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--md")
    a = ap.parse_args()
    rows, extraction = rt.processar()
    itens = rt.analisar(rows, extraction)
    chave = {r["id"]: enquadramento.chave(r) for r in rows}
    for i in itens:
        i["chave"] = chave[i["id"]]
    entrada = [{"id": i["id"], "texto": i["texto"]} for i in itens]
    est = {t: tipos_ia.estimar(entrada, Settings(), tamanho=t) for t in (12, 1)}
    cache = tipos_ia.carregar_cache()
    regras = {chave[i["id"]]: i["tipo"] for i in itens}
    comp = tipos_ia.comparar(regras, cache) if cache else None
    uso = json.loads(tipos_ia.CACHE.read_text(encoding="utf-8")) | {} if cache else None
    uso = {"gerado_em": uso["gerado_em"], "uso": uso["uso"]} if uso else None
    saida = {
        "estimativa": est,
        "comparacao": tipos_ia.resumo_comparacao(comp) if comp else "sem respostas de IA em cache",
    }
    print(json.dumps(saida, ensure_ascii=False, indent=1, default=str))
    if a.md:
        Path(a.md).write_text(markdown(est, comp, itens, uso), encoding="utf-8", newline="\n")


def markdown(est, comp, itens, uso=None):
    e12, e1 = est[12], est[1]
    L = [
        "# Classificação de tipos por IA: estimativa de custo e comparação com as regras",
        "",
        (
            f"**Uma execução autorizada foi feita em {uso['gerado_em']}**: {uso['uso']['chamadas']} chamadas em lotes de 12, "
            f"{uso['uso']['tokens_entrada']:,} tokens de entrada e {uso['uso']['tokens_saida']:,} de saída; custo ao PREÇO TETO "
            f"(US$ 2,50 / US$ 10 por milhão, autorizado pelo fundador, NÃO é o preço real do deployment): US$ {uso['uso']['custo_ao_preco_teto_usd']:.2f}, "
            f"dentro do orçamento de US$ {uso['uso']['orcamento_usd']:.0f}. Resposta da IA é interpretação"
        )
        if uso
        else '**Nenhuma chamada de IA foi feita.** Este arquivo traz a estimativa para o seu "ok". Resposta da IA é interpretação',
        f'("{tipos_ia.ROTULO}"), validada contra a lista de tipos.',
        "",
        "## Estimativa (168 obrigações da RN 1.137)",
        "| Plano | Chamadas | Tokens de entrada | Saída (JSON) | Saída (teto com raciocínio) |",
        "|---|---|---|---|---|",
        f"| Lotes de 12 | {e12['chamadas']} | {e12['tokens_entrada']:,} | {e12['tokens_saida_json']:,} | {e12['tokens_saida_teto_com_raciocinio']:,} |",
        f"| Uma por obrigação | {e1['chamadas']} | {e1['tokens_entrada']:,} | {e1['tokens_saida_json']:,} | {e1['tokens_saida_teto_com_raciocinio']:,} |",
        "",
        "Método: 1 token ≈ 3 caracteres (heurística do projeto, `athenix/llm.py`); o teto de saída é de 3.000",
        "tokens por chamada (modelo de raciocínio gasta tokens pensando). O preço real do deployment não está",
        "configurado; a execução usou o preço TETO acima. Fórmula: `custo = (entrada × preço_entrada + saída × preço_saída) / 1.000.000`.",
        "",
        "Exemplos ILUSTRATIVOS de preço (não são os do seu deployment), plano de lotes de 12:",
        "| Preço (entrada / saída por 1 M) | Custo mínimo (saída JSON) | Custo máximo (teto de saída) |",
        "|---|---|---|",
    ]
    for pe, ps in PRECOS_ILUSTRATIVOS:
        mn = (e12["tokens_entrada"] * pe + e12["tokens_saida_json"] * ps) / 1e6
        mx = (e12["tokens_entrada"] * pe + e12["tokens_saida_teto_com_raciocinio"] * ps) / 1e6
        L.append(f"| US$ {pe} / US$ {ps} | US$ {mn:.2f} | US$ {mx:.2f} |")
    L += [
        "",
        "Com lotes de 12 a entrada é menor (o prompt de tipos se repete 14 vezes, não 168).",
        "",
    ]
    if comp:
        r = tipos_ia.resumo_comparacao(comp)
        L += [
            "## Comparação regra × IA",
            f"- {r['por_situacao']}; **tipo a revisar: {r['tipo_a_revisar']}**.",
            "",
        ]
        por_id = {i["chave"]: i for i in itens}
        for x in comp:
            if x["tipo"] == tipos_ia.A_REVISAR:
                i = por_id[x["id"]]
                L.append(
                    f'- **{i["dispositivo"]}**: regra = {x["regra"]}; IA = {x["ia"]}. "{i["texto"][:200]}"'
                )
    else:
        L += ["## Comparação regra × IA", "Ainda sem respostas de IA em cache.", ""]
    return chr(10).join(L) + chr(10)


if __name__ == "__main__":
    main()
