import calendar
import re
from datetime import date, timedelta

from .structure import DATE, parse_date

NUMBERS = {
    **dict.fromkeys(("um", "uma"), 1), **dict.fromkeys(("dois", "duas"), 2),
    **dict.fromkeys(("três", "tres"), 3), "quatro": 4, "cinco": 5, "seis": 6, "sete": 7,
    "oito": 8, "nove": 9, "dez": 10, "onze": 11, "doze": 12, "treze": 13,
    **dict.fromkeys(("catorze", "quatorze"), 14), "quinze": 15, "dezesseis": 16,
    "dezessete": 17, "dezoito": 18, "dezenove": 19, "vinte": 20, "trinta": 30, "quarenta": 40,
    "cinquenta": 50, "sessenta": 60, "setenta": 70, "oitenta": 80, "noventa": 90,
    **dict.fromkeys(("cem", "cento"), 100), **dict.fromkeys(("duzentos", "duzentas"), 200),
    **dict.fromkeys(("trezentos", "trezentas"), 300), "quatrocentos": 400, "quinhentos": 500,
    "seiscentos": 600, "setecentos": 700, "oitocentos": 800, "novecentos": 900,
}  # fmt: skip
_WORD = "|".join(sorted(NUMBERS, key=len, reverse=True))
# Quantidade em algarismos ("90 (noventa) dias") ou por extenso ("cento e vinte dias").
PERIOD = re.compile(
    rf"\b(\d+|(?:{_WORD})(?:\s+e\s+(?:{_WORD}))*)\s*(?:\([^)]{{1,60}}\)\s*)?"
    r"(dias?(?:\s+úteis|\s+corridos)?|meses|mês|anos?|minutos?|horas?)\b",
    re.I,
)
# Publicação/vigência da própria norma ("da publicação", "desta Resolução") × de outro ato
# ("da publicação das instruções", "da minuta"), que é evento futuro sem data.
OWN_MARK = re.compile(
    r"\b(publicação|vigência|entrada em vigor)(?:\s+(dest[ae]|d[aoe]s?)\s+(\w+))?", re.I
)
EVENT = re.compile(
    r"\b(?:contad[oa]s?|a\s+partir|após|antes|advento)\b[^.;]{0,30}?\bd[aoe]s?\s+\w+", re.I
)


MONTH_NAMES = (
    "janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro"
)
FREQUENCY = "anual|mensal|semestral|trimestral|bimestral|semanal|diária"
# Recorrência: "anualmente", "com periodicidade anual", "a cada ano", "em janeiro" (sem ano).
# "a cada período de 12 meses": o "12 meses" é a PERIODICIDADE, não um prazo único para cumprir.
PERIODO_RECORRENTE = re.compile(
    r"a\s+cada\s+per[íi]odo\s+de\s+(?:\d+|\w+)\s*(?:\([^)]{1,40}\)\s*)?(?:dias|meses|anos?)\b", re.I
)
# "maior que 12 meses", "superior a 30 dias": limite de comparação, não prazo para cumprir.
COMPARACAO = re.compile(
    r"(?:maior|menor|superior|inferior|mais|menos)"
    + r"\s+(?:do\s+)?que\s+$|(?:superior|inferior|igual)\s+a\s+$",
    re.I,
)
# Marco direto, sem quantidade de dias: "devem ser implementadas na data de publicação desta Resolução".
# "entra em vigor na data de sua publicação" é vigência (não é prazo de obrigação) e fica de fora.
MARCO_DIRETO = re.compile(
    r"\bna\s+data\s+(?:de|da)\s+(?:sua\s+|dest[ae]\s+)?publicação(?:\s+dest[ae]\s+Resolução(?:\s+Normativa)?)?",
    re.I,
)
# "o maior prazo entre doze meses da publicação e o prazo informado pela distribuidora": prazo CONDICIONAL.
MAIOR_ENTRE = re.compile(r"\bmaior\s+(?:prazo\s+)?entre\b", re.I)
PERIODIC = re.compile(
    r"\b(?:(?:anual|mensal|semestral|trimestral|bimestral|semanal|diari)mente"
    rf"|com\s+periodicidade\s+(?:mínima\s+)?(?:{FREQUENCY})"
    r"|a\s+cada\s+(?:ano|mês|semestre|trimestre|bimestre|semana)"
    r"|a\s+cada\s+per[íi]odo\s+de\s+(?:\d+|\w+)\s*(?:\([^)]{1,40}\)\s*)?(?:dias|meses|anos?)"
    rf"|(?:em|no\s+mês\s+de)\s+(?:{MONTH_NAMES})(?!\s+de\s+\d{{4}}))\b",
    re.I,
)


def clause(text, start, end):
    """Cláusula entre o ponto/ponto e vírgula anterior e o seguinte."""
    left = max(text.rfind(".", 0, start), text.rfind(";", 0, start)) + 1
    tail = re.split(r"[.;]", text[end:], maxsplit=1)[0]
    return text[left:end] + tail


def quantity(token):
    if token.isdigit():
        return int(token)
    return sum(NUMBERS[word] for word in re.split(r"\s+e\s+", token.lower()))


def landmark(text):
    mark = OWN_MARK.search(text)
    if mark:
        connector, noun = (mark.group(2) or "").lower(), (mark.group(3) or "").lower()
        if not connector or connector.startswith("dest") or noun == "presente":
            if mark.group(1).lower() == "publicação":
                return "publication", "Publicação da norma"
            return "effective", "Vigência da norma"
        return "event", mark.group(0)[:1].upper() + mark.group(0)[1:]
    event = EVENT.search(text)
    if event:
        return "event", event.group(0).strip()
    return "unknown", "Marco não identificado"


def unique_date(dates, kind):
    candidates = {d["date"] for d in dates if d["kind"] == kind}
    return next(iter(candidates)) if len(candidates) == 1 else None


def compute(quantity, unit, base, direction=1, convention="last_day"):
    if unit.startswith("dia"):
        return base + timedelta(days=direction * quantity)
    months = quantity * (12 if unit.startswith("ano") else 1) * direction
    absolute = base.year * 12 + base.month - 1 + months
    year, month = divmod(absolute, 12)
    month += 1
    last = calendar.monthrange(year, month)[1]
    if base.day > last and convention == "next_day":
        return date(year, month, last) + timedelta(days=1)
    return date(year, month, min(base.day, last))


def rules(text, unit_id, dates, inherited="", clarification=False, target_dates=None):
    result = []
    recorrentes = [m.span() for m in PERIODO_RECORRENTE.finditer(text)]
    periods = [
        m
        for m in PERIOD.finditer(text)
        if not any(a <= m.start() and m.end() <= b for a, b in recorrentes)
        and not COMPARACAO.search(text[max(0, m.start() - 30) : m.start()])
    ]
    for index, match in enumerate(periods):
        left = max(text.rfind(".", 0, match.start()) + 1, text.rfind(";", 0, match.start()) + 1)
        end = periods[index + 1].start() if index + 1 < len(periods) else len(text)
        # Ponto ou ponto e vírgula fecham a cláusula; quebra de linha do PDF/HTML não.
        tail = re.split(r"[.;]", text[match.end() : end], maxsplit=1)[0]
        local = text[left : match.end()] + tail
        kind, label = landmark(local)
        inherited_used = False
        if kind == "unknown" and inherited:
            kind, label = landmark(inherited)
            inherited_used = kind != "unknown"
        amount, unit = quantity(match.group(1)), match.group(2).lower()
        direction = -1 if re.search(r"\bantes\b|\bantecedência\b", local, re.I) else 1
        record = {
            "unit_id": unit_id,
            "quantity": amount,
            "unit": unit,
            "landmark": kind,
            "event": label,
            "quote": local.strip(),
            "direction": direction,
            "convention": "exclude_start_last_day_v1",
            "inherited": inherited_used,
            "date": None,
            "state": "not_calculated",
        }
        relevant_dates = (target_dates or []) if clarification else dates
        base = unique_date(relevant_dates, kind)
        if "úteis" in unit:
            reason = "Calendário de feriados versionado ausente"
        elif unit.startswith(("minuto", "hora")) and kind != "event":
            # Minutos/horas só fazem sentido a partir de um evento operacional; nunca viram data civil.
            reason = "Prazo em minutos/horas sem evento identificado; nenhuma data presumida"
        elif kind == "event":
            record["state"] = "awaiting_event"
            reason = label + "; sem data até o evento"
        elif not base:
            reason = "Marco desconhecido ou datas conflitantes; nenhuma data presumida"
        else:
            try:
                record["date"] = compute(
                    amount, unit, date.fromisoformat(base), direction
                ).isoformat()
                record["state"] = "provisional"
                record["base"] = base
                reason = "Calculado; convenção ainda não confirmada por pessoa"
            except (ValueError, OverflowError):
                reason = "Quantidade fora do intervalo suportado"
        if record["state"] == "provisional" and MAIOR_ENTRE.search(
            text[max(0, match.start() - 80) : match.start()]
        ):
            # Parcela conhecida (a contada da publicação); o outro termo depende de dado que a norma não traz.
            record["parcela_conhecida"] = record["date"]
            record["date"] = None
            record["state"] = "conditional"
            record["event"] = f"O maior entre {amount} {unit} da publicação e o prazo informado"
            reason = (
                "Prazo condicional: o maior de dois termos, e um deles depende de informação da "
                "distribuidora; sem data única"
            )
        record["explanation"] = (
            f"{amount} {unit}; marco: {label}; base: {base or 'desconhecida'}; "
            f"direção: {'antes' if direction < 0 else 'após'}; "
            f"convenção: exclui início, mês limitado ao último dia (v1). {reason}."
        )
        result.append(record)
    for match in PERIODIC.finditer(text):
        result.append(
            {
                "unit_id": unit_id,
                "quantity": None,
                "unit": "periodic",
                "landmark": "recurring",
                "event": match.group(0),
                "quote": clause(text, match.start(), match.end()).strip(),
                "direction": 1,
                "convention": "periodic_v1",
                "inherited": False,
                "date": None,
                "state": "recurring",
                "explanation": f"Obrigação recorrente ({match.group(0)}); próxima ocorrência "
                "não calculada sem calendário de referência.",
            }
        )
    if not periods:
        for match in MARCO_DIRETO.finditer(text):
            antes = text[max(0, match.start() - 60) : match.start()]
            if re.search(r"vigor|vigência|efeitos", antes, re.I):
                continue
            base = unique_date(dates, "publication")
            result.append(
                {
                    "unit_id": unit_id,
                    "quantity": 0,
                    "unit": "dias",
                    "landmark": "publication",
                    "event": "Publicação da norma",
                    "quote": clause(text, match.start(), match.end()).strip(),
                    "direction": 1,
                    "convention": "marco_direto_v1",
                    "inherited": False,
                    "date": base,
                    "base": base,
                    "state": "provisional" if base else "not_calculated",
                    "explanation": "Prazo na data de publicação da norma (marco direto, sem quantidade de dias); "
                    + ("calculado" if base else "publicação desconhecida: nenhuma data presumida")
                    + "; confirmação humana pendente.",
                }
            )
        for match in DATE.finditer(text):
            parsed = parse_date(match)
            if parsed and re.search(
                r"até|prazo|limite", text[max(0, match.start() - 35) : match.start()], re.I
            ):
                result.append(
                    {
                        "unit_id": unit_id,
                        "quantity": None,
                        "unit": "fixed_date",
                        "landmark": "fixed",
                        "date": parsed,
                        "state": "provisional",
                        "quote": match.group(),
                        "convention": "explicit_date_v1",
                        "explanation": f"Data fixa explícita: {parsed}; fundamento: {unit_id}; confirmação humana pendente.",
                    }
                )
    return result


# Redação defeituosa em prazo: unidade combinada/repetida ("180 dias mês", "30 dias dias"), número e
# extenso divergentes ("180 (cento e vinte) dias") ou unidade ausente ("em até 90 (noventa) para").
_UNIDADE = r"(?:dias?(?:\s+úteis|\s+corridos)?|meses|mês|anos?|minutos?|horas?)"
_COMBINADA = re.compile(rf"\b(\d+)\s*(?:\(([^)]{{1,60}})\)\s*)?({_UNIDADE})\s+({_UNIDADE})\b", re.I)
_EXTENSO = re.compile(r"\b(\d+)\s*\(([a-zà-úç\s]{3,60})\)", re.I)
_SEM_UNIDADE = re.compile(
    rf"\b(?:até|em|prazo\s+de)\s+(\d+)\s*(?:\(([^)]{{1,60}})\)\s*)?(?!{_UNIDADE}\b)(para|contad[oa]s?|a\s+partir|após)\b",
    re.I,
)


def erros_materiais(texto):
    """Possíveis erros materiais de prazo no texto, com a leitura mais provável. Nunca corrige sozinho:
    a leitura fica "a confirmar" até um esclarecimento oficial confirmado."""
    out = []
    for m in _COMBINADA.finditer(texto):
        u1, u2 = m.group(3).lower(), m.group(4).lower()
        problema = (
            "unidade repetida" if u1 == u2 else f"unidade combinada ({m.group(3)} {m.group(4)})"
        )
        out.append(
            {"problema": problema, "trecho": m.group(0), "leitura_provavel": f"{m.group(1)} {u1}"}
        )
    for m in _EXTENSO.finditer(texto):
        palavras = re.split(r"\s+e\s+", m.group(2).strip().lower())
        if not all(p in NUMBERS for p in palavras):
            continue
        extenso = sum(NUMBERS[p] for p in palavras)
        if extenso != int(m.group(1)):
            out.append(
                {
                    "problema": f"número e extenso divergentes ({m.group(1)} × {extenso})",
                    "trecho": m.group(0),
                    "leitura_provavel": f"{m.group(1)} (algarismos) ou {extenso} (extenso)",
                }
            )
    for m in _SEM_UNIDADE.finditer(texto):
        out.append(
            {
                "problema": "unidade de tempo ausente",
                "trecho": m.group(0),
                "leitura_provavel": f"{m.group(1)} dias?",
            }
        )
    return out
