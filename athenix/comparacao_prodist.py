"""Comparação documental do Módulo 4: sem inferir o histórico de outras fontes ou mudar deveres."""

import hashlib
import json
import re
from pathlib import Path

from .normalizacao import espacos

ROOT = Path(__file__).resolve().parents[1]
ITEM = re.compile(r"(?m)^\s*(\d+)\.\s+")
SECAO = re.compile(r"(?m)^\s*Seção\s+4\.\d+\s*$")
MARCAS = re.compile(r'[”"]?\s*\((?:NR|AC)\)\s*$')


def compacto(texto):
    return re.sub(r"\s+", "", espacos(MARCAS.sub("", texto))).strip('“”"')


def ler_pdf(raw):
    import pypdfium2

    with pypdfium2.PdfDocument(raw) as pdf:
        folhas = [p.get_textpage().get_text_range().replace("\r", "") for p in pdf]
    texto = "\n".join(folhas)
    if "MÓDULO 4" not in texto or "ANEXO IV" not in texto:
        raise ValueError("Fonte não identifica o Anexo IV / Módulo 4.")
    inicios, pos = [], 0
    for folha in folhas:
        inicios.append(pos)
        pos += len(folha) + 1

    def pagina(posicao):
        return sum(inicio <= posicao for inicio in inicios)

    marcas = list(ITEM.finditer(texto))
    itens = {}
    for i, m in enumerate(marcas):
        fim = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
        bloco = texto[m.start(1) : fim]
        corte = SECAO.search(bloco)
        if corte:
            bloco = bloco[: corte.start()]
        bloco = re.split(r"\(Alterado o anexo, pela REN", bloco)[0].rstrip()
        n = m.group(1)
        if n in itens:
            raise ValueError(f"Número de item duplicado: {n}")
        itens[n] = {
            "trecho": espacos(bloco),
            "pagina": pagina(m.start(1)),
            "ultima_pagina": pagina(m.start(1) + len(bloco) - 1),
            "comparavel": compacto(re.sub(r"(?m)^\s*[a-z]\)\s*", "", bloco)),
        }
    if not itens or set(map(int, itens)) != set(range(1, len(itens) + 1)):
        raise ValueError("Itens da fonte incompletos ou fora da sequência.")
    return itens


def comparar(anterior, atual):
    return {
        n: {
            "classe": "novo"
            if n not in anterior
            else "ja_existia"
            if anterior[n]["comparavel"] == v["comparavel"]
            else "alterado",
            "anterior": {k: x for k, x in anterior[n].items() if k != "comparavel"}
            if n in anterior
            else None,
            "atual": {k: x for k, x in v.items() if k != "comparavel"},
        }
        for n, v in atual.items()
    }


def fontes():
    catalogo = json.loads((ROOT / "tests/fontes_impacto/fontes.json").read_text(encoding="utf-8"))
    docs = {}
    for versao in ("v2", "v3"):
        (d,) = [d for d in catalogo["documentos"] if d["id"] == f"prodist4_{versao}"]
        arquivo = ROOT / "tests/fontes_impacto" / d["arquivo"]
        raw = arquivo.read_bytes()
        if hashlib.sha256(raw).hexdigest() != d["sha256"]:
            raise ValueError(f"Hash divergente na fonte {versao}.")
        docs[versao] = {
            "arquivo": arquivo.relative_to(ROOT).as_posix(),
            "sha256": d["sha256"],
            "titulo": d["ato"],
            "url": f"/fontes/{arquivo.name}",
            "origem": d["url"],
        }
    return docs


def unidades_do_modulo(extraction):
    unidades = extraction["units"]
    inicios = [
        i
        for i, u in enumerate(unidades)
        if u["kind"] == "article"
        and u["owner"] == "self"
        and re.search(r"O Anexo IV da Resolução Normativa nº 956", espacos(u["text"]))
    ]
    if len(inicios) != 1:
        raise ValueError("Bloco alterador do Anexo IV não identificado univocamente.")
    inicio = inicios[0]
    fim = next(
        (
            i
            for i in range(inicio + 1, len(unidades))
            if unidades[i]["kind"] == "article" and unidades[i]["owner"] == "self"
        ),
        len(unidades),
    )
    item, mapa = None, {}
    for u in unidades[inicio + 1 : fim]:
        if u["kind"] == "item":
            item = u["label"]
        if item and u["kind"] in {"item", "letter", "unstructured"}:
            mapa[u["id"]] = item
    return mapa


def montar(plano, extraction):
    gabarito = json.loads((ROOT / "tests/gabarito/fontes.json").read_text(encoding="utf-8"))
    norma = next(d for d in gabarito["documentos"] if d["id"] == "ren20251137")
    if plano["norma"]["sha256"] != norma["sha256"]:
        return None
    docs = fontes()
    anterior, atual = (ler_pdf((ROOT / docs[v]["arquivo"]).read_bytes()) for v in ("v2", "v3"))
    itens = comparar(anterior, atual)
    mapa = unidades_do_modulo(extraction)
    registros = {}
    for o in plano["obrigacoes"]:
        n = mapa.get(o["unidade"])
        if not n:
            continue
        if n not in atual:
            raise ValueError(f"Item {n} da RN ausente na v3.")
        registros[o["id"]] = {
            "item": n,
            "classe": itens[n]["classe"],
            "confere_v3": compacto(o["trecho"]) in compacto(atual[n]["trecho"]),
        }
    resumo = {
        c: sum(r["classe"] == c for r in registros.values())
        for c in ("novo", "alterado", "ja_existia")
    }
    resumo["sem_fonte"] = len(plano["obrigacoes"]) - len(registros)
    resumo["divergencias_v3"] = sum(not r["confere_v3"] for r in registros.values())
    return {
        "escopo": "Anexo IV da REN 956/2021 — Módulo 4 do PRODIST (v2 × v3)",
        "fontes": docs,
        "resumo": resumo,
        "registros": registros,
        "itens": itens,
        "limite": "Classificação pela presença e redação do item na v2/v3, sem inferir o histórico dos demais módulos ou atos. Divergências v3 × RN 1.137 exigem revisão; a fonte e os deveres do plano são preservados.",
    }
