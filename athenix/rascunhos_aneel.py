"""Pedidos de esclarecimento montados só dos sinais e leituras já registrados, sem IA ou envio."""

import hashlib
import json

from . import esclarecimentos

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
