"""Possíveis erros materiais de prazo (temporal.erros_materiais) e esclarecimentos oficiais
(athenix/esclarecimentos.py): a busca roda só sobre os documentos salvos e nunca muda o cálculo sem uma
entrada confirmada em athenix/data/esclarecimentos_oficiais.json."""

import copy
import json
from pathlib import Path

import pytest

from athenix import esclarecimentos
from athenix.temporal import erros_materiais

ROOT = Path(__file__).resolve().parents[1]
PLANO = json.loads((ROOT / "landing/src/content/plano-rn1137.json").read_text(encoding="utf-8"))
ART_13_VI = next(o for o in PLANO["obrigacoes"] if o["dispositivo"] == "Art. 13, inciso VI")


# --- erros materiais
def test_art_13_vi_real_180_dias_mes():
    (e,) = erros_materiais(ART_13_VI["trecho"])
    assert e["problema"] == "unidade combinada (dias mês)" and e["leitura_provavel"] == "180 dias"


@pytest.mark.parametrize(
    ("texto", "problema"),
    [
        (
            "em até 180 (cento e vinte) dias da publicação",
            "número e extenso divergentes (180 × 120)",
        ),
        ("deve enviar em até 90 (noventa) para a ANEEL", "unidade de tempo ausente"),
        ("no prazo de 30 dias dias contados da publicação", "unidade repetida"),
        ("em até 12 meses anos da vigência", "unidade combinada (meses anos)"),
    ],
)
def test_frases_sinteticas_com_redacao_defeituosa(texto, problema):
    assert [e["problema"] for e in erros_materiais(texto)] == [problema]


@pytest.mark.parametrize(
    "texto",
    [
        "Até 90 (noventa) dias para revisar e publicar os planos",
        "disponibilidade ininterrupta durante 24 horas por dia e 7 dias por semana",
        "com atualização a cada 30 minutos",
        "em até 180 (cento e oitenta) dias da data de sua publicação",
    ],
)
def test_redacao_correta_nao_vira_erro_material(texto):
    assert erros_materiais(texto) == []


def test_plano_lista_erro_material_e_aplica_so_a_leitura_confirmada():
    (em,) = PLANO["erros_materiais"]
    assert em["dispositivo"] == "Art. 13, inciso VI" and em["leitura_provavel"] == "180 dias"
    assert (
        em["rotulo"] == "esclarecido"
        and "texto original: '180 (cento e oitenta) dias mês'" in em["esclarecimento"]
    )
    assert ART_13_VI["prazo"]["data"] == "2026-04-28"
    assert ART_13_VI["prazo"]["texto"].endswith("· esclarecido (FAQ da ANEEL)")


# --- busca nos esclarecimentos salvos
@pytest.fixture(scope="module")
def trechos():
    return esclarecimentos.carregar()


def test_fontes_salvas_tem_url_data_e_hash_conferido(trechos):
    assert trechos and all(
        t["url"].startswith("https://www.gov.br/aneel/") and t["consultado_em"] for t in trechos
    )
    assert {t["sha256"] for t in trechos} == {
        "a3ace3d565c44118f29952ebad2b7a5012ab1e210d3d97e687a601f3b276f4da"
    }


def test_busca_acha_o_faq_do_art_13_vi(trechos):
    caso = {
        "norma": "ren20251137",
        "dispositivo": ART_13_VI["dispositivo"],
        "trecho": ART_13_VI["trecho"],
        "prazo": "180 dias",
    }
    (primeiro, *_) = esclarecimentos.buscar(caso, trechos)
    assert primeiro["citacao"].startswith(
        "3.2 Qual é o prazo para início das apurações do indicador DISE?"
    )
    assert "o prazo final para início das apurações é 28/04/2026" in primeiro["citacao"]


def test_busca_nao_acha_nada_sem_mencao(trechos):
    caso = {"norma": "ren20251137", "dispositivo": "item 999", "trecho": "A distribuidora deve publicar o relatório anual das cooperativas."}  # fmt: skip
    assert esclarecimentos.buscar(caso, trechos) == []
    # documento de outra norma não serve
    assert (
        esclarecimentos.buscar(
            {**caso, "norma": "dou_ren20261174", "trecho": ART_13_VI["trecho"]}, trechos
        )
        == []
    )


def test_possivel_esclarecimento_nunca_muda_o_calculo_sem_entrada_confirmada(trechos):
    base = {"obrigacoes": copy.deepcopy(PLANO["obrigacoes"]), "transicao": PLANO["transicao"]}
    for o in base["obrigacoes"]:  # estado antes da anotação
        o["prazo"]["texto"] = o["prazo"]["texto"].replace(" · esclarecido (FAQ da ANEEL)", "")
        o.pop("erro_material", None), o.pop("esclarecimento", None)
    sem = copy.deepcopy(base)
    esclarecimentos.anotar_plano(sem, "ren20251137", trechos, entradas=[])
    vi = next(o for o in sem["obrigacoes"] if o["dispositivo"] == "Art. 13, inciso VI")
    assert vi["esclarecimento"] is None and vi["erro_material"]["rotulo"] == "a confirmar"
    assert vi["prazo"]["texto"].endswith(esclarecimentos.SUFIXO_ERRO)
    assert any(c["tipo"] == "possível erro material" for c in sem["a_confirmar"]["casos"])
    # cálculo (data, situação, faixa, fila) igual ao do plano sem nenhuma anotação
    chave = lambda o: (o["prazo"]["data"], o["situacao"], o.get("faixa"), o.get("posicao_fila"))  # noqa: E731
    assert [chave(o) for o in sem["obrigacoes"]] == [chave(o) for o in base["obrigacoes"]]


def test_entrada_confirmada_com_data_diferente_do_motor_trava(trechos):
    plano = {"obrigacoes": copy.deepcopy(PLANO["obrigacoes"]), "transicao": PLANO["transicao"]}
    (e,) = [x for x in esclarecimentos.confirmados() if x["dispositivo"] == "Art. 13, inciso VI"]
    errada = e | {"prazo": e["prazo"] | {"data": "2026-05-01"}}
    with pytest.raises(ValueError, match="difere do prazo calculado"):
        esclarecimentos.anotar_plano(plano, "ren20251137", trechos, entradas=[errada])


def test_relatorio_a_confirmar_por_norma():
    a = PLANO["a_confirmar"]
    assert a["total"] == sum(a["por_tipo"].values()) and a["com_possivel_esclarecimento"] == len(
        a["casos"]
    )
    assert all(c["possiveis_esclarecimentos"][0]["fonte"]["sha256"] for c in a["casos"])


def test_art_14_confirmado_pelo_faq_1_8_sem_mudar_a_data():
    (o,) = [x for x in PLANO["obrigacoes"] if x["dispositivo"] == "Art. 14"]
    assert o["prazo"]["data"] is None and o["situacao"] == "evento"  # continua por evento, sem data
    assert o["esclarecimento"]["nota"].startswith(
        "prazo condicionado às instruções da ANEEL; segundo o FAQ (1.8)"
    )
    assert (
        "Ainda não há prazo estabelecido para a publicação das instruções pela ANEEL."
        in o["esclarecimento"]["nota"]
    )
