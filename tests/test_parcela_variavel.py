"""Parcela Variável: sem norma não calcula; com parâmetros citados, calcula só aritmética permitida.

As fórmulas abaixo são SINTÉTICAS (inventadas para testar o motor) e não representam a norma.
"""

import pytest

from athenix import parcela_variavel as pv

SINTETICO = {
    "norma": {"ato": "SINTÉTICO", "sha256": "0" * 64},
    "componentes": {
        "base": {"expressao": "RAP / 12", "dispositivo": "SINTÉTICO 1", "trecho": "SINTÉTICO"},
        "PVI": {
            "expressao": "BASE * K * DURACAO / 43200",
            "dispositivo": "SINTÉTICO 2",
            "trecho": "SINTÉTICO",
        },  # fmt: skip
        "PVRO": {
            "expressao": "BASE * DURACAO / 43200 * FRACAO",
            "dispositivo": "SINTÉTICO 3",
            "trecho": "SINTÉTICO",
        },  # fmt: skip
        "PVA": {"expressao": None, "dispositivo": None, "trecho": None},
        "limite": {
            "expressao": "min(TOTAL, BASE / 2)",
            "dispositivo": "SINTÉTICO 4",
            "trecho": "SINTÉTICO",
        },  # fmt: skip
    },
    "fatores": {"K": {"valor": 10, "dispositivo": "SINTÉTICO 5", "trecho": "SINTÉTICO"}},
}


def test_arquivo_real_vazio_responde_nao_estimavel_e_lista_o_que_falta():
    r = pv.calcular(120_000_000, [{"tipo": "PVI", "duracao_min": 60}], pv.carregar())
    assert r["estimavel"] is False
    assert "norma vigente (ato e sha256 do arquivo)" in r["faltam"]
    assert any("componente PVI" in f for f in r["faltam"])
    assert pv.carregar()["procurar"]  # o arquivo diz o que buscar


def test_motor_calcula_com_parametros_citados_e_aplica_limite():
    eventos = [{"tipo": "PVI", "duracao_min": 60}, {"tipo": "PVRO", "duracao_min": 120, "variaveis": {"FRACAO": 0.5}}]  # fmt: skip
    r = pv.calcular(120_000_000, eventos, SINTETICO)
    base = 10_000_000
    assert r["base"] == base
    assert r["parcelas"][0]["valor"] == pytest.approx(base * 10 * 60 / 43200)
    assert r["total_antes_do_limite"] == pytest.approx(sum(p["valor"] for p in r["parcelas"]))
    assert r["total"] == pytest.approx(min(r["total_antes_do_limite"], base / 2))
    assert {f["componente"] for f in r["fontes"]} == {"base", "PVI", "PVRO", "limite"}


def test_componente_sem_citacao_bloqueia_o_tipo_pedido():
    r = pv.calcular(120_000_000, [{"tipo": "PVA", "duracao_min": 10}], SINTETICO)
    assert r["estimavel"] is False and any("PVA" in f for f in r["faltam"])
    sem_trecho = SINTETICO | {"fatores": {"K": {"valor": 10, "dispositivo": "x", "trecho": ""}}}
    assert any("fator K" in f for f in pv.pendencias(sem_trecho, ("PVI",)))


@pytest.mark.parametrize(
    "expressao",
    ["__import__('os').system('x')", "RAP.real", "open('x')", "X + 1", "RAP ** 2", "[RAP]"],
)
def test_expressao_fora_da_aritmetica_permitida_e_recusada(expressao):
    with pytest.raises(ValueError):
        pv.avaliar_expressao(expressao, {"RAP": 1.0})
