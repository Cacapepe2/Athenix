"""Amostra reproduzível de "área sugerida (IA)" para revisão humana: 10 deveres sorteados com semente fixa,
5 de "Regulatório" e 5 das demais áreas. Só lê os planos e o índice de fontes; não muda nada.

Uso: python scripts/demo/amostra_areas_ia.py   (grava docs/pitch/amostra_areas_ia.md)
"""

import json
import random
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAIDA = ROOT / "docs/pitch/amostra_areas_ia.md"
SEMENTE = 20261123
SITE = "https://athenix-two.vercel.app"
NORMAS = {"rn1137": ("RN ANEEL 1.137/2025", "/demo"), "ren1174": ("REN ANEEL 1.174/2026", "/demo?norma=ren1174")}  # fmt: skip


def chave(texto):
    """Mesma chave do site (landing/src/content/fontes.ts): NFC e sem espaços nem aspas nas pontas."""
    return re.sub(r"\s", "", unicodedata.normalize("NFC", texto)).strip('“”"').removesuffix("…")


def sortear():
    citacoes = json.loads((ROOT / "landing/src/content/fontes-publicas.json").read_text(encoding="utf-8"))["citacoes"]  # fmt: skip
    deveres = []
    for nome, (rotulo, rota) in NORMAS.items():
        p = json.loads(
            (ROOT / f"landing/src/content/plano-{nome}.json").read_text(encoding="utf-8")
        )
        for o in p["obrigacoes"]:
            if o.get("area_ia"):
                fonte = citacoes.get(p["norma"]["sha256"], {}).get(chave(o["area_ia"]["trecho"]))
                deveres.append({
                    "norma": rotulo,
                    "id": o["id"],
                    "dispositivo": o["dispositivo"],
                    "titulo": o.get("titulo_curto") or o["titulo_completo"],
                    "area": o["area"],
                    "trecho": o["area_ia"]["trecho"],
                    "fonte": SITE + fonte["url"] if fonte else None,
                    "plano": f"{SITE}{rota}#obrigacao-{o['id']}",
                })  # fmt: skip
    deveres.sort(key=lambda d: (d["norma"], d["id"]))
    rnd = random.Random(SEMENTE)
    reg = [d for d in deveres if d["area"] == "Regulatório"]
    outras = [d for d in deveres if d["area"] != "Regulatório"]
    return rnd.sample(reg, 5) + rnd.sample(outras, 5), len(deveres)


def relatorio(amostra, total):
    partes = [
        "# Amostra de “área sugerida (IA)” para revisão",
        f"10 de {total} deveres com área sugerida (IA), sorteados com a semente fixa `{SEMENTE}` "
        "(`python scripts/demo/amostra_areas_ia.py`): 5 de “Regulatório” e 5 das demais áreas. "
        "Cada área é **Sugestão** da IA e aguarda revisão humana. A amostra não mudou nada no plano.",
    ]
    for n, d in enumerate(amostra, start=1):
        fonte = (
            f"[fonte oficial]({d['fonte']})" if d["fonte"] else "fonte sem localização registrada"
        )
        partes.append(
            f"## {n}. {d['titulo']}\n\n"
            f"- **Norma e dispositivo:** {d['norma']}, {d['dispositivo']}\n"
            f"- **Área sugerida (IA):** {d['area']}\n"
            f"- **Trecho citado:** “{d['trecho']}”\n"
            f"- **Links:** {fonte} · [detalhe no plano]({d['plano']})"
        )
    return "\n\n".join(partes) + "\n"


def main():
    amostra, total = sortear()
    SAIDA.write_text(relatorio(amostra, total), encoding="utf-8", newline="\n")
    print(f"{SAIDA.relative_to(ROOT)}: {len(amostra)} de {total}")


if __name__ == "__main__":
    main()
