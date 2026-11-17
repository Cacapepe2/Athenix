"""Gera landing/src/content/demo-rn1137.json: dados reais da RN 1.137/2025 para a demo do site.

Uso: python scripts/exportar_demo_site.py [--saida caminho]
Requer o módulo de impacto e a demo local (PRs #9 a #13). Processa a norma por regras (sem IA), avalia
com o perfil ilustrativo (athenix/data/perfil_ilustrativo.json) e exporta, para cada obrigação
escolhida, o trecho literal com âncora verificada, o dispositivo, o prazo e a estimativa de impacto
com premissas, confiança e fonte. O site só lê este arquivo: nenhum número é digitado nele.

Escolha: as três primeiras da ordem calculada e um exemplo separado sem enquadramento.
"""

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient  # noqa: E402

from athenix import impacto  # noqa: E402
from athenix.app import create_app  # noqa: E402
from athenix.config import Settings  # noqa: E402
from athenix.demo import USUARIO, preparar  # noqa: E402

SAIDA = ROOT / "landing" / "src" / "content" / "demo-rn1137.json"
FORMATO = {
    "article": "Art. {}",
    "paragraph": "{}",
    "clause": "inciso {}",
    "item": "item {}",
    "letter": "alínea {}",
    "annex": "Anexo {}",
}


def norm(texto):
    return " ".join((texto or "").split())


def rotulo(unit, by_id):
    """Dispositivo legível a partir da árvore de unidades: "Art. 20, inciso II"."""
    partes, u = [], unit
    while u:
        if fmt := FORMATO.get(u["kind"]):
            partes.append(fmt.format(u["label"]))
        u = by_id.get(u.get("parent"))
    return ", ".join(reversed(partes)) or unit["label"]


def obrigacao(i, by_id, posicao, params):
    row, m = i["row"], i["multa"]
    ancora = next(a for a in row["anchors"] if a["state"] == "verified")
    unit = by_id[ancora["unit_id"]]
    trecho = norm(ancora["quote"])
    assert trecho in norm(unit["text"]), "trecho não é literal da unidade"
    fontes = []
    for pr in m["premissas"]:
        p = params["parametros"].get(pr["parametro"] or "")
        if p and p["dispositivo"] not in fontes:
            fontes.append(p["dispositivo"] + (" da REN 846" if p.get("fonte") == "846" else ""))
    return {
        "id": row["id"],
        "acao": norm(row["action"]),
        "titulo_curto": impacto.titulo_obrigacao(row["action"]),
        "sujeito": norm(row["subject"]),
        "unidade": unit["id"],
        "dispositivo": rotulo(unit, by_id),
        "trecho": trecho,
        "posicao": posicao,
        "prazo": i["urgencia"]["principal"],
        "prazo_detalhe": i["urgencia"]["detalhe"],
        "data_prazo": i["urgencia"]["data"],
        "categorias": [
            {"nome": impacto.CATEGORIAS[c], "motivo": mot} for c, mot in i["categorias"]
        ],
        "impacto": {
            "grupos": m["grupos"],
            "enquadramentos": [
                {"dispositivo": e["dispositivo"], "grupo": e["grupo"], "trecho": e["trecho"]}
                for e in i["enquadramentos"]
            ],
            "minimo_reais": 0.0,
            "maximo_reais": m["reais"]["maximo"],
            "maximo_pct": m["maximo"],
            "provavel_reais": m["reais"]["provavel"],
            "motivo_provavel": m["motivo_provavel"],
            "teto_grupo_pct": m["teto_pct"],
            "teto_legal_pct": m["teto_legal_pct"],
            "teto_legal_subestimado": m["teto_legal"]["subestimado"] if m["teto_legal"] else None,
            "premissas": [pr["texto"] for pr in m["premissas"]],
            "fontes": fontes,
        },
        "verificar_enquadramento": bool(i.get("verificar")),
        "confianca": i["confianca"],
        "motivo_confianca": i["motivo_confianca"],
    }


def main(saida):
    params = impacto.carregar()
    demo = impacto.perfil_ilustrativo()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        settings = Settings(model="", api_key="", ai_mode="off")
        senha = preparar(settings, banco=Path(tmp) / "demo.db")
        with TestClient(create_app(settings)) as client:
            client.post("/api/login", json={"username": USUARIO, "password": senha})
            rows = client.get("/api/obligations").json()["items"]
            doc = client.get(f"/api/documents/{rows[0]['document_id']}").json()
    units = doc["extraction"]["units"]
    by_id = {u["id"]: u for u in units}
    perfil = impacto.perfil({k: demo[k] for k in ("segmento", "base", "data_referencia")})
    resultado = impacto.avaliar(params, rows, perfil)
    ranking = resultado["ranking"]
    posicao = {id(i): n for n, i in enumerate(ranking, start=1)}
    escolha = ranking[:3] + resultado["verificar"][:1]
    obrigacoes = [obrigacao(i, by_id, posicao.get(id(i)), params) for i in escolha]
    outros = [i for i in resultado["itens"] if i not in ranking and i not in resultado["verificar"]]
    funil = {
        "total": len(rows),
        "priorizadas": len(ranking),
        "verificar": len(resultado["verificar"]),
        "fora_perfil": sum(not i["aplicavel"] for i in outros),
        "sem_estimativa": sum(i["aplicavel"] for i in outros),
        "desconsideradas": len(rows) - len(resultado["itens"]),
    }
    assert funil["total"] == sum(v for k, v in funil.items() if k != "total")

    alertas, usadas = [], {o["unidade"] for o in obrigacoes}
    regua = impacto.alteracoes_da_regua(units)
    if regua:
        alertas.append({
            "id": "regua",
            "titulo": "Mudanças nas infrações e multas",
            "detalhe": "A norma muda a REN 846/2019, que define as multas do setor elétrico.",
            "efeito_empresa": "Revise os planos e procedimentos afetados: a norma altera as infrações que podem gerar multa para a empresa.",
            "unidade": regua[0]["id"],
        })  # fmt: skip
    for n, d in enumerate(impacto.citacoes_divergentes(units)):
        cs = d["citacoes"]
        alertas.append({
            "id": f"citacao{n}",
            "titulo": "Mesma norma, datas diferentes",
            "detalhe": f"A {d['ato']} aparece como “{norm(cs[0]['trecho'])}” e “{norm(cs[1]['trecho'])}”.",
            "unidade": cs[1]["unit_id"],
            "efeito_empresa": "Confira a versão oficial citada antes de definir ações e prazos; a referência inconsistente exige revisão.",
        })  # fmt: skip
    usadas |= {a["unidade"] for a in alertas}
    for alerta in alertas:
        complementos = [u["id"] for u in impacto.redacao_alterada(units, by_id[alerta["unidade"]])]
        alerta["redacao"] = complementos
        usadas.update(complementos)

    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    fonte = params["fontes"]["1137"]
    dados = {
        "gerado_por": "scripts/exportar_demo_site.py",
        "commit_origem": commit,
        "gerado_em": date.today().isoformat(),
        "criterio": "3 primeiras obrigações da ordem de prioridade; exemplo separado sem enquadramento",
        "funil": funil,
        "regra_ordem": impacto.REGRA_ORDEM,
        "aviso": impacto.AVISO,
        "aviso_data": impacto.AVISO_DATA,
        "norma": {
            "titulo": "RN ANEEL 1.137/2025",
            "arquivo": fonte["arquivo"],
            "url": "https://www2.aneel.gov.br/cedoc/ren20251137.pdf",
            "sha256": fonte["sha256"],
            "vigencia": fonte["vigencia"],
            "obrigacoes_extraidas": len(rows),
            "priorizadas": len(ranking),
            "verificar_enquadramento": len(resultado["verificar"]),
        },
        "perfil": {
            "rotulo": demo["rotulo"],
            "aviso": demo["aviso"],
            "segmento": demo["segmento"],
            "base_reais": float(demo["base"]),
            "origem_base": demo["origem_base"],
            "data_referencia": demo["data_referencia"],
        },
        "unidades": [
            {"id": u["id"], "dispositivo": rotulo(u, by_id), "texto": norm(u["text"])}
            for u in units
            if u["id"] in usadas
        ],
        "alertas": alertas,
        "obrigacoes": obrigacoes,
    }
    Path(saida).write_text(
        json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"{saida}: {len(obrigacoes)} obrigações, {len(alertas)} alertas (commit {commit})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--saida", default=str(SAIDA))
    main(parser.parse_args().saida)
