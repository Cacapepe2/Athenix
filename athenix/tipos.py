"""Tipos de obrigação: classificação por regras e manual por tipo (athenix/data/tipos_obrigacao.json).

Sem IA na classificação. O texto da norma nunca é alterado: o texto é normalizado (minúsculas, sem
acento) só para casar os sinais. O que não casar suficientemente vai para "outros".

Gancho de IA (opcional, desligado): `especializar` só ESPECIALIZA o texto do manual para a obrigação.
A citação literal continua vindo das regras. Modo "off" (padrão) não faz nada; "cached" lê
athenix/data/manuais_especializados.json (id da obrigação → texto), sem rede; "live" exige gerador
explícito E `custo_confirmado=True` (a estimativa de custo vem de `estimar_custo`, antes do "ok").
"""

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

DADOS = Path(__file__).parent / "data"
TIPOS = DADOS / "tipos_obrigacao.json"
CACHE_MANUAIS = DADOS / "manuais_especializados.json"
PESO_VERBO, PESO_CONTEXTO, BONUS_VERBO_PRINCIPAL = 2, 1, 3
MODAL = re.compile(r"\bdeve(?:m|ra|rao)?\s+")


@lru_cache(maxsize=1)
def carregar(path=TIPOS):
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    for tipo in cfg["tipos"]:
        tipo["_sinais"] = [re.compile(p) for p in tipo["sinais"]]
        tipo["_contexto"] = [re.compile(p) for p in tipo["contexto"]]
    return cfg


def normalizar(texto):
    """Minúsculas e sem acento, mantendo o mesmo comprimento (índice a índice) do original."""
    saida = []
    for c in texto or "":
        base = unicodedata.normalize("NFD", c)[0] if not unicodedata.combining(c) else ""
        saida.append(base.lower() if base else "")
    return "".join(saida)


def _pontuar(tipo, norm):
    achados = []
    # Verbo principal: o que vem logo depois de "deve/devem/deverá/deverão".
    modal = MODAL.search(norm)
    janela = norm[modal.end() : modal.end() + 40] if modal else ""
    bonus = 0
    for pad in tipo["_sinais"]:
        if m := pad.search(norm):
            achados.append(("sinal", pad.pattern, m.start(), m.end()))
            bonus = BONUS_VERBO_PRINCIPAL if janela and pad.search(janela) else bonus
    ctx = []
    for pad in tipo["_contexto"]:
        if m := pad.search(norm):
            ctx.append(("contexto", pad.pattern, m.start(), m.end()))
    if tipo.get("exige_contexto") and not ctx:
        return 0, []
    pontos = PESO_VERBO * len(achados) + PESO_CONTEXTO * len(ctx) + bonus
    return pontos, achados + ctx


def classificar_texto(texto, cfg=None):
    cfg = cfg or carregar()
    norm = normalizar(texto)
    candidatos = []
    for ordem, tipo in enumerate(cfg["tipos"]):
        if tipo["id"] == "outros":
            continue
        pontos, achados = _pontuar(tipo, norm)
        if pontos >= cfg["minimo_pontos"]:
            candidatos.append((pontos, -ordem, tipo["id"], achados))
    if not candidatos:
        return {
            "tipo": "outros",
            "por": "sem sinal suficiente",
            "pontos": 0,
            "sinais": [],
            "candidatos": [],
        }
    candidatos.sort(reverse=True)  # mais pontos; empate: tipo que vem antes na lista
    pontos, _, tipo, achados = candidatos[0]
    return {
        "tipo": tipo,
        "por": "regra",
        "pontos": pontos,
        "sinais": [
            {"classe": c, "padrao": p, "trecho": (texto or "")[i:f]} for c, p, i, f in achados
        ],
        "candidatos": [(c[2], c[0]) for c in candidatos[:3]],
    }


def classificar(texto, contexto="", cfg=None):
    """Classifica pelo texto do dispositivo; se não casar, tenta com o texto dos dispositivos-pai
    (alíneas e incisos soltos só fazem sentido com o caput). `por` diz de onde veio."""
    r = classificar_texto(texto, cfg)
    if r["tipo"] == "outros" and contexto:
        r2 = classificar_texto(f"{contexto} {texto}", cfg)
        if r2["tipo"] != "outros":
            return r2 | {"por": "regra (com o texto do dispositivo-pai)"}
    return r


def manual(tipo_id, cfg=None):
    cfg = cfg or carregar()
    return next(t for t in cfg["tipos"] if t["id"] == tipo_id)


def estimar_custo(obrigacoes, tokens_por_chamada=900):
    """Estimativa grosseira de tokens para especializar `obrigacoes` (só antes de pedir o "ok")."""
    return {"chamadas": len(obrigacoes), "tokens_estimados": len(obrigacoes) * tokens_por_chamada}


def especializar(obrigacao_id, tipo_id, texto, modo="off", gerador=None, custo_confirmado=False):
    """Texto do manual especializado para a obrigação, ou None. Interpretação, nunca citação."""
    if modo == "off":
        return None
    if modo == "cached":
        if not CACHE_MANUAIS.exists():
            return None
        return json.loads(CACHE_MANUAIS.read_text(encoding="utf-8")).get(obrigacao_id)
    if modo == "live":
        if gerador is None or not custo_confirmado:
            raise PermissionError(
                "modo live exige gerador explícito e custo_confirmado=True (ok do fundador)"
            )
        return gerador(obrigacao_id, tipo_id, texto)
    raise ValueError(f"modo desconhecido: {modo}")
