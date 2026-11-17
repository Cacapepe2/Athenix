import os
from dataclasses import dataclass, field
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / ".env"


def carregar_env(path=ENV):
    """Lê variáveis ATHENIX_* de .env para o ambiente, sem sobrescrever as já definidas.
    Nunca imprime valores: devolve só os nomes lidos. Chamado nos pontos de entrada (CLI e scripts),
    não na importação, para os testes não herdarem o .env de quem desenvolve."""
    path = Path(path)
    if not path.is_file():
        return []
    nomes = []
    for linha in path.read_text(encoding="utf-8-sig").splitlines():
        linha = linha.strip()
        if linha.startswith("#") or "=" not in linha:
            continue
        nome, valor = (p.strip() for p in linha.split("=", 1))
        if nome.startswith("ATHENIX_"):
            os.environ.setdefault(nome, valor.strip("\"'"))
            nomes.append(nome)
    return nomes


@dataclass
class Settings:
    database_url: str = field(
        default_factory=lambda: os.getenv("ATHENIX_DATABASE_URL", "sqlite:///.local/athenix.db")
    )
    max_bytes: int = 10 * 1024 * 1024
    max_pages: int = 300
    max_text: int = 1_000_000
    session_hours: int = 8
    secure_cookie: bool = field(default_factory=lambda: os.getenv("ATHENIX_HTTPS") == "1")
    model: str = field(default_factory=lambda: os.getenv("ATHENIX_MODEL", ""))
    api_key: str = field(default_factory=lambda: os.getenv("ATHENIX_API_KEY", ""), repr=False)
    endpoint: str = "https://api.openai.com/v1/chat/completions"
    input_price: str = field(default_factory=lambda: os.getenv("ATHENIX_INPUT_USD_M", ""))
    output_price: str = field(default_factory=lambda: os.getenv("ATHENIX_OUTPUT_USD_M", ""))
    price_source: str = field(default_factory=lambda: os.getenv("ATHENIX_PRICE_SOURCE", ""))
    price_date: str = field(default_factory=lambda: os.getenv("ATHENIX_PRICE_DATE", ""))
    # Azure OpenAI: com ATHENIX_AZURE_ENDPOINT definido, `model` é o nome do deployment.
    azure_endpoint: str = field(default_factory=lambda: os.getenv("ATHENIX_AZURE_ENDPOINT", ""))
    azure_api_version: str = field(
        default_factory=lambda: os.getenv("ATHENIX_AZURE_API_VERSION", "2025-04-01-preview")
    )
    reasoning_effort: str = field(
        default_factory=lambda: os.getenv("ATHENIX_REASONING_EFFORT", "low")
    )
    run_budget_usd: str = field(default_factory=lambda: os.getenv("ATHENIX_RUN_BUDGET_USD", "0.50"))
    # off (padrão): nenhuma chamada de rede; cached: só respostas já gravadas; live: chamada paga.
    ai_mode: str = field(default_factory=lambda: os.getenv("ATHENIX_AI_MODE", "off"))

    def prepare(self):
        if self.database_url == "sqlite:///.local/athenix.db":
            Path(".local").mkdir(exist_ok=True)


NOTICE = "Estudo experimental. Não é parecer jurídico, auditoria de conformidade ou certificação."
