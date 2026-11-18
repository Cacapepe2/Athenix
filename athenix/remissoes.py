"""Remissões explícitas a outro ato que está no acervo local: índice e resolução proposta.

Só resolve "art. N [incisos ...] do <ato> nº X" quando o ato existe uma única vez no índice e o artigo
(e os incisos pedidos) são localizados no texto do destino, com citação verificada lá. O resultado é
sempre uma proposta para revisão humana: a prova literal (citações do destino) fica separada da
decisão de que a remissão está resolvida. Divergências da fonte (por exemplo, data do ato citada
errada) são listadas e nunca corrigidas em silêncio. Um salto só: a remissão do destino não é
seguida, então não há ciclos. Sem documento local, a remissão continua não resolvida, com o motivo.
"""

import re
from datetime import date

from .evidence import verify
from .structure import MONTHS

TIPO = r"Resolução Normativa|Resolução Homologatória|Lei Complementar|Lei|Decreto"
NUMERO = r"(?P<num>\d{1,3}(?:\.\d{3})+|\d+)"
DATA = r"(?P<dia>\d{1,2})[º°o]?\s+de\s+(?P<mes>[a-zç]+)\s+de\s+(?P<ano>\d{4})"
ROMANO = r"[IVXLC]+"
REMISSAO = re.compile(
    rf"(?:incisos?\s+(?P<incisos>{ROMANO}(?:\s*(?:,|e)\s*{ROMANO})*)\s+(?:do\s+caput\s+)?d[oa]\s+)?"
    rf"art\.?\s*(?P<art>\d+)[º°o]?(?P<suf>-[A-Z])?\s*[;,]?\s+d[oa]\s+"
    rf"(?P<tipo>{TIPO})(?:\s+ANEEL)?\s+(?:n[º°o.]*\s*)?{NUMERO}(?:/(?P<ano_curto>\d{{4}}))?"
    rf"(?:,?\s+de\s+{DATA})?",
    re.I,
)
ATO = re.compile(rf"(?P<tipo>{TIPO})(?:\s+ANEEL)?\s+n[º°o.]*\s*{NUMERO},\s+de\s+{DATA}", re.I)


def _data(m):
    mes = MONTHS.get((m["mes"] or "").lower())
    return date(int(m["ano"]), mes, int(m["dia"])) if m["dia"] and mes else None


def chave_ato(tipo, numero):
    return (" ".join(tipo.split()).casefold(), numero.replace(".", ""))


def ato(descricao):
    """("decreto", "12068"), data do ato a partir de "Decreto nº 12.068, de 20 de junho de 2024"."""
    m = ATO.search(descricao)
    return (chave_ato(m["tipo"], m["num"]), _data(m)) if m else (None, None)


class Indice:
    """Atos do acervo local. `extrair(doc)` devolve a extração do documento (sob demanda)."""

    def __init__(self, docs, extrair):
        self.atos, self.extrair, self._cache = {}, extrair, {}
        for doc in docs:
            chave, quando = ato(doc["ato"])
            if chave:
                self.atos.setdefault(chave, []).append(doc | {"data_ato": quando})

    def extracao(self, doc):
        if doc["id"] not in self._cache:
            self._cache[doc["id"]] = self.extrair(doc)
        return self._cache[doc["id"]]


def _ordinal(n):
    return f"{n}º" if int(n) < 10 else str(n)


def _incisos(texto):
    return re.findall(ROMANO, texto) if texto else []


def _juntar(rotulos):
    return rotulos[0] if len(rotulos) == 1 else ", ".join(rotulos[:-1]) + " e " + rotulos[-1]


def resolver(texto, posicao, indice):
    """Resolução da remissão que contém `posicao` em `texto`: dict com `estado` "proposta" (com
    alvo) ou "nao_resolvida" (com motivo); None se não houver remissão explícita a ato ali."""
    m = next((m for m in REMISSAO.finditer(texto) if m.start() <= posicao < m.end()), None)
    if not m:
        return None
    candidatos = indice.atos.get(chave_ato(m["tipo"], m["num"]), [])
    if not candidatos:
        return {"estado": "nao_resolvida", "motivo": "ato citado ausente do acervo local"}
    if len(candidatos) > 1:
        return {"estado": "nao_resolvida", "motivo": "mais de uma versão local do ato: ambígua"}
    doc = candidatos[0]
    ext = indice.extracao(doc)
    units = ext["units"]
    art = m["art"] + (m["suf"] or "")
    cabeca = re.compile(rf"Art\.?\s*{m['art']}[º°o]?{re.escape(m['suf'] or '')}(?![\d-])", re.I)
    # Cabeçalho do artigo pelo início do texto, não pelo rótulo: pode estar quebrado entre linhas.
    artigos = [
        u
        for u in units
        if u.get("owner") in (None, "self") and cabeca.match(" ".join(u["text"].split()))
    ]
    if not artigos:
        return {"estado": "nao_resolvida", "motivo": f"Art. {art} não encontrado no destino"}
    if len(artigos) > 1:
        return {
            "estado": "nao_resolvida",
            "motivo": f"Art. {art} aparece mais de uma vez no destino",
        }
    artigo, pedidos = artigos[0], _incisos(m["incisos"])
    alvo = [artigo]
    for rotulo in pedidos:
        filho = [u for u in units if u.get("parent") == artigo["id"] and u["label"] == rotulo]
        if len(filho) != 1:
            return {"estado": "nao_resolvida", "motivo": f"inciso {rotulo} do Art. {art} não encontrado no destino"}  # fmt: skip
        alvo.append(filho[0])
    citacoes = [
        verify(u["text"].strip(), u["id"], units, ext["text_hash"], source=ext.get("source"))
        for u in alvo
    ]
    divergencias = []
    citada = _data(m)
    if citada and doc["data_ato"] and citada != doc["data_ato"]:
        divergencias.append(
            f"data citada {citada:%d/%m/%Y} difere da data do ato no acervo ({doc['data_ato']:%d/%m/%Y})"
        )
    if any(c["state"] != "verified" for c in citacoes):
        divergencias.append("citação do destino não confirmada por segunda leitura")
    dispositivo = f"Art. {_ordinal(m['art'])}{m['suf'] or ''}" + (f", {_juntar(pedidos)}" if pedidos else "")  # fmt: skip
    return {
        "estado": "proposta",
        "revisao": "aguarda revisão humana",
        "doc": doc["id"],
        "ato": doc["ato"],
        "dispositivo": dispositivo,
        "trecho_origem": m.group(),
        "citacoes": [
            {"unit_id": c["unit_id"], "estado": c["state"], "trecho": c.get("quote", "")[:300]}
            for c in citacoes
        ],
        "divergencias": divergencias,
    }


def resolver_itens(items, extraction, indice):
    """Preenche `reference.target` dos itens de remissão que apontam para ato do acervo local."""
    by_id = {u["id"]: u for u in extraction["units"]}
    for item in items:
        ref = item.get("reference")
        if item.get("type") != "reference" or not ref:
            continue
        unit = by_id.get(item["anchors"][0]["unit_id"]) if item.get("anchors") else None
        if not unit:
            continue
        res = resolver(unit["text"], ref["offset"], indice)
        if res is None:
            continue
        ref["resolucao"] = res
        if res["estado"] == "proposta":
            ref["target"] = {k: res[k] for k in ("doc", "dispositivo", "estado")}
    return items
