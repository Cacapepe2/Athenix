"""Configura a IA (Azure OpenAI / Microsoft Foundry) no arquivo .env, sem a chave passar por outro lugar.

Uso (no seu terminal):  python scripts/configurar_ia.py

- Pergunta cada valor; a chave é digitada com entrada oculta (não aparece na tela).
- Grava no .env da raiz do projeto (cria a partir do .env.example se não existir). Outras linhas e
  variáveis do arquivo ficam como estão.
- Deixa ATHENIX_AI_MODE=off: nenhuma chamada paga acontece por causa desta configuração.
- No fim mostra só "presente/ausente" de cada variável e a chave mascarada (4 últimos caracteres).
Enter numa pergunta mantém o valor atual (mostrado entre colchetes; a chave nunca é mostrada).
"""

import getpass
import re
import subprocess
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"
EXEMPLO = ROOT / ".env.example"
CHAVE = "ATHENIX_API_KEY"
VARIAVEIS = [
    "ATHENIX_AI_MODE",
    "ATHENIX_AZURE_ENDPOINT",
    CHAVE,
    "ATHENIX_MODEL",
    "ATHENIX_AZURE_API_VERSION",
    "ATHENIX_REASONING_EFFORT",
    "ATHENIX_INPUT_USD_M",
    "ATHENIX_OUTPUT_USD_M",
    "ATHENIX_PRICE_SOURCE",
    "ATHENIX_PRICE_DATE",
    "ATHENIX_RUN_BUDGET_USD",
]
FICTICIOS = {"https://exemplo-recurso.openai.azure.com", "exemplo-deployment", "0.00"}


def ler(path):
    """Valores ATHENIX_* já gravados (só para sugerir o atual; a chave nunca é exibida)."""
    if not Path(path).is_file():
        return {}
    valores = {}
    for linha in Path(path).read_text(encoding="utf-8-sig").splitlines():
        if "=" in linha and not linha.lstrip().startswith("#"):
            nome, valor = (p.strip() for p in linha.split("=", 1))
            if nome.startswith("ATHENIX_"):
                valores[nome] = valor.strip("\"'")
    return valores


def gravar(path, novos):
    """Atualiza as variáveis no arquivo, preservando comentários, ordem e as demais linhas."""
    path = Path(path)
    linhas = path.read_text(encoding="utf-8-sig").splitlines() if path.is_file() else []
    faltam = dict(novos)
    for i, linha in enumerate(linhas):
        nome = linha.split("=", 1)[0].strip()
        if "=" in linha and not linha.lstrip().startswith("#") and nome in faltam:
            linhas[i] = f"{nome}={faltam.pop(nome)}"
    linhas += [f"{n}={v}" for n, v in faltam.items()]
    path.write_text("\n".join(linhas) + "\n", encoding="utf-8", newline="\n")


def mascarar(valor):
    return f"…{valor[-4:]}" if valor and len(valor) >= 8 else ("(curta demais)" if valor else "")


def separar_uri(texto):
    """Do "Target URI" do Foundry tira a base, o deployment e a api-version, se vierem juntos."""
    url = urlparse(texto.strip())
    base = f"{url.scheme}://{url.netloc}" if url.scheme and url.netloc else texto.strip()
    m = re.search(r"/deployments/([^/]+)/", url.path + "/")
    versao = parse_qs(url.query).get("api-version", [None])[0]
    return base, (m.group(1) if m else None), versao


def validar(nome, valor):
    """Mensagem de erro, ou None se o valor serve."""
    if nome == "ATHENIX_AZURE_ENDPOINT":
        valor = separar_uri(valor)[0]  # aceita o Target URI inteiro
        ok = re.fullmatch(r"https://[a-z0-9-]+\.(openai\.azure\.com|cognitiveservices\.azure\.com|services\.ai\.azure\.com)", valor)  # fmt: skip
        return None if ok else "use a base do endpoint, ex.: https://meu-recurso.openai.azure.com"
    if nome == CHAVE:
        return None if len(valor) >= 20 and " " not in valor else "a chave parece incompleta"
    if nome == "ATHENIX_MODEL":
        return None if re.fullmatch(r"[A-Za-z0-9._-]+", valor) else "use o nome do deployment"
    if nome == "ATHENIX_AZURE_API_VERSION":
        ok = re.fullmatch(r"\d{4}-\d{2}-\d{2}(-preview)?", valor)
        return None if ok else "formato AAAA-MM-DD ou AAAA-MM-DD-preview"
    if nome == "ATHENIX_REASONING_EFFORT":
        return None if valor in {"", "low", "medium", "high"} else "low, medium, high ou vazio"
    if nome in {"ATHENIX_INPUT_USD_M", "ATHENIX_OUTPUT_USD_M", "ATHENIX_RUN_BUDGET_USD"}:
        try:
            ok = Decimal(valor) > 0 and Decimal(valor).is_finite()
        except InvalidOperation:
            ok = False
        return None if ok else "número maior que zero, com ponto (ex.: 2.00)"
    if nome == "ATHENIX_PRICE_SOURCE":
        return None if valor.startswith("https://") else "endereço da página de preço (https://...)"
    if nome == "ATHENIX_PRICE_DATE":
        try:
            ok = date.fromisoformat(valor) <= date.today()
        except ValueError:
            ok = False
        return None if ok else "data AAAA-MM-DD, até hoje"
    return None


PERGUNTAS = {
    "ATHENIX_AZURE_ENDPOINT": "Endpoint (pode colar o Target URI inteiro do deployment)",
    "ATHENIX_MODEL": "Nome do deployment",
    "ATHENIX_AZURE_API_VERSION": "Versão da API",
    "ATHENIX_REASONING_EFFORT": "Esforço de raciocínio (low/medium/high; '-' = vazio, modelo sem raciocínio)",
    "ATHENIX_INPUT_USD_M": "Preço de ENTRADA em US$ por 1 milhão de tokens",
    "ATHENIX_OUTPUT_USD_M": "Preço de SAÍDA em US$ por 1 milhão de tokens",
    "ATHENIX_PRICE_SOURCE": "Página de onde tirou o preço (https://...)",
    "ATHENIX_PRICE_DATE": "Data em que consultou o preço (AAAA-MM-DD)",
    "ATHENIX_RUN_BUDGET_USD": "Teto de custo por execução, em US$",
}


def perguntar(nome, atual, sugestao=None):
    padrao = sugestao or (atual if atual not in FICTICIOS else "")
    while True:
        valor = input(f"{PERGUNTAS[nome]} [{padrao}]: ").strip() or padrao
        if nome == "ATHENIX_REASONING_EFFORT" and valor == "-":
            valor = ""
        if (erro := validar(nome, valor)) is None:
            return valor
        print(f"  ✗ {erro}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if not ENV.exists():
        ENV.write_text(EXEMPLO.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        print(f"Criado {ENV.name} a partir de {EXEMPLO.name}.")
    atual = ler(ENV)
    novos = {"ATHENIX_AI_MODE": "off"}
    endpoint = perguntar("ATHENIX_AZURE_ENDPOINT", atual.get("ATHENIX_AZURE_ENDPOINT", ""))
    novos["ATHENIX_AZURE_ENDPOINT"], deployment, versao = separar_uri(endpoint)
    while True:
        tem = bool(atual.get(CHAVE))
        chave = getpass.getpass(
            "Chave (KEY 1), entrada oculta" + (" [Enter mantém a atual]" if tem else "") + ": "
        ).strip()
        if not chave and tem:
            break
        if (erro := validar(CHAVE, chave)) is None:
            novos[CHAVE] = chave
            break
        print(f"  ✗ {erro}")
    novos["ATHENIX_MODEL"] = perguntar("ATHENIX_MODEL", atual.get("ATHENIX_MODEL", ""), deployment)
    novos["ATHENIX_AZURE_API_VERSION"] = perguntar(
        "ATHENIX_AZURE_API_VERSION", atual.get("ATHENIX_AZURE_API_VERSION", "2025-04-01-preview"), versao
    )  # fmt: skip
    novos["ATHENIX_REASONING_EFFORT"] = perguntar("ATHENIX_REASONING_EFFORT", atual.get("ATHENIX_REASONING_EFFORT", "low"))  # fmt: skip
    for nome in ("ATHENIX_INPUT_USD_M", "ATHENIX_OUTPUT_USD_M", "ATHENIX_PRICE_SOURCE"):
        novos[nome] = perguntar(nome, atual.get(nome, ""))
    novos["ATHENIX_PRICE_DATE"] = perguntar("ATHENIX_PRICE_DATE", atual.get("ATHENIX_PRICE_DATE", ""), date.today().isoformat())  # fmt: skip
    novos["ATHENIX_RUN_BUDGET_USD"] = perguntar("ATHENIX_RUN_BUDGET_USD", atual.get("ATHENIX_RUN_BUDGET_USD", "0.50"))  # fmt: skip
    gravar(ENV, novos)
    final = ler(ENV)
    print("\nGravado em .env (ATHENIX_AI_MODE=off: nenhuma chamada será feita por causa disto).")
    for nome in VARIAVEIS:
        presente = "presente" if final.get(nome) else "ausente"
        extra = f"  {mascarar(final[nome])}" if nome == CHAVE and final.get(nome) else ""
        print(f"  {nome:28} {presente}{extra}")
    ignorado = subprocess.run(["git", "check-ignore", "-q", str(ENV)], cwd=ROOT).returncode == 0
    print("\n.env ignorado pelo git: " + ("sim" if ignorado else "NÃO — não faça commit; avise"))


if __name__ == "__main__":
    main()
