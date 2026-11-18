"""Análise regulatória preliminar de cada obrigação prioritária de um tema (demo e relatório-piloto).

Junta, para a obrigação: tipo (athenix/tipos.py), manual do tipo (ideias de cumprimento e evidências,
"sugestão") e dependências externas em duas camadas:
- no texto: só ATO de terceiro nomeado na própria obrigação, com o trecho literal conferido na fonte;
- prática conhecida por tema: sem citação da norma, com referência pública e a cautela do contraponto.

Tipo: só aparece como definitivo quando a regra e a IA (lida do cache local, sem chamada) concordam; se
discordam, "tipo a revisar". Sem resposta da IA no cache (o caso hoje: nenhuma IA foi chamada), o tipo
sai marcado "só pela regra · IA não consultada" e a pessoa decide. Não é parecer jurídico.
"""

import json
from pathlib import Path

from . import dependencias, enquadramento, tipos, tipos_ia
from .evidence import verify
from .normalizacao import espacos

ROTULO = "Análise regulatória preliminar · não constitui parecer jurídico · revisar com o jurídico"
# Prática conhecida: tema do plano -> dependência externa típica. Sem citação da norma da RN 1.137.
PRATICA_POR_TEMA = {"manejo": "autorizacao_municipal"}
# Causa externa conhecida por tema, fora do texto da norma e sem referência pública: só "a avaliar".
CAUSAS_POR_TEMA = {
    "consumidor": {
        "nome": "Indisponibilidade de canais de terceiros",
        "nota": "Prática conhecida, fora do texto da norma, sem citação nem referência pública. A avaliar com o jurídico, caso a caso.",
    }
}
SO_REGRA = "só pela regra · segunda leitura da IA não feita"
A_REVISAR = tipos_ia.A_REVISAR
TIPOS_DE_DETALHE = {"letter", "clause", "item", "paragraph"}


def _tipo(texto, detalhe, cache_ia, oid, cfg):
    regra = tipos.classificar(texto, detalhe=detalhe, cfg=cfg)
    tipo = regra["tipo"]
    if tipo == "outros":
        return {"id": None, "nome": None, "situacao": "sem_tipo", "por": regra["por"]}
    nome = tipos.manual(tipo, cfg)["nome"]
    if cache_ia:
        c = tipos_ia.comparar({oid: tipo}, cache_ia)[0]
        if c["situacao"] != "concordam":
            return {
                "id": None,
                "nome": None,
                "situacao": "a_revisar",
                "por": f"regra: {nome}; IA: {c['ia'] or 'sem resposta válida'}",
            }
        return {"id": tipo, "nome": nome, "situacao": "concordam", "por": "regra e IA concordam"}
    return {"id": tipo, "nome": nome, "situacao": "so_regra", "por": SO_REGRA}


def montar(out, rows, extraction, cache_ia=None):
    """Anexa `analise` às obrigações principais de cada tema de `out` (plano.montar) e devolve o
    bloco global (manuais, dependências, prática por tema)."""
    cfg_tipos = tipos.carregar()
    cfg_dep = dependencias.carregar()
    cache_ia = tipos_ia.carregar_cache() if cache_ia is None else cache_ia
    units = extraction["units"]
    por_unidade = {u["id"]: u for u in units}
    por_obrigacao = {o["id"]: o for o in out["obrigacoes"]}
    por_linha = {r["id"]: r for r in rows}
    manuais, deps = {}, {}

    def verificar(trecho, unit_id):
        return verify(
            trecho, unit_id, units, extraction["text_hash"], source=extraction.get("source")
        )["state"]

    for t in out["temas"]:
        principais = set(t["principais"])
        t["dependencias_no_texto"] = []
        for oid in t["obrigacoes"]:
            o = por_obrigacao[oid]
            unit = por_unidade.get(o["unidade"])
            if not unit:
                continue
            achadas = dependencias.detectar(
                unit["text"], None, lambda tr, u=unit["id"]: verificar(tr, u), cfg_dep
            )
            no_texto = [
                {"id": d["id"], "trecho_literal": espacos(d["trecho_literal"])}
                for d in achadas
                if d["origem"] == "texto" and d["citacao"] == "verified"
            ]
            for d in no_texto:
                deps.setdefault(d["id"], dependencias.manual_da_dependencia(d["id"], cfg_dep))
                t["dependencias_no_texto"].append({"obrigacao": oid, **d})
            if oid not in principais and not no_texto:
                continue
            texto = espacos(unit["text"])
            detalhe = bool(unit["parent"]) and unit["kind"] in TIPOS_DE_DETALHE
            tipo = _tipo(texto, detalhe, cache_ia, enquadramento.chave(por_linha[oid]), cfg_tipos)
            if tipo["id"] and tipo["id"] not in manuais:
                m = tipos.manual(tipo["id"], cfg_tipos)
                manuais[tipo["id"]] = {
                    "nome": m["nome"],
                    "ideias_cumprimento": m["ideias_cumprimento"],
                    "evidencias": m["evidencias"],
                    "status": m["status"],
                }
            o["analise"] = {"tipo": tipo, "dependencias_no_texto": no_texto}
    pratica = {}
    for tema, dep in PRATICA_POR_TEMA.items():
        deps.setdefault(dep, dependencias.manual_da_dependencia(dep, cfg_dep))
        pratica[tema] = dep
    return {
        "rotulo": ROTULO,
        "tipo_so_regra": SO_REGRA,
        "tipo_a_revisar": A_REVISAR,
        "manuais": manuais,
        "dependencias": deps,
        "pratica_por_tema": pratica,
        "causas_por_tema": CAUSAS_POR_TEMA,
        "contraponto": _contraponto(cfg_dep),
    }


def _contraponto(cfg_dep):
    p = cfg_dep["precedentes"][cfg_dep["contraponto_obrigatorio"]]
    return {k: p[k] for k in ("titulo", "urls", "o_que_e", "a_confirmar")}


REFERENCIA_ESCALA = Path(__file__).parent / "data" / "referencia_escala.json"


def referencia_escala(path=REFERENCIA_ESCALA):
    """Mediana e máximo por auto de infração de distribuição (n = 21), sem empresa: só ordem de
    grandeza, não estimativa por obrigação (docs/valor_provavel_csv.md)."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
