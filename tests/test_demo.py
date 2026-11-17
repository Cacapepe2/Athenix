"""Demo de um comando: RN 1.137 processada por regras, usuário de demo, sem IA e sem rede."""

from fastapi.testclient import TestClient

from athenix import demo
from athenix.app import create_app
from athenix.config import Settings


def test_demo_prepares_rn1137_and_a_working_login(tmp_path):
    settings = Settings(model="", api_key="", ai_mode="off")
    senha = demo.preparar(settings, banco=tmp_path / "demo.db")
    assert len(senha) >= 12 and settings.database_url.endswith("demo.db")
    with TestClient(create_app(settings)) as client:
        login = client.post("/api/login", json={"username": demo.USUARIO, "password": senha})
        assert login.status_code == 200
        obrigacoes = client.get("/api/obligations").json()
        assert obrigacoes["count"] > 100
        assert {r["document_title"] for r in obrigacoes["items"]} == {"RN ANEEL 1.137/2025"}
        page = client.get("/impacto?perfil=ilustrativo")
        assert "Perfil ilustrativo" in page.text and "Citação inconsistente na fonte" in page.text
