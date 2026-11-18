"""Decisão de penalidade (3.4): votos reais da ANEEL em .local/dados_aneel/ e atos do DOU."""

from pathlib import Path

import pdfplumber
import pytest

from athenix import dou, penalidade, structure

RAIZ = Path(__file__).parent.parent
VOTOS = RAIZ / ".local/dados_aneel"
SEM_VOTOS = pytest.mark.skipif(not VOTOS.exists(), reason="votos da ANEEL só existem em .local/")


def _decisao(nome):
    with pdfplumber.open(VOTOS / nome) as pdf:
        return penalidade.decisao_de_penalidade([structure.page_text(p) for p in pdf.pages])


@SEM_VOTOS
def test_voto_que_reforma_a_multa_traz_o_novo_valor_com_citacao():
    d = _decisao("adsp20242090_1.pdf")
    assert d["processo"]["valor"] == "48500.006992/2022-98" and d["processo"]["pagina"] == 1
    assert "Taesa" in d["agente"]["valor"] and d["auto_de_infracao"]["numero"] == "0018/2023-SFT"
    assert [v["reais"] for v in d["valores_decididos"]] == ["8738737.50"]
    assert {"negar provimento", "reformar"} <= set(d["efeito"])
    assert "R$ 8.738.737,50" in d["dispositivo"]["trecho"] and d["dispositivo"]["pagina"] >= 15


@SEM_VOTOS
def test_voto_que_mantem_a_multa():
    d = _decisao("adsp20223244_1.pdf")
    assert d["auto_de_infracao"]["numero"] == "002/2022-SFE"
    assert [v["reais"] for v in d["valores_decididos"]] == ["32949775.22"]
    assert "manter" in d["efeito"] and d["dispositivos_infringidos_citados"]
    assert d["estado"].startswith("pendente de revisão humana")


@pytest.mark.parametrize("nome", ["dou_dsp20261293", "dou_ren20261162", "dou_ren20261174"])
def test_atos_do_dou_do_acervo_nao_decidem_penalidade(nome):
    # O Despacho 1.293 indefere uma súmula sobre a REN 846: cita penalidades, mas não decide multa.
    html = dou.ler_html((RAIZ / f"tests/fontes_impacto/dou/{nome}.html").read_bytes())
    assert penalidade.decisao_de_penalidade([html["texto"]]) is None
