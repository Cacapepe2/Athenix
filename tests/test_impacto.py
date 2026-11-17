"""Módulo de impacto: valores fixos, nenhum número sem premissa e fonte, perfil vazio."""

import copy
import hashlib
from datetime import date
from pathlib import Path

import pytest

from athenix import impacto
from conftest import propose

PARAMS = impacto.carregar()
HOJE = "2026-11-11"


def row(action, deadlines=(), modality="duty", subject="As distribuidoras", rid="o1"):
    return {
        "id": rid,
        "action": action,
        "subject": subject,
        "modality": modality,
        "status": "detected",
        "evidence": [{"unit_id": "u1", "quote": action}],
        "anchors": [{"state": "verified", "unit_id": "u1", "quote": action}],
        "deadlines": list(deadlines),
        "document_id": "d1",
        "document_title": "Norma",
    }


PLANO = row("As distribuidoras devem manter Plano de Contingência atualizado e publicado.")


def avaliar(rows, **form):
    return impacto.avaliar(PARAMS, rows, impacto.perfil({"data_referencia": HOJE} | form))


def test_parameter_file_only_has_verified_current_wordings():
    for pid, p in PARAMS["parametros"].items():
        assert p["ancora"] == "verified" and not p["revogado"], pid
    limits = [PARAMS["parametros"][f"limite_grupo_{g}"]["percentuais"] for g in impacto.GRUPOS]
    # Lidos do texto do Art. 8º da REN 846 compilada (sha256 d8b6fae9…), não digitados.
    assert limits == [[0.125], [0.25], [0.5], [1.0], [2.0]]
    fontes = Path(__file__).parent / "fontes_impacto"
    for fonte in PARAMS["fontes"].values():
        path = Path(__file__).parents[1] / fonte["arquivo"]
        if path.exists():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == fonte["sha256"]
        else:
            assert (
                path.parent.name == fontes.name
            )  # só as fontes de terceiros podem faltar (fora do repo)


def test_list_inside_an_infraction_is_not_an_infraction():
    # Art. 9º, IV ("cadastro relativo a:") enumera I a IV; antes viravam infrações com rótulo repetido.
    rotulos = [i["dispositivo"] for i in PARAMS["infracoes"]]
    assert len(rotulos) == len(set(rotulos)) == 109
    iv = next(i for i in PARAMS["infracoes"] if i["dispositivo"] == "Art. 9º, IV")
    assert [x["dispositivo"] for x in iv["itens"]] == [
        f"Art. 9º, IV, {n}" for n in ("I", "II", "III", "IV")
    ]
    assert all(x["ancora"] == "verified" for x in iv["itens"])


def test_fixed_values_explicit_group_with_base_and_premises():
    item = avaliar([PLANO], segmento="distribuicao", base="1.000.000,00", reincidencias="1",
                   fracao_valor_base="50")["itens"][0]  # fmt: skip
    m = item["multa"]
    assert [e["dispositivo"] for e in item["enquadramentos"]] == ["Art. 12, XXVI"]
    assert m["grupos"] == ["IV"] and m["agravantes_pct"] == 40
    assert m["maximo"] == {"com_teto": 1.0, "sem_teto": pytest.approx(1.4)}
    assert m["provavel"] == {"com_teto": pytest.approx(0.7), "sem_teto": pytest.approx(0.7)}
    assert m["reais"]["maximo"] == {"com_teto": 10000.0, "sem_teto": pytest.approx(14000.0)}
    assert m["reais"]["provavel"]["com_teto"] == pytest.approx(7000.0)
    assert item["confianca"] == "médio"  # grupo só por coincidência de termos


def test_fixed_values_all_aggravating_and_cap_scenarios():
    form = dict(base="1000000", reincidencias="3", tn_nao_atendidos="2", antecedentes="2",
                soma_antecedentes_pct="1,5", fracao_valor_base="50", atenuante="espontanea",
                grupo_o1="IV")  # fmt: skip
    m = avaliar([PLANO], **form)["itens"][0]["multa"]
    # 120% (reincidência, teto) + 2 × 15% (TN) + 2 × 4% (antecedentes, faixa b) = 158%.
    assert m["agravantes_pct"] == pytest.approx(158)
    assert m["maximo"]["sem_teto"] == pytest.approx(2.58)
    assert m["maximo"]["com_teto"] == 1.0
    # Provável: 0,5% × 2,58 = 1,29% → com teto 1% → atenuante de 95%.
    assert m["provavel"]["com_teto"] == pytest.approx(0.05)
    assert m["provavel"]["sem_teto"] == pytest.approx(0.0645)
    assert avaliar([PLANO], **form)["itens"][0]["confianca"] == "alto"
    # 2,58% fica abaixo do teto legal (3%): o valor não muda e não é marcado como limitado.
    assert not m["limitado_teto_legal"] and m["teto_legal_pct"] == 3.0


def test_report_opens_with_obligations_naming_the_segment():
    vencida = [{"date": "2026-01-28", "state": "provisional"}]
    trans = row(
        "As transmissoras devem implementar o plano em 90 dias.",
        vencida,
        subject="As transmissoras",
        rid="t1",
    )
    trans_dup = row(
        "As transmissoras devem implementar o plano em 90 dias.",
        subject="As transmissoras",
        rid="t2",
    )
    pv = row(
        "A transmissora deve manter a disponibilidade das instalações.",
        subject="A transmissora",
        rid="t3",
    )
    dist = row("As distribuidoras devem publicar o plano.", vencida, rid="d1")
    gen = row("Os agentes devem informar a ANEEL.", subject="Os agentes", rid="g1")
    gen2 = row("Os agentes devem registrar as ocorrências.", subject="Os agentes", rid="g2")
    rows = [dist, gen, gen2, trans, trans_dup, pv]
    grupos = {f"grupo_{r['id']}": "IV" for r in rows}
    p = impacto.perfil({"data_referencia": HOJE} | grupos)  # segmento vazio: transmissoras primeiro
    d = impacto.destaques(impacto.avaliar(PARAMS, rows, p), p)
    ids = [x["item"]["row"]["id"] for x in d["itens"]]
    assert d["segmento"] == "transmissao" and ids[:2] == ["t1", "t3"]
    assert "t2" not in ids and "d1" not in ids  # texto repetido uma vez; distribuidora fora
    assert [x["especifica"] for x in d["itens"]] == [True, True, False]  # completa até 3
    assert d["itens"][0]["frase"].startswith("Faça isto primeiro")
    assert [i["row"]["id"] for i in d["parcela_variavel"]] == ["t3"]
    p = impacto.perfil({"data_referencia": HOJE, "segmento": "distribuicao"} | grupos)
    d = impacto.destaques(impacto.avaliar(PARAMS, rows, p), p)
    assert [x["item"]["row"]["id"] for x in d["itens"]][0] == "d1" and d["parcela_variavel"] == []


def test_only_availability_of_installations_counts_as_revenue_risk():
    p = impacto.perfil({"segmento": "transmissao"})
    receita = {
        texto: any(c == "receita" for c, _ in impacto.classificar(row(texto), texto, p))
        for texto in (
            "A transmissora deve manter a disponibilidade das instalações.",
            "A transmissora deve evitar a indisponibilidade de equipamentos.",
            # Textos reais da RN 1.137 que antes caíam como Parcela Variável:
            "d) Infraestrutura de Apoio: Garantir a disponibilidade de recursos e infraestrutura",
            "§ 5º O atendimento telefônico deve ter disponibilidade ininterrupta durante 24 horas",
        )
    }
    assert list(receita.values()) == [True, True, False, False]


def test_same_rule_in_annex_and_new_wording_block_appears_once():
    texto = (
        "c) As cessões emergenciais entre distribuidoras e transmissoras devem ser reembolsadas "
        * 3
    )
    a = row(texto + "preservando a individualidade.", subject="As transmissoras", rid="a1")
    b = row(
        texto + "preservando a individualidade. ........”(NR)", subject="As transmissoras", rid="b1"
    )
    p = impacto.perfil({"data_referencia": HOJE, "grupo_a1": "IV", "grupo_b1": "IV"})
    d = impacto.destaques(impacto.avaliar(PARAMS, [a, b], p), p)
    assert [x["item"]["row"]["id"] for x in d["itens"]] == ["a1"]


def units(*textos):
    return [{"id": f"u{i}", "text": t} for i, t in enumerate(textos)]


def test_same_act_cited_with_different_dates_is_flagged():
    # D3 como regra geral: vale para qualquer ato, não só para a RN 948.
    alertas = impacto.citacoes_divergentes(units(
        "Art. 1º Conforme a Resolução Normativa nº 948, de 16 de novembro de 2021, a distribuidora",
        "Art. 2º A Resolução Normativa nº 948, de 21 de novembro, passa a vigorar com",
        "Art. 3º Nos termos da Lei nº 9.427, de 26 de dezembro de 1996, e da Lei nº 9.427/1997",
    ))  # fmt: skip
    assert [a["ato"] for a in alertas] == ["Resolução Normativa nº 948", "Lei nº 9427"]
    assert [c["unit_id"] for c in alertas[0]["citacoes"]] == ["u0", "u1"]
    assert "de 21 de novembro" in alertas[0]["citacoes"][1]["trecho"]


def test_consistent_or_undated_citations_are_not_flagged():
    assert not impacto.citacoes_divergentes(units(
        "Art. 1º A REN nº 1.000, de 7 de dezembro de 2021, e a Resolução Normativa nº 1.000.",
        "Art. 2º A Resolução Normativa nº 1.000, de 7 de dezembro de 2021, também se aplica.",
        "Art. 3º A Resolução Normativa nº 1.001, de 7 de dezembro de 2021, no mesmo dia.",
        "Art. 4º A Resolução Normativa nº 1.000/2021 e a Resolução Normativa nº 1.000, de 7 de dezembro",
    ))  # fmt: skip
    riscado = units(
        "Art. 1º Lei nº 1, de 2 de maio de 2000", "Art. 2º Lei nº 1, de 3 de maio de 2000"
    )
    riscado[1]["struck"] = "revoked"
    assert not impacto.citacoes_divergentes(riscado)


def test_real_rn1137_flags_rn948_dates():
    from athenix.config import Settings
    from athenix.poc import reader

    pdf = Path(__file__).parent / "norma_poc" / "ren20251137.pdf"
    extraction = reader.read_pdf(pdf, Settings())["extraction"]
    alertas = impacto.citacoes_divergentes(extraction["units"])
    rn948 = next(a for a in alertas if a["ato"] == "Resolução Normativa nº 948")
    datas = {c["data"] for c in rn948["citacoes"]}
    assert {(16, "novembro", "2021"), (21, "novembro", None)} <= datas


MAX_V = dict(reincidencias="10", tn_nao_atendidos="20", antecedentes="50", grupo_o1="V")


def test_legal_cap_follows_the_date_of_the_infraction():
    vig = PARAMS["parametros"]["teto_legal_vigencia"]
    # Lei 15.269/2025, Art. 24, IV + "publicado no DOU de 25.11.2025" (planalto.gov.br).
    assert vig["ancora"] == "verified" and vig["data"] == "2025-11-25"
    assert PARAMS["parametros"]["teto_legal_anterior"]["percentuais"] == [2.0]
    antes = row(PLANO["action"], [{"date": "2025-10-01", "state": "provisional"}])
    depois = row(PLANO["action"], [{"date": "2026-01-28", "state": "provisional"}])
    m_antes = avaliar([antes], **MAX_V)["itens"][0]["multa"]
    m_depois = avaliar([depois], **MAX_V)["itens"][0]["multa"]
    assert (
        m_antes["maximo"]["sem_teto"] == 2.0
        and m_antes["teto_legal"]["parametro"] == "teto_legal_anterior"
    )
    assert (
        m_depois["maximo"]["sem_teto"] == 3.0
        and m_depois["teto_legal"]["parametro"] == "teto_legal_lei"
    )
    texto = next(
        pr["texto"] for pr in m_antes["premissas"] if pr["parametro"] == "teto_legal_anterior"
    )
    assert "antes de 25/11/2025" in texto and "data do prazo" in texto
    assert any(pr["texto"] == impacto.AVISO_DATA for pr in m_antes["premissas"])
    # Sem prazo: data de referência do perfil, dito na premissa.
    sem_prazo = avaliar([PLANO], **MAX_V)["itens"][0]["multa"]
    assert any("data de referência do perfil" in pr["texto"] for pr in sem_prazo["premissas"])


def test_unconfirmed_effective_date_shows_both_limits():
    sem_vig = copy.deepcopy(PARAMS)
    sem_vig["parametros"]["teto_legal_vigencia"]["ancora"] = "pending"
    perfil = impacto.perfil({"data_referencia": HOJE} | MAX_V)
    m = impacto.avaliar(sem_vig, [PLANO], perfil)["itens"][0]["multa"]
    assert m["maximo"]["sem_teto"] == 3.0 and m["teto_legal"]["alternativo_pct"] == 2.0
    assert any("não confirmado" in pr["texto"] and "2%" in pr["texto"] for pr in m["premissas"])


def test_gross_revenue_converts_the_legal_cap_d6():
    com = avaliar([PLANO], base="1000000", faturamento="1500000", **MAX_V)["itens"][0]["multa"]
    # 3% de R$ 1,5 mi = R$ 45 mil = 4,5% da base (ROL) de R$ 1 mi.
    assert com["teto_legal_pct"] == pytest.approx(4.5) and not com["teto_legal"]["subestimado"]
    assert com["reais"]["maximo"]["sem_teto"] == pytest.approx(45000.0)
    sem = avaliar([PLANO], base="1000000", **MAX_V)["itens"][0]["multa"]
    assert sem["teto_legal"]["subestimado"]
    assert any("possivelmente subestimado" in pr["texto"] for pr in sem["premissas"])
    with pytest.raises(ValueError):
        impacto.perfil({"faturamento": "-1"})


def test_legal_cap_limits_both_scenarios():
    legal = PARAMS["parametros"]["teto_legal_lei"]
    # Lido do Art. 3º, X da Lei 9.427/1996 (planalto.gov.br, sha256 ff948e34…), não digitado.
    assert legal["ancora"] == "verified" and legal["percentuais"] == [3.0]
    form = dict(base="1000000", reincidencias="10", tn_nao_atendidos="20", antecedentes="50",
                fracao_valor_base="100", grupo_o1="V")  # fmt: skip
    m = avaliar([PLANO], **form)["itens"][0]["multa"]
    # Antes: 2% × (1 + 470%) = 11,4% da base no cenário sem teto do grupo. Depois: 3% (teto legal).
    assert m["agravantes_pct"] == pytest.approx(470)
    assert m["maximo"] == {"com_teto": 2.0, "sem_teto": 3.0} and m["limitado_teto_legal"]
    assert m["provavel"]["sem_teto"] == 3.0
    assert m["reais"]["maximo"]["sem_teto"] == pytest.approx(30000.0)
    assert any(pr["parametro"] == "teto_legal_lei" for pr in m["premissas"])
    sem_lei = copy.deepcopy(PARAMS)
    sem_lei["parametros"]["teto_legal_lei"]["ancora"] = "pending"
    perfil = impacto.perfil({"data_referencia": HOJE} | form)
    m = impacto.avaliar(sem_lei, [PLANO], perfil)["itens"][0]["multa"]
    assert m["maximo"]["sem_teto"] == pytest.approx(11.4) and m["teto_legal_pct"] is None


def test_empty_profile_gives_wide_range_in_percent_and_low_confidence():
    obrigacao = row("A distribuidora deve enviar o relatório mensal à ANEEL.")
    result = avaliar([obrigacao])
    item = result["itens"][0]
    m = item["multa"]
    assert m["grupos"] == list(impacto.GRUPOS)
    assert (m["piso_teto_pct"], m["teto_pct"], m["minimo_pct"]) == (0.125, 2.0, 0.0)
    assert m["provavel"] is None and "reais" not in m
    # Enquadramento desconhecido: fora da fila, em "Verificar enquadramento", faixa larga visível.
    assert result["ranking"] == [] and result["verificar"] == [item] and result["frases"] == []
    assert item["confianca"] == "baixo" and "Enquadramento desconhecido" in item["motivo_confianca"]
    # Com o grupo informado entra na fila; sem a base, a confiança segue baixa e a frase pede a base.
    com_grupo = avaliar([obrigacao], grupo_o1="II")
    assert com_grupo["ranking"][0]["confianca"] == "baixo"
    assert "base de cálculo não informada" in com_grupo["ranking"][0]["motivo_confianca"]
    assert "informe a base" in com_grupo["frases"][0]


@pytest.mark.parametrize("broken", ["pending", "revoked"])
def test_no_value_without_verified_current_source(broken):
    params = copy.deepcopy(PARAMS)
    if broken == "pending":
        params["parametros"]["limite_grupo_IV"]["ancora"] = "pending"
    else:
        params["parametros"]["limite_grupo_IV"]["revogado"] = "revoked"
    result = impacto.avaliar(params, [PLANO], impacto.perfil({"base": "1000"}))
    assert result["itens"][0]["multa"]["estimavel"] is False
    assert result["ranking"] == []


def test_every_premise_points_to_a_parameter_or_the_user():
    form = dict(base="1000", reincidencias="1", antecedentes="1", fracao_valor_base="10",
                atenuante="ate_tn", grupo_o1="II")  # fmt: skip
    m = avaliar([PLANO], **form)["itens"][0]["multa"]
    for premissa in m["premissas"]:
        assert premissa["parametro"] in PARAMS["parametros"], premissa


def test_unverified_obligation_is_out_of_calculation():
    unverified = row("A distribuidora deve publicar o plano.") | {"anchors": [{"state": "pending"}]}
    item = avaliar([unverified], base="1000")["itens"][0]
    assert item["multa"]["estimavel"] is False and item["confianca"] == "baixo"


def test_classification_and_applicability():
    p = impacto.perfil({"segmento": "transmissao"})
    assert (
        impacto.classificar(row("pode utilizar rádio", modality="permission"), "", p)[0][0]
        == "nenhuma"
    )
    cats = [
        c
        for c, _ in impacto.classificar(
            row("deve implantar sistema e informar à ANEEL"), "Parcela Variável", p
        )
    ]
    assert cats == ["multa", "adequacao", "receita", "fiscalizacao"]
    assert impacto.aplicabilidade(row("x", subject="As distribuidoras"), p)[0] is False
    assert impacto.aplicabilidade(row("x", subject="A transmissora"), p)[0] is True


def test_urgency_and_priority_rule():
    vencida = row("deve A", [{"date": "2026-01-28", "state": "provisional"}], rid="a")
    proxima = row("deve B", [{"date": "2026-12-01", "state": "provisional"}], rid="b")
    sem_data = row("deve C", [{"state": "awaiting_event"}], rid="c")
    result = avaliar([sem_data, proxima, vencida], grupo_a="IV", grupo_b="IV", grupo_c="IV")
    # Mesma exposição: o peso do prazo decide (vencida 1, até 90 dias 0,8, sem data 0,3).
    assert [i["row"]["id"] for i in result["ranking"]] == ["a", "b", "c"]
    assert "há 287 dias" in result["ranking"][0]["urgencia"]["texto"]
    assert "faltam 20 dias" in result["ranking"][1]["urgencia"]["texto"]
    assert result["frases"][0].startswith("Faça isto primeiro: deve A")


@pytest.mark.parametrize(
    "form",
    [
        {"segmento": "geracao"},
        {"base": "-1"},
        {"grupo_x": "VI"},
        {"reincidencias": "1,5"},
        {"base": "nan"},
    ],
)
def test_profile_validation(form):
    with pytest.raises(ValueError):
        impacto.perfil(form)


def test_brazilian_number_format():
    assert impacto.perfil({"base": "R$ 1.234.567,89"})["base"] == pytest.approx(1234567.89)
    assert impacto.perfil({"data_referencia": HOJE})["data_referencia"] == date(2026, 11, 11)


def test_rule_change_alert_and_screens(env):
    app, client, settings = env
    norma = (
        "<html><body><p>Art. 1º A distribuidora deve manter Plano de Contingência atualizado.</p>"
        "<p>Art. 2º A Resolução Normativa nº 846, de 11 de junho de 2019, passa a vigorar com a "
        "seguinte redação:</p><p>Art. 3º Aplica-se a Resolução Normativa nº 948, de 16 de novembro "
        "de 2021, e a Resolução Normativa nº 948, de 21 de novembro.</p></body></html>"
    ).encode()
    propose(env, norma)
    page = client.get("/impacto?base=1000000&segmento=distribuicao")
    assert page.status_code == 200
    assert "altera a régua de penalidade" in page.text and "Art. 12, XXVI" in page.text
    assert "Citação inconsistente na fonte" in page.text and "de 21 de novembro" in page.text
    assert "a confirmar com a fonte oficial da ANEEL" in page.text and impacto.AVISO in page.text
    report = client.get("/impacto/relatorio?base=1000000&download=1")
    assert report.status_code == 200 and "attachment" in report.headers["content-disposition"]
    assert report.text.count(impacto.AVISO) >= 2
    assert client.get("/impacto?base=-5").status_code == 400
    client.cookies.clear()
    assert client.get("/impacto").status_code == 401


def test_illustrative_profile_is_labeled_and_traceable(env):
    app, client, settings = env
    propose(
        env,
        "<html><body><p>Art. 1º A distribuidora deve manter Plano de Contingência atualizado.</p></body></html>".encode(),
    )
    demo = impacto.perfil_ilustrativo()
    assert demo["segmento"] == "distribuicao" and float(demo["base"]) > 0 and demo["origem_base"]
    redirect = client.get("/impacto?perfil=ilustrativo", follow_redirects=False)
    assert redirect.status_code == 303 and f"base={demo['base']}" in redirect.headers["location"]
    page = client.get(redirect.headers["location"])
    assert "Perfil ilustrativo" in page.text and "possivelmente subestimado" in page.text
    report = client.get(redirect.headers["location"].replace("/impacto?", "/impacto/relatorio?"))
    assert "PERFIL ILUSTRATIVO" in report.text
    assert impacto.AVISO_DATA in page.text and impacto.AVISO_DATA in report.text
    for html in (page.text, report.text):
        assert "Verificar enquadramento" in html and "peso do prazo" in html
    # Mudou a base: deixa de ser o perfil ilustrativo e o rótulo some.
    outra = client.get("/impacto?segmento=distribuicao&base=123")
    assert "Perfil ilustrativo:" not in outra.text


def test_identified_group_iv_ranks_above_any_unknown_framing():
    # Antes: grupo desconhecido valia "todos os grupos" (máximo 2%) e passava à frente do Grupo IV.
    vencida = [{"date": "2026-01-28", "state": "provisional"}]
    conhecido = row(PLANO["action"], subject="As distribuidoras", rid="k1")  # sem prazo, Grupo IV
    desconhecidos = [
        row(f"A distribuidora deve enviar o relatório {n} à ANEEL.", vencida, rid=f"u{n}")
        for n in range(5)
    ]
    result = avaliar([*desconhecidos, conhecido], base="1000000")
    assert [i["row"]["id"] for i in result["ranking"]] == ["k1"]
    assert result["ranking"][0]["enquadramentos"][0]["grupo"] == "IV"
    assert {i["row"]["id"] for i in result["verificar"]} == {f"u{n}" for n in range(5)}
    assert all(i["confianca"] == "baixo" for i in result["verificar"])
    assert all(i["multa"]["maximo"]["sem_teto"] == 2.0 for i in result["verificar"])  # faixa larga


def test_order_combines_probable_exposure_and_deadline():
    vencida = row("deve A", [{"date": "2026-01-28", "state": "provisional"}], rid="a")
    sem_data = row("deve B", rid="b")
    # Grupo V sem data (2%/2 × 0,3 = 0,3) fica abaixo de Grupo IV vencido (1%/2 × 1 = 0,5).
    result = avaliar([sem_data, vencida], grupo_a="IV", grupo_b="V")
    assert [i["row"]["id"] for i in result["ranking"]] == ["a", "b"]
    assert impacto.prioridade(result["ranking"][0]) == pytest.approx(0.5)
    assert impacto.prioridade(result["ranking"][1]) == pytest.approx(0.3)
    assert result["regra"] == impacto.REGRA_ORDEM and "peso do prazo" in result["regra"]


def test_summary_points_to_segment_obligations_awaiting_framing():
    trans = row("As transmissoras devem implementar o plano.", [{"date": "2026-01-28", "state": "provisional"}],
                subject="As transmissoras", rid="t1")  # fmt: skip
    gen = row(
        "Os agentes devem manter Plano de Contingência atualizado.", subject="Os agentes", rid="g1"
    )
    p = impacto.perfil({"data_referencia": HOJE, "segmento": "transmissao"})
    d = impacto.destaques(impacto.avaliar(PARAMS, [trans, gen], p), p)
    assert [x["item"]["row"]["id"] for x in d["itens"]] == ["g1"] and not d["itens"][0][
        "especifica"
    ]
    assert [i["row"]["id"] for i in d["verificar_segmento"]] == ["t1"]


def test_presentation_title_and_deadline_keep_literal_and_calculation():
    literal = "I - Até 90 (noventa) dias para revisar e publicar os planos, conforme a norma;"
    r = row(literal, [{"date": "2026-01-28", "state": "provisional"}])
    i = avaliar([r], grupo_o1="IV")["ranking"][0]
    assert i["titulo"] == "Revisar e publicar os planos"
    assert i["row"]["action"] == literal
    assert i["urgencia"]["principal"] == "Vencido desde 28/01/2026 (287 dias)"
    assert "provisório" in i["urgencia"]["detalhe"]
    assert (
        impacto.titulo_obrigacao("94. As distribuidoras devem estabelecer um plano.")
        == "Estabelecer um plano"
    )
    assert (
        impacto.urgencia(row("x", [{"date": "2026-12-01"}]), date(2026, 11, 11))["principal"]
        == "Vence em 01/12/2026"
    )


def test_amendment_wording_survives_owner_change():
    units = [
        {"id": "a", "kind": "article", "owner": "self", "text": "passa a vigorar:"},
        {"id": "b", "kind": "article", "owner": "REN846", "text": "Nova redação"},
        {"id": "c", "kind": "clause", "owner": "REN846", "text": "Infração"},
        {"id": "d", "kind": "article", "owner": "self", "text": "Próximo artigo"},
    ]
    assert [u["id"] for u in impacto.redacao_alterada(units, units[0])] == ["b", "c"]
