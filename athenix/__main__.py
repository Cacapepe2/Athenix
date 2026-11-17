import argparse
import getpass
import json
import sys
import time

from .auth import create_user
from .config import Settings, carregar_env
from .db import database, initialize, verify_chain
from .llm import modo


def main():
    parser = argparse.ArgumentParser(
        description="Athenix — inteligência regulatória com evidências"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve", help="Servidor local com trabalhador integrado")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--no-worker", action="store_true")
    demo = sub.add_parser(
        "demo", help="Demonstração local: RN 1.137 já processada, usuário de demo, sem IA"
    )
    demo.add_argument("--port", type=int, default=8000)
    sub.add_parser("worker", help="Trabalhador separado da fila persistente")
    sub.add_parser("verify", help="Conferir trilha")
    user = sub.add_parser(
        "create-user", help="Provisionar conta; papel jurídico exige verificação externa"
    )
    user.add_argument("username")
    user.add_argument("--role", choices=["operator", "technical", "legal"], default="technical")
    poc = sub.add_parser("poc", help="Extração, comparação e estruturação da norma de PoC")
    poc.add_argument("--a", default="tests/norma_poc/ren20251137.pdf")
    poc.add_argument("--b", default="tests/norma_poc/dou.pdf")
    poc.add_argument("--out", default="artifacts/poc")
    poc.add_argument("--ocr", choices=["none", "docling"], default="none")
    poc.add_argument("--ai", action="store_true", help="Usa o modelo configurado (Azure), com teto")
    args = parser.parse_args()
    carregar_env()  # .env local (fora do git); variáveis já definidas no ambiente prevalecem
    # Console do Windows (cp1252/cp850) ou saída redirecionada: caractere sem mapa vira "?", não erro.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    settings = Settings()
    settings.prepare()
    ia = modo(settings)
    if args.command in {"serve", "worker", "demo", "poc"}:
        pedido = f" (pedido: {ia['pedido']})" if ia["pedido"] != ia["efetivo"] else ""
        print(f"Modo de IA: {ia['efetivo']}{pedido}: {ia['motivo']}.", flush=True)
    if args.command == "demo":
        import uvicorn

        from .app import create_app
        from .demo import USUARIO, preparar

        print("Preparando a demo (banco .local/demo.db, RN 1.137 por regras)...", flush=True)
        senha = preparar(settings)
        url = f"http://127.0.0.1:{args.port}"
        print(
            f"\nPronto. Abra {url}/login e entre com\n"
            f"  usuário: {USUARIO}\n"
            f"  senha:   {senha}\n"
            f"Roteiro: Obrigações ({url}/matrix) -> Impacto com perfil ilustrativo "
            f"({url}/impacto?perfil=ilustrativo) -> Exportar relatório.\n"
            "Ctrl+C encerra. A senha muda a cada execução.\n",
            flush=True,
        )
        uvicorn.run(create_app(settings), host="127.0.0.1", port=args.port, access_log=False)
        return
    if args.command == "poc":
        from .poc.run import run

        ocr = None
        if args.ocr == "docling":
            from pathlib import Path

            from .poc.ocr import docling_ocr

            def ocr(path, pages):
                images = Path(args.out) / "pages" / Path(path).stem
                return docling_ocr(path, pages, cache_dir=args.out, images_dir=images)

        result = run(args.a, args.b, args.out, settings, ocr=ocr, ai=args.ai)
        print(json.dumps({"comparison": result["comparison"], "log": result["log"]["ai"]}))
        return
    if args.command == "serve":
        import uvicorn
        from .app import create_app

        uvicorn.run(
            create_app(settings, embedded_worker=not args.no_worker),
            host=args.host,
            port=args.port,
            access_log=False,
        )
        return
    engine, factory = database(settings.database_url)
    initialize(engine)
    if args.command == "create-user":
        password = getpass.getpass("Senha (mínimo 12 caracteres): ")
        if password != getpass.getpass("Confirme a senha: "):
            raise SystemExit("Senhas diferentes.")
        with factory.begin() as session:
            create_user(session, args.username, password, args.role)
        print("Conta provisionada. A atribuição de papel não comprova qualificação profissional.")
    elif args.command == "verify":
        with factory() as session:
            print(verify_chain(session))
    else:
        from .services import recover_stale, run_one

        recover_stale(factory)
        try:
            while True:
                if not run_one(factory, settings):
                    time.sleep(0.5)
        except KeyboardInterrupt:
            pass
    engine.dispose()


if __name__ == "__main__":
    main()
