"""Demonstração local em um comando: banco próprio, usuário de demonstração e a RN 1.137 já
processada por regras (sem IA, sem chave, sem rede)."""

import secrets
from pathlib import Path

from .auth import create_user
from .db import database, initialize
from .services import enqueue, receive, run_one

ROOT = Path(__file__).resolve().parents[1]
NORMA = ROOT / "tests" / "norma_poc" / "ren20251137.pdf"
BANCO = ROOT / ".local" / "demo.db"
USUARIO = "demo"


def preparar(settings, banco=BANCO, norma=NORMA, titulo="RN ANEEL 1.137/2025", origem=None):
    """Recria o banco da demo (só `banco`, por padrão .local/demo.db), cria o usuário e processa
    a norma (por padrão, a RN 1.137; `norma` aceita outro PDF ou HTML versionado).

    Devolve a senha, gerada a cada execução: nenhuma credencial fica no repositório.
    """
    banco.parent.mkdir(exist_ok=True)
    for antigo in banco.parent.glob(banco.name + "*"):
        antigo.unlink()
    settings.database_url = "sqlite:///" + banco.as_posix()
    engine, factory = database(settings.database_url)
    initialize(engine)
    senha = secrets.token_urlsafe(12)
    with factory.begin() as session:
        user = create_user(session, USUARIO, senha)
        document, _ = receive(
            session,
            settings,
            Path(norma).read_bytes(),
            titulo,
            origem or "tests/norma_poc/ren20251137.pdf (PDF da norma publicado pela ANEEL)",
            "norm",
            "",
            user.id,
        )
        user_id, document_id = user.id, document.id
    while run_one(factory, settings):
        pass
    with factory.begin() as session:
        enqueue(session, document_id, "rules", user_id, settings)
    while run_one(factory, settings):
        pass
    engine.dispose()
    return senha
