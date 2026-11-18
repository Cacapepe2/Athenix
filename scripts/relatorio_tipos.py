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
        detalhe = bool(unit["parent"]) and unit["kind"] in {"letter", "clause", "item", "paragraph"}
        classe = tipos.classificar(espacos(texto), pais, detalhe=detalhe)

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
    detalhe = sum(i["por"].startswith("detalhe do dispositivo-pai") for i in itens)
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
        "detalhe_do_dispositivo_pai_sem_tipo_proprio": detalhe,
        "outros": por_tipo.get("outros", 0),
        "outros_sem_sinal": por_tipo.get("outros", 0) - detalhe,
        "dependencia_no_texto": {"obrigacoes": com_texto, "por_tipo": dict(dep_texto)},
        "dependencia_so_inferida_pelo_tipo": {"obrigacoes": so_tipo, "por_tipo": dict(dep_tipo)},
        "citacoes_das_dependencias_no_texto": dict(cit),
    }


def markdown(itens, r):
    cfg = tipos.carregar()
    nomes = {t["id"]: t["nome"] for t in cfg["tipos"]}
    d = r["dependencia_no_texto"]
    L = [
        "# Tipos de obrigação e dependências externas na RN 1.137/2025",
        "",
        "Gerado por `python scripts/relatorio_tipos.py` (regras, sem IA). Manuais e dependências estão como",
        "**rascunho — revisar**. Texto normativo = citação; tipo e dependência = interpretação.",
        "",
        "**Regras desta versão:** o tipo vem só do texto do PRÓPRIO dispositivo. Alínea, inciso ou item que só",
        'detalha o conteúdo do caput (sem verbo próprio) NÃO herda o tipo dele: fica como "detalhe do',
        'dispositivo-pai". Dependência externa só é marcada quando o cumprimento depende de um ATO do terceiro',
        "(autorizar, licenciar, aprovar, emitir, ordenar, disponibilizar sistema ou dado); definições e menções",
        "sem esse ato não contam, e dependência que viria só do tipo não é marcada por obrigação.",
        "A precisão do tipo ainda não foi medida de forma independente; a comparação com a IA (docs/tipos_obrigacao_ia.md,",
        "quando houver autorização de custo) mostra onde regra e IA concordam.",
        "",
        f"- Obrigações: **{r['obrigacoes']}**; com tipo por regra: **{r['classificadas_por_regra']} ({r['pct_por_regra']}%)**.",
        f"- Sem tipo próprio: **{r['outros']}**, sendo {r['detalhe_do_dispositivo_pai_sem_tipo_proprio']} detalhes do dispositivo-pai",
        f"  e {r['outros_sem_sinal']} sem sinal.",
        "",
        "| Tipo | Obrigações |",
        "|---|---|",
    ]
    L += [f"| {nomes[t]} | {n} |" for t, n in r["por_tipo"].items()]
    L += [
        "",
        "## Dependências externas (só com ato do terceiro no texto)",
        f"- Obrigações com dependência: **{d['obrigacoes']}**. Por dependência: {d['por_tipo']}.",
        f"- Citação do trecho que disparou (verificação literal): {r['citacoes_das_dependencias_no_texto']}.",
        "",
        "## Obrigações sem tipo próprio (com a citação)",
        "",
    ]
    for i in itens:
        if i["tipo"] == "outros":
            marca = "detalhe do pai" if i["por"].startswith("detalhe") else "sem sinal"
            L.append(f'- **{i["dispositivo"]}** ({marca}): "{i["texto"][:240]}"')
    return chr(10).join(L) + chr(10)


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
