"""Classificação por IA: lotes, estimativa, validação da resposta e comparação com as regras. Sem chamada."""

from athenix import tipos_ia
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
