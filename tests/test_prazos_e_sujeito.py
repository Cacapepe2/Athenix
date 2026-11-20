"""Data-base dos prazos (trava), sujeito e modalidade herdados do caput, e citação das obrigações, com
trechos reais da RN 1.137/2025 e da REN 1.174/2026."""

import json
from pathlib import Path

import pytest

from athenix import plano, structure

ROOT = Path(__file__).resolve().parents[1]
P1137 = json.loads((ROOT / "landing/src/content/plano-rn1137.json").read_text(encoding="utf-8"))
P1174 = json.loads((ROOT / "landing/src/content/plano-ren1174.json").read_text(encoding="utf-8"))

# Cabeçalho do DOU (com "Diário Oficial da União" antes do título), data de outro ato e vigência da REN 1.174.
TEXTO_1174 = (
    "Serviços Diário Oficial da União\n"
    "RESOLUÇÃO NORMATIVA Nº 1.174, DE 27 DE OUTUBRO DE 2026\n"
    "Publicado em: 04/11/2026\n"
    "Art. 14. No caso de unidade consumidora que tenha exercido a opção do art. 166 para migração ao ACL "
    "antes da vigência do Decreto nº 13.097, de 12 de agosto de 2026, o consumidor deve ser notificado "
    "em até 90 dias da publicação desta Resolução.\n"
    "Art. 18. Esta Resolução entra em vigor na data de sua publicação e produz efeitos:\n"
)


def test_data_de_outro_ato_nao_vira_vigencia_nem_publicacao_da_norma():
    datas = {(d["kind"], d["date"]) for d in structure.act_dates(TEXTO_1174)}
    assert ("signature", "2026-10-27") in datas  # data do título é de ASSINATURA
    assert ("publication", "2026-11-04") in datas
    assert ("effective", "2026-11-04") in datas  # Art. 18: em vigor na data da publicação
    assert not any(
        d[1] == "2026-08-12" for d in datas
    )  # "vigência do Decreto nº 13.097": outro ato
    assert not any(k == "publication" and v == "2026-10-27" for k, v in datas)


def _extraction(publicacoes):
    return {"dates": [{"kind": "publication", "date": d} for d in publicacoes]}


def test_trava_prazo_com_data_base_anterior_a_publicacao_gera_erro():
    ruim = [{"deadlines": [{"date": "2026-11-10", "base": "2026-08-12", "event": "Vigência da norma", "quote": "I - 90 dias"}]}]  # fmt: skip
    with pytest.raises(ValueError, match="anterior à publicação"):
        plano.validar_bases_dos_prazos(ruim, _extraction(["2026-11-04"]))
    bom = [{"deadlines": [{"date": "2027-02-02", "base": "2026-11-04", "event": "Vigência da norma", "quote": "I - 90 dias"}]}]  # fmt: skip
    plano.validar_bases_dos_prazos(bom, _extraction(["2026-11-04"]))
    # prazo contado de OUTRO evento (sem relação com a publicação desta norma) não é checado
    outro = [{"deadlines": [{"date": "2026-01-10", "base": "2026-01-01", "event": "Publicação das instruções", "quote": "x"}]}]  # fmt: skip
    plano.validar_bases_dos_prazos(outro, _extraction(["2026-11-04"]))


def test_json_da_ren_1174_nao_tem_prazo_contado_de_antes_da_publicacao():
    pub = P1174["norma"]["vigencia"]
    assert pub == "2026-11-04"
    com_base = [o for o in P1174["obrigacoes"] if o["prazo"]["data"]]
    assert com_base
    for o in com_base:
        assert o["prazo"]["base"] and o["prazo"]["base"] >= pub, o["dispositivo"]
        assert (
            o["prazo"]["base"] != "2026-08-12"
        )  # a data do Decreto nº 13.097, lida antes como vigência
    assert P1137["resumo"]["por_situacao"]["vencida"] == 6  # a RN 1.137 não mudou


def caput(texto, sujeito, modalidade="duty"):
    return {"subject": sujeito, "modality": modalidade, "action": texto}


@pytest.mark.parametrize(
    ("caput_texto", "linha", "esperado"),
    [
        # REN 1.174, art. 13, § 2º, I: inciso sem sujeito próprio; quem pede a redução é o consumidor
        (
            "§ 2º A solicitação de redução do montante de energia elétrica contratado por consumidor livre e especial no CCER deve ser realizada com a antecedência de pelo menos:",
            caput(
                "I - 90 dias: para o consumidor do subgrupo AS ou A4; ou",
                "A solicitação de redução do montante de energia elétrica contratado por consumidor livre e especial no CCER",
            ),  # fmt: skip
            "dever_de_outro_agente",
        ),
        # REN 1.174, art. 4º, I, a): alínea sob "a distribuidora deve apresentar à ANEEL": dever dela
        (
            "I - a distribuidora deve apresentar à ANEEL, previamente ao início, a proposta do Sandbox contendo:",
            caput("a) prazo;", "a distribuidora"),
            "dever",
        ),
        # REN 1.174: "A distribuidora não deve alterar o faturamento até a manifestação do consumidor"
        (
            "Art. 14. No caso de unidade consumidora que receba o benefício tarifário, o consumidor deve ser notificado:",
            caput(
                "§ 4º A distribuidora não deve alterar o faturamento realizado até a manifestação do consumidor",
                "A distribuidora não",
            ),  # fmt: skip
            "dever",
        ),
        # REN 1.174: sujeito "não identificado" herda o da distribuidora no caput
        (
            "Art. 166-A. A distribuidora deve responder ao consumidor no prazo de dez dias, observando:",
            caput(
                "I - deve garantir a mesma titularidade no CUSD e nos contratos no ACL; e",
                "não identificado",
            ),
            "dever",
        ),
        # RN 1.137, item 139, alínea b: "a cessionária deverá manter dossiê ... poderão ser requisitados"
        (
            "139. Os contratos de Cessão Emergencial entre distribuidoras deverão conter:",
            caput(
                "b) a cessionária deverá manter dossiê individualizado em sua sede, que poderão ser requisitados pela fiscalização",
                "a cessionária",
            ),  # fmt: skip
            "dever",
        ),
        # RN 1.137, item 111: direito do consumidor; item 125: faculdade; art. 10, I: competência da ANEEL
        (
            "",
            caput(
                "111. O consumidor e demais usuários podem, a qualquer tempo, solicitar a suspensão",
                "O consumidor e demais usuários",
                "permission",
            ),
            "direito_de_terceiro",
        ),  # fmt: skip
        (
            "",
            caput(
                "125. As distribuidoras ou transmissoras podem promover o auxílio",
                "As distribuidoras ou transmissoras",
                "permission",
            ),
            "faculdade",
        ),  # fmt: skip
        (
            "",
            caput(
                "I - articular, coordenar, monitorar e supervisionar as providências",
                "A Agência",
                "permission",
            ),
            "competencia_aneel",
        ),  # fmt: skip
    ],
)
def test_inciso_sem_sujeito_proprio_herda_o_do_caput(caput_texto, linha, esperado):
    assert plano.natureza(linha, caput_texto) == esperado


def test_totais_reprocessados_das_duas_normas():
    assert P1137["resumo"]["aplicaveis"] == 155  # igual ao total anterior à herança do caput
    assert P1174["resumo"]["aplicaveis"] == len(P1174["obrigacoes"])
    r = P1174["resumo"]
    assert r["identificadas"] == r["aplicaveis"] + r["fora_do_perfil"] + r["outros_dispositivos"]
    # o inciso "90 dias: para o consumidor..." saiu dos deveres da distribuidora
    assert not any(
        o["titulo_completo"].startswith("90 dias: para o consumidor") for o in P1174["obrigacoes"]
    )
    assert any(
        "90 dias: para o consumidor" in (o["trecho"] or "") for o in P1174["outros_dispositivos"]
    )


def test_toda_obrigacao_do_plano_tem_dispositivo_e_citacao_verificada():
    for plano_ in (P1137, P1174):
        for o in plano_["obrigacoes"]:
            assert o["unidade"] and o["dispositivo"] and o["trecho"], o["id"]
    # as duas que ficavam sem citação (itens 23-G e 23-H da RN 1.137) agora citam a 1ª frase do dispositivo
    g = [o for o in P1137["obrigacoes"] if (o["dispositivo"] or "").endswith(("23-G", "23-H"))]
    assert len(g) == 2 and all("informar e manter, por até cinco anos" in o["trecho"] for o in g)


def test_revisao_a_cada_periodo_de_12_meses_e_recorrencia_nao_prazo_unico():
    # REN 1.174, art. 13, § 3º (texto real): "maior que 12 meses" é limite de comparação e
    # "a cada período de 12 meses" é a periodicidade; nenhum dos dois é prazo para cumprir.
    from athenix import temporal

    texto = (
        "§ 3º No caso de período do CCER ser maior que 12 meses, deve ser permitida a revisão dos valores "
        "mensais de energia elétrica contratada a cada período de 12 meses."
    )
    regras = temporal.rules(texto, "u1", [{"kind": "publication", "date": "2026-11-04"}, {"kind": "effective", "date": "2026-11-04"}])  # fmt: skip
    assert regras and all(r["state"] == "recurring" for r in regras)
    assert not any(r.get("date") for r in regras)
    # prazo comum continua prazo: "em até 60 dias da publicação"
    comum = temporal.rules("A primeira reunião deverá ocorrer em até 60 dias da publicação desta Resolução.", "u2", [{"kind": "publication", "date": "2026-11-04"}])  # fmt: skip
    assert comum and comum[0]["date"] == "2027-01-03"


def test_art_13_par_3_da_ren_1174_e_recorrente_no_plano():
    o = next(x for x in P1174["obrigacoes"] if x["dispositivo"] == "Art. 13, § 3º")
    assert o["situacao"] == "recorrente" and o["prazo"]["data"] is None
    r = P1174["resumo"]["por_situacao"]
    assert r["recorrente"] == 2  # art. 11, VIII (semestral) e art. 13, § 3º (12 meses)
    assert sum(1 for x in P1174["obrigacoes"] if x["prazo"]["data"]) == 5
