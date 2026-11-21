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
    for o in P1174["obrigacoes"]:
        if o["prazo"]["data"]:
            assert o["prazo"]["base"] and o["prazo"]["base"] >= pub, o["dispositivo"]
            assert (
                o["prazo"]["base"] != "2026-08-12"
            )  # a data do Decreto nº 13.097, lida antes como vigência
    assert (
        P1137["resumo"]["por_situacao"]["vencida"] == 7
    )  # os 6 de antes + o art. 18 (na data de publicação)


def test_marco_direto_na_data_de_publicacao_vira_prazo_e_o_maior_entre_vira_condicional():
    # RN 1.137, art. 18: "devem ser implementadas na data de publicação" -> vencido desde 30/10/2025
    a18 = next(o for o in P1137["obrigacoes"] if o["dispositivo"] == "Art. 18")
    assert a18["situacao"] == "vencida" and a18["prazo"]["data"] == "2025-10-30"
    assert a18["prazo"]["base"] == "2025-10-30" and a18["prazo"]["texto"].startswith(
        "Vencido desde 30/10/2025"
    )
    # "entra em vigor na data de sua publicação" é vigência: não vira prazo de obrigação
    from athenix import temporal

    datas = [{"kind": "publication", "date": "2025-10-30"}]
    assert not temporal.rules(
        "Esta Resolução entra em vigor na data de sua publicação.", "u", datas
    )
    assert (
        temporal.rules(
            "As disposições devem ser implementadas na data de publicação desta Resolução Normativa.",
            "u",
            datas,
        )[0]["date"]
        == "2025-10-30"
    )
    # REN 1.174, art. 14, § 1º, II: o maior entre 12 meses da publicação e o prazo informado: sem data única
    a14 = next(o for o in P1174["obrigacoes"] if o["dispositivo"] == "Art. 14, § 1º, inciso II")
    assert (
        a14["prazo"]["data"] is None
        and a14["prazo"]["condicional"] is True
        and a14["situacao"] == "evento"
    )
    assert (
        "maior entre 12 meses da publicação (04/11/2027) e o prazo informado pela distribuidora"
        in a14["prazo"]["texto"]
    )
    texto = "a aplicação deve ser realizada até o maior prazo entre o prazo de doze meses da publicação desta Resolução e o prazo reduzido informado pela distribuidora"
    regra = temporal.rules(texto, "u", [{"kind": "publication", "date": "2026-11-04"}])[0]
    assert (
        regra["state"] == "conditional"
        and regra["date"] is None
        and regra["parcela_conhecida"] == "2027-11-04"
    )


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
    assert (
        P1137["resumo"]["aplicaveis"] == 153
    )  # 155 menos o art. 10, §§ 2º e 3º (competência da ANEEL)
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
    assert (
        sum(1 for x in P1174["obrigacoes"] if x["prazo"]["data"]) == 0
    )  # as 2 de adequação (art. 16) viraram transição; a reunião do grupo (art. 12, § 11) não é da distribuidora


@pytest.mark.parametrize(
    ("texto", "vira_dever"),
    [
        # casos reais da REN 1.174: a distribuidora age de forma explícita
        (
            "§ 4º Indeferida a migração, a solicitação feita pelo consumidor conforme art. 166 será encerrada pela distribuidora, não ocorrendo o encerramento do CCER.",
            True,
        ),
        (
            "Parágrafo único. Em caso de desistência da migração o CCER será mantido, devendo a distribuidora efetuar a cobrança no faturamento.",
            True,
        ),
        (
            "§ 5º A efetivação para retorno ao ACR somente será realizada pela distribuidora após notificação pela CCEE.",
            True,
        ),
        ("§ 3º A distribuidora efetuará a conciliação dos montantes no mês seguinte.", True),
        # futuro sem a distribuidora como agente: NÃO vira dever
        (
            "§ 4º Cada membro do grupo de trabalho terá dois suplentes, para efeitos de substituição em suas ausências.",
            False,
        ),
        (
            "§ 7º As despesas relacionadas à participação dos representantes correrão por conta de dotações orçamentárias.",
            False,
        ),
        (
            "§ 10. Até que a coordenação do grupo seja definida pelos participantes, a Abradee exercerá a coordenação de forma temporária.",
            False,
        ),
        (
            "§ 2º O grupo de trabalho será composto por, no mínimo, representantes das seguintes instituições:",
            False,
        ),
        # a distribuidora é só o objeto/lugar, quem age é a ANEEL
        (
            "114. A ANEEL estabelecerá procedimento para comunicação das situações de crise enfrentadas pelas distribuidoras.",
            False,
        ),
        ("II - pelas distribuidoras:", False),
        (
            "I - do recebimento da notificação eletrônica pela distribuidora feita pelo sistema da CCEE; e",
            False,
        ),
    ],
)
def test_futuro_so_vira_dever_quando_a_distribuidora_age_explicitamente(texto, vira_dever):
    from athenix import proposals

    unidade = {"id": "u1", "parent": None, "kind": "paragraph", "text": texto}
    candidatos = proposals.rule_candidates({"units": [unidade]})
    assert bool(candidatos) is vira_dever
    if vira_dever:
        assert candidatos[0]["subject"] == "a distribuidora" or proposals.DUTY.search(texto)


def test_nada_some_em_silencio_na_ren_1174_e_a_rn_1137_nao_muda_de_contagem():
    assert P1137["resumo"]["aplicaveis"] == 153
    assert P1174["resumo"]["aplicaveis"] == 83
    s10 = [
        o
        for o in P1174["sem_dever_identificado"]
        if "Abradee exercerá a coordenação" in o["trecho"]
    ]
    assert len(s10) == 1 and s10[0]["motivo"] == "sem dever identificado"
    assert s10[0]["dispositivo"] == "Art. 12, § 10"
    ids = [
        o["id"]
        for p in (P1137, P1174)
        for k in ("obrigacoes", "outros_dispositivos", "sem_dever_identificado")
        for o in p[k]
    ]
    assert len(ids) == len(set(ids))


ART_10_3 = "§3º A Portaria que instituir Comitê de Crise deverá atender as demais disposições da Portaria nº 6.803, de 30 de janeiro de 2023, no que couber."
CAPUT_ART_10 = "Art. 10. A Agência poderá instituir Comitê de Crise para articular, coordenar e monitorar as providências em eventos climáticos extremos."


def test_art_10_par_3_da_rn_1137_e_competencia_da_aneel_nao_dever_da_distribuidora():
    # o emissor é a Portaria da Agência (o caput: "A Agência poderá instituir..."); nada de R$ 50 mi para a distribuidora
    linha = {
        "subject": "A Portaria que instituir Comitê de Crise",
        "modality": "duty",
        "action": ART_10_3,
    }
    assert plano.natureza(linha, CAPUT_ART_10) == "competencia_aneel"
    assert (
        plano.natureza({"subject": "A Portaria", "modality": "duty", "action": ART_10_3}, "")
        == "competencia_aneel"
    )
    # § 2º: "O Comitê de Crise deverá ser estabelecido por Portaria emitida pelo Diretor-Geral": herda o emissor do caput
    p2 = {
        "subject": "O Comitê de Crise",
        "modality": "duty",
        "action": "§ 2º O Comitê de Crise deverá ser estabelecido por Portaria emitida pelo Diretor-Geral.",
    }
    assert plano.natureza(p2, CAPUT_ART_10) == "competencia_aneel"
    # a distribuidora como sujeito continua dever, mesmo sob caput da Agência
    assert (
        plano.natureza(
            {
                "subject": "As distribuidoras",
                "modality": "duty",
                "action": "As distribuidoras deverão informar",
            },
            CAPUT_ART_10,
        )
        == "dever"
    )
    # no plano real: sai dos deveres e vai para "Outros dispositivos" (competência da ANEEL), com a citação
    deveres = {o["dispositivo"] for o in P1137["obrigacoes"]}
    assert "Art. 10, §3º" not in deveres and "Art. 10, § 2º" not in deveres
    outros = {o["dispositivo"]: o for o in P1137["outros_dispositivos"]}
    assert outros["Art. 10, §3º"]["natureza"] == "competencia_aneel"
    assert "Portaria nº 6.803" in outros["Art. 10, §3º"]["trecho"]


def test_sujeito_implicito_quando_a_distribuidora_nao_esta_escrita_no_texto_nem_no_caput():
    caput_dist = "Art. 5º As distribuidoras deverão manter canal de atendimento, observando:"
    # explícito: a distribuidora é o sujeito (próprio ou herdado do caput) ou age "pela distribuidora"
    assert not plano.sujeito_implicito(
        {"subject": "As distribuidoras", "action": "As distribuidoras deverão informar"}, ""
    )
    assert not plano.sujeito_implicito(
        {"subject": "não identificado", "action": "I - o prazo máximo"}, caput_dist
    )
    assert not plano.sujeito_implicito(
        {"subject": "A solicitação", "action": "A solicitação será encerrada pela distribuidora"},
        "",
    )
    # implícito: sujeito impessoal de norma dirigida às distribuidoras
    assert plano.sujeito_implicito(
        {
            "subject": "O plano de contingência",
            "action": "O plano de contingência deve ser elaborado",
        },
        "",
    )
    # contagem real, por norma (89 e 45 explícitos; 64 e 38 implícitos): a mesma divisão da leitura estrita medida antes
    for p, total, implicitos in ((P1137, 153, 64), (P1174, 83, 38)):
        assert len(p["obrigacoes"]) == total
        assert sum(1 for o in p["obrigacoes"] if o["sujeito_implicito"]) == implicitos
