"""Compilação automática (Bloco 5): REN 846 oficial + alterações de 2026, com os arquivos reais."""

import json
import re
from pathlib import Path

import pytest

from athenix import compilacao, dou, structure
from athenix.config import Settings
from athenix.normalizacao import chave
from scripts import compilar_normas as cn

RAIZ = Path(__file__).parent.parent
S = Settings()


@pytest.fixture(scope="module")
def comp():
    return cn.montar(S)


def _doc(nome):
    html = dou.ler_html((RAIZ / f"tests/fontes_impacto/dou/{nome}.html").read_bytes())
    return structure.from_pieces([html["texto"]], [], [], "dou", S)


def _texto(comp, em, chave_dispositivo):
    vigentes = compilacao.texto_vigente(comp, em)
    return next((d["texto"] for d in vigentes if d["chave"] == chave_dispositivo), None)


def test_bloco_sem_aspas_de_fechamento_termina_no_proximo_artigo_do_ato():
    # RN 1.148 (biblioteca da ANEEL): o bloco da REN 846 não tem aspas de fechamento nem (NR).
    pdf = (RAIZ / "tests/fontes_impacto/ren20261148.pdf").read_bytes()
    ex = structure.extract(pdf, "application/pdf", S)
    donos = {u["label"]: u["owner"] for u in ex["units"] if u["kind"] == "article"}
    assert donos["9º"] == donos["10"] == "self" and "846" in donos["11"]
    assert any("sem aspas de fechamento" in w for w in ex["warnings"])


def test_inciso_com_aspas_de_abertura_e_nr_sem_aspas_de_fechamento():
    # RN 1.162 (DOU): `"XII - ...` abre aspas; `...tensão; (NR)` fecha sem aspas.
    ex = _doc("dou_ren20261162")
    chaves = compilacao.caminhos(ex["units"])
    donos = {chaves[u["id"]]: u["owner"] for u in ex["units"]}
    for c in ("article:10/clause:VII", "article:10/clause:XII", "article:10/clause:XIX"):
        assert "846" in donos[c], c


def test_so_os_atos_que_alteram_a_846_geram_operacoes(comp):
    r = {x["ato"]: x for x in comp["relatorio"]}
    assert all(r[a]["altera_a_846"] for a in ("REN 1.148/2026", "REN 1.162/2026", "REN 1.174/2026"))
    nomes = [a["ato"]["nome"] for a in comp["alteradoras"]]
    assert nomes == ["REN 1.148/2026", "REN 1.162/2026", "REN 1.174/2026"]


def test_vigencia_de_cada_ato(comp):
    v = {a["ato"]["nome"]: a["vigencia_padrao"] for a in comp["alteradoras"]}
    assert v == {
        "REN 1.148/2026": "2027-01-01",
        "REN 1.162/2026": "2026-06-24",
        "REN 1.174/2026": "2026-11-04",
    }


def test_texto_vigente_em_cada_data(comp):
    antes = _texto(comp, "2025-12-01", "article:9/clause:IV")
    depois = _texto(comp, "2026-06-24", "article:9/clause:IV")
    assert "atualização de cadastro" in antes and "armazenamento" not in antes
    assert "sistemas de armazenamento de energia" in depois
    assert _texto(comp, "2026-06-23", "article:21/paragraph:§11") is None  # incluído em 24/06/2026
    assert "Valor Anual de Referência" in _texto(comp, "2026-06-24", "article:21/paragraph:§11")
    assert _texto(comp, "2026-11-03", "article:11/clause:XXIV") is None
    assert "Lei nº 9.074" in _texto(comp, "2026-11-04", "article:11/clause:XXIV")


def test_cada_dispositivo_registra_a_norma_e_a_fonte_da_redacao_atual(comp):
    h = comp["historico"]["article:10/clause:XII"]
    assert [x["tipo"] for x in h] == ["base", "substituir"]
    assert h[0]["fonte"]["tipo"] == "biblioteca da ANEEL" and h[0]["fonte"]["sha256"]
    ultimo = h[-1]
    assert ultimo["redacao_dada_por"] == "REN 1.162/2026" and ultimo["fonte"]["tipo"] == "DOU"
    assert ultimo["fonte"]["publicacao_dou"]["pagina"] == "92"
    assert (
        ultimo["citacao"]["artigo_do_ato"] == "16"
        and "armazenamento" in ultimo["citacao"]["trecho"]
    )


def test_xxiii_e_sucessao_no_tempo_com_incerteza_e_duvida_de_numeracao(comp):
    # RN 1.137 até 31/12/2026; RN 1.148 (sem (NR)/(AC) no texto da fonte) a partir de 01/01/2027.
    assert comp["conflitos"] == []
    chave_xxiii = "article:11/clause:XXIII"
    assert "interrupções no fornecimento" in _texto(comp, "2026-12-31", chave_xxiii)
    assert "Ouvidoria" in _texto(comp, "2027-01-01", chave_xxiii)
    h = comp["historico"][chave_xxiii]
    assert [x["vigencia"] for x in h] == ["2025-10-21", "2027-01-01"]
    assert h[1]["redacao_dada_por"] == "REN 1.148/2026" and h[1]["aviso"].startswith("INCERTO")
    (d,) = comp["duvidas_para_especialista"]
    assert d["dispositivo"] == chave_xxiii and d["para"].startswith("especialista")
    assert d["vigencias"] == {"anterior": "2025-10-21", "nova": "2027-01-01"}


def test_mesma_data_sem_marcador_continua_conflito():
    base = _base(("article:1", "Art. 1º A."))
    a = _alt("REN A", "2026-01-01", "2026-02-01", ("article:1", "Art. 1º B.", None))
    b = _alt("REN B", "2026-01-02", "2026-02-01", ("article:1", "Art. 1º C.", None))
    assert len(compilacao.compilar({"nome": "T"}, base, [a, b])["conflitos"]) == 1


def test_subitens_nao_reproduzidos_ficam_vigentes_e_vao_para_decisao_humana(comp):
    filhos = {i["dispositivo"] for i in comp["inferencias"]}
    assert filhos == {f"article:9/clause:IV/letter:{x}" for x in "abc"}
    assert all(i["aplicada"] is False for i in comp["inferencias"])
    assert len(comp["historico"]["article:9/clause:IV/letter:a"]) == 1  # nada foi revogado


def test_revogacao_explicita_so_vira_caminho_nas_formas_simples():
    ex = _doc("dou_ren20261174")
    achados, sem = compilacao.revogacoes(ex["units"], "1000")
    chaves = [a["chave"] for a in achados]
    assert "article:133/paragraph:§4" in chaves and "article:148/clause:I" in chaves
    assert "article:164" in chaves and achados[0]["trecho"].startswith("I - os §§ 4º")
    assert any("Seção IV" in s["item"] for s in sem)  # forma não suportada: sem palpite
    assert compilacao.revogacoes(ex["units"], "846") == ([], [])


def _base(*dispositivos):
    fonte = {"tipo": "teste", "arquivo": "x", "sha256": "0"}
    return {
        "vigente_desde": "2020-01-01",
        "dispositivos": [
            {
                "chave": c,
                "texto": t,
                "situacao": "vigente",
                "redacao_dada_por": None,
                "fonte": fonte,
            }
            for c, t in dispositivos
        ],
    }


def _alt(nome, data, vigencia, *ops, tipo="substituir"):
    fonte = {"tipo": "teste", "arquivo": nome, "sha256": "0"}
    return {
        "ato": {"nome": nome, "data": data},
        "fonte": fonte,
        "operacoes": [
            {
                "chave": c,
                "tipo": tipo,
                "texto": t,
                "marcador": m,
                "vigencia": vigencia,
                "citacao": {"trecho": t, "artigo_do_ato": "1"},
            }
            for c, t, m in ops
        ],
    }


def test_duas_normas_no_mesmo_dispositivo_e_na_mesma_data_geram_conflito():
    base = _base(("article:1", "Art. 1º Texto A."))
    a = _alt("REN A", "2026-01-01", "2026-02-01", ("article:1", "Art. 1º Texto B.", "NR"))
    b = _alt("REN B", "2026-01-02", "2026-02-01", ("article:1", "Art. 1º Texto C.", "NR"))
    r = compilacao.compilar({"nome": "T"}, base, [a, b])
    assert len(r["conflitos"]) == 1 and r["aplicadas"] == []
    assert [h["texto"] for h in r["historico"]["article:1"]] == ["Art. 1º Texto A."]


def test_alteracoes_em_datas_diferentes_valem_em_sequencia_e_preservam_as_anteriores():
    base = _base(("article:1", "Art. 1º Texto A."))
    a = _alt("REN A", "2026-01-01", "2026-02-01", ("article:1", "Art. 1º Texto B.", "NR"))
    b = _alt("REN B", "2026-03-01", "2026-04-01", ("article:1", "Art. 1º Texto C.", "NR"))
    r = compilacao.compilar({"nome": "T"}, base, [b, a])  # fora de ordem: a data manda
    assert r["conflitos"] == []
    textos = [
        compilacao.texto_vigente(r, d)[0]["texto"]
        for d in ("2026-01-31", "2026-02-01", "2026-04-01")
    ]
    assert textos == ["Art. 1º Texto A.", "Art. 1º Texto B.", "Art. 1º Texto C."]


def test_revogacao_de_artigo_leva_os_subitens_e_sem_vigencia_nao_e_aplicada():
    base = _base(("article:2", "Art. 2º X."), ("article:2/clause:I", "I - y;"))
    rev = _alt("REN R", "2026-01-01", "2026-02-01", ("article:2", None, None), tipo="revogar")
    sem = _alt("REN S", "2026-01-01", None, ("article:2", "Art. 2º Z.", "NR"))
    r = compilacao.compilar({"nome": "T"}, base, [rev, sem])
    antes = [d["chave"] for d in compilacao.texto_vigente(r, "2026-01-31")]
    assert antes == ["article:2", "article:2/clause:I"]
    assert compilacao.texto_vigente(r, "2026-02-01") == []
    assert r["nao_aplicado"][0]["motivo"] == "vigência não determinada"


def test_arquivo_versionado_e_igual_ao_gerado_agora(comp):
    versionado = json.loads(
        (RAIZ / "athenix/data/compilado_ren846.json").read_text(encoding="utf-8")
    )
    gerado = json.loads(json.dumps(comp, ensure_ascii=False, sort_keys=True))
    assert versionado == gerado


LEIS = RAIZ / ".local/fontes_impacto/ren2019846_compilada.pdf"
CONFERIDOS = (
    "article:9/clause:VII",
    "article:10/clause:VII",
    "article:10/clause:XII",
    "article:10/clause:XIX",
    "article:21/paragraph:§11",
    "article:21/paragraph:§11/clause:I",
)


@pytest.mark.skipif(not LEIS.exists(), reason="cópia do Leis.org só existe em .local/")
def test_conferencia_independente_com_a_copia_do_leis_org(comp):
    # Uso só interno: a cópia (Leis.org, gerada em 04/11/2026) consolida o que já vigora.
    ex = structure.extract(LEIS.read_bytes(), "application/pdf", S)
    vivas = [u for u in ex["units"] if u.get("struck") != "revoked"]
    chaves = compilacao.caminhos(vivas)
    ruido = re.compile(r"\s*Leis\.org/aneel.*$")
    nota = re.compile(r"\((?:Redação dada|Incluíd|Acrescid|Revogad)[^)]*\)")

    def sem(texto):
        return chave(nota.sub("", ruido.sub("", texto)))

    leis = {}
    for u in vivas:
        if u["owner"] == "self":
            leis.setdefault(chaves[u["id"]].split("#")[0], []).append(
                sem(compilacao.limpa_texto(u["text"]))
            )
    for k in CONFERIDOS:
        assert sem(_texto(comp, "2026-11-18", k)) in leis[k], k


def test_detectar_o_que_a_norma_nova_altera_no_acervo():
    ex = _doc("dou_ren20261174")
    d = compilacao.detectar(ex, {"846", "1011"})
    assert d["no_acervo"] == ["1011", "846"]
    assert "1000" in d["fora_do_acervo"] and "846" not in d["fora_do_acervo"]
    assert d["revogacoes"]["1011"]["dispositivos"] == ["article:13/clause:VI"]
    assert "846" not in d["revogacoes"]  # a 1.174 altera a 846 (art. 10) mas não a revoga
    # Norma que não cita nenhuma do acervo: nada a fazer.
    assert compilacao.detectar(_doc("dou_dsp20261293"), {"846"})["no_acervo"] == []


def test_pontilhado_depois_do_caput_mantem_os_incisos():
    # "Art. 9º Texto novo: / ........ / II - novo; / ........" (NR): I e III continuam valendo.
    base = _base(("article:9", "Art. 9º Velho:"), ("article:9/clause:I", "I - a;"),
                 ("article:9/clause:II", "II - b;"), ("article:9/clause:III", "III - c."))  # fmt: skip
    alt = _alt("REN A", "2026-01-01", "2026-02-01", ("article:9", "Art. 9º Novo:", "NR"),
               ("article:9/clause:II", "II - novo;", "NR"))  # fmt: skip
    r = compilacao.compilar({"nome": "T"}, base, [alt])
    vigentes = [d["chave"] for d in compilacao.texto_vigente(r, "2026-02-01")]
    assert vigentes == [
        "article:9",
        "article:9/clause:I",
        "article:9/clause:II",
        "article:9/clause:III",
    ]
    assert {i["dispositivo"] for i in r["inferencias"]} == {
        "article:9/clause:I",
        "article:9/clause:III",
    }


def test_incluir_de_novo_dispositivo_revogado_nao_duplica_a_ordem():
    base = _base(("article:1", "Art. 1º A."))
    rev = _alt("REN R", "2026-01-01", "2026-02-01", ("article:1", None, None), tipo="revogar")
    nova = _alt("REN N", "2026-03-01", "2026-04-01", ("article:1", "Art. 1º B.", "NR"))
    r = compilacao.compilar({"nome": "T"}, base, [rev, nova])
    assert r["ordem"] == ["article:1"]
    assert [d["texto"] for d in compilacao.texto_vigente(r, "2026-04-01")] == ["Art. 1º B."]


def test_caput_mais_um_com_sufixo_nao_fecha_o_bloco():
    linhas = [
        "Art. 1º A Resolução Normativa nº 846, de 2019, passa a vigorar com as seguintes alterações:",
        "“Art. 2º-A Texto novo.",
        "Art. 2º-B Outro texto novo.” (NR)",
        "Art. 2º Esta Resolução vale.",
    ]
    texto = "NL".join(linhas).replace("NL", chr(10)) + chr(10)
    marcadores, avisos = structure.segment(texto, [{"number": 1, "start": 0, "end": len(texto)}])
    donos = {m["label"]: m["owner"] for m in marcadores if m["kind"] == "article"}
    assert "846" in donos["2º-B"] and donos["2º"] == "self"
    assert not [a for a in avisos if "sem aspas" in a]


@pytest.mark.parametrize(
    ("linha", "anexo"),
    [
        ("Anexo II do Decreto nº 1", False),
        ("Anexo 12 da Lei nº 2", False),
        ("Anexo II e III da Lei", False),
        ("ANEXO II", True),
        ("ANEXO I DA RESOLUÇÃO", True),
    ],
)
def test_remissao_a_anexo_em_linha_quebrada(linha, anexo):
    marcadores, _ = structure.segment(
        "Art. 1º X." + chr(10) + linha + chr(10), [{"number": 1, "start": 0, "end": 99}]
    )
    assert any(m["kind"] == "annex" for m in marcadores) is anexo


def test_original_de_2019_x_compilado_oficial():
    # Validação (a): o que deve coincidir. Original (DOU de 18/06/2019, p. 37) x compilado oficial
    # (até a RN 1.137): todo dispositivo sem nota de redação no compilado tem o texto do original.
    html = dou.ler_html((RAIZ / "tests/fontes_impacto/dou/dou_ren20190846.html").read_bytes())
    assert html["publicacao"]["pagina"] == "37" and html["titulo"]["numero"] == "846"
    ex = structure.from_pieces([html["texto"]], [], [], "dou", S)
    chaves = compilacao.caminhos(ex["units"])
    ignorar = {"heading", "unstructured"}
    original = {
        chaves[u["id"]]: compilacao.limpa_texto(u["text"])
        for u in ex["units"]
        if u["owner"] == "self" and u["kind"] not in ignorar
    }
    comp = json.loads((RAIZ / "athenix/data/compilado_ren846.json").read_text(encoding="utf-8"))
    base = {k: h[0] for k, h in comp["historico"].items() if h[0]["tipo"] == "base"}
    nota = re.compile(
        r"\s*\((?:Redação (?:dada|acrescida)|Incluíd[oa]|Acrescid[oa]|Revogad[oa])[^)]*\)"
    )
    assert len(original) == 343 and not [k for k in original if k not in base]
    sem_nota = [k for k, b in base.items() if b["redacao_dada_por"].startswith("texto original")]
    diferentes = [
        k
        for k in sem_nota
        if k in original
        and chave(nota.sub("", original[k])) != chave(nota.sub("", base[k]["texto"]))
    ]
    # As 2 diferenças são ruído: "26." solto no fim do art. 27 do HTML e o aviso "Este texto não
    # substitui o publicado no D.O." no fim do art. 51 do compilado.
    assert diferentes == ["article:27", "article:51"]
    assert len(base) - len(original) == 142  # dispositivos criados por alterações até a RN 1.137
