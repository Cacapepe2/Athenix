"""Normalização única do texto para COMPARAR e ESTRUTURAR. O texto guardado nunca muda.

Toda comparação entre leituras (extrator × segunda leitura, citação × fonte, gabarito × sistema) passa
por aqui, para que espaços, quebras de linha, hifenização, aspas, travessões e grafia antiga sejam
tratados do mesmo jeito em todo lugar. `normalizar` devolve o texto normalizado e o mapa de posições:
`mapa[i]` é a posição, no texto original, do caractere `i` do texto normalizado. Assim um trecho
achado no normalizado volta ao intervalo exato do original.
"""

import unicodedata

# Aspas e travessões tipográficos viram ASCII: motores de PDF divergem neles.
EQUIVALENTES = {c: '"' for c in "“”„‟«»"} | {c: "'" for c in "‘’‚‛"} | {c: "-" for c in "–—‐‑‒−"}
# Invisíveis: hífen condicional, espaço de largura zero, BOM, marca de direção.
INVISIVEIS = set("­​‌‍⁠﻿‎‏")
TREMA = "̈"


def _hifenizacao(texto, i):
    """Fim do trecho "palavra-<quebra de linha>continuação" a partir do hífen em `i`, ou None.

    Só junta quando há letra antes do hífen, quebra de linha depois (com espaços opcionais) e a
    linha seguinte começa com letra minúscula: "manu-\\ntenção". "Art. 3º-D", "I -" e "auto-\\nProdução"
    (maiúscula) não são juntados.
    """
    if i == 0 or not texto[i - 1].isalpha():
        return None
    j = i + 1
    while j < len(texto) and texto[j] in " \t\r ":
        j += 1
    if j >= len(texto) or texto[j] != "\n":
        return None
    j += 1
    while j < len(texto) and texto[j] in " \t\r \f":
        j += 1
    return j if j < len(texto) and texto[j].islower() else None


def normalizar(texto, espacos="um", hifenizacao=True, trema=True, caixa=False):
    """Texto normalizado e mapa de posições. `espacos`: "um" (sequências viram um espaço),
    "nenhum" (removidos: motores divergem na inferência de espaços) ou "manter"."""
    texto = texto or ""
    saida, mapa = [], []
    i = 0
    while i < len(texto):
        c = texto[i]
        if c in INVISIVEIS:
            i += 1
            continue
        if hifenizacao and c == "-" and (fim := _hifenizacao(texto, i)) is not None:
            i = fim  # "manu-\ntenção" → "manutenção"
            continue
        if c.isspace():
            if espacos == "nenhum" or (espacos == "um" and saida and saida[-1] == " "):
                i += 1
                continue
            if espacos == "um":
                c = " "
        elif unicodedata.combining(c):
            # Acento separado do caractere base: compõe com o anterior (mesma posição de origem).
            if not (trema and c == TREMA) and saida:
                saida[-1] = unicodedata.normalize("NFC", saida[-1] + c)
            i += 1
            continue
        else:
            c = EQUIVALENTES.get(c, c)
            if trema and c in "üÜ":
                c = "u" if c == "ü" else "U"
        for parte in c.casefold() if caixa else c:
            saida.append(parte)
            mapa.append(i)
        i += 1
    if espacos == "um" and saida and saida[0] == " ":
        saida, mapa = saida[1:], mapa[1:]
    if espacos == "um" and saida and saida[-1] == " ":
        saida, mapa = saida[:-1], mapa[:-1]
    return "".join(saida), mapa


def chave(texto):
    """Forma de comparação entre leituras de motores diferentes (sem espaços)."""
    return normalizar(texto, espacos="nenhum")[0]


def espacos(texto):
    """Só colapsa espaços e quebras de linha, para exibir; não muda mais nada."""
    return " ".join((texto or "").split())


def intervalo_original(mapa, inicio, fim):
    """Intervalo [início, fim) no texto original de um trecho [inicio, fim) do texto normalizado."""
    return mapa[inicio], mapa[fim - 1] + 1
