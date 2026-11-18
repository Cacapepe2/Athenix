"""Compilação de normas: aplica a norma nova sobre a norma-alvo e guarda as versões por vigência.

Sem IA. Para cada norma ingerida: (1) detecta quais normas do acervo ela altera, inclui ou revoga
(só quando a norma-alvo é explícita, pelo leitor de blocos de alteração de `structure.segment`);
(2) aplica e gera nova versão com a data de vigência, preservando as anteriores; (3) registra em cada
dispositivo a norma que deu a redação e a fonte; (4) se duas normas alteram o mesmo dispositivo de
forma incompatível, sinaliza o conflito e NÃO escolhe. O texto lido nunca é alterado: a redação nova
é o trecho citado da norma alteradora, sem as aspas e a marca (NR)/(AC).
"""

import re
from datetime import date, timedelta

from . import structure

MARCADOR = re.compile(r"[\"”]?\s*\((NR|AC)\)\s*$")
PONTILHADO = re.compile(r"^[\s.…]*$")
NOTA = re.compile(
    r"\((Redação dada|Incluíd[oa]|Acrescid[oa]|Revogad[oa])\s+(?:pel[ao]\s+)?([^)]+)\)", re.I
)
REVOGADO = re.compile(r"^\(?Revogad[oa]\)?\.?(?:\s+pel[ao].*)?$", re.I)
ROTULO = {
    "article": structure.ARTICLE,
    "paragraph": structure.PARAGRAPH,
    "clause": structure.CLAUSE,
    "letter": structure.LETTER,
    "item": structure.ITEM,
}
ORDINAIS = {"formula", "table", "unstructured"}  # rótulo posicional: renumerado por pai
ROMANOS = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def limpa_texto(texto):
    """Junta quebras de linha do PDF (hifenização incluída) sem tocar em aspas ou travessões."""
    linhas = [ln for ln in texto.splitlines() if not PONTILHADO.match(ln)]
    texto = "\n".join(linhas)
    texto = re.sub(r"(?<=\w)-\n(?=[a-zà-ú])", "", texto)
    return " ".join(texto.split())


def sem_rotulo(unit):
    """Texto do dispositivo sem o rótulo ("Art. 9º", "§ 1º", "IV -") e sem aspas de abertura."""
    texto = limpa_texto(unit["text"]).lstrip('“" ')
    padrao = ROTULO.get(unit["kind"])
    if padrao and (m := padrao.match(texto)):
        texto = texto[m.end() :]
    return texto.strip()


def rotulo_chave(label):
    return re.sub(r"[º°.\s]", "", label or "").replace("Parágrafoúnico", "PU")


def caminhos(units):
    """Chave estável de cada unidade: 'article:9/clause:IV'. Fórmula e tabela têm rótulo posicional
    (a ordem no ato muda o número), então ganham o número de ordem sob o mesmo pai. A repetição do
    mesmo caminho entre donos diferentes (o art. 9º do ato e o "Art. 9º" citado) não colide."""
    contagem, usadas, chaves = {}, {}, {}
    for u in units:
        pai = chaves.get(u["parent"], "")
        rotulo = rotulo_chave(u["label"])
        if u["kind"] in ORDINAIS:
            contagem[(pai, u["kind"])] = contagem.get((pai, u["kind"]), 0) + 1
            rotulo = str(contagem[(pai, u["kind"])])
        chave = f"{pai}/{u['kind']}:{rotulo}" if pai else f"{u['kind']}:{rotulo}"
        vistas = usadas.get((u["owner"], chave), 0)
        usadas[(u["owner"], chave)] = vistas + 1
        chaves[u["id"]] = chave + (f"#{vistas + 1}" if vistas else "")
    return chaves


def ordem_do_irmao(chave):
    """Valor de ordenação do último rótulo ('clause:XXIV' → 24); None se não comparável."""
    tipo, _, rotulo = chave.split("/")[-1].partition(":")
    rotulo = rotulo.split("#")[0]
    if tipo == "clause" and rotulo and set(rotulo) <= set(ROMANOS):
        total = 0
        for i, c in enumerate(rotulo):
            v = ROMANOS[c]
            total += -v if i + 1 < len(rotulo) and ROMANOS[rotulo[i + 1]] > v else v
        return (total, "")
    if tipo in {"article", "paragraph", "item"} and (
        m := re.match(r"§?(\d+)(?:-([A-Z]))?$", rotulo)
    ):
        return (int(m.group(1)), m.group(2) or "")
    if tipo == "letter" and len(rotulo) == 1:
        return (ord(rotulo), "")
    return None


# --- leitura da norma-base (texto compilado) ----------------------------------------------------


def ler_base(content, media, settings, fonte, texto=None):
    """Dispositivos da norma-alvo no texto compilado oficial, cada um com a nota de redação."""
    ex = (
        structure.from_pieces([texto], [], [], "compilado", settings)
        if texto is not None
        else structure.extract(content, media, settings)
    )
    chaves = caminhos(ex["units"])
    dispositivos = []
    for u in ex["units"]:
        if u["owner"] != "self" or u["kind"] in {"heading", "unstructured"}:
            continue
        texto_u = limpa_texto(u["text"]).lstrip('“" ')
        nota = NOTA.findall(texto_u)
        situacao = {
            "revoked": "revogado (riscado na fonte)",
            "partial": "riscado parcial: conferir",
        }.get(u.get("struck"), "vigente")
        dispositivos.append(
            {
                "chave": chaves[u["id"]],
                "rotulo": u["label"],
                "tipo": u["kind"],
                "texto": texto_u,
                "redacao_dada_por": "; ".join(f"{a}: {b.strip()}" for a, b in nota) or None,
                "situacao": situacao,
                "fonte": fonte,
            }
        )
    return {"extraction": ex, "dispositivos": dispositivos}


# --- leitura da norma alteradora --------------------------------------------------------------


def numero_da_norma(texto):
    m = re.search(r"[\d.]+\d", texto or "")
    return re.sub(r"\D", "", m.group()) if m else ""


def alvos(extraction):
    """Normas que o ato altera ou inclui, pelas unidades de bloco citado (alvo explícito)."""
    out = {}
    for u in extraction["units"]:
        if u["owner"] not in {"self", "unresolved"} and numero_da_norma(u["owner"]):
            out.setdefault(numero_da_norma(u["owner"]), set()).add(u["owner"])
    return {k: sorted(v) for k, v in out.items()}


def ler_alteradora(extraction, alvo, ato, publicacao):
    """Operações do ato sobre a norma `alvo` (número, ex.: '846'): substituir, incluir ou revogar."""
    units = extraction["units"]
    chaves = caminhos(units)
    vig = vigencias(units, publicacao)
    ops, pendentes, artigo, anterior = [], [], None, None
    for u in units:
        if u["owner"] == "self":
            if u["kind"] == "article":
                artigo = rotulo_chave(u["label"])
            anterior, pendentes = None, []  # fim do bloco, com ou sem (NR)/(AC)
            continue
        if numero_da_norma(u["owner"]) != alvo or u["kind"] in {"heading", "unstructured"}:
            continue
        resto = sem_rotulo(u)
        chave = chaves[u["id"]]
        if not resto or PONTILHADO.match(resto):
            anterior = chave  # âncora: o texto omitido não muda
            continue
        completo = limpa_texto(u["text"]).lstrip('“" ')  # com o rótulo: é a redação do dispositivo
        marcador = MARCADOR.search(completo)
        texto = (MARCADOR.sub("", completo) if marcador else completo).rstrip('”" ').strip()
        sem_marca = MARCADOR.sub("", resto).rstrip('”" ').strip()
        tipo = "revogar" if REVOGADO.match(sem_marca) else "substituir"
        data, nota = vig["por_artigo"].get(artigo, (vig["padrao"], None))
        op = {
            "chave": chave,
            "tipo": tipo,  # substituir vira incluir se o dispositivo não existir
            "texto": None if tipo == "revogar" else texto,
            "marcador": marcador.group(1) if marcador else None,
            "artigo_do_ato": artigo,
            "vigencia": data.isoformat() if data else None,
            "nota_vigencia": nota,
            "anterior": anterior,
            "citacao": {
                "ato": ato["nome"],
                "artigo_do_ato": artigo,
                "trecho": limpa_texto(u["text"])[:400],
                "inicio": u["start"],
                "fim": u["end"],
            },
        }
        ops.append(op)
        pendentes.append(op)
        if marcador:  # (NR)/(AC) fecha o bloco: vale para todos os dispositivos dele
            for pendente in pendentes:
                pendente["marcador"] = marcador.group(1)
            pendentes = []
        anterior = chave
    revogados, sem_caminho = revogacoes(units, alvo)
    for r in revogados:
        data, nota = vig["por_artigo"].get(r["artigo_do_ato"], (vig["padrao"], None))
        ops.append(
            {
                "chave": r["chave"],
                "tipo": "revogar",
                "texto": None,
                "marcador": None,
                "artigo_do_ato": r["artigo_do_ato"],
                "vigencia": data.isoformat() if data else None,
                "nota_vigencia": nota,
                "anterior": None,
                "citacao": {
                    "ato": ato["nome"],
                    "artigo_do_ato": r["artigo_do_ato"],
                    "trecho": r["trecho"],
                    "inicio": r["inicio"],
                    "fim": r["fim"],
                },
            }
        )
    vig["revogacao_sem_caminho"] = sem_caminho
    return ops, vig


def mais_meses(base, n):
    ano, mes = divmod(base.month - 1 + n, 12)
    dia = base.day
    while True:
        try:
            return date(base.year + ano, mes + 1, dia)
        except ValueError:
            dia -= 1


def prazo_em(texto, base):
    """Data de 'em N dias/meses' (N por algarismo) a contar da publicação, ou None."""
    m = re.search(r"em\s+(?:até\s+)?(\d+)\s*(?:\([^)]*\)\s*)?(dias|meses)", texto, re.I)
    if not m:
        return None
    return (
        base + timedelta(days=int(m.group(1)))
        if m.group(2) == "dias"
        else mais_meses(base, int(m.group(1)))
    )


def vigencias(units, publicacao):
    """Vigência do ato: padrão ('entra em vigor ...') e, por artigo do ato, as exceções de
    'produz efeitos'. `publicacao`: data ISO do DOU. O que não for reconhecido fica sem data."""
    pub = date.fromisoformat(publicacao) if publicacao else None
    padrao, por_artigo, avisos = None, {}, []
    for i, u in enumerate(units):
        if u["owner"] != "self" or not re.search(r"entra(?:m)? em vigor", u["text"], re.I):
            continue
        texto = limpa_texto(u["text"])
        if re.search(r"entra(?:m)? em vigor na data de sua publicação", texto, re.I):
            padrao = pub
        elif m := structure.DATE.search(texto):
            padrao = (
                date.fromisoformat(structure.parse_date(m)) if structure.parse_date(m) else None
            )
        elif pub and (p := prazo_em(texto, pub)):
            padrao = p
        if padrao is None:
            avisos.append(f"vigência do ato não reconhecida: {texto[:120]}")
        if "produz efeitos" in texto.lower() and pub:
            atraso, parte = None, False
            for v in units[i + 1 :]:
                if v["owner"] != "self" or v["kind"] in {"article", "annex", "heading"}:
                    break
                t = limpa_texto(v["text"])
                if v["kind"] == "clause":
                    atraso = prazo_em(t, pub) or (pub if "data de sua publicação" in t else None)
                    parte = "na parte" in t
                    arts = re.findall(r"\bart\.\s*(\d+)", t)
                else:
                    arts, parte = re.findall(r"\bart\.\s*(\d+)", t), parte or "na parte" in t
                if atraso and arts and not re.search(r"demais dispositivos", t):
                    for a in arts:
                        por_artigo[a] = (
                            atraso,
                            "vigência parcial ('na parte que'): conferir"
                            if "na parte" in t
                            else None,
                        )
                if not atraso and arts:
                    avisos.append(f"efeitos não reconhecidos: {t[:100]}")
        break
    return {"padrao": padrao, "por_artigo": por_artigo, "avisos": avisos, "publicacao": publicacao}


# --- aplicação -----------------------------------------------------------------------------------


def subarvore(ordem, chave):
    return [c for c in ordem if c == chave or c.startswith(chave + "/")]


def posicao(ordem, chave):
    """Índice de inserção de um dispositivo novo: entre irmãos pela ordem dos rótulos; sem irmãos
    comparáveis, ao fim da subárvore do pai; sem pai, ao fim."""
    pai = chave.rsplit("/", 1)[0] if "/" in chave else ""
    irmaos = [c for c in ordem if (c.rsplit("/", 1)[0] if "/" in c else "") == pai]
    novo = ordem_do_irmao(chave)
    if novo and irmaos and all(ordem_do_irmao(c) for c in irmaos):
        for c in irmaos:
            if ordem_do_irmao(c) > novo:
                return ordem.index(c)
    if irmaos:
        return ordem.index(subarvore(ordem, irmaos[-1])[-1]) + 1
    if pai and pai in ordem:
        return ordem.index(subarvore(ordem, pai)[-1]) + 1
    return len(ordem)


def compilar(norma, base, alteradoras):
    """`base`: saída de `ler_base` + metadados; `alteradoras`: lista de {ato, fonte, operacoes,
    vigencia}. Devolve histórico por dispositivo, conflitos e o que não foi aplicado."""
    ordem = [d["chave"] for d in base["dispositivos"]]
    hist = {
        d["chave"]: [
            {
                "vigencia": base["vigente_desde"],
                "tipo": "base",
                "texto": d["texto"],
                "situacao": d["situacao"],
                "redacao_dada_por": d["redacao_dada_por"] or f"texto original da {norma['nome']}",
                "fonte": d["fonte"],
                "citacao": None,
            }
        ]
        for d in base["dispositivos"]
    }
    ops = [
        (o["vigencia"], alt["ato"]["data"], alt["ato"]["nome"], n, o, alt)
        for alt in alteradoras
        for n, o in enumerate(alt["operacoes"])
    ]
    conflitos, nao_aplicado, aplicadas, inferencias = [], [], [], []
    por_chave = {}
    for item in ops:
        por_chave.setdefault((item[4]["chave"], item[0]), []).append(item)
    bloqueadas = set()
    for (chave, vigencia), grupo in por_chave.items():
        atos = {g[5]["ato"]["nome"] for g in grupo}
        textos = {g[4]["texto"] for g in grupo}
        if len(atos) > 1 and len(textos) > 1:
            conflitos.append(
                {
                    "dispositivo": chave,
                    "vigencia": vigencia,
                    "motivo": "duas normas alteram o mesmo dispositivo na mesma data com textos diferentes",
                    "atos": sorted(atos),
                    "trechos": {g[5]["ato"]["nome"]: g[4]["citacao"]["trecho"] for g in grupo},
                    "decisao": "nenhuma: nenhuma das redações foi aplicada",
                }
            )
            bloqueadas.add((chave, vigencia))
    for vigencia, _, _, _, o, alt in sorted(ops, key=lambda x: (x[0] or "9999", x[1], x[2], x[3])):
        if vigencia is None:
            nao_aplicado.append(
                {
                    "dispositivo": o["chave"],
                    "ato": alt["ato"]["nome"],
                    "motivo": "vigência não determinada",
                }
            )
            continue
        if (o["chave"], vigencia) in bloqueadas:
            continue
        atual = hist.get(o["chave"], [{}])[-1]
        existe = bool(atual) and atual["situacao"].startswith(("vigente", "riscado"))
        aviso = None
        if o["tipo"] == "revogar":
            if not existe:
                nao_aplicado.append(
                    {
                        "dispositivo": o["chave"],
                        "ato": alt["ato"]["nome"],
                        "motivo": "revoga dispositivo inexistente",
                    }
                )
                continue
            tipo, situacao = "revogar", "revogado"
        elif not existe:
            tipo, situacao = "incluir", "vigente"
            if o["marcador"] == "NR":
                aviso = "marcador (NR) em dispositivo que não existe: tratado como inclusão"
        elif o["marcador"] == "NR":
            tipo, situacao = "substituir", "vigente"
        elif o["texto"] == atual["texto"]:
            continue  # mesma redação: nada a aplicar
        else:
            conflitos.append(
                {
                    "dispositivo": o["chave"],
                    "vigencia": vigencia,
                    "motivo": "texto diferente sobre dispositivo que já existe, "
                    + (
                        "com marcador (AC) de acréscimo"
                        if o["marcador"] == "AC"
                        else "sem marcador (NR)/(AC) na norma alteradora"
                    ),
                    "atos": [atual["redacao_dada_por"], alt["ato"]["nome"]],
                    "redacao_existente": atual["texto"],
                    "redacao_proposta": o["texto"],
                    "trecho": o["citacao"]["trecho"],
                    "decisao": "nenhuma: a redação proposta não foi aplicada; requer decisão humana",
                }
            )
            continue
        if tipo == "incluir":
            ordem.insert(posicao(ordem, o["chave"]), o["chave"])
        hist.setdefault(o["chave"], []).append(
            {
                "vigencia": vigencia,
                "tipo": tipo,
                "texto": None if tipo == "revogar" else o["texto"],
                "situacao": situacao,
                "redacao_dada_por": alt["ato"]["nome"],
                "fonte": alt["fonte"],
                "citacao": o["citacao"],
                "marcador": o["marcador"],
                "aviso": aviso,
            }
        )
        if tipo == "revogar":
            for filho in subarvore(ordem, o["chave"])[1:]:  # revogar o dispositivo leva os subitens
                if hist[filho][-1]["situacao"].startswith("vigente"):
                    hist[filho].append(
                        {
                            "vigencia": vigencia,
                            "tipo": "revogar_com_pai",
                            "texto": None,
                            "situacao": "revogado",
                            "redacao_dada_por": alt["ato"]["nome"],
                            "fonte": alt["fonte"],
                            "citacao": o["citacao"],
                            "inferido": False,
                            "aviso": None,
                        }
                    )
        if tipo == "substituir":
            # Nova redação de um dispositivo vale para ele inteiro: subitens que o ato não reproduz
            # (nem lista) saem com ele. É inferência (LC 95), marcada e levada ao relatório.
            do_ato = {x[4]["chave"] for x in ops if x[5] is alt and x[0] == vigencia}
            for filho in subarvore(ordem, o["chave"])[1:]:
                if filho in do_ato or not hist[filho][-1]["situacao"].startswith("vigente"):
                    continue
                hist[filho].append(
                    {
                        "vigencia": vigencia,
                        "tipo": "revogar_implicito",
                        "texto": None,
                        "situacao": "revogado",
                        "redacao_dada_por": alt["ato"]["nome"],
                        "fonte": alt["fonte"],
                        "citacao": o["citacao"],
                        "inferido": True,
                        "aviso": f"subitem não reproduzido na nova redação de {o['chave']}: "
                        "revogação inferida, conferir",
                    }
                )
                inferencias.append(
                    {
                        "dispositivo": filho,
                        "ato": alt["ato"]["nome"],
                        "motivo": f"nova redação de {o['chave']}",
                    }
                )
        aplicadas.append(
            {
                "dispositivo": o["chave"],
                "ato": alt["ato"]["nome"],
                "tipo": tipo,
                "vigencia": vigencia,
            }
        )
    return {
        "norma": norma,
        "ordem": ordem,
        "historico": hist,
        "conflitos": conflitos,
        "nao_aplicado": nao_aplicado,
        "aplicadas": aplicadas,
        "inferencias": inferencias,
    }


def texto_vigente(compilado, em):
    """Dispositivos vigentes em `em` (AAAA-MM-DD): a última redação com vigência ≤ `em`."""
    saida = []
    for chave in compilado["ordem"]:
        validas = [h for h in compilado["historico"][chave] if h["vigencia"] <= em]
        if validas and validas[-1]["situacao"].startswith(("vigente", "riscado")):
            saida.append({"chave": chave, **validas[-1]})
    return saida


ITEM_REVOGADO = (
    # (padrão do item, função que devolve as chaves)
    (
        re.compile(
            r"^(?:o|os)\s+arts?\.\s*(\d+(?:-[A-Z])?(?:\s*(?:,|e)\s*\d+(?:-[A-Z])?)*)$", re.I
        ),
        lambda m: [f"article:{n}" for n in re.findall(r"\d+(?:-[A-Z])?", m.group(1))],
    ),
    (
        re.compile(r"^(?:o|os)\s+§§?\s*([\d\sº°,e]+?)\s+do\s+art\.\s*(\d+(?:-[A-Z])?)$", re.I),
        lambda m: [f"article:{m.group(2)}/paragraph:§{n}" for n in re.findall(r"\d+", m.group(1))],
    ),
    (
        re.compile(
            r"^(?:o|os)\s+incisos?\s+([IVXLCDM,\se]+?)\s+do\s+art\.\s*(\d+(?:-[A-Z])?)$", re.I
        ),
        lambda m: [
            f"article:{m.group(2)}/clause:{r}" for r in re.findall(r"[IVXLCDM]+", m.group(1))
        ],
    ),
    (
        re.compile(r"^o\s+parágrafo\s+único\s+do\s+art\.\s*(\d+(?:-[A-Z])?)$", re.I),
        lambda m: [f"article:{m.group(1)}/paragraph:PU"],
    ),
)


def revogacoes(units, alvo):
    """Revogações explícitas da norma `alvo` ("Ficam revogados: I - o art. N, o § 2º do art. M, ...
    da Resolução Normativa nº X"). Só as formas simples viram caminho (artigo, parágrafo, inciso,
    parágrafo único); o resto é devolvido em `sem_caminho`, sem palpite."""
    chaves, achados, sem_caminho = caminhos(units), [], []
    for i, u in enumerate(units):
        if u["owner"] != "self" or not re.search(r"\bficam?\s+revogad[oa]s?\b", u["text"], re.I):
            continue
        artigo = next(
            (
                rotulo_chave(w["label"])
                for w in reversed(units[: i + 1])
                if w["kind"] == "article" and w["owner"] == "self"
            ),
            None,
        )
        for v in units[i : i + 40]:
            if v is not u and (v["kind"] in {"article", "annex"} or v["owner"] != "self"):
                break
            t = limpa_texto(v["text"])
            m = re.search(r"\bda\s+Resolução\s+Normativa\s+n[º°o]\s*([\d.]+)", t)
            if not m or numero_da_norma(m.group(1)) != alvo:
                continue
            lista = re.sub(r"^(?:[IVXLCDM]+\s*-\s*)", "", t[: m.start()]).strip(" ,;")
            for item in re.split(r",\s+(?=(?:o|os|a|as)\s)", lista):
                for padrao, chaves_do_item in ITEM_REVOGADO:
                    if achou := padrao.match(item.strip()):
                        achados += [
                            {
                                "chave": c,
                                "artigo_do_ato": artigo,
                                "unidade": chaves[v["id"]],
                                "trecho": t[:400],
                                "inicio": v["start"],
                                "fim": v["end"],
                            }
                            for c in chaves_do_item(achou)
                        ]
                        break
                else:
                    sem_caminho.append(
                        {
                            "item": item.strip()[:200],
                            "artigo_do_ato": artigo,
                            "unidade": chaves[v["id"]],
                        }
                    )
    return achados, sem_caminho


def detectar(extraction, acervo):
    """Passo 1 para cada norma ingerida: o que ela altera, inclui ou revoga no acervo.

    `acervo`: números das normas que o Athenix compila (ex.: {"846"}). Só conta norma-alvo explícita
    (bloco de alteração com a norma citada no caput ou 'Ficam revogados ... da Resolução Normativa nº X');
    alvo fora do acervo é listado e não gera operação."""
    em_blocos = alvos(extraction)
    revogadas = {}
    for numero in acervo:
        achados, sem_caminho = revogacoes(extraction["units"], numero)
        if achados or sem_caminho:
            revogadas[numero] = {
                "dispositivos": [a["chave"] for a in achados],
                "sem_caminho": sem_caminho,
            }
    no_acervo = sorted((set(em_blocos) | set(revogadas)) & set(acervo))
    return {
        "no_acervo": no_acervo,
        "fora_do_acervo": sorted(set(em_blocos) - set(acervo)),
        "revogacoes": revogadas,
    }
