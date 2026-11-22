"""Leitor de vigência e transição (athenix/vigencia.py). Casos reais: arts. 16 a 18 da REN 1.174/2026 e
arts. 13 a 18 da RN 1.137/2025, com o mapeamento conferido pelo fundador como gabarito (nada disso está
no código). Mais frases sintéticas com outras redações, ambiguidade e referência não encontrada."""

import json
import re
from pathlib import Path

import pytest

from athenix import vigencia
from athenix.config import Settings
from athenix.poc import reader
from athenix.structure import extract

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def ren1174():
    e = extract(
        (ROOT / "tests/fontes_impacto/dou/dou_ren20261174.html").read_bytes(),
        "text/html",
        Settings(),
        "norm",
    )
    return e, vigencia.ligar(e, regras := vigencia.ler(e)), regras


@pytest.fixture(scope="module")
def rn1137():
    e = reader.read_pdf(ROOT / "tests/norma_poc/ren20251137.pdf", Settings())["extraction"]
    return e, vigencia.ligar(e, regras := vigencia.ler(e)), regras


def _unidades(e, norma, artigo, sub=None):
    """Unidades da norma alterada `norma` (dígitos) no artigo `artigo` (e na parte `sub`, se dada)."""
    by_id = {u["id"]: u for u in e["units"]}
    out = []
    for u in e["units"]:
        if re.sub(r"\D", "", u["owner"]) != norma:
            continue
        cadeia, x = [], u
        while x:
            cadeia.append((x["kind"], (x["label"] or "").replace(" ", "")))
            x = by_id.get(x["parent"]) if x["parent"] else None
        if ("article", artigo) in cadeia and (sub is None or sub in [r for _, r in cadeia]):
            out.append(u["id"])
    assert out, (norma, artigo, sub)
    return out


def _marcos(marcos, ids):
    return {(marcos[i]["tipo"], marcos[i]["data"], marcos[i]["fonte"]["dispositivo"]) for i in ids}


# --- REN 1.174/2026, arts. 16 e 18 (gabarito do fundador)
@pytest.mark.parametrize(
    ("artigo", "sub", "esperado"),
    [
        ("166", "§1º", ("adequacao", "2027-11-04", "Art. 16, I")),
        ("333", "§4º", ("adequacao", "2027-11-04", "Art. 16, I")),
        ("396", "XVIII", ("adequacao", "2027-11-04", "Art. 16, I")),
        ("159-B", None, ("adequacao", "2027-05-03", "Art. 16, II, a")),
        ("142", None, ("adequacao", "2027-05-03", "Art. 16, II, b")),
        ("166-A", None, ("adequacao", "2027-05-03", "Art. 16, II, b")),
        ("167", None, ("adequacao", "2027-05-03", "Art. 16, II, b")),
        ("170", None, ("adequacao", "2027-05-03", "Art. 16, II, b")),
        ("172-C", None, ("vigencia", "2027-05-03", "Art. 18, I, b")),
    ],
)
def test_ren_1174_alteracoes_da_ren_1000_ligadas_ao_inciso_certo(ren1174, artigo, sub, esperado):
    e, marcos, _ = ren1174
    assert _marcos(marcos, _unidades(e, "1000", artigo, sub)) == {esperado}


def test_ren_1174_art_166_paragrafo_1_e_inciso_ii_do_caput_nao_herdam_o_artigo_inteiro(ren1174):
    e, marcos, _ = ren1174
    art_166 = _unidades(e, "1000", "166")
    par_1 = set(_unidades(e, "1000", "166", "§1º"))
    resto = {
        x
        for x in _marcos(marcos, [i for i in art_166 if i not in par_1])
        if x[2] != "Art. 16, II, a"
    }
    assert resto == {("adequacao", "2027-05-03", "Art. 16, II, b")}
    # Inciso II do CAPUT do art. 166 (Art. 16, II, a); o inciso II do § 6º do mesmo artigo não é esse.
    by_id = {u["id"]: u for u in e["units"]}
    incisos_ii = [i for i in art_166 if by_id[i]["kind"] == "clause" and by_id[i]["label"] == "II"]
    do_caput = [i for i in incisos_ii if by_id[by_id[i]["parent"]]["kind"] == "article"]
    assert _marcos(marcos, do_caput) == {("adequacao", "2027-05-03", "Art. 16, II, a")}
    assert all(
        marcos[i]["fonte"]["dispositivo"] != "Art. 16, II, a"
        for i in set(incisos_ii) - set(do_caput)
    )


def test_ren_1174_outras_normas_e_demais_dispositivos(ren1174):
    e, marcos, regras = ren1174
    assert _marcos(marcos, _unidades(e, "1011", "9º-A")) == {
        ("vigencia", "2027-05-03", "Art. 18, I, a")
    }
    assert _marcos(marcos, _unidades(e, "948", "3º-A")) == {
        ("vigencia", "2027-05-03", "Art. 18, I, c")
    }
    assert _marcos(marcos, _unidades(e, "957", "7º")) == {("vigencia", "2027-02-02", "Art. 18, II")}
    anexo_iv = [u["id"] for u in e["units"] if u["kind"] == "annex" and u["label"] == "IV"]
    assert _marcos(marcos, anexo_iv) == {("adequacao", "2027-05-03", "Art. 16, II, b")}
    # Art. 2º fora das partes citadas e artigos próprios: "quanto aos demais dispositivos" (Art. 18, III)
    assert _marcos(marcos, _unidades(e, "1000", "1º")) == {
        ("em_vigor", "2026-11-04", "Art. 18, III")
    }
    art_13 = [u["id"] for u in e["units"] if u["owner"] == "self" and u["label"] == "13"]
    assert _marcos(marcos, art_13) == {("em_vigor", "2026-11-04", "Art. 18, III")}
    # Art. 17 é prazo dos representantes da comercialização varejista: não vira marco da distribuidora.
    assert all(r["outro_agente"] for r in regras if r["rotulo"].startswith("Art. 17"))
    assert not any(
        (m.get("fonte") or {}).get("dispositivo", "").startswith("Art. 17") for m in marcos.values()
    )
    # Caput do art. 16: até a adequação, valem as regras anteriores.
    assert all(r["nota"] for r in regras if r["rotulo"].startswith("Art. 16, I"))


def test_ren_1174_unidade_sem_artigo_no_bloco_tem_artigo_inferido_pela_posicao(ren1174):
    """Sem artigo identificado no bloco do art. 2º: o artigo alterado logo antes (342-A, 655-Y) não é citado
    em nenhuma regra, então vale "demais" (Art. 18, III), com a inferência declarada e a confirmar."""
    e, marcos, _ = ren1174
    inferidos = [
        m for m in marcos.values() if m.get("inferencia")
    ]  # 25 unidades; 6 delas são deveres
    p = json.loads((ROOT / "landing/src/content/plano-ren1174.json").read_text(encoding="utf-8"))
    assert (
        sum(
            "inferido pela posição" in ((o["marco"] or {}).get("nota") or "")
            for o in p["obrigacoes"]
        )
        == 6
    )
    assert {(m["tipo"], m["data"]) for m in inferidos} == {("em_vigor", "2026-11-04")}
    notas = {(o["marco"] or {}).get("nota") for o in p["obrigacoes"]}
    assert {m["inferencia"] for m in inferidos} & notas == {
        "artigo da REN 1.000 inferido pela posição no texto (342-A); a confirmar",
        "artigo da REN 1.000 inferido pela posição no texto (655-Y); a confirmar",
    }
    assert not [m for m in marcos.values() if m["tipo"] == "a_confirmar"]


def test_ren_1174_no_plano_publicado():
    p = json.loads((ROOT / "landing/src/content/plano-ren1174.json").read_text(encoding="utf-8"))
    (pu,) = [o for o in p["obrigacoes"] if o["trecho"].startswith("Parágrafo único. A adequação")]
    # dever da distribuidora (isonomia), sem data própria: vale desde a publicação ("demais", Art. 18, III)
    assert (pu["marco"]["tipo"], pu["marco"]["data"]) == ("em_vigor", "2026-11-04")
    assert not [o for o in p["obrigacoes"] if o["trecho"].startswith("Art. 17.")]
    par_1 = next(o for o in p["obrigacoes"] if o["dispositivo"] == "Art. 166, § 1º")
    assert par_1["prazo"]["texto"] == "Adequação até 04/11/2027"
    assert par_1["marco"]["nota"] == "Até a adequação, valem as regras anteriores"
    em_vigor = [o for o in p["obrigacoes"] if (o["marco"] or {}).get("tipo") == "em_vigor"]
    assert em_vigor and all(
        o["prazo"]["texto"].startswith("Em vigor desde 04/11/2026 (sem período de adequação)")
        for o in em_vigor
        if o["situacao"] == "sem_prazo"
    )
    # 180 dias NÃO é padrão: só o que um inciso cita tem adequação.
    assert len(em_vigor) > 30


# --- RN 1.137/2025, arts. 13 a 18
@pytest.mark.parametrize(
    ("item", "esperado"),
    [
        ("103", ("adequacao", "2026-01-28", "Art. 13, I")),
        ("108", ("adequacao", "2026-01-28", "Art. 13, I")),
        ("148", ("adequacao", "2026-01-28", "Art. 13, I")),
        ("104", ("adequacao", "2026-04-28", "Art. 13, II")),
        ("105", ("adequacao", "2026-04-28", "Art. 13, III")),
        ("106", ("adequacao", "2026-04-28", "Art. 13, IV")),
        ("107", ("adequacao", "2026-04-28", "Art. 13, V")),
        ("114", ("adequacao", None, "Art. 14")),  # 30 dias da publicação das instruções da ANEEL
        ("113", ("adequacao", None, "Art. 15")),
        ("145", ("em_vigor", "2025-10-30", "Art. 18")),  # "não listadas nos artigos 13 a 16"
    ],
)
def test_rn_1137_itens_do_anexo_iv(rn1137, item, esperado):
    e, marcos, _ = rn1137
    ids = [
        u["id"]
        for u in e["units"]
        if u["kind"] == "item" and u["label"] == item and "956" in u["owner"]
    ]
    assert _marcos(marcos, ids) == {esperado}


def test_rn_1137_referencias_fora_do_texto_ficam_a_confirmar(rn1137):
    _, _, regras = rn1137
    rel = {
        r["dispositivo"]: r["alvos_a_confirmar"] for r in vigencia.relatorio(regras, {})["regras"]
    }
    assert rel["Art. 13, VI"] and rel["Art. 16"]  # PRODIST e Decreto 12.068: não estão na norma
    assert not rel["Art. 13, I"]


# --- Frases sintéticas: outras redações
def _u(i, kind, label, owner, parent, start, text):
    return {"id": i, "kind": kind, "label": label, "owner": owner, "parent": parent, "start": start, "end": start + len(text), "text": text}  # fmt: skip


def _norma(*artigos_finais, pub="2026-03-02"):
    """Norma com um bloco de alteração (art. 2º altera a REN 500: arts. 10 e 11) e um artigo próprio (3º)."""
    units = [
        _u(
            "a1",
            "article",
            "2º",
            "self",
            None,
            0,
            "Art. 2º A Resolução Normativa nº 500, de 1º de março de 2020, passa a vigorar com as seguintes alterações:",
        ),  # fmt: skip
        _u(
            "b1",
            "article",
            "10",
            "Resolução Normativa nº 500",
            None,
            10,
            '"Art. 10. A distribuidora deve publicar o relatório."',
        ),  # fmt: skip
        _u(
            "b2",
            "paragraph",
            "§ 3º",
            "Resolução Normativa nº 500",
            "b1",
            20,
            "§ 3º O relatório deve ser mensal.",
        ),  # fmt: skip
        _u(
            "b3",
            "article",
            "11",
            "Resolução Normativa nº 500",
            None,
            30,
            '"Art. 11. A distribuidora deve manter o cadastro."',
        ),  # fmt: skip
        _u(
            "a2",
            "article",
            "3º",
            "self",
            None,
            40,
            "Art. 3º As distribuidoras devem enviar o plano à ANEEL.",
        ),  # fmt: skip
    ]
    units += artigos_finais
    return {"units": units, "dates": [{"kind": "publication", "date": pub}]}


def test_sintetica_produz_efeitos_em_dias_e_demais_dispositivos():
    e = _norma(
        _u(
            "f1",
            "article",
            "9º",
            "self",
            None,
            50,
            "Art. 9º Esta Resolução entra em vigor na data de sua publicação, produzindo efeitos:",
        ),  # fmt: skip
        _u(
            "f2", "clause", "I", "self", "f1", 60, "I - em 60 (sessenta) dias, quanto ao art. 3º; e"
        ),
        _u(
            "f3",
            "clause",
            "II",
            "self",
            "f1",
            70,
            "II - na data de sua publicação, quanto aos demais dispositivos.",
        ),  # fmt: skip
    )
    m = vigencia.ligar(e, vigencia.ler(e))
    assert (m["a2"]["tipo"], m["a2"]["data"]) == ("vigencia", "2026-05-01")
    assert {(m[i]["tipo"], m[i]["data"]) for i in ("b1", "b2", "b3")} == {
        ("em_vigor", "2026-03-02")
    }


def test_sintetica_adequacao_num_artigo_so_na_parte_que_altera_um_paragrafo():
    e = _norma(
        _u(
            "f1",
            "article",
            "9º",
            "self",
            None,
            50,
            "Art. 9º A adequação às alterações desta Resolução deve ser realizada em até 6 (seis) meses da publicação, quanto ao art. 2º, na parte que altera o § 3º do art. 10 da Resolução Normativa nº 500, de 1º de março de 2020.",
        ),  # fmt: skip
    )
    m = vigencia.ligar(e, vigencia.ler(e))
    assert (m["b2"]["tipo"], m["b2"]["data"]) == ("adequacao", "2026-09-02")
    assert "b1" not in m and "b3" not in m  # sem "demais dispositivos": nada presumido


def test_sintetica_ambigua_e_referencia_nao_encontrada():
    e = _norma(
        _u(
            "f1",
            "article",
            "9º",
            "self",
            None,
            50,
            "Art. 9º A adequação às alterações desta Resolução deve ser realizada nos seguintes prazos:",
        ),  # fmt: skip
        _u(
            "f2",
            "clause",
            "I",
            "self",
            "f1",
            60,
            "I - em 90 dias da publicação, quanto ao art. 2º, na parte que altera o art. 11 da Resolução Normativa nº 500;",
        ),  # fmt: skip
        _u(
            "f3",
            "clause",
            "II",
            "self",
            "f1",
            70,
            "II - em 180 dias da publicação, quanto ao art. 2º, na parte que altera o art. 11 e o art. 99 da Resolução Normativa nº 500.",
        ),  # fmt: skip
    )
    regras = vigencia.ler(e)
    m = vigencia.ligar(e, regras)
    assert (
        m["b3"]["tipo"] == "a_confirmar" and m["b3"]["data"] is None
    )  # dois incisos, datas diferentes
    rel = {
        r["dispositivo"]: r["alvos_a_confirmar"] for r in vigencia.relatorio(regras, m)["regras"]
    }
    assert rel["Art. 9º, II"] == ["norma 500, art 99"]  # art. 99 não existe no texto


def test_sintetica_nao_listadas_devem_ser_implementadas():
    e = _norma(
        _u(
            "f1",
            "article",
            "8º",
            "self",
            None,
            45,
            "Art. 8º As distribuidoras devem implantar o canal de que trata o art. 11 da Resolução Normativa nº 500 em até 30 dias, contados da publicação.",
        ),  # fmt: skip
        _u(
            "f2",
            "article",
            "9º",
            "self",
            None,
            50,
            "Art. 9º As disposições não listadas no artigo 8º devem ser implementadas na data de publicação desta Resolução.",
        ),  # fmt: skip
    )
    m = vigencia.ligar(e, vigencia.ler(e))
    assert (m["b3"]["tipo"], m["b3"]["data"]) == ("adequacao", "2026-04-01")
    assert (m["b1"]["tipo"], m["b1"]["data"]) == ("em_vigor", "2026-03-02")


def test_rn_1137_paragrafo_unico_do_art_13_vale_desde_a_publicacao(rn1137):
    """ "Os planos de contingência em vigor ... devem ser publicados": sem prazo próprio, pelo Art. 18."""
    e, marcos, _ = rn1137
    (pu,) = [
        u["id"]
        for u in e["units"]
        if u["owner"] == "self"
        and u["text"].startswith("Parágrafo único. Os planos de contingência")
    ]
    assert _marcos(marcos, [pu]) == {("em_vigor", "2025-10-30", "Art. 18")}


def test_rn_1137_vencidas_por_obrigacao_principal():
    p = json.loads((ROOT / "landing/src/content/plano-rn1137.json").read_text(encoding="utf-8"))
    v = [o for o in p["obrigacoes"] if o["situacao"] == "vencida"]
    principais = {o["principal"] for o in v}
    detalhes = [o for o in v if o["detalhe"]]
    assert (len(principais), len(detalhes)) == (14, 11)
    # as 11 alíneas de detalhe são do item 107 ("a) Número da ocorrência" ...), uma só obrigação-mãe
    assert {o["dispositivo"].split(",")[0] for o in detalhes} == {"item 107"}
