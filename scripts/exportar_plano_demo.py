"""Gera landing/src/content/plano-rn1137.json: o plano de ação da RN 1.137/2025 para a demo do site.

Uso:
  python scripts/exportar_plano_demo.py                  # plano com o perfil ilustrativo
  python scripts/exportar_plano_demo.py --importar-ia artifacts/revisao-ensaio
      # recria athenix/data/ia_cache_rn1137.json a partir do cache local do ensaio (sem rede)

Processa a norma por regras (sem IA), avalia com o perfil ilustrativo e monta o plano com
athenix/plano.py. Os títulos e enquadramentos sugeridos pela IA vêm do cache versionado
(athenix/data/ia_cache_rn1137.json), sem nenhuma chamada: títulos só quando passam nos filtros;
enquadramentos só como "Interpretação da IA", fora do cálculo. O site só lê o JSON gerado.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient  # noqa: E402

from athenix import impacto, plano  # noqa: E402
from athenix.app import create_app  # noqa: E402
from athenix.config import Settings  # noqa: E402
from athenix.demo import USUARIO, preparar  # noqa: E402
from athenix.normalizacao import espacos  # noqa: E402
from exportar_demo_site import rotulo  # noqa: E402

SAIDA = ROOT / "landing" / "src" / "content" / "plano-rn1137.json"
SITUACAO_PRINCIPAL = "principal não condicional e não genérica"


def processar():
    """RN 1.137 processada por regras num banco descartável: (linhas, unidades, parâmetros)."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        settings = Settings(model="", api_key="", ai_mode="off")
        senha = preparar(settings, banco=Path(tmp) / "demo.db")
        with TestClient(create_app(settings)) as client:
            client.post("/api/login", json={"username": USUARIO, "password": senha})
            rows = client.get("/api/obligations").json()["items"]
            doc = client.get(f"/api/documents/{rows[0]['document_id']}").json()
    return rows, doc["extraction"]["units"], impacto.carregar()


def montar(base, data_referencia, faturamento=None):
    """Plano para uma distribuidora com a base informada (None = em branco)."""
    rows, units, params = processar()
    form = {"segmento": "distribuicao", "base": "" if base is None else str(base)}
    form |= {"data_referencia": data_referencia, "faturamento": faturamento or ""}
    p = impacto.perfil(form)
    resultado = impacto.avaliar(params, rows, p)
    out = plano.montar(resultado, units, params, p, plano.carregar_temas(), plano.carregar_ia())
    by_id = {u["id"]: u for u in units}
    for o in out["obrigacoes"]:
        o["dispositivo"] = rotulo(by_id[o["unidade"]], by_id) if o["unidade"] else None
        assert o["trecho"] is None or o["trecho"] in espacos(by_id[o["unidade"]]["text"])
    return out, params, p


def importar_ia(pasta):
    """Cache enxuto e versionável: só as sugestões processadas, sem respostas brutas."""
    pasta = Path(pasta).resolve()
    fontes = [pasta / "titulos" / "resultado.json", pasta / "enquadramento_proposta.json"]
    titulos, enq = (json.loads(f.read_text(encoding="utf-8")) for f in fontes)
    cache = {
        "aviso": "Sugestões da IA gravadas no ensaio de 17/11/2026. Aguardam revisão humana e não entram no cálculo.",
        "modelo": titulos["modelo"],
        "reasoning": titulos["reasoning"],
        "gerado_por": "scripts/exportar_plano_demo.py --importar-ia",
        "fontes": [{"arquivo": f.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(f.read_bytes()).hexdigest()} for f in fontes],
        "criterio_titulos": "Título aplicado só sem alerta de sentido, com verbo no início, até 85 caracteres e citação literal presente no texto.",
        "criterio_enquadramentos": f"Só a sugestão principal com situação '{SITUACAO_PRINCIPAL}'.",
        "titulos": {
            t["id"]: {
                "titulo": t["titulo_ia"],
                "citacao": t["citacao"]["quote"],
                "alerta": t["alerta_revisao"] or None,
                "ajuste_proposto": t["ajuste_proposto_por_revisao"] or None,
            }
            for t in titulos["titulos"]
            if t["citacao"]["state"] == "verified"
        },
        "enquadramentos": {
            x["id"]: {
                "dispositivo": x["principal"]["device"],
                "grupo": x["principal"]["group"],
                "justificativa": x["principal"]["reason"],
                "duvida": x["principal"]["open_question"],
            }
            for x in enq["linhas"]
            if x["situacao"] == SITUACAO_PRINCIPAL
        },
    }  # fmt: skip
    plano.CACHE_IA.write_text(
        json.dumps(cache, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        f"{plano.CACHE_IA}: {len(cache['titulos'])} títulos, {len(cache['enquadramentos'])} enquadramentos"
    )


def main(saida):
    demo = impacto.perfil_ilustrativo()
    out, params, p = montar(demo["base"], demo["data_referencia"])
    ia = plano.carregar_ia()
    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    fonte = params["fontes"]["1137"]
    dados = {
        "gerado_por": "scripts/exportar_plano_demo.py",
        "commit_origem": commit,
        "gerado_em": date.today().isoformat(),
        "aviso": impacto.AVISO,
        "norma": {
            "titulo": "RN ANEEL 1.137/2025",
            "url": "https://www2.aneel.gov.br/cedoc/ren20251137.pdf",
            "sha256": fonte["sha256"],
            "vigencia": fonte["vigencia"],
        },
        "perfil": {
            "rotulo": demo["rotulo"],
            "aviso": demo["aviso"],
            "base_reais": float(demo["base"]),
            "origem_base": demo["origem_base"],
            "data_referencia": demo["data_referencia"],
        },
        "ia": {
            k: ia[k]
            for k in ("aviso", "modelo", "reasoning", "criterio_titulos", "criterio_enquadramentos")
        }
        if ia
        else None,  # fmt: skip
        **out,
    }
    Path(saida).write_text(
        json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    r = out["resumo"]
    print(f"{saida}: {r['aplicaveis']} obrigações, {r['temas']} temas (commit {commit})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--saida", default=str(SAIDA))
    parser.add_argument("--importar-ia", metavar="PASTA")
    args = parser.parse_args()
    importar_ia(args.importar_ia) if args.importar_ia else main(args.saida)
