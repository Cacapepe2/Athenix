"""Leitor de vigência e transição de QUALQUER norma: lê as cláusulas da própria norma ("entra em vigor",
"produz efeitos", "a adequação ... deve ser realizada nos seguintes prazos", "devem ser implementadas",
"demais dispositivos") e liga cada inciso/alínea aos dispositivos que ela cita ("quanto ao art. 2º, na
parte que inclui o § 1º no art. 166 da Resolução Normativa nº 1.000", "itens 103 e 108 do Anexo IV da
Resolução Normativa nº 956, com redação dada pelo art. 3º"). Nenhuma lista de dispositivos no código:
tudo vem do texto. Referência não encontrada ou ligação ambígua fica "a confirmar"; nenhuma data é
presumida."""

import re
from datetime import date

from . import temporal

# Cláusula de transição da própria norma (no caput do artigo ou no próprio dispositivo).
GATILHO = re.compile(
    r"\bentra(?:rá)?\s+em\s+vigor|\bproduz(?:irá|indo)?\s+efeitos|\badequa[çc][ãa]o\s+[àa]s?\s+altera"
    r"|\bprazos?\s+para\s+(?:a\s+)?implementa[çc][ãa]o|\bdevem\s+ser\s+implementad"
    r"|\bdemais\s+(?:dispositivos|disposi[çc][õo]es)|\bdisposi[çc][õo]es\s+n[ãa]o\s+listadas",
    re.I,
)
ADEQUACAO = re.compile(r"\badequa[çc][ãa]o|\bimplementa|\bimplanta", re.I)
DEMAIS = re.compile(
    r"\bdemais\s+(?:dispositivos|disposi[çc][õo]es)|\bdisposi[çc][õo]es\s+n[ãa]o\s+listadas", re.I
)
# "devendo ser mantida a aplicação das disposições anteriores até a implementação": até a adequação,
# valem as regras anteriores.
REGRAS_ANTERIORES = re.compile(
    r"mantid[ao]s?\s+a\s+aplica[çc][ãa]o\s+das\s+disposi[çc][õo]es\s+anteriores"
    r"|(?:continuam?|permanecem?)\s+(?:a\s+)?(?:aplic|vig)\w*\s+as\s+(?:regras|disposi[çc][õo]es)\s+anteriores",
    re.I,
)
# Prazo de OUTRO agente ("Os representantes da comercialização varejista terão prazo..."): não é marco
# da distribuidora; fica no relatório.
OUTRO_AGENTE = re.compile(
    r"^\W*(?:Art\.?\s*\d+\w*\.?\s*)?(?:[OA]s?\s+)?(?:transmissor|representantes?\s+da\s+comercializa|"
    r"comercializador|gerador|ccee\b|c[âa]mara\s+de\s+comercializa|ons\b|operador\s+nacional|consumidor)",
    re.I,
)
NORMA = re.compile(r"Resolu[çc][ãa]o\s+Normativa(?:\s+ANEEL)?\s+n[ºo°]?\s*([\d.]+)", re.I)
ANEXO = re.compile(r"\bAnexo\s+([IVXLC]+)\b")
ART = r"(\d+)\s*[ºo°]?(?:\s*-\s*([A-Z]))?"
NA_PARTE = re.compile(r"\bna\s+parte\s+que\s+(?:inclui|altera|acrescenta|revoga|d[áa])", re.I)
SUB = re.compile(
    r"(§\s*\d+\s*[ºo°]?|par[áa]grafo\s+[úu]nico|inciso\s+[IVXLC]+|al[íi]nea\s+[a-z])\s+(?:no|do|ao)\s+"
    rf"(?:caput\s+do\s+)?art\.?\s*{ART}",
    re.I,
)
ARTS = re.compile(rf"\barts?\.?\s*({ART}(?:\s*(?:,|\be\b)\s*{ART})*)", re.I)
ARTIGOS = re.compile(r"\bartigos?\s+((?:\d+\s*[ºo°]?\s*(?:,|\be\b)\s*)*\d+\s*[ºo°]?)", re.I)
ITENS = re.compile(
    r"\bite(?:m|ns)\s+((?:\d+(?:\s*,\s*|\s+e\s+))*\d+)\s+do\s+Anexo\s+([IVXLC]+)", re.I
)
# Rótulo do próprio dispositivo no início do texto ("Art. 21.", "II -", "b)"): não é referência.
ROTULO_INICIAL = re.compile(
    r"^\W*(?:Art\.?\s*\d+\s*[ºo°]?(?:-[A-Z])?\.?|[IVXLC]+\s*[-–]|[a-z]\)|§\s*\d+\s*[ºo°]?\.?"
    r"|Par[áa]grafo\s+[úu]nico\.?)\s*"
)
REDACAO = re.compile(rf"reda[çc][ãa]o\s+dada\s+pelo\s+art\.?\s*{ART}", re.I)


def _art(numero, letra=None):
    return f"{int(numero)}" + (f"-{letra.lower()}" if letra else "")


def _lista_arts(trecho):
    return [_art(n, letra) for n, letra in re.findall(ART, trecho)]


def _sub(rotulo):
    r = re.sub(r"\s+", "", rotulo.lower())
    if r.startswith("§"):
        return "§" + str(int(re.sub(r"\D", "", r)))
    if r.startswith("par"):
        return "§unico"
    return re.sub(r"^(inciso|al[íi]nea)", "", r)


def _rotulo_unidade(u):
    """Rótulo normalizado do dispositivo: "166", "9-a", "§1", "§unico", "ii", "a", "103"."""
    label = (u.get("label") or "").strip()
    if u["kind"] == "article":
        m = re.match(ART, label)
        return _art(*m.groups()) if m else label.lower()
    if u["kind"] == "paragraph":
        return _sub(label) if label else ""
    if u["kind"] == "item":
        return re.sub(r"\D", "", label)
    return label.lower()


def _artigos_proprios(units):
    """Artigos da própria norma, na ordem do texto (os blocos de alteração ficam dentro deles)."""
    return sorted(
        (u for u in units if u["owner"] == "self" and u["kind"] == "article" and not u["parent"]),
        key=lambda u: u["start"],
    )


def _bloco(u, by_id, artigos):
    """Artigo da própria norma que contém a unidade (o bloco de alteração "Art. 2º A Resolução ... passa
    a vigorar com as seguintes alterações" contém as unidades da norma alterada)."""
    if u["owner"] == "self":
        raiz = u
        while raiz["parent"]:
            raiz = by_id[raiz["parent"]]
        if raiz["kind"] == "article":
            return raiz
    dono = None
    for a in artigos:
        if a["start"] <= u["start"]:
            dono = a
    return dono


def _cadeia(u, by_id):
    """[(tipo, rótulo normalizado, pai é artigo)] da unidade até a raiz, na mesma norma."""
    out = []
    while u:
        pai = by_id.get(u["parent"]) if u["parent"] else None
        out.append((u["kind"], _rotulo_unidade(u), bool(pai and pai["kind"] == "article")))
        u = pai if pai and pai["owner"] == u["owner"] else None
    return out


def _norma(texto):
    m = NORMA.search(texto or "")
    return re.sub(r"\D", "", m.group(1)) if m else None


def _rotulo_regra(u, by_id):
    """ "Art. 16, II, b" para a alínea b do inciso II do art. 16 da própria norma."""
    partes = []
    while u:
        label = (u.get("label") or "").strip()
        if u["kind"] == "article":
            partes.append(f"Art. {label}")
        elif label:
            partes.append(label)
        u = by_id.get(u["parent"]) if u["parent"] else None
    return ", ".join(reversed(partes))


def _referencias(texto):
    """Do texto de um inciso/alínea de transição: artigos da própria norma e alvos na norma alterada.
    Alvo: {"norma", "anexo", "art", "sub", "item"}; `sub`/`item` restringem a parte do artigo/anexo."""
    proprios, alvos = [], []
    norma = _norma(texto)
    corte = NA_PARTE.search(texto)
    if corte:
        proprios = _lista_arts(" ".join(m.group(1) for m in ARTS.finditer(texto[: corte.start()])))
        parte = texto[corte.end() :]
        fim = NORMA.search(parte)
        parte = parte[: fim.start()] if fim else parte
        # "o art. 3º-A no Anexo II": o anexo qualifica o artigo; "e o Anexo IV": é um alvo à parte.
        qualifica = re.search(r"\b(?:no|do)\s+Anexo\s+([IVXLC]+)", parte)
        avulso = r"(?<![nd])\bo\s+Anexo\s+([IVXLC]+)"  # "e o Anexo IV" (não "no/do Anexo")
        for m in re.finditer(avulso, parte):
            alvos.append({"norma": norma, "anexo": m.group(1)})
        parte = re.sub(avulso, " ", parte)
        for m in SUB.finditer(parte):
            alvos.append(
                {"norma": norma, "art": _art(m.group(2), m.group(3)), "sub": _sub(m.group(1))}
            )
        for m in ARTS.finditer(SUB.sub(" ", parte)):
            for a in _lista_arts(m.group(1)):
                alvos.append(
                    {"norma": norma, "art": a, "anexo": qualifica.group(1) if qualifica else None}
                )
        return proprios, alvos
    for m in ITENS.finditer(texto):
        for n in re.findall(r"\d+", m.group(1)):
            alvos.append({"norma": _norma(texto[m.end() :]), "anexo": m.group(2), "item": n})
    redacao = REDACAO.search(texto)
    if redacao:
        proprios = [_art(*redacao.groups())]
    if alvos:
        return proprios, alvos
    # "quanto ao art. 4º", "c) art. 3º.", "nos arts. 21-A e 21-B da Resolução Normativa nº 1.011"
    for m in ARTS.finditer(texto):
        depois = texto[m.end() : m.end() + 80]
        n = (
            _norma(depois)
            if re.match(r"\s*(?:,\s*)?(?:da|na|no)\s+(?:Anexo\s+\w+\s+da\s+)?Resolu", depois)
            else None
        )
        if n:
            alvos += [{"norma": n, "art": a} for a in _lista_arts(m.group(1))]
        elif re.search(r"\b(?:Decreto|Lei|PRODIST|M[óo]dulo)\b", depois[:40]):
            alvos.append({"externo": texto[m.start() : m.end() + 40].strip()})
        else:
            proprios += _lista_arts(m.group(1))
    for m in ARTIGOS.finditer(texto):
        proprios += _lista_arts(m.group(1))
    if not alvos and re.search(r"\b(?:Se[çc][ãa]o|M[óo]dulo)\s+\d", texto):
        alvos.append({"externo": texto.strip()[:120]})
    return proprios, alvos


def _casa(alvo, u, cadeia, bloco):
    """Especificidade (0 = não casa) do alvo para a unidade."""
    if "externo" in alvo:
        return 0
    cabecalho = (bloco or {}).get("text", "")[:200]
    # Unidade sem número de norma no dono (ex.: anexo lido como "Resolução."): vale a norma do bloco.
    norma = _norma_digitos(u["owner"]) or _norma(cabecalho)
    if alvo.get("norma") and norma != alvo["norma"]:
        return 0
    anexo_bloco = ANEXO.search(cabecalho)
    if (
        "art" not in alvo and "item" not in alvo
    ):  # anexo inteiro: a unidade-anexo ou o bloco do anexo
        if u["kind"] == "annex":
            return 2 if _rotulo_unidade(u).upper() == alvo["anexo"] else 0
        return 2 if anexo_bloco and anexo_bloco.group(1) == alvo["anexo"] else 0
    if alvo.get("anexo") and (not anexo_bloco or anexo_bloco.group(1) != alvo["anexo"]):
        return 0
    if "item" in alvo:
        return 3 if any(k == "item" and r == alvo["item"] for k, r, _ in cadeia) else 0
    if not any(k == "article" and r == alvo["art"] for k, r, _ in cadeia):
        return 0
    if not alvo.get("sub"):
        return 2
    sub = alvo["sub"]
    if sub.startswith("§"):
        return 3 if any(k == "paragraph" and r == sub for k, r, _ in cadeia) else 0
    # Inciso citado direto do artigo ("o inciso II no caput do art. 166") é o do caput: pai = artigo.
    if re.fullmatch(r"[ivxlc]+", sub):
        return (
            3 if any(k == "clause" and r == sub and do_artigo for k, r, do_artigo in cadeia) else 0
        )
    return 3 if any(k == "letter" and r == sub for k, r, _ in cadeia) else 0


def _norma_digitos(owner):
    return "self" if owner == "self" else re.sub(r"\D", "", owner or "")


def _publicacao(dates):
    return temporal.unique_date(dates, "publication")


def _prazo(texto, caput, uid, dates):
    """Primeiro prazo do texto (herdando o marco do caput); "na data de sua publicação" = publicação."""
    for d in temporal.rules(texto, uid, dates, inherited=caput):
        if d.get("date") or d.get("state") == "awaiting_event":
            return {k: d.get(k) for k in ("date", "state", "event", "quantity", "unit", "base")}
    if re.search(r"\bna\s+data\s+(?:de|da)\s+(?:sua\s+)?publica[çc][ãa]o", texto, re.I):
        pub = _publicacao(dates)
        return {"date": pub, "state": "provisional", "event": "Publicação da norma", "base": pub}
    return None


def ler(extraction):
    """Regras de transição da norma: [{unidade, rotulo, tipo, prazo, proprios, alvos, demais, excluidos,
    nota, outro_agente, trecho}]."""
    units, dates = extraction["units"], extraction["dates"]
    by_id = {u["id"]: u for u in units}
    filhos = {}
    for u in units:
        filhos.setdefault(u["parent"], []).append(u)
    artigos = _artigos_proprios(units)
    regras, citados = [], {}

    def regra(u, caput, texto_prazo, artigo, tipo=None):
        texto = re.sub(r"\s+", " ", u["text"]).strip()
        proprios, alvos = _referencias(ROTULO_INICIAL.sub("", texto))
        proprios = list(dict.fromkeys(proprios))
        demais = bool(DEMAIS.search(texto))
        excluidos = []
        if demais:
            m = ARTIGOS.search(texto) or ARTS.search(texto)
            excluidos = _lista_arts(m.group(1)) if m else []
            citados.update(
                {a: "adequacao" if ADEQUACAO.search(texto) else "vigencia" for a in excluidos}
            )
        if not (proprios or alvos or demais):
            return
        regras.append(
            {
                "unidade": u["id"],
                "rotulo": _rotulo_regra(u, by_id),
                "tipo": tipo
                or ("adequacao" if ADEQUACAO.search(f"{caput} {texto}") else "vigencia"),
                "prazo": _prazo(texto_prazo, caput, u["id"], dates),
                "proprios": proprios,
                "alvos": alvos,
                "demais": demais,
                "excluidos": excluidos,
                "nota": REGRAS_ANTERIORES.search(caput or texto).group(0)
                if REGRAS_ANTERIORES.search(caput or texto)
                else None,
                "outro_agente": bool(OUTRO_AGENTE.match(artigo["text"])),
                "artigo": _rotulo_unidade(artigo),
                "trecho": texto,
            }
        )

    def ler_artigo(a, tipo=None):
        caput = re.sub(r"\s+", " ", a["text"]).strip()
        incisos = [f for f in filhos.get(a["id"], []) if f["kind"] == "clause"]
        if not incisos:
            regra(a, "", caput, a, tipo)
            return
        for inciso in incisos:
            alineas = [f for f in filhos.get(inciso["id"], []) if f["kind"] == "letter"]
            for alvo in alineas or [inciso]:
                regra(alvo, caput, inciso["text"], a, tipo)

    for a in artigos:
        if GATILHO.search(a["text"]):
            ler_artigo(a)
    # "As disposições não listadas nos artigos 13, 14, 15 e 16": os artigos citados também são de transição.
    for a in artigos:
        if _rotulo_unidade(a) in citados and not GATILHO.search(a["text"]):
            ler_artigo(a, citados[_rotulo_unidade(a)])
    return regras


def ligar(extraction, regras):
    """{unidade: marco} para cada unidade da norma coberta por uma regra, e o relatório de alvos não
    encontrados. Marco: tipo "adequacao" | "vigencia" | "em_vigor" | "a_confirmar"."""
    units = extraction["units"]
    by_id = {u["id"]: u for u in units}
    artigos = _artigos_proprios(units)
    pub = _publicacao(extraction["dates"])
    transicao = {r["unidade"] for r in regras} | {
        u["id"]
        for u in units
        if u["owner"] == "self" and u["kind"] == "article" and GATILHO.search(u["text"])
    }
    # A regra e os dispositivos que a contêm (o caput do artigo, o inciso que enumera alíneas).
    com_regra = set()
    for r in regras:
        x = by_id.get(r["unidade"])
        while x:
            com_regra.add(x["id"])
            x = by_id.get(x["parent"]) if x["parent"] else None
    artigos_transicao = {by_id[i]["id"] for i in transicao if by_id[i]["kind"] == "article"} | {
        _bloco(by_id[r["unidade"]], by_id, artigos)["id"] for r in regras
    }
    achados = {id(a): 0 for r in regras for a in r["alvos"]}
    marcos = {}
    for u in units:
        if u["kind"] in {"heading", "unstructured", "formula", "table"}:
            continue
        bloco = _bloco(u, by_id, artigos)
        if not bloco or u["id"] in transicao or u["id"] in com_regra:
            continue
        # Dispositivo de um artigo de transição sem prazo próprio (ex.: o parágrafo único que manda
        # publicar os planos em vigor): vale desde a publicação pela cláusula "demais", se houver.
        if u["owner"] == "self" and bloco["id"] in artigos_transicao:
            nivel = {}
            for r in regras:
                if r["demais"]:
                    nivel.setdefault(r["tipo"], []).append((0.5, r))
            marco = _marco(nivel, pub)
            if marco:
                marcos[u["id"]] = marco
            continue
        cadeia = _cadeia(u, by_id)
        # Dispositivo sem artigo próprio dentro de um bloco de alteração com regras por parte: não dá para
        # saber a que artigo da norma alterada pertence; marca "a confirmar" em vez de escolher.
        if (
            u["owner"] == "self"
            and bloco["kind"] == "article"
            and not any(k == "article" for k, _, _ in cadeia)
            and any(r["alvos"] and _rotulo_unidade(bloco) in r["proprios"] for r in regras)
        ):
            marcos[u["id"]] = {
                "tipo": "a_confirmar",
                "data": None,
                "motivo": "dispositivo sem artigo identificado no bloco de alteração "
                f"(Art. {bloco['label']}); a regra de transição depende do artigo alterado",
            }
            continue
        nivel = {}
        for r in regras:
            if r["outro_agente"] or r["demais"]:
                continue
            pontos = 0
            for a in r["alvos"]:
                p = _casa(a, u, cadeia, bloco)
                if p and (not r["proprios"] or _rotulo_unidade(bloco) in r["proprios"]):
                    achados[id(a)] += 1
                    pontos = max(pontos, p)
            if not r["alvos"] and _rotulo_unidade(bloco) in r["proprios"]:
                pontos = 1
            if pontos:
                nivel.setdefault(r["tipo"], []).append((pontos, r))
        if (
            not nivel
        ):  # "quanto aos demais dispositivos": só o que nenhuma regra específica alcançou
            for r in regras:
                if r["demais"] and _rotulo_unidade(bloco) not in r["excluidos"]:
                    nivel.setdefault(r["tipo"], []).append((0.5, r))
        marco = _marco(nivel, pub)
        if marco:
            marcos[u["id"]] = marco
    for r in regras:
        for a in r["alvos"]:
            if "externo" in a or not achados[id(a)]:
                a["a_confirmar"] = True
    return marcos


def _escolher(candidatos):
    """Regra mais específica; duas no mesmo nível com prazos diferentes = ambíguo (None, lista)."""
    topo = max(p for p, _ in candidatos)
    melhores = [r for p, r in candidatos if p == topo]
    prazos = {((r["prazo"] or {}).get("date"), (r["prazo"] or {}).get("state")) for r in melhores}
    return (melhores[0], None) if len(prazos) == 1 else (None, melhores)


def _fonte(r):
    return {"dispositivo": r["rotulo"], "unidade": r["unidade"], "trecho": r["trecho"]}


def _marco(nivel, pub):
    for tipo in ("adequacao", "vigencia"):
        if tipo not in nivel:
            continue
        r, ambiguas = _escolher(nivel[tipo])
        if ambiguas:
            return {
                "tipo": "a_confirmar",
                "data": None,
                "motivo": "mais de uma regra de transição com prazos diferentes",
                "candidatos": [_fonte(x) for x in ambiguas],
            }
        prazo = r["prazo"] or {}
        if not prazo.get("date") and prazo.get("state") != "awaiting_event":
            return {
                "tipo": "a_confirmar",
                "data": None,
                "motivo": "prazo não lido",
                "fonte": _fonte(r),
            }
        if prazo.get("date") and pub and prazo["date"] <= pub:
            return {"tipo": "em_vigor", "data": pub, "fonte": _fonte(r)}
        return {
            "tipo": tipo,
            "data": prazo.get("date"),
            "estado": prazo.get("state"),
            "evento": prazo.get("event"),
            "nota": r["nota"] if tipo == "adequacao" else None,
            "fonte": _fonte(r),
        }
    return None


ROTULO = {"adequacao": "Adequação", "vigencia": "Vigência"}


def aplicar(rows, extraction):
    """Liga o marco de transição a cada obrigação (pela unidade da âncora) e o põe no prazo: adequação e
    vigência diferida viram prazo com data (ou por evento); "em vigor desde a publicação" fica no campo
    `marco`, sem prazo vencido inventado. Devolve o relatório da transição da norma."""
    regras = ler(extraction)
    marcos = ligar(extraction, regras)
    for row in rows:
        ancora = next((a for a in row.get("anchors", []) if a.get("state") == "verified"), None)
        marco = marcos.get(ancora["unit_id"]) if ancora else None
        if not marco:
            continue
        row["marco"] = marco
        if marco["tipo"] not in ROTULO:
            continue
        fonte = marco["fonte"]
        row.setdefault("deadlines", []).append(
            {
                "unit_id": fonte["unidade"],
                "quantity": None,
                "unit": "transicao",
                "landmark": "publication" if marco["data"] else "event",
                "event": f"{ROTULO[marco['tipo']]} ({fonte['dispositivo']})",
                "quote": fonte["trecho"],
                "direction": 1,
                "convention": "transicao_v1",
                "inherited": False,
                "date": marco["data"],
                "base": marco["data"] and _publicacao(extraction["dates"]),
                "state": marco.get("estado") or "provisional",
                "marco": marco["tipo"],
                "explanation": f"{ROTULO[marco['tipo']]} pela regra de transição {fonte['dispositivo']}; "
                "confirmação humana pendente.",
            }
        )
    return relatorio(regras, marcos)


def relatorio(regras, marcos):
    return {
        "regras": [
            {
                "dispositivo": r["rotulo"],
                "tipo": r["tipo"],
                "data": (r["prazo"] or {}).get("date"),
                "demais": r["demais"],
                "outro_agente": r["outro_agente"],
                "alvos_a_confirmar": [
                    a.get("externo")
                    or ", ".join(f"{k} {v}" for k, v in a.items() if v and k != "a_confirmar")
                    for a in r["alvos"]
                    if a.get("a_confirmar")
                ],
            }
            for r in regras
        ],
        "unidades": len(marcos),
    }


def data_br(iso):
    return date.fromisoformat(iso).strftime("%d/%m/%Y") if iso else None
