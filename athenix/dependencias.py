"""Dependências externas (athenix/data/dependencias_externas.json): quando cumprir depende do governo
ou de terceiros. Sem IA.

Duas origens, mostradas de forma diferente:
- "texto": o sinal aparece no próprio texto da obrigação; guarda-se o TRECHO LITERAL que disparou (a
  frase que contém o sinal, como está no original), que passa pela verificação de citação existente
  (`athenix.evidence.verify`) quando o chamador a fornece;
- "inferida_pelo_tipo": o sinal não está no texto; a dependência vem só do tipo da obrigação
  (`dependencias_tipicas` em tipos_obrigacao.json) e aparece com menos destaque, sem citação.

O texto da norma não muda: a normalização (minúsculas, sem acento) só serve para casar os sinais.
Possível excludente não é garantia de afastamento de penalidade.
"""

import json
import re
from functools import lru_cache
from pathlib import Path

import unicodedata

from .tipos import carregar as carregar_tipos
from .tipos import normalizar

DEPENDENCIAS = Path(__file__).parent / "data" / "dependencias_externas.json"
FIM_FRASE = re.compile(r"[.;:]")
LIMITE = 400


@lru_cache(maxsize=1)
def carregar(path=DEPENDENCIAS):
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    for tipo in cfg["tipos"]:
        tipo["_sinais"] = [re.compile(p, re.S) for p in tipo["sinais"]]
    return cfg


ABREVIACOES = {"art", "arts", "n", "no", "inc", "al", "fl", "p", "cap", "§", "ex"}


def _fins(plano):
    """Posições de fim de frase: [.;:], exceto o ponto de abreviação ("art.", "nº.", "inc.")."""
    fins = []
    for m in FIM_FRASE.finditer(plano):
        if m.group() == "." and plano[m.end() : m.end() + 1].isdigit():
            continue  # ponto de milhar ("12.068")
        if m.group() == "." and re.search(
            r"(?<![\w§])(" + "|".join(ABREVIACOES) + r")$", plano[: m.start()], re.I
        ):
            continue
        fins.append(m)
    return fins


def _frase(texto, inicio, fim):
    """Frase (ou item) do original que contém [inicio, fim), no máximo LIMITE caracteres. As quebras
    de linha do PDF não encerram a frase (a busca usa o texto com as quebras trocadas por espaço, de
    mesmo comprimento); o ponto de "art." não encerra; o recorte de frase longa é em palavras inteiras."""
    plano = texto.replace(chr(10), " ")
    fins = _fins(plano)
    ini = max((m.end() for m in fins if m.end() <= inicio), default=0)
    seguinte = next((m for m in fins if m.start() >= fim), None)
    fim_f = seguinte.start() if seguinte else len(plano)
    if fim_f - ini > LIMITE:  # frase longa: recorta em torno do sinal, em palavras inteiras
        a, b = max(inicio - LIMITE // 2, 0), min(fim + LIMITE // 2, len(plano))
        a = plano.rfind(" ", 0, a + 1) + 1 if a > 0 else 0
        b = plano.find(" ", b) if plano.find(" ", b) >= 0 else len(plano)
        ini, fim_f = a, b
    return texto[ini:fim_f].strip()


def detectar(texto, tipo_obrigacao=None, verificar=None, cfg=None, incluir_inferidas=False):
    """Dependências da obrigação. `verificar(trecho)` (opcional) devolve o estado da citação
    ("verified"/"pending"/…); sem ele, o estado fica "nao_verificada"."""
    cfg = cfg or carregar()
    texto = unicodedata.normalize(
        "NFC", texto or ""
    )  # 1 caractere = 1 índice; o literal sai em NFC
    norm = normalizar(texto)
    achadas, vistos = [], set()
    for tipo in cfg["tipos"]:
        for pad in tipo["_sinais"]:
            if m := pad.search(norm):
                trecho = _frase(texto, m.start(), m.end())
                achadas.append(
                    {
                        "id": tipo["id"],
                        "origem": "texto",
                        "sinal": texto[m.start() : m.end()],
                        "trecho_literal": trecho,
                        "citacao": verificar(trecho) if verificar else "nao_verificada",
                    }
                )
                vistos.add(tipo["id"])
                break
    if (
        tipo_obrigacao and incluir_inferidas
    ):  # desligado por padrão: só se marca dependência de ATO no texto
        tipicas = next(
            (
                t["dependencias_tipicas"]
                for t in carregar_tipos()["tipos"]
                if t["id"] == tipo_obrigacao
            ),
            [],
        )
        achadas += [
            {
                "id": d,
                "origem": "inferida_pelo_tipo",
                "sinal": None,
                "trecho_literal": None,
                "citacao": None,
            }
            for d in tipicas
            if d not in vistos
        ]
    return achadas


def manual_da_dependencia(dep_id, cfg=None):
    cfg = cfg or carregar()
    d = next(t for t in cfg["tipos"] if t["id"] == dep_id)
    return {
        **{k: d[k] for k in ("id", "nome", "o_que_guardar", "caminho", "cautela", "status")},
        "precedentes": [
            {
                "id": p,
                **{
                    k: cfg["precedentes"][p][k]
                    for k in ("titulo", "urls", "o_que_e", "a_confirmar")
                },
            }
            for p in d["precedentes"]
        ],
    }
