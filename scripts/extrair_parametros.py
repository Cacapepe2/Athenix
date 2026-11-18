"""Extrai, pelo pipeline do Athenix, os parâmetros de penalidade da REN 846 e das normas que a
alteram, e grava o arquivo versionado usado pelo módulo de impacto.

Uso:
  python scripts/extrair_parametros.py                      # regrava athenix/data/penalidades_ren846.json
  python scripts/extrair_parametros.py --dump saida.json    # também despeja todos os dispositivos

Lê os PDFs em tests/fontes_impacto/ (versão oficial, quando existir) ou, na falta, em
.local/fontes_impacto/ (cópia local, fora do repositório; origem a confirmar com a fonte oficial da
ANEEL). Nenhum valor é digitado: percentuais são lidos do trecho citado.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from athenix.config import Settings  # noqa: E402
from athenix.evidence import verify  # noqa: E402
from athenix.normalizacao import espacos, normalizar  # noqa: E402
from athenix.impacto import ALTERA, PARAMETROS, termos  # noqa: E402
from athenix.poc import reader  # noqa: E402
from athenix.saude import _romano  # noqa: E402
from athenix import dou  # noqa: E402
from athenix.structure import extract, from_pieces, independent_source  # noqa: E402
from athenix.temporal import NUMBERS  # noqa: E402

FONTES = ROOT / "tests" / "fontes_impacto"
LOCAL = ROOT / ".local" / "fontes_impacto"


def fonte(nome):
    """Versão oficial em tests/fontes_impacto/; na falta, a cópia local (fora do repositório)."""
    return next((p / nome for p in (FONTES, LOCAL) if (p / nome).exists()), FONTES / nome)


DOCS = {
    "846": (
        FONTES / "atren2019846.pdf",
        "REN 846/2019 (texto compilado oficial até a RN 1.137/2025)",
    ),
    "1137": (ROOT / "tests/norma_poc/ren20251137.pdf", "RN 1.137/2025"),
    "1148": (FONTES / "ren20261148.pdf", "REN 1.148/2026"),
    "1162": (FONTES / "dou/dou_ren20261162.html", "REN 1.162/2026 (DOU)"),
    "1174": (FONTES / "dou/dou_ren20261174.html", "REN 1.174/2026 (DOU)"),
    "9427": (FONTES / "l9427cons.htm", "Lei 9.427/1996 (texto compilado)"),
    "9648": (FONTES / "l9648cons.htm", "Lei 9.648/1998 (texto compilado)"),
    "15269": (FONTES / "l15269.htm", "Lei 15.269/2025"),
}
ORIGENS = {
    "846": "biblioteca da ANEEL (compilado oficial), baixado em 17/11/2026",
    "1137": "ANEEL (texto compilado já no repositório)",
    "1148": "biblioteca da ANEEL, baixado em 17/11/2026",
    "1162": "DOU de 24/06/2026, seção 1, p. 92 (Imprensa Nacional), baixado em 17/11/2026",
    "1174": "DOU de 04/11/2026, seção 1, p. 68 (Imprensa Nacional), baixado em 17/11/2026",
    "9427": "planalto.gov.br (Presidência da República), texto compilado obtido em 17/11/2026",
    "9648": "planalto.gov.br (Presidência da República), texto compilado obtido em 17/11/2026",
    "15269": "planalto.gov.br (Presidência da República), obtido em 17/11/2026",
}
# Nota de redação do texto compilado ("(Redação dada pela Lei nº 15.269, de 2025)").
REDACAO_LEI = re.compile(r"\((?:Redação dada|Incluíd[oa]|Acrescid[oa])\s+pel[ao]\s+([^)]*)\)")
FOOTER = re.compile(r"\s*Leis\.org/aneel - [^\n]*(?:\n\s*\d+/\d+)?|\n\s*\d+/\d+\s*(?=\n|$)")
LABEL = re.compile(
    r"^\s*(?:Art\.?\s*\d+[º°]?(?:-[A-Z])?\.?|§\s*\d+[º°]?|Parágrafo único\.|[IVXLCDM]+\s*-|[a-z]\))\s*"
)
# Ignora faixas ("1% a 5% (um a cinco por cento)"): o extenso descreve a faixa inteira.
PCT = re.compile(r"(?<!%\sa\s)(\d+(?:,\d+)?)\s*%\s*\(([^)]+)\)")
PERCENT = re.compile(r"(\d+(?:,\d+)?)\s*%")
FRACTION = {"décimos": 10, "centésimos": 100, "milésimos": 1000}
ORIGEM = re.compile(
    r"\((?:Reda[çc][ãa]o\s+(?:dada|acrescida)|Incluíd[oa]|Acrescid[oa])\s+pel[ao]\s+([^)]*)\)"
)

# Parâmetro → dispositivo da REN 846 compilada. O valor sai do trecho, nunca deste arquivo.
SPEC = {
    "sujeicao_penalidades": ("5º", "Infrações sujeitam o agente às penalidades do art. 5º"),
    "advertencia": ("6º", "Advertência no lugar da multa (piso zero)"),
    "teto_legal": ("7º", "Teto legal por infração (fora da REN 846)"),
    "sem_repasse": ("7º > Parágrafo único", "Multa não pode ser repassada à tarifa"),
    "base_grupos": ("8º", "Percentuais incidem sobre a base do art. 21"),
    "limite_grupo_I": ("8º > I", "Limite do Grupo I"),
    "limite_grupo_II": ("8º > II", "Limite do Grupo II"),
    "limite_grupo_III": ("8º > III", "Limite do Grupo III"),
    "limite_grupo_IV": ("8º > IV", "Limite do Grupo IV"),
    "limite_grupo_V": ("8º > V", "Limite do Grupo V"),
    "multa_diaria": (
        "15 > § 2º",
        "Multa diária por obrigação de fazer: até 30 dias, até 2% da base",
    ),
    "base_rol": ("21", "Base de cálculo: ROL dos 12 meses anteriores ao AI"),
    "base_rap": ("21 > § 3º", "Base de transmissora fora de operação: RAP"),
    "base_segmento": ("21 > § 6º", "Base do segmento da infração"),
    "ordem_calculo": ("22 > § 1º", "Valor base + agravantes − atenuantes"),
    "pisos_tetos": ("22 > § 2º", "Valor base por metodologia própria; pisos e tetos"),
    "metodologia_afastavel": ("22 > § 6º", "Metodologia do valor base pode ser afastada"),
    "agravante_reincidencia": ("23 > I", "Agravante por reincidência específica"),
    "agravante_tn": ("23 > II", "Agravante por Termo de Notificação não atendido"),
    "agravante_antecedentes": ("23 > III", "Agravante por antecedentes (teto)"),
    "antecedentes_a": ("23 > III > a", "Faixa de antecedentes a)"),
    "antecedentes_b": ("23 > III > b", "Faixa de antecedentes b)"),
    "antecedentes_c": ("23 > III > c", "Faixa de antecedentes c)"),
    "antecedentes_d": ("23 > III > d", "Faixa de antecedentes d)"),
    "antecedentes_e": ("23 > III > e", "Faixa de antecedentes e)"),
    "agravantes_somam": ("23 > § 2º", "Agravantes se somam"),
    "atenuantes_nao_cumulativas": ("24", "Atenuantes não se acumulam"),
    "atenuante_espontanea": ("24 > I", "Atenuante: cessação espontânea antes da fiscalização"),
    "atenuante_tn": ("24 > II", "Atenuante: cessação até o prazo do TN"),
    "atenuante_comprovacao": (
        "24 > Parágrafo único",
        "Atenuantes só contam se comprovadas à Fiscalização antes do AI",
    ),
    "reducao_renuncia": ("38 > § 2º", "Redução por renúncia ao recurso"),
}


def words(text):
    tokens = [t for t in re.split(r"\s+e\s+|\s+", text.lower()) if t]
    return sum(NUMBERS[t] for t in tokens) if all(t in NUMBERS for t in tokens) else None


def spelled(text):
    """Valor de 'cento e vinte e cinco milésimos por cento', 'zero vírgula zero um por cento',
    'dois inteiros e cinco décimos por cento'. Grafia anterior a 2009 ('cinqüenta') vale igual."""
    # Trema (grafia antiga) não muda o número: "cinqüenta" = "cinquenta" (athenix.normalizacao).
    text = normalizar(text, caixa=True)[0]
    text = re.sub(r"\s*por\s+cento\s*$", "", text)
    if m := re.fullmatch(r"(.+?)\s+inteiros?\s+e\s+(.+)", text):
        whole, frac = words(m.group(1)), spelled(m.group(2))
        return None if whole is None or frac is None else whole + frac
    for name, div in FRACTION.items():
        if text.endswith(name):
            n = words(text[: -len(name)])
            return None if n is None else n / div
    if "vírgula" in text:
        whole, frac = [p.strip() for p in text.split("vírgula")]
        zeros = len(re.match(r"(zero\s+)*", frac + " ").group(0).split())
        rest = re.sub(r"^(zero\s+)*", "", frac)
        w = 0 if whole == "zero" else words(whole)
        f = words(rest) if rest else 0
        if w is None or f is None:
            return None
        return w + f / 10 ** (zeros + len(str(f)))
    return words(text)


def mismatches(text):
    out = []
    for m in PCT.finditer(text):
        digits = float(m.group(1).replace(",", "."))
        value = spelled(m.group(2))
        if value is None or abs(value - digits) > 1e-9:
            out.append(
                {"algarismo": m.group(1) + "%", "extenso": m.group(2), "extenso_lido": value}
            )
    return out


def label_path(unit, by_id):
    labels = []
    while unit:
        labels.append(unit["label"])
        unit = by_id.get(unit["parent"])
    return " > ".join(reversed(labels))


def cite(unit, extraction):
    """Cita o dispositivo em pedaços contíguos (o rodapé da página interrompe o texto)."""
    parts = [p.strip() for p in FOOTER.split(unit["text"]) if p and p.strip()]
    cited, anchors, note = [], [], None
    for i, part in enumerate(parts):
        anchor = verify(
            part,
            unit["id"],
            extraction["units"],
            extraction["text_hash"],
            source=extraction["source"],
        )
        if (
            anchor["state"] != "verified"
            and i == 0
            and LABEL.match(part)
            and not unit.get("struck")
        ):
            # pdfium lê o selo "Art. N" fora do lugar: confirma o texto sem o rótulo.
            retry = verify(
                LABEL.sub("", part, count=1),
                unit["id"],
                extraction["units"],
                extraction["text_hash"],
                source=extraction["source"],
            )
            if retry["state"] == "verified":
                anchor, note = retry, "rótulo do dispositivo não confirmado pela 2ª leitura"
        cited.append(espacos(part))
        anchors.append(anchor)
    verified = bool(anchors) and all(a["state"] == "verified" for a in anchors)
    return {
        "trecho": " […] ".join(cited),
        "ancora": "verified" if verified else (anchors[0]["state"] if anchors else "invalid"),
        "motivo": next((a["reason"] for a in anchors if a.get("reason")), None),
        "nota": note,
        "revogado": unit.get("struck"),
    }


COMPILADO = ROOT / "athenix/data/compilado_ren846.json"
EM_PADRAO = (
    "2026-11-17"  # data de referência do catálogo (data do sprint); redação posterior é futura
)


def vigencia_compilada(name):
    """Vigência do ato que altera a REN 846, como a compilação a leu (entra em vigor / publicação)."""
    if not COMPILADO.exists():
        return None
    for alteradora in json.loads(COMPILADO.read_text(encoding="utf-8"))["alteradoras"]:
        if re.sub(r"\D", "", alteradora["ato"]["nome"].split("/")[0]) == name:
            return alteradora["vigencia_padrao"]
    return None


def read(name):
    path, title = DOCS[name]
    content = path.read_bytes()
    if path.suffix == ".html":  # matéria do DOU: só o ato, sem navegação do portal
        texto = dou.ler_html(content)["texto"]
        extraction = from_pieces(
            [texto],
            [],
            [],
            "dou.ler_html",
            Settings(),
            source=independent_source(content, "text/html"),
        )
    elif path.suffix == ".htm":
        extraction = extract(content, "text/html", Settings(), "norm")
    else:
        extraction = reader.read_pdf(path, Settings())["extraction"]
    by_id = {u["id"]: u for u in extraction["units"]}
    units = [u | {"path": label_path(u, by_id)} for u in extraction["units"]]
    effective = [d for d in extraction["dates"] if d["kind"] == "effective"]
    if len({d["date"] for d in effective}) > 1:
        # Datas de vigência distintas (ex.: vigência de outro ato citada): fica a da publicação.
        effective = [d for d in effective if d.get("basis") == "publication"]
    if path.suffix == ".htm":
        # Lei compilada: cada dispositivo vale desde a lei que lhe deu redação; não há data única.
        effective = []
    return {
        "titulo": title,
        "arquivo": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(content).hexdigest(),
        "vigencia": vigencia_compilada(name)
        or (effective[0]["date"] if len({d["date"] for d in effective}) == 1 else None),
        "extraction": extraction,
        "units": units,
    }


def teto_legal(lei):
    """Limite por infração da Lei 9.427/1996 (Art. 3º, X): só a redação não riscada entra."""
    vigentes = [u for u in lei["units"] if u["path"] == "3 > X" and not u.get("struck")]
    if len(vigentes) != 1:
        return {
            "descricao": "Teto legal da multa por infração",
            "dispositivo": "Art. 3, X",
            "trecho": "",
            "ancora": "pending",
            "motivo": f"{len(vigentes)} redações vigentes",
            "nota": None,
            "revogado": None,
            "percentuais": [],
            "fonte": "9427",
        }
    entry = cite(vigentes[0], lei["extraction"])
    redacao = REDACAO_LEI.search(entry["trecho"])
    trecho = entry["trecho"] = espacos(REDACAO_LEI.sub("", entry["trecho"]))
    return {
        "descricao": "Teto legal da multa por infração (% do faturamento dos 12 meses anteriores)",
        "dispositivo": "Art. 3, X da Lei 9.427/1996",
        **entry,
        "redacao_dada_por": redacao.group(1) if redacao else None,
        "percentuais": [float(v.replace(",", ".")) for v in PERCENT.findall(trecho)],
        "fonte": "9427",
    }


def teto_anterior(lei):
    """Redação original do Art. 3º, X da Lei 9.427 (2%), no texto da Lei 9.648/1998 que a incluiu."""
    alvo = [
        u
        for u in lei["units"]
        if espacos(u["text"]).startswith("X - fixar as multas") and not u.get("struck")
    ]
    base = {
        "descricao": "Teto legal anterior por infração (% do faturamento), para infrações antes da nova redação",
        "dispositivo": "Art. 3, X da Lei 9.427/1996, redação incluída pela Lei 9.648/1998",
        "fonte": "9648",
    }
    if len(alvo) != 1:
        return base | {"trecho": "", "ancora": "pending", "motivo": f"{len(alvo)} redações",
                       "nota": None, "revogado": None, "percentuais": []}  # fmt: skip
    entry = cite(alvo[0], lei["extraction"])
    trecho = entry["trecho"] = espacos(REDACAO_LEI.sub("", entry["trecho"]))
    return (
        base
        | entry
        | {"percentuais": [float(v.replace(",", ".")) for v in PERCENT.findall(trecho)]}
    )


def trecho_verificado(unit, padrao, extraction):
    """Cita só a frase que casa com `padrao` dentro da unidade, conferida pela segunda leitura."""
    texto = espacos(unit["text"])
    m = re.search(padrao, texto)
    if not m:
        return None, "invalid"
    anchor = verify(m.group(0), unit["id"], extraction["units"], extraction["text_hash"],
                    source=extraction["source"])  # fmt: skip
    return m, anchor["state"]


def vigencia_teto(lei):
    """Início dos efeitos da redação de 3% (Art. 3º da Lei 15.269/2025 altera o Art. 3º, X da Lei
    9.427). Só vale com o caput e o inciso IV do Art. 24 citados, o Art. 3º fora das exceções (I a
    III) e a data de publicação lida do próprio texto; senão fica pendente e o cálculo mostra os dois
    limites."""
    proprias = [u for u in lei["units"] if u.get("owner") == "self"]
    base = {
        "descricao": "Início dos efeitos da redação de 3% do teto legal",
        "dispositivo": "Art. 24, caput e IV da Lei 15.269/2025",
        "fonte": "15269",
        "percentuais": [],
        "revogado": None,
    }
    caput = next((u for u in proprias if u["path"] == "24"), None)
    inciso_iv = next((u for u in proprias if u["path"] == "24 > IV"), None)
    if not caput or not inciso_iv:
        return base | {"trecho": "", "ancora": "pending", "motivo": "Art. 24 não localizado",
                       "nota": None, "data": None}  # fmt: skip
    excecoes = " ".join(
        espacos(u["text"])
        for u in proprias
        if u["path"].startswith("24 > ") and not u["path"].startswith("24 > IV")
    )
    # "art. 3º-D" (Lei 10.848) é outro dispositivo; só "art. 3º" sozinho tiraria a regra geral.
    art3_excecao = re.search(r"\bart\.\s*3º(?![-\w])", excecoes)
    c, c_estado = trecho_verificado(
        caput, r"Art\. 24\. Esta Lei entra em vigor na data de sua publicação", lei["extraction"]
    )
    iv, iv_estado = trecho_verificado(
        inciso_iv,
        r"IV - na data de sua publicação, quanto aos demais dispositivos\.",
        lei["extraction"],
    )
    pub, pub_estado = trecho_verificado(
        inciso_iv, r"publicado no DOU de (\d{2})\.(\d{2})\.(\d{4})", lei["extraction"]
    )
    ok = all(e == "verified" for e in (c_estado, iv_estado, pub_estado)) and not art3_excecao
    data = f"{pub.group(3)}-{pub.group(2)}-{pub.group(1)}" if pub else None
    motivo = None
    if art3_excecao:
        motivo = "o Art. 3º aparece entre as exceções do Art. 24: conferir"
    elif not ok:
        motivo = "trecho do Art. 24 ou data de publicação não confirmados pela segunda leitura"
    return base | {
        "trecho": " […] ".join(m.group(0) for m in (c, iv) if m),
        "publicacao": pub.group(0) if pub else None,
        "ancora": "verified" if ok else "pending",
        "motivo": motivo,
        "nota": "O Art. 3º da Lei 15.269/2025 (nova redação do Art. 3º, X da Lei 9.427) não está nas "
        "exceções dos incisos I a III do Art. 24: produz efeitos na data da publicação.",
        "data": data if ok else None,
    }


def group_of(units, article):
    caput = next(u for u in units if u["path"] == article)
    match = re.search(r"Grupo\s+([IV]+)\b", caput["text"])
    return match.group(1) if match else None


def sobrepor_alteracoes(infracoes, docs, em, ren_units):
    """Aplica ao catálogo de infrações as redações que a compilação (`compilado_ren846.json`) dá
    aos incisos dos arts. 9º a 13 por atos posteriores ao compilado oficial. Redação com vigência
    depois de `em` não entra: vai para `vigencia_futura`. O literal do ato fica em `trecho_literal`."""
    comp = json.loads(COMPILADO.read_text(encoding="utf-8"))
    futuras = []
    for chave, historico in comp["historico"].items():
        m = re.fullmatch(r"article:(9|10|11|12|13)/clause:([IVXLC]+)", chave)
        ops = [h for h in historico if h["tipo"] in {"substituir", "incluir"}]
        if not m or not ops:
            continue
        artigo = "9º" if m.group(1) == "9" else m.group(1)
        dispositivo = f"Art. {artigo}, {m.group(2)}"
        for h in (h for h in ops if h["vigencia"] > em):
            futuras.append(
                {
                    "dispositivo": dispositivo,
                    "ato": h["redacao_dada_por"],
                    "vigencia_desde": h["vigencia"],
                    "trecho": h["texto"],
                }
            )
        vigentes = [h for h in ops if h["vigencia"] <= em]
        if not vigentes:
            continue
        h = vigentes[-1]
        doc = docs[re.sub(r"\D", "", h["redacao_dada_por"].split("/")[0])]
        unit = next(
            u
            for u in doc["units"]
            if "846" in u["owner"] and u["path"] == f"{artigo} > {m.group(2)}"
        )
        literal = cite(unit, doc["extraction"])
        entrada = {
            "dispositivo": dispositivo,
            "grupo": group_of(ren_units, artigo),
            **literal,
            "trecho": h["texto"],
            "trecho_literal": literal["trecho"],
            "origem": h["redacao_dada_por"],
            "vigencia_desde": h["vigencia"],
            "fonte_da_redacao": {k: h["fonte"].get(k) for k in ("tipo", "arquivo", "sha256")},
            "termos": termos(h["texto"]),
        }
        existente = next(
            (i for i, x in enumerate(infracoes) if x["dispositivo"] == dispositivo), None
        )
        if existente is not None:
            infracoes[existente] = entrada
        else:
            ordem = _romano(m.group(2))
            mesmos = [
                i for i, x in enumerate(infracoes)
                if x["dispositivo"].startswith(f"Art. {artigo},")
                and _romano(x["dispositivo"].rsplit(" ", 1)[1]) < ordem
            ]  # fmt: skip
            infracoes.insert((mesmos[-1] + 1) if mesmos else len(infracoes), entrada)
    return futuras


def build(docs, em=EM_PADRAO):
    ren = docs["846"]
    by_path = {}
    for unit in ren["units"]:
        by_path.setdefault(unit["path"], []).append(unit)
    parametros = {}
    for pid, (path, description) in SPEC.items():
        # Redação revogada nunca entra: entre redações do mesmo dispositivo, fica a não riscada.
        candidates = by_path.get(path, [])
        current = [u for u in candidates if not u.get("struck")]
        unit = (current or candidates)[0]
        entry = cite(unit, ren["extraction"])
        if len(current) != 1:
            entry |= {"ancora": "pending", "motivo": f"{len(current)} redações vigentes: conferir"}
        # A nota "(Redação dada pela ...)" é anotação da compilação, não texto do ato: fica fora do trecho.
        trecho = entry["trecho"] = espacos(ORIGEM.sub("", entry["trecho"]))
        parametros[pid] = {
            "descricao": description,
            "dispositivo": "Art. " + path.replace(" > ", ", "),
            **entry,
            "percentuais": [float(v.replace(",", ".")) for v in PERCENT.findall(trecho)],
            "fonte": "846",
        }
    parametros["teto_legal_lei"] = teto_legal(docs["9427"])
    parametros["teto_legal_anterior"] = teto_anterior(docs["9648"])
    parametros["teto_legal_vigencia"] = vigencia_teto(docs["15269"])
    infracoes = []
    for unit in ren["units"]:
        match = re.fullmatch(r"(9º|10|11|12|13) > ([IVXLC]+)", unit["path"])
        if not match or unit.get("struck"):
            continue
        entry = cite(unit, ren["extraction"])
        origem = ORIGEM.search(entry["trecho"])
        entry["trecho"] = espacos(ORIGEM.sub("", entry["trecho"]))
        entry["origem"] = espacos(origem.group(1)) if origem else "redação original"
        dono = infracoes[-1] if infracoes else None
        # Lista dentro de um inciso ("IV - ... cadastro relativo a:" seguido de "I - unidades
        # consumidoras;"): a numeração recomeça. São itens do inciso, não infrações.
        if (
            dono
            and dono["dispositivo"].startswith(f"Art. {match.group(1)},")
            and dono["trecho"].endswith(":")
            and _romano(match.group(2)) <= _romano(dono["dispositivo"].rsplit(" ", 1)[1])
        ):
            dono.setdefault("itens", []).append(
                {"dispositivo": f"{dono['dispositivo']}, {match.group(2)}", **entry}
            )
            continue
        infracoes.append(
            {
                "dispositivo": f"Art. {match.group(1)}, {match.group(2)}",
                "grupo": group_of(ren["units"], match.group(1)),
                **entry,
                "termos": termos(entry["trecho"]),
            }
        )
    futuras = sobrepor_alteracoes(infracoes, docs, em, ren["units"])
    # Base de cálculo para Sistemas de Armazenamento (REN 1.162, art. 21, § 11): inclusão de 2026.
    sae = next(u for u in docs["1162"]["units"] if "846" in u["owner"] and u["path"] == "21 > § 11")
    parametros["base_armazenamento"] = {
        "descricao": "Base de cálculo da multa para Sistemas de Armazenamento de Energia (valor estimado da receita anual)",
        "dispositivo": "Art. 21, § 11 (incluído pela REN 1.162/2026)",
        **cite(sae, docs["1162"]["extraction"]),
        "percentuais": [],
        "fonte": "1162",
        "vigencia_desde": docs["1162"]["vigencia"],
    }
    # D1: o inciso XXIII do art. 11 tem duas redações em atos diferentes; nenhuma é escolhida.
    leituras = []
    for name in ("1137", "1148"):
        doc = docs[name]
        unit = next(u for u in doc["units"] if u["path"] == "11 > XXIII")
        leituras.append(
            {"ato": doc["titulo"], "vigencia_desde": doc["vigencia"]}
            | cite(unit, doc["extraction"])
        )
    alteracoes = []
    for name in ("1137", "1148", "1162", "1174"):
        doc = docs[name]
        for unit in doc["units"]:
            if re.search(ALTERA, espacos(unit["text"])):
                alteracoes.append(
                    {
                        "ato": doc["titulo"],
                        "vigencia_desde": doc["vigencia"],
                        "dispositivo": "Art. " + unit["path"],
                    }
                    | cite(unit, doc["extraction"])
                )
    alertas = []
    for name, doc in docs.items():
        for unit in doc["units"]:
            if unit.get("struck"):
                continue
            for problem in mismatches(unit["text"]):
                alertas.append(
                    {
                        "tipo": "algarismo_extenso",
                        "ato": doc["titulo"],
                        "dispositivo": "Art. " + unit["path"].replace(" > ", ", "),
                        "detalhe": f'{problem["algarismo"]} escrito como "{problem["extenso"]}"',
                    }
                    | cite(unit, doc["extraction"])
                )
    return {
        "versao": 1,
        "gerado_por": "scripts/extrair_parametros.py (pipeline Athenix, sem valores digitados)",
        "fontes": {
            name: {k: doc[k] for k in ("titulo", "arquivo", "sha256", "vigencia")}
            | {
                "origem": ORIGENS.get(
                    name,
                    "a confirmar com a fonte oficial da ANEEL (cópia local, fora do repositório)",
                )
            }
            for name, doc in docs.items()
        },
        "nao_estimaveis": [
            "Metodologia de cálculo do valor base da multa (Art. 22, §§ 2º e 6º): não está no repositório.",
            "Perda de receita por Parcela Variável (PVI/PVRO) de transmissoras: a REN 905 veio só em 3 páginas, sem os módulos (e a REN 1.162 também a altera).",
            "Efeitos no Fator X da distribuidora (REN 1.148/2026, PRORET 2.5/2.5-A): anexos não fornecidos.",
            "Despacho 1.293/2026 (DOU 23/04/2026): indefere súmula sobre os arts. 36 a 45 da REN 846; não decide multa nem altera parâmetro.",
            "Custo de adequação: depende de dados internos da empresa.",
        ],
        "vigencia_futura": futuras,
        "conflitos_de_compilacao": json.loads(COMPILADO.read_text(encoding="utf-8"))["conflitos"],
        "data_de_referencia": em,
        "parametros": parametros,
        "infracoes": infracoes,
        "duvidas": [
            {
                "id": "D1",
                "dispositivo": "Art. 11, XXIII",
                "texto": "Duas redações para o mesmo inciso em atos diferentes; o compilado mostra só a da RN 1.137. Dúvida para especialista.",
                "leituras": leituras,
            },
            {
                "id": "D5",
                "dispositivo": "Arts. 8º e 23",
                "texto": "A norma não diz se o resultado após agravantes continua limitado ao teto do grupo: calculados os dois cenários. Nos dois, o resultado fica limitado ao teto legal por infração (Lei 9.427/1996, Art. 3º, X).",
            },
            {
                "id": "D6",
                "dispositivo": "Lei 9.427/1996, Art. 3º, X × REN 846, Art. 21",
                "texto": "A lei limita a multa a um percentual do faturamento; a REN 846 calcula sobre a Receita Operacional Líquida (ROL). O cálculo aplica o teto legal sobre a mesma base informada, o que pode subestimar o teto em reais quando o faturamento é maior que a ROL. Dúvida para especialista.",
            },
        ],
        "alteracoes_da_regua": alteracoes,
        "alertas_fonte": alertas,
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--saida", default=str(PARAMETROS))
    parser.add_argument("--dump")
    parser.add_argument("--em", default=EM_PADRAO, help="data de referência (AAAA-MM-DD)")
    args = parser.parse_args()
    docs = {name: read(name) for name in DOCS}
    result = build(docs, args.em)
    Path(args.saida).write_text(
        json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    if args.dump:
        dump = {
            name: [
                {"path": u["path"], "kind": u["kind"], **cite(u, doc["extraction"])}
                for u in doc["units"]
            ]
            for name, doc in docs.items()
        }
        Path(args.dump).write_text(json.dumps(dump, ensure_ascii=False, indent=1), encoding="utf-8")
    pending = [k for k, v in result["parametros"].items() if v["ancora"] != "verified"]
    print(
        f"{len(result['parametros'])} parâmetros ({len(pending)} não verificados: {pending}),",
        f"{len(result['infracoes'])} infrações, {len(result['alteracoes_da_regua'])} alterações,",
        f"{len(result['alertas_fonte'])} alertas da fonte",
    )


if __name__ == "__main__":
    main()
