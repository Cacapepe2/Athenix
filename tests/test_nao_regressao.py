"""Trava de não regressão: nenhuma métrica do gabarito pode piorar em relação à linha de base.

Melhorias atualizam `tests/baseline/metricas_v1.json` só em commit próprio, explicando o porquê:
python scripts/avaliar.py --congelar tests/baseline/metricas_v1.json
"""

import copy
import json
from pathlib import Path

import pytest

from scripts import avaliar

BASE = Path(__file__).parent / "baseline" / "metricas_v1.json"


@pytest.fixture(scope="module")
def base():
    return json.loads(BASE.read_text(encoding="utf-8"))


def piorar(base, mudanca):
    atual = copy.deepcopy(base)
    mudanca(atual)
    return avaliar.regressoes(atual, base)


def test_baseline_freezes_the_agreed_numbers(base):
    por = base["por_verificacao"]
    assert (base["casos_totalmente_corretos"], base["total_casos"]) == (19, 20)
    assert [
        (por[k]["acertos"], por[k]["total"]) for k in ("obrigacao", "prazo", "autoria", "vigencia")
    ] == [
        (11, 11),
        (8, 8),
        (10, 10),
        (4, 4),
    ]
    assert {d: m["falsas_verificadas"] for d, m in base["por_documento"].items()} == {
        "ren20251137": 0,
        "reh20243348": 0,
        "dec12068": 0,
    }


def test_guard_flags_each_kind_of_regression(base):
    doc = "ren20251137"
    assert avaliar.regressoes(base, base) == []
    piora = {
        "casos corretos": lambda a: a.update(casos_totalmente_corretos=18),
        "verificação": lambda a: a["por_verificacao"]["prazo"].update(acertos=7),
        "falsa verificada": lambda a: a["por_documento"][doc].update(falsas_verificadas=1),
        "citação some da fonte": lambda a: a["por_documento"][doc].update(citacoes_encontradas=251),
        "citação não encontrada": lambda a: a["por_documento"][doc].update(nao_encontradas=3),
        "prazo duplicado": lambda a: a["por_documento"][doc].update(prazos_duplicados=1),
        "sujeito com rótulo": lambda a: a["por_documento"][doc].update(sujeitos_com_rotulo=1),
        "documento some": lambda a: a["por_documento"].pop(doc),
        "gabarito mudou de tamanho": lambda a: a.update(total_casos=21),
        "verificação some": lambda a: a["por_verificacao"].pop("autoria"),
    }
    for nome, mudanca in piora.items():
        assert piorar(base, mudanca), nome


def test_guard_accepts_improvements_and_new_checks(base):
    def melhora(a):
        a["casos_totalmente_corretos"] = 20
        a["por_verificacao"]["remissao"]["acertos"] = 1
        a["por_verificacao"]["nova"] = {"acertos": 0, "total": 3}
        a["por_documento"]["ren20251137"].update(nao_encontradas=0, citacoes_encontradas=254)

    assert piorar(base, melhora) == []


def test_current_pipeline_does_not_regress(base):
    atual = avaliar.metricas(avaliar.evaluate())
    assert avaliar.regressoes(atual, base) == []
