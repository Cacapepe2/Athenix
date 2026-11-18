"""Plano de ação de uma norma para um perfil: resumo, temas, linha do tempo, decisões e o porquê.

Monta a apresentação a partir de impacto.avaliar; não calcula multa nova. Tema = seção da própria
norma (título conferido no texto) ou, nas disposições transitórias e sem seção, o primeiro assunto
nomeado no texto. Títulos e enquadramentos sugeridos pela IA vêm de um cache revisável, aparecem
marcados como interpretação e nunca entram no cálculo.
"""

import json
import re
from pathlib import Path

from . import impacto
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
    "(a maior primeiro; tema sem enquadramento, nem sugerido, fica depois); 3) prazo vencido antes de "
    "a vencer (o mais antigo primeiro), depois recorrente e sem data; 4) número de obrigações. "
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
        valor = exposicao_pct(t, preliminar)[0]
        return (
            diag.get(t["id"]) == "sim",
            -(-1 if valor is None else valor),
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
    if "awaiting_event" in estados:
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
    Fora do cálculo confirmado; só o cenário preliminar (demo e relatório-piloto) a usa, marcada."""
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


def montar(resultado, units, params, p, cfg, ia=None, chave=None, cenarios=None):
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
    obrigacoes, infracoes = [], {}

    for item in resultado["itens"]:
        if not item["aplicavel"]:
            continue
        row = item["row"]
        item["chave"] = chave(row)
        ancora = next((a for a in row.get("anchors", []) if a.get("state") == "verified"), None)
        unidade = by_id.get(ancora["unit_id"]) if ancora else None
        tema, motivo_tema = tema_de(item, secoes.get(ancora["unit_id"]) if ancora else None, cfg)
        titulo, origem_titulo = _titulo(item, ia, units_texto)
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
            infracoes.setdefault(d, {"grupo": validas[d]["grupo"], "trecho": validas[d]["trecho"]})
        urg = item["urgencia"]
        obrigacoes.append({
            "id": row["id"],
            "titulo": titulo,
            "titulo_origem": origem_titulo,
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
    temas = [_tema(t, obrigacoes, fontes_temas.get(t["id"], []), cfg) for t in cfg["temas"]]
    temas = ordenar_temas([t for t in temas if t["n"]])
    return {
        "resumo": _resumo(obrigacoes, resultado, temas),
        "decisoes": decisoes(obrigacoes, temas),
        "temas": temas,
        "ordem_inicial": [t["id"] for t in temas],
        "obrigacoes": obrigacoes,
        "infracoes": infracoes,
        "linha_do_tempo": {
            s: [o["id"] for o in obrigacoes if o["situacao"] == s] for s in SITUACOES
        },
        "nomes_situacao": NOMES_SITUACAO,
        "regra_ordem": ORDEM_PLANO,
        "evidencias": {e["id"]: e["texto"] for e in cfg["evidencias"]},
        "reducao": reducao(params),
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


def _resumo(obrigacoes, resultado, temas):
    grupos = [o["grupo"] for o in obrigacoes if o["grupo"]]
    return {
        "identificadas": len([i for i in resultado["itens"]]),
        "aplicaveis": len(obrigacoes),
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
