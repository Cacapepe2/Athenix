"""Relatório de tipos de obrigação e dependências externas na RN 1.137/2025 (regras, sem IA).

Uso: python scripts/relatorio_tipos.py [--md docs/tipos_obrigacao_rn1137.md] [--json saida.json]
Processa a norma como a demo (banco descartável), classifica cada obrigação pelo texto do próprio
dispositivo (e, se não casar, com o dos dispositivos-pai), detecta dependências externas e verifica
cada trecho literal de dependência contra a norma (`evidence.verify`). Nenhuma chamada de IA.
"""

import argparse
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from fastapi.testclient import TestClient  # noqa: E402

from athenix import dependencias, tipos  # noqa: E402
from athenix.app import create_app  # noqa: E402
from athenix.config import Settings  # noqa: E402
from athenix.demo import USUARIO, preparar  # noqa: E402
from athenix.evidence import verify  # noqa: E402
from athenix.normalizacao import espacos  # noqa: E402
from athenix.poc.semantic import dispositivo  # noqa: E402


def processar():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        settings = Settings(model="", api_key="", ai_mode="off")
        senha = preparar(settings, banco=Path(tmp) / "demo.db")
        with TestClient(create_app(settings)) as client:
            client.post("/api/login", json={"username": USUARIO, "password": senha})
            rows = client.get("/api/obligations").json()["items"]
            doc = client.get(f"/api/documents/{rows[0]['document_id']}").json()
    return rows, doc["extraction"]


def contexto_dos_pais(unit, por_id):
    partes = []
    pai = por_id.get(unit["parent"])
    while pai:
        partes.append(espacos(pai["text"]))
        pai = por_id.get(pai["parent"])
    return " ".join(reversed(partes))


def analisar(rows=None, extraction=None):
    if rows is None:
        rows, extraction = processar()
    units = extraction["units"]
    por_id = {u["id"]: u for u in units}
    saida = []
    for row in rows:
        ancora = row["anchors"][0] if row["anchors"] else None
        unit = por_id.get(ancora["unit_id"]) if ancora else None
        if not unit:
            continue
        texto = unit["text"]
        pais = contexto_dos_pais(unit, por_id)
        classe = tipos.classificar(espacos(texto), pais)

        def verificar(trecho, unit=unit):
            r = verify(
                trecho, unit["id"], units, extraction["text_hash"], source=extraction.get("source")
            )
            return r["state"]

        deps = dependencias.detectar(texto, classe["tipo"], verificar)
        saida.append(
            {
                "id": row["id"],
                "dispositivo": dispositivo(unit, por_id),
                "unidade": unit["id"],
                "texto": espacos(texto),
                "tipo": classe["tipo"],
                "por": classe["por"],
                "sinais": [s["trecho"] for s in classe["sinais"]],
                "dependencias": deps,
            }
        )
    return saida


def resumo(itens):
    n = len(itens)
    por_tipo = Counter(i["tipo"] for i in itens)
    por_regra = sum(i["tipo"] != "outros" for i in itens)
    do_pai = sum(i["por"].startswith("regra (com") for i in itens)
    dep_texto = Counter(d["id"] for i in itens for d in i["dependencias"] if d["origem"] == "texto")
    dep_tipo = Counter(d["id"] for i in itens for d in i["dependencias"] if d["origem"] != "texto")
    com_texto = sum(any(d["origem"] == "texto" for d in i["dependencias"]) for i in itens)
    so_tipo = sum(
        bool(i["dependencias"]) and all(d["origem"] != "texto" for d in i["dependencias"])
        for i in itens
    )
    cit = Counter(d["citacao"] for i in itens for d in i["dependencias"] if d["origem"] == "texto")
    return {
        "obrigacoes": n,
        "por_tipo": dict(por_tipo.most_common()),
        "classificadas_por_regra": por_regra,
        "pct_por_regra": round(100 * por_regra / n, 1),
        "classificadas_com_texto_do_pai": do_pai,
        "outros": por_tipo.get("outros", 0),
        "dependencia_no_texto": {"obrigacoes": com_texto, "por_tipo": dict(dep_texto)},
        "dependencia_so_inferida_pelo_tipo": {"obrigacoes": so_tipo, "por_tipo": dict(dep_tipo)},
        "citacoes_das_dependencias_no_texto": dict(cit),
    }


def markdown(itens, r):
    cfg = tipos.carregar()
    nomes = {t["id"]: t["nome"] for t in cfg["tipos"]}
    L = ["# Tipos de obrigação e dependências externas na RN 1.137/2025", "",
         "Gerado por `python scripts/relatorio_tipos.py` (regras, sem IA). Manuais e dependências estão como",
         "**rascunho — revisar**. Texto normativo = citação; tipo e dependência inferida = interpretação.", "",
         "**Precisão:** classificar por regra não é o mesmo que classificar certo. Em revisão manual de duas",
         "amostras (28 e 34 obrigações, de 3 em 3 e de 5 em 5), cerca de 65% a 75% dos tipos eram plausíveis.",
         "Erros típicos: dispositivo que lista conteúdo (alínea) herda o tipo do caput; verbo genérico vence o",
         "verbo principal. \"outros\" é o resultado honesto quando falta sinal. A revisão humana dos tipos é necessária.", "",
         f"- Obrigações: **{r['obrigacoes']}**; classificadas por regra: **{r['classificadas_por_regra']} "
         f"({r['pct_por_regra']}%)**, das quais {r['classificadas_com_texto_do_pai']} só com o texto do dispositivo-pai; "
         f"em \"outros\": **{r['outros']}**.", "",
         "| Tipo | Obrigações |", "|---|---|"]  # fmt: skip
    L += [f"| {nomes[t]} | {n} |" for t, n in r["por_tipo"].items()]
    dt, di = r["dependencia_no_texto"], r["dependencia_so_inferida_pelo_tipo"]
    L += ["", "## Dependências externas",
          f"- Sinal **no próprio texto**: {dt['obrigacoes']} obrigações. Por dependência: {dt['por_tipo']}.",
          f"- Só **inferida pelo tipo** (sem sinal no texto): {di['obrigacoes']} obrigações.",
          f"- Citação do trecho que disparou (verificação literal): {r['citacoes_das_dependencias_no_texto']}.", "",
          "## Obrigações em \"outros\" (com a citação)", ""]  # fmt: skip
    for i in itens:
        if i["tipo"] == "outros":
            L.append(f'- **{i["dispositivo"]}**: "{i["texto"][:260]}"')
    return "\n".join(L) + "\n"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--md")
    ap.add_argument("--json")
    a = ap.parse_args()
    itens = analisar()
    r = resumo(itens)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    if a.md:
        Path(a.md).write_text(markdown(itens, r), encoding="utf-8", newline="\n")
    if a.json:
        Path(a.json).write_text(json.dumps(itens, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
