"""ATHENIX_AI_MODE: off (padrão) não toca a rede; cached só reaproveita; live tem teto e repete 429."""

import json

import httpx
import pytest
from conftest import drain, upload
from sqlalchemy import select
from test_proposals_ai import candidate, configured

from athenix import llm
from athenix.config import Settings
from athenix.db import CallClaim
from athenix.poc import semantic
from athenix.services import enqueue, extraction_data

NORMA = "<html><p>Art. 1º As empresas deverão enviar o relatório.</p></html>".encode()


def sem_rede(monkeypatch):
    def proibido(*args, **kwargs):
        raise AssertionError("Chamada de rede no modo off.")

    monkeypatch.setattr(httpx, "Client", proibido)
    monkeypatch.setattr(llm.httpx, "Client", proibido)


def test_default_is_off_and_incomplete_live_falls_back(monkeypatch):
    monkeypatch.delenv("ATHENIX_AI_MODE", raising=False)
    assert llm.modo(Settings())["efetivo"] == "off"
    assert llm.modo(Settings(ai_mode="LIGADO"))["efetivo"] == "off"
    live = llm.modo(Settings(ai_mode="live", model="m", api_key="", input_price=""))
    assert live["efetivo"] == "off" and "ATHENIX_API_KEY" in live["motivo"]
    assert llm.modo(Settings(ai_mode="cached", model=""))["efetivo"] == "off"
    completo = Settings()
    configured(completo)
    assert llm.modo(completo)["efetivo"] == "live"
    completo.run_budget_usd = "0"
    assert "teto de custo" in llm.modo(completo)["motivo"]


def test_off_makes_no_network_call_even_with_credentials(env, monkeypatch):
    app, client, settings = env
    configured(settings)
    settings.ai_mode = "off"
    sem_rede(monkeypatch)
    with pytest.raises(RuntimeError, match="nenhuma chamada"):
        llm.call_model(settings, llm.request_payload(settings.model, []))
    doc = upload(env, NORMA)
    endpoint = f"/api/documents/{doc['id']}/runs"
    response = client.post(endpoint, json={"kind": "ai", "budget": "1", "confirm_paid": True})
    assert response.status_code == 400 and "IA desligada" in response.text
    assert client.post(endpoint, json={"kind": "rules"}).status_code == 200
    drain(app, settings)
    assert client.get("/api/obligations").json()["count"] == 1
    page = client.get("/impacto")
    assert "IA: off" in page.text
    assert client.get("/health").json()["ai_mode"]["efetivo"] == "off"
    with app.state.factory() as session:
        extraction = extraction_data(session, doc["id"])
    run = {"spent": 0, "calls": []}
    chamada = lambda *_: pytest.fail("Chamada indevida")  # noqa: E731
    assert semantic.ai_items({}, extraction, [], settings, run, call=chamada) == ([], [])
    assert run["ai"]["status"] == "skipped" and "off" in run["ai"]["reason"]


def test_cached_reuses_recorded_answers_and_never_calls(env, monkeypatch):
    app, client, settings = env
    configured(settings)
    doc = upload(env, NORMA)
    with app.state.factory() as session:
        extraction = extraction_data(session, doc["id"])
    resposta = {
        "status": "complete",
        "raw": {
            "model": "modelo-sintetico",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": json.dumps({"items": [candidate(extraction)]})},
                }
            ],
        },
    }
    calls = []
    monkeypatch.setattr(llm, "call_model", lambda *_: calls.append(1) or resposta)
    endpoint = f"/api/documents/{doc['id']}/runs"
    assert (
        client.post(endpoint, json={"kind": "ai", "budget": "1", "confirm_paid": True}).status_code
        == 200
    )
    drain(app, settings)
    assert calls == [1]
    # cached: mesma requisição volta do banco, sem chamada e sem custo.
    settings.ai_mode, settings.api_key = "cached", ""
    monkeypatch.setattr(llm, "call_model", lambda *_: pytest.fail("Chamada no modo cached"))
    with app.state.factory.begin() as write:  # nova execução (fresh) da mesma requisição
        run_id = enqueue(write, doc["id"], "ai", "teste", settings, fresh=True)[0].id
    drain(app, settings)
    assert client.get(f"/api/runs/{run_id}").json()["state"] == "completed"
    # Miss no cached: não chama, falha com motivo e não deixa trava que bloqueie um live futuro.
    outro = upload(
        env, "<html><p>Art. 1º As empresas deverão publicar o plano anual.</p></html>".encode()
    )
    falha = client.post(
        f"/api/documents/{outro['id']}/runs", json={"kind": "ai", "confirm_paid": True}
    ).json()
    drain(app, settings)
    estado = client.get(f"/api/runs/{falha['id']}").json()
    assert estado["state"] == "failed" and "nenhuma chamada" in json.dumps(
        estado, ensure_ascii=False
    )
    with app.state.factory() as session:
        assert not [c for c in session.scalars(select(CallClaim)) if c.run_id == falha["id"]]


@pytest.mark.parametrize(
    "respostas,esperas,status",
    [
        ([(429, {"Retry-After": "1"}), (200, {})], [1.0], "complete"),
        ([(429, {}), (429, {}), (200, {})], [2.0, 4.0], "complete"),
        ([(429, {"Retry-After": "120"})], [], "rate_limited"),  # acima do limite: não espera
        ([(503, {})], [], "unknown_result"),  # 5xx pode ter sido cobrado: nunca repete
    ],
)
def test_live_retries_only_rate_limit(monkeypatch, respostas, esperas, status):
    fila = list(respostas)
    corpo = {"choices": [{"finish_reason": "stop", "message": {"content": '{"items": []}'}}]}
    real_client = httpx.Client
    transport = httpx.MockTransport(
        lambda request: httpx.Response(fila[0][0], json=corpo, headers=fila.pop(0)[1])
    )
    monkeypatch.setattr(llm.httpx, "Client", lambda **kwargs: real_client(transport=transport))
    settings = Settings()
    configured(settings)
    dormiu = []
    result = llm.call_model(
        settings, llm.request_payload("modelo-sintetico", []), sleep=dormiu.append
    )
    assert result["status"] == status and dormiu == esperas


def test_live_budget_cannot_exceed_configured_cap(env, monkeypatch):
    app, client, settings = env
    configured(settings)
    settings.run_budget_usd = "0.50"
    monkeypatch.setattr(llm, "call_model", lambda *_: pytest.fail("Chamada indevida"))
    doc = upload(env, NORMA)
    response = client.post(
        f"/api/documents/{doc['id']}/runs", json={"kind": "ai", "budget": "1", "confirm_paid": True}
    )
    assert response.status_code == 400 and "teto configurado" in response.text
