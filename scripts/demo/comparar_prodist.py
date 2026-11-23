"""Relatório reproduzível das fontes v2/v3 e das divergências em relação à RN 1.137."""

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from athenix.comparacao_prodist import montar  # noqa: E402
from athenix.config import Settings  # noqa: E402
from athenix.structure import extract  # noqa: E402

SAIDA = ROOT / "docs/pitch/comparacao_anexo_iv.md"
ROTULOS = {"novo": "novo", "alterado": "alterado", "ja_existia": "já existia"}


def relatorio(plano, comparacao):
    c = comparacao
    r = c["resumo"]
    totais = Counter(v["classe"] for v in c["itens"].values())
    partes = [
        "# Anexo IV da REN 956/2021 — comparação documental v2 × v3",
        "Fontes oficiais baixadas do repositório público da ANEEL e fornecidas pelo fundador em 22/11/2026. "
        "Sem rede ou IA na comparação. O recorte temporal anterior à RN 1.137 é o informado para a v2.",
        f"**Plano RN 1.137: {r['novo']} novos · {r['alterado']} alterados · {r['ja_existia']} já existiam · "
        f"{r['sem_fonte']} sem fonte anterior.** São registros da lista de deveres do plano, incluindo seus "
        "detalhamentos; as contagens existentes não mudam (147 deveres, 8 obrigações vencidas e 11 detalhes vencidos).",
        f"No módulo completo, incluindo dispositivos que não são deveres contados no plano: "
        f"{totais['novo']} itens novos, {totais['alterado']} alterado e {totais['ja_existia']} já existentes. "
        "O item 1 é a apresentação das seções do módulo; a ampliação do índice não é um novo dever.",
        c["limite"],
        "A comparação identifica presença e redação por número de item; não conclui que inexista qualquer "
        "dever equivalente em outro ato. Ignora espaços/quebras e os marcadores de alínea na comparação "
        "integral do item: a fonte v2 renderiza as letras, mas não as devolve na extração textual. "
        "As citações exibidas permanecem literais; os dispositivos e páginas identificam a fonte.",
        "## Fontes e hashes",
    ]
    for v, f in c["fontes"].items():
        partes.append(
            f"- **{v} — {f['titulo']}**: [{f['arquivo']}]({f['origem']}); SHA-256 `{f['sha256']}`."
        )
    partes += [
        "## A v3 confere com a RN 1.137?",
        f"**Não integralmente:** {len(c['registros']) - r['divergencias_v3']} dos {len(c['registros'])} "
        f"registros de dever do Módulo 4 conferem literalmente, ignorando espaços e marcas NR/AC; "
        f"{r['divergencias_v3']} divergem. O rodapé da v3 atribui o anexo à REN 1.137, mas isso não elimina "
        "as diferenças abaixo. Não foi escolhida uma redação substituta: o plano continua citando o PDF da RN 1.137.",
        "Há diferenças de remissão, além de pontuação ou concordância: nos itens 110 e 112, "
        "a RN remete ao item 105 e a v3 ao item 103. A divergência foi conferida visualmente na "
        "página física 7 do PDF da RN e na página 23 da v3. Não se presume equivalência entre essas leituras.",
    ]
    divergentes = {}
    for o in plano["obrigacoes"]:
        registro = c["registros"].get(o["id"])
        if registro and not registro["confere_v3"]:
            divergentes.setdefault(registro["item"], []).append(o)
    for n, obrigacoes in divergentes.items():
        atual = c["itens"][n]["atual"]
        partes += [f"### Item {n} — conferir a divergência entre fontes"]
        for o in obrigacoes:
            partes.append(f"**RN 1.137 — {o['dispositivo']}:** “{o['trecho']}”")
        partes.append(
            f"**v3 — item {n}, página física {atual['pagina']} "
            f"(até {atual['ultima_pagina']}):** “{atual['trecho']}”"
        )
    partes += ["## Itens alterados — texto anterior ao lado do atual"]
    for n, item in c["itens"].items():
        if item["classe"] != "alterado":
            continue
        partes += [
            f"### Item {n}",
            f"| v2 — página {item['anterior']['pagina']} | v3 — página {item['atual']['pagina']} |\n"
            "| --- | --- |\n"
            + "| “"
            + item["anterior"]["trecho"].replace("|", r"\|")
            + "” | “"
            + item["atual"]["trecho"].replace("|", r"\|")
            + "” |",
        ]
    partes += [
        "## Inventário do módulo completo",
        "| Item | Classe v2 × v3 | Página v2 | Página v3 |\n| --- | --- | --- | --- |",
    ]
    partes[-1] += "\n" + "\n".join(
        f"| {n} | {ROTULOS[v['classe']]} | {v['anterior']['pagina'] if v['anterior'] else 'ausente'} | {v['atual']['pagina']} |"
        for n, v in c["itens"].items()
    )
    partes += [
        "## Limites e decisão",
        "O item 4 foi retomado com as fontes fornecidas. "
        "Os 35 registros sem fonte anterior não recebem uma classificação presumida. "
        "Caio e revisão especializada devem conferir as divergências antes de adotar outra redação. "
        "O PR #52 permanece draft; seu merge não foi autorizado.",
    ]
    return "\n\n".join(partes) + "\n"


def main():
    plano = json.loads((ROOT / "landing/src/content/plano-rn1137.json").read_text(encoding="utf-8"))
    extraction = extract(
        (ROOT / "tests/norma_poc/ren20251137.pdf").read_bytes(),
        "application/pdf",
        Settings(ai_mode="off", model="", api_key=""),
    )
    c = montar(plano, extraction)
    SAIDA.write_text(relatorio(plano, c), encoding="utf-8", newline="\n")
    print(json.dumps(c["resumo"]))


if __name__ == "__main__":
    main()
