"""Plano de ação de uma norma para um perfil: resumo, temas, linha do tempo, decisões e o porquê.

Monta a apresentação a partir de impacto.avaliar; não calcula multa nova. Tema = seção da própria
norma (título conferido no texto) ou, nas disposições transitórias e sem seção, o primeiro assunto
nomeado no texto. Títulos e enquadramentos sugeridos pela IA vêm de um cache revisável, aparecem
marcados como interpretação. No modo "só identificados no texto" não entram no cálculo; no cenário
preliminar (decisão do fundador, docs/CONTEXTO.md) entram no valor do tema, sempre marcados como sugeridos.
Só DEVERES da distribuidora entram na contagem principal; faculdades, direitos de terceiros e
competências da ANEEL vão para `outros_dispositivos`. Os ids das obrigações são estáveis (chave do texto).
"""

import json
import re
from pathlib import Path

from . import impacto, proposals
from .db import digest
from .evidence import verify
from .enquadramento import chave as chave_texto
from .enquadramento import infracoes_validas
from .normalizacao import espacos

DATA = Path(__file__).parent / "data"
TEMAS = DATA / "plano_temas.json"
CACHE_IA = DATA / "ia_cache_rn1137.json"
SITUACOES = ("vencida", "90dias", "depois", "recorrente", "evento", "sem_prazo")
NOMES_SITUACAO = {
    "vencida": "Vencidas",
    "90dias": "Próximos 90 dias",
    "depois": "Depois de 90 dias",
    "recorrente": "Recorrentes",
    "evento": "Dependem de um evento",
    "sem_prazo": "Sem prazo no texto",
}
ORDEM_PLANO = (
    "Sem histórico de multas, o valor provável não é estimável. Ordenamos por: 1) o que você marcou "
    "como já atendido vai para o fim; 2) exposição máxima por infração do tema, no porte escolhido "
    "(a maior primeiro; tema sem enquadramento, nem sugerido, fica depois); 3) no empate do valor em reais, o "
    "enquadramento identificado no texto antes do sugerido; 4) mais obrigações vencidas (cada uma é uma infração "
    "possível); 5) prazo vencido antes de a vencer (o mais antigo primeiro), depois recorrente e sem data. "
    "Exposições de infrações diferentes não se somam: vale a maior de cada tema."
)
# Como reduzir a exposição. Trecho, dispositivo e percentual vêm do catálogo (fonte e hash); a
# condição e o efeito em linguagem simples são interpretação da Athenix e aguardam revisão humana.
ROTULO_REDUCAO = "Análise regulatória preliminar · não constitui parecer jurídico"
CAUSA_EXTERNA = "argumento a confirmar com advogado"
# Excludente de responsabilidade só com texto da própria obrigação: caso fortuito, força maior.
EXCLUDENTE = re.compile(r"caso fortuito|força maior|calamidade pública", re.IGNORECASE)
# (parâmetro, nome, condição, efeito, cenário do motor com este atenuante ou None)
REDUCOES = (
    ("advertencia", "Advertência no lugar da multa",
     "Sem reincidência específica e com infração de baixa ofensividade, nas infrações dos arts. 9º a 13.",
     "A penalidade passa a ser advertência, sem multa. O texto não fixa percentual.", None),
    ("atenuante_espontanea", "Cessar e reparar antes da fiscalização",
     "Parar a infração e reparar todo o dano ao serviço e aos consumidores antes de a ANEEL comunicar a fiscalização ou lavrar Termo de Notificação.",
     "Reduz o valor calculado da multa (art. 23) no percentual do texto.", "espontanea"),
    ("atenuante_tn", "Cessar e reparar até o prazo do Termo de Notificação",
     "Parar a infração e reparar todo o dano até o fim do prazo para se manifestar sobre o Termo de Notificação.",
     "Reduz o valor calculado da multa (art. 23) no percentual do texto.", "ate_tn"),
    ("reducao_renuncia", "Renunciar ao recurso e pagar no prazo",
     "Depois da multa aplicada: renunciar expressamente ao recurso em dez dias e pagar no prazo do caput do art. 38, sem parcelar.",
     "Reduz o valor da multa aplicada no percentual do texto. Não é atenuante do art. 24; a combinação com um atenuante não foi calculada.", None),
    ("metodologia_afastavel", "Afastamento da metodologia do valor base",
     "Decisão excepcional e fundamentada da ANEEL quando o valor não atende à razoabilidade e à proporcionalidade.",
     "O texto não fixa percentual.", None),
)  # fmt: skip
REGRAS_REDUCAO = ("atenuantes_nao_cumulativas", "atenuante_comprovacao", "ordem_calculo")
# Degraus de prazo da ordem: evento sem data e sem prazo no texto ficam juntos ("sem data").
DEGRAU = {"vencida": 0, "90dias": 1, "depois": 2, "recorrente": 3, "evento": 4, "sem_prazo": 4}


NOMES_NATUREZA = {
    "faculdade": "Faculdade (pode, não deve)",
    "direito_de_terceiro": "Direito de terceiro (consumidor ou usuário)",
    "competencia_aneel": "Competência da ANEEL",
    "dever_de_outro_agente": "Dever de outro agente (não é da distribuidora)",
    "regra_de_transicao": "Regra de transição: prazo de adequação a outro dispositivo",
    "sem_dever_identificado": "Sem dever identificado: o sujeito não é a distribuidora",
}
# Quem EMITE o ato (a Agência, a Portaria, o Diretor-Geral): é competência da ANEEL, nunca dever da distribuidora.
SUJEITO_EMISSOR = re.compile(
    r"^\W*(?:(?:a|o|as|os)\s+)?(?:portaria|diretor(?:-geral)?|diretoria|superintend\w*|despacho)\b",
    re.I,
)
MOTIVO_SEM_DEVER = "sem dever identificado"
KINDS_SEM_DEVER = {"article", "paragraph", "clause", "item", "letter"}


def sem_dever_identificado(units, resultado):
    """Unidades lidas pela extração que NÃO viraram obrigação nem outro dispositivo classificado (sem marcador
    deôntico e sem a distribuidora agindo de forma explícita). Nada some em silêncio: vão para "Outros dispositivos"
    com o motivo "sem dever identificado". Ficam de fora só o título/anexo/tabela, o texto revogado, o rótulo
    muito curto e a frase que apenas introduz uma enumeração (os filhos carregam o sentido)."""
    ancoradas = {
        a["unit_id"]
        for i in resultado["itens"]
        for a in i["row"].get("anchors", [])
        if a.get("unit_id")
    }
    com_filhos = {u["parent"] for u in units if u.get("parent")}
    vistos, saida = {}, []
    for u in units:
        texto = espacos(u["text"])
        if (
            u["kind"] not in KINDS_SEM_DEVER
            or u["id"] in ancoradas
            or u.get("struck") == "revoked"
            or len(texto) < 25
            or (texto.endswith(":") and u["id"] in com_filhos)
        ):
            continue
        base = "sd-" + digest(texto.encode())[:12]
        n = vistos.get(base, 0)
        vistos[base] = n + 1
        saida.append({
            "id": base if n == 0 else f"{base}-{n}",
            "natureza": "sem_dever_identificado",
            "rotulo": "Sem dever identificado",
            "sujeito": "",
            "unidade": u["id"],
            "trecho": texto,
            "motivo": MOTIVO_SEM_DEVER,
        })  # fmt: skip
    return saida


SUJEITO_ANEEL = re.compile(r"^\W*(?:a\s+)?(?:ag[êe]ncia|aneel)\b", re.I)
# Sujeito que é OUTRO agente do setor (CCEE, Sandbox, comercializador, consumidor...): o dever não é da
# distribuidora. Só vale quando o sujeito COMEÇA por ele; sujeito impessoal ("O plano de contingência")
# continua na contagem da distribuidora.
SUJEITO_OUTRO_AGENTE = re.compile(
    r"^\W*(?:[oa]s?\s+)?(?:ccee\b|c[âa]mara de comercializa|ons\b|operador nacional|sandbox|"
    r"representante da comercializa|(?:agente\s+)?comercializador|gerador|autoprodutor|"
    r"consumidor|interessado|(?:primeira\s+)?reuni[ãa]o|grupo de trabalho|institui[çc][õo]es participantes)",
    re.I,
)
# "A adequação às alterações promovidas por esta Resolução deve ser realizada nos seguintes prazos": o
# prazo é de OUTROS dispositivos (as alterações), não um dever próprio; vira regra de transição.
TRANSICAO = re.compile(r"^\W*(?:Art\.?\s*\d+\w*\.?\s*)?A\s+adequa[çc][ãa]o\b", re.I)
SUJEITO_DISTRIBUIDORA = re.compile(
    r"distribuidor|concession[áa]ri|permission[áa]ri|cession[áa]ri", re.I
)
SUJEITO_TERCEIRO = re.compile(r"\b(?:consumidor(?:es)?|usu[áa]rios?)\b", re.I)


# Complemento agentivo: "deve ser realizada por consumidor", "pela CCEE": quem age é OUTRO agente.
AGENTE_NO_CAPUT = re.compile(
    r"\b(?:por|pel[oa]s?)\s+(?:o\s+|a\s+|os\s+|as\s+)?(?:consumidor(?:es)?|ccee\b|"
    r"c[âa]mara de comercializa|sandbox|comercializador(?:es)?|representante da comercializa)",
    re.I,
)


def ancorar_pendentes(rows, extraction):
    """Obrigação cuja âncora ficou "pending" (o trecho do dispositivo traz tabela ou quebra de linha junto)
    ganha a PRIMEIRA FRASE do próprio dispositivo como citação, se o verificador a confirmar literalmente
    na fonte. O que continuar sem citação verificada sai do plano (nada de obrigação sem dispositivo)."""
    por_id = {u["id"]: u for u in extraction["units"]}
    for row in rows:
        if any(a.get("state") == "verified" for a in row.get("anchors", [])):
            continue
        for ev in row.get("evidence", []):
            unit = por_id.get(ev.get("unit_id"))
            if not unit:
                continue
            frase = next(iter(proposals.sentences(unit["text"])), "")
            if len(frase) < 16:
                continue
            r = verify(frase, unit["id"], extraction["units"], extraction["text_hash"], source=extraction.get("source"))  # fmt: skip
            if r["state"] == "verified":
                row["anchors"] = [{"unit_id": unit["id"], "quote": frase, "state": "verified"}]
                break
    return rows


def validar_bases_dos_prazos(rows, extraction):
    """Trava: prazo contado da publicação ou da vigência da PRÓPRIA norma com data-base anterior à
    publicação é erro de leitura (por exemplo, a data de outro ato lida como vigência). Interrompe."""
    publicacoes = {d["date"] for d in extraction["dates"] if d["kind"] == "publication"}
    if len(publicacoes) != 1:
        return
    publicacao = next(iter(publicacoes))
    for row in rows:
        for d in row.get("deadlines", []):
            if d.get("date") and d.get("event") in ("Publicação da norma", "Vigência da norma") and (d.get("base") or "") < publicacao:  # fmt: skip
                raise ValueError(
                    f"Prazo com data-base {d.get('base')} anterior à publicação da norma ({publicacao}): "
                    f"{d.get('quote', '')[:80]!r}. Corrija a leitura da data (athenix/structure.py)."
                )


def caput_do_dispositivo(unit, by_id):
    """Texto do caput: o ancestral mais próximo que traz marcador deôntico (deve, poderá...)."""
    atual = by_id.get(unit.get("parent")) if unit else None
    while atual:
        if proposals.DUTY.search(atual["text"]):
            return espacos(atual["text"])
        atual = by_id.get(atual.get("parent"))
    return ""


def natureza(row, caput=""):
    """Natureza do dispositivo pelo SUJEITO e pela MODALIDADE da oração principal (modality vem de
    proposals.modality): "dever" da distribuidora; "competencia_aneel" quando o sujeito é a Agência;
    "direito_de_terceiro" quando consumidor ou usuário é o sujeito de uma permissão; "faculdade" para
    qualquer outra permissão; "dever_de_outro_agente" quando o sujeito é outro agente (CCEE, Sandbox,
    comercializador, consumidor). Só "dever" entra na contagem principal."""
    sujeito = row.get("subject", "") or ""
    # Inciso sem sujeito próprio ("não identificado", fragmento sem substantivo) HERDA o sujeito do caput.
    if caput and (
        not sujeito
        or sujeito == "não identificado"
        or not re.search(r"[A-Za-zÀ-ú]{4}", sujeito)  # sem substantivo ("-A.", "a)")
        or re.match(
            r"\s*[a-zà-ú]+(?:ar|er|ir)\b", sujeito
        )  # começa por verbo ("celebrar o Contrato...")
    ):
        sujeito = proposals.subject_of(caput)
    if TRANSICAO.search(sujeito) or TRANSICAO.search(caput[:140]):
        return "regra_de_transicao"
    if SUJEITO_ANEEL.match(sujeito) or SUJEITO_EMISSOR.match(sujeito):
        return "competencia_aneel"
    if row.get("modality") == "permission":
        return "direito_de_terceiro" if SUJEITO_TERCEIRO.search(sujeito) else "faculdade"
    if SUJEITO_OUTRO_AGENTE.match(sujeito):
        return "dever_de_outro_agente"
    # Sujeito impessoal ("A solicitação de redução...") mas o caput diz quem age: "por consumidor livre".
    texto = f"{caput} {row.get('action', '')}"
    distribuidora_age = re.search(
        r"\bpel[oa]s?\s+(?:distribuidor|concession)|\b(?:a|as)\s+distribuidor\w*\s+(?:dever|deve|poder|pode|fica)",
        texto,
        re.I,
    )
    if (
        not SUJEITO_DISTRIBUIDORA.search(sujeito)
        and not distribuidora_age
        and AGENTE_NO_CAPUT.search(texto)
    ):
        return "dever_de_outro_agente"
    # O caput é do emissor ("A Agência poderá instituir..."): o que o detalha não é dever da distribuidora.
    sujeito_do_caput = proposals.subject_of(caput) if caput else ""
    if (
        (SUJEITO_ANEEL.match(sujeito_do_caput) or SUJEITO_EMISSOR.match(sujeito_do_caput))
        and not SUJEITO_DISTRIBUIDORA.search(sujeito)
        and not distribuidora_age
    ):
        return "competencia_aneel"
    # Sem emissor distinto: o dispositivo segue como dever (sujeito impessoal de norma dirigida às distribuidoras).
    # A variante estrita (só com a distribuidora como sujeito, próprio ou do caput) derrubaria ~100 deveres e foi
    # medida à parte: ver .review/PROGRESSO.md. Quem decide é o fundador.
    return "dever"


def exposicao_pct(t, preliminar=True):
    """Exposição máxima por infração do tema, em % da base, e a origem do grupo: "confirmado" (o texto
    da obrigação nomeia a infração) ou "sugerido" (interpretação da IA, só no cenário preliminar).
    Nunca soma infrações: vale a maior. Sem enquadramento nem sugestão: (None, None)."""
    conf = t["faixa"]["maximo_pct"]["com_teto"] if t["faixa"] else None
    sug = (
        t["faixa_preliminar"]["maximo_pct"]["com_teto"]
        if preliminar and t["faixa_preliminar"]
        else None
    )
    if conf is None and sug is None:
        return None, None
    if sug is not None and (conf is None or sug > conf):
        return sug, "sugerido"
    return conf, "confirmado"


def ordenar_temas(temas, diagnostico=None, preliminar=True):
    """Temas na ordem de ORDEM_PLANO. `diagnostico`: {tema: "sim" | "parcial" | "nao"}.
    landing/src/content/plano.ts repete esta regra; o teste de lá compara com `ordem_inicial`."""
    diag = diagnostico or {}

    def chave(t):
        degrau = min((DEGRAU[s] for s in SITUACOES if t["contagem"][s]), default=5)
        data = (t["prazo_mais_urgente"] or {}).get("data") or "9999-12-31"
        valor, origem = exposicao_pct(t, preliminar)
        return (
            diag.get(t["id"]) == "sim",
            -(-1 if valor is None else valor),
            origem == "sugerido",  # no empate de R$, identificado no texto antes de sugerido
            -t["contagem"][
                "vencida"
            ],  # cada obrigação vencida é uma infração possível; R$ nunca soma
            degrau,
            data if degrau < 3 else "",
            -t["n"],
        )

    return sorted(temas, key=chave)


# shortcut: infinitivo pela terminação (-ar/-er/-ir); "Poder" ou "Lugar" também passam. Só ordena e
# filtra títulos; um título que falha continua com o título por regras.
INFINITIVO = re.compile(r"^(?:Não\s+)?[A-ZÀ-Ú][a-zà-úç]+(?:ar|er|ir)\b")


def carregar_temas(path=TEMAS):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def carregar_ia(path=CACHE_IA):
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def secao_por_unidade(units):
    """Rótulo do último título ("Seção 4.7") antes de cada unidade, na ordem do texto."""
    atual, out = None, {}
    for u in sorted(units, key=lambda u: u["start"]):
        if u["kind"] == "heading":
            atual = u["label"]
        out[u["id"]] = atual
    return out


def temas_automaticos(units, base):
    """Temas de uma norma sem arquivo de temas: um por CAPÍTULO (título do próprio texto). `base` é o
    arquivo de temas padrão, de onde vêm só os catálogos de evidência e de "o que guardar". Devolve
    (cfg, {unidade: tema}). Unidades antes do primeiro capítulo e sem capítulo vão para "outros"."""
    cap = re.compile(r"^\W*(CAP[ÍI]TULO\s+[IVXLC]+(?:-[A-Z])?)\s*(.*)$", re.I | re.S)
    temas, por_unidade, atual = [], {}, "outros"
    for u in sorted(units, key=lambda u: u["start"]):
        if u["kind"] == "heading":
            m = cap.match(espacos(u["text"]))
            if m:
                titulo = m.group(2).strip(' "”.') or m.group(1)
                rotulo_cap = "Capítulo " + m.group(1).split(None, 1)[1].upper()
                nome = f"{rotulo_cap}: {titulo.lower().capitalize()}"
                atual = re.sub(r"\W+", "_", m.group(1).lower()).strip("_") + f"_{len(temas)}"
                temas.append({"id": atual, "nome": nome, "secoes": [], "padrao": None})
        por_unidade[u["id"]] = atual
    temas.append(
        {"id": "outros", "nome": "Disposições gerais e outras", "secoes": [], "padrao": None}
    )
    return base | {"temas": temas}, por_unidade


def conferir_secoes(cfg, units):
    """Cada título de seção do arquivo de temas existe no texto logo após o rótulo. Devolve a fonte."""
    ordem = sorted(units, key=lambda u: u["start"])
    fontes = {}
    for tema in cfg["temas"]:
        for s in tema["secoes"]:
            n = next(
                i
                for i, u in enumerate(ordem)
                if u["kind"] == "heading" and u["label"] == s["rotulo"]
            )
            vizinhos = [espacos(u["text"]) for u in ordem[n : n + 2]]
            unidade = next(
                (ordem[n + k]["id"] for k, t in enumerate(vizinhos) if s["titulo"] in t), None
            )
            assert unidade, f"Título da {s['rotulo']} não encontrado no texto: {s['titulo']}"
            fontes.setdefault(tema["id"], []).append(s | {"unidade": unidade})
    return fontes


def tema_de(item, secao, cfg):
    """(tema, motivo): pela seção da norma; senão, pelo primeiro assunto nomeado no texto."""
    for tema in cfg["temas"]:
        if any(s["rotulo"] == secao for s in tema["secoes"]):
            return tema["id"], f"{secao} da norma"
    texto = espacos(item["row"].get("action", ""))
    achados = [
        (m.start(), t["id"], m.group())
        for t in cfg["temas"]
        if t["padrao"] and (m := re.search(t["padrao"], texto))
    ]
    if achados:
        _, tid, termo = min(achados)
        return tid, f'O texto nomeia "{termo}"'
    return "outros", "Sem seção temática nem assunto reconhecido"


def evidencias(pedacos, cfg):
    """Evidências sugeridas, cada uma com o trecho literal que a motivou (dentro de um só pedaço
    de texto da obrigação, para o trecho continuar literal)."""
    out = []
    for e in cfg["evidencias"]:
        for texto in pedacos:
            if m := re.search(e["padrao"], texto):
                ini, fim = max(0, m.start() - 60), min(len(texto), m.end() + 60)
                out.append({"id": e["id"], "trecho": texto[ini:fim].strip()})
                break
    return out


def situacao(item):
    nivel = item["urgencia"]["nivel"]
    if nivel < 3:
        return SITUACOES[nivel]
    estados = {d.get("state") for d in item["row"].get("deadlines", [])}
    if "recurring" in estados:
        return "recorrente"
    if "awaiting_event" in estados or "conditional" in estados:
        return "evento"
    return "sem_prazo"


def _titulo(item, ia, units_texto):
    """Título do cache da IA só se passou nos filtros: sem alerta, verbo no início, até 85
    caracteres e citação literal presente no texto. Senão, o título por regras."""
    regra = impacto.titulo_obrigacao(item["row"].get("action", ""))
    sug = (ia or {}).get("titulos", {}).get(item["chave"])
    if (
        sug
        and not sug.get("alerta")
        and len(sug["titulo"]) <= 85
        and INFINITIVO.match(sug["titulo"])
        and espacos(sug["citacao"]) in units_texto
    ):
        return sug["titulo"], "ia"
    return regra, "regra"


FRAGMENTO = re.compile(
    r"^(?:Ser|Estar|Ocorrer|Até|Em\s+até|Em\s+caso|No\s+caso|Caso|\d)\b|^[a-zà-ú]"
)


def titulo_com_contexto(completo, row, caput):
    """Inciso ou parágrafo sem sujeito próprio ganha o sujeito (e o "deve") do caput:
    "Ser realizada até o maior prazo..." vira "A aplicação do benefício tarifário deve ser realizada até...";
    "Até doze meses da publicação..." vira "<caput sem rótulo>: até doze meses...". Título de IA não muda."""
    if not FRAGMENTO.match(completo):
        return completo
    sujeito = (row.get("subject") or "").strip()
    if not sujeito or sujeito == "não identificado" or not re.search(r"[A-Za-zÀ-ú]{4}", sujeito):
        sujeito = proposals.subject_of(caput) if caput else ""
    if not sujeito or sujeito == "não identificado":
        # Sujeito longo demais para o extrator ("Para unidades..., as condições comerciais devem ser..."):
        # usa o último sintagma "o/a/os/as ..." antes do verbo modal do próprio texto.
        acao = row.get("action", "")
        modal = re.search(r"\b(?:deve|devem|deverá|deverão)\b", acao, re.I)
        antes = acao[: modal.start()] if modal else ""
        inicios = list(re.finditer(r",\s*((?:o|a|os|as)\s+)", antes, re.I))
        sujeito = espacos(antes[inicios[0].start(1) :]) if inicios and len(antes) - inicios[0].start(1) <= 200 else ""  # fmt: skip
    if re.match(r"(?:Ser|Estar|Ocorrer)\b", completo) and sujeito and sujeito != "não identificado":
        plural = re.search(r"\b(?:devem|deverão)\b", row.get("action", ""), re.I)
        return f"{sujeito[:1].upper()}{sujeito[1:]} {'devem' if plural else 'deve'} {completo[:1].lower()}{completo[1:]}"
    base = proposals.LEADING_LABEL.sub("", caput).strip().rstrip(":").strip() if caput else ""
    if base and len(base) <= 200:
        return f"{base[:1].upper()}{base[1:]}: {completo[:1].lower()}{completo[1:]}"
    return completo


def _titulo_completo(item, titulo, origem):
    """Título sem corte (o título curto termina em "…" quando passa de 88 caracteres)."""
    if origem == "ia":
        return titulo
    return impacto.titulo_obrigacao(item["row"].get("action", ""), limite=None)


def _ia_enquadramento(item, ia, validas):
    s = (ia or {}).get("enquadramentos", {}).get(item["chave"])
    if not s or s["dispositivo"] not in validas:
        return None
    return {k: s.get(k) for k in ("dispositivo", "grupo", "justificativa", "duvida")}


def _faixa(item, base, com_atenuante=None):
    """`com_atenuante`: {atenuante: % da base}, o valor do motor com valor base no teto do grupo
    (pior caso, sem agravantes) e o atenuante aplicado (REN 846, art. 24)."""
    return _faixa_de(item["multa"], base, com_atenuante)


def _faixa_de(m, base, com_atenuante=None):
    com_atenuante = com_atenuante or {}
    out = {
        "grupos": m["grupos"],
        "teto_grupo_pct": m["teto_pct"],
        "maximo_pct": m["maximo"],
        "teto_legal_pct": m["teto_legal_pct"],
        "teto_legal_lei_pct": (m["teto_legal"] or {}).get("pct_lei"),
        "teto_legal_subestimado": (m["teto_legal"] or {}).get("subestimado"),
        "com_atenuante_pct": com_atenuante,
    }
    if base is not None:
        out["maximo_reais"] = {k: v / 100 * base for k, v in m["maximo"].items()}
        out["com_atenuante_reais"] = {k: v / 100 * base for k, v in com_atenuante.items()}
    return out


def _faixa_preliminar(params, row, p, grupo):
    """Faixa do cenário preliminar: o grupo SUGERIDO pela IA (aguarda confirmação) passado pelo mesmo
    motor (impacto.multa), com os atenuantes do art. 24 calculados como nos enquadramentos do texto.
    Fora do cálculo do que o texto identifica; só o cenário preliminar (demo e relatório-piloto) a usa, marcada."""
    m = impacto.multa(params, row, p, [grupo], False)
    if not m.get("estimavel"):
        return None
    com = {}
    for nome in impacto.ATENUANTES:
        if nome == "nenhuma":
            continue
        mm = impacto.multa(
            params, row, p | {"atenuante": nome, "fracao_valor_base": 100.0}, [grupo], False
        )
        if mm.get("provavel"):
            com[nome] = mm["provavel"]["com_teto"]
    return _faixa_de(m, p["base"], com)


def _com_atenuante(cenarios, row_id):
    """% da base em cada cenário do motor (fração do valor base 100%, atenuante aplicado)."""
    out = {}
    for nome, itens in cenarios.items():
        m = (itens.get(row_id) or {}).get("multa") or {}
        if m.get("provavel"):
            out[nome] = m["provavel"]["com_teto"]
    return out


def _ids_por_padrao(pedacos, lista):
    return [e["id"] for e in lista if any(re.search(e["padrao"], t) for t in pedacos)]


def escala_de_gravidade(params):
    """Teto de multa de cada grupo (REN 846, art. 8º) e o teto legal (Lei 9.427/1996, art. 3º, X), cada um
    com dispositivo, trecho literal, fonte e SHA-256. O nome de negócio de cada grupo (leve, média...)
    fica no site (landing/src/content/gravidade.ts), num único lugar."""
    saida = {}
    for pid in [f"limite_grupo_{g}" for g in impacto.GRUPOS] + ["teto_legal_lei"]:
        par = impacto.parametro(params, pid)
        if not par:
            continue
        fonte = params["fontes"][par["fonte"]]
        saida[pid] = {
            "dispositivo": par["dispositivo"],
            "trecho": espacos(par["trecho"]),
            "percentual": par["percentuais"][0] if par["percentuais"] else None,
            "fonte": fonte["titulo"],
            "sha256": fonte["sha256"],
        }
    return saida


def reducao(params):
    """Bloco geral de "Como reduzir a exposição": regras e medidas da REN 846 com citação."""

    def citar(pid):
        par = impacto.parametro(params, pid)
        if not par:
            return None
        fonte = params["fontes"][par["fonte"]]
        return {
            "parametro": pid,
            "dispositivo": par["dispositivo"],
            "trecho": par["trecho"],
            "percentual": par["percentuais"][0] if par["percentuais"] else None,
            "fonte": fonte["titulo"],
            "sha256": fonte["sha256"],
        }

    medidas = []
    for pid, nome, condicao, efeito, cenario in REDUCOES:
        c = citar(pid)
        if c:
            medidas.append(c | {"nome": nome, "condicao": condicao, "efeito": efeito, "cenario": cenario})  # fmt: skip
    return {
        "rotulo": ROTULO_REDUCAO,
        "regras": [c for c in map(citar, REGRAS_REDUCAO) if c],
        "medidas": medidas,
        "causa_externa": CAUSA_EXTERNA,
    }


def montar(
    resultado,
    units,
    params,
    p,
    cfg,
    ia=None,
    chave=None,
    cenarios=None,
    tema_por_unidade=None,
    recomendacoes=None,
    titulos_curtos=None,
    evite=None,
):
    """Plano para o perfil `p`. `chave(row)` identifica a obrigação no cache da IA. `cenarios`:
    {atenuante: resultado de impacto.avaliar com esse atenuante e fração do valor base 100%}."""
    chave = chave or chave_texto
    cenarios = {
        nome: {i["row"]["id"]: i for i in r["itens"]} for nome, r in (cenarios or {}).items()
    }
    by_id = {u["id"]: u for u in units}
    secoes = secao_por_unidade(units)
    fontes_temas = conferir_secoes(cfg, units)
    units_texto = espacos(" ".join(u["text"] for u in units))
    validas = infracoes_validas(params)
    fila = {id(i): n for n, i in enumerate(resultado["ranking"], start=1)}
    verificar = {id(i) for i in resultado["verificar"]}
    obrigacoes, infracoes, outros = [], {}, []
    sem_dever_linhas = []

    for item in resultado["itens"]:
        if not item["aplicavel"]:
            continue
        row = item["row"]
        item["chave"] = chave(row)
        ancora = next((a for a in row.get("anchors", []) if a.get("state") == "verified"), None)
        unidade = by_id.get(ancora["unit_id"]) if ancora else None
        nat = natureza(row, caput_do_dispositivo(unidade, by_id))
        if nat == "sem_dever_identificado":
            sem_dever_linhas.append({
                "id": item["chave"],
                "natureza": nat,
                "rotulo": NOMES_NATUREZA[nat],
                "sujeito": espacos(row.get("subject", "")),
                "unidade": unidade["id"] if unidade else None,
                "trecho": espacos(ancora["quote"]) if ancora else None,
                "motivo": MOTIVO_SEM_DEVER + ": o sujeito não é a distribuidora (nem pelo caput)",
            })  # fmt: skip
            continue
        if nat != "dever":
            outros.append({
                "id": item["chave"],
                "natureza": nat,
                "rotulo": NOMES_NATUREZA[nat],
                "sujeito": espacos(row.get("subject", "")),
                "unidade": unidade["id"] if unidade else None,
                "trecho": espacos(ancora["quote"]) if ancora else None,
                "motivo": "Não é dever da distribuidora: não entra na contagem nem no cálculo de multa.",
            })  # fmt: skip
            continue
        if tema_por_unidade is not None:  # norma sem arquivo de temas: tema = capítulo
            tema = tema_por_unidade.get(ancora["unit_id"], "outros") if ancora else "outros"
            motivo_tema = "Capítulo da norma" if tema != "outros" else "Sem capítulo identificado"
        else:
            tema, motivo_tema = tema_de(
                item, secoes.get(ancora["unit_id"]) if ancora else None, cfg
            )
        titulo, origem_titulo = _titulo(item, ia, units_texto)
        completo = _titulo_completo(item, titulo, origem_titulo)
        if origem_titulo != "ia":
            contextual = titulo_com_contexto(completo, row, caput_do_dispositivo(unidade, by_id))
            if contextual != completo:
                completo = contextual
                titulo = (
                    contextual if len(contextual) <= 88 else contextual[:85].rsplit(" ", 1)[0] + "…"
                )
        pedacos = [espacos(row.get("action", ""))] + [
            espacos(e.get("quote", "")) for e in row.get("evidence", [])
        ]
        calculo = (
            "fila" if id(item) in fila else "verificar" if id(item) in verificar else "sem_multa"
        )
        regra = [
            {"dispositivo": e["dispositivo"], "grupo": e["grupo"]}
            for e in item["enquadramentos"]
            if calculo == "fila"
        ]
        sugestao = _ia_enquadramento(item, ia, validas) if calculo == "verificar" else None
        for d in [e["dispositivo"] for e in regra] + (
            [sugestao["dispositivo"]] if sugestao else []
        ):
            infracoes.setdefault(d, {
                "grupo": validas[d]["grupo"],
                "trecho": validas[d]["trecho"],
                "origem_da_redacao": validas[d].get("origem"),
            })  # fmt: skip
        urg = item["urgencia"]
        obrigacoes.append({
            "id": item["chave"],  # estável entre execuções (o id do banco é aleatório)
            "titulo": titulo,
            "titulo_origem": origem_titulo,
            "titulo_completo": completo,
            # Rótulo de até 5 palavras (IA, linguagem simples) para os blocos; None: a tela encurta o título.
            "titulo_curto": (titulos_curtos or {}).get(item["chave"]),
            # "Evite" sugerido pela IA (valida: cita trecho do dispositivo); None: a tela não mostra a linha.
            "evite": (evite or {}).get(item["chave"]),
            # Ações específicas sugeridas pela IA para ESTE dispositivo (validadas: citam o próprio texto).
            "recomendacoes": (recomendacoes or {}).get(item["chave"], []),
            "contexto": caput_do_dispositivo(unidade, by_id)[:300],  # caput do inciso/parágrafo, para o leitor e a IA
            "tema": tema,
            "motivo_tema": motivo_tema,
            "unidade": unidade["id"] if unidade else None,
            "trecho": espacos(ancora["quote"]) if ancora else None,
            "situacao": situacao(item),
            "prazo": {
                "data": urg["data"],
                "texto": urg["principal"],
                "dias": urg["dias"],
                "provisorio": "provisório" in urg["detalhe"],
                # Prazo CONDICIONAL ("o maior entre 12 meses da publicação e o prazo informado"): sem data única.
                "condicional": any(
                    d.get("state") == "conditional" for d in row.get("deadlines", [])
                ),
                # Data de referência da contagem (marco do prazo), para a tela dizer de onde ele vem.
                "base": next(
                    (d.get("base") for d in row.get("deadlines", []) if d.get("date") == urg["data"]),
                    None,
                ),
            },
            "calculo": calculo,
            "posicao_fila": fila.get(id(item)),
            "enquadramento": regra,
            "ia": sugestao,
            "grupo": max((e["grupo"] for e in regra), key=impacto.GRUPOS.index, default=None),
            "faixa_preliminar": _faixa_preliminar(params, row, p, sugestao["grupo"]) if sugestao else None,
            "faixa": _faixa(item, p["base"], _com_atenuante(cenarios, row["id"])) if calculo == "fila" else None,
            "premissas": [pr["texto"] for pr in item["multa"]["premissas"]] if calculo == "fila" else [],
            "motivo_sem_calculo": None
            if calculo != "sem_multa"
            else (item["multa"] or {}).get("motivo") or "Sem consequência financeira estimável.",
            "evidencias": evidencias(pedacos, cfg),
            "guardar": _ids_por_padrao(pedacos, cfg.get("guardar", [])),
            "excludente": next((t for t in pedacos if EXCLUDENTE.search(t)), None),
        })  # fmt: skip

    ordem_sit = {s: n for n, s in enumerate(SITUACOES)}
    obrigacoes.sort(
        key=lambda o: (
            ordem_sit[o["situacao"]],
            o["prazo"]["data"] or "9999",
            -impacto.GRUPOS.index(o["grupo"]) if o["grupo"] else 1,
            o["posicao_fila"] or 999,
        )
    )
    sem_dever = sem_dever_linhas + sem_dever_identificado(units, resultado)
    ids = [o["id"] for o in obrigacoes] + [o["id"] for o in outros] + [o["id"] for o in sem_dever]
    assert len(set(ids)) == len(ids), "chave de obrigação repetida: o id estável não é único"
    temas = [_tema(t, obrigacoes, fontes_temas.get(t["id"], []), cfg) for t in cfg["temas"]]
    temas = ordenar_temas([t for t in temas if t["n"]])
    return {
        "resumo": _resumo(obrigacoes, resultado, temas, outros),
        "decisoes": decisoes(obrigacoes, temas),
        "temas": temas,
        "ordem_inicial": [t["id"] for t in temas],
        "obrigacoes": obrigacoes,
        "outros_dispositivos": outros,
        "sem_dever_identificado": sem_dever,
        "infracoes": infracoes,
        "linha_do_tempo": {
            s: [o["id"] for o in obrigacoes if o["situacao"] == s] for s in SITUACOES
        },
        "nomes_situacao": NOMES_SITUACAO,
        "regra_ordem": ORDEM_PLANO,
        "evidencias": {e["id"]: e["texto"] for e in cfg["evidencias"]},
        "reducao": reducao(params),
        "escala_de_gravidade": escala_de_gravidade(params),
        "guardar": {e["id"]: e["texto"] for e in cfg.get("guardar", [])},
    }


def _tema(cfg_tema, obrigacoes, fontes, cfg):
    obs = [o for o in obrigacoes if o["tema"] == cfg_tema["id"]]
    contagem = {s: sum(o["situacao"] == s for o in obs) for s in SITUACOES}
    com_data = [o for o in obs if o["prazo"]["data"]]
    urgente = min(com_data, key=lambda o: o["prazo"]["data"]) if com_data else None
    na_fila = [o for o in obs if o["calculo"] == "fila"]
    grupos = sorted({o["grupo"] for o in na_fila}, key=impacto.GRUPOS.index)
    faixa = max(
        (o["faixa"] for o in na_fila), key=lambda f: f["maximo_pct"]["com_teto"], default=None
    )
    infr = sorted({e["dispositivo"] for o in na_fila for e in o["enquadramento"]})
    sugeridas = [o for o in obs if o["faixa_preliminar"]]
    faixa_prelim = max(
        (o["faixa_preliminar"] for o in sugeridas),
        key=lambda f: f["maximo_pct"]["com_teto"],
        default=None,
    )
    ia = [o["ia"]["dispositivo"] for o in obs if o["ia"]]
    ia_top = max(set(ia), key=lambda d: (ia.count(d), d)) if ia else None
    ev = {}
    for o in obs:
        for e in o["evidencias"]:
            ev.setdefault(e["id"], {"id": e["id"], "n": 0, "exemplo": None})
            ev[e["id"]]["n"] += 1
            ev[e["id"]]["exemplo"] = ev[e["id"]]["exemplo"] or {"obrigacao": o["id"], "trecho": e["trecho"]}  # fmt: skip
    guardar = {}
    for o in obs:
        for g in o["guardar"]:
            guardar[g] = guardar.get(g, 0) + 1
    excludentes = [
        {"obrigacao": o["id"], "trecho": o["excludente"]} for o in obs if o["excludente"]
    ]
    principais = sorted(
        obs,
        key=lambda o: (
            not INFINITIVO.match(o["titulo"]),
            SITUACOES.index(o["situacao"]),
            o["calculo"] != "fila",
            o["posicao_fila"] or 999,
        ),
    )[:4]
    return {
        "id": cfg_tema["id"],
        "nome": cfg_tema["nome"],
        "fontes": fontes,
        "n": len(obs),
        "contagem": contagem,
        "prazo_mais_urgente": {
            "obrigacao": urgente["id"],
            **urgente["prazo"],
            "situacao": urgente["situacao"],
        }
        if urgente
        else None,  # fmt: skip
        "na_fila": len(na_fila),
        "a_confirmar": sum(o["calculo"] == "verificar" for o in obs),
        "grupos": grupos,
        "grupo_mais_grave": grupos[-1] if grupos else None,
        "infracoes": infr,
        "faixa": faixa,
        "faixa_preliminar": faixa_prelim,
        "grupos_sugeridos": sorted({o["ia"]["grupo"] for o in sugeridas}, key=impacto.GRUPOS.index),
        "ia": {"dispositivo": ia_top, "n": ia.count(ia_top), "de": len(ia)} if ia_top else None,
        "evidencias": sorted(ev.values(), key=lambda e: -e["n"])[:3],
        "guardar": [{"id": g, "n": n} for g, n in sorted(guardar.items(), key=lambda x: -x[1])[:3]],
        "excludentes": excludentes,
        "causa_externa": None if excludentes else CAUSA_EXTERNA,
        "principais": [o["id"] for o in principais],
        "obrigacoes": [o["id"] for o in obs],
    }


def _resumo(obrigacoes, resultado, temas, outros=()):
    grupos = [o["grupo"] for o in obrigacoes if o["grupo"]]
    return {
        "identificadas": len([i for i in resultado["itens"]]),
        "aplicaveis": len(obrigacoes),  # só deveres da distribuidora
        "outros_dispositivos": len(outros),
        "fora_do_perfil": sum(not i["aplicavel"] for i in resultado["itens"]),
        "por_situacao": {s: sum(o["situacao"] == s for o in obrigacoes) for s in SITUACOES},
        "na_fila": sum(o["calculo"] == "fila" for o in obrigacoes),
        "a_confirmar": sum(o["calculo"] == "verificar" for o in obrigacoes),
        "sem_multa": sum(o["calculo"] == "sem_multa" for o in obrigacoes),
        "grupo_mais_grave": max(grupos, key=impacto.GRUPOS.index) if grupos else None,
        "temas": len(temas),
    }


def decisoes(obrigacoes, temas, preliminar=True):
    """As 3 primeiras decisões da semana: os 3 primeiros temas da ordem (já com a exposição por
    infração), cada um com R$ em risco (em % da base aqui; a demo converte no porte escolhido) e a
    situação do prazo. Mais um item secundário: confirmar enquadramentos libera o cálculo de N temas."""
    top = [
        {
            "tema": t["id"],
            "nome": t["nome"],
            "exposicao_pct": exposicao_pct(t, preliminar)[0],
            "origem": exposicao_pct(t, preliminar)[1],
            "prazo": t["prazo_mais_urgente"],
            "obrigacoes_vencidas": t["contagem"]["vencida"],
        }
        for t in temas[:3]
    ]
    a_confirmar = [o for o in obrigacoes if o["calculo"] == "verificar"]
    return {
        "principais": top,
        "confirmar": {
            "obrigacoes": len(a_confirmar),
            "temas_sem_calculo_confirmado": sum(
                1 for t in temas if not t["faixa"] and t["a_confirmar"]
            ),
        },
    }
