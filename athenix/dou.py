"""Leitura do Diário Oficial da União (in.gov.br): matéria em HTML e página da versão certificada.

Os dois formatos trazem o mesmo ato com ruído diferente: o HTML tem navegação, botões e rodapé do
portal; o PDF é a PÁGINA do jornal (várias colunas, vários atos, cabeçalho e rodapé do DOU, número
de página e selo ICP-Brasil), e o ato pode continuar na página seguinte. Aqui o ato pedido é
conteúdo e o resto fica como ruído rotulado. O texto lido nunca é alterado; a normalização é só
da comparação (`athenix.normalizacao`).
"""

import io
import re
import statistics

import pdfplumber
from bs4 import BeautifulSoup

from .structure import decode_html, page_sides

TIPOS = (
    r"RESOLUÇÃO(?:\s+(?:NORMATIVA|AUTORIZATIVA|HOMOLOGATÓRIA|CONJUNTA))?|DESPACHO|PORTARIA"
    r"(?:\s+INTERMINISTERIAL)?|DECRETO|LEI|INSTRUÇÃO\s+NORMATIVA|AVISO|EDITAL|ATO|ERRATA|RETIFICAÇÃO"
)
TITULO = re.compile(
    rf"^(?P<tipo>{TIPOS})(?:\s+(?P<sigla>[A-ZÀ-Ú][A-ZÀ-Ú/-]*))?\s+N[º°o]\s*(?P<numero>[\d.]+)"
    r"(?:/(?P<ano_n>\d{4}))?,?\s+DE\s+(?P<dia>\d{1,2})[º°]?\s+(?:DE\s+)?(?P<mes>[A-ZÇÀ-Ú]+)\s+DE\s+"
    r"(?P<ano>\d{4})\s*$"
)
MESES = (
    "JANEIRO FEVEREIRO MARÇO ABRIL MAIO JUNHO JULHO AGOSTO SETEMBRO OUTUBRO NOVEMBRO DEZEMBRO"
).split()
CABECALHO = (
    re.compile(r"^Seção\s+\d\b"),
    re.compile(r"\bISSN\s+\d{4}-\d{3}[\dX]\b"),
    re.compile(r"^Nº\s+\d+,\s+\w+-feira,\s+\d{1,2}\s+de\s+\w+\s+de\s+\d{4}$"),
)
RODAPE = (
    re.compile(r"^Este documento pode ser verificado no endereço eletrônico"),
    re.compile(r"autenticidade\.html,\s+pelo\s+código\s+\d+"),
    re.compile(r"^Documento assinado digitalmente conforme MP"),
    re.compile(r"Infraestrutura de Chaves Públicas Brasileira"),
    re.compile(r"^ICP\s*-?\s*Brasil$"),
)
PREAMBULO = re.compile(
    r"^(?:O|A|OS|AS)\s+[A-ZÀ-Ú-]{4,}(?:\s+[A-ZÀ-Ú/-]+){1,}"
)  # "O DIRETOR-GERAL DA ..."


def parse_titulo(linha):
    """{tipo, sigla, numero, data} de um título de ato do DOU, ou None."""
    m = TITULO.match(" ".join((linha or "").split()))
    if not m or m["mes"].upper() not in MESES:
        return None
    mes = MESES.index(m["mes"].upper()) + 1
    return {
        "tipo": " ".join(m["tipo"].split()).upper(),
        "sigla": m["sigla"],
        "numero": m["numero"].replace(".", ""),
        "data": f"{m['ano']}-{mes:02d}-{int(m['dia']):02d}",
        "titulo": " ".join(linha.split()),
    }


def _chave_ato(titulo):
    return (titulo["tipo"], titulo["numero"], titulo["data"])


# --- HTML -------------------------------------------------------------------------------------


def ler_html(content):
    """Matéria do DOU em HTML: metadados de publicação, cabeçalho do ato, texto e ruído do portal."""
    texto, encoding, _ = decode_html(content)
    soup = BeautifulSoup(texto, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()
    corpo = soup.find(class_="texto-dou")
    if corpo is None:
        raise ValueError("HTML sem o bloco do ato (texto-dou): não é uma matéria do DOU.")

    def campo(css):
        el = soup.find(class_=css)
        return el.get_text(" ", strip=True) if el else None

    secao = campo("secao-dou")
    titulo_el = corpo.find(class_="identifica")
    ementa_el = corpo.find(class_="ementa")
    titulo = parse_titulo(titulo_el.get_text(" ", strip=True)) if titulo_el else None
    ruido = [
        {"tipo": rotulo, "texto": el.get_text(" ", strip=True)[:120]}
        for rotulo, css in (
            ("cabecalho_portal", "cabecalho-dou"),
            ("botoes_materia", "barra-botoes-materia"),
            ("detalhes_publicacao", "detalhes-dou"),
        )
        if (el := soup.find(class_=css))
    ]
    if rodape := soup.find("footer"):
        ruido.append({"tipo": "rodape_portal", "texto": rodape.get_text(" ", strip=True)[:120]})
    return {
        "formato": "html",
        "codificacao": encoding,
        "publicacao": {
            "data": campo("publicado-dou-data"),
            "edicao": campo("edicao-dou-data"),
            "secao": re.sub(r"\D", "", secao or "") or None,
            "pagina": campo("secao-dou-data"),
            "orgao": campo("orgao-dou-data"),
        },
        "titulo": titulo,
        "ementa": ementa_el.get_text(" ", strip=True) if ementa_el else None,
        "texto": corpo.get_text("\n", strip=True),
        "ruido": ruido,
    }


# --- PDF --------------------------------------------------------------------------------------


def _classifica(linha, altura):
    """(rótulo de ruído, número da página lido na linha) ou (None, None) se for conteúdo."""
    texto = " ".join(linha["text"].split())
    if linha["top"] < altura * 0.1 and any(p.search(texto) for p in CABECALHO):
        return "cabecalho_dou", None
    if linha["bottom"] > altura * 0.9:
        # O número da página fica num círculo no centro do rodapé e pode vir colado a uma linha.
        sem_numero = re.sub(r"^\d{1,4}\s+|\s+\d{1,4}$", "", texto)
        if any(p.search(sem_numero) for p in RODAPE):
            numero = (
                re.match(r"^(\d{1,4})\s+", texto)
                or re.search(r"\s(\d{1,4})$", texto)
                or re.search(r"eletrônico\s+(\d{1,4})\s+Documento assinado", texto)  # coluna única
            )
            return "rodape_dou", numero.group(1) if numero else None
        if re.fullmatch(r"\d{1,4}", texto):
            return "numero_pagina", texto
    return None, None


def _branco(char):
    """Texto com cor de preenchimento (1, 1, 1[, 1]): conferido por renderização, o PDF do DOU o
    desenha em branco sobre branco."""
    cor = char.get("non_stroking_color")
    return isinstance(cor, (tuple, list)) and len(cor) >= 3 and all(v == 1 for v in cor)


def _tamanho(linha):
    return statistics.median(c["size"] for c in linha["chars"]) if linha["chars"] else 0


def ler_pdf(content):
    """Página(s) do DOU em PDF: linhas na ordem de leitura por coluna e atos separados pelo título."""
    paginas, ruido, linhas = [], [], []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            # Texto branco (cor de preenchimento 1,1,1) é invisível ao leitor humano; o DOU deixa
            # na camada de texto marcas como "W:0.0035cm H:0.0035cm" sob as linhas de pontos.
            invisivel = "".join(c["text"] for c in page.chars if _branco(c)).strip()
            if invisivel:
                ruido.append(
                    {"tipo": "texto_invisivel", "pagina": page.page_number, "texto": invisivel}
                )
                page = page.filter(lambda o: o.get("object_type") != "char" or not _branco(o))
            lados = page_sides(page)
            lidas = [
                (i, ln) for i, lado in enumerate(lados) for ln in lado.extract_text_lines()
                if ln["text"].strip()
            ]  # fmt: skip
            corpo = statistics.median([_tamanho(ln) for _, ln in lidas] or [0])
            info = {"pagina": page.page_number, "colunas": len(lados), "numero_dou": None}
            for coluna, ln in lidas:
                rotulo, numero = _classifica(ln, float(page.height))
                texto = ln["text"].rstrip()
                if rotulo:
                    ruido.append({"tipo": rotulo, "pagina": page.page_number, "texto": texto})
                    info["numero_dou"] = numero or info["numero_dou"]
                    continue
                linhas.append(
                    {
                        "texto": texto,
                        "pagina": page.page_number,
                        "coluna": coluna,
                        "titulo_de_secao": bool(corpo) and _tamanho(ln) >= 1.25 * corpo,
                    }
                )
            paginas.append(info)
    atos, orgao, anterior_foi_orgao, atual = [], [], False, None
    for ln in linhas:
        titulo = parse_titulo(ln["texto"])
        if ln["titulo_de_secao"] and not titulo:
            # Cabeçalho de órgão (letra maior), ruído que vale para os atos seguintes: linhas
            # seguidas compõem o caminho (AGÊNCIA ... / DIRETORIA COLEGIADA). Não encerra o ato.
            orgao = [*orgao, ln["texto"]] if anterior_foi_orgao else [ln["texto"]]
            anterior_foi_orgao = True
            ruido.append({"tipo": "cabecalho_orgao", "pagina": ln["pagina"], "texto": ln["texto"]})
            continue
        anterior_foi_orgao = False
        if titulo:
            atual = {
                "titulo": titulo,
                "orgao": list(orgao),
                "linhas": [],
                "paginas": {ln["pagina"]},
            }
            atos.append(atual)
        elif atual is None:
            ruido.append(
                {"tipo": "antes_do_primeiro_ato", "pagina": ln["pagina"], "texto": ln["texto"]}
            )
        else:
            atual["linhas"].append(ln["texto"])
            atual["paginas"].add(ln["pagina"])
    for ato in atos:
        ato["paginas"] = sorted(ato["paginas"])
        ato["texto"] = "\n".join(ato["linhas"])
    return {"formato": "pdf", "paginas": paginas, "atos": atos, "ruido": ruido}


def escolher_ato(pdf, titulo):
    """O ato da página que tem o título (tipo, número, data) do ato pedido; None se não estiver."""
    achados = [a for a in pdf["atos"] if _chave_ato(a["titulo"]) == _chave_ato(titulo)]
    return achados[0] if achados else None
