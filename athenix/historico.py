"""Referência histórica de multas para o valor provável: pipeline pronto, ainda sem dados reais.

Método em docs/proposta_valor_provavel.md. Uma observação é uma infração com grupo, valor por
infração e base de cálculo verificáveis, cada uma com arquivo, página, trecho e hash da fonte. O
percentual é 100 × principal final / base da própria infração. Por estrato (grupo, segmento e
regime): n, agentes, período, mediana, quartis, extremos e concentração. Abaixo do mínimo de
observações, ou com qualquer dado sintético, o estrato não é publicável e o provável continua "não
estimável". Nada aqui entra em impacto.py: ligar a referência ao cálculo depende de aprovação.
"""

import csv
import hashlib
import re
import statistics
from datetime import date
from pathlib import Path

CAMPOS = (
    "auto_infracao", "processo", "agente", "cnpj", "segmento", "dispositivo", "grupo", "regime",
    "data_infracao", "sancao", "base_tipo", "base_valor", "base_periodo", "principal_inicial",
    "principal_final", "estado", "valor_por_infracao", "fonte_arquivo", "fonte_pagina",
    "fonte_trecho", "fonte_sha256", "coletado_em", "sintetico",
)  # fmt: skip
OBRIGATORIOS = set(CAMPOS) - {"processo", "cnpj", "principal_inicial", "base_periodo"}
GRUPOS = ("I", "II", "III", "IV", "V")
SEGMENTOS = {"distribuicao", "transmissao", "geracao", "outro"}
ESTADOS = {"autuado", "reformado_em_recurso", "encerrado", "pago"}
# Decisão de produto a validar (proposta, item 7): mínimo de infrações verificadas por estrato.
MINIMO_N = 30
# Só decisão definitiva entra; "reformado_em_recurso" pode ainda mudar. Decisão pendente do fundador.
ESTADOS_ELEGIVEIS = frozenset({"encerrado", "pago"})
# Campos do CSV "Auto de Infração" da ANEEL citados na proposta (schema publicado no portal).
COLUNAS_AUTOS = (
    "VlrPenalidade",
    "VlrMultaAposJuizo",
    "VlrMultaAposDiretoria",
    "DscEnquadramentoAI",
)
ROTULO = "Referência histórica — não é previsão da sanção"


def _numero(texto):
    texto = (texto or "").strip().replace("R$", "").replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    return float(texto)


def validar(linha):
    """Lista de problemas de uma linha do CSV de observações (vazia = válida)."""
    erros = [f"{c} vazio" for c in sorted(OBRIGATORIOS) if not (linha.get(c) or "").strip()]
    if erros:
        return erros
    if linha["grupo"] not in GRUPOS:
        erros.append(f"grupo inválido: {linha['grupo']}")
    if linha["segmento"] not in SEGMENTOS:
        erros.append(f"segmento inválido: {linha['segmento']}")
    if linha["estado"] not in ESTADOS:
        erros.append(f"estado inválido: {linha['estado']}")
    if linha["sancao"] not in {"multa", "advertencia"}:
        erros.append(f"sanção inválida: {linha['sancao']}")
    for c in ("valor_por_infracao", "sintetico"):
        if linha[c] not in {"sim", "nao"}:
            erros.append(f"{c} deve ser sim ou nao")
    if not re.fullmatch(r"[0-9a-f]{64}", linha["fonte_sha256"]):
        erros.append("fonte_sha256 deve ter 64 caracteres hexadecimais")
    for c in ("data_infracao", "coletado_em"):
        try:
            date.fromisoformat(linha[c])
        except ValueError:
            erros.append(f"{c} deve ser AAAA-MM-DD")
    for c in ("base_valor", "principal_final"):
        try:
            v = _numero(linha[c])
            if v < 0 or (c == "base_valor" and v == 0):
                erros.append(f"{c} deve ser positivo")
        except ValueError:
            erros.append(f"{c} não é número")
    return erros


def elegivel(linha, estados=ESTADOS_ELEGIVEIS):
    """(entra no cálculo?, motivo)."""
    if linha["valor_por_infracao"] != "sim":
        return False, "auto com total agregado: não se divide o total entre infrações"
    if linha["estado"] not in estados:
        return False, f"estado {linha['estado']}: sem decisão definitiva"
    if linha["sancao"] == "advertencia":
        return False, "advertência: contada à parte, fora do percentual"
    return True, None


def ler_observacoes(path):
    """(observações válidas, erros por linha). Arquivo UTF-8, separador ';' ou ','."""
    texto = Path(path).read_text(encoding="utf-8-sig")
    dialeto = csv.Sniffer().sniff(texto.splitlines()[0], delimiters=";,")
    leitor = csv.DictReader(texto.splitlines(), dialect=dialeto)
    faltam = [c for c in CAMPOS if c not in (leitor.fieldnames or [])]
    if faltam:
        return [], [(1, [f"colunas ausentes: {', '.join(faltam)}"])]
    validas, erros = [], []
    for n, linha in enumerate(leitor, start=2):
        if problemas := validar(linha):
            erros.append((n, problemas))
        else:
            validas.append(linha)
    return validas, erros


def _quartis(valores):
    if len(valores) < 2:
        return valores[0], valores[0]
    q1, _, q3 = statistics.quantiles(valores, n=4, method="inclusive")
    return q1, q3


def estatisticas(observacoes, estados=ESTADOS_ELEGIVEIS, minimo=MINIMO_N, min_agentes=None):
    """Um resumo por estrato (grupo, segmento, regime), com exclusões contadas. `min_agentes`
    (diversidade mínima de agentes) não tem padrão: sem ele, nenhum estrato é publicável."""
    estratos = {}
    for o in observacoes:
        chave = (o["grupo"], o["segmento"], o["regime"])
        e = estratos.setdefault(chave, {"obs": [], "exclusoes": {}, "advertencias": 0, "sintetico": False})  # fmt: skip
        e["sintetico"] |= o["sintetico"] == "sim"
        ok, motivo = elegivel(o, estados)
        if o["sancao"] == "advertencia":
            e["advertencias"] += 1
        if ok:
            e["obs"].append(o)
        else:
            e["exclusoes"][motivo] = e["exclusoes"].get(motivo, 0) + 1
    out = []
    for (grupo, segmento, regime), e in sorted(estratos.items()):
        pcts = sorted(100 * _numero(o["principal_final"]) / _numero(o["base_valor"]) for o in e["obs"])  # fmt: skip
        agentes = [o["agente"] for o in e["obs"]]
        res = {
            "grupo": grupo,
            "segmento": segmento,
            "regime": regime,
            "n": len(pcts),
            "agentes": len(set(agentes)),
            "advertencias": e["advertencias"],
            "exclusoes": e["exclusoes"],
            "sintetico": e["sintetico"],
        }
        if pcts:
            q1, q3 = _quartis(pcts)
            datas = sorted(o["data_infracao"] for o in e["obs"])
            res |= {
                "mediana_pct": statistics.median(pcts),
                "q1_pct": q1,
                "q3_pct": q3,
                "minimo_pct": pcts[0],
                "maximo_pct": pcts[-1],
                "periodo": [datas[0], datas[-1]],
                "maior_participacao_agente": max(agentes.count(a) for a in set(agentes))
                / len(agentes),  # fmt: skip
            }
        if e["sintetico"]:
            res["publicavel"], res["motivo"] = False, "SINTÉTICO: dados de teste, nunca usar"
        elif len(pcts) < minimo:
            res["publicavel"], res["motivo"] = False, f"n = {len(pcts)} < {minimo}: não estimável"
        elif min_agentes is None:
            # Diversidade mínima de agentes ainda não foi decidida (proposta, item 7).
            res["publicavel"], res["motivo"] = False, "aguarda decisão da diversidade mínima de agentes"  # fmt: skip
        elif res["agentes"] < min_agentes:
            res["publicavel"], res["motivo"] = False, f"{res['agentes']} agentes < {min_agentes}: concentrado demais"  # fmt: skip
        else:
            res["publicavel"], res["motivo"] = True, "publicável após revisão de especialista"
        out.append(res)
    return out


def referencia(base, estrato):
    """Base informada × mediana percentual, com rótulo, n, período e quartis. Só estrato publicável."""
    if not estrato.get("publicavel"):
        return {"estimavel": False, "motivo": estrato.get("motivo", "estrato não publicável")}
    return {
        "estimavel": True,
        "rotulo": ROTULO,
        "valor": base * estrato["mediana_pct"] / 100,
        "intervalo": [base * estrato["q1_pct"] / 100, base * estrato["q3_pct"] / 100],
        "n": estrato["n"],
        "agentes": estrato["agentes"],
        "periodo": estrato["periodo"],
    }


def ler_autos(path, separador=";", encoding="utf-8-sig"):
    """Confere o CSV de Auto de Infração da ANEEL: colunas citadas na proposta, linhas e hash.
    Não vira observação: o cadastro não traz base de cálculo nem decisão definitiva."""
    dados = Path(path).read_bytes()
    linhas = dados.decode(encoding).splitlines()
    cabecalho = next(csv.reader(linhas[:1], delimiter=separador), [])
    return {
        "sha256": hashlib.sha256(dados).hexdigest(),
        "linhas": max(0, len(linhas) - 1),
        "colunas": cabecalho,
        "faltando": [c for c in COLUNAS_AUTOS if c not in cabecalho],
    }
