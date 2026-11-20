"""Gera landing/src/content/plano-rn1137.json: o plano de ação da RN 1.137/2025 para a demo do site.

Uso:
  python scripts/exportar_plano_demo.py                  # plano com o perfil ilustrativo
  python scripts/exportar_plano_demo.py --importar-ia artifacts/revisao-ensaio
      # recria athenix/data/ia_cache_rn1137.json a partir do cache local do ensaio (sem rede)

Processa a norma por regras (sem IA), avalia com o perfil ilustrativo e monta o plano com
athenix/plano.py. Os títulos e enquadramentos sugeridos pela IA vêm do cache versionado
(athenix/data/ia_cache_rn1137.json), sem nenhuma chamada: títulos só quando passam nos filtros;
enquadramentos só como "Interpretação da IA", fora do cálculo. O site só lê o JSON gerado.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient  # noqa: E402

from athenix import analise, impacto, plano  # noqa: E402
from athenix.app import create_app  # noqa: E402
from athenix.config import Settings  # noqa: E402
from athenix.demo import USUARIO, preparar  # noqa: E402
from athenix.normalizacao import espacos  # noqa: E402
import extrair_parametros as ep  # noqa: E402
from exportar_demo_site import rotulo  # noqa: E402

SAIDA = ROOT / "landing" / "src" / "content" / "plano-rn1137.json"
SITUACAO_PRINCIPAL = "principal não condicional e não genérica"


def processar():
    """RN 1.137 processada por regras num banco descartável: (linhas, unidades, parâmetros)."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        settings = Settings(model="", api_key="", ai_mode="off")
        senha = preparar(settings, banco=Path(tmp) / "demo.db")
        with TestClient(create_app(settings)) as client:
            client.post("/api/login", json={"username": USUARIO, "password": senha})
            rows = client.get("/api/obligations").json()["items"]
            doc = client.get(f"/api/documents/{rows[0]['document_id']}").json()
    return rows, doc["extraction"], impacto.carregar()


def avaliar(rows, params, base, data_referencia, faturamento=None, atenuante="nenhuma"):
    """impacto.avaliar para uma distribuidora. Com atenuante, o valor base vai ao teto do grupo
    (fração 100%, pior caso) para o motor aplicar o atenuante sobre ele."""
    form = {"segmento": "distribuicao", "base": "" if base is None else str(base)}
    form |= {"data_referencia": data_referencia, "faturamento": faturamento or ""}
    if atenuante != "nenhuma":
        form |= {"atenuante": atenuante, "fracao_valor_base": "100"}
    p = impacto.perfil(form)
    return impacto.avaliar(params, rows, p), p


def montar(base, data_referencia, faturamento=None, processado=None):
    """Plano para uma distribuidora com a base informada (None = em branco)."""
    rows, extraction, params = processado or processar()
    units = extraction["units"]
    resultado, p = avaliar(rows, params, base, data_referencia, faturamento)
    cenarios = {
        a: avaliar(rows, params, base, data_referencia, faturamento, a)[0]
        for a in impacto.ATENUANTES
        if a != "nenhuma"
    }
    out = plano.montar(
        resultado,
        units,
        params,
        p,
        plano.carregar_temas(),
        plano.carregar_ia(),
        cenarios=cenarios,
    )
    out["analise"] = analise.montar(out, rows, extraction)
    by_id = {u["id"]: u for u in units}
    for o in out["obrigacoes"] + out["outros_dispositivos"]:
        o["dispositivo"] = rotulo(by_id[o["unidade"]], by_id) if o["unidade"] else None
        assert o["trecho"] is None or o["trecho"] in espacos(by_id[o["unidade"]]["text"])
    return out, params, p


def importar_ia(pasta):
    """Cache enxuto e versionável: só as sugestões processadas, sem respostas brutas."""
    pasta = Path(pasta).resolve()
    fontes = [pasta / "titulos" / "resultado.json", pasta / "enquadramento_proposta.json"]
    titulos, enq = (json.loads(f.read_text(encoding="utf-8")) for f in fontes)
    cache = {
        "aviso": "Sugestões da IA gravadas no ensaio de 17/11/2026. Aguardam revisão humana. No modo só identificados no texto não entram no cálculo; no cenário preliminar entram no valor do tema, sempre marcadas como sugeridas.",
        "modelo": titulos["modelo"],
        "reasoning": titulos["reasoning"],
        "gerado_por": "scripts/exportar_plano_demo.py --importar-ia",
        "fontes": [{"arquivo": f.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(f.read_bytes()).hexdigest()} for f in fontes],
        "criterio_titulos": "Título aplicado só sem alerta de sentido, com verbo no início, até 85 caracteres e citação literal presente no texto.",
        "criterio_enquadramentos": f"Só a sugestão principal com situação '{SITUACAO_PRINCIPAL}'.",
        "titulos": {
            t["id"]: {
                "titulo": t["titulo_ia"],
                "citacao": t["citacao"]["quote"],
                "alerta": t["alerta_revisao"] or None,
                "ajuste_proposto": t["ajuste_proposto_por_revisao"] or None,
            }
            for t in titulos["titulos"]
            if t["citacao"]["state"] == "verified"
        },
        "enquadramentos": {
            x["id"]: {
                "dispositivo": x["principal"]["device"],
                "grupo": x["principal"]["group"],
                "justificativa": x["principal"]["reason"],
                "duvida": x["principal"]["open_question"],
            }
            for x in enq["linhas"]
            if x["situacao"] == SITUACAO_PRINCIPAL
        },
    }  # fmt: skip
    plano.CACHE_IA.write_text(
        json.dumps(cache, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        f"{plano.CACHE_IA}: {len(cache['titulos'])} títulos, {len(cache['enquadramentos'])} enquadramentos"
    )


def simulador(demo, processado):
    """Faixas de porte do perfil ilustrativo e casos de conferência do motor Python: o simulador do
    site (landing/src/content/plano.ts) refaz a conta no navegador e o teste compara com estes."""
    casos = []
    for base, fat in [(f["base"], None) for f in demo["faixas_porte"]] + [
        (demo["base"], str(int(demo["base"]) // 10))
    ]:
        # O último caso (faturamento menor que a base) é artificial: força o teto legal a limitar.
        out, _, _ = montar(base, demo["data_referencia"], fat, processado)
        o = next(o for o in out["obrigacoes"] if o["faixa"])
        casos.append({
            "base": float(base),
            "faturamento": float(fat) if fat else None,
            "obrigacao": o["id"],
            "maximo_reais": o["faixa"]["maximo_reais"]["com_teto"],
            "com_atenuante_reais": o["faixa"]["com_atenuante_reais"],
        })  # fmt: skip
    faixas = [f | {"base": float(f["base"])} for f in demo["faixas_porte"]]
    return {"faixas": faixas, "origem_faixas": demo["origem_faixas"], "conferencia": casos}


# Fonte(s) que sustentam a redação de cada infração, pela "origem" registrada no catálogo. A primeira
# em que o trecho literal é encontrado vale; se nenhuma, a exportação falha (nada sem proveniência).
ORIGEM_PARA_FONTES = {
    "redação original": ["846"],
    "REN ANEEL 1.000, de 07.12.2021": ["846"],
    "REN ANEEL 1.137, de 21.10.2025": ["846", "1137"],
    "REN 1.162/2026": ["1162"],
    "REN 1.174/2026": ["1174"],
}
FONTE_DO_ATO = {"RN 1.137/2025": "1137", "REN 1.148/2026": "1148"}
CHAVES_DE_GERACAO = (
    "commit_origem",
    "gerado_em",
)  # metadados fora da comparação de reprodutibilidade


def _textos_da_fonte(nome, cache):
    if nome not in cache:
        cache[nome] = [espacos(u["text"]) for u in ep.read(nome)["units"]]
    return cache[nome]


def _fonte_de(params, nome):
    f = params["fontes"][nome]
    return {"titulo": f["titulo"], "arquivo": f["arquivo"], "sha256": f["sha256"]}


def proveniencia(out, params):
    """Leva a fonte, o SHA-256 e a origem da redação de cada infração citada até o JSON, no formato das
    atenuantes, e VALIDA o trecho literal contra o arquivo indicado (relê a fonte versionada)."""
    cache = {}
    for disp, inf in sorted(out["infracoes"].items()):
        trecho = espacos(inf["trecho"])
        candidatas = ORIGEM_PARA_FONTES[inf["origem_da_redacao"]]
        achou = next(
            (n for n in candidatas if any(trecho in t for t in _textos_da_fonte(n, cache))), None
        )
        assert achou, f"{disp}: o trecho citado não está em {candidatas}; exportação interrompida"
        inf["fonte"] = _fonte_de(params, achou)
        inf["conferido_na_fonte"] = True
    return cache


def _limpar(trecho):
    """Texto de uma leitura como a extração entregou, sem o pontilhado do sumário nem a hifenização."""
    t = re.sub(r"\s*\.{5,}\s*$", "", espacos(trecho))
    t = re.sub(r"(?<=[a-zà-ú])- (?=[a-zà-ú])", "", t)
    return t.rstrip("”").strip()


def sucessao_no_tempo(params, cache):
    """As duas redações datadas do art. 11, XXIII (dúvida D1): fonte, SHA-256, vigência e estado. A
    redação futura continua INCERTA (sem (NR)/(AC) na fonte); nada é convertido em conclusão."""
    d1 = next(d for d in params["duvidas"] if d["id"] == "D1")
    leituras = sorted(d1["leituras"], key=lambda x: x["vigencia_desde"])
    saida = []
    for n, x in enumerate(leituras):
        nome = FONTE_DO_ATO[x["ato"]]
        ate = (
            (date.fromisoformat(leituras[n + 1]["vigencia_desde"]) - timedelta(days=1)).isoformat()
            if n + 1 < len(leituras)
            else None
        )
        confere = any(_limpar(x["trecho"]) in t for t in _textos_da_fonte(nome, cache))
        saida.append({
            "ato": x["ato"],
            "vigencia_de": x["vigencia_desde"],
            "vigencia_ate": ate,
            "trecho": _limpar(x["trecho"]),
            "fonte": _fonte_de(params, nome),
            "estado": "verified" if x["ancora"] == "verified" else "incerta",
            "conferido_na_fonte": bool(confere) and x["ancora"] == "verified",
            "motivo": x.get("motivo"),
        })  # fmt: skip
    return {
        "dispositivo": d1["dispositivo"],
        "duvida": d1["id"],
        "texto_da_duvida": d1["texto"],
        "redacoes": saida,
    }


def gerar(data=None, commit=None):
    """Monta o JSON da demo. `data` e `commit` são entradas controláveis (a reprodutibilidade compara o
    resto, sem estes dois metadados); por padrão, hoje e o HEAD do git."""
    demo = impacto.perfil_ilustrativo()
    processado = processar()
    out, params, p = montar(demo["base"], demo["data_referencia"], processado=processado)
    cache = proveniencia(out, params)
    out["sucessao_no_tempo"] = [sucessao_no_tempo(params, cache)]
    ia = plano.carregar_ia()
    commit = (
        commit
        or subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip()
    )
    fonte = params["fontes"]["1137"]
    dados = {
        "gerado_por": "scripts/exportar_plano_demo.py",
        "commit_origem": commit,
        "gerado_em": data or date.today().isoformat(),
        "aviso": impacto.AVISO,
        "norma": {
            "titulo": "RN ANEEL 1.137/2025",
            "url": "https://www2.aneel.gov.br/cedoc/ren20251137.pdf",
            "sha256": fonte["sha256"],
            "vigencia": fonte["vigencia"],
        },
        "perfil": {
            "rotulo": demo["rotulo"],
            "aviso": demo["aviso"],
            "base_reais": float(demo["base"]),
            "origem_base": demo["origem_base"],
            "data_referencia": demo["data_referencia"],
        },
        "ia": {
            k: ia[k]
            for k in ("aviso", "modelo", "reasoning", "criterio_titulos", "criterio_enquadramentos")
        }
        if ia
        else None,  # fmt: skip
        "referencia_escala": analise.referencia_escala(),
        "simulador": simulador(demo, processado),
        **out,
    }
    return dados, out


def diferencas(a, b, caminho="", limite=10):
    """Primeiras diferenças entre dois JSONs (lista de caminhos), para a mensagem da verificação."""
    achadas = []
    if type(a) is not type(b):
        return [caminho or "/"]
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                achadas.append(f"{caminho}/{k}")
            else:
                achadas += diferencas(a[k], b[k], f"{caminho}/{k}", limite)
            if len(achadas) >= limite:
                break
    elif isinstance(a, list):
        if len(a) != len(b):
            return [f"{caminho} (tamanho {len(a)} x {len(b)})"]
        for i, (x, y) in enumerate(zip(a, b)):
            achadas += diferencas(x, y, f"{caminho}[{i}]", limite)
            if len(achadas) >= limite:
                break
    elif a != b:
        achadas.append(caminho)
    return achadas[:limite]


def verificar(saida, dados):
    """O export regenerado tem de ser igual ao JSON versionado, exceto os metadados de geração."""
    versionado = json.loads(Path(saida).read_text(encoding="utf-8"))
    novo = json.loads(json.dumps(dados, ensure_ascii=False))
    for k in CHAVES_DE_GERACAO:
        versionado.pop(k, None)
        novo.pop(k, None)
    dif = diferencas(versionado, novo)
    if dif:
        print(f"{saida} NÃO reproduz o export regenerado. Primeiras diferenças: {', '.join(dif)}")
        print("Regenere com: python scripts/exportar_plano_demo.py")
        return 1
    print(f"{saida} reproduz o export regenerado (sem {', '.join(CHAVES_DE_GERACAO)}).")
    return 0


def main(saida, data=None, commit=None, checar=False):
    dados, out = gerar(data, commit)
    if checar:
        return verificar(saida, dados)
    Path(saida).write_text(
        json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    r = out["resumo"]
    print(
        f"{saida}: {r['aplicaveis']} deveres da distribuidora, {r['outros_dispositivos']} outros "
        f"dispositivos, {r['temas']} temas (commit {dados['commit_origem']})"
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--saida", default=str(SAIDA))
    parser.add_argument("--importar-ia", metavar="PASTA")
    parser.add_argument("--data", help="data de geração (AAAA-MM-DD); padrão: hoje")
    parser.add_argument("--commit", help="commit de origem; padrão: HEAD do git")
    parser.add_argument("--verificar", action="store_true", help="compara com o JSON versionado")
    args = parser.parse_args()
    if args.importar_ia:
        importar_ia(args.importar_ia)
    else:
        sys.exit(main(args.saida, args.data, args.commit, args.verificar))
