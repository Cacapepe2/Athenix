"""Extração e segmentação independentes; offsets no texto canônico, sem reparos ocultos."""

import codecs
import io
import re
from html.parser import HTMLParser
from importlib.metadata import version

from bs4 import BeautifulSoup

from .db import digest
from .evidence import key

BOMS = (
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)
META_CHARSET = re.compile(rb"""<meta[^>]+charset\s*=\s*["']?\s*([A-Za-z0-9_.:-]+)""", re.I)
# WHATWG Encoding: navegadores leem rótulos latin-1/ascii como windows-1252.
LEGACY = {"iso-8859-1", "iso8859-1", "latin1", "latin-1", "l1", "cp819", "ascii", "us-ascii"}
# Mojibake típico: UTF-8 lido como 1252 (Ã§, â€), byte inválido (�) e Latin Extended-A, ausente
# do português (ş, ă, ŕ, ę, ő surgem de windows-1252 lido como windows-1250).
SUSPECT = re.compile("�|Ã[\u0080-¿]|Â[\u0080-¿]|â€|[Ā-ſ]")
SUSPECT_LIMIT = 3  # shortcut: limiar fixo; calibrar com corpus rotulado se entrarem textos não PT

# "Art." / "ART." abre artigo; "art." minúsculo no início da linha é remissão quebrada (LC 95/1998).
ARTICLE = re.compile(r'^\s*[“"]?\s*(?:Art|ART)\.?\s*(\d+(?:[º°])?(?:-[A-Z])?)\.?\s*')
# "§ 6º do art. 15" no início da linha é remissão quebrada: o texto de um parágrafo começa com
# maiúscula (LC 95/1998), nunca com "do", "da", "deste", "e"... (o "o" é o ordinal sobrescrito).
PARAGRAPH = re.compile(
    r'^\s*[“"]?\s*(§\s*\d+(?!\d)[º°]?|Parágrafo único)\.?'
    r"(?!\s*[º°]?\s*(?-i:o\s+)?(?-i:d[oa]s?|dest[ea]s?|n[oa]s?|aos?|e|ou)\b)\s*",
    re.I,
)
CLAUSE = re.compile(r'^\s*[“"]?\s*([IVXLCDM]+)\s*[–—-]\s+')
LETTER = re.compile(r'^\s*[“"]?\s*([a-z])\)\s+')
ITEM = re.compile(r'^\s*[“"]?\s*(\d+(?:-[A-Z])?)\.\s+')
# "Anexo I do Decreto..." no início de uma linha quebrada é remissão no meio da frase, não anexo: a
# continuação em minúscula ("do", "da", "ao"...) a denuncia; "ANEXO I DA RESOLUÇÃO" segue anexo.
ANNEX = re.compile(
    r'^\s*[“"]?\s*ANEXO\s+([IVXLCDM\d]+)(?!\s*[º°]?\s*(?-i:d[oae]s?|n[oa]s?|aos?|e|ou|dest[ea]s?)\b)',
    re.I,
)
TABLE = re.compile(r"^\s*Tabela\s+(\d+)", re.I)
# Título/Capítulo/Seção sozinho na linha (ou "– Nome"): encerra o dispositivo anterior, para o
# texto do título não vazar para ele (ex.: "Seção VII Das Sanções e Penalidades" após um §).
HEADING = re.compile(
    r'^\s*[“"]?\s*((?:TÍTULO|CAPÍTULO|SEÇÃO|SUBSEÇÃO|Título|Capítulo|Seção|Subseção)\s+'
    r"(?:[IVXLCDM]+|\d+(?:\.\d+)*))\s*(?:[–—-]\s*[A-ZÀ-Ú][^\n]{0,80})?\s*$"
)
ALTERACAO = r"altera|redação|passa|fica|resolução"
ACT = re.compile(
    r"(?:Resolução(?:\s+Normativa)?|Lei|Decreto|Portaria)\s*(?:n[º°o.]*)?\s*[\d.]+(?:/\d{4})?", re.I
)
MONTHS = {
    name: i + 1
    for i, name in enumerate(
        (
            "janeiro",
            "fevereiro",
            "março",
            "abril",
            "maio",
            "junho",
            "julho",
            "agosto",
            "setembro",
            "outubro",
            "novembro",
            "dezembro",
        )
    )
}
# Aceita 30/10/2025, 30-10-2025, 30.10.2025 (rodapé "D.O. de") e "1º de julho de 2024".
DATE = re.compile(
    r"\b(?P<d>\d{1,2})(?P<sep>[/.-])(?P<m>\d{1,2})(?P=sep)(?P<y>\d{4})\b"
    r"|\b(?P<day>\d{1,2})[º°]?\s+de\s+(?P<month>"
    + "|".join(MONTHS)
    + r")\s+de\s+(?P<year>\d{4})\b",
    re.I,
)


def decode_html(content, charset=None):
    """Bytes → texto na ordem do WHATWG: BOM, cabeçalho HTTP, <meta>, UTF-8 estrito, windows-1252."""
    for bom, encoding in BOMS:
        if content.startswith(bom):
            return content.decode(encoding), encoding, "BOM"
    meta = META_CHARSET.search(content[:4096])
    declared = ((charset, "cabeçalho HTTP"), (meta and meta.group(1).decode("ascii"), "meta"))
    for label, method in declared:
        if not label:
            continue
        encoding = "windows-1252" if label.lower() in LEGACY else label.lower()
        try:
            return content.decode(encoding), encoding, method
        except (LookupError, UnicodeDecodeError):
            continue
    try:
        return content.decode("utf-8"), "utf-8", "UTF-8 estrito"
    except UnicodeDecodeError:
        return content.decode("windows-1252", errors="replace"), "windows-1252", "padrão legado"


class _PlainText(HTMLParser):
    """Leitura do HTML pela biblioteca padrão, sem a seleção de conteúdo do extrator."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        self.skip += tag in {"script", "style"}

    def handle_endtag(self, tag):
        self.skip = max(0, self.skip - (tag in {"script", "style"}))

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def independent_source(content, media, charset=None):
    """Segunda leitura da fonte por outro motor. Citação só é verificada se aparecer nela."""
    try:
        if media == "text/html":
            text, encoding, method = decode_html(content, charset)
            parser = _PlainText()
            parser.feed(text)
            parser.close()
            rendered, engine = "".join(parser.parts), f"html.parser+{encoding} ({method})"
        else:
            import pypdfium2

            pdf = pypdfium2.PdfDocument(content)
            try:
                rendered = "\n".join(page.get_textpage().get_text_range() for page in pdf)
            finally:
                pdf.close()
            engine = "pypdfium2/" + version("pypdfium2")
    except Exception as error:  # sem segunda leitura, nenhuma citação é confirmável
        return {"engine": None, "trusted": False, "suspect": 0, "samples": [], "key": "",
                "error": type(error).__name__}  # fmt: skip
    found = SUSPECT.findall(rendered)
    return {
        "engine": engine,
        "trusted": len(found) < SUSPECT_LIMIT,
        "suspect": len(found),
        "samples": sorted(set(found))[:5],
        "key": key(rendered),
    }


def detect_media(content, limit):
    if not content or len(content) > limit:
        raise ValueError("Arquivo vazio ou acima do limite de 10 MiB.")
    if content.startswith(b"%PDF-"):
        return "application/pdf"
    beginning = content[:4096].decode("utf-8-sig", errors="replace").lstrip()
    if re.search(r"<(?:!doctype\s+html|html|head|body|article|main)\b", beginning, re.I):
        return "text/html"
    raise ValueError("Conteúdo não reconhecido. Envie PDF ou HTML; a extensão não define o tipo.")


def parse_date(match):
    from datetime import date

    g = match.groupdict()
    month = int(g["m"]) if g["m"] else MONTHS[g["month"].lower()]
    try:
        return date(int(g["y"] or g["year"]), month, int(g["d"] or g["day"])).isoformat()
    except ValueError:
        return None


def act_dates(text):
    found = []
    for match in DATE.finditer(text):
        context = text[max(0, match.start() - 100) : match.start()].lower()
        kind = None
        # Pista imediatamente anterior vence: "Brasília, 20 de junho" é assinatura, mesmo após
        # "entra em vigor na data de sua publicação" na linha de cima.
        if re.search(r"(?:brasília|assinad[oa] em)\s*,?\s*$", context):
            kind = "signature"
        elif re.search(r"publica(?:d[ao]|ção)|diário oficial|\bdou\b", context):
            kind = "publication"
        elif re.search(r"vig[êe]ncia|entra em vigor", context):
            kind = "effective"
        elif re.search(r"assina|brasília|resolução[^\n]{0,60}\bde\s*$", context):
            kind = "signature"
        parsed = parse_date(match)
        if kind and parsed:
            start = max(0, text.rfind("\n", 0, match.start()) + 1)
            end = text.find("\n", match.end())
            end = len(text) if end < 0 else end
            found.append(
                {"kind": kind, "date": parsed, "start": start, "end": end, "quote": text[start:end]}
            )
    publication = {d["date"] for d in found if d["kind"] == "publication"}
    vigor = r"entra(?:rá)?\s+em\s+vigor\s+na\s+data\s+de\s+sua\s+publicação"
    for match in re.finditer(vigor, text, re.I):
        if len(publication) != 1:  # sem data única de publicação, a vigência fica sem data
            break
        start = text.rfind("\n", 0, match.start()) + 1
        end = text.find("\n", match.end())
        end = len(text) if end < 0 else end
        found.append(
            {
                "kind": "effective",
                "date": next(iter(publication)),
                "start": start,
                "end": end,
                "quote": text[start:end],
                "basis": "publication",
            }
        )
    return found


def is_title(line):
    """Nome de título: maiúsculas ("DA LICITAÇÃO") ou "Das Sanções e Penalidades", sem pontuação final."""
    line = line.strip()
    return (
        len(line) <= 120
        and line[-1] not in ".;:,"
        and (line == line.upper() or re.match(r"D[aeo]s?\s", line) is not None)
    )


def segment(text, pages, faq=False):
    markers = []
    quoted, nesting, straight = False, 0, False
    heading_title = False
    target = None
    caput_art = None  # nº do artigo do próprio ato que abriu o bloco de alteração em curso
    stack = []
    offset = 0
    in_table = False
    warnings = []
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        article = ARTICLE.match(line)
        if quoted and article and caput_art is not None and not stripped.startswith(("“", '"')):
            # Texto oficial sem as aspas de fechamento nem "(NR)" (ex.: RN 1.148 da biblioteca da
            # ANEEL): o artigo seguinte do próprio ato, sem aspas, encerra o bloco.
            if int(re.match(r"\d+", article.group(1)).group()) == caput_art + 1:
                quoted, nesting, straight = False, 0, False
                warnings.append(
                    f"Bloco citado sem aspas de fechamento: encerrado antes do {line.strip()[:14]}"
                )
        # A 1ª linha de um bloco citado não troca a norma-alvo: a norma que ela cita é parte do
        # texto citado, e só o HTML (linha inteira) a deixaria visível ao ACT; no PDF ela quebra.
        if not quoted and not stripped.startswith(("“", '"')):
            acts = ACT.findall(line)
            if acts and re.search(ALTERACAO, line, re.I):
                target = acts[-1]
            if ARTICLE.match(line) and not stripped.startswith(("“", '"')):
                # Artigo próprio que abre bloco de alteração: a norma-alvo é a lei do caput inteiro,
                # que o HTML do planalto quebra em várias linhas ("Art. 5º A\nLei\nnº 9.648 ... passa").
                fim = min(
                    (p for p in (text.find("“", offset), text.find('"', offset)) if p >= 0),
                    default=len(text),
                )
                caput = text[offset : min(fim, offset + 600)]
                citados = ACT.findall(caput)
                if citados and re.search(ALTERACAO, caput, re.I):
                    target = " ".join(citados[0].split())
                    caput_art = int(re.match(r"\d+", ARTICLE.match(line).group(1)).group())
        starts_quote = stripped.startswith(("“", '"'))
        owner = target if quoted or starts_quote else "self"
        kind, label, depth, matched = None, None, 0, None
        question = re.match(r"^\s*(\d+\.\d+)\s+", line) if faq else None
        if question:
            kind, label, depth = "question", question.group(1), 2
        for pattern, candidate_kind, level in (
            (HEADING, "heading", 0),
            (ARTICLE, "article", 1),
            (PARAGRAPH, "paragraph", 2),
            (ANNEX, "annex", 1),
            (TABLE, "table", 5),
            (CLAUSE, "clause", 3),
            (ITEM, "item", 4),
            (LETTER, "letter", 4),
        ):
            if question:
                break
            matched = pattern.match(line)
            if matched and pattern is PARAGRAPH:
                # A remissão ("§ 6 o / do art. 15") pode continuar na linha seguinte do HTML.
                matched = pattern.match(text[offset : offset + len(line) + 40])
            if matched:
                if in_table and candidate_kind in {"letter", "clause"}:
                    continue
                kind, label, depth = candidate_kind, matched.group(1), level
                break
        if not kind and re.search(r"[=∑∫]|\b[fF]\s*\([^)]*\)\s*=", line):
            kind, label, depth = "formula", str(len(markers) + 1), 5
        # O título guarda só o próprio nome; o texto seguinte sem marcador (ex.: artigo que o HTML
        # quebrou) abre unidade própria, para não sumir da detecção de obrigações.
        if kind:
            heading_title = kind == "heading"
        elif heading_title and stripped.strip() and not is_title(stripped):
            kind, label, depth = "unstructured", "Texto após título", 1
            heading_title = False
        if kind == "letter":
            # No PRODIST as alíneas pertencem ao item numerado; na LC 95 ficam sob o inciso.
            context = next(
                (
                    m
                    for m in reversed(stack)
                    if m["owner"] == owner
                    and m["kind"] in {"item", "clause", "paragraph", "article", "annex"}
                ),
                None,
            )
            if context and context["kind"] == "item":
                depth = context["depth"] + 1
        if kind:
            if kind in {"article", "paragraph", "item", "annex", "heading"}:
                in_table = False
            if kind == "table":
                in_table = True
            while stack and (stack[-1]["depth"] >= depth or stack[-1]["owner"] != owner):
                stack.pop()
            parent = stack[-1]["id"] if stack else None
            identifier = f"u{len(markers) + 1:04d}"
            marker = {
                "id": identifier,
                "kind": kind,
                "label": label,
                "depth": depth,
                "parent": parent,
                "owner": owner or "unresolved",
                "start": offset,
            }
            markers.append(marker)
            if kind != "heading":  # título fecha o anterior, mas não vira pai
                stack.append(marker)
            if owner is None:
                warnings.append("Bloco citado com norma-alvo não resolvida: " + identifier)
        # Profundidade: “ANEXO 8.C” dentro de um bloco citado não encerra o bloco externo.
        for character in line:
            if character == "“":
                nesting += 1
            elif character == "”":
                nesting = max(0, nesting - 1)
            elif character == '"':
                straight = not straight
        # LC 95: "(NR)"/"(AC)" encerra a nova redação, com ou sem as aspas de fechamento (o DOU as omite
        # em alguns blocos).
        if re.search(r'[”"]\s*\((?:NR|AC)\)|\((?:NR|AC)\)\s*$', line):
            nesting, straight = 0, False
        quoted = nesting > 0 or straight
        offset += len(line)
    if not markers or markers[0]["start"] > 0:
        markers.insert(
            0,
            {
                "id": "preamble",
                "kind": "unstructured",
                "label": "Preâmbulo",
                "depth": 0,
                "parent": None,
                "owner": "self",
                "start": 0,
            },
        )
    for index, marker in enumerate(markers):
        marker["end"] = markers[index + 1]["start"] if index + 1 < len(markers) else len(text)
        marker["text"] = text[marker["start"] : marker["end"]]
        marker["pages"] = [
            p["number"] for p in pages if p["start"] < marker["end"] and p["end"] > marker["start"]
        ]
    if not any(m["kind"] == "article" or (faq and m["kind"] == "question") for m in markers):
        warnings.append("Estrutura LC 95 não reconhecida; conteúdo não estruturado exige revisão.")
    if quoted:
        warnings.append("Aspas sem fechamento: autoria do bloco precisa de conferência.")
    return markers, warnings


def struck_runs(page):
    """Palavras riscadas da página (redação revogada em textos compilados), em sequências.

    Riscado = linha horizontal fina que cobre ao menos metade da palavra na altura do meio dela;
    sublinhado (na base da palavra) e bordas de tabela entre linhas não contam.
    """
    rules = [
        r
        for r in (*page.lines, *page.rects)
        if abs(r["bottom"] - r["top"]) < 1.5 and r["x1"] - r["x0"] > 3
    ]
    runs, current = [], []
    for word in page.extract_words() if rules else []:
        height, width = word["bottom"] - word["top"], word["x1"] - word["x0"]
        middle = (word["top"] + word["bottom"]) / 2
        if any(
            abs((r["top"] + r["bottom"]) / 2 - middle) <= 0.3 * height
            and min(r["x1"], word["x1"]) - max(r["x0"], word["x0"]) >= 0.5 * width
            for r in rules
        ):
            current.append(word["text"])
        elif current:
            runs.append(current)
            current = []
    return runs + [current] if current else runs


def locate_struck(text, runs):
    """Intervalos [início, fim) de cada sequência riscada no texto da página, em ordem; None se
    alguma não for encontrada (aí não dá para separar com segurança o que está riscado)."""
    chars = [i for i, c in enumerate(text) if not c.isspace()]
    flat = "".join(text[i] for i in chars)
    spans, cursor = [], 0
    for run in runs:
        needle = "".join("".join(run).split())
        at = flat.find(needle, cursor)
        if at < 0:
            return None
        spans.append((chars[at], chars[at + len(needle) - 1] + 1))
        cursor = at + len(needle)
    return spans


def mark_struck(units, text, pages, struck):
    """Marca dispositivos com texto riscado: "revoked" (todo riscado) ou "partial" (parte riscada
    ou página cujo riscado não foi localizado). Os dois ficam fora da interpretação."""
    covered = bytearray(len(text))
    unsure = set()
    for page, runs in zip(pages, struck or []):
        if not runs:
            continue
        spans = locate_struck(text[page["start"] : page["end"]], runs)
        if spans is None:
            unsure.add(page["number"])
            continue
        for start, end in spans:
            covered[page["start"] + start : page["start"] + end] = b"\x01" * (end - start)
    revoked = partial = 0
    for unit in units:
        body = [i for i in range(unit["start"], unit["end"]) if not text[i].isspace()]
        hit = sum(covered[i] for i in body)
        if body and hit >= 0.9 * len(body):
            unit["struck"] = "revoked"
            revoked += 1
        elif hit or unsure & set(unit.get("pages", [])):
            unit["struck"] = "partial"
            partial += 1
    if revoked or partial:
        return [
            f"Texto riscado na fonte: {revoked} dispositivo(s) com redação revogada e {partial} com "
            "riscado parcial ficam fora da interpretação e do cálculo; citações pendentes."
        ]
    return []


GUTTER_MIN = 8.0  # largura mínima (pt) do corredor entre colunas
GUTTER_LINES = 15  # linhas de texto corrido exigidas em cada coluna
GUTTER_FILL = 0.6  # largura mediana das linhas / largura da metade da página: texto corrido


def _median(values):
    ordered = sorted(values)
    return ordered[len(ordered) // 2] if ordered else 0


def _column_lines(words, left, right):
    rows = {}
    for w in words:
        if left <= (w["x0"] + w["x1"]) / 2 < right:
            rows.setdefault(round(w["top"] / 3), []).append(w)
    return [r for r in rows.values() if len(r) >= 4]


def column_gutter(page):
    """x do corredor vertical entre duas colunas de texto corrido (ex.: página do DOU), ou None.

    Conservador: só há corredor se uma faixa livre de palavras de ≥ 8 pt cruza quase toda a
    página e cada lado tem muitas linhas largas. Tabela e página de coluna única dão None."""
    words = page.extract_words()
    if len(words) < 150:
        return None
    width = int(page.width)
    cover = [0] * (width + 2)
    for w in words:
        for x in range(int(w["x0"]) + 1, min(int(w["x1"]) + 1, width + 1)):
            cover[x] += 1
    tolerance = max(2, int(len(words) * 0.015))
    best, run = None, None
    for x in range(int(width * 0.3), int(width * 0.7) + 1):
        if cover[x] <= tolerance:
            run = (run[0], x) if run else (x, x)
            if best is None or run[1] - run[0] > best[1] - best[0]:
                best = run
        else:
            run = None
    if not best or best[1] - best[0] < GUTTER_MIN:
        return None
    middle = (best[0] + best[1]) / 2
    for left, right, span in ((0, middle, middle), (middle, width, width - middle)):
        lines = _column_lines(words, left, right)
        wide = [max(w["x1"] for w in r) - min(w["x0"] for w in r) for r in lines]
        if len(lines) < GUTTER_LINES or _median(wide) < GUTTER_FILL * span:
            return None
    if any(t.bbox[0] < middle < t.bbox[2] for t in page.find_tables()):
        return None  # o "corredor" é o vão entre colunas de uma tabela que cruza a página
    return middle


def page_sides(page):
    """Páginas (filtradas) na ordem de leitura: uma por coluna, esquerda antes da direita."""
    gutter = column_gutter(page)
    if gutter is None:
        return [page]

    # Cada palavra inteira fica na coluna do seu centro: um número que cruza o corredor (ex.: o
    # número da página do DOU, no meio do rodapé) não é cortado ao meio.
    rows = {}
    for w in page.extract_words():
        rows.setdefault(round(w["top"]), []).append(w)

    def word_center(char):
        cx, cy = (char["x0"] + char["x1"]) / 2, round(char["top"])
        for row in (cy - 1, cy, cy + 1):
            for w in rows.get(row, ()):
                if w["x0"] - 0.5 <= cx <= w["x1"] + 0.5:
                    return (w["x0"] + w["x1"]) / 2
        return cx

    def side(left):
        def keep(obj):
            if obj.get("object_type") != "char":
                return True
            return (word_center(obj) < gutter) is left

        return page.filter(keep)

    return [side(True), side(False)]


def page_text(page):
    sides = page_sides(page)
    if len(sides) == 1:
        return page.extract_text() or ""  # coluna única: idêntico à leitura anterior
    return "\n".join(s.extract_text() or "" for s in sides)


def extract(content, media, settings, role=None, charset=None):
    warnings, links = [], []
    pieces, struck = [], []
    faq = role == "clarification"
    if media == "text/html":
        # Decodificar antes: o palpite do BeautifulSoup leu windows-1252 como windows-1250.
        decoded, encoding, method = decode_html(content, charset)
        soup = BeautifulSoup(decoded, "html.parser")
        title = soup.title.get_text() if soup.title else ""
        faq = faq or bool(re.search(r"\bFAQ\b|perguntas frequentes", title, re.I))
        for tag in soup(["script", "style", "noscript", "iframe", "object", "svg"]):
            tag.decompose()
        main_content = (
            soup.find(id="content-core")
            or soup.find("main")
            or soup.find("article")
            or soup.body
            or soup
        )
        for index, link in enumerate(main_content.find_all("a", href=True)):
            links.append(
                {
                    "id": f"link-{index}",
                    "url": link["href"],
                    "label": link.get_text(" ", strip=True),
                    "page": 1,
                    "state": "identified",
                }
            )
        pieces = [main_content.get_text("\n", strip=True)]
        # Texto compilado (ex.: planalto.gov.br) marca a redação revogada com <strike>, como o PDF.
        riscado = ["strike", "s", "del"]
        struck = [
            [
                words
                for tag in main_content.find_all(riscado)
                if not tag.find_parent(riscado) and (words := tag.get_text(" ", strip=True).split())
            ]
        ]
        extractor = f"beautifulsoup4/{version('beautifulsoup4')}:main-v1;{encoding} ({method})"
    else:
        import pdfplumber

        extractor = "pdfplumber/" + version("pdfplumber")
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                if len(pdf.pages) > settings.max_pages:
                    raise ValueError("PDF excede o limite de páginas.")
                for page in pdf.pages:
                    pieces.append(page_text(page))
                    struck.append(struck_runs(page))
                    if not pieces[-1].strip():
                        warnings.append(f"Página {page.page_number} sem texto: requer OCR.")
                    for annotation in page.hyperlinks:
                        links.append(
                            {
                                "id": f"link-{len(links)}",
                                "url": annotation.get("uri", ""),
                                "label": "Link do PDF",
                                "page": page.page_number,
                                "bbox": [annotation.get(k) for k in ("x0", "top", "x1", "bottom")],
                                "state": "identified",
                            }
                        )
        except ValueError:
            raise
        except Exception as error:
            raise ValueError(
                "PDF corrompido, protegido ou não suportado; original preservado."
            ) from error
    source = independent_source(content, media, charset)
    return from_pieces(pieces, links, warnings, extractor, settings, faq, source, struck)


def from_pieces(pieces, links, warnings, extractor, settings, faq=False, source=None, struck=None):
    """Monta o resultado a partir do texto de cada página; usado também pelo pipeline com OCR."""
    if not source:
        warnings.append("Sem segunda leitura da fonte: citações ficam pendentes.")
    elif not source["trusted"]:
        warnings.append(
            f"Texto da fonte possivelmente corrompido ({source['suspect']} ocorrências como "
            f"{' '.join(source['samples'])}): citações ficam pendentes."
        )
    pages = []
    text = "\n\f\n".join(pieces)
    if len(text) > settings.max_text:
        raise ValueError("Texto extraído excede o limite de segurança.")
    offset = 0
    for number, piece in enumerate(pieces, start=1):
        pages.append(
            {
                "number": number,
                "start": offset,
                "end": offset + len(piece),
                "characters": len(piece),
            }
        )
        offset += len(piece) + 3
    units, structural_warnings = segment(text, pages, faq)
    warnings.extend(structural_warnings)
    warnings.extend(mark_struck(units, text, pages, struck))
    if re.search(r"ignore.{0,40}instru|system prompt|revele.{0,20}senha", text, re.I):
        warnings.append("Possível prompt injection: conteúdo tratado como dado não confiável.")
    if any(u["kind"] in {"table", "formula"} for u in units):
        warnings.append("Tabelas e fórmulas preservadas como texto; exigem conferência visual.")
    references = []
    for unit in units:
        for match in re.finditer(
            r"\b(?:art\.?\s*\d+[º°]?(?:-[A-Z])?|Anexo\s+[IVXLCDM]+|Tabela\s+\d+)",
            unit["text"],
            re.I,
        ):
            references.append(
                {
                    "unit_id": unit["id"],
                    "quote": match.group(),
                    "target": None,
                    "state": "unresolved",
                }
            )
    return {
        "text": text,
        "text_hash": digest(text.encode()),
        "extractor": extractor,
        "pages": pages,
        "units": units,
        "links": links,
        "warnings": warnings,
        "dates": act_dates(text),
        "references": references,
        "source": source,
    }
