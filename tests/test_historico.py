"""Referência histórica: validação, exclusões, estatística e trava contra dado sintético."""

import statistics
import subprocess
import sys
from pathlib import Path

import pytest

from athenix import historico

ROOT = Path(__file__).resolve().parents[1]


def obs(i, **mudar):
    linha = {c: "" for c in historico.CAMPOS} | {
        "auto_infracao": f"AI-{i}", "agente": f"A{i % 6}", "segmento": "distribuicao",
        "dispositivo": "Art. 12, XXVI", "grupo": "IV", "regime": "REN 846", "data_infracao": "2024-03-01",
        "sancao": "multa", "base_tipo": "ROL", "base_valor": "1000000", "principal_final": str(1000 * (i + 1)),
        "estado": "pago", "valor_por_infracao": "sim", "fonte_arquivo": "voto.pdf", "fonte_pagina": "3",
        "fonte_trecho": "trecho", "fonte_sha256": "a" * 64, "coletado_em": "2026-11-17", "sintetico": "nao",
    }  # fmt: skip
    return linha | mudar


def test_validacao_aponta_cada_problema():
    assert historico.validar(obs(0)) == []
    assert "grupo inválido: VI" in historico.validar(obs(0, grupo="VI"))
    assert "base_valor deve ser positivo" in historico.validar(obs(0, base_valor="0"))
    assert "fonte_sha256 deve ter 64 caracteres hexadecimais" in historico.validar(obs(0, fonte_sha256="x"))  # fmt: skip
    assert "fonte_trecho vazio" in historico.validar(obs(0, fonte_trecho=" "))


def test_total_agregado_advertencia_e_estado_sem_decisao_ficam_fora():
    linhas = [obs(0), obs(1, valor_por_infracao="nao"), obs(2, sancao="advertencia", principal_final="0"), obs(3, estado="autuado")]  # fmt: skip
    (e,) = historico.estatisticas(linhas)
    assert e["n"] == 1 and e["advertencias"] == 1
    assert sum(e["exclusoes"].values()) == 3
    assert any("não se divide" in m for m in e["exclusoes"])


def test_mediana_quartis_e_minimo_de_observacoes():
    linhas = [obs(i) for i in range(30)]  # 0,1% a 3,0% da base
    (e,) = historico.estatisticas(linhas, min_agentes=5)
    pcts = [100 * 1000 * (i + 1) / 1_000_000 for i in range(30)]
    assert e["mediana_pct"] == pytest.approx(statistics.median(pcts))
    assert e["q1_pct"] < e["mediana_pct"] < e["q3_pct"]
    assert e["agentes"] == 6 and e["publicavel"]
    assert e["maior_participacao_agente"] == pytest.approx(5 / 30)
    ref = historico.referencia(2_000_000, e)
    assert ref["valor"] == pytest.approx(2_000_000 * e["mediana_pct"] / 100)
    assert ref["rotulo"] == historico.ROTULO
    (poucos,) = historico.estatisticas(linhas[:29], min_agentes=5)
    assert not poucos["publicavel"] and "29 < 30" in poucos["motivo"]
    assert not historico.referencia(2_000_000, poucos)["estimavel"]
    # Sem decisão sobre diversidade de agentes, nada é publicável.
    (sem_decisao,) = historico.estatisticas(linhas)
    assert not sem_decisao["publicavel"]


def test_dado_sintetico_nunca_e_publicavel(tmp_path):
    csv = tmp_path / "s.csv"
    subprocess.run([sys.executable, str(ROOT / "scripts/referencia_historica.py"), "--sintetico", str(csv)], check=True, capture_output=True)  # fmt: skip
    validas, erros = historico.ler_observacoes(csv)
    assert not erros and validas and all(v["sintetico"] == "sim" for v in validas)
    for e in historico.estatisticas(validas, minimo=1, min_agentes=1):
        assert not e["publicavel"] and e["motivo"].startswith("SINTÉTICO")


def test_colunas_ausentes_e_csv_de_autos(tmp_path):
    ruim = tmp_path / "ruim.csv"
    ruim.write_text("grupo;agente\nIV;A\n", encoding="utf-8")
    assert historico.ler_observacoes(ruim)[1][0][1][0].startswith("colunas ausentes")
    autos = tmp_path / "autos.csv"
    autos.write_text("NumAI;VlrPenalidade;DscEnquadramentoAI\n1;10,00;x\n", encoding="utf-8")
    r = historico.ler_autos(autos)
    assert r["linhas"] == 1 and set(r["faltando"]) == {"VlrMultaAposJuizo", "VlrMultaAposDiretoria"}
