"""Mapa de robustez: roda os invariantes de saúde (athenix/saude.py) no corpus e grava tabela e detalhes.

Uso: python scripts/avaliar_corpus.py [--saida artifacts/corpus]
Corpus: tests/corpus_planalto/ (16 atos do planalto), documentos já versionados e, se existirem, as
cópias locais em .local/fontes_impacto/ (fora do repositório). Documento ausente aparece na tabela.
"""

import hashlib
import json
import sys
from pathlib import Path

import argparse  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
CORPUS = REPO / "tests" / "corpus_planalto"
_args = argparse.ArgumentParser()
_args.add_argument("--saida", default=str(REPO / "artifacts" / "corpus"))
SAIDA = Path(_args.parse_args().saida)
sys.path.insert(0, str(REPO))
from athenix import saude  # noqa: E402
from athenix.config import Settings  # noqa: E402
from athenix.poc import reader  # noqa: E402
from athenix.structure import extract  # noqa: E402

R = REPO
DOCS = [
    ("Lei 8.987/1995 (concessões)", "Planalto · HTML", CORPUS / "l8987.htm"),
    ("Lei 9.074/1995 (concessões e permissões)", "Planalto · HTML", CORPUS / "l9074.htm"),
    ("Lei 9.427/1996 (ANEEL)", "Planalto · HTML", R / "tests/fontes_impacto/l9427cons.htm"),
    ("Lei 9.478/1997 (política energética)", "Planalto · HTML", CORPUS / "l9478.htm"),
    ("Lei 9.648/1998", "Planalto · HTML", R / "tests/fontes_impacto/l9648cons.htm"),
    ("Lei 9.991/2000 (P&D e eficiência)", "Planalto · HTML", CORPUS / "l9991.htm"),
    ("Lei 10.438/2002 (Proinfa, CDE)", "Planalto · HTML", CORPUS / "l10438.htm"),
    ("Lei 10.848/2004 (comercialização)", "Planalto · HTML", CORPUS / "l10848.htm"),
    ("Lei 12.783/2013 (renovação de concessões)", "Planalto · HTML", CORPUS / "l12783.htm"),
    ("Lei 13.360/2016", "Planalto · HTML", CORPUS / "l13360.htm"),
    ("Lei 13.848/2019 (agências reguladoras)", "Planalto · HTML", CORPUS / "l13848.htm"),
    ("Lei 14.120/2021", "Planalto · HTML", CORPUS / "l14120.htm"),
    ("Lei 14.182/2021 (Eletrobras)", "Planalto · HTML", CORPUS / "l14182.htm"),
    ("Lei 14.300/2022 (micro e minigeração)", "Planalto · HTML", CORPUS / "l14300.htm"),
    ("Lei 15.269/2025", "Planalto · HTML", R / "tests/fontes_impacto/l15269.htm"),
    ("Decreto 2.335/1997 (estrutura da ANEEL)", "Planalto · HTML", CORPUS / "d2335.htm"),
    ("Decreto 5.163/2004 (comercialização)", "Planalto · HTML", CORPUS / "d5163.htm"),
    ("Decreto 7.246/2010 (sistemas isolados)", "Planalto · HTML", CORPUS / "d7246.htm"),
    ("Decreto 10.946/2022 (eólica offshore)", "Planalto · HTML", CORPUS / "d10946.htm"),
    ("Decreto 12.068/2024", "Planalto · HTML", R / "tests/gabarito/D12068.htm"),
    ("RN ANEEL 1.137/2025", "ANEEL · PDF", R / "tests/norma_poc/ren20251137.pdf"),
    ("RN 1.137/2025 no DOU", "DOU · PDF", R / "tests/norma_poc/dou.pdf"),
    ("REH ANEEL 3.348/2024", "Cópia de terceiro (ISA) · PDF", R / "tests/gabarito/reh20243348.pdf"),
    (
        "REN ANEEL 846/2019 compilada",
        "Biblioteca da ANEEL · PDF",
        R / "tests/fontes_impacto/atren2019846.pdf",
    ),
    (
        "REN ANEEL 1.148/2026",
        "Biblioteca da ANEEL · PDF",
        R / "tests/fontes_impacto/ren20261148.pdf",
    ),
    (
        "REN ANEEL 1.174/2026 compilada",
        "Cópia local (Leis.org) · PDF",
        R / ".local/fontes_impacto/ren20261174.pdf",
    ),
]

linhas, detalhes = [], []
for nome, origem, caminho in DOCS:
    if not caminho.exists():
        linhas.append((nome, origem, None, "arquivo ausente", "", 0, 0))
        continue
    conteudo = caminho.read_bytes()
    try:
        if caminho.suffix == ".pdf":
            extracao = reader.read_pdf(caminho, Settings())["extraction"]
        else:
            extracao = extract(conteudo, "text/html", Settings(), "norm")
    except Exception as erro:  # registra e segue: o mapa precisa de todos
        linhas.append(
            (nome, origem, 0, "falha na extração", f"{type(erro).__name__}: {erro}"[:160], 0, 0)
        )
        continue
    r = saude.avaliar(extracao)
    principais = sorted(r["alertas"], key=lambda a: -a["penalidade"])[:3]
    resumo = (
        " / ".join(
            a["mensagem"]
            + (
                f" Ex.: {'; '.join(a['exemplos'][:2])}"
                if a["exemplos"] and a["tipo"] != "ocr"
                else ""
            )
            for a in principais
        )
        or "nenhum"
    )
    linhas.append(
        (
            nome,
            origem,
            r["nota"],
            r["situacao"],
            resumo,
            r["metricas"]["dispositivos"],
            r["metricas"]["cobertura"],
        )
    )
    detalhes.append(
        {"documento": nome, "origem": origem, "sha256": hashlib.sha256(conteudo).hexdigest(), **r}
    )

linhas.sort(key=lambda x: (x[2] is None, x[2] if x[2] is not None else 0))
md = [
    "| Documento | Fonte | Nota | Situação | Dispositivos | Cobertura | Principais alertas |",
    "| --- | --- | ---: | --- | ---: | ---: | --- |",
]
for nome, origem, nota, sit, resumo, n, cob in linhas:
    md.append(
        f"| {nome} | {origem} | {nota if nota is not None else '—'} | {sit} | {n} | {cob:.0%} | {resumo.replace('|', '/')} |"
    )
SAIDA.mkdir(parents=True, exist_ok=True)
(SAIDA / "corpus_saude.md").write_text("\n".join(md) + "\n", encoding="utf-8")
(SAIDA / "corpus_saude.json").write_text(
    json.dumps(detalhes, ensure_ascii=False, indent=1), encoding="utf-8"
)
notas = [x[2] for x in linhas if isinstance(x[2], int)]
print(
    f"{len(linhas)} documentos; média {sum(notas) / len(notas):.0f}; abaixo de {saude.LIMITE}: {sum(n < saude.LIMITE for n in notas)}"
)
