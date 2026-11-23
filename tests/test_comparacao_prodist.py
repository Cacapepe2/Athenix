import copy
import hashlib
import json
from collections import Counter

import pytest

from athenix import comparacao_prodist as c
from athenix.config import Settings
from athenix.structure import extract
from scripts.demo.comparar_prodist import relatorio, SAIDA


@pytest.fixture(scope="module")
def dados():
    p = json.loads((c.ROOT / "landing/src/content/plano-rn1137.json").read_text(encoding="utf-8"))
    e = extract(
        (c.ROOT / "tests/norma_poc/ren20251137.pdf").read_bytes(),
        "application/pdf",
        Settings(ai_mode="off", model="", api_key=""),
    )
    return p, e, c.montar(p, e)


def test_fontes_reais_hash_sequencia_e_classes(dados):
    _, _, r = dados
    for f in r["fontes"].values():
        assert hashlib.sha256((c.ROOT / f["arquivo"]).read_bytes()).hexdigest() == f["sha256"]
    assert len(r["itens"]) == 148
    assert Counter(i["classe"] for i in r["itens"].values()) == {
        "novo": 55,
        "alterado": 1,
        "ja_existia": 92,
    }
    assert r["itens"]["103"]["classe"] == "novo" and r["itens"]["103"]["anterior"] is None
    assert r["itens"]["1"]["classe"] == "alterado"
    assert "Seção 4.7" not in r["itens"]["1"]["anterior"]["trecho"]
    assert "Seção 4.7" in r["itens"]["1"]["atual"]["trecho"]
    assert r["itens"]["92"]["classe"] == "ja_existia"
    assert r["itens"]["93"]["classe"] == "ja_existia"  # nova seção não integra o item anterior


def test_escopo_por_bloco_sem_alterar_plano_ou_classificar_outros_modulos(dados):
    p, e, r = dados
    antes = copy.deepcopy(p)
    assert c.montar(p, e) == r and p == antes
    assert r["resumo"] == {
        "novo": 112,
        "alterado": 0,
        "ja_existia": 0,
        "sem_fonte": 35,
        "divergencias_v3": 20,
    }
    assert not any(
        o["id"] in r["registros"]
        for o in p["obrigacoes"]
        if o["dispositivo"] == "Art. 13, inciso VI"
    )
    outra = copy.deepcopy(p)
    outra["norma"]["sha256"] = "outra fonte"
    assert c.montar(outra, e) is None
    with pytest.raises(ValueError, match="univocamente"):
        c.unidades_do_modulo({"units": []})


def test_v3_divergente_nao_substitui_citacao_da_rn_e_relatorio_reproduz(dados):
    p, _, r = dados
    o = next(o for o in p["obrigacoes"] if o["dispositivo"] == "item 110")
    assert "item 105" in o["trecho"]
    assert "item 103" in r["itens"]["110"]["atual"]["trecho"]
    assert r["registros"][o["id"]]["confere_v3"] is False
    o = next(o for o in p["obrigacoes"] if o["dispositivo"] == "item 115")
    assert r["registros"][o["id"]]["confere_v3"] is False
    assert "aos Poderes Públicos" in o["trecho"]
    assert "ao Poder Público" in r["itens"]["115"]["atual"]["trecho"]
    o = next(o for o in p["obrigacoes"] if o["dispositivo"] == "item 103")
    assert r["registros"][o["id"]]["confere_v3"] is True
    assert relatorio(p, r) == SAIDA.read_text(encoding="utf-8")


def test_hash_incorreto_interrompe(tmp_path, monkeypatch):
    catalogo = tmp_path / "tests/fontes_impacto"
    catalogo.mkdir(parents=True)
    (catalogo / "x.pdf").write_bytes(b"adulterado")
    (catalogo / "fontes.json").write_text(
        json.dumps(
            {"documentos": [{"id": "prodist4_v2", "arquivo": "x.pdf", "sha256": "incorreto"}]}
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(c, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="Hash divergente"):
        c.fontes()
