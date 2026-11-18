"""Parcela Variável das transmissoras (PVI, PVRO, PVA): estrutura de cálculo, sem a norma ainda.

Nenhuma fórmula, fator ou limite está no código. Cada componente (base, PVI, PVRO, PVA, limite) e
cada fator vem de data/parcela_variavel.json com a expressão transcrita da norma, o dispositivo, o
trecho literal e o hash do arquivo. Sem isso, o cálculo responde "não estimável" e diz o que falta.
As expressões aceitam só números, variáveis declaradas, + - * / e min/max: nada é executado.
"""

import ast
import json
import operator
import re
from pathlib import Path

PARAMETROS = Path(__file__).parent / "data" / "parcela_variavel.json"
TIPOS = ("PVI", "PVRO", "PVA")
OPERADORES = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}  # fmt: skip
FUNCOES = {"min": min, "max": max}


def carregar(path=PARAMETROS):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def avaliar_expressao(expressao, variaveis):
    """Aritmética restrita: números, nomes de `variaveis`, + - * /, sinal e min/max."""

    def ev(no):
        if isinstance(no, ast.Expression):
            return ev(no.body)
        if isinstance(no, ast.Constant) and isinstance(no.value, (int, float)):
            return no.value
        if isinstance(no, ast.Name) and no.id in variaveis:
            return variaveis[no.id]
        if isinstance(no, ast.BinOp) and type(no.op) in OPERADORES:
            return OPERADORES[type(no.op)](ev(no.left), ev(no.right))
        if isinstance(no, ast.UnaryOp) and isinstance(no.op, ast.USub):
            return -ev(no.operand)
        if (
            isinstance(no, ast.Call)
            and isinstance(no.func, ast.Name)
            and no.func.id in FUNCOES
            and no.args
            and not no.keywords
        ):
            return FUNCOES[no.func.id](*(ev(a) for a in no.args))
        raise ValueError(f"expressão não permitida: {ast.dump(no)[:80]}")

    return ev(ast.parse(expressao, mode="eval"))


def _citado(c):
    return bool(c and c.get("expressao") and c.get("dispositivo") and (c.get("trecho") or "").strip())  # fmt: skip


def pendencias(params, tipos=TIPOS):
    """O que falta para calcular: norma com hash e componentes/fatores com citação."""
    faltam = []
    norma = params.get("norma") or {}
    if not (norma.get("ato") and re.fullmatch(r"[0-9a-f]{64}", norma.get("sha256") or "")):
        faltam.append("norma vigente (ato e sha256 do arquivo)")
    comps = params.get("componentes", {})
    faltam += [f"componente {c} com expressão, dispositivo e trecho" for c in ("base", *tipos) if not _citado(comps.get(c))]  # fmt: skip
    faltam += [f"fator {k} com dispositivo e trecho" for k, f in params.get("fatores", {}).items() if not (f.get("dispositivo") and f.get("trecho") and isinstance(f.get("valor"), (int, float)))]  # fmt: skip
    return faltam


def calcular(rap_anual, eventos, params):
    """PV estimada para os eventos informados. Cada evento: {"tipo": PVI|PVRO|PVA,
    "duracao_min": n, "variaveis": {...}} (variáveis extras exigidas pela expressão da norma)."""
    tipos = sorted({e["tipo"] for e in eventos} & set(TIPOS))
    if faltam := pendencias(params, tipos):
        return {"estimavel": False, "motivo": "Norma de Parcela Variável não carregada.", "faltam": faltam}  # fmt: skip
    comps = params["componentes"]
    fatores = {k: f["valor"] for k, f in params.get("fatores", {}).items()}
    base = avaliar_expressao(comps["base"]["expressao"], {"RAP": rap_anual, **fatores})
    parcelas = []
    for e in eventos:
        if e["tipo"] not in TIPOS:
            raise ValueError(f"tipo de evento desconhecido: {e['tipo']}")
        nomes = {"RAP": rap_anual, "BASE": base, "DURACAO": e["duracao_min"], **fatores, **e.get("variaveis", {})}  # fmt: skip
        parcelas.append({"tipo": e["tipo"], "valor": avaliar_expressao(comps[e["tipo"]]["expressao"], nomes)})  # fmt: skip
    total = sum(p["valor"] for p in parcelas)
    limitado = None
    if _citado(comps.get("limite")):
        limitado = avaliar_expressao(comps["limite"]["expressao"], {"TOTAL": total, "BASE": base, "RAP": rap_anual, **fatores})  # fmt: skip
    usados = ["base", *tipos] + (["limite"] if limitado is not None else [])
    return {
        "estimavel": True,
        "base": base,
        "parcelas": parcelas,
        "total": total if limitado is None else limitado,
        "total_antes_do_limite": total,
        "fontes": [
            {"componente": c, "dispositivo": comps[c]["dispositivo"], "trecho": comps[c]["trecho"]}
            for c in usados
        ],  # fmt: skip
        "norma": params["norma"],
        "aviso": "Estimativa com base nas premissas listadas, não constitui parecer jurídico.",
    }
