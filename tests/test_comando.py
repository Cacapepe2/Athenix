"""Comando único `python -m athenix processar`: do arquivo oficial da norma ao JSON do plano."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import exportar_plano_demo as exp  # noqa: E402

NORMAS = {
    "rn1137": ROOT / "tests/norma_poc/ren20251137.pdf",
    "ren1174": ROOT / "tests/fontes_impacto/dou/dou_ren20261174.html",
}


def rodar(arquivo, saida, *extra):
    return subprocess.run(
        [sys.executable, "-m", "athenix", "processar", str(arquivo), "--agente", "distribuidora", "--saida", str(saida), *extra],  # fmt: skip
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT, timeout=300,
    )  # fmt: skip


@pytest.mark.parametrize("nome", ["rn1137", "ren1174"])
def test_comando_roda_nas_duas_normas_com_saida_limpa(nome, tmp_path):
    saida = tmp_path / f"plano-{nome}.json"
    r = rodar(NORMAS[nome], saida)
    assert r.returncode == 0, r.stderr[-500:]
    assert r.stderr.strip() == ""  # sem stack trace nem warning
    assert "Traceback" not in r.stdout and "Warning" not in r.stdout
    for passo in ("1. Obrigações extraídas", "2. Deveres da distribuidora", "3. Prazos", "4. Enquadramento", "5. Temas", "Tempo total"):  # fmt: skip
        assert passo in r.stdout
    dados = json.loads(saida.read_text(encoding="utf-8"))
    assert dados["resumo"]["aplicaveis"] == len(dados["obrigacoes"]) > 10
    assert dados["norma"]["sha256"] and dados["temas"]


def test_rn1137_pelo_comando_reproduz_exatamente_o_json_versionado(tmp_path):
    saida = tmp_path / "plano.json"
    r = rodar(NORMAS["rn1137"], saida, "--data", "2000-01-01", "--commit", "0000000")
    assert r.returncode == 0, r.stderr[-500:]
    versionado = ROOT / "landing/src/content/plano-rn1137.json"
    gerado = json.loads(saida.read_text(encoding="utf-8"))
    assert gerado["commit_origem"] == "0000000" and gerado["gerado_em"] == "2000-01-01"
    assert exp.verificar(versionado, gerado) == 0  # igual, exceto data e commit


def test_arquivo_inexistente_diz_o_que_faltou_sem_stack_trace(tmp_path):
    r = rodar(tmp_path / "nao-existe.pdf", tmp_path / "x.json")
    assert (
        r.returncode == 2 and "Arquivo não encontrado" in r.stdout and "Traceback" not in r.stderr
    )
