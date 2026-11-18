"""Plano de ação: tema pela seção da norma, prazos do motor temporal e IA fora do cálculo."""

import pytest

from athenix import impacto, plano

PARAMS = impacto.carregar()
CFG = plano.carregar_temas()

MANEJO = "94. As distribuidoras devem estabelecer um plano de manejo vegetal e disponibilizá-lo em seu sítio eletrônico."
TRANSITORIA = "II - Até 180 (cento e oitenta) dias para implementar o registro das interações com o Poder Público Municipal em relação ao manejo da vegetação;"  # fmt: skip
CESSAO = "a) Valor global da contratação com detalhamento dos recursos envolvidos."
UNITS = [
    {"id": "h1", "kind": "heading", "label": "Seção 4.7", "start": 0, "text": "Seção 4.7"},
    {
        "id": "t1",
        "kind": "unstructured",
        "label": "Texto",
        "start": 10,
        "text": "Poda e manejo vegetal\nResponsabilidades",
    },  # fmt: skip
    {"id": "u1", "kind": "item", "label": "94", "start": 20, "text": MANEJO},
    {"id": "h2", "kind": "heading", "label": "Seção 4.10", "start": 200, "text": "Seção 4.10"},
    {
        "id": "t2",
        "kind": "unstructured",
        "label": "Texto",
        "start": 210,
        "text": "Cessão Emergencial de recursos humanos, equipamentos e materiais entre distribuidoras Objetivo",
    },  # fmt: skip
    {"id": "u3", "kind": "letter", "label": "a", "start": 300, "text": CESSAO},
    {
        "id": "h3",
        "kind": "heading",
        "label": "Seção X",
        "start": 400,
        "text": "Seção X Das Disposições Finais e Transitórias",
    },  # fmt: skip
    {"id": "u2", "kind": "clause", "label": "II", "start": 410, "text": TRANSITORIA},
]
# Só as seções usadas pelo teste precisam existir no texto sintético.
CFG_TESTE = CFG | {
    "temas": [
        t | {"secoes": [s for s in t["secoes"] if s["rotulo"] in {"Seção 4.7", "Seção 4.10"}]}
        for t in CFG["temas"]
    ]
}


def row(rid, unit, action, deadlines=()):
    return {
        "id": rid,
        "action": action,
        "subject": "As distribuidoras",
        "modality": "duty",
        "status": "detected",
        "evidence": [{"unit_id": unit, "quote": action}],
        "anchors": [{"state": "verified", "unit_id": unit, "quote": action}],
        "deadlines": list(deadlines),
    }


ROWS = [
    row("m", "u1", MANEJO),
    row("t", "u2", TRANSITORIA, [{"date": "2026-04-28", "state": "provisional"}]),
    row("c", "u3", CESSAO, [{"date": None, "state": "awaiting_event"}]),
]


def montar(ia=None, base="5000000000"):
    form = {"segmento": "distribuicao", "base": base, "data_referencia": "2026-11-17"}
    p = impacto.perfil(form)
    resultado = impacto.avaliar(PARAMS, ROWS, p)
    return plano.montar(resultado, UNITS, PARAMS, p, CFG_TESTE, ia, chave=lambda r: r["id"])


def test_tema_pela_secao_da_norma_ou_pelo_primeiro_assunto_nomeado():
    obs = {o["id"]: o for o in montar()["obrigacoes"]}
    assert obs["m"]["tema"] == "manejo" and obs["m"]["motivo_tema"] == "Seção 4.7 da norma"
    # Disposição transitória: "Poder Público" aparece antes de "manejo" no texto.
    assert obs["t"]["tema"] == "poder_publico"
    assert obs["t"]["motivo_tema"] == 'O texto nomeia "Poder Público"'
    assert obs["c"]["tema"] == "cessao"


def test_titulo_de_secao_ausente_no_texto_interrompe_a_exportacao():
    cfg = CFG | {"temas": [{"id": "x", "nome": "X", "secoes": [{"rotulo": "Seção 4.7", "titulo": "Outro título"}], "padrao": None}]}  # fmt: skip
    with pytest.raises(AssertionError, match="Seção 4.7"):
        plano.conferir_secoes(cfg, UNITS)


def test_linha_do_tempo_e_decisoes_usam_as_datas_do_motor():
    out = montar()
    assert out["linha_do_tempo"]["vencida"] == ["t"]
    assert out["linha_do_tempo"]["evento"] == ["c"]
    assert out["resumo"]["por_situacao"]["vencida"] == 1
    primeira = out["decisoes"][0]
    assert primeira["obrigacoes"] == ["t"] and "28/04/2026" in primeira["titulo"]
    t = next(o for o in out["obrigacoes"] if o["id"] == "t")
    assert t["prazo"]["provisorio"] is True


def test_ia_aparece_como_sugestao_e_nao_entra_no_calculo():
    ia = {
        "titulos": {
            "c": {
                "titulo": "Informar o valor global da contratação",
                "citacao": "Valor global da contratação",
                "alerta": None,
            }
        },  # fmt: skip
        "enquadramentos": {
            "c": {"dispositivo": "Art. 11, V", "grupo": "III", "justificativa": "j", "duvida": None}
        },  # fmt: skip
    }
    sem, com = montar(), montar(ia)
    c = next(o for o in com["obrigacoes"] if o["id"] == "c")
    assert c["ia"]["dispositivo"] == "Art. 11, V" and c["calculo"] == "verificar"
    assert c["faixa"] is None and c["grupo"] is None
    assert c["titulo"] == "Informar o valor global da contratação" and c["titulo_origem"] == "ia"
    assert "Art. 11, V" in com["infracoes"]
    # O cálculo (fila, grupos e faixas) é o mesmo com e sem a IA.
    chaves = ("calculo", "grupo", "faixa", "posicao_fila")
    assert [{k: o[k] for k in chaves} for o in sem["obrigacoes"]] == [
        {k: o[k] for k in chaves} for o in com["obrigacoes"]
    ]


def test_titulo_da_ia_com_alerta_ou_citacao_ausente_nao_e_aplicado():
    for sug in (
        {
            "titulo": "Informar o valor global",
            "citacao": "Valor global da contratação",
            "alerta": "Mudou o sentido",
        },  # fmt: skip
        {"titulo": "Informar o valor global", "citacao": "trecho que não existe", "alerta": None},
        {"titulo": "Valor global", "citacao": "Valor global da contratação", "alerta": None},
    ):
        c = next(o for o in montar({"titulos": {"c": sug}})["obrigacoes"] if o["id"] == "c")
        assert c["titulo_origem"] == "regra"


def test_evidencia_sugerida_traz_o_trecho_que_a_motivou():
    m = next(o for o in montar()["obrigacoes"] if o["id"] == "m")
    ids = {e["id"]: e["trecho"] for e in m["evidencias"]}
    assert "sítio eletrônico" in ids["site"] and ids["site"] in MANEJO
    assert "plano" in ids


def test_base_em_branco_mantem_percentuais_sem_reais():
    out = montar(base="")
    fila = [o for o in out["obrigacoes"] if o["calculo"] == "fila"]
    assert fila and all("maximo_reais" not in o["faixa"] for o in fila)
    assert all(o["faixa"]["teto_grupo_pct"] for o in fila)


def test_ordem_dos_temas_pelo_prazo_gravidade_e_diagnostico():
    def tema(tid, sit, data=None, grupo=None, n=1):
        contagem = {s: int(s == sit) for s in plano.SITUACOES}
        urg = {"data": data} if data else None
        return {"id": tid, "contagem": contagem, "prazo_mais_urgente": urg, "grupo_mais_grave": grupo, "n": n}  # fmt: skip

    temas = [
        tema("sem_data_iv", "sem_prazo", grupo="IV", n=30),
        tema("evento_sem_grupo", "evento", n=40),
        tema("vencida_recente", "vencida", "2026-04-28", "IV"),
        tema("vencida_antiga", "vencida", "2026-01-28"),
        tema("vencida_recente_v", "vencida", "2026-04-28", "V"),
    ]
    ids = lambda ts: [t["id"] for t in ts]  # noqa: E731
    assert ids(plano.ordenar_temas(temas)) == [
        "vencida_antiga",
        "vencida_recente_v",
        "vencida_recente",
        "sem_data_iv",
        "evento_sem_grupo",
    ]
    diag = {"vencida_antiga": "sim", "sem_data_iv": "parcial", "evento_sem_grupo": "nao"}
    assert ids(plano.ordenar_temas(temas, diag)) == [
        "vencida_recente_v",
        "vencida_recente",
        "sem_data_iv",  # grupo identificado (IV) vem antes da lacuna maior sem grupo
        "evento_sem_grupo",
        "vencida_antiga",
    ]


def cenarios(base="5000000000"):
    """Resultados do motor com cada atenuante e valor base no teto do grupo (como o exportador)."""
    out = {}
    for a in ("espontanea", "ate_tn"):
        form = {"segmento": "distribuicao", "base": base, "data_referencia": "2026-11-17"}
        p = impacto.perfil(form | {"atenuante": a, "fracao_valor_base": "100"})
        out[a] = impacto.avaliar(PARAMS, ROWS, p)
    return out


def test_reducao_cita_o_catalogo_e_nao_inventa_percentual():
    r = montar()["reducao"]
    assert r["rotulo"] == "Análise regulatória preliminar · não constitui parecer jurídico"
    por_id = {m["parametro"]: m for m in r["medidas"]} | {g["parametro"]: g for g in r["regras"]}
    assert {"atenuante_espontanea", "atenuante_tn", "atenuantes_nao_cumulativas"} <= set(por_id)
    assert "atenuante_comprovacao" in por_id
    for pid, m in por_id.items():
        par = PARAMS["parametros"][pid]
        assert m["trecho"] == par["trecho"] and m["dispositivo"] == par["dispositivo"]
        assert m["sha256"] == PARAMS["fontes"][par["fonte"]]["sha256"]
        assert m["percentual"] == (par["percentuais"] or [None])[0]
    assert por_id["atenuante_espontanea"]["percentual"] == 95.0
    # Sem percentual no texto, o efeito diz isso em vez de inventar um número.
    for pid in ("advertencia", "metodologia_afastavel"):
        assert por_id[pid]["percentual"] is None
        assert "não fixa percentual" in por_id[pid]["efeito"]


def test_cenario_com_atenuante_vem_do_motor_e_nao_mexe_no_maximo():
    sem, com = montar(), plano.montar(
        impacto.avaliar(PARAMS, ROWS, impacto.perfil({"segmento": "distribuicao", "base": "5000000000", "data_referencia": "2026-11-17"})),
        UNITS, PARAMS, impacto.perfil({"segmento": "distribuicao", "base": "5000000000", "data_referencia": "2026-11-17"}),
        CFG_TESTE, chave=lambda r: r["id"], cenarios=cenarios(),
    )  # fmt: skip
    f_sem = next(o["faixa"] for o in sem["obrigacoes"] if o["faixa"])
    f_com = next(o["faixa"] for o in com["obrigacoes"] if o["faixa"])
    assert f_sem["com_atenuante_pct"] == {} and f_com["maximo_pct"] == f_sem["maximo_pct"]
    teto = f_com["teto_grupo_pct"]
    assert f_com["com_atenuante_pct"]["espontanea"] == pytest.approx(teto * 0.05)
    assert f_com["com_atenuante_pct"]["ate_tn"] == pytest.approx(teto * 0.5)
    assert f_com["com_atenuante_reais"]["ate_tn"] == pytest.approx(teto * 0.5 / 100 * 5e9)
    assert f_com["teto_legal_lei_pct"] == PARAMS["parametros"]["teto_legal_lei"]["percentuais"][0]


def test_causa_externa_sem_texto_fica_a_confirmar_com_advogado():
    for t in montar()["temas"]:
        assert t["excludentes"] == [] and t["causa_externa"] == "argumento a confirmar com advogado"
    # Com excludente no texto da própria obrigação, o trecho literal é citado.
    texto = "94. As distribuidoras devem publicar o plano, ressalvados os casos de força maior."
    rows = [row("f", "u1", texto)]
    p = impacto.perfil({"segmento": "distribuicao", "base": "", "data_referencia": "2026-11-17"})
    out = plano.montar(impacto.avaliar(PARAMS, rows, p), UNITS, PARAMS, p, CFG_TESTE, chave=lambda r: r["id"])  # fmt: skip
    t = next(t for t in out["temas"] if t["n"])
    assert t["excludentes"] == [{"obrigacao": "f", "trecho": texto}] and t["causa_externa"] is None


def test_o_que_guardar_e_sugestao_ligada_ao_texto_do_dever():
    out = montar()
    assert set(out["guardar"]) == {g["id"] for g in CFG["guardar"]}
    m = next(o for o in out["obrigacoes"] if o["id"] == "m")
    assert "indisponibilidade" in m["guardar"]  # "sítio eletrônico"
    assert "versoes" in m["guardar"]  # "plano"
    assert "não são exigência da norma" in CFG["descricao_guardar"].lower()
