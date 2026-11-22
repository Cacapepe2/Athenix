"""Esclarecimentos oficiais (FAQ, retificação, alteração) para o que está "a confirmar".

A busca roda só sobre os documentos oficiais SALVOS em tests/fontes_impacto/esclarecimentos/ (com URL,
data de consulta e hash conferido), nunca na internet durante o processamento. O que ela acha é só um
"possível esclarecimento": mostra a citação literal e a fonte e continua "a confirmar". Uma leitura só
entra no cálculo quando há uma entrada confirmada por pessoa em athenix/data/esclarecimentos_oficiais.json.
"""

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONTES = ROOT / "tests" / "fontes_impacto" / "esclarecimentos"
CONFIRMADOS = Path(__file__).parent / "data" / "esclarecimentos_oficiais.json"
SUGESTAO = "verificar retificação ou esclarecimento da ANEEL"
# Pergunta numerada do FAQ ("3.2 Qual é o prazo ...?"): cada uma vira um trecho de busca.
PERGUNTA = re.compile(r"(?=\b\d{1,2}\.\d{1,2}\s+[A-ZÀ-Ú][^?]{5,400}\?)")
PALAVRA = re.compile(r"[A-Za-zÀ-ú]{8,}")
SIGLA = re.compile(r"\b[A-Z]{3,}\b")
COMUNS = {"distribuidoras", "distribuidora", "resolução", "normativa", "dezembro", "publicação",
          "consumidores", "disposições", "conforme", "informações", "relacionadas"}  # fmt: skip


class _Texto(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes, self.pular = [], 0

    def handle_starttag(self, tag, attrs):
        self.pular += tag in {"script", "style"}

    def handle_endtag(self, tag):
        self.pular -= tag in {"script", "style"}

    def handle_data(self, data):
        if not self.pular:
            self.partes.append(data)


def _texto(caminho):
    bruto = caminho.read_bytes()
    if caminho.suffix.lower() in {".html", ".htm"}:
        p = _Texto()
        p.feed(bruto.decode("utf-8", "replace"))
        return re.sub(r"\s+", " ", " ".join(p.partes)).strip()
    return re.sub(r"\s+", " ", bruto.decode("utf-8", "replace")).strip()


def carregar(pasta=FONTES):
    """Trechos dos documentos salvos: [{norma, tipo, titulo, url, arquivo, sha256, consultado_em, trecho}].
    Hash divergente é erro: nunca se busca num arquivo que não é o registrado."""
    meta = pasta / "fontes.json"
    if not meta.exists():
        return []
    out = []
    for doc in json.loads(meta.read_text(encoding="utf-8"))["documentos"]:
        arquivo = pasta / doc["arquivo"]
        if hashlib.sha256(arquivo.read_bytes()).hexdigest() != doc["sha256"]:
            raise ValueError(f"Hash divergente em {arquivo.name}: o arquivo não é o registrado.")
        texto = _texto(arquivo)
        partes = [p.strip() for p in PERGUNTA.split(texto) if p.strip()]
        if len(partes) < 3:  # documento sem perguntas numeradas: janelas de frases
            frases = re.split(r"(?<=[.?!])\s+", texto)
            partes = [" ".join(frases[i : i + 3]) for i in range(0, len(frases), 3)]
        info = {k: doc[k] for k in ("norma", "tipo", "titulo", "url", "sha256", "consultado_em")}
        out += [info | {"arquivo": doc["arquivo"], "trecho": p[:900]} for p in partes]
    return out


def _mencoes(dispositivo):
    """Padrões que citam o dispositivo: "art. 13, VI", "inciso VI do art. 13", "item 105"."""
    d = dispositivo or ""
    pads = []
    art = re.search(r"Art\.\s*(\d+)", d)
    inc = re.search(r"inciso\s+([IVXLC]+)", d)
    item = re.search(r"\bitem\s+(\d+)", d)
    if art and inc:
        a, i = art.group(1), inc.group(1)
        pads += [
            rf"\bart(?:igo)?\.?\s*{a}\b[^.?]{{0,40}}\b(?:inciso\s+)?{i}\b",
            rf"\binciso\s+{i}\b[^.?]{{0,40}}\bart\w*\.?\s*{a}\b",
        ]
    if item:
        pads.append(rf"\bitens?\s+(?:\d+\s*,\s*)*{item.group(1)}\b")
    return [re.compile(p, re.I) for p in pads]


def buscar(caso, trechos, limite=3):
    """Possíveis esclarecimentos para um caso {dispositivo, trecho, norma, prazo?}: menção ao dispositivo
    ou ao tema (siglas, números e termos do trecho; "prazo", a leitura provável como "180 dias", pesa mais).
    Nunca muda o cálculo."""
    texto = caso.get("trecho") or ""
    siglas = set(SIGLA.findall(texto))
    numeros = set(re.findall(r"\b\d{2,}\b", texto))
    termos = {w.lower() for w in PALAVRA.findall(texto)} - COMUNS
    mencoes = _mencoes(caso.get("dispositivo"))
    achados = []
    for t in trechos:
        if caso.get("norma") and t["norma"] != caso["norma"]:
            continue
        s = t["trecho"]
        mencao = any(p.search(s) for p in mencoes)
        sig = {x for x in siglas if re.search(rf"\b{x}\b", s)}
        pontos = 3 * len(sig) + 2 * sum(bool(re.search(rf"\b{n}\b", s)) for n in numeros)
        pontos += sum(w in s.lower() for w in termos)
        if caso.get("prazo") and re.search(re.escape(caso["prazo"]), s, re.I):
            pontos += 10
        if mencao or (sig and pontos >= 5):
            achados.append(((10 if mencao else 0) + pontos, t))
    achados.sort(key=lambda x: -x[0])
    return [
        {
            "citacao": t["trecho"],
            "fonte": {
                k: t[k] for k in ("titulo", "tipo", "url", "arquivo", "sha256", "consultado_em")
            },
        }
        for _, t in achados[:limite]
    ]


def confirmados(caminho=CONFIRMADOS):
    if not caminho.exists():
        return []
    return json.loads(caminho.read_text(encoding="utf-8"))["entradas"]


def _mesmo_dispositivo(a, b):
    norm = lambda s: re.sub(r"\s+|inciso|al[íi]nea|,", "", (s or "").lower())  # noqa: E731
    return norm(a) == norm(b)


def aplicar_confirmados(obrigacoes, norma, entradas=None):
    """Aplica só as leituras CONFIRMADAS (entrada em esclarecimentos_oficiais.json) com a nota
    "texto original: '…'; esclarecido por …". Devolve as entradas aplicadas."""
    aplicadas = []
    for e in confirmados() if entradas is None else entradas:
        if e["norma"] != norma:
            continue
        for o in obrigacoes:
            if not _mesmo_dispositivo(o.get("dispositivo"), e["dispositivo"]):
                continue
            prazo = e.get("prazo") or {}
            if prazo.get("data") and o["prazo"]["data"] not in (None, prazo["data"]):
                raise ValueError(
                    f"{e['dispositivo']}: leitura confirmada ({prazo['data']}) difere do prazo calculado "
                    f"({o['prazo']['data']}); revisar a entrada ou o motor antes de publicar."
                )
            nota = (
                f"{e['leitura']}; texto original: '{e['texto_original']}'; esclarecido por {e['tipo']} da ANEEL "
                f"({e['fonte']['url']}): «{e['fonte']['trecho']}»"
            )
            o["esclarecimento"] = {"leitura": e["leitura"], "nota": nota, "tipo": e["tipo"], "fonte": e["fonte"],
                                   "confirmado_por": e["confirmado_por"], "confirmado_em": e["confirmado_em"]}  # fmt: skip
            if o.get("erro_material"):
                o["erro_material"]["rotulo"] = "esclarecido"
            aplicadas.append(e)
    return aplicadas


SUFIXO_ERRO = " · possível erro material da norma (a confirmar)"


def anotar_plano(out, norma, trechos=None, entradas=None):
    """Possíveis erros materiais de prazo (com a leitura provável, "a confirmar"), leituras oficiais
    confirmadas e o relatório do que está "a confirmar", com os possíveis esclarecimentos encontrados."""
    from .temporal import erros_materiais

    for o in out["obrigacoes"]:
        erros = erros_materiais(o.get("trecho") or "")
        if erros:
            o["erro_material"] = erros[0] | {"rotulo": "a confirmar", "sugestao": SUGESTAO}
            o["prazo"]["texto"] += SUFIXO_ERRO
    for o in out["obrigacoes"]:
        o.setdefault("erro_material", None)
        o.setdefault("esclarecimento", None)
    aplicar_confirmados(out["obrigacoes"], norma, entradas)
    for o in out["obrigacoes"]:
        if o["esclarecimento"]:
            o["prazo"]["texto"] = (
                o["prazo"]["texto"].replace(SUFIXO_ERRO, "")
                + f" · esclarecido ({o['esclarecimento']['tipo']} da ANEEL)"
            )
    out["erros_materiais"] = [
        {"dispositivo": o["dispositivo"], "obrigacao": o["id"], "trecho": o["trecho"]}
        | o["erro_material"]
        | ({"esclarecimento": o["esclarecimento"]["nota"]} if o["esclarecimento"] else {})
        for o in out["obrigacoes"]
        if o["erro_material"]
    ]
    out["a_confirmar"] = relatorio_a_confirmar(
        out, norma, carregar() if trechos is None else trechos
    )


def casos_a_confirmar(out, norma):
    """Sinais de incerteza do plano, antes de filtrar por possíveis respostas no FAQ."""
    casos = []
    for o in out["obrigacoes"]:
        base = {
            "dispositivo": o["dispositivo"],
            "trecho": o["trecho"],
            "norma": norma,
            "obrigacao": o["id"],
        }
        if (o.get("marco") or {}).get("tipo") == "a_confirmar":
            casos.append(base | {"tipo": "transição ambígua"})
        if "inferido pela posição" in ((o.get("marco") or {}).get("nota") or ""):
            casos.append(base | {"tipo": "artigo inferido pela posição"})
        if o.get("erro_material") and not o.get("esclarecimento"):
            prazo = o["erro_material"]["leitura_provavel"].split(" (")[0].rstrip("?")
            casos.append(base | {"tipo": "possível erro material", "prazo": prazo})
        if o.get("sujeito_implicito"):
            casos.append(base | {"tipo": "sujeito incerto"})
        if not o.get("enquadramento"):
            casos.append(base | {"tipo": "enquadramento sem texto"})
    for r in ((out.get("transicao") or {}).get("regras")) or []:
        if r.get("alvos_a_confirmar"):
            casos.append({"dispositivo": r["dispositivo"], "trecho": r.get("trecho") or " ".join(r["alvos_a_confirmar"]),
                          "norma": norma, "tipo": "referência a outra norma", "alvos": r["alvos_a_confirmar"]})  # fmt: skip
    return casos


def relatorio_a_confirmar(out, norma, trechos):
    """Busca possíveis esclarecimentos para os sinais existentes, sem confirmar uma interpretação."""
    casos = casos_a_confirmar(out, norma)
    achados = []
    for c in casos:
        r = buscar(c, trechos)
        if r:
            achados.append(
                {k: c[k] for k in ("tipo", "dispositivo")}
                | {"trecho": (c["trecho"] or "")[:240], "possiveis_esclarecimentos": r}
            )
    por_tipo = {}
    for c in casos:
        por_tipo[c["tipo"]] = por_tipo.get(c["tipo"], 0) + 1
    return {
        "total": len(casos),
        "por_tipo": dict(sorted(por_tipo.items())),
        "com_possivel_esclarecimento": len(achados),
        "aviso": "Possível esclarecimento encontrado nos documentos oficiais salvos: continua a confirmar; "
        "só uma entrada confirmada em athenix/data/esclarecimentos_oficiais.json muda o cálculo.",
        "casos": achados,
    }
