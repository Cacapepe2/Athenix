"""Capturas da tela de impacto e da 1ª página do relatório com a RN 1.137 (navegador real).

Uso: python scripts/capturar_impacto.py      # requer requirements-qa.txt (Playwright)
Sobe o app com banco descartável, cria conta local, envia tests/norma_poc/ren20251137.pdf, roda a
extração por regras (sem IA) e grava em docs/telas/:
  1_impacto_topo.png          tela de impacto, perfil transmissora
  2_impacto_prioridade.png    lista completa priorizada (perfil transmissora)
  3_impacto_perfil_vazio.png  tela de impacto sem perfil
  4_relatorio.png             1ª página do relatório em A4 (impressão do navegador)
e o PDF do relatório em docs/exemplos/relatorio_impacto_rn1137.pdf.
Usa o Edge do sistema quando existir; senão, o Chromium do Playwright.
"""

import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import pypdfium2
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
NORMA = ROOT / "tests" / "norma_poc" / "ren20251137.pdf"
TELAS = ROOT / "docs" / "telas"
PDF = ROOT / "docs" / "exemplos" / "relatorio_impacto_rn1137.pdf"
PERFIL = "segmento=transmissao&data_referencia=2026-11-17"


def esperar(condicao, segundos, erro):
    limite = time.monotonic() + segundos
    while not (resultado := condicao()):
        if time.monotonic() > limite:
            raise RuntimeError(erro)
        time.sleep(0.3)
    return resultado


def navegador(playwright):
    try:
        return playwright.chromium.launch(channel="msedge")
    except Exception:
        return playwright.chromium.launch()


def main():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="athenix-telas-", ignore_cleanup_errors=True) as tmp:
        env = os.environ | {
            "ATHENIX_DATABASE_URL": "sqlite:///" + (Path(tmp) / "telas.db").as_posix(),
            "ATHENIX_API_KEY": "",
            "ATHENIX_MODEL": "",
        }
        server = subprocess.Popen(
            [sys.executable, "-m", "athenix", "serve", "--port", str(port)],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:

            def pronto():
                try:
                    return httpx.get(url + "/health").status_code == 200
                except httpx.HTTPError:
                    return False

            esperar(pronto, 30, "Servidor não ficou pronto.")
            with sync_playwright() as playwright:
                browser = navegador(playwright)
                context = browser.new_context(viewport={"width": 1440, "height": 1000})
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(url + "/login")
                senha = secrets.token_urlsafe(24)
                page.get_by_label("Usuário", exact=True).fill("demo-local")
                page.get_by_label("Senha", exact=False).fill(senha)
                page.get_by_role("button", name="Criar conta técnica").click()
                page.get_by_label("Usuário", exact=True).fill("demo-local")
                page.get_by_label("Senha", exact=True).fill(senha)
                page.get_by_role("button", name="Entrar", exact=True).click()
                api = context.request
                csrf = api.post(
                    url + "/api/login", data={"username": "demo-local", "password": senha}
                ).json()["csrf"]
                headers = {"x-csrf-token": csrf}
                doc = api.post(
                    url + "/api/documents",
                    headers=headers,
                    multipart={
                        "file": {
                            "name": NORMA.name,
                            "mimeType": "application/pdf",
                            "buffer": NORMA.read_bytes(),
                        },
                        "title": "RN ANEEL 1.137/2025",
                        "origin": "tests/norma_poc/ren20251137.pdf",
                        "role": "norm",
                    },
                ).json()
                esperar(  # 400 "ainda não estruturado" enquanto a fila processa
                    lambda: api.get(f"{url}/api/documents/{doc['id']}").ok,
                    90,
                    "Documento não foi processado.",
                )
                run = api.post(
                    f"{url}/api/documents/{doc['id']}/runs", headers=headers, data={"kind": "rules"}
                ).json()
                esperar(
                    lambda: (
                        api.get(f"{url}/api/runs/{run['id']}").json()["state"]
                        not in {"queued", "running"}
                    ),
                    120,
                    "Extração por regras não terminou.",
                )
                total = api.get(url + "/api/obligations").json()["count"]
                assert total, "Nenhuma obrigação extraída."

                TELAS.mkdir(parents=True, exist_ok=True)
                page.goto(f"{url}/impacto?{PERFIL}")
                page.screenshot(path=str(TELAS / "1_impacto_topo.png"))
                page.get_by_role("heading", name="Obrigações priorizadas").evaluate(
                    "e => e.scrollIntoView({block: 'start'})"
                )
                page.screenshot(path=str(TELAS / "2_impacto_prioridade.png"))
                page.goto(f"{url}/impacto?data_referencia=2026-11-17")
                page.get_by_role("heading", name="Perfil da empresa").scroll_into_view_if_needed()
                page.screenshot(path=str(TELAS / "3_impacto_perfil_vazio.png"))

                page.goto(f"{url}/impacto/relatorio?{PERFIL}")
                page.emulate_media(media="print")
                PDF.parent.mkdir(parents=True, exist_ok=True)
                page.pdf(path=str(PDF), format="A4", print_background=True,
                         margin={"top": "12mm", "bottom": "12mm", "left": "10mm", "right": "10mm"})  # fmt: skip
                pdf = pypdfium2.PdfDocument(str(PDF))
                try:
                    paginas = len(pdf)
                    pdf[0].render(scale=1.6).to_pil().save(TELAS / "4_relatorio.png")
                finally:
                    pdf.close()
                browser.close()
                if errors:
                    raise RuntimeError(f"Erros de JavaScript: {errors}")
                print(
                    f"{total} obrigações; relatório com {paginas} páginas A4; capturas em {TELAS}"
                )
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == "__main__":
    main()
