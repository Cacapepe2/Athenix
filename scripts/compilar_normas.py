"""Compila a REN 846: compilado oficial da ANEEL (até a RN 1.137/2025) + alterações de 2026.

Sem IA. Base: tests/fontes_impacto/atren2019846.pdf (biblioteca da ANEEL). Alteradoras, em ordem
cronológica: REN 1.148 (biblioteca da ANEEL), REN 1.162 e REN 1.174 (DOU, HTML). Grava
athenix/data/compilado_ren846.json (versões, histórico por dispositivo, conflitos).

Uso: python scripts/compilar_normas.py [--saida caminho.json] [--em AAAA-MM-DD]
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from athenix import compilacao, dou, structure  # noqa: E402
from athenix.config import Settings  # noqa: E402

F = ROOT / "tests/fontes_impacto"
SAIDA = ROOT / "athenix/data/compilado_ren846.json"
NORMA = {"numero": "846", "nome": "REN 846/2019"}
BASE = {
    "arquivo": "tests/fontes_impacto/atren2019846.pdf",
    "tipo": "biblioteca da ANEEL",
    "compilado_ate": "REN 1.137, de 21/10/2025",
    "vigente_desde": "2025-10-21",
}
ALTERADORAS = [
    {
        "nome": "REN 1.148/2026",
        "data": "2026-01-27",
        "arquivo": "tests/fontes_impacto/ren20261148.pdf",
        "tipo": "biblioteca da ANEEL",
    },
    {
        "nome": "REN 1.162/2026",
        "data": "2026-06-02",
        "arquivo": "tests/fontes_impacto/dou/dou_ren20261162.html",
        "tipo": "DOU",
    },
    {
        "nome": "REN 1.174/2026",
        "data": "2026-10-27",
        "arquivo": "tests/fontes_impacto/dou/dou_ren20261174.html",
        "tipo": "DOU",
    },
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publicacao_iso(texto):
    m = re.search(r"D\.O\. de (\d{2})\.(\d{2})\.(\d{4})", texto)
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def ler_ato(spec, settings):
    caminho = ROOT / spec["arquivo"]
    fonte = {"tipo": spec["tipo"], "arquivo": spec["arquivo"], "sha256": sha(caminho)}
    if caminho.suffix == ".html":
        html = dou.ler_html(caminho.read_bytes())
        d, m, a = html["publicacao"]["data"].split("/")
        ex = structure.from_pieces([html["texto"]], [], [], "dou", settings)
        fonte["publicacao_dou"] = {**html["publicacao"], "data": f"{a}-{m}-{d}"}
        return ex, fonte, f"{a}-{m}-{d}"
    ex = structure.extract(caminho.read_bytes(), "application/pdf", settings)
    return ex, fonte, publicacao_iso(ex["text"])


def montar(settings=None):
    settings = settings or Settings()
    base_path = ROOT / BASE["arquivo"]
    fonte_base = {k: BASE[k] for k in ("tipo", "arquivo", "compilado_ate")} | {
        "sha256": sha(base_path)
    }
    base = compilacao.ler_base(base_path.read_bytes(), "application/pdf", settings, fonte_base)
    base["vigente_desde"] = BASE["vigente_desde"]
    alteradoras, relatorio = [], []
    for spec in sorted(ALTERADORAS, key=lambda s: s["data"]):
        ex, fonte, pub = ler_ato(spec, settings)
        ato = {"nome": spec["nome"], "data": spec["data"]}
        alvos = compilacao.alvos(ex)
        if NORMA["numero"] not in alvos:
            relatorio.append({"ato": spec["nome"], "altera_a_846": False, "alvos": sorted(alvos)})
            continue
        ops, vig = compilacao.ler_alteradora(ex, NORMA["numero"], ato, pub)
        fonte["publicacao"] = pub
        alteradoras.append({"ato": ato, "fonte": fonte, "operacoes": ops, "vigencia": vig})
        relatorio.append(
            {
                "ato": spec["nome"],
                "altera_a_846": True,
                "operacoes": len(ops),
                "vigencia_padrao": vig["padrao"].isoformat() if vig["padrao"] else None,
                "avisos": vig["avisos"] + [w for w in ex["warnings"] if "sem aspas" in w],
                "alvos": sorted(alvos),
            }
        )
    compilado = compilacao.compilar(NORMA, base, alteradoras)
    compilado["base"] = fonte_base | {"vigente_desde": BASE["vigente_desde"]}
    compilado["alteradoras"] = [
        {
            "ato": a["ato"],
            "fonte": a["fonte"],
            "vigencia_padrao": a["vigencia"]["padrao"].isoformat()
            if a["vigencia"]["padrao"]
            else None,
            "operacoes": len(a["operacoes"]),
        }
        for a in alteradoras
    ]
    compilado["relatorio"] = relatorio
    return compilado


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default=str(SAIDA))
    ap.add_argument("--em", help="imprime o resumo do texto vigente nessa data")
    a = ap.parse_args()
    comp = montar()
    Path(a.saida).write_text(
        json.dumps(comp, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {k: comp[k] for k in ("relatorio", "aplicadas", "conflitos", "nao_aplicado")},
            ensure_ascii=False,
            indent=1,
        )
    )
    if a.em:
        print(len(compilacao.texto_vigente(comp, a.em)), "dispositivos vigentes em", a.em)


if __name__ == "__main__":
    main()
