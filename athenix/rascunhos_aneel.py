"""Pedidos de esclarecimento montados só dos sinais e leituras já registrados, sem IA ou envio."""

import hashlib
import json
from pathlib import Path

from . import esclarecimentos
from .normalizacao import espacos

DIVERGENCIAS = Path(__file__).parent / "data/divergencias_prodist_perguntas.json"
TIPO_DIVERGENCIA = "divergência entre o texto publicado da RN e a versão compilada do PRODIST"

ROTULO = "rascunho — revisar antes de enviar"
SEM_ALTERNATIVA = "As leituras normativas alternativas não estão determinadas nos dados; revisar a interpretação antes de enviar."


def leituras(caso, o, out):
    tipo = caso["tipo"]
    if tipo == "enquadramento sem texto":
        ia = (o or {}).get("ia")
        sugestao = (
            [
                f"Sugestão já registrada pela IA: {ia['dispositivo']} (Grupo {ia['grupo']}); aguarda revisão humana."
            ]
            if ia
            else []
        )
        return (
            "Qual enquadramento da REN 846 se aplica ao dispositivo e qual fundamento sustenta essa leitura?",
            sugestao
            + [
                "O texto da obrigação não identifica a infração; o enquadramento permanece em aberto."
            ],
            SEM_ALTERNATIVA,
        )
    if tipo == "sujeito incerto":
        return (
            "A responsabilidade pelo dever descrito deve ser atribuída à distribuidora, embora o sujeito não esteja expresso?",
            [
                "Hipótese usada no plano: dever da distribuidora, por ser norma dirigida às distribuidoras.",
                "O dispositivo não nomeia o sujeito; a atribuição permanece sem confirmação até esclarecimento.",
            ],
            SEM_ALTERNATIVA,
        )
    if tipo == "artigo inferido pela posição":
        m = o["marco"]
        return (
            "A qual artigo pertence este trecho de alteração e qual marco de aplicação deve ser observado?",
            [
                f"Hipótese registrada: {m['nota']}.",
                f"Marco usado no plano: {m['dispositivo']}, data {m.get('data') or 'não determinada'}.",
            ],
            SEM_ALTERNATIVA,
        )
    if tipo == "possível erro material":
        erro = o["erro_material"]
        return (
            "Qual é a leitura correta do prazo diante do possível erro material registrado no dispositivo?",
            [
                f"Texto original: {o['trecho']}",
                f"Leitura provável já registrada pelo motor: {erro['leitura_provavel']}.",
            ],
            None,
        )
    if tipo == "referência a outra norma":
        return (
            "Qual dispositivo da norma referenciada se aplica a este comando e como deve ser cumprida a remissão?",
            [f"Remissão não resolvida pelo motor: {a}" for a in caso["alvos"]],
            SEM_ALTERNATIVA,
        )
    if tipo == "transição ambígua":
        candidatas = (o.get("marco") or {}).get("candidatos") or []
        regras = {r["dispositivo"]: r for r in (out.get("transicao") or {}).get("regras", [])}
        return (
            "Qual regra de transição e qual data se aplicam a este dispositivo?",
            [
                f"Regra candidata: {d}; data registrada: {(regras.get(d) or {}).get('data') or 'não determinada'}."
                for d in candidatas
            ],
            None if len(candidatas) > 1 else SEM_ALTERNATIVA,
        )
    raise ValueError(f"Tipo de dúvida não tratado: {tipo}")


def montar(out, norma, trechos):
    por_id = {o["id"]: o for o in out["obrigacoes"]}
    dispositivos = out["obrigacoes"] + out.get("outros_dispositivos", [])
    grupos = {}
    for c in esclarecimentos.casos_a_confirmar(out, norma):
        o = por_id.get(c.get("obrigacao"))
        if not c["trecho"] or not c["dispositivo"]:
            raise ValueError("Rascunho exige dispositivo e citação literal.")
        # Um esclarecimento de prazo não confirma enquadramento ou sujeito de outra dúvida.
        if (
            o
            and o.get("esclarecimento")
            and c["tipo"] in {"possível erro material", "transição ambígua"}
        ):
            continue
        pergunta, alternativas, limite = leituras(c, o, out)
        chave = json.dumps([norma, c["tipo"], alternativas], ensure_ascii=False)
        grupo = grupos.setdefault(
            chave,
            {
                "id": "aneel-" + hashlib.sha256(chave.encode()).hexdigest()[:16],
                "rotulo": ROTULO,
                "tipo": c["tipo"],
                "duvida": pergunta,
                "leituras_possiveis": alternativas,
                "limite": limite,
                "referencias": [],
            },
        )
        ids = (
            [c["obrigacao"]]
            if c.get("obrigacao")
            else [
                d["id"]
                for d in dispositivos
                if esclarecimentos._mesmo_dispositivo(d.get("dispositivo"), c["dispositivo"])
            ]
        )
        ref = next(
            (
                r
                for r in grupo["referencias"]
                if r["dispositivo"] == c["dispositivo"] and r["trecho"] == c["trecho"]
            ),
            None,
        )
        if ref:
            ref["itens"] = list(dict.fromkeys(ref["itens"] + ids))
            continue
        grupo["referencias"].append(
            {
                "dispositivo": c["dispositivo"],
                "trecho": c["trecho"],
                "itens": ids,
                "fonte": {k: out["norma"][k] for k in ("titulo", "url", "sha256")},
                "possiveis_esclarecimentos": esclarecimentos.buscar(c, trechos),
            }
        )
    return list(grupos.values())


def divergencias_prodist(out, comparacao, path=DIVERGENCIAS):
    """Rascunhos para as divergências escolhidas pelo responsável entre o texto publicado da RN e a versão
    compilada do PRODIST (v3). Cada fragmento precisa estar, literalmente, no trecho da RN e no item da v3."""
    if not comparacao:
        return []
    v3 = comparacao["fontes"]["v3"]
    rn = {k: out["norma"][k] for k in ("titulo", "url", "sha256")}
    rascunhos = []
    for d in json.loads(Path(path).read_text(encoding="utf-8"))["divergencias"]:
        o = next((o for o in out["obrigacoes"] if o["dispositivo"] == d["dispositivo"]), None)
        atual = comparacao["itens"].get(d["item"], {}).get("atual")
        if not o or not atual:
            raise ValueError(
                f"Divergência sem dispositivo no plano ou item na v3: {d['dispositivo']}"
            )
        if espacos(d["rn"]) not in espacos(o["trecho"]) or espacos(d["v3"]) not in espacos(
            atual["trecho"]
        ):
            raise ValueError(f"Fragmento não conferido na fonte: {d['dispositivo']}")
        leituras = [
            f"Texto publicado da RN 1.137: “{d['rn']}”.",
            f"Versão compilada do PRODIST, Módulo 4 (v3), página {atual['pagina']}: “{d['v3']}”.",
        ]
        if d.get("hipotese_nao_conferida"):
            leituras.append(d["hipotese_nao_conferida"])
        chave = json.dumps([rn["sha256"], v3["sha256"], d], ensure_ascii=False, sort_keys=True)
        rascunhos.append(
            {
                "id": "aneel-" + hashlib.sha256(chave.encode()).hexdigest()[:16],
                "rotulo": ROTULO,
                "tipo": TIPO_DIVERGENCIA,
                "duvida": f"Qual redação do {d['dispositivo']} deve ser observada ({d['natureza']}): a do texto "
                "publicado da RN 1.137 ou a da versão compilada do PRODIST, Módulo 4 (v3)?",
                "leituras_possiveis": leituras,
                "limite": "Divergência registrada pela comparação documental; nenhuma redação foi escolhida e "
                "o plano continua citando o texto publicado da RN 1.137.",
                "referencias": [
                    {
                        "dispositivo": f"RN 1.137 — {d['dispositivo']}",
                        "trecho": o["trecho"],
                        "itens": [o["id"]],
                        "fonte": rn,
                        "possiveis_esclarecimentos": [],
                    },
                    {
                        "dispositivo": f"PRODIST, Módulo 4 (v3) — item {d['item']}, página {atual['pagina']}",
                        "trecho": atual["trecho"],
                        "itens": [o["id"]],
                        "fonte": {
                            "titulo": v3["titulo"],
                            "url": v3["origem"],
                            "sha256": v3["sha256"],
                        },
                        "possiveis_esclarecimentos": [],
                    },
                ],
            }
        )
    return rascunhos
