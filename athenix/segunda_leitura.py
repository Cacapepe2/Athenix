"""Segunda leitura offline: nunca substitui o resultado oficial das regras."""

import re
from collections import Counter

from .evidence import key, verify
from .normalizacao import espacos, normalizar

LABEL = "possível obrigação não detectada · revisar"
HEADING = re.compile(
    r"^(?:Art\.?\s*\d+[º°]?\.?|\d+\.|§\s*\d+[º°]?\.?|Parágrafo único\.|[IVXLCDM]+\s*[-–])\s*", re.I
)
EXTERNAL_DUTY = re.compile(
    r"\b(?:devem|deverá|deverão|deve|dever[aã] ser|obrigad[oa]s?|vedad[oa]s?)\b", re.I
)
FINANCIAL_ACT = re.compile(
    r"^(?:estabelecer|fixar|homologar|aprovar|declarar|reconhecer)\b.*\b(?:receitas?|tarifas?|valores?|parcelas?|reajustes?|resultados?|índices?)\b",
    re.I,
)
DECLARATORY = re.compile(
    r"^(?:revoga(?:r|-se)|ficam? revogad[oa]s?|(?:esta|este)\s+.+?\s+entra em vigor|fica\s+instituíd[oa]|não se aplicam)\b",
    re.I,
)


def sem_dever_externo(text):
    """Exclui atos de efeito normativo/financeiro, preservando dever externo explícito."""
    text = HEADING.sub("", espacos(text), count=1)
    if EXTERNAL_DUTY.search(text):
        return False
    return bool(FINANCIAL_ACT.search(text) or DECLARATORY.search(text))


def motivo_descarte(item, units):
    if item["type"] not in {"obligation", "prohibition"}:
        return "permissão: não é obrigação nem proibição"
    unit = units.get(item.get("locator", {}).get("unit_id"))
    if not unit or unit.get("struck"):
        return "dispositivo ausente ou com redação riscada"
    if sem_dever_externo(item["literal_text"]):
        return "ato homologatório/declaratório sem dever externo explícito"
    # Não elimina uma norma inteira: artigos da mesma norma podem impor deveres reais.
    if not EXTERNAL_DUTY.search(espacos(item["literal_text"])):
        parent = units.get(unit.get("parent"))
        while parent:
            if sem_dever_externo(parent["text"]):
                return "trecho subordinado a ato homologatório/declaratório sem dever externo"
            parent = units.get(parent.get("parent"))
    return None


def construir(comparacao, contexto):
    result = {
        "rotulo": LABEL,
        "resultado_oficial": "regras",
        "chamadas_pagas": 0,
        "criterio_diferenca": "Mesmo dispositivo e tipo usados no ensaio; novidade semântica exige revisão humana.",
        "por_norma": {},
        "itens": [],
        "descartados": [],
    }
    for doc_id, diff in comparacao["extraction"]["differences"].items():
        doc = contexto["docs"][doc_id]
        extraction = doc["extraction"]
        units = {u["id"]: u for u in extraction["units"]}
        candidates = {i["id"]: i for i in comparacao["extraction"]["ai_items"][doc_id]}
        official = {(i.get("locator", {}).get("unit_id"), i["type"]) for i in doc["items"]}
        seen, counts = set(), Counter(entrada=len(diff["ai_only_obligations"]))
        for brief in diff["ai_only_obligations"]:
            item = candidates[brief["id"]]
            reason = motivo_descarte(item, units)
            anchors = []
            if not reason:
                for a in item.get("anchors", []):
                    checked = verify(
                        a.get("quote", ""),
                        a.get("unit_id"),
                        extraction["units"],
                        extraction["text_hash"],
                        source=extraction.get("source"),
                    )
                    anchors.append(checked)
                if not anchors or any(
                    a["state"] != "verified"
                    or normalizar(a["quote"], espacos="nenhum", caixa=True)[0]
                    not in doc["reference_key"]
                    for a in anchors
                ):
                    reason = "citação não confirmada nas duas leituras"
            unit_id = item.get("locator", {}).get("unit_id")
            identity = (unit_id, item["type"], key(str(item["interpretation"])))
            if not reason and ((unit_id, item["type"]) in official or identity in seen):
                reason = "já encontrado pelas regras ou repetido no cache"
            if reason:
                counts[reason] += 1
                result["descartados"].append(
                    {
                        "norma": doc_id,
                        "id": item["id"],
                        "dispositivo": item["dispositivo"],
                        "motivo": reason,
                        "literal": item["literal_text"],
                    }
                )
                continue
            seen.add(identity)
            counts["restantes"] += 1
            result["itens"].append(
                {
                    "norma": doc_id,
                    "id": item["id"],
                    "tipo": item["type"],
                    "rotulo": LABEL,
                    "status": "suggested",
                    "validation_state": "pending_human_review",
                    "dispositivo": item["dispositivo"],
                    "literal": item["literal_text"],
                    "interpretacao_ia": item["interpretation"],
                    "citacoes": anchors,
                }
            )
        result["por_norma"][doc_id] = dict(counts)
    # Amostra reproduzível: até cinco por norma, priorizando verbos de ação concretos.
    sample = []
    for doc_id in result["por_norma"]:
        options = [i for i in result["itens"] if i["norma"] == doc_id]
        concrete = re.compile(
            r"^(?:realizar|apurar|definir|conter|desenvolver|elaborar|manter|publicar|enviar|informar|disponibilizar|incluir)\b",
            re.I,
        )
        options.sort(key=lambda i: not bool(concrete.search(i["interpretacao_ia"]["action"])))
        sample += options[:5]
    result["amostra_10"] = sample[:10]
    result["criterio_amostra"] = (
        "Até cinco por norma, priorizando verbos de ação concretos; não aleatória nem estimativa de precisão."
    )
    return result
