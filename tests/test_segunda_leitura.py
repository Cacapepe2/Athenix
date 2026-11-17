"""A segunda leitura não transforma atos da autoridade em deveres da empresa."""

import copy

import pytest

from athenix.evidence import key
from athenix.normalizacao import normalizar
from athenix.segunda_leitura import LABEL, construir, motivo_descarte, sem_dever_externo


@pytest.mark.parametrize(
    "text",
    [
        "Art. 87. Estabelecer as Receitas Anuais Permitidas pela disponibilização das instalações.",
        "Art. 4º Fixar os valores das Parcelas de Ajuste, conforme Anexo VI.",
        "Art. 9º Homologar as tarifas aplicáveis à concessionária.",
        "Art. 21. Esta Resolução entra em vigor na data de sua publicação.",
        "Art. 3º Revoga-se o inciso VIII da resolução anterior.",
    ],
)
def test_atos_sem_dever_externo_sao_excluidos_sem_identificar_norma(text):
    assert sem_dever_externo(text)


@pytest.mark.parametrize(
    "text",
    [
        "Art. 3º A concessionária deverá informar à ANEEL as receitas realizadas.",
        "Art. 4º Homologar os valores; as concessionárias devem publicar o relatório.",
        "Não deixar de enviar as informações de receitas à ANEEL.",
    ],
)
def test_obrigacoes_externas_inclusive_em_ato_homologatorio_sao_preservadas(text):
    assert not sem_dever_externo(text)


def test_nao_exclui_dever_real_por_causa_do_titulo_do_ato():
    units = {
        "u1": {"id": "u1", "parent": None, "text": "Homologar as tarifas."},
        "u2": {"id": "u2", "parent": "u1", "text": "A empresa deverá enviar relatório."},
    }
    item = {"type": "obligation", "locator": {"unit_id": "u2"}, "literal_text": units["u2"]["text"]}
    assert motivo_descarte(item, units) is None


def cached():
    text = "As distribuidoras realizarão inspeções periódicas na vegetação."
    unit = {"id": "u1", "parent": None, "text": text, "start": 0, "end": len(text)}
    item = {
        "id": "ia1",
        "type": "obligation",
        "literal_text": text,
        "dispositivo": "Art. 99",
        "locator": {"unit_id": "u1"},
        "interpretation": {
            "subject": "As distribuidoras",
            "action": "realizar",
            "object": "inspeções",
        },
        "anchors": [{"unit_id": "u1", "quote": text}],
    }
    comparison = {
        "extraction": {
            "differences": {"norma": {"ai_only_obligations": [{"id": "ia1"}]}},
            "ai_items": {"norma": [item]},
        }
    }
    context = {
        "docs": {
            "norma": {
                "extraction": {
                    "units": [unit],
                    "text_hash": "hash",
                    "source": {"trusted": True, "engine": "independente", "key": key(text)},
                },
                "items": [],
                "reference_key": normalizar(text, espacos="nenhum", caixa=True)[0],
            }
        }
    }
    return comparison, context


def test_cache_valido_gera_sugestao_separada_sem_mutar_regras():
    comparison, context = cached()
    original = copy.deepcopy(context)
    result = construir(comparison, context)
    assert result["por_norma"]["norma"]["restantes"] == 1
    assert result["itens"][0]["rotulo"] == LABEL
    assert result["itens"][0]["validation_state"] == "pending_human_review"
    assert result["chamadas_pagas"] == 0 and result["resultado_oficial"] == "regras"
    assert context == original


def test_citacao_nao_confirmada_e_descartada():
    comparison, context = cached()
    context["docs"]["norma"]["extraction"]["source"]["key"] = "outrafonte"
    result = construir(comparison, context)
    assert not result["itens"]
    assert "citação" in result["descartados"][0]["motivo"]


def test_mesma_obrigacao_oficial_nao_reaparece_como_novidade():
    comparison, context = cached()
    context["docs"]["norma"]["items"] = [{"type": "obligation", "locator": {"unit_id": "u1"}}]
    assert not construir(comparison, context)["itens"]


def test_permissao_nao_e_apresentada_como_obrigacao():
    comparison, context = cached()
    comparison["extraction"]["ai_items"]["norma"][0]["type"] = "permission"
    assert not construir(comparison, context)["itens"]


def test_citacao_ruim_anterior_nao_suprime_uma_sugestao_valida():
    comparison, context = cached()
    bad = copy.deepcopy(comparison["extraction"]["ai_items"]["norma"][0])
    bad["id"] = "invalida"
    bad["anchors"][0]["quote"] = "Uma citação que não existe no texto da norma."
    comparison["extraction"]["ai_items"]["norma"].insert(0, bad)
    comparison["extraction"]["differences"]["norma"]["ai_only_obligations"].insert(
        0, {"id": "invalida"}
    )
    result = construir(comparison, context)
    assert [i["id"] for i in result["itens"]] == ["ia1"]
    assert len(result["descartados"]) == 1


def attribution_fixture():
    from athenix.segunda_leitura import chave_atribuicao

    comparison, context = cached()
    item = construir(comparison, context)["itens"][0]
    review = {
        "metodo": "Triagem documental, sem confirmação humana.",
        "atribuicoes": [
            {
                "id": item["id"],
                "norma": item["norma"],
                "chave_conteudo": chave_atribuicao(item),
                "grupo": "agente_regulado",
                "responsavel": "Distribuidora",
                "fundamento": "O texto identifica a distribuidora como sujeito.",
                "evidencias": [{"unit_id": "u1", "quote": item["literal"]}],
            }
        ],
    }
    return construir(comparison, context), review, context


def test_atribuicao_separa_cliente_sem_mutar_o_resultado_original():
    from athenix.segunda_leitura import atribuir_responsaveis

    result, review, context = attribution_fixture()
    before = copy.deepcopy(result)
    separated = atribuir_responsaveis(result, review, context)
    assert separated["por_norma"]["norma"]["possiveis_obrigacoes_cliente"] == 1
    assert separated["grupos_responsavel"]["agente_regulado"] == ["ia1"]
    assert separated["itens"][0]["possivel_obrigacao_cliente"]
    assert result == before


def test_atribuicao_nao_inclui_aneel_governo_outros_na_contagem_do_cliente():
    from athenix.segunda_leitura import atribuir_responsaveis, chave_atribuicao

    result, review, context = attribution_fixture()
    text = "A ANEEL deverá fiscalizar as distribuidoras e publicar os resultados."
    item = result["itens"][0]
    item["literal"] = text
    item["interpretacao_ia"] = {
        "subject": "A ANEEL",
        "action": "fiscalizar e publicar",
        "object": "resultados",
    }
    e = context["docs"]["norma"]["extraction"]
    e["units"][0].update(text=text, end=len(text))
    e["source"]["key"] = key(text)
    context["docs"]["norma"]["reference_key"] = normalizar(text, espacos="nenhum", caixa=True)[0]
    r = review["atribuicoes"][0]
    r.update(
        grupo="aneel_governo_outros",
        responsavel="ANEEL",
        chave_conteudo=chave_atribuicao(item),
        fundamento="ANEEL fiscaliza; distribuidoras são o objeto, não o sujeito do dever.",
        evidencias=[{"unit_id": "u1", "quote": text}],
    )
    separated = atribuir_responsaveis(result, review, context)
    assert separated["por_norma"]["norma"]["possiveis_obrigacoes_cliente"] == 0
    assert separated["por_norma"]["norma"]["aneel_governo_outros"] == 1
    assert not separated["itens"][0]["possivel_obrigacao_cliente"]


def test_atribuicao_desatualizada_ou_sem_cobertura_e_bloqueada():
    from athenix.segunda_leitura import atribuir_responsaveis

    result, review, context = attribution_fixture()
    with pytest.raises(ValueError, match="exatamente"):
        atribuir_responsaveis(result, dict(review, atribuicoes=[]), context)
    result["itens"][0]["interpretacao_ia"]["subject"] = "Outro sujeito"
    with pytest.raises(ValueError, match="Sugestão mudou"):
        atribuir_responsaveis(result, review, context)


def test_citacao_de_contexto_inventada_nao_sustenta_atribuicao():
    from athenix.segunda_leitura import atribuir_responsaveis

    result, review, context = attribution_fixture()
    review["atribuicoes"][0]["evidencias"][0]["quote"] = (
        "O governo deverá realizar uma tarefa inexistente."
    )
    with pytest.raises(ValueError, match="citação literal"):
        atribuir_responsaveis(result, review, context)


def test_manifesto_documental_tem_64_ids_distintos_e_fontes_de_contexto():
    import json
    from pathlib import Path

    path = Path(__file__).parents[1] / "docs/ensaios/responsaveis_segunda_leitura.json"
    rows = json.loads(path.read_text(encoding="utf-8"))["atribuicoes"]
    assert len({r["id"] for r in rows}) == len(rows) == 64
    assert sum(r["grupo"] == "agente_regulado" for r in rows) == 30
    assert all(r["evidencias"] and len(r["chave_conteudo"]) == 64 for r in rows)
    assert all(r["grupo"] in {"agente_regulado", "aneel_governo_outros"} for r in rows)
