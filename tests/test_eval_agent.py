"""Testes do executor sem dependência de rede ou modelo."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.eval_agent import avaliar, contagens, dimensoes, executar


class EvalAgentTests(unittest.TestCase):
    def test_dimensoes_nao_inferem_aprovacao_sem_casos(self):
        with tempfile.TemporaryDirectory() as pasta:
            xml = Path(pasta) / "casos.xml"
            self.assertTrue(all(d["estado"] == "nao_avaliado" for d in dimensoes(xml).values()))
            xml.write_text(
                '<testsuites><testsuite><testcase classname="tests.test_evidence" name="test_exact_independent_recalculation"><failure/></testcase></testsuite></testsuites>'
            )
            report = dimensoes(xml)
            self.assertEqual(report["resposta_final"]["estado"], "falhou")
            self.assertEqual(report["caminho"]["estado"], "nao_avaliado")
            xml.write_text(
                '<testsuites><testsuite><testcase classname="tests.test_evidence" name="test_exact_independent_recalculation"/></testsuite></testsuites>'
            )
            self.assertEqual(dimensoes(xml)["resposta_final"]["estado"], "incompleto")

    def test_timeout_e_falha_nao_aprovam(self):
        with patch(
            "scripts.eval_agent.subprocess.run", side_effect=subprocess.TimeoutExpired("x", 1)
        ):
            self.assertEqual(executar("x", [], 1, {})["estado"], "timeout")
        with patch(
            "scripts.eval_agent.subprocess.run", return_value=subprocess.CompletedProcess([], 1)
        ):
            self.assertEqual(executar("x", [], 1, {})["estado"], "falhou")

    def test_conta_skips_e_erros(self):
        with tempfile.TemporaryDirectory() as pasta:
            xml = Path(pasta) / "test.xml"
            xml.write_text(
                "<testsuites><testsuite><testcase><skipped/></testcase><testcase><failure/></testcase><error/></testsuite></testsuites>"
            )
            self.assertEqual(contagens(xml), {"total": 2, "pulados": 1, "falhas": 1, "erros": 1})

    def test_sem_evidencia_falha_e_preserva_relatorio(self):
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta) / "run"
            with patch(
                "scripts.eval_agent.executar",
                return_value={"nome": "health", "estado": "aprovado", "duracao_segundos": 0},
            ):
                report = avaliar("health", saida, 1)
            self.assertEqual(report["estado"], "falhou")
            self.assertTrue((saida / "relatorio.json").exists())
            with self.assertRaises(FileExistsError):
                avaliar("health", saida, 1)

    def test_skip_e_ressalva_e_modo_off(self):
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta) / "run"

            def fake(nome, args, timeout, env):
                self.assertEqual(env["ATHENIX_AI_MODE"], "off")
                self.assertEqual(env["ATHENIX_API_KEY"], "")
                (saida / "health.xml").write_text(
                    "<testsuites><testsuite><testcase><skipped/></testcase></testsuite></testsuites>"
                )
                return {"nome": nome, "estado": "aprovado", "duracao_segundos": 0}

            with patch("scripts.eval_agent.executar", side_effect=fake):
                self.assertEqual(avaliar("health", saida, 1)["estado"], "ressalvas")


if __name__ == "__main__":
    unittest.main()
