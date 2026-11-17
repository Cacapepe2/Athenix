"""Saúde da extração: invariantes gerais, válidos para qualquer documento (nada específico de norma).

Nota de 0 a 100. Penalidades (shortcut: pesos fixos, calibrar com o corpus de robustez):
- numeração: -2 por salto, repetição ou ordem invertida (até -30);
- trecho literal: -40 × fração de dispositivos que não aparecem na segunda leitura da fonte;
  sem segunda leitura confiável, -20;
- dispositivo que começa no meio de palavra: -3 cada (até -20);
- cobertura do texto estruturado abaixo de 80%: -1 por ponto percentual que falta (até -30);
- página sem texto (exige OCR): -10.
Abaixo de LIMITE, o documento fica marcado "revisar extração".
"""

import re

from .normalizacao import chave

LIMITE = 70
COBERTURA_MINIMA = 0.80
# Tabela e fórmula raramente batem entre motores de PDF (ordem das células): fora do teste literal.
SEM_TESTE_LITERAL = {"table", "formula", "heading", "unstructured"}
ROMANOS = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def _romano(texto):
    if not texto or any(c not in ROMANOS for c in texto):
        return None
    total = 0
    for atual, seguinte in zip(texto, texto[1:] + " "):
        valor = ROMANOS[atual]
        total += -valor if seguinte in ROMANOS and ROMANOS[seguinte] > valor else valor
    return total


def numero(unit):
    """(número, sufixo) do rótulo do dispositivo, ou None quando não é numerado em sequência."""
    rotulo, tipo = unit["label"].strip(), unit["kind"]
    if tipo in {"article", "item"}:
        m = re.match(r"(\d+)\s*[º°o]?\s*(?:-\s*([A-Z]+))?", rotulo)
        return (int(m.group(1)), m.group(2) or "") if m else None
    if tipo == "paragraph":
        m = re.match(r"§\s*(\d+)", rotulo)
        return (int(m.group(1)), "") if m else None
    if tipo == "clause":
        n = _romano(rotulo.upper())
        return (n, "") if n else None
    if tipo == "letter" and len(rotulo) == 1 and rotulo.isalpha():
        return (ord(rotulo.lower()) - 96, "")
    return None


NOMES = {
    "article": "Art.",
    "paragraph": "§",
    "clause": "inciso",
    "letter": "alínea",
    "item": "item",
}


def _rotulo(unit):
    nome, rotulo = NOMES.get(unit["kind"], unit["kind"]), unit["label"]
    return rotulo if rotulo.startswith(nome) else f"{nome} {rotulo}"  # "§ 1º" já traz o sinal


def numeracao(units):
    """Saltos, repetições e ordem invertida na sequência de cada nível (mesmo pai, tipo e dono).

    A redação revogada (riscada) entra na sequência: sem ela, um artigo revogado viraria salto. A
    redação antiga seguida da nova, com o mesmo número, não é repetição.
    """
    grupos = {}
    for u in units:
        if (n := numero(u)) is None:
            continue
        grupos.setdefault((u["parent"], u["kind"], u.get("owner")), []).append((u, n))
    achados = []
    for sequencia in grupos.values():
        sequencia.sort(key=lambda par: par[0]["start"])
        for (anterior, (n0, s0)), (atual, (n1, s1)) in zip(sequencia, sequencia[1:]):
            if (n1, s1) == (n0, s0):
                if not (anterior.get("struck") or atual.get("struck")):
                    achados.append(("repetição", f"{_rotulo(atual)} repetido"))
            elif n1 == n0 or n1 == n0 + 1:
                continue  # mesmo número com sufixo ("23" → "23-A") ou o próximo
            elif n1 > n0:
                achados.append(("salto", f"{_rotulo(anterior)} → {_rotulo(atual)}"))
            else:
                achados.append(("ordem", f"{_rotulo(anterior)} antes de {_rotulo(atual)}"))
    return achados


def avaliar(extracao):
    """Nota, situação e alertas de qualidade da extração de um documento."""
    texto = extracao.get("text") or ""
    units = [u for u in extracao.get("units", []) if not u.get("struck")]
    alertas, nota = [], 100.0

    def alerta(tipo, mensagem, exemplos=(), penalidade=0.0):
        nonlocal nota
        nota -= penalidade
        alertas.append(
            {
                "tipo": tipo,
                "mensagem": mensagem,
                "exemplos": list(exemplos)[:5],
                "penalidade": round(penalidade, 1),
            }
        )

    achados = numeracao(extracao.get("units", []))
    if achados:
        contagem = {
            t: sum(1 for a in achados if a[0] == t) for t in ("salto", "repetição", "ordem")
        }
        plural = {"salto": "saltos", "repetição": "repetições", "ordem": "ordens invertidas"}
        singular = {"salto": "salto", "repetição": "repetição", "ordem": "ordem invertida"}
        partes = [f"{n} {(plural if n > 1 else singular)[t]}" for t, n in contagem.items() if n]
        alerta("numeracao", "Numeração fora de sequência: " + ", ".join(partes) + ".",
               (a[1] for a in achados), min(30, 2 * len(achados)))  # fmt: skip

    fonte = extracao.get("source") or {}
    testaveis = [u for u in units if u["kind"] not in SEM_TESTE_LITERAL and u["text"].strip()]
    if fonte.get("key") and fonte.get("trusted"):
        ausentes = [u for u in testaveis if chave(u["text"]) not in fonte["key"]]
        if ausentes:
            fracao = len(ausentes) / len(testaveis)
            alerta("literal", f"{len(ausentes)} de {len(testaveis)} dispositivos não aparecem na segunda leitura da fonte.",
                   (_rotulo(u) for u in ausentes), 40 * fracao)  # fmt: skip
    else:
        alerta(
            "literal",
            "Sem segunda leitura confiável da fonte: o texto extraído não pôde ser conferido.",
            (),
            20,
        )

    meio = [
        u
        for u in units
        if 0 < u["start"] < len(texto)
        and texto[u["start"] - 1].isalnum()
        and texto[u["start"]].isalnum()
    ]
    if meio:
        alerta("meio_de_palavra", f"{len(meio)} dispositivo(s) começam no meio de uma palavra.",
               (_rotulo(u) for u in meio), min(20, 3 * len(meio)))  # fmt: skip

    total = sum(1 for c in texto if not c.isspace())
    # Redação revogada (riscada) também está estruturada: conta para a cobertura.
    estruturado = sum(
        1
        for u in extracao.get("units", [])
        if u["kind"] != "unstructured"
        for c in texto[u["start"] : u["end"]]
        if not c.isspace()
    )
    cobertura = estruturado / total if total else 0.0
    if cobertura < COBERTURA_MINIMA:
        alerta("cobertura", f"Só {cobertura:.0%} do texto ficou estruturado em dispositivos (mínimo {COBERTURA_MINIMA:.0%}).",
               (), min(30, 100 * (COBERTURA_MINIMA - cobertura)))  # fmt: skip

    sem_texto = [w for w in extracao.get("warnings", []) if "sem texto" in w and "OCR" in w]
    if sem_texto:
        alerta("ocr", f"{len(sem_texto)} página(s) sem texto: exigem OCR.", sem_texto, 10)

    nota = max(0, round(nota))
    return {
        "nota": nota,
        "situacao": "ok" if nota >= LIMITE else "revisar extração",
        "limite": LIMITE,
        "alertas": alertas,
        "metricas": {
            "dispositivos": len(units),
            "testados_literal": len(testaveis),
            "cobertura": round(cobertura, 3),
            "anomalias_numeracao": len(achados),
        },
    }
