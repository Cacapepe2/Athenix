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
    ("texto", "grupos"),
    [
        ("Multa do Grupo IV (REN 846/2019) Art. 12", "IV"),
        (
            "Multa do Grupo III (REN 846/2019) Art. 11 / Multa do Grupo III (REN 846/2019) Art. 11",
            "III",
        ),
        # Auto com mais de um grupo vira estrato próprio (o valor é do auto, não é dividido).
        (
            "Multa do Grupo V (REN 846/2019) Art. 13 / Multa do Grupo III (REN 846/2019) Art. 11",
            "III+V",
        ),
        ("Multa do Grupo III Art. 6º", None),  # regime anterior: sem REN 846
        ("Multa do Grupo IV (REN 846/2019) Art. 11", None),  # grupo declarado difere do catálogo
        ("Advertência Art. 3º", None),
        ("", None),
    ],
)
def test_grupos_do_auto_coerentes_com_o_catalogo(texto, grupos):
    assert A.grupos_do_caso(texto, POR_ARTIGO)[0] == grupos


def test_segmento_so_por_evidencia_explicita():
    assert A.segmento_do_caso({"CodObjetoFiscalizado": "EOL.CV.BA.001"})[0] == "geração"
    nat = {"CodObjetoFiscalizado": "Não", "NomNaturezaFiscalizacao": "Obras de Transmissão"}
    assert A.segmento_do_caso(nat) == ("transmissão", "natureza da fiscalização")
    nome = {
        "NomAgenteFiscalizado": "XYZ Distribuição de Energia S/A",
        "NomNaturezaFiscalizacao": "Técnica",
    }
    assert A.segmento_do_caso(nome) == ("distribuição", "nome no CSV de autos")
    assert (
        A.segmento_do_caso({"NomAgenteFiscalizado": "Light"}, "LIGHT DISTRIBUIDORA S.A.")[0]
        == "distribuição"
    )
    assert A.segmento_do_caso(
        {"NomAgenteFiscalizado": "Light", "NomNaturezaFiscalizacao": "Comercial"}
    )[0] == ("segmento não identificado")
    assert A.segmento_do_caso({"NomAgenteFiscalizado": "Geradora e Transmissão e Distribuição"})[
        0
    ] == ("segmento não identificado")


def _sigec(*situacoes):
    linhas = [
        {
            "NumAutoInfracao": "1/2020-X",
            "NumCPFCNPJ": "11.111.111/0001-11",
            "SigNomAgente": "A",
            "DscSituacaoCredito": s,
        }
        for s in situacoes
    ]
    return A.Sigec(linhas)


@pytest.mark.parametrize(
    ("situacoes", "esperado"),
    [
        (["Quitada", "Quitada"], "quitado"),
        (["Multa Convertida em Advertência"], "convertida em advertência"),
        (["Cancelada", "Suspenso COM Seguro Garantia"], "suspenso (judicial ou seguro)"),
        (["Cancelada"], "cancelada"),
        (["Parcelamento"], "parcelado"),
    ],
)
def test_situacao_do_credito_no_sigec_cruza_por_auto_e_cnpj(situacoes, esperado):
    s = _sigec(*situacoes)
    assert s.situacao("1/2020-X", "11111111000111") == esperado
    assert s.situacao("1/2020-X", "99999999000199") is None  # mesmo número, outra empresa


def test_estado_usa_sigec_e_depois_encerramento_e_diretoria():
    r = {"NumTermoEncerramento": "", "DatDecisaoDiretoria": ""}
    assert A.estado(r, None) == "em andamento"
    assert A.estado(r | {"DatDecisaoDiretoria": "2020-01-01"}, None) == "decidido pela Diretoria"
    assert A.estado(r | {"NumTermoEncerramento": "TE 1"}, None) == "encerrado"
    assert (
        A.estado(r | {"NumTermoEncerramento": "TE 1"}, "suspenso (judicial ou seguro)")
        not in A.CONTAM
    )
    assert A.estado(r, "quitado") in A.CONTAM


def _casos(n, empresas):
    return [
        {
            "cnpj": str(i % empresas),
            "valor": Decimal(i + 1),
            "campo": "VlrPenalidade",
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
        r["contagem"]["classificados (grupos da REN 846)"]
        + sum(r["nao_classificados_por"].values())
        == 1635
    )
    assert r["estratos"]["I x distribuição"]["valor_provavel"].startswith("amostra insuficiente")
    assert r["segmento_de_todos_os_autos"]["distribuição"] == 109
