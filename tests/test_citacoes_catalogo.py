"""Regressão: verificação de fragmentos não verifica uma citação inventada pela junção."""

from athenix import impacto
from athenix.evidence import key
from scripts.extrair_parametros import cite


def walk(value):
    if isinstance(value, dict):
        if value.get("ancora") == "verified" and "trecho" in value:
            yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def test_catalogo_nao_marca_omissao_editorial_como_literal():
    quotes = list(walk(impacto.carregar()))
    assert len(quotes) >= 150
    assert all("[…]" not in q["trecho"] and "[...]" not in q["trecho"] for q in quotes)
    for device in ("Art. 10, IX", "Art. 11, XXIV", "Art. 12, XX"):
        item = next(x for x in impacto.carregar()["infracoes"] if x["dispositivo"] == device)
        assert len(item["citacoes"]) == 2
        assert all(c["ancora"] == "verified" for c in item["citacoes"])
        assert any(key(item["trecho"]) in key(c["trecho"]) for c in item["citacoes"])


def test_rodape_nao_gera_citacao_composta_verified():
    first = "IX - deixar de implantar, operar ou manter as"
    second = "instalações de observações hidrométricas e solarimétricas;"
    text = first + "\nLeis.org/aneel - Rodapé\n\f\n8/46\n" + second
    unit = {"id": "u1", "text": text, "start": 0, "end": len(text), "struck": None}
    extraction = {
        "units": [unit],
        "text_hash": "hash",
        "source": {
            "trusted": True,
            "engine": "independente",
            "key": key(first) + "RODAPE" + key(second),
        },
    }
    result = cite(unit, extraction)
    assert result["ancora"] == "verified"
    assert result["trecho"] == second
    assert [c["trecho"] for c in result["citacoes"]] == [first, second]
    assert key(result["trecho"]) in extraction["source"]["key"]
    assert "[…]" not in result["trecho"]


def test_citacoes_verified_existem_em_leitura_independente_das_fontes_disponiveis():
    from scripts.extrair_parametros import DOCS, read

    docs = [read(name) for name, (path, _) in DOCS.items() if path.exists()]
    keys = [d["extraction"]["source"]["key"] for d in docs]
    all_present = len(docs) == len(DOCS)
    checked = 0
    for quote in walk(impacto.carregar()):
        if all_present or quote.get("fonte") in {
            name for name, (path, _) in DOCS.items() if path.exists()
        }:
            assert any(key(quote["trecho"]) in source for source in keys), quote["trecho"]
            checked += 1
    assert checked >= 3  # As três leis são fontes públicas versionadas, inclusive no CI.


def test_parte_sem_confirmacao_nao_herda_verified_da_primeira():
    first = "IX - deixar de implantar, operar ou manter as"
    second = "instalações cuja redação não foi confirmada na fonte independente;"
    text = first + "\nLeis.org/aneel - Rodapé\n\f\n8/46\n" + second
    unit = {"id": "u1", "text": text, "start": 0, "end": len(text), "struck": None}
    extraction = {
        "units": [unit],
        "text_hash": "hash",
        "source": {"trusted": True, "engine": "independente", "key": key(first)},
    }
    result = cite(unit, extraction)
    assert result["ancora"] != "verified"
    assert result["citacoes"][0]["ancora"] == "verified"
    assert result["citacoes"][1]["ancora"] != "verified"
