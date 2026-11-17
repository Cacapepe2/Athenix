"""Fontes do módulo de impacto (REN 846 e alteradoras): integridade e estrutura citável."""

import hashlib
import json
from pathlib import Path

import pytest

from athenix.config import Settings
from athenix.poc import reader
from athenix.structure import segment
from scripts.extrair_parametros import fonte

DIR = Path(__file__).parent / "fontes_impacto"
AGUARDANDO = (
    "REN 846 não encontrada em tests/fontes_impacto/ (versão oficial) nem em .local/fontes_impacto/ "
    "(cópia local, fora do repositório): aguardando o arquivo oficial da ANEEL"
)
SEM_PDF = pytest.mark.skipif(not fonte("ren2019846_compilada.pdf").exists(), reason=AGUARDANDO)


def test_hashes_match_provenance():
    docs = json.loads((DIR / "fontes.json").read_text(encoding="utf-8"))["documentos"]
    present = [d for d in docs if fonte(d["arquivo"]).exists()]
    assert any(d["id"] == "lei9427" for d in present)  # fonte oficial versionada: nunca falta
    for doc in present:
        assert hashlib.sha256(fonte(doc["arquivo"]).read_bytes()).hexdigest() == doc["sha256"]
    if missing := [d["arquivo"] for d in docs if d not in present]:
        pytest.skip(f"{AGUARDANDO} ({', '.join(missing)})")


def test_legal_cap_is_the_current_wording_of_law_9427():
    # Texto compilado do planalto.gov.br (sha256 ff948e34…): a redação de 2% está riscada.
    from scripts.extrair_parametros import read, teto_legal

    p = teto_legal(read("9427"))
    assert p["ancora"] == "verified" and not p["revogado"]
    assert p["percentuais"] == [3.0] and "3% (três por cento) do faturamento" in p["trecho"]
    assert p["redacao_dada_por"] == "Lei nº 15.269, de 2025"


def test_lowercase_art_at_line_start_is_a_remission_not_an_article():
    text = (
        "Art. 16. Constitui infração:\n"
        "I - a realização de obras, observado o disposto no\n"
        "art. 8º da Lei nº 9.074, de 7 de julho de 1995; e\n"
        "§ 1º O descumprimento implicará multa diária.\n"
    )
    units, _ = segment(text, [{"number": 1, "start": 0, "end": len(text)}])
    by_id = {u["id"]: u for u in units}
    assert [u["label"] for u in units if u["kind"] == "article"] == ["16"]
    paragraph = next(u for u in units if u["label"] == "§ 1º")
    assert by_id[paragraph["parent"]]["label"] == "16"


def test_paragraph_sign_followed_by_connector_is_a_remission_not_a_paragraph():
    # Lei 9.427/1996 no planalto.gov.br: antes, "§ 6 o do art. 15" virava parágrafo e os incisos
    # VII a XXII do Art. 3º eram citados como "Art. 3º, § 6º, X".
    text = (
        "Art. 3º Compete à ANEEL:\n"
        "V - dirimir as divergências, na forma do\n"
        "§ 6 o do art. 15 da Lei n o 9.074, de 7 de julho de 1995;\n"
        "X - fixar as multas administrativas.\n"
        "§ 1 o No exercício da competência prevista nos incisos VIII e IX.\n"
        "§ 2º A ANEEL deverá articular-se com a Secretaria.\n"
    )
    units, _ = segment(text, [{"number": 1, "start": 0, "end": len(text)}])
    by_id = {u["id"]: u for u in units}
    assert [u["label"] for u in units if u["kind"] == "paragraph"] == ["§ 1", "§ 2º"]
    inciso = next(u for u in units if u["label"] == "X")
    assert by_id[inciso["parent"]]["label"] == "3º"


@pytest.fixture(scope="module")
def ren846():
    read = reader.read_pdf(fonte("ren2019846_compilada.pdf"), Settings())
    units = read["extraction"]["units"]
    return units, {u["id"]: u for u in units}


@SEM_PDF
def test_real_embargo_daily_fine_is_cited_under_art_16(ren846):
    units, by_id = ren846
    # Antes: "art. 8º da Lei nº 9.074" virava artigo e o § 1º do Art. 16 era citado como "Art. 8º § 1º".
    unit = next(
        u
        for u in units
        if u["text"].startswith("§ 1º Na hipótese da aplicação das penalidades de embargo")
    )
    assert by_id[unit["parent"]]["label"] == "16"
    assert [u["label"] for u in units if u["kind"] == "article"].count("8º") == 1


@pytest.mark.parametrize(
    "text,value",
    [
        ("cento e vinte e cinco milésimos por cento", 0.125),
        ("vinte e cinco centésimos por cento", 0.25),
        ("cinco décimos por cento", 0.5),
        ("zero vírgula zero um por cento", 0.01),
        ("zero vírgula vinte e cinco por cento", 0.25),
        ("cento e vinte por cento", 120),
    ],
)
def test_spelled_percentages(text, value):
    from scripts.extrair_parametros import spelled

    assert spelled(text) == pytest.approx(value)


def test_digits_vs_words_mismatch_is_flagged():
    from scripts.extrair_parametros import mismatches

    # Texto real da REN 846 compilada, Art. 45-I, § 4º.
    assert mismatches("Será acrescido o valor de 25% (cinco por cento) para cada antecedente")
    assert not mismatches("I - 40% (quarenta por cento) para cada caso de reincidência")
    assert not mismatches("III - de 1% a 5% (um a cinco por cento) para cada caso")
