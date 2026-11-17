"""Sugestão de enquadramento: regras curadas, IA validada, duas citações e confirmação humana."""

import json
import sys
from decimal import Decimal
from pathlib import Path

from conftest import propose

from athenix import enquadramento, impacto
from athenix.config import Settings

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import sugerir_enquadramento as script  # noqa: E402

PARAMS = impacto.carregar()
REGRAS = enquadramento.carregar_regras()
NORMA = (
    "<html><body>Publicado em 04/11/2026."
    "<p>Art. 1º As distribuidoras devem notificar o Poder Público imediatamente após a "
    "identificação de um evento crítico.</p></body></html>"
).encode()


def row(texto, anchors=True, **extra):
    a = [{"state": "verified", "unit_id": "u1", "quote": texto}] if anchors else []
    return {"id": "r1", "action": texto, "evidence": [{"quote": texto}], "anchors": a} | extra


def test_regras_curadas_sugerem_com_as_duas_citacoes():
    r = row("As distribuidoras devem manter registro do serviço de manejo da vegetação.")
    [s] = enquadramento.sugestoes(PARAMS, r, REGRAS)
    assert s["fonte"] == "regra" and s["infracao"]["dispositivo"] == "Art. 12, XXVII"
    assert "Plano de Manejo Vegetal" in s["infracao"]["trecho"]  # lado da infração, literal
    assert s["obrigacao"] == {"unit_id": "u1", "quote": r["action"]}  # lado da obrigação
    # Rejeitada para esta obrigação: não volta a ser sugerida.
    assert enquadramento.sugestoes(PARAMS, r | {"enquadramento_rejeitado": ["Art. 12, XXVII"]}, REGRAS) == []  # fmt: skip
    # Sem trecho verificado da obrigação não há citação dos dois lados: nenhuma sugestão.
    assert enquadramento.sugestoes(PARAMS, row(r["action"], anchors=False), REGRAS) == []
    assert enquadramento.sugestoes(PARAMS, row("Publicar o relatório anual."), REGRAS) == []


def test_ia_so_com_dispositivo_existente_e_marcada_como_interpretacao():
    r = row("Publicar o relatório anual de qualidade.")
    ia = {
        "modelo": "m",
        "gerado_em": "2026-11-17",
        "sugestoes": {
            enquadramento.chave(r): [
                {"dispositivo": "Art. 99, I", "justificativa": "inventado"},
                {"dispositivo": "Art. 9º, III", "justificativa": "Prestar informações."},
            ]
        },
    }
    [s] = enquadramento.sugestoes(PARAMS, r, REGRAS, ia)
    assert s["fonte"] == "ia" and s["infracao"]["dispositivo"] == "Art. 9º, III"
    assert enquadramento.sugestoes(PARAMS, r, REGRAS, None) == []


def test_validacao_da_resposta_da_ia():
    def resposta(conteudo, status="complete"):
        return {"status": status, "raw": {"choices": [{"message": {"content": conteudo}}]}}

    validas, erro = enquadramento.validar_ia(PARAMS, resposta(json.dumps({"sugestoes": [
        {"dispositivo": "Art. 12, XXVI", "justificativa": "Plano de Contingência."},
        {"dispositivo": "Art. 1º, I", "justificativa": "não existe"},
        {"dispositivo": "Art. 12, XXVII", "justificativa": "  "},
    ]})))  # fmt: skip
    assert erro is None and [v["dispositivo"] for v in validas] == ["Art. 12, XXVI"]
    assert enquadramento.validar_ia(PARAMS, resposta("não é json"))[1] == "invalid_json"
    assert enquadramento.validar_ia(PARAMS, resposta("", "refusal"))[1] == "refusal"
    # O pedido restringe o dispositivo à lista de infrações (enum) e não inclui itens como infrações.
    payload = enquadramento.payload_ia("m", PARAMS, row("x"))
    enum = payload["response_format"]["json_schema"]["schema"]["properties"]["sugestoes"]["items"]
    assert len(enum["properties"]["dispositivo"]["enum"]) == 109


def test_confirmacao_humana_tira_de_verificar_e_registra_quem_confirmou(env):
    app, client, settings = env
    _, rows = propose(env, NORMA)
    [ob] = [r for r in rows if "Poder Público" in r["action"]]
    tela = client.get("/impacto?segmento=distribuicao")
    assert "Sugestões de enquadramento" in tela.text and "Art. 12, XXVIII" in tela.text
    assert "Sugestão, não decisão" in tela.text
    base = {"expected_count": ob["decisions_count"], "review_type": "technical"}
    # Dispositivo fora da lista de infrações é recusado.
    erro = client.post(f"/api/obligations/{ob['id']}/review", json=base | {"action": "frame", "dispositivo": "Art. 99, I", "reason": "x"})  # fmt: skip
    assert erro.status_code >= 400
    ok = client.post(
        f"/obligations/{ob['id']}/review",
        data=base | {"action": "frame", "dispositivo": "Art. 12, XXVIII", "sugerido_por": "regra",
                     "reason": "Comunicação ao Poder Público em evento crítico.",
                     "voltar": "/impacto?segmento=distribuicao"},
        follow_redirects=False,
    )  # fmt: skip
    assert ok.status_code == 303 and ok.headers["location"] == "/impacto?segmento=distribuicao"
    [ob2] = [r for r in client.get("/api/obligations").json()["items"] if r["id"] == ob["id"]]
    assert ob2["enquadramento"]["dispositivo"] == "Art. 12, XXVIII"
    assert ob2["enquadramento"]["por"] == "analista"
    perfil = impacto.perfil({"segmento": "distribuicao"})
    res = impacto.avaliar(PARAMS, [ob2], perfil)
    assert not res["verificar"] and res["ranking"][0]["enquadramentos"][0]["confirmado"]
    tela = client.get("/impacto?segmento=distribuicao")
    assert "Enquadramento confirmado por analista" in tela.text
    # Redirecionamento só para a tela de impacto.
    fora = client.post(
        f"/obligations/{ob['id']}/review",
        data={"expected_count": ob2["decisions_count"], "action": "reject_frame",
              "dispositivo": "Art. 12, XXVIII", "reason": "Rever.", "voltar": "https://exemplo.com"},
        follow_redirects=False,
    )  # fmt: skip
    assert fora.headers["location"].startswith("/obligations/")
    [ob3] = [r for r in client.get("/api/obligations").json()["items"] if r["id"] == ob["id"]]
    assert ob3["enquadramento"] is None and ob3["enquadramento_rejeitado"] == ["Art. 12, XXVIII"]


def test_script_de_ia_nao_chama_sem_live_e_sem_custo_confirmado(tmp_path):
    rows = [row("Publicar o relatório anual de qualidade.")]
    chamadas = []

    def falsa(settings, payload):
        chamadas.append(payload)
        conteudo = json.dumps({"sugestoes": [{"dispositivo": "Art. 9º, III", "justificativa": "j"}]})  # fmt: skip
        return {"status": "complete", "raw": {"choices": [{"message": {"content": conteudo}}],
                                              "usage": {"prompt_tokens": 1000, "completion_tokens": 100}}}  # fmt: skip

    saida = tmp_path / "s.json"
    off = Settings(model="m", api_key="", ai_mode="off")
    assert script.executar(off, PARAMS, rows, "100", saida, falsa) is None and not chamadas
    live = Settings(model="m", api_key="k", ai_mode="live", input_price="2", output_price="8",
                    price_source="https://exemplo.com/precos", price_date="2026-11-01",
                    run_budget_usd="5")  # fmt: skip
    maximo = Decimal(script.estimar(live, PARAMS, rows)["custo_maximo_usd"])
    assert script.executar(live, PARAMS, rows, None, saida, falsa) is None
    assert script.executar(live, PARAMS, rows, str(maximo - Decimal("0.01")), saida, falsa) is None
    assert not chamadas and not saida.exists()
    r = script.executar(live, PARAMS, rows, str(maximo), saida, falsa)
    assert len(chamadas) == 1 and r["custo_usd"] == "0.0028"  # 1000 × 2 + 100 × 8 por milhão
    assert r["sugestoes"][enquadramento.chave(rows[0])][0]["dispositivo"] == "Art. 9º, III"
    assert json.loads(saida.read_text(encoding="utf-8"))["modelo"] == "m"


def test_pedido_azure_com_raciocinio_sem_store():
    sem = enquadramento.payload_ia("m", PARAMS, row("x"))
    com = enquadramento.payload_ia("m", PARAMS, row("x"), "low")
    assert sem["store"] is False and "reasoning_effort" not in sem
    assert "store" not in com and com["reasoning_effort"] == "low"
    assert com["max_completion_tokens"] > sem["max_completion_tokens"]
    azure = Settings(azure_endpoint="https://x.openai.azure.com", reasoning_effort="")
    assert enquadramento.raciocinio(azure) is None  # vazio: modelo sem raciocínio
    assert enquadramento.raciocinio(Settings(azure_endpoint="", reasoning_effort="low")) is None
