"""Tabela comparativa das notas de saúde entre versões do mapa de robustez (docs/robustez/).

Uso: python scripts/comparar_mapas.py
Cada mapa é a saída de scripts/avaliar_corpus.py (corpus_saude.json) gravada numa etapa do trabalho.
"""

import json
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parents[1] / "docs" / "robustez"
ETAPAS = [
    ("Original", "mapa_1_original.json"),
    ("Autoria por caput", "mapa_2_autoria.json"),
    ("Vetado/revogado", "mapa_3_vetado_revogado.json"),
]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    mapas = [json.loads((PASTA / f).read_text(encoding="utf-8")) for _, f in ETAPAS]
    nomes = [d["documento"] for d in mapas[0]]
    assert all([d["documento"] for d in m] == nomes for m in mapas), (
        "mapas com documentos diferentes"
    )
    cab = " | ".join(n for n, _ in ETAPAS)
    print(f"| Documento | {cab} | Anomalias de numeração |")
    print("| --- |" + " ---: |" * len(ETAPAS) + " ---: |")
    for linha in zip(*mapas):
        notas = " | ".join(str(d["nota"]) for d in linha)
        anom = " → ".join(str(d["metricas"]["anomalias_numeracao"]) for d in linha)
        print(f"| {linha[0]['documento']} | {notas} | {anom} |")
    print()
    for (nome, _), m in zip(ETAPAS, mapas):
        notas = [d["nota"] for d in m]
        anom = sum(d["metricas"]["anomalias_numeracao"] for d in m)
        abaixo = sum(n < 70 for n in notas)
        print(
            f"- {nome}: média {sum(notas) / len(notas):.1f}; abaixo de 70: {abaixo}; anomalias de numeração: {anom}."
        )


if __name__ == "__main__":
    main()
