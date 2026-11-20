"""Impacto e prioridade das obrigações: cálculo determinístico sobre parâmetros citados.

Todo número sai de um parâmetro extraído da REN 846 (com dispositivo, trecho e âncora verificada)
ou de uma premissa informada pelo usuário. Sem isso, o valor fica "não estimável".
"""

import json
import math
import re

from .normalizacao import espacos
from datetime import date
from pathlib import Path

PARAMETROS = Path(__file__).parent / "data" / "penalidades_ren846.json"
PERFIL_ILUSTRATIVO = Path(__file__).parent / "data" / "perfil_ilustrativo.json"
AVISO = "Estimativa com base nas premissas listadas, não constitui parecer jurídico."
AVISO_DATA = "Limite legal conforme a data do prazo; a data real da infração pode diferir."
GRUPOS = ("I", "II", "III", "IV", "V")
# Cláusula que altera a régua de penalidade (REN 846/2019).
ALTERA = r"Resolução Normativa(?:\s+ANEEL)?\s+n[º°o]\s*846\b[^.]{0,80}?passa(?:m)?\s+a\s+vigorar"
CATEGORIAS = {
    "multa": "Penalidade / multa",
    "adequacao": "Custo de adequação",
    "receita": "Perda ou redução de receita",
    "fiscalizacao": "Risco operacional / fiscalização",
    "nenhuma": "Sem consequência financeira identificável",
}
ATENUANTES = {"nenhuma": None, "espontanea": "atenuante_espontanea", "ate_tn": "atenuante_tn"}
TERM = re.compile(r"\b[A-ZÀ-Ú][a-zà-ú]+(?:(?:\s+(?:de|da|do|das|dos|e)\s+|\s+)[A-ZÀ-Ú][a-zà-ú]+)+")
GENERIC = {"Resolução Normativa", "Lei", "Redação"}
ADEQUACAO = re.compile(
    r"\b(?:implant|implement|disponibiliz|instal|desenvolv|elabor|contrat|adequ|adquir|mant[eé]r|"
    r"constitu|substitu|ampli|capacit|treina)\w*",
    re.I,
)
RECEITA = re.compile(
    r"Parcela Variável|\bPVI\b|\bPVRO\b|Receita Anual Permitida|\bRAP\b|Fator X", re.I
)
# Só disponibilidade de instalações de transmissão pesa na Parcela Variável; "disponibilidade de
# recursos" ou de atendimento telefônico não (falsos positivos na RN 1.137).
DISPONIBILIDADE = re.compile(
    r"(?:in)?disponibilidade\s+d[aeo]s?\s+(?:instala\w+|ativos?|equipamentos?|linhas?\s+de\s+"
    r"transmiss\w+|fun[çc](?:ão|ões)\s+transmiss\w+|transformador\w*)",
    re.I,
)
FISCALIZACAO = re.compile(
    r"\b(?:ANEEL|fiscaliz\w*|inform\w*|envi\w*|comunic\w*|registr\w*|public\w*|divulg\w*|report\w*)",
    re.I,
)
SEGMENTO = {
    "distribuicao": re.compile(
        r"distribuidor|permissionári|concessionári\w* de distribuição", re.I
    ),
    "transmissao": re.compile(r"transmissor|concessionári\w* de transmissão", re.I),
}


def carregar(path=PARAMETROS):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def perfil_ilustrativo():
    """Perfil de demonstração (sem empresa real), com a origem da ordem de grandeza da ROL."""
    return json.loads(PERFIL_ILUSTRATIVO.read_text(encoding="utf-8"))


def termos(texto):
    """Nomes próprios de instrumentos citados na infração ("Plano de Contingência")."""
    return sorted({t for t in TERM.findall(texto) if t not in GENERIC})


def parametro(params, pid):
    """Só entra no cálculo parâmetro com âncora verificada e redação não revogada."""
    p = params["parametros"].get(pid)
    return p if p and p["ancora"] == "verified" and not p.get("revogado") else None


def _numero(texto, minimo=0.0, maximo=math.inf, inteiro=False):
    texto = (texto or "").strip().replace("R$", "").replace(" ", "")
    if not texto:
        return None
    if "," in texto:  # formato brasileiro: 1.234.567,89
        texto = texto.replace(".", "").replace(",", ".")
    valor = float(texto)
    if not math.isfinite(valor) or not minimo <= valor <= maximo:
        raise ValueError(f"Valor fora do intervalo permitido: {texto}")
    if inteiro and valor != int(valor):
        raise ValueError(f"Informe um número inteiro: {texto}")
    return int(valor) if inteiro else valor


def perfil(form):
    """Perfil da empresa a partir do formulário (fronteira de confiança: valida tudo)."""
    get = form.get
    segmento = get("segmento", "") or ""
    atenuante = get("atenuante", "nenhuma") or "nenhuma"
    if segmento not in {"", "distribuicao", "transmissao"} or atenuante not in ATENUANTES:
        raise ValueError("Segmento ou atenuante inválido.")
    hoje = get("data_referencia") or ""
    grupos = {}
    for chave, valor in form.items():
        if chave.startswith("grupo_") and valor:
            if valor not in GRUPOS:
                raise ValueError("Grupo de multa inválido.")
            grupos[chave[6:]] = valor
    return {
        "segmento": segmento,
        "em_operacao": get("em_operacao", "sim") != "nao",
        "base": _numero(get("base")),
        "faturamento": _numero(get("faturamento")),
        "reincidencias": _numero(get("reincidencias"), 0, 10, True) or 0,
        "tn_nao_atendidos": _numero(get("tn_nao_atendidos"), 0, 20, True) or 0,
        "antecedentes": _numero(get("antecedentes"), 0, 50, True) or 0,
        "soma_antecedentes_pct": _numero(get("soma_antecedentes_pct"), 0, 100),
        "atenuante": atenuante,
        "fracao_valor_base": _numero(get("fracao_valor_base"), 0, 100),
        "data_referencia": date.fromisoformat(hoje) if hoje else date.today(),
        "grupos": grupos,
    }


def _faixa_antecedentes(params, soma):
    """Percentual por antecedente conforme o somatório das multas anteriores (Art. 23, III, a–e)."""
    for letra in "abcde":
        p = parametro(params, f"antecedentes_{letra}")
        if not p:
            return None, None
        piso = re.search(r"igual ou superior a (\d+(?:,\d+)?)%", p["trecho"])
        teto = re.search(r"menor que (\d+(?:,\d+)?)%", p["trecho"])
        lo = float(piso.group(1).replace(",", ".")) if piso else -math.inf
        hi = float(teto.group(1).replace(",", ".")) if teto else math.inf
        if lo <= soma < hi:
            return p["percentuais"][0], f"antecedentes_{letra}"
    return None, None


def agravantes(params, p):
    """Soma dos agravantes (Art. 23, § 2º). Devolve (percentual ou None, premissas)."""
    total, premissas = 0.0, []
    regras = (
        ("reincidencias", "agravante_reincidencia", "reincidência(s) específica(s)"),
        ("tn_nao_atendidos", "agravante_tn", "Termo(s) de Notificação não atendido(s)"),
    )
    for campo, pid, nome in regras:
        n = p[campo]
        if not n:
            continue
        par = parametro(params, pid)
        if not par:
            return None, premissas + [_premissa(f"{n} {nome}", None, "parâmetro não verificado")]
        cada, teto = par["percentuais"][0], (par["percentuais"][1:] or [math.inf])[-1]
        valor = min(n * cada, teto)
        total += valor
        premissas.append(_premissa(f"{n} {nome}: +{_pct(valor)} (até {_pct(cada)} cada)", pid))
    if p["antecedentes"]:
        par = parametro(params, "agravante_antecedentes")
        if p["soma_antecedentes_pct"] is None:
            cada, pid = (par["percentuais"][1], "agravante_antecedentes") if par else (None, None)
            nota = "somatório não informado: usada a faixa máxima"
        else:
            cada, pid = _faixa_antecedentes(params, p["soma_antecedentes_pct"])
            nota = f"somatório informado {_pct(p['soma_antecedentes_pct'])} da base"
        if not par or cada is None:
            return None, premissas + [_premissa("antecedentes", None, "parâmetro não verificado")]
        valor = min(p["antecedentes"] * cada, par["percentuais"][-1])
        total += valor
        premissas.append(
            _premissa(f"{p['antecedentes']} antecedente(s): +{_pct(valor)} ({nota})", pid)
        )
    if premissas:
        premissas.append(_premissa("Agravantes somados", "agravantes_somam"))
    return total, premissas


def _premissa(texto, pid, nota=None, editavel=True):
    return {"texto": texto, "parametro": pid, "nota": nota, "editavel": editavel}


def _pct(valor):
    return f"{valor:.4f}".rstrip("0").rstrip(".").replace(".", ",") + "%"


def reais(valor):
    inteiro, frac = f"{valor:,.2f}".split(".")
    return "R$ " + inteiro.replace(",", ".") + "," + frac


def titulo_obrigacao(texto, limite=88):
    """Resumo derivado do texto; a citação literal continua no detalhe. `limite=None` não corta o
    título (PDF, diagnóstico e planilha mostram a frase inteira)."""
    texto = espacos(texto)
    texto = re.sub(r"^(?:(?:[IVXLCDM]+\s*[-–]|\d+[.]|[a-z][)])\s*)+", "", texto)
    # "dias mês para": redação literal do Art. 13, VI da RN 1.137/2025.
    texto = re.sub(r"^Até .*? dias(?: mês)? para\s+", "", texto, flags=re.I)
    modal = re.match(r"^.*?\b(não\s+)?(?:devem|deverão|deve|deverá)\s+", texto, flags=re.I)
    if modal:
        texto = ("não " if modal[1] else "") + texto[modal.end() :]
    resumos = {
        "revisar e publicar os planos de manejo vegetal, de comunicação e de contingência": "Revisar e publicar planos de manejo, comunicação e contingência",
        "estabelecer um plano de manejo vegetal na sua área de atuação": "Criar o plano de manejo vegetal",
        "garantir a rápida remoção de árvores ou galhos caídos sobre a rede": "Remover árvores ou galhos caídos sobre a rede",
    }
    for inicio, resumo in resumos.items():
        if texto.casefold().startswith(inicio):
            return resumo
    texto = re.split(
        r",?\s+(?:de que tratam|conforme|nos termos|que contemple|com vistas)\b",
        texto,
        maxsplit=1,
        flags=re.I,
    )[0]
    texto = texto.rstrip(" :;.")
    if limite and len(texto) > limite:
        texto = texto[: limite - 3].rsplit(" ", 1)[0] + "…"
    return texto[:1].upper() + texto[1:] if texto else "Revisar obrigação na fonte"


def texto_obrigacao(row):
    return " ".join([row.get("action", "")] + [e.get("quote", "") for e in row.get("evidence", [])])


def enquadramentos(params, texto):
    """Infrações da REN 846 cujos instrumentos nomeados aparecem todos no texto da obrigação."""
    alvo = _singular(texto)
    return [
        i
        for i in params["infracoes"]
        if i["ancora"] == "verified"
        and i["termos"]
        and all(_singular(t) in alvo for t in i["termos"])
    ]


def _singular(texto):
    # shortcut: tira o "s" final de cada palavra ("planos" = "plano"); plurais em -ões não casam.
    return " ".join(w.rstrip("s") for w in texto.casefold().split())


def classificar(row, texto, p):
    """Categorias de consequência, cada uma com o motivo determinístico."""
    if row.get("modality") == "permission":
        return [("nenhuma", "Faculdade: não há dever cujo descumprimento gere sanção.")]
    out = [
        (
            "multa",
            "Dever em norma da ANEEL: o descumprimento sujeita às penalidades do Art. 5º da REN 846.",
        )
    ]
    if m := ADEQUACAO.search(row.get("action", "")):
        out.append(("adequacao", f'Exige "{m.group()}": custo interno da empresa.'))
    transmissao = p["segmento"] == "transmissao" or (
        not p["segmento"] and SEGMENTO["transmissao"].search(texto)
    )
    if (m := RECEITA.search(texto)) or (transmissao and DISPONIBILIDADE.search(texto)):
        termo = m.group() if m else "disponibilidade de instalações de transmissão"
        out.append(
            ("receita", f'Menciona "{termo}": pode afetar a receita (Parcela Variável/Fator X).')
        )
    if m := FISCALIZACAO.search(row.get("action", "")):
        out.append(
            ("fiscalizacao", f'Dever de "{m.group()}": falha é verificável em fiscalização.')
        )
    return out


def aplicabilidade(row, p):
    if not p["segmento"]:
        return True, "Segmento não informado: considerada aplicável (premissa)."
    texto = row.get("subject", "") + " " + row.get("action", "")
    proprio = SEGMENTO[p["segmento"]].search(texto)
    outro = next((s for s, rx in SEGMENTO.items() if s != p["segmento"] and rx.search(texto)), None)
    if outro and not proprio:
        return False, f"Sujeito do dispositivo é do segmento de {outro.replace('cao', 'ção')}."
    return (
        True,
        "Sujeito compatível com o segmento informado."
        if proprio
        else "Sujeito genérico: considerada aplicável (premissa).",
    )


def urgencia(row, hoje):
    datas = [d for d in row.get("deadlines", []) if d.get("date")]
    if datas:
        prazo = min(datas, key=lambda d: d["date"])
        quando = date.fromisoformat(prazo["date"])
        dias = (quando - hoje).days
        estado = "confirmado" if prazo.get("state") == "confirmed" else "provisório"
        data_br = quando.strftime("%d/%m/%Y")
        if dias < 0:
            return {
                "nivel": 0,
                "dias": dias,
                "data": prazo["date"],
                "texto": f"venceu em {data_br}, há {-dias} dias (prazo {estado}): exposição atual",
                "principal": f"Vencido desde {data_br} ({-dias} dias)",
                "detalhe": f"Prazo {estado}; exposição atual calculada na data de referência.",
            }
        return {
            "nivel": 1 if dias <= 90 else 2,
            "dias": dias,
            "data": prazo["date"],
            "texto": f"vence em {data_br}, faltam {dias} dias (prazo {estado})",
            "principal": f"Vence em {data_br}",
            "detalhe": f"Faltam {dias} dias; prazo {estado}.",
        }
    estados = {d.get("state") for d in row.get("deadlines", [])}
    if "recurring" in estados:
        texto = "obrigação recorrente: próxima ocorrência não calculada"
    elif "awaiting_event" in estados:
        texto = "prazo conta de um evento ainda sem data"
    else:
        texto = "sem prazo identificado no texto"
    return {
        "nivel": 3,
        "dias": None,
        "data": None,
        "texto": texto,
        "principal": texto[:1].upper() + texto[1:],
        "detalhe": "Nenhuma data foi presumida.",
    }


def teto_legal(params, row, p):
    """Teto legal por infração em % da base de cálculo: (limite, premissas, detalhes).

    A redação vale pela data da infração: a do prazo (vencido ou a vencer) ou, sem prazo, a data de
    referência do perfil (premissa). Antes do início dos efeitos da Lei 15.269/2025 vale a redação
    anterior; se esse início não estiver confirmado, usa o limite atual e mostra o anterior. D6: com
    faturamento bruto e base informados, o teto (% do faturamento) é convertido para % da base.
    """
    atual = parametro(params, "teto_legal_lei")
    if not atual or not atual["percentuais"]:
        return (
            math.inf,
            [_premissa("Teto legal sem parâmetro verificado: resultado sem limite final", None)],
            None,
        )
    anterior = parametro(params, "teto_legal_anterior")
    anterior_pct = anterior["percentuais"][0] if anterior and anterior["percentuais"] else None
    vigencia = parametro(params, "teto_legal_vigencia")
    inicio = date.fromisoformat(vigencia["data"]) if vigencia and vigencia.get("data") else None
    prazo = urgencia(row, p["data_referencia"])["data"]
    quando = date.fromisoformat(prazo) if prazo else p["data_referencia"]
    origem_data = "data do prazo" if prazo else "data de referência do perfil (obrigação sem prazo)"
    alternativo = None
    if inicio and anterior_pct is not None and quando < inicio:
        lei, pid = anterior, "teto_legal_anterior"
        regra = (
            f"infração em {quando:%d/%m/%Y}, antes de {inicio:%d/%m/%Y} ({vigencia['dispositivo']})"
        )
    elif inicio:
        lei, pid = atual, "teto_legal_lei"
        regra = f"infração em {quando:%d/%m/%Y}, a partir de {inicio:%d/%m/%Y} ({vigencia['dispositivo']})"
    else:
        lei, pid, alternativo = atual, "teto_legal_lei", anterior_pct
        regra = (
            "início dos efeitos da nova redação não confirmado no texto: usado o limite atual"
            + (f"; antes dela valia {_pct(anterior_pct)}" if anterior_pct is not None else "")
        )
    pct = lei["percentuais"][0]
    redacao = (
        f", redação dada pela {lei['redacao_dada_por']}" if lei.get("redacao_dada_por") else ""
    )
    premissas = [
        _premissa(
            f"Teto legal: {_pct(pct)} do faturamento por infração ({lei['dispositivo']}{redacao}); "
            f"{regra}; data considerada: {origem_data}",
            pid,
            editavel=False,
        ),
        _premissa(AVISO_DATA, pid, editavel=False),
    ]
    faturamento, base = p.get("faturamento"), p["base"]
    if faturamento is not None and base:
        limite = pct * faturamento / base
        premissas.append(
            _premissa(
                f"Faturamento bruto informado ({reais(faturamento)}): teto legal = {_pct(limite)} da base",
                pid,
                "dúvida D6",
            )
        )
    elif faturamento is not None:
        limite = pct
        premissas.append(
            _premissa(
                "Faturamento bruto informado: informe a base para converter o teto legal", None
            )
        )
    else:
        limite = pct
        premissas.append(
            _premissa(
                "Teto legal possivelmente subestimado: faturamento bruto não informado, aplicado sobre a base (ROL)",
                pid,
                "dúvida D6: informe o faturamento bruto dos 12 meses anteriores",
            )
        )
    detalhes = {
        "pct_lei": pct,
        "parametro": pid,
        "data": quando.isoformat(),
        "alternativo_pct": alternativo,
        "subestimado": faturamento is None,
    }
    return limite, premissas, detalhes


def multa(params, row, p, grupos, explicitos):
    """Faixa da multa em % da base e, se informada, em R$. Dois cenários para a dúvida D5."""
    limites = {g: parametro(params, f"limite_grupo_{g}") for g in grupos}
    if not all(limites.values()) or not parametro(params, "base_grupos"):
        return {"estimavel": False, "motivo": "Limite do grupo sem âncora verificada."}
    teto = max(lim["percentuais"][0] for lim in limites.values())
    piso_teto = min(lim["percentuais"][0] for lim in limites.values())
    agr, premissas = agravantes(params, p)
    origem = (
        "informado pelo usuário"
        if row["id"] in p["grupos"]
        else "indicado por termo coincidente com infração tipificada"
        if explicitos
        else "desconhecido: considerados todos os grupos"
    )
    premissas = [
        _premissa(
            f"Enquadramento: Grupo(s) {', '.join(grupos)} ({origem})",
            f"limite_grupo_{grupos[-1]}",
            "a ANEEL decide o enquadramento",
        ),
        _premissa(
            "Mínimo 0: cabe advertência ou atenuante, e a metodologia do valor base não está no repositório",
            "advertencia",
            editavel=False,
        ),
        _premissa("Máximo sem atenuante (pior caso)", "ordem_calculo", editavel=False),
    ] + premissas
    if agr is None:
        return {
            "estimavel": False,
            "motivo": "Agravante sem parâmetro verificado.",
            "premissas": premissas,
        }
    # Teto legal por infração (Lei 9.427/1996, Art. 3º, X): limite final nos dois cenários da D5.
    limite, extras, legal = teto_legal(params, row, p)
    premissas += extras
    res = {
        "estimavel": True,
        "grupos": grupos,
        "teto_pct": teto,
        "piso_teto_pct": piso_teto,
        "teto_legal_pct": None if math.isinf(limite) else limite,
        "teto_legal": legal,
        "agravantes_pct": agr,
        "minimo_pct": 0.0,
        "maximo": {"com_teto": min(teto, limite), "sem_teto": min(teto * (1 + agr / 100), limite)},
        "limitado_teto_legal": teto * (1 + agr / 100) > limite,
        "provavel": None,
        "premissas": premissas,
    }
    if p["fracao_valor_base"] is not None and len(grupos) == 1:
        aten = parametro(params, ATENUANTES[p["atenuante"]]) if ATENUANTES[p["atenuante"]] else None
        reducao = aten["percentuais"][0] if aten else 0.0
        base = teto * p["fracao_valor_base"] / 100
        bruto = base * (1 + agr / 100)
        res["provavel"] = {
            "com_teto": min(min(bruto, teto) * (1 - reducao / 100), limite),
            "sem_teto": min(bruto * (1 - reducao / 100), limite),
        }
        premissas.append(
            _premissa(
                f"Valor base = {_pct(p['fracao_valor_base'])} do teto (informado pelo usuário)",
                "pisos_tetos",
            )
        )
        premissas.append(
            _premissa(f"Atenuante: {p['atenuante']} (−{_pct(reducao)})", ATENUANTES[p["atenuante"]])
        )
    elif p["fracao_valor_base"] is None:
        res["motivo_provavel"] = (
            "Valor provável não estimável: informe a fração do teto usada como valor base."
        )
    else:
        res["motivo_provavel"] = "Valor provável não estimável sem enquadramento em um único grupo."
    return res


def _base(params, p):
    if p["segmento"] == "transmissao" and not p["em_operacao"]:
        return "RAP vigente na data do auto de infração", "base_rap"
    return "ROL dos 12 meses anteriores ao auto de infração", "base_rol"


def avaliar(params, rows, p):
    """Avalia e prioriza obrigações pela REGRA_ORDEM: exposição provável × peso do prazo. As de
    enquadramento desconhecido saem da fila e vão para "verificar" (faixa larga, confiança baixa)."""
    base_nome, base_pid = _base(params, p)
    resultado = []
    for row in rows:
        if row.get("status") in {"rejected", "superseded", "revoked"}:
            continue
        verificada = any(a.get("state") == "verified" for a in row.get("anchors", []))
        texto = texto_obrigacao(row)
        aplicavel, motivo_aplic = aplicabilidade(row, p)
        cats = classificar(row, texto, p)
        explicitos = enquadramentos(params, texto)
        if confirmado := row.get("enquadramento"):
            # Enquadramento confirmado por pessoa (services.review, ação "frame") prevalece.
            infracao = next(
                (i for i in params["infracoes"] if i["dispositivo"] == confirmado["dispositivo"]),
                None,
            )
            if infracao:
                explicitos = [infracao | {"confirmado": confirmado}]
        grupos = (
            [p["grupos"][row["id"]]]
            if row["id"] in p["grupos"]
            else sorted({i["grupo"] for i in explicitos}, key=GRUPOS.index) or list(GRUPOS)
        )
        item = {
            "row": row,
            "titulo": titulo_obrigacao(row.get("action", "")),
            "verificada": verificada,
            "aplicavel": aplicavel,
            "motivo_aplicabilidade": motivo_aplic,
            "categorias": cats,
            "enquadramentos": explicitos,
            "urgencia": urgencia(row, p["data_referencia"]),
            "multa": None,
        }
        if not verificada:
            item["multa"] = {
                "estimavel": False,
                "motivo": "Obrigação sem citação verificada: fora do cálculo.",
            }
        elif any(c == "multa" for c, _ in cats):
            item["multa"] = multa(params, row, p, grupos, explicitos)
        m = item["multa"]
        if m and m.get("estimavel") and p["base"] is not None:
            m["reais"] = {
                "minimo": 0.0,
                "maximo": {k: v / 100 * p["base"] for k, v in m["maximo"].items()},
                "provavel": {k: v / 100 * p["base"] for k, v in m["provavel"].items()}
                if m["provavel"]
                else None,
            }
        item["confianca"], item["motivo_confianca"] = confianca(item, p)
        resultado.append(item)
    estimaveis = [
        i for i in resultado if i["aplicavel"] and i["multa"] and i["multa"].get("estimavel")
    ]
    for i in estimaveis:
        i["verificar"] = not enquadramento_conhecido(i, p)
    ranking = sorted(
        (i for i in estimaveis if not i["verificar"]),
        key=lambda i: (-prioridade(i), i["urgencia"]["nivel"], i["urgencia"]["data"] or "9999"),
    )
    verificar = sorted(
        (i for i in estimaveis if i["verificar"]),
        key=lambda i: (i["urgencia"]["nivel"], i["urgencia"]["data"] or "9999"),
    )
    return {
        "itens": resultado,
        "ranking": ranking,
        "verificar": verificar,
        "regra": REGRA_ORDEM,
        "frases": [frase(i, p, n) for n, i in enumerate(ranking[:3])],
        "base": {"nome": base_nome, "parametro": base_pid, "valor": p["base"]},
        "aviso": AVISO,
    }


# Peso do prazo na prioridade. Premissa de produto, ainda sem validação de especialista (Bloco 5).
PESO_URGENCIA = {0: 1.0, 1: 0.8, 2: 0.5, 3: 0.3}
REGRA_ORDEM = (
    "Ordem: exposição provável (o valor provável, se informado; senão, o ponto médio da faixa) "
    "multiplicada pelo peso do prazo (vencida 1; vence em até 90 dias 0,8; depois 0,5; sem data 0,3); "
    'obrigações com enquadramento desconhecido ficam fora da fila, em "Verificar enquadramento".'
)


def enquadramento_conhecido(item, p):
    """Grupo escolhido pelo usuário ou infração tipificada identificada pelo texto."""
    return item["row"]["id"] in p["grupos"] or bool(item["enquadramentos"])


def exposicao(item):
    """Exposição provável em % da base: o valor provável informado ou o ponto médio de [0, máximo]."""
    m = item["multa"]
    return m["provavel"]["sem_teto"] if m["provavel"] else m["maximo"]["sem_teto"] / 2


def prioridade(item):
    return exposicao(item) * PESO_URGENCIA[item["urgencia"]["nivel"]]


def confianca(item, p):
    m = item["multa"]
    if not m or not m.get("estimavel"):
        return "baixo", m["motivo"] if m else "Sem consequência financeira estimável."
    if not enquadramento_conhecido(item, p):
        # Faixa de todos os grupos: larga demais para decidir antes de confirmar o enquadramento.
        return "baixo", "Enquadramento desconhecido: confirme o grupo de multa antes de priorizar."
    faltas = []
    if p["base"] is None:
        faltas.append("base de cálculo não informada")
    if m["provavel"] is None:
        faltas.append("valor provável sem premissa")
    if not faltas and item["row"]["id"] in p["grupos"]:
        return "alto", "Base, enquadramento e valor base informados; parâmetros verificados."
    if not faltas:
        return (
            "médio",
            "Enquadramento só por coincidência de termos com a infração: confirme o grupo.",
        )
    if len(faltas) == 1 and p["base"] is not None:
        return "médio", "Falta: " + faltas[0] + "."
    return "baixo", "Falta: " + "; ".join(faltas) + "."


def formatar(item, p, chave="sem_teto"):
    m = item["multa"]
    escolhido = m["provavel"] or m["maximo"]
    pct = escolhido[chave]
    rotulo = "provável" if m["provavel"] else "no máximo"
    if p["base"] is not None:
        return f"{rotulo} {reais(pct / 100 * p['base'])} ({_pct(pct)} da base)"
    return f"{rotulo} {_pct(pct)} da base (informe a base para ver em R$)"


ORDEM = ("Faça isto primeiro", "Depois", "Em seguida", "Na sequência", "Por último")


def frase(item, p, posicao):
    acao = espacos(item["row"].get("action", ""))
    acao = acao[:140] + ("…" if len(acao) > 140 else "")
    return f"{ORDEM[posicao]}: {acao} — pesa {formatar(item, p)} e {item['urgencia']['texto']}."


def nomeia(item, segmento):
    texto = item["row"].get("subject", "") + " " + item["row"].get("action", "")
    return bool(SEGMENTO[segmento].search(texto))


def destaques(resultado, p, limite=5):
    """Abertura do relatório: até `limite` obrigações na ordem da regra de prioridade.

    Vêm primeiro as que nomeiam o segmento do perfil; sem segmento informado, as que nomeiam
    transmissoras (público inicial), quando houver. Só se faltarem (menos de 3) entram as de sujeito
    genérico, marcadas. Texto repetido aparece uma vez. Também lista onde a Parcela Variável seria o
    impacto principal: obrigações aplicáveis classificadas como perda de receita.
    """
    ranking = resultado["ranking"]
    alvo = p["segmento"] or (
        "transmissao" if any(nomeia(i, "transmissao") for i in ranking) else ""
    )
    vistos, proprios, genericos = set(), [], []
    for i in ranking:
        # Mesma regra no Anexo e no bloco de nova redação ("…(NR)"): o início basta para repetir.
        chave = espacos(i["row"].get("action", "")).casefold()[:200]
        if chave in vistos:
            continue
        vistos.add(chave)
        if alvo and nomeia(i, alvo):
            proprios.append(i)
        elif not any(nomeia(i, s) for s in SEGMENTO):
            genericos.append(i)
    escolha = (
        proprios[:limite] + genericos[: max(0, 3 - len(proprios))] if alvo else genericos[:limite]
    )
    especificos = {id(i) for i in proprios}
    receita = [
        i
        for i in resultado["itens"]
        if i["aplicavel"] and any(c == "receita" for c, _ in i["categorias"])
    ]
    return {
        "segmento": alvo,
        "itens": [
            {"item": i, "especifica": id(i) in especificos, "frase": frase(i, p, n)}
            for n, i in enumerate(escolha)
        ],
        "outros": len(ranking) - len(escolha),
        # Nomeiam o segmento, mas sem enquadramento: ficam em "Verificar enquadramento".
        "verificar_segmento": [
            i for i in resultado.get("verificar", []) if alvo and nomeia(i, alvo)
        ],
        "parcela_variavel": receita if alvo != "distribuicao" else [],
    }


def redacao_alterada(units, unit):
    """Texto que segue o caput até o próximo artigo da própria norma."""
    index = next(n for n, u in enumerate(units) if u["id"] == unit["id"])
    redacao = []
    for u in units[index + 1 :]:
        if u["kind"] == "article" and u.get("owner") == unit.get("owner"):
            break
        redacao.append(u)
    return redacao


def alteracoes_da_regua(units):
    """Dispositivos do documento que alteram a REN 846 (a régua de penalidade)."""
    return [u for u in units if re.search(ALTERA, espacos(u["text"]))]


TIPOS_ATO = {
    "REN": "Resolução Normativa",
    "RN": "Resolução Normativa",
    "REH": "Resolução Homologatória",
}
CITACAO_ATO = re.compile(
    r"\b(Resolução Normativa|Resolução Homologatória|Resolução Autorizativa|Lei Complementar|Lei|"
    r"Decreto|Despacho|Portaria|REN|RN|REH)(?:\s+ANEEL)?\s+(?:n[º°o]\.?\s*)?(\d{1,3}(?:\.\d{3})*|\d+)"
    r"(?:/(\d{4}))?(?:,?\s+de\s+(\d{1,2})[º°o]?\s+de\s+([a-zç]+)(?:\s+de\s+(\d{4}))?)?"
)


def citacoes_divergentes(units):
    """Mesma norma (tipo e número) citada no documento com dia, mês ou ano diferentes.

    Parte ausente não conta como conflito: "de 21 de novembro" diverge de "de 16 de novembro de
    2021" pelo dia. Cada variante leva o trecho e a unidade, para conferência na fonte.
    """
    variantes = {}
    for unit in units:
        if unit.get("struck"):
            continue
        texto = espacos(unit["text"])
        for m in CITACAO_ATO.finditer(texto):
            dia, mes, ano = m.group(4), m.group(5), m.group(6) or m.group(3)
            if not (dia or ano):
                continue
            tipo = TIPOS_ATO.get(m.group(1), m.group(1))
            chave = (tipo, m.group(2).replace(".", ""))
            data = (int(dia) if dia else None, mes, ano)
            lista = variantes.setdefault(chave, [])
            if all(v["data"] != data for v in lista):
                lista.append({"data": data, "trecho": m.group(0), "unit_id": unit["id"]})
    alertas = []
    for (tipo, numero), lista in variantes.items():
        conflita = any(
            x is not None and y is not None and x != y
            for a in lista
            for b in lista
            for x, y in zip(a["data"], b["data"])
        )
        if conflita:
            alertas.append({"ato": f"{tipo} nº {numero}", "citacoes": lista})
    return alertas
