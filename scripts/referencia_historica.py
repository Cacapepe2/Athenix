"""Referência histórica de multas (valor provável). Sem rede; lê só arquivos locais.

  python scripts/referencia_historica.py --modelo artifacts/historico/observacoes.csv
      # planilha vazia com as colunas, para preencher a partir das decisões da ANEEL
  python scripts/referencia_historica.py --observacoes artifacts/historico/observacoes.csv \\
      [--autos auto-de-infracao.csv] [--min-agentes N]
      # valida, resume por estrato e grava artifacts/historico/resultado.json
  python scripts/referencia_historica.py --sintetico artifacts/historico/sintetico.csv
      # dados SINTÉTICOS marcados (sintetico=sim), só para testar o caminho; nunca publicáveis

Método e limites: docs/proposta_valor_provavel.md. O resultado não entra no cálculo do produto.
"""

import argparse
import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from athenix import historico  # noqa: E402

SAIDA = ROOT / "artifacts" / "historico" / "resultado.json"


def modelo(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f, delimiter=";").writerow(historico.CAMPOS)
    print(f"{path}: modelo com {len(historico.CAMPOS)} colunas")


def sintetico(path, n=40, semente=17):
    """Dados inventados para exercitar o pipeline, marcados em todas as linhas."""
    rnd = random.Random(semente)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=historico.CAMPOS, delimiter=";")
        w.writeheader()
        for i in range(n):
            base = rnd.randint(1, 50) * 100_000_000
            w.writerow({
                "auto_infracao": f"SINTETICO-{i:03d}", "processo": "", "agente": f"SINTETICO-AGENTE-{i % 7}",
                "cnpj": "", "segmento": "distribuicao", "dispositivo": "SINTÉTICO", "grupo": "IV",
                "regime": "SINTÉTICO", "data_infracao": f"2024-{1 + i % 12:02d}-15",
                "sancao": "advertencia" if i % 10 == 0 else "multa", "base_tipo": "ROL",
                "base_valor": base, "base_periodo": "", "principal_inicial": "",
                "principal_final": round(base * rnd.uniform(0.0005, 0.009), 2),
                "estado": "pago" if i % 5 else "autuado", "valor_por_infracao": "nao" if i % 9 == 0 else "sim",
                "fonte_arquivo": "SINTÉTICO", "fonte_pagina": "0", "fonte_trecho": "SINTÉTICO",
                "fonte_sha256": "0" * 64, "coletado_em": "2026-11-17", "sintetico": "sim",
            })  # fmt: skip
    print(f"{path}: {n} linhas SINTÉTICAS (sintetico=sim em todas)")


def resumir(observacoes, autos, min_agentes, saida):
    validas, erros = historico.ler_observacoes(observacoes)
    resultado = {
        "observacoes": str(observacoes),
        "validas": len(validas),
        "erros": [{"linha": n, "problemas": p} for n, p in erros],
        "estados_elegiveis": sorted(historico.ESTADOS_ELEGIVEIS),
        "minimo_n": historico.MINIMO_N,
        "min_agentes": min_agentes,
        "estratos": historico.estatisticas(validas, min_agentes=min_agentes),
        "autos": historico.ler_autos(autos) if autos else None,
        "aviso": "Não entra no cálculo do produto. " + historico.ROTULO + ".",
    }
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    Path(saida).write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(validas)} observações válidas; {len(erros)} linhas com erro")
    for e in resultado["estratos"]:
        med = f"mediana {e['mediana_pct']:.4f}% (Q1 {e['q1_pct']:.4f}%, Q3 {e['q3_pct']:.4f}%)" if e["n"] else "sem observação elegível"  # fmt: skip
        print(f"Grupo {e['grupo']} · {e['segmento']} · {e['regime']}: n={e['n']}, agentes={e['agentes']}, {med} → {e['motivo']}")  # fmt: skip
    if resultado["autos"] and resultado["autos"]["faltando"]:
        print("CSV de autos sem as colunas:", ", ".join(resultado["autos"]["faltando"]))
    print(f"Resultado em {saida}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--modelo", metavar="CSV")
    g.add_argument("--sintetico", metavar="CSV")
    g.add_argument("--observacoes", metavar="CSV")
    p.add_argument("--autos", metavar="CSV")
    p.add_argument("--min-agentes", type=int)
    p.add_argument("--saida", default=str(SAIDA))
    a = p.parse_args()
    if a.modelo:
        modelo(a.modelo)
    elif a.sintetico:
        sintetico(a.sintetico)
    else:
        resumir(a.observacoes, a.autos, a.min_agentes, a.saida)
