"""Teste de tabelas: dicionário de dados do Auto de Infração (PDF) x CSV real.

Extrai a tabela com o pipeline do Athenix (pdfplumber, sem IA), compara os campos com as colunas do
CSV e mede a qualidade da extração. Uso (raiz do repositório):
  python scripts/testar_tabelas.py [--csv .local/dados_aneel/auto-infracao.csv]
Só resumo na saída: o CSV tem CPF/CNPJ de agentes e nenhuma linha dele é impressa.
"""

import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pdfplumber  # noqa: E402

from athenix.config import Settings  # noqa: E402
from athenix.poc import reader  # noqa: E402

DICIONARIO = ROOT / "tests/fontes_impacto/dados_abertos/dm-auto-de-infracao.pdf"
CAMPO = re.compile(r"^[A-Z][A-Za-z0-9]{3,}$")
TIPOS = {"Cadeia de caracteres": "texto", "Data Simples": "data", "Numérico": "numero"}


def _limpa(cell):
    return re.sub(r"\s+", " ", cell or "").strip()


def campos_do_pipeline(tabelas):
    """Uma linha por campo. Cada linha da tabela é lida pelas colunas não vazias, na ordem
    nome, tipo, [tamanho], descrição: o tamanho é opcional (datas não têm) e o cabeçalho de
    uma página pode ter colunas a mais que as linhas (célula mesclada)."""
    campos, descartadas = [], []
    for t in tabelas:
        for linha in t["rows"]:
            cel = [_limpa(c) for c in linha]
            cheias = [c for c in cel if c]
            if not cheias or not CAMPO.match(cheias[0]) or " " in cheias[0]:
                descartadas.append((t["id"], cheias))
                continue
            nome, resto = cheias[0], cheias[1:]
            tipo = resto[0] if resto else ""
            tamanho = resto[1] if len(resto) >= 3 else ""
            descricao = resto[-1] if len(resto) >= 2 else ""
            campos.append(
                {
                    "nome": nome,
                    "tipo": tipo,
                    "tamanho": tamanho,
                    "descricao": descricao,
                    "tabela": t["id"],
                    "colunas_cheias": len(cheias),
                }
            )
    return campos, descartadas


def campos_do_texto(path):
    """Segunda leitura independente: nomes de campo no texto corrido das páginas (sem tabelas)."""
    nomes = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for linha in (page.extract_text() or "").splitlines():
                primeiro = linha.split(" ")[0] if linha else ""
                if CAMPO.match(primeiro) and any(c.isupper() for c in primeiro[1:]):
                    nomes.append(primeiro)
    return nomes


def _palavras(texto):
    return re.findall(r"\w+", (texto or "").lower())


def fidelidade_e_alinhamento(path, tabelas):
    """Texto perdido ou inventado (palavras da área da tabela x palavras das células) e
    colunas desalinhadas em relação ao cabeçalho (célula mesclada)."""
    perdidas, inventadas, total, desalinhadas = [], [], 0, []
    with pdfplumber.open(path) as pdf:
        for t in tabelas:
            page = pdf.pages[t["page"] - 1]
            area = page.crop(t["bbox"], strict=False)
            no_pdf = _palavras(" ".join(w["text"] for w in area.extract_words()))
            nas_celulas = _palavras(" ".join(c or "" for linha in t["rows"] for c in linha))
            total += len(no_pdf)
            falta, sobra = list(no_pdf), []
            for p in nas_celulas:
                if p in falta:
                    falta.remove(p)
                else:
                    sobra.append(p)
            perdidas += [(t["id"], p) for p in falta]
            inventadas += [(t["id"], p) for p in sobra]
            cab = [_limpa(c) for c in t["rows"][0]]
            if any(c.startswith("Tamanho") for c in cab):
                i_cab = next(i for i, c in enumerate(cab) if c.startswith("Tamanho"))
                for linha in t["rows"][1:]:
                    onde = [i for i, c in enumerate(linha) if _limpa(c).replace(",", "").isdigit()]
                    if onde and onde[0] != i_cab:
                        desalinhadas.append((t["id"], _limpa(linha[0]), onde[0], i_cab))
    return {
        "palavras_no_pdf": total,
        "palavras_perdidas": perdidas,
        "palavras_a_mais": inventadas,
        "tamanho_fora_da_coluna_do_cabecalho": desalinhadas,
    }


def le_csv(path):
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            texto = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    return leitor.fieldnames, list(leitor), enc


def confere_dados(campo, linhas):
    """Tipo e tamanho declarados x valores reais da coluna."""
    valores = [(r.get(campo["nome"]) or "").strip() for r in linhas]
    nao_vazios = [v for v in valores if v]
    r = {"preenchidos": len(nao_vazios), "total": len(valores)}
    tipo = TIPOS.get(campo["tipo"])
    tam = campo["tamanho"]
    if tipo == "texto" and tam.isdigit() and nao_vazios:
        r["max_len"] = max(len(v) for v in nao_vazios)
        r["excede_tamanho"] = sum(len(v) > int(tam) for v in nao_vazios)
    elif tipo == "numero" and nao_vazios:
        bons = [v for v in nao_vazios if re.fullmatch(r"-?\d*([.,]\d+)?", v)]  # ",99" sem inteiro
        r["nao_numericos"] = len(nao_vazios) - len(bons)
        m = re.fullmatch(r"(\d+)(?:,(\d+))?", tam)
        if m and bons:
            inteiros = max(len(re.split(r"[.,]", v)[0].lstrip("-")) for v in bons)
            decimais = max(
                (len(re.split(r"[.,]", v)[1]) if re.search(r"[.,]", v) else 0) for v in bons
            )
            r["max_inteiros"], r["max_decimais"] = inteiros, decimais
            r["decimais_declaradas"] = int(m.group(2) or 0)
    elif tipo == "data" and nao_vazios:
        bons = [v for v in nao_vazios if re.match(r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}", v)]
        r["formato_data_invalido"] = len(nao_vazios) - len(bons)
        r["exemplo_formato"] = re.sub(r"\d", "9", nao_vazios[0])
    elif not tipo:
        r["tipo_desconhecido"] = campo["tipo"]
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(ROOT / ".local/dados_aneel/auto-infracao.csv"))
    ap.add_argument("--json", help="grava o detalhe completo neste caminho")
    a = ap.parse_args()

    r = reader.read_pdf(DICIONARIO, Settings())
    campos, descartadas = campos_do_pipeline(r["tables"])
    colunas, linhas, enc = le_csv(a.csv)
    do_texto = campos_do_texto(DICIONARIO)

    nomes = [c["nome"] for c in campos]
    dup = sorted({n for n in nomes if nomes.count(n) > 1})
    so_dic = [n for n in nomes if n not in colunas]
    so_csv = [c for c in colunas if c not in nomes]
    perdidos = [n for n in dict.fromkeys(do_texto) if n not in nomes]
    por_tabela = {}
    for c in campos:
        por_tabela[c["tabela"]] = por_tabela.get(c["tabela"], 0) + 1
    sem_tipo = [c["nome"] for c in campos if c["tipo"] not in TIPOS]
    sem_desc = [c["nome"] for c in campos if len(c["descricao"]) < 8]
    desc_outro_campo = [
        c["nome"]
        for c in campos
        if any(o != c["nome"] and o in c["descricao"] and CAMPO.match(o) for o in colunas)
    ]
    dados = {c["nome"]: confere_dados(c, linhas) for c in campos if c["nome"] in colunas}
    problemas_tipo = {
        n: d
        for n, d in dados.items()
        if d.get("excede_tamanho") or d.get("nao_numericos") or d.get("formato_data_invalido")
    }
    ordem_igual = [n for n in colunas if n in nomes] == [n for n in nomes if n in colunas]

    resumo = {
        "csv": {"colunas": len(colunas), "linhas": len(linhas), "codificacao": enc},
        "dicionario": {
            "campos_pipeline": len(campos),
            "por_tabela": por_tabela,
            "linhas_descartadas": [(t, c) for t, c in descartadas],
            "nomes_so_no_texto_corrido": perdidos,
            "duplicados": dup,
        },
        "comparacao": {
            "no_dicionario_e_nao_no_csv": so_dic,
            "no_csv_e_nao_no_dicionario": so_csv,
            "mesma_ordem": ordem_igual,
        },
        "celulas": {
            **fidelidade_e_alinhamento(DICIONARIO, r["tables"]),
            "tabelas_por_pagina": {t["id"]: len(t["rows"]) for t in r["tables"]},
            "cabecalho_repetido_nas_paginas_seguintes": [
                t["id"] for t in r["tables"][1:] if _limpa(t["rows"][0][0]) == "Nome do Campo"
            ],
        },
        "qualidade": {
            "sem_tipo_reconhecido": sem_tipo,
            "descricao_vazia_ou_curta": sem_desc,
            "descricao_cita_outro_campo": desc_outro_campo,
            "tipo_ou_tamanho_nao_bate_com_dados": problemas_tipo,
        },
    }
    print(json.dumps(resumo, ensure_ascii=False, indent=1))
    if a.json:
        Path(a.json).write_text(
            json.dumps({"campos": campos, "dados": dados, **resumo}, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
