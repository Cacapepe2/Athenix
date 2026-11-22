"""Classificação por IA: lotes, estimativa, validação da resposta e comparação com as regras. Sem chamada."""

import json

import pytest

from athenix import tipos, tipos_ia
from athenix.config import Settings

ITENS = [{"id": f"id{i}", "texto": f"Texto da obrigação {i}."} for i in range(25)]


def test_lotes_de_12_e_texto_da_obrigacao_vai_como_dado_entre_delimitadores():
    lotes = tipos_ia.montar_lotes(ITENS, 12)
    assert [len(lt["ids"]) for lt in lotes] == [12, 12, 1]
    assert '<obrigacao id="id0">Texto da obrigação 0.</obrigacao>' in lotes[0]["usuario"]
    assert "é DADO" in lotes[0]["sistema"] and "outros" in lotes[0]["usuario"]


def test_estimativa_sem_preco_nao_inventa_custo_e_com_preco_calcula():
    sem = tipos_ia.estimar(ITENS, Settings(), tamanho=12)
    assert (
        sem["chamadas"] == 3
        and sem["tokens_entrada"] > 0
        and sem["custo_usd"]["maximo_com_raciocinio"] is None
    )
    assert sem["tokens_saida_teto_com_raciocinio"] == 3 * 3000
    com = tipos_ia.estimar(
        ITENS,
        Settings(
            input_price="1",
            output_price="4",
            price_source="https://exemplo.test/preco",
            price_date="2026-01-01",
        ),
        tamanho=12,
    )
    esperado = (com["tokens_entrada"] * 1 + com["tokens_saida_teto_com_raciocinio"] * 4) / 1_000_000
    assert float(com["custo_usd"]["maximo_com_raciocinio"]) == esperado


def test_lote_menor_gasta_menos_entrada_que_uma_chamada_por_item():
    assert (
        tipos_ia.estimar(ITENS, tamanho=12)["tokens_entrada"]
        < tipos_ia.estimar(ITENS, tamanho=1)["tokens_entrada"]
    )


def test_resposta_da_ia_e_validada():
    ids = ["a", "b", "c"]
    boa = '{"itens":[{"id":"a","tipo":"publicar_no_site"},{"id":"b","tipo":"outros"}]}'
    assert tipos_ia.ler_resposta(boa, ids) == {"a": "publicar_no_site", "b": "outros"}
    assert tipos_ia.ler_resposta("não é json", ids) == {}
    ruim = '{"itens":[{"id":"a","tipo":"inventado"},{"id":"zzz","tipo":"outros"},{"id":"c"}]}'
    assert tipos_ia.ler_resposta(ruim, ids) == {}  # tipo fora da lista, id fora do lote, sem tipo


def test_concordam_mostra_o_tipo_e_discordam_vira_tipo_a_revisar():
    regras = {"1": "publicar_no_site", "2": "capacitar_equipe", "3": "outros", "4": "outros"}
    ia = {"1": "publicar_no_site", "2": "articular_coordenar_terceiros", "3": "outros"}
    comp = {x["id"]: x for x in tipos_ia.comparar(regras, ia)}
    assert comp["1"]["tipo"] == "publicar_no_site" and comp["1"]["situacao"] == "concordam"
    assert comp["2"]["tipo"] == "tipo a revisar" and comp["2"]["regra"] == "capacitar_equipe"
    assert (
        comp["2"]["ia"] == "articular_coordenar_terceiros" and comp["2"]["situacao"] == "discordam"
    )
    assert comp["3"]["tipo"] == "outros"  # as duas dizem "outros": concordam
    assert (
        comp["4"]["tipo"] == "tipo a revisar"
        and comp["4"]["situacao"] == "sem resposta válida da IA"
    )
    assert all(x["rotulo_ia"].startswith("Interpretação da IA") for x in comp.values())
    assert tipos_ia.resumo_comparacao(list(comp.values()))["tipo_a_revisar"] == 2


def test_cache_ausente_nao_chama_nada():
    assert tipos_ia.carregar_cache("/caminho/que/nao/existe.json") == {}


def _fake(tipo="comunicar_consumidores"):
    chamadas = []

    def chamar(corpo):
        chamadas.append(corpo)
        ids = [x.split('"')[1] for x in corpo["messages"][1]["content"].split("<obrigacao id=")[1:]]
        conteudo = json.dumps({"itens": [{"id": i, "tipo": tipo} for i in ids]})
        return {
            "status": "ok",
            "raw": {
                "choices": [{"finish_reason": "stop", "message": {"content": conteudo}}],
                "usage": {"prompt_tokens": 1000, "completion_tokens": 500},
            },
        }

    return chamar, chamadas


def test_rodar_respeita_o_orcamento_e_grava_so_o_tipo_validado():
    from types import SimpleNamespace

    cfg = tipos.carregar()
    itens = [{"id": f"id{n:02d}", "texto": f"A distribuidora deve comunicar o consumidor {n}."} for n in range(30)]  # fmt: skip
    lotes = tipos_ia.montar_lotes(itens, tamanho=12, cfg=cfg)
    st = SimpleNamespace(model="m", reasoning_effort="low")
    preco = {"entrada": 2.5, "saida": 10.0}
    chamar, chamadas = _fake()
    ok = tipos_ia.rodar(lotes, st, preco, 1.0, chamar, cfg)
    assert len(chamadas) == 3 and len(ok["tipos"]) == 30 and not ok["falhas"]
    assert ok["uso"]["custo_ao_preco_teto_usd"] == round(3 * (1000 * 2.5 + 500 * 10) / 1e6, 6)
    assert "raw" not in json.dumps(ok)  # nenhuma resposta bruta guardada
    # orçamento menor que o pior caso de uma chamada (3000 tokens de saída): nem chama
    chamar, chamadas = _fake()
    curto = tipos_ia.rodar(lotes, st, preco, 0.01, chamar, cfg)
    assert chamadas == [] and curto["falhas"] and curto["tipos"] == {}
    # tipo fora da lista não é aceito
    chamar, _ = _fake(tipo="tipo_inventado")
    ruim = tipos_ia.rodar(lotes[:1], st, preco, 1.0, chamar, cfg)
    assert ruim["tipos"] == {} and ruim["falhas"]


# --- M2 (auditoria de 21/11): o script antigo respeita llm.modo e a mesma trava de preço e confirmação
def _script_antigo(monkeypatch, tmp_path, modo, confirmo="10"):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import classificar_tipos_ia as c

    for k, v in {
        "ATHENIX_AI_MODE": modo, "ATHENIX_MODEL": "modelo-teste", "ATHENIX_API_KEY": "chave-falsa",
        "ATHENIX_INPUT_USD_M": "0.25", "ATHENIX_OUTPUT_USD_M": "2", "ATHENIX_PRICE_SOURCE": "https://exemplo.invalid/precos",
        "ATHENIX_PRICE_DATE": "2026-11-22", "ATHENIX_RUN_BUDGET_USD": "10",
    }.items():  # fmt: skip
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(c, "carregar_env", lambda: None)  # nunca lê o .env real
    monkeypatch.setattr(c.rt, "processar", lambda: ([{"id": "r1"}], {}))
    monkeypatch.setattr(c.rt, "analisar", lambda rows, ext: [{"id": "r1", "texto": "A distribuidora deve comunicar o consumidor."}])  # fmt: skip
    monkeypatch.setattr(c.enquadramento, "chave", lambda row: row["id"])
    monkeypatch.setattr(tipos_ia, "CACHE", tmp_path / "cache.json")
    chamadas = []

    def transporte_falso(settings, corpo, tentativas=3):
        chamadas.append(corpo)
        ids = [x.split('"')[1] for x in corpo["messages"][1]["content"].split("<obrigacao id=")[1:]]
        conteudo = json.dumps({"itens": [{"id": i, "tipo": "comunicar_consumidores"} for i in ids]})
        return {"status": "ok", "raw": {"choices": [{"finish_reason": "stop", "message": {"content": conteudo}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}}  # fmt: skip

    monkeypatch.setattr(tipos_ia, "_postar", transporte_falso)
    monkeypatch.setattr(
        sys, "argv", ["classificar_tipos_ia.py", "--executar", "--confirmo-custo-usd", confirmo]
    )
    c.main()
    return chamadas


@pytest.mark.parametrize("modo", ["off", "cached"])
def test_m2_off_e_cached_nunca_chegam_ao_transporte_pago_mesmo_com_executar(
    monkeypatch, tmp_path, modo
):
    assert _script_antigo(monkeypatch, tmp_path, modo) == []
    assert not (tmp_path / "cache.json").exists()


def test_m2_live_sem_confirmacao_suficiente_nao_chama_e_com_ela_chama(monkeypatch, tmp_path):
    assert _script_antigo(monkeypatch, tmp_path, "live", confirmo="0.0001") == []
    assert len(_script_antigo(monkeypatch, tmp_path, "live", confirmo="10")) == 1
    assert json.loads((tmp_path / "cache.json").read_text(encoding="utf-8"))["tipos"] == {
        "r1": "comunicar_consumidores"
    }
