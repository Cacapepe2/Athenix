"""Plano de ação de uma norma para um perfil: resumo, temas, linha do tempo, decisões e o porquê.

Monta a apresentação a partir de impacto.avaliar; não calcula multa nova. Tema = seção da própria
norma (título conferido no texto) ou, nas disposições transitórias e sem seção, o primeiro assunto
nomeado no texto. Títulos e enquadramentos sugeridos pela IA vêm de um cache revisável, aparecem
marcados como interpretação e nunca entram no cálculo.
"""

import json
import re
from datetime import date
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
    "Sem histórico de multas, o valor provável não é estimável e não entra na ordem. Ordenamos por: "
    "1) o que você marcou como já atendido vai para o fim; 2) prazo vencido primeiro (o mais antigo "
    "antes), depois a vencer, recorrente e sem data; 3) grupo de infração mais grave identificado "
    "(na REN 846, o Grupo V é o mais grave; enquadramento a confirmar vem depois); 4) a lacuna "
    "informada (não temos antes de parcial); 5) número de obrigações."
)
# Degraus de prazo da ordem: evento sem data e sem prazo no texto ficam juntos ("sem data").
DEGRAU = {"vencida": 0, "90dias": 1, "depois": 2, "recorrente": 3, "evento": 4, "sem_prazo": 4}
LACUNA = {"nao": 0, "parcial": 1}


def ordenar_temas(temas, diagnostico=None):
    """Temas na ordem de ORDEM_PLANO. `diagnostico`: {tema: "sim" | "parcial" | "nao"}.
    landing/src/content/plano.ts repete esta regra; o teste de lá compara com `ordem_inicial`."""
    diag = diagnostico or {}

    def chave(t):
        degrau = min((DEGRAU[s] for s in SITUACOES if t["contagem"][s]), default=5)
        data = (t["prazo_mais_urgente"] or {}).get("data") or "9999-12-31"
        grav = impacto.GRUPOS.index(t["grupo_mais_grave"]) if t["grupo_mais_grave"] else -1
        d = diag.get(t["id"])
        return (d == "sim", degrau, data if degrau < 3 else "", -grav, LACUNA.get(d, 2), -t["n"])

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


def _faixa(item, base):
    m = item["multa"]
    out = {
        "grupos": m["grupos"],
        "teto_grupo_pct": m["teto_pct"],
        "maximo_pct": m["maximo"],
        "teto_legal_pct": m["teto_legal_pct"],
        "teto_legal_subestimado": (m["teto_legal"] or {}).get("subestimado"),
    }
    if base is not None:
        out["maximo_reais"] = {k: v / 100 * base for k, v in m["maximo"].items()}
    return out


def montar(resultado, units, params, p, cfg, ia=None, chave=None):
    """Plano para o perfil `p`. `chave(row)` identifica a obrigação no cache da IA."""
    chave = chave or chave_texto
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
            "faixa": _faixa(item, p["base"]) if calculo == "fila" else None,
            "premissas": [pr["texto"] for pr in item["multa"]["premissas"]] if calculo == "fila" else [],
            "motivo_sem_calculo": None
            if calculo != "sem_multa"
            else (item["multa"] or {}).get("motivo") or "Sem consequência financeira estimável.",
            "evidencias": evidencias(pedacos, cfg),
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
    ia = [o["ia"]["dispositivo"] for o in obs if o["ia"]]
    ia_top = max(set(ia), key=lambda d: (ia.count(d), d)) if ia else None
    ev = {}
    for o in obs:
        for e in o["evidencias"]:
            ev.setdefault(e["id"], {"id": e["id"], "n": 0, "exemplo": None})
            ev[e["id"]]["n"] += 1
            ev[e["id"]]["exemplo"] = ev[e["id"]]["exemplo"] or {"obrigacao": o["id"], "trecho": e["trecho"]}  # fmt: skip
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
        "ia": {"dispositivo": ia_top, "n": ia.count(ia_top), "de": len(ia)} if ia_top else None,
        "evidencias": sorted(ev.values(), key=lambda e: -e["n"])[:3],
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


def _data_br(iso):
    return date.fromisoformat(iso).strftime("%d/%m/%Y")


def decisoes(obrigacoes, temas):
    """Até três decisões para a semana, derivadas dos prazos e do enquadramento pendente."""
    nomes = {t["id"]: t["nome"] for t in temas}
    vencidas = [o for o in obrigacoes if o["situacao"] == "vencida"]
    proximas = [o for o in obrigacoes if o["situacao"] == "90dias"]
    out = []
    for grupo in (vencidas, proximas):
        por_data = {}
        for o in grupo:
            por_data.setdefault(o["prazo"]["data"], []).append(o)
        for data, obs in sorted(por_data.items()):
            if len(out) == 2:
                break
            verbo = "venceu" if grupo is vencidas else "vence"
            n = len(obs)
            titulo = (
                f"Comprovar ou regularizar a entrega cujo prazo {verbo} em {_data_br(data)}"
                if n == 1
                else f"Comprovar ou regularizar as {n} entregas cujo prazo {verbo} em {_data_br(data)}"
            )
            out.append({
                "titulo": titulo,
                "itens": [o["titulo"] for o in obs],
                "obrigacoes": [o["id"] for o in obs],
                "temas": sorted({nomes[o["tema"]] for o in obs}),
                "motivo": "Data calculada pelo motor temporal a partir da publicação da norma; continua provisória até uma pessoa confirmar a contagem.",
            })  # fmt: skip
    a_confirmar = [o for o in obrigacoes if o["calculo"] == "verificar"]
    if a_confirmar and len(out) < 3:
        temas_sem = [t["nome"] for t in temas if t["a_confirmar"] and not t["na_fila"]]
        out.append({
            "titulo": f"Designar quem confirma o enquadramento de {len(a_confirmar)} obrigações na REN 846",
            "itens": [f"Sem essa confirmação, a exposição destes temas não é calculada: {', '.join(temas_sem)}."] if temas_sem else [],
            "obrigacoes": [],
            "temas": temas_sem,
            "motivo": "Sugestões de enquadramento (por regra ou pela IA) só entram no cálculo depois de confirmadas por uma pessoa.",
        })  # fmt: skip
    return out[:3]
