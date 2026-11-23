import copy
import json
from pathlib import Path

import pytest

from athenix import esclarecimentos, rascunhos_aneel

ROOT = Path(__file__).resolve().parents[1]


def plano(nome):
    return json.loads((ROOT / f"landing/src/content/plano-{nome}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("nome,norma", [("rn1137", "ren20251137"), ("ren1174", "dou_ren20261174")])
def test_cada_sinal_tem_citacao_e_rascunho_reproduzido_sem_mudar_o_plano(nome, norma):
    p = plano(nome)
    antes = copy.deepcopy(p)
    grupos = rascunhos_aneel.montar(p, norma, esclarecimentos.carregar())
    divergencias = rascunhos_aneel.divergencias_prodist(p, p.get("comparacao_anterior"))
    assert grupos + divergencias == p["rascunhos_aneel"] and p == antes
    for c in esclarecimentos.casos_a_confirmar(p, norma):
        assert any(
            g["tipo"] == c["tipo"]
            and any(
                r["dispositivo"] == c["dispositivo"] and r["trecho"] == c["trecho"]
                for r in g["referencias"]
            )
            for g in grupos
        )
    for g in grupos:
        assert g["rotulo"] == "rascunho — revisar antes de enviar"
        assert g["duvida"].endswith("?")
        for r in g["referencias"]:
            assert r["itens"] and r["fonte"]["sha256"] == p["norma"]["sha256"]
            for e in r["possiveis_esclarecimentos"]:
                assert e["citacao"] and e["fonte"]["sha256"]


def test_duvidas_repetidas_agrupam_sem_perder_os_itens():
    p = plano("rn1137")
    o = copy.deepcopy(next(o for o in p["obrigacoes"] if o["sujeito_implicito"]))
    duplicada = copy.deepcopy(o)
    duplicada["id"] += "-outra-frase"
    p["obrigacoes"] = [o, duplicada]
    p["transicao"] = None
    grupos = rascunhos_aneel.montar(p, "ren20251137", [])
    (grupo,) = [g for g in grupos if g["tipo"] == "sujeito incerto"]
    (ref,) = grupo["referencias"]
    assert ref["itens"] == [o["id"], duplicada["id"]]
    assert ref["trecho"] == o["trecho"]


def test_prazo_confirmado_nao_reabre_pergunta_mas_enquadramento_continua_incerto():
    p = plano("rn1137")
    for dispositivo in ("Art. 13, inciso VI", "Art. 14"):
        o = next(o for o in p["obrigacoes"] if o["dispositivo"] == dispositivo)
        assert o["esclarecimento"]
        grupos = [
            g for g in p["rascunhos_aneel"] if any(o["id"] in r["itens"] for r in g["referencias"])
        ]
        assert any(g["tipo"] == "enquadramento sem texto" for g in grupos)
        assert not any(g["tipo"] in ("possível erro material", "transição ambígua") for g in grupos)


def test_sem_confirmacao_mostra_leitura_provavel_e_faq_sem_aplicar_correcao():
    p = plano("rn1137")
    o = next(o for o in p["obrigacoes"] if o["dispositivo"] == "Art. 13, inciso VI")
    o["esclarecimento"] = None
    antes = copy.deepcopy(p)
    grupos = rascunhos_aneel.montar(p, "ren20251137", esclarecimentos.carregar())
    (grupo,) = [g for g in grupos if g["tipo"] == "possível erro material"]
    assert any("180 dias" in leitura for leitura in grupo["leituras_possiveis"])
    assert grupo["referencias"][0]["possiveis_esclarecimentos"]
    assert p == antes and o["esclarecimento"] is None


def test_sem_citacao_nao_inventa_um_pedido():
    p = plano("rn1137")
    p["obrigacoes"][0]["trecho"] = None
    p["obrigacoes"][0]["sujeito_implicito"] = True
    with pytest.raises(ValueError, match="citação literal"):
        rascunhos_aneel.montar(p, "ren20251137", [])


def test_divergencias_prodist_viram_rascunho_com_as_duas_fontes_e_sem_envio():
    p = plano("rn1137")
    c = p["comparacao_anterior"]
    r = rascunhos_aneel.divergencias_prodist(p, c)
    assert [x["referencias"][0]["dispositivo"] for x in r] == [
        "RN 1.137 — item 143, alínea f",
        "RN 1.137 — item 143, alínea d",
        "RN 1.137 — item 110",
        "RN 1.137 — item 112",
        "RN 1.137 — item 119",
    ]
    for x in r:
        assert x["rotulo"] == "rascunho — revisar antes de enviar" and x["duvida"].endswith("?")
        assert (
            x["tipo"] == "divergência entre o texto publicado da RN e a versão compilada do PRODIST"
        )
        rn, v3 = x["referencias"]
        assert rn["fonte"]["sha256"] == p["norma"]["sha256"]
        assert v3["fonte"]["sha256"] == c["fontes"]["v3"]["sha256"] and rn["itens"] == v3["itens"]
        texto = " ".join(x["leituras_possiveis"]).lower()
        assert "erro" not in texto and "retifica" not in texto
    assert "Hipótese não conferida" in r[-1]["leituras_possiveis"][-1]
    assert rascunhos_aneel.divergencias_prodist(p, None) == []


def test_divergencia_com_fragmento_que_nao_esta_na_fonte_para_o_export(tmp_path):
    p = plano("rn1137")
    dados = json.loads(rascunhos_aneel.DIVERGENCIAS.read_text(encoding="utf-8"))
    dados["divergencias"][0]["v3"] = "treinamentos anuais ou simulações"
    falso = tmp_path / "d.json"
    falso.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="não conferido"):
        rascunhos_aneel.divergencias_prodist(p, p["comparacao_anterior"], falso)
