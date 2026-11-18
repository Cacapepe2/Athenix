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

from .tipos import carregar as carregar_tipos
from .tipos import normalizar

DEPENDENCIAS = Path(__file__).parent / "data" / "dependencias_externas.json"
FIM_FRASE = re.compile(r"[.;:\n]")
LIMITE = 400


@lru_cache(maxsize=1)
def carregar(path=DEPENDENCIAS):
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    for tipo in cfg["tipos"]:
        tipo["_sinais"] = [re.compile(p) for p in tipo["sinais"]]
    return cfg


def _frase(texto, inicio, fim):
    """Frase (ou item) do original que contém [inicio, fim), no máximo LIMITE caracteres."""
    ini = max((m.end() for m in FIM_FRASE.finditer(texto, 0, inicio)), default=0)
    m = FIM_FRASE.search(texto, fim)
    fim_f = m.start() if m else len(texto)
    trecho = texto[ini:fim_f].strip()
    if len(trecho) > LIMITE:  # frase longa: recorta em torno do sinal, em palavras inteiras
        a, b = max(inicio - LIMITE // 2, 0), min(fim + LIMITE // 2, len(texto))
        trecho = texto[a:b].strip()
    return trecho


def detectar(texto, tipo_obrigacao=None, verificar=None, cfg=None):
    """Dependências da obrigação. `verificar(trecho)` (opcional) devolve o estado da citação
    ("verified"/"pending"/…); sem ele, o estado fica "nao_verificada"."""
    cfg = cfg or carregar()
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
    if tipo_obrigacao:
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
