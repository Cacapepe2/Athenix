"""Leitura do DOU: HTML x PDF certificado dos atos reais em tests/fontes_impacto/dou/.

Cada teste cobre uma causa GERAL de divergência (vale para qualquer página do DOU ou PDF de
colunas), usando o arquivo real; nenhuma regra aqui é específica de um ato.
"""

import pdfplumber
import pytest

from athenix import dou, structure
from athenix.config import Settings
from scripts import comparar_dou as cd

PASTA = cd.PASTA
PARES = ["dou_dsp20261293", "dou_ren20261162", "dou_ren20261174"]


def _pdf(nome):
    return (PASTA / f"{nome}_certificada.pdf").read_bytes()


def _html(nome):
    return (PASTA / f"{nome}.html").read_bytes()


def test_pagina_do_dou_em_duas_colunas_e_lida_coluna_por_coluna():
    with pdfplumber.open(PASTA / "dou_ren20261174_certificada.pdf") as pdf:
        lados = structure.page_sides(pdf.pages[0])
    assert len(lados) == 2
    direita = lados[1].extract_text()
    assert "RESOLUÇÃO NORMATIVA Nº 1.174" in direita
    assert "PORTARIA SNTEP/MME" not in direita  # o outro ato fica na coluna da esquerda


def test_coluna_unica_continua_lida_como_antes():
    with pdfplumber.open(PASTA / "dou_ren20261162_certificada.pdf") as pdf:
        pagina = pdf.pages[0]
        assert structure.page_sides(pagina) == [pagina]
        assert structure.page_text(pagina) == pagina.extract_text()


def test_pagina_de_tabela_nao_vira_duas_colunas():
    # Página real de uma tabela de 3 colunas: o vão entre colunas não é corredor de texto.
    with pdfplumber.open(PASTA.parent.parent / "norma_poc/ren20251137.pdf") as pdf:
        assert structure.column_gutter(pdf.pages[16]) is None


@pytest.mark.parametrize("nome", PARES)
def test_html_do_dou_separa_ato_de_navegacao_e_botoes(nome):
    lido = dou.ler_html(_html(nome))
    assert lido["texto"].startswith(lido["titulo"]["titulo"])  # sem "Caminho de Navegação"
    assert (
        "Versão certificada" not in lido["texto"] and "Publicador de Conteúdos" not in lido["texto"]
    )
    assert {r["tipo"] for r in lido["ruido"]} >= {
        "cabecalho_portal",
        "botoes_materia",
        "rodape_portal",
    }
    assert lido["publicacao"]["secao"] == "1"


@pytest.mark.parametrize(
    ("nome", "pagina", "edicao"),
    [
        ("dou_ren20261174", "68", "207"),
        ("dou_ren20261162", "92", "116"),
        ("dou_dsp20261293", "66", "75"),
    ],
)
def test_cabecalho_rodape_e_numero_da_pagina_ficam_como_ruido(nome, pagina, edicao):
    html, pdf = dou.ler_html(_html(nome)), dou.ler_pdf(_pdf(nome))
    tipos = {r["tipo"] for r in pdf["ruido"]}
    assert {"cabecalho_dou", "rodape_dou"} <= tipos
    assert pdf["paginas"][0]["numero_dou"] == pagina == html["publicacao"]["pagina"]
    assert html["publicacao"]["edicao"] == edicao
    texto = "\n".join(a["texto"] for a in pdf["atos"])
    for marca in ("ISSN 1677-7042", "autenticidade.html", "Documento assinado digitalmente"):
        assert marca not in texto


def test_atos_da_mesma_pagina_sao_separados_pelo_titulo():
    pdf = dou.ler_pdf(_pdf("dou_ren20261174"))
    numeros = [a["titulo"]["numero"] for a in pdf["atos"]]
    # 16820 e 16822 têm o título sem o "DE" antes do mês ("27 OUTUBRO DE 2026").
    assert numeros == ["3258", "16820", "16822", "16823", "16824", "1174"]
    alvo = dou.escolher_ato(pdf, dou.ler_html(_html("dou_ren20261174"))["titulo"])
    assert alvo["titulo"]["numero"] == "1174" and "PORTARIA" not in alvo["texto"]
    assert alvo["orgao"] == ["AGÊNCIA NACIONAL DE ENERGIA ELÉTRICA", "DIRETORIA COLEGIADA"]


def test_texto_branco_invisivel_e_ruido_e_nao_conteudo():
    pdf = dou.ler_pdf(_pdf("dou_ren20261162"))
    invisivel = [r for r in pdf["ruido"] if r["tipo"] == "texto_invisivel"]
    assert invisivel and "W:0.0035cm" in invisivel[0]["texto"]
    assert "W:0.0035cm" not in pdf["atos"][0]["texto"]


def test_bloco_citado_nao_troca_a_norma_alvo_pela_norma_que_cita():
    # A 1ª linha do bloco do art. 35-A cita a RN 1.029; no HTML a citação cabe numa linha, no PDF
    # quebra. A norma-alvo do bloco é a RN 875 (caput do art. 2º) nos dois.
    par = cd.ler_par("dou_ren20261162")
    donos = {}
    for lado in ("h", "p"):
        ex, _ = cd.extrair(par[lado])
        donos[lado] = [u["owner"] for u in ex["units"] if u["label"] == "35-A"]
    assert donos["h"] == donos["p"] and "875" in donos["h"][0] and "1.029" not in donos["h"][0]


def test_remissao_a_anexo_no_inicio_de_linha_quebrada_nao_e_anexo():
    ex = structure.extract(_pdf("dou_ren20261162"), "application/pdf", Settings())
    assert not [u for u in ex["units"] if u["kind"] == "annex"]
    texto = (
        "Art. 1º Texto.\nAnexo I do Decreto nº 2.335, de 1997, e no que consta\nANEXO I\nTabela\n"
    )
    marcadores, _ = structure.segment(texto, [{"number": 1, "start": 0, "end": len(texto)}])
    assert [m["label"] for m in marcadores if m["kind"] == "annex"] == ["I"]  # só o "ANEXO I" real


@pytest.mark.parametrize("nome", PARES)
def test_html_x_pdf_na_area_coberta_so_difere_em_espacos(nome):
    r = cd.comparar(nome)
    assert {d["tipo"] for d in r["texto"]["diferencas"]} <= {"espaçamento"}
    e = r["estrutura"]
    assert e["so_no_pdf"] == e["so_no_html"] == e["texto_diferente_apos_normalizar"] == []
    assert e["alteradas"]["html"] == e["alteradas"]["pdf"]
    assert r["obrigacoes_prazos_vigencia"]["so_no_html"] == []
    assert r["obrigacoes_prazos_vigencia"]["so_no_pdf"] == []
    assert r["normas_citadas"]["so_no_html"] == r["normas_citadas"]["so_no_pdf"] == []
    assert r["citacoes_literais"]["html_ausente_no_pdf"] == []
    assert r["citacoes_literais"]["pdf_ausente_no_html"] == []


def test_pdf_certificado_e_so_a_pagina_do_ato():
    # Pares completos: só o despacho (cabe na página). As resoluções continuam nas páginas seguintes.
    cobertura = {n: cd.comparar(n)["texto"]["cobertura"] for n in PARES}
    assert cobertura["dou_dsp20261293"] >= 0.999
    assert cobertura["dou_ren20261162"] < 0.5 and cobertura["dou_ren20261174"] < 0.2
