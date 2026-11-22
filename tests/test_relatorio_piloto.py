"""Relatório-piloto (auditoria de 21/11, A2): o CI monta o HTML (sem PDF, sem navegador) e confere as
invariantes: aviso de que não é parecer jurídico, nenhum R$ fora das partes ilustrativas e contagens
iguais às do plano publicado."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "piloto"))
import gerar_relatorio as gr  # noqa: E402

PLANO = json.loads((ROOT / "landing/src/content/plano-rn1137.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def relatorio():
    return gr.montar_html()


def test_html_tem_o_aviso_e_nenhum_valor_fora_das_partes_ilustrativas(relatorio):
    html, _ = relatorio
    gr.conferir(html)  # as mesmas asserções que o gerador faz antes do PDF
    assert html.count(gr.AVISO_JURIDICO) >= 2


def test_contagens_iguais_as_do_plano_publicado(relatorio):
    html, p = relatorio
    r = PLANO["resumo"]
    assert p["resumo"]["aplicaveis"] == r["aplicaveis"] and len(p["obrigacoes"]) == len(
        PLANO["obrigacoes"]
    )
    assert (
        f"{r['aplicaveis']} obrigações para distribuidoras · {r['por_situacao']['vencida']} com prazo vencido"
        in html
    )
    assert f"Outros dispositivos relevantes ({len(PLANO['outros_dispositivos'])})" in html


def test_conferir_recusa_relatorio_sem_aviso_ou_com_reais_fora_do_lugar(relatorio):
    html, _ = relatorio
    with pytest.raises(AssertionError, match="parecer jurídico"):
        gr.conferir(html.replace(gr.AVISO_JURIDICO, ""))
    with pytest.raises(AssertionError, match="valor em reais sem base informada"):
        gr.conferir(html.replace("<h2", "<p>multa de R$ 1 mi</p><h2", 1))
