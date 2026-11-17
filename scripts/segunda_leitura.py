"""Gera lista de revisão separada a partir do cache do ensaio, sem rede nem .env."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from athenix.segunda_leitura import construir  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=ROOT / "artifacts/comparacao-regras-ia")
    parser.add_argument("--saida", type=Path, default=ROOT / "artifacts/revisao-ensaio")
    args = parser.parse_args()
    result = construir(
        json.loads((args.cache / "comparacao.json").read_text(encoding="utf-8")),
        json.loads((args.cache / "contexto_regras.json").read_text(encoding="utf-8")),
    )
    args.saida.mkdir(parents=True, exist_ok=True)
    (args.saida / "segunda_leitura.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Segunda leitura — revisão humana",
        "",
        "As regras continuam oficiais. Esta lista não entra no gabarito, na trava ou no cálculo de exposição.",
        "",
        "| Norma | Entradas do ensaio | Possíveis obrigações restantes |",
        "|---|---:|---:|",
    ]
    for norm, c in result["por_norma"].items():
        lines.append(f"| {norm} | {c['entrada']} | {c.get('restantes', 0)} |")
    lines += [
        "",
        "Critério: " + result["criterio_diferenca"],
        "",
        "## Amostra de 10",
        "",
        result["criterio_amostra"],
        "",
    ]
    for index, item in enumerate(result["amostra_10"], 1):
        i = item["interpretacao_ia"]
        lines += [
            f"### {index}. {item['norma']} — {item['dispositivo']}",
            "",
            item["rotulo"],
            "",
            f"Interpretação sugerida: {i['subject']} — {i['action']} {i['object']}",
            "",
            "Citações literais verificadas:",
            "",
        ]
        for a in item["citacoes"]:
            lines += [
                "> " + a["quote"].replace("\n", "\n> "),
                "",
                f"Unidade `{a['unit_id']}`; SHA-256 do texto `{a['text_hash']}`; posições {a['start']}–{a['end']}; segunda leitura `{a['source_check']}`.",
                "",
            ]
    lines += ["## Descartes", ""]
    for item in result["descartados"]:
        lines.append(
            f"- {item['norma']} · {item['dispositivo']}: {item['motivo']} (`{item['id']}`)."
        )
    (args.saida / "segunda_leitura.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "por_norma": result["por_norma"],
                "total": len(result["itens"]),
                "amostra": len(result["amostra_10"]),
                "paid_calls": 0,
            },
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
