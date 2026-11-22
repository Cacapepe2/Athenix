"""Dever dentro de uma faculdade da distribuidora: só se ela optar, com caput rastreável."""

import json
from pathlib import Path

import pytest

from athenix import plano, proposals
from athenix.config import Settings
from athenix.structure import extract

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("modal", ["pode", "poderá", "podem", "é facultado", "fica facultado"])
def test_faculdade_em_ancestral_do_dever_e_das_alineas(modal):
    caput = f"Art. 9. A distribuidora {modal} aderir ao programa, observadas as condições:"
    units = [
        {"id": "a", "parent": None, "text": caput, "kind": "article"},
        {
            "id": "i",
            "parent": "a",
            "text": "I - a distribuidora deve apresentar:",
            "kind": "clause",
        },
        {"id": "l", "parent": "i", "text": "a) o plano de acompanhamento.", "kind": "letter"},
    ]
    by_id = {u["id"]: u for u in units}
    assert proposals.modality(caput) == "permission"
    assert proposals.rule_candidates({"units": units})
    for u in units[1:]:
        assert plano.faculdade_do_dispositivo(u, by_id)["trecho"] == caput


@pytest.mark.parametrize(
    "caput",
    [
        "Art. 9. A distribuidora deve participar do programa:",
        "Art. 9. O consumidor pode solicitar informação à distribuidora:",
        "Art. 9. A distribuidora deve divulgar as regras, que podem ser consultadas:",
    ],
)
def test_dever_ou_faculdade_de_terceiro_nao_sao_adesao_voluntaria(caput):
    raiz = {"id": "a", "parent": None, "text": caput}
    assert plano.faculdade_do_dispositivo({"parent": "a"}, {"a": raiz}) is None


def test_sandbox_texto_real_sujeito_modalidade_e_deveres_fora_da_exposicao():
    e = extract(
        (ROOT / "tests/fontes_impacto/dou/dou_ren20261174.html").read_bytes(),
        "text/html",
        Settings(),
        "norm",
    )
    by_id = {u["id"]: u for u in e["units"]}
    (caput,) = [
        u
        for u in e["units"]
        if u["kind"] == "article" and u["owner"] == "self" and u["label"] == "11"
    ]
    assert proposals.subject_of(caput["text"]) == "As distribuidoras"
    assert proposals.modality(caput["text"]) == "permission"
    assert "podem desenvolver Sandbox Regulatório" in caput["text"]
    filhos = {u["label"]: u for u in e["units"] if u["parent"] == caput["id"]}
    assert proposals.subject_of(filhos["I"]["text"]) == "a distribuidora"
    assert proposals.modality(filhos["I"]["text"]) == "duty"
    assert "previamente ao início" in filhos["I"]["text"]
    assert "a partir da autorização do Sandbox" in filhos["VIII"]["text"]
    assert "semestralmente" in filhos["VIII"]["text"]
    assert proposals.modality(filhos["VIII"]["text"]) == "duty"
    p = json.loads((ROOT / "landing/src/content/plano-ren1174.json").read_text(encoding="utf-8"))
    condicionais = [o for o in p["outros_dispositivos"] if o["natureza"] == "dever_condicional"]
    sandbox = [o for o in condicionais if o["condicao"]["unidade"] == caput["id"]]
    assert len(sandbox) == 9  # proposta (2 trechos + 5 alíneas), divulgação e relatórios.
    assert {o["dispositivo"] for o in sandbox} >= {"Art. 11, inciso I", "Art. 11, inciso VIII"}
    for o in sandbox:
        assert o["rotulo"] == "Dever condicional: se aderir ao sandbox"
        assert o["condicao"]["trecho"] == " ".join(caput["text"].split())
        assert plano.faculdade_do_dispositivo(by_id[o["unidade"]], by_id)["unidade"] == caput["id"]
        assert o["id"] not in {d["id"] for d in p["obrigacoes"]}
        assert all(o["id"] not in t["obrigacoes"] for t in p["temas"])
    # A regra geral também alcança o Art. 166, § 6º, I: prazos menores são faculdade.
    assert len(condicionais) == 10
    assert p["resumo"]["aplicaveis"] == 75  # 85 - 9 do sandbox - 1 de prazos opcionais.
