import importlib.util
from pathlib import Path

from athenix import areas, areas_ia
from athenix.config import Settings

ROOT = Path(__file__).resolve().parents[1]
TEXTO = "A distribuidora deve publicar no sítio eletrônico o plano de contingência atualizado."


def script():
    spec = importlib.util.spec_from_file_location(
        "sugerir_areas_ia", ROOT / "scripts/sugerir_areas_ia.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_area_so_da_lista_e_trecho_literal_do_dever():
    assert areas_ia.validar("Comunicação/Atendimento", "publicar no sítio eletrônico", TEXTO) == (
        "Comunicação/Atendimento",
        "publicar no sítio eletrônico",
        None,
    )
    assert (
        areas_ia.validar("A definir", "", TEXTO)[2] == "a IA não indicou nenhuma das áreas da lista"
    )
    assert (
        areas_ia.validar("Financeiro", "publicar", TEXTO)[2]
        == "a IA indicou uma área fora da lista"
    )
    assert areas_ia.validar("Regulatório", "publicar na internet", TEXTO)[2] == (
        "o trecho citado pela IA não está no texto do dever"
    )
    assert areas_ia.validar("Regulatório", "", TEXTO)[2]
    assert "A definir" not in areas_ia.opcoes() and len(areas_ia.opcoes()) == 6


def test_aplicar_marca_a_origem_e_mantem_a_definir_com_motivo():
    cache = {
        "areas": {
            "a": {"area": "TI/Sistemas", "trecho": "o plano de contingência"},
            "b": {"area": "TI/Sistemas", "trecho": "texto que não está no dever"},
        },
        "reprovados": {"c": "a IA não indicou nenhuma das áreas da lista"},
    }
    o = {id_: {"id": id_, "area": "A definir", "area_origem": None} for id_ in "abcd"}
    for x in o.values():
        areas_ia.aplicar(x, TEXTO, cache)
    assert (o["a"]["area"], o["a"]["area_origem"]) == ("TI/Sistemas", "ia")
    assert o["a"]["area_ia"] == {
        "rotulo": "área sugerida (IA)",
        "trecho": "o plano de contingência",
    }
    assert o["b"]["area"] == "A definir" and "não está no texto" in o["b"]["area_motivo"]
    assert o["c"]["area"] == "A definir" and o["c"]["area_motivo"]
    assert o["d"] == {"id": "d", "area": "A definir", "area_origem": None}
    regra = {"id": "a", "area": "Jurídico", "area_origem": "regra"}
    areas_ia.aplicar(regra, TEXTO, cache)
    assert regra == {
        "id": "a",
        "area": "Jurídico",
        "area_origem": "regra",
    }  # a regra não é sobrescrita


def test_sem_live_ou_sem_confirmacao_nao_chama(monkeypatch, capsys):
    m = script()
    chamadas = []
    monkeypatch.setattr(m.se, "chamar_com_tempo_longo", lambda *a, **k: chamadas.append(1))
    cfg = areas.carregar()
    lotes = m.montar_lotes([{"id": "x", "dispositivo": "Art. 1", "trecho": TEXTO}], cfg)
    est = {"custo_maximo_usd": "0.01", "preco": None}
    cache = {"areas": {}, "reprovados": {}}
    m.executar(Settings(ai_mode="off", model="", api_key=""), lotes, "1", est, cache, cfg)
    assert not chamadas and "Nenhuma chamada feita" in capsys.readouterr().out
    assert (
        '<obrigacao id="x"' in lotes[0]["usuario"]
        and "Comunicação/Atendimento" in lotes[0]["usuario"]
    )


def test_planos_publicados_area_ia_na_lista_com_trecho_do_dever_ou_motivo():
    import json

    for nome in ("rn1137", "ren1174"):
        p = json.loads(
            (ROOT / f"landing/src/content/plano-{nome}.json").read_text(encoding="utf-8")
        )
        for o in p["obrigacoes"]:
            if o.get("area_ia"):
                assert o["area"] in areas_ia.opcoes() and o["area_origem"] == "ia"
                assert o["area_ia"]["rotulo"] == "área sugerida (IA)"
                assert areas_ia.espacos(o["area_ia"]["trecho"]) in areas_ia.espacos(o["trecho"])
            if o["area"] == "A definir" and o["id"] in areas_ia.carregar()["reprovados"]:
                assert o["area_motivo"]
