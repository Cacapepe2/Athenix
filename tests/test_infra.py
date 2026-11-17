"""Docker: o compose repassa toda variável lida em config.py e a imagem não leva ferramentas de teste."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _config_defaults():
    texto = (ROOT / "athenix" / "config.py").read_text(encoding="utf-8")
    pares = re.findall(r'os\.getenv\("(ATHENIX_\w+)"(?:,\s*"([^"]*)")?\)', texto)
    return {nome: padrao for nome, padrao in pares}


def _compose_env():
    texto = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    return dict(re.findall(r"^\s+(ATHENIX_\w+):\s*(.+?)\s*$", texto, re.M))


def test_compose_repassa_variaveis_com_os_padroes_do_config():
    config, compose = _config_defaults(), _compose_env()
    assert "ATHENIX_AI_MODE" in config and "ATHENIX_AZURE_ENDPOINT" in config
    for nome, padrao in config.items():
        if nome == "ATHENIX_DATABASE_URL":
            continue  # o compose aponta para o PostgreSQL do serviço db
        valor = compose.get(nome)
        assert valor, f"{nome} não é repassado ao container"
        m = re.fullmatch(r"\$\{" + nome + r"(:?-)(.*)\}", valor)
        assert m, f"{nome} deve vir do ambiente/.env, sem valor fixo: {valor}"
        assert m[2] == padrao, f"{nome}: padrão {m[2]!r} difere do config.py ({padrao!r})"
    assert compose["ATHENIX_AI_MODE"] == "${ATHENIX_AI_MODE:-off}"
    # Vazio é valor válido (sem raciocínio): só a ausência usa o padrão.
    assert compose["ATHENIX_REASONING_EFFORT"].startswith("${ATHENIX_REASONING_EFFORT-")


def test_imagem_de_producao_sem_dependencias_de_teste():
    assert "requirements.lock" in (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "requirements-dev" not in (ROOT / "Dockerfile").read_text(encoding="utf-8")
    prod = (ROOT / "requirements.lock").read_text(encoding="utf-8-sig").lower()
    for pacote in ("pytest", "hypothesis", "ruff", "httpx2"):
        assert not re.search(rf"^{pacote}==", prod, re.M), pacote
    dev = (ROOT / "requirements-dev.lock").read_text(encoding="utf-8").lower()
    assert "-r requirements.lock" in dev and "pytest==" in dev
