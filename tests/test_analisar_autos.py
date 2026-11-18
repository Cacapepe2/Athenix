"""Regras do valor provável (Bloco 4.2) com linhas sintéticas; contagens reais só se o CSV existir."""

from decimal import Decimal

import pytest

from scripts import analisar_autos as A

POR_ARTIGO = {"9": "I", "10": "II", "11": "III", "12": "IV", "13": "V"}


def test_valor_aceita_virgula_decimal_e_sem_inteiro():
    assert A.valor("123456,78") == Decimal("123456.78")
    assert A.valor(",99") == Decimal("0.99") and A.valor(" ") is None and A.valor("") is None


def test_valor_final_diretoria_depois_juizo_depois_penalidade():
    r = {"VlrPenalidade": "100,00", "VlrMultaAposJuizo": "80,00", "VlrMultaAposDiretoria": "70,00"}
    assert A.valor_final(r) == (Decimal("70.00"), "VlrMultaAposDiretoria")
    assert A.valor_final(r | {"VlrMultaAposDiretoria": ""}) == (
        Decimal("80.00"),
        "VlrMultaAposJuizo",
    )
    assert A.valor_final({"VlrPenalidade": "100,00"}) == (Decimal("100.00"), "VlrPenalidade")
    assert A.valor_final({"VlrPenalidade": ""}) == (None, None)


@pytest.mark.parametrize(
    ("texto", "grupo"),
    [
        ("Multa do Grupo IV (REN 846/2019) Art. 12", "IV"),
        (
            "Multa do Grupo III (REN 846/2019) Art. 11 / Multa do Grupo III (REN 846/2019) Art. 11",
            "III",
        ),
        (
            "Multa do Grupo III (REN 846/2019) Art. 11 / Multa do Grupo V (REN 846/2019) Art. 13",
            None,
        ),
        ("Multa do Grupo III Art. 6º", None),  # regime anterior: sem REN 846
        ("Multa do Grupo IV (REN 846/2019) Art. 11", None),  # grupo declarado difere do catálogo
        ("Advertência Art. 3º", None),
        ("", None),
    ],
)
def test_grupo_so_quando_unico_e_coerente_com_o_catalogo(texto, grupo):
    assert A.grupo_do_caso(texto, POR_ARTIGO)[0] == grupo


def test_segmento_so_por_evidencia_explicita():
    assert A.segmento_do_caso({"CodObjetoFiscalizado": "EOL.CV.BA.001"}) == "geração"
    assert (
        A.segmento_do_caso(
            {"CodObjetoFiscalizado": "Não", "NomNaturezaFiscalizacao": "Obras de Transmissão"}
        )
        == "transmissão"
    )
    assert (
        A.segmento_do_caso({"CodObjetoFiscalizado": "", "NomNaturezaFiscalizacao": "Comercial"})
        == "segmento não identificado"
    )


def test_estado_pago_encerrado_decidido_ou_em_andamento():
    r = {"NumAutoInfracao": "1/2020-X", "NumTermoEncerramento": "", "DatDecisaoDiretoria": ""}
    assert A.estado(r, set()) == "em andamento"
    assert A.estado(r | {"DatDecisaoDiretoria": "2020-01-01"}, set()) == "decidido pela Diretoria"
    assert A.estado(r | {"NumTermoEncerramento": "TE 1"}, set()) == "encerrado"
    assert A.estado(r, {"1/2020-X"}) == "pago"


def _casos(n, empresas):
    return [
        {
            "cnpj": str(i % empresas),
            "valor": Decimal(i + 1),
            "campo": "VlrPenalidade",
            "estado": "pago",
            "reformado": False,
        }
        for i in range(n)
    ]


def test_limiar_de_10_casos_e_5_empresas():
    assert A.estrato(_casos(9, 9))["valor_provavel"] == "amostra insuficiente (n = 9)"
    assert (
        A.estrato(_casos(30, 4))["valor_provavel"] == "amostra insuficiente (n = 30)"
    )  # só 4 empresas
    ok = A.estrato(_casos(10, 5))
    assert ok["valor_provavel"] == "estimável" and ok["mediana"] == "5.5"


@pytest.mark.skipif(not (A.DADOS / "auto-infracao.csv").exists(), reason="CSV só existe em .local/")
def test_contagens_reais():
    r = A.analisar()
    assert r["contagem"]["autos no CSV"] == 1635
    assert (
        sum(r["nao_classificados_por"].values()) + r["contagem"]["classificados em grupo (REN 846)"]
        == 1635
    )
    assert r["estratos"]["IV x distribuição"]["valor_provavel"].startswith("amostra insuficiente")
