"""Executor local de avaliação. Não usa LLM como juiz nem executa chamadas pagas."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
LIMITES = [
    "Gabarito elaborado por IA, ainda sem revisão de especialista.",
    "Testes offline não medem qualidade, custo ou latência de um modelo real.",
    "Duração mede esta máquina; não constitui benchmark de produção.",
    "Não certifica conformidade regulatória nem segurança completa.",
]


DIMENSOES = {
    "resposta_final": {
        "casos": [
            "tests.test_evidence::test_exact_independent_recalculation",
            "tests.test_evidence::test_changed_word_or_paraphrase_invalid",
        ],
        "lacuna": "Gabarito sem revisão especializada; não mede resposta de modelo real.",
    },
    "caminho": {
        "casos": [
            "tests.test_modos_ia::test_off_makes_no_network_call_even_with_credentials",
            "tests.test_modos_ia::test_cached_reuses_recorded_answers_and_never_calls",
            "tests.test_proposals_ai::test_budget_and_missing_key_prevent_call",
        ],
        "lacuna": "Verifica contratos de chamadas; não há avaliação de trajetórias reais de ferramentas.",
    },
    "seguranca": {
        "casos": [
            "tests.test_proposals_ai::test_injection_not_generated_and_no_tools",
            "tests.test_proposals_ai::test_no_evidence_or_out_of_scope_rejected_item",
            "tests.test_workflow::test_unauthenticated_and_csrf_writes_refused",
        ],
        "lacuna": "Não mede resistência de modelo real a injeção nem vazamento de dados em respostas.",
    },
    "incerteza": {
        "casos": [
            "tests.test_evidence::test_without_independent_source_never_verified",
            "tests.test_structure_temporal::test_conflicting_dates_do_not_select_first",
            "tests.test_structure_temporal::test_effective_on_publication_needs_a_single_publication_date",
        ],
        "lacuna": "Verifica abstenção determinística; não mede calibração de confiança do modelo.",
    },
}


def dimensoes(junit):
    """Só atribui evidência a casos executados; nomes ausentes nunca significam aprovação."""
    try:
        casos = list(ET.parse(junit).getroot().iter("testcase"))
    except (OSError, ET.ParseError):
        casos = []
    resultado = {}
    for nome, regra in DIMENSOES.items():
        evidencias, ausentes = [], []
        for esperado in regra["casos"]:
            encontrados = [
                c
                for c in casos
                if (c.get("classname", "") + "::" + c.get("name", "").split("[", 1)[0]) == esperado
            ]
            if not encontrados:
                ausentes.append(esperado)
            for caso in encontrados:
                estado = "aprovado"
                if caso.find("failure") is not None or caso.find("error") is not None:
                    estado = "falhou"
                elif caso.find("skipped") is not None:
                    estado = "pulado"
                evidencias.append(
                    {"caso": esperado, "variante": caso.get("name"), "estado": estado}
                )
        estado = "verificado_offline"
        if any(e["estado"] == "falhou" for e in evidencias):
            estado = "falhou"
        elif not evidencias:
            estado = "nao_avaliado"
        elif ausentes or any(e["estado"] == "pulado" for e in evidencias):
            estado = "incompleto"
        resultado[nome] = {
            "estado": estado,
            "evidencias": evidencias,
            "casos_ausentes": ausentes,
            "lacuna": regra["lacuna"],
        }
    return resultado


def executar(nome, argumentos, timeout, env):
    inicio = time.monotonic()
    try:
        resultado = subprocess.run(
            [sys.executable, *argumentos],
            cwd=ROOT,
            env=env,
            capture_output=True,
            timeout=timeout,
        )
        estado = "aprovado" if resultado.returncode == 0 else "falhou"
        codigo = resultado.returncode
    except subprocess.TimeoutExpired:
        estado, codigo = "timeout", None
    except OSError:
        estado, codigo = "erro_execucao", None
    return {
        "nome": nome,
        "estado": estado,
        "codigo": codigo,
        "duracao_segundos": round(time.monotonic() - inicio, 3),
        "comando": [sys.executable, *argumentos],
    }


def contagens(path):
    suites = ET.parse(path).getroot()
    casos = list(suites.iter("testcase"))
    if not casos:
        raise ValueError("JUnit sem casos")
    return {
        "total": len(casos),
        "falhas": sum(c.find("failure") is not None for c in casos),
        "erros": len(list(suites.iter("error"))),
        "pulados": sum(c.find("skipped") is not None for c in casos),
    }


def avaliar(perfil, saida, timeout):
    saida = Path(saida).resolve()
    # Evita reutilizar artefatos de uma execução anterior como evidência atual.
    saida.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env.update(ATHENIX_AI_MODE="off", ATHENIX_API_KEY="", PYTHONDONTWRITEBYTECODE="1")
    etapas = []
    grupos = [("health", ["tests/test_migrations_pdf.py", "tests/test_evidence.py"])]
    if perfil == "completo":
        grupos = [("suite_completa", ["tests"])]
    for nome, arquivos in grupos:
        junit = saida / f"{nome}.xml"
        etapa = executar(
            nome, ["-m", "pytest", *arquivos, "-q", f"--junitxml={junit}"], timeout, env
        )
        if junit.exists() or etapa["estado"] == "aprovado":
            try:
                etapa["testes"] = contagens(junit)
                if etapa["testes"]["falhas"] or etapa["testes"]["erros"]:
                    etapa["estado"] = "falhou"
                elif etapa["testes"]["pulados"] and etapa["estado"] == "aprovado":
                    etapa["estado"] = "ressalvas"
            except (OSError, ET.ParseError, ValueError):
                etapa["estado"] = "evidencia_invalida"
        etapas.append(etapa)
    if perfil == "completo":
        etapas.append(executar("segredos", ["scripts/check_secrets.py"], timeout, env))
        etapa = executar(
            "gabarito",
            [
                "scripts/avaliar.py",
                "--rotulo",
                "eval",
                "--saida",
                str(saida),
                "--comparar",
                "tests/baseline/metricas_v1.json",
            ],
            timeout,
            env,
        )
        if (saida / "eval.json").exists() or etapa["estado"] == "aprovado":
            try:
                from scripts.avaliar import metricas

                etapa["metricas"] = metricas(json.loads((saida / "eval.json").read_text("utf-8")))
            except (OSError, ValueError, KeyError, ImportError, TypeError):
                etapa["estado"] = "evidencia_invalida"
        etapas.append(etapa)
    falhou = any(e["estado"] not in {"aprovado", "ressalvas"} for e in etapas)
    estado = (
        "falhou"
        if falhou
        else "ressalvas"
        if any(e["estado"] == "ressalvas" for e in etapas)
        else "aprovado"
    )
    report = {
        "versao": 2,
        "perfil": perfil,
        "estado": estado,
        "data_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "etapas": etapas,
        "dimensoes": dimensoes(
            saida / ("suite_completa.xml" if perfil == "completo" else "health.xml")
        ),
        "limites": LIMITES,
    }
    (saida / "relatorio.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    linhas = [
        f"# Eval Agent: {estado}",
        "",
        f"Perfil: {perfil}",
        "",
        "| Etapa | Estado | Segundos |",
        "| --- | --- | --- |",
    ]
    linhas += [f"| {e['nome']} | {e['estado']} | {e['duracao_segundos']} |" for e in etapas]
    linhas += ["", "| Dimensão | Evidência offline | Lacuna |", "| --- | --- | --- |"]
    linhas += [
        f"| {nome} | {d['estado']} | {d['lacuna']} |" for nome, d in report["dimensoes"].items()
    ]
    linhas += ["", *[f"- {limite}" for limite in LIMITES]]
    (saida / "relatorio.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--perfil", choices=["health", "completo"], default="health")
    parser.add_argument("--saida", type=Path)
    parser.add_argument("--timeout", type=int, default=900, help="limite por etapa em segundos")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout deve ser positivo")
    saida = args.saida or ROOT / "artifacts" / "eval-agent" / datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    try:
        report = avaliar(args.perfil, saida, args.timeout)
    except FileExistsError:
        parser.error("--saida já existe; escolha um diretório novo")
    print(f"{report['estado']}: {saida / 'relatorio.json'}")
    return 1 if report["estado"] == "falhou" else 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
