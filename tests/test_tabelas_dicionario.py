"""Teste de tabelas com o dicionário de dados real do Auto de Infração (ANEEL, v1.0, 03/05/2022)."""

from pathlib import Path

import pytest

from athenix.config import Settings
from athenix.poc import reader
from scripts import testar_tabelas as tt

CSV = Path(__file__).parent.parent / ".local/dados_aneel/auto-infracao.csv"


@pytest.fixture(scope="module")
def lido():
    return reader.read_pdf(tt.DICIONARIO, Settings())


def test_todos_os_campos_do_dicionario_sao_extraidos(lido):
    campos, _ = tt.campos_do_pipeline(lido["tables"])
    assert len(campos) == 28 and len({c["nome"] for c in campos}) == 28
    assert all(c["tipo"] in tt.TIPOS and len(c["descricao"]) > 8 for c in campos)
    por_nome = {c["nome"]: c for c in campos}
    assert por_nome["VlrMultaAposDiretoria"]["tamanho"] == "16,2"
    assert por_nome["DatDecisaoDiretoria"]["tamanho"] == ""  # data não tem tamanho


def test_tabela_da_pagina_seguinte_herda_o_cabecalho(lido):
    # A pág. 3 continua a tabela da pág. 2 sem repetir o cabeçalho: a 1ª linha é dado.
    p2, p3 = lido["tables"][0], lido["tables"][1]
    assert p3["continuation_of"] == p2["id"] and p3["header_inherited"]
    assert p3["header"] == p2["header"] and p3["header"][0] == "Nome do Campo"
    assert p3["rows"][0][0] == "NumProcessoPunitivo"  # linha preservada como lida
    assert "continuation_of" not in p2


def test_nenhuma_palavra_perdida_nem_acrescentada_nas_celulas(lido):
    r = tt.fidelidade_e_alinhamento(tt.DICIONARIO, lido["tables"])
    assert r["palavras_no_pdf"] > 400
    assert r["palavras_perdidas"] == [] and r["palavras_a_mais"] == []


@pytest.mark.skipif(not CSV.exists(), reason="CSV dos dados abertos só existe em .local/")
def test_campos_do_dicionario_x_colunas_do_csv(lido):
    campos, _ = tt.campos_do_pipeline(lido["tables"])
    colunas, linhas, _ = tt.le_csv(CSV)
    nomes = [c["nome"] for c in campos]
    assert [n for n in nomes if n not in colunas] == ["DatLavramentoTE"]
    assert [c for c in colunas if c not in nomes] == ["DatLavraturaTE"]  # grafia diverge
    assert len(colunas) == 28 and len(linhas) > 1000
