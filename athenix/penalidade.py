"""Decisão de penalidade em voto/despacho da ANEEL (recurso contra auto de infração), por regras.

Extrai só o que está escrito, cada campo com o trecho literal e a página: agente (INTERESSADO),
processo, auto de infração, efeito (a frase do dispositivo), valor decidido em R$ e os dispositivos
que o voto diz terem sido infringidos. Nada é inferido: campo ausente fica `None`. Não há valor
"provável" aqui; o resultado serve para conferir o CSV de autos de infração, sem misturar com ele.
"""

import re
from decimal import Decimal

CAMPO = {
    "agente": re.compile(r"^INTERESSADO:\s*(.+?)\.?\s*$", re.M),
    "processo": re.compile(r"^PROCESSO:\s*(\d{5}\.\d{6}/\d{4}-\d{2})\.?\s*$", re.M),
}
AUTO = re.compile(r"Auto de Infra[çc][ãa]o\s+n[º°o]?\s*(\d+/\d{4}(?:-[A-Z]{2,5})?)", re.I)
DISPOSITIVO = re.compile(r"^\s*(?:[IVX]+\s*[.–-]\s*)?DISPOSITIVO\s*$", re.M)
PARAGRAFO = re.compile(r"\n(?=\d+\.\s)")  # parágrafos numerados do voto
RODAPE_FL = re.compile(r"\s*FL\.\s*\d+ de \d+\s*")
VALOR = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})")
EFEITO = re.compile(
    r"negar provimento|dar provimento|dar parcial provimento|conhecer|reformar|manter|cancelar|"
    r"reduzir|retirar|alterando o valor",
    re.I,
)
INFRINGIDO = re.compile(r"infring|descumpr|inobserv|desobedec", re.I)
ARTIGOS = re.compile(
    r"\bart(?:s|igos?)?\.?\s*\d+[º°]?(?:-[A-Z])?(?:\s*(?:,|e|a)\s*\d+[º°]?(?:-[A-Z])?)*"
    r"(?:,?\s*(?:§\s*\d+[º°]?|inciso\s+[IVXLC]+|alínea\s+\w+))*",
    re.I,
)


def _reais(texto):
    return Decimal(texto.replace(".", "").replace(",", "."))


def decisao_de_penalidade(paginas):
    """`paginas`: lista de textos (um por página). Devolve a decisão, ou None se o texto não tiver
    seção DISPOSITIVO com um parágrafo que decida valor em reais."""
    texto = "\n".join(paginas)
    planas = [" ".join(p.split()) for p in paginas]

    def pagina_de(trecho):
        chave = " ".join(trecho.split())[:80]
        return next((n for n, p in enumerate(planas, 1) if chave in p), None)

    def campo(nome):
        m = CAMPO[nome].search(texto)
        if not m:
            return None
        return {
            "valor": m.group(1).strip(),
            "trecho": m.group(0).strip(),
            "pagina": pagina_de(m.group(0)),
        }

    secoes = list(DISPOSITIVO.finditer(texto))
    if not secoes:
        return None
    corpo = texto[secoes[-1].end() :]
    corpo = corpo.split("Brasília,")[0]
    decisorios = [p for p in PARAGRAFO.split(corpo) if VALOR.search(p) and EFEITO.search(p)]
    if not decisorios:
        return None
    paragrafo = RODAPE_FL.sub(" ", decisorios[0]).strip()
    auto = AUTO.search(paragrafo) or AUTO.search(texto)
    infringidos = [
        {
            "artigos": sorted({a.strip() for a in ARTIGOS.findall(par)}),
            "trecho": " ".join(par.split())[:400],
            "pagina": pagina_de(par),
        }
        for par in PARAGRAFO.split(texto)
        if INFRINGIDO.search(par) and ARTIGOS.search(par)
    ]
    return {
        "agente": campo("agente"),
        "processo": campo("processo"),
        "auto_de_infracao": {"numero": auto.group(1), "trecho": auto.group(0)} if auto else None,
        "efeito": sorted({e.lower() for e in EFEITO.findall(paragrafo)}),
        "valores_decididos": [
            {"reais": str(_reais(v)), "texto": f"R$ {v}"} for v in VALOR.findall(paragrafo)
        ],
        "dispositivo": {"trecho": " ".join(paragrafo.split()), "pagina": pagina_de(paragrafo)},
        "dispositivos_infringidos_citados": infringidos[:10],
        "estado": "pendente de revisão humana; extração por regras, sem inferência",
    }
