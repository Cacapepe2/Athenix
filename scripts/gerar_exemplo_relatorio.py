"""Gera docs/exemplos/relatorio_impacto_rn1137.html: RN 1.137/2025, transmissora, base não informada.

Uso: python scripts/gerar_exemplo_relatorio.py [consulta]   # padrão: segmento=transmissao&data_referencia=2026-11-17
Sobe o app com banco descartável, envia a norma de tests/norma_poc/, roda a extração por regras (sem IA)
e grava o relatório exportável exatamente como o botão "Exportar relatório" o entrega.
"""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient  # noqa: E402

from athenix.app import create_app  # noqa: E402
from athenix.config import Settings  # noqa: E402
from athenix.services import run_one  # noqa: E402

NORMA = ROOT / "tests" / "norma_poc" / "ren20251137.pdf"
SAIDA = ROOT / "docs" / "exemplos" / "relatorio_impacto_rn1137.html"


def main(consulta):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        settings = Settings(
            database_url=f"sqlite:///{tmp}/exemplo.db",
            model="",
            api_key="",
            input_price="",
            output_price="",
            price_source="",
            price_date="",
        )
        app = create_app(settings)
        with TestClient(app) as client:
            senha = "exemplo-local-2026"
            client.post(
                "/setup",
                data={"nonce": app.state.setup_nonce, "username": "exemplo", "password": senha},
            )
            login = client.post("/api/login", json={"username": "exemplo", "password": senha})
            client.headers["x-csrf-token"] = login.json()["csrf"]
            doc = client.post(
                "/api/documents",
                files={"file": (NORMA.name, NORMA.read_bytes(), "application/pdf")},
                data={
                    "title": "RN ANEEL 1.137/2025",
                    "origin": "tests/norma_poc/ren20251137.pdf",
                    "role": "norm",
                },
            ).json()
            while run_one(app.state.factory, settings):
                pass
            client.post(f"/api/documents/{doc['id']}/runs", json={"kind": "rules"})
            while run_one(app.state.factory, settings):
                pass
            resposta = client.get(f"/impacto/relatorio?{consulta}&download=1")
            assert resposta.status_code == 200, resposta.text[:300]
    SAIDA.write_text(resposta.text, encoding="utf-8", newline="\n")
    print(f"{SAIDA.relative_to(ROOT)}: {len(resposta.text)} caracteres")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "segmento=transmissao&data_referencia=2026-11-17")
