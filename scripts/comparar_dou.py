"""Consistência HTML x PDF dos atos do DOU em tests/fontes_impacto/dou/ (pipeline do Athenix, sem IA).

Para cada par (dou_<ato>.html + dou_<ato>_certificada.pdf) compara: cabeçalho, texto normalizado,
estrutura, obrigações/prazos/vigência, normas citadas e alteradas e citações literais, e lista cada
diferença com a causa provável. O PDF certificado é a PÁGINA do DOU: cobre só o começo do ato quando
ele continua na página seguinte, e essa parte ausente é "fora da cobertura", não diferença de leitura.

Uso: python scripts/comparar_dou.py [--json saida.json] [--legado]
  --legado: mede o "antes" com a leitura anterior (HTML inteiro pelo extrator geral; PDF sem colunas).
Texto lido nunca é alterado: a normalização (athenix.normalizacao) vale só para comparar.
"""

import argparse
import difflib
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pdfplumber  # noqa: E402

from athenix import dou, structure  # noqa: E402
from athenix.config import Settings  # noqa: E402
from athenix.normalizacao import chave, normalizar  # noqa: E402
from athenix.poc.compare import _keyed  # noqa: E402
from athenix.poc.semantic import deterministic_items  # noqa: E402

PASTA = ROOT / "tests/fontes_impacto/dou"
PAGINAS = [{"number": 1, "source": "text_layer", "state": "faithful", "reasons": []}]
SETTINGS = Settings()
CITADA = re.compile(
    r"(?P<tipo>Resolução\s+(?:Normativa|Autorizativa|Homologatória)|Lei(?:\s+Complementar)?|Decreto"
    r"|Portaria|Despacho)\s*(?:n[º°o.]*\s*)?(?P<num>\d{1,3}(?:\.\d{3})*|\d+)(?:\s*/\s*(?P<ano>\d{4}))?"
    r"(?:\s*,\s*de\s+(?P<dia>\d{1,2})[º°]?\s+de\s+(?P<mes>\w+)\s+de\s+(?P<ano2>\d{4}))?",
    re.I,
)


def pares():
    return sorted(p.name[: -len(".html")] for p in PASTA.glob("dou_*.html"))


# --- leitura ------------------------------------------------------------------------------------


def ementa_de(linhas):
    """Linhas entre o título e o preâmbulo ("O DIRETOR-GERAL ..."): a ementa do ato, se houver."""
    saida = []
    for ln in linhas:
        if dou.PREAMBULO.match(ln.strip()):
            break
        saida.append(ln.strip())
    else:
        return ""  # sem preâmbulo reconhecido: não arrisca chamar de ementa
    return " ".join(saida)


def ler_par(nome, legado=False):
    html = dou.ler_html((PASTA / f"{nome}.html").read_bytes())
    pdf_bytes = (PASTA / f"{nome}_certificada.pdf").read_bytes()
    pdf = dou.ler_pdf(pdf_bytes)
    alvo = dou.escolher_ato(pdf, html["titulo"])
    if alvo is None:
        raise ValueError(f"{nome}: o ato do HTML não está na página do PDF")
    h_linhas = html["texto"].split("\n")
    p_linhas = [alvo["titulo"]["titulo"], *alvo["linhas"]]
    if legado:
        conteudo = (PASTA / f"{nome}.html").read_bytes()
        h_texto = structure.extract(conteudo, "text/html", SETTINGS)["text"]
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as doc:
            p_texto = "\n".join(p.extract_text() or "" for p in doc.pages)
        return {"nome": nome, "html": html, "pdf": pdf, "alvo": alvo, "h": h_texto, "p": p_texto}
    return {
        "nome": nome,
        "html": html,
        "pdf": pdf,
        "alvo": alvo,
        "h": "\n".join(h_linhas),
        "p": "\n".join(p_linhas),
    }


# --- cabeçalho ----------------------------------------------------------------------------------


def cabecalho(par):
    h, p, alvo = par["html"], par["pdf"], par["alvo"]
    tp = alvo["titulo"]
    th = h["titulo"]
    cab_pdf = next(
        (r["texto"] for r in p["ruido"] if r["tipo"] == "cabecalho_dou" and "Nº" in r["texto"]), ""
    )
    m = re.search(r"Nº\s+(\d+),.*?(\d{1,2}) de (\w+) de (\d{4})", cab_pdf)
    mes = [x.lower() for x in dou.MESES].index(m.group(3).lower()) + 1 if m else None
    pub_pdf = {
        "edicao": m.group(1) if m else None,
        "data": f"{int(m.group(2)):02d}/{mes:02d}/{m.group(4)}" if m else None,
        "pagina": p["paginas"][0]["numero_dou"],
    }
    orgao_pdf = " / ".join(alvo["orgao"])
    ementa_h, ementa_p = ementa_de(par["h"].split("\n")[1:]), ementa_de(par["p"].split("\n")[1:])
    linhas = [
        ("tipo", th["tipo"], tp["tipo"]),
        ("número", th["numero"], tp["numero"]),
        ("data do ato", th["data"], tp["data"]),
        ("data de publicação", h["publicacao"]["data"], pub_pdf["data"]),
        ("edição", h["publicacao"]["edicao"], pub_pdf["edicao"]),
        ("página do DOU", h["publicacao"]["pagina"], pub_pdf["pagina"]),
        ("ementa", ementa_h, ementa_p),
    ]
    difs = []
    for campo, a, b in linhas:
        if chave(a or "") != chave(b or ""):
            difs.append({"onde": f"cabeçalho · {campo}", "html": a, "pdf": b})
    ck = lambda x: normalizar(x or "", espacos="nenhum", caixa=True)[0]  # noqa: E731
    partes_h = ck(h["publicacao"]["orgao"])
    if not alvo["orgao"]:
        difs.append(
            {
                "onde": "cabeçalho · órgão",
                "html": h["publicacao"]["orgao"],
                "pdf": None,
                "causa": "layout do DOU: o órgão é cabeçalho de seção e não vem junto do ato nesta página",
            }
        )
    elif not all(ck(o) in partes_h for o in alvo["orgao"]):
        difs.append(
            {"onde": "cabeçalho · órgão", "html": h["publicacao"]["orgao"], "pdf": orgao_pdf}
        )
    return {
        "campos": len(linhas) + 1,
        "diferencas": difs,
        "titulo_sigla": (th["sigla"], tp["sigla"]),
    }


# --- texto --------------------------------------------------------------------------------------


def _tokens(texto):
    norm, mapa = normalizar(texto, espacos="um")
    out = [(m.group(), m.start(), m.end()) for m in re.finditer(r"\S+", norm)]
    return norm, mapa, out


def alinhar(h_texto, p_texto):
    """Alinha o texto do PDF ao começo do texto do HTML, palavra a palavra, em forma normalizada.

    Devolve as diferenças (com a causa provável), a cobertura do PDF e o corte no texto original do
    HTML. A normalização só serve à comparação; o texto lido não muda."""
    hn, hmapa, ht = _tokens(h_texto)
    pn, _, pt = _tokens(p_texto)
    hw, pw = [t[0] for t in ht], [t[0] for t in pt]
    janela = min(len(hw), int(len(pw) * 1.15) + 20)
    sm = difflib.SequenceMatcher(None, hw[:janela], pw, autojunk=False)
    difs, fim_h = [], 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            fim_h = i2
            continue
        a, b = " ".join(hw[i1:i2]), " ".join(pw[j1:j2])
        contexto = " ".join(hw[max(i1 - 4, 0) : i1])
        if a.replace(" ", "") == b.replace(" ", ""):
            causa = (
                "leitura do PDF: a camada de texto da página justificada do DOU perde os espaços"
            )
            tipo = "espaçamento"
        elif tag == "delete" and j1 == len(pw):
            continue  # cauda do HTML além do fim do PDF: não é diferença, é falta de cobertura
        elif tag == "insert" and len(b) <= 2:
            causa, tipo = (
                "leitura do PDF: glifo solto da fonte do marcador (não existe no HTML)",
                "glifo",
            )
        else:
            causa, tipo = "a investigar", "texto"
        difs.append({"tipo": tipo, "html": a, "pdf": b, "contexto": contexto, "causa": causa})
        fim_h = max(fim_h, i2)
    fim_h = fim_h or 0
    corte = hmapa[ht[fim_h - 1][2] - 1] + 1 if fim_h else 0
    return {
        "palavras_html": len(hw),
        "palavras_pdf": len(pw),
        "palavras_html_cobertas": fim_h,
        "cobertura": round(fim_h / len(hw), 3) if hw else 0,
        "diferencas": difs,
        "corte_html": corte,
    }


# --- estrutura, obrigações, normas, citações ---------------------------------------------------


def extrair(texto):
    ex = structure.from_pieces([texto], [], [], "dou", SETTINGS)
    doc = {"file": "dou", "sha256": ex["text_hash"]}
    itens, _ = deterministic_items(doc, ex, PAGINAS)
    return ex, itens


def _citadas(texto):
    out = Counter()
    for m in CITADA.finditer(texto):
        tipo = " ".join(m["tipo"].split()).lower()
        ano = m["ano"] or m["ano2"] or ""
        out[f"{tipo} {m['num'].replace('.', '')}/{ano}"] += 1
    return out


def estrutura(ex_h, ex_p, corte):
    kh, kp = _keyed(ex_h, PAGINAS), _keyed(ex_p, PAGINAS)
    cobertas_h = {k: v for k, v in kh.items() if v["start"] < corte}
    so_pdf = sorted(set(kp) - set(cobertas_h))
    so_html = sorted(set(cobertas_h) - set(kp))
    divergentes = [
        k for k in set(kp) & set(cobertas_h) if chave(kp[k]["text"]) != chave(cobertas_h[k]["text"])
    ]
    contagem = lambda ks, d: dict(Counter(d[k]["kind"] for k in ks))  # noqa: E731
    return {
        "html_na_cobertura": contagem(cobertas_h, kh),
        "pdf": contagem(kp, kp),
        "html_fora_da_cobertura": len(kh) - len(cobertas_h),
        "so_no_pdf": ["|".join(map(str, k)) for k in so_pdf],
        "so_no_html": ["|".join(map(str, k)) for k in so_html],
        "texto_diferente_apos_normalizar": ["|".join(map(str, k)) for k in sorted(divergentes)],
        "alteradas": {
            "html": sorted({v["owner"] for v in cobertas_h.values() if v["owner"] != "self"}),
            "pdf": sorted({v["owner"] for v in kp.values() if v["owner"] != "self"}),
        },
    }


def _quote(item):
    """Trecho citado do item: o literal verificado ou, sem segunda leitura, o proposto (só texto)."""
    a = item["anchors"][0] if item["anchors"] else {}
    return a.get("quote") or a.get("proposed_quote") or ""


def itens_por_tipo(itens, corte=None):
    chaves = Counter()
    for it in itens:
        if corte is not None and it["locator"]["start"] >= corte:
            continue
        quote = chave(_quote(it))
        chaves[(it["type"], it["dispositivo"], quote)] += 1
    return chaves


def obrigacoes(itens_h, itens_p, corte):
    a, b = itens_por_tipo(itens_h, corte), itens_por_tipo(itens_p)
    tipos = lambda c: dict(Counter(t for (t, _, _), n in c.items() for _ in range(n)))  # noqa: E731
    return {
        "html_na_cobertura": tipos(a),
        "pdf": tipos(b),
        "so_no_html": sorted(f"{t} · {d}" for (t, d, _) in set(a) - set(b)),
        "so_no_pdf": sorted(f"{t} · {d}" for (t, d, _) in set(b) - set(a)),
    }


def citacoes(itens_h, itens_p, h_texto, p_texto, corte):
    """Cada trecho citado por um lado deve existir no texto normalizado do outro."""
    hn, pn = chave(h_texto), chave(p_texto)
    faltam_no_pdf = [
        it["dispositivo"]
        for it in itens_h
        if it["locator"]["start"] < corte and it["anchors"] and chave(_quote(it)) not in pn
    ]
    faltam_no_html = [
        it["dispositivo"] for it in itens_p if it["anchors"] and chave(_quote(it)) not in hn
    ]
    return {
        "citacoes_html": sum(
            1 for it in itens_h if it["anchors"] and it["locator"]["start"] < corte
        ),
        "citacoes_pdf": sum(1 for it in itens_p if it["anchors"]),
        "html_ausente_no_pdf": faltam_no_pdf,
        "pdf_ausente_no_html": faltam_no_html,
    }


def comparar(nome, legado=False):
    par = ler_par(nome, legado)
    alin = alinhar(par["h"], par["p"])
    corte = alin["corte_html"]
    ex_h, it_h = extrair(par["h"])
    ex_p, it_p = extrair(par["p"])
    ruido_pdf = Counter(r["tipo"] for r in par["pdf"]["ruido"])
    outros = [a["titulo"]["titulo"] for a in par["pdf"]["atos"] if a is not par["alvo"]]
    cit_h, cit_p = _citadas(par["h"][:corte]), _citadas(par["p"])
    return {
        "ato": par["html"]["titulo"]["titulo"],
        "publicacao": par["html"]["publicacao"],
        "par_completo": alin["cobertura"] >= 0.999,
        "cabecalho": None if legado else cabecalho(par),
        "texto": alin,
        "estrutura": estrutura(ex_h, ex_p, corte),
        "obrigacoes_prazos_vigencia": obrigacoes(it_h, it_p, corte),
        "normas_citadas": {
            "html_na_cobertura": sum(cit_h.values()),
            "pdf": sum(cit_p.values()),
            "so_no_html": sorted((cit_h - cit_p).elements()),
            "so_no_pdf": sorted((cit_p - cit_h).elements()),
        },
        "citacoes_literais": citacoes(it_h, it_p, par["h"], par["p"], corte),
        "ruido": {
            "pdf_isolado": dict(ruido_pdf),
            "html_isolado": [r["tipo"] for r in par["html"]["ruido"]],
            "outros_atos_na_pagina_do_pdf": outros,
            "pdf_numero_da_pagina": par["pdf"]["paginas"][0]["numero_dou"],
        },
        "datas_vigencia_html": [d for d in ex_h["dates"] if d["kind"] == "effective"][:2],
        "datas_vigencia_pdf": [d for d in ex_p["dates"] if d["kind"] == "effective"][:2],
    }


def resumo(r):
    n_dif = len(r["texto"]["diferencas"])
    estr = r["estrutura"]
    n_estr = (
        len(estr["so_no_pdf"])
        + len(estr["so_no_html"])
        + len(estr["texto_diferente_apos_normalizar"])
    )
    n_cab = len(r["cabecalho"]["diferencas"]) if r["cabecalho"] else None
    n_ob = len(r["obrigacoes_prazos_vigencia"]["so_no_html"]) + len(
        r["obrigacoes_prazos_vigencia"]["so_no_pdf"]
    )
    n_cit = len(r["citacoes_literais"]["html_ausente_no_pdf"]) + len(
        r["citacoes_literais"]["pdf_ausente_no_html"]
    )
    return {
        "ato": r["ato"],
        "cobertura_do_pdf": r["texto"]["cobertura"],
        "diferencas_de_texto": n_dif,
        "diferencas_de_estrutura": n_estr,
        "diferencas_de_cabecalho": n_cab,
        "obrigacoes_prazos": n_ob,
        "citacoes_literais": n_cit,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--legado", action="store_true")
    a = ap.parse_args()
    todos = {n: comparar(n, a.legado) for n in pares()}
    for n, r in todos.items():
        print(json.dumps(resumo(r), ensure_ascii=False))
    if a.json:
        Path(a.json).write_text(json.dumps(todos, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
