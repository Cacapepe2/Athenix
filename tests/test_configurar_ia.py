"""Configuração da IA: só funções puras, com valores fictícios (o interativo é rodado pelo usuário)."""

import os

from athenix.config import carregar_env
from scripts import configurar_ia as c

FICTICIA = "chaveficticia" + "0123456789abcdefWXYZ"


def test_endpoint_v1_target_uri_antigo_e_so_o_host():
    v1 = "https://meu-recurso.openai.azure.com/openai/v1/"
    # base_url do exemplo oficial (API v1), com ou sem barra e com /chat/completions: fica v1.
    for colado in (v1, v1[:-1], v1 + "chat/completions", "https://meu-recurso.openai.azure.com"):
        assert c.separar_uri(colado) == (v1, None, None), colado
        assert c.validar("ATHENIX_AZURE_ENDPOINT", colado) is None
    antigo = "https://meu-recurso.openai.azure.com/openai/deployments/meu-gpt/chat/completions?api-version=2025-04-01-preview"  # fmt: skip
    assert c.separar_uri(antigo) == ("https://meu-recurso.openai.azure.com", "meu-gpt", "2025-04-01-preview")  # fmt: skip
    assert c.validar("ATHENIX_AZURE_ENDPOINT", "https://x.services.ai.azure.com/openai/v1/") is None
    assert c.validar("ATHENIX_AZURE_ENDPOINT", "http://x.com") is not None
    assert c.validar("ATHENIX_AZURE_API_VERSION", "") is None  # opcional


def test_validacoes():
    assert c.validar("ATHENIX_INPUT_USD_M", "2.00") is None
    assert c.validar("ATHENIX_INPUT_USD_M", "2,00") is not None
    assert c.validar("ATHENIX_INPUT_USD_M", "0") is not None
    assert c.validar("ATHENIX_PRICE_DATE", "2999-01-01") is not None
    assert c.validar("ATHENIX_PRICE_SOURCE", "azure.com") is not None
    assert c.validar("ATHENIX_REASONING_EFFORT", "") is None
    assert c.validar("ATHENIX_REASONING_EFFORT", "max") is not None
    assert c.validar("ATHENIX_REASONING_EFFORT", "minimal") is None  # gpt-5


def test_gravar_preserva_o_resto_e_mascara(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# comentário\nOUTRA=1\nATHENIX_AI_MODE=live\nATHENIX_MODEL=velho\n", encoding="utf-8")  # fmt: skip
    c.gravar(env, {"ATHENIX_AI_MODE": "off", "ATHENIX_MODEL": "novo", c.CHAVE: FICTICIA})
    texto = env.read_text(encoding="utf-8")
    assert texto.startswith("# comentário\nOUTRA=1\nATHENIX_AI_MODE=off\nATHENIX_MODEL=novo\n")
    assert c.ler(env)[c.CHAVE] == FICTICIA
    assert c.mascarar(FICTICIA) == "…WXYZ" and FICTICIA not in c.mascarar(FICTICIA)
    # O carregador só lê ATHENIX_*, não sobrescreve o ambiente e não devolve valores.
    monkeypatch.setenv("ATHENIX_MODEL", "do-ambiente")
    monkeypatch.delenv(c.CHAVE, raising=False)
    nomes = carregar_env(env)
    assert "OUTRA" not in nomes and os.environ["ATHENIX_MODEL"] == "do-ambiente"
    assert os.environ[c.CHAVE] == FICTICIA and FICTICIA not in repr(nomes)
