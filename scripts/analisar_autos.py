"""Valor provável de multa a partir dos dados abertos da ANEEL (Auto de Infração + SIGEC). Sem IA.

Resultado de ANÁLISE: não entra na demo nem no cálculo do produto até revisão do fundador.
Regras (Bloco 4.2):
- valor final do caso = VlrMultaAposDiretoria se houver; senão VlrMultaAposJuizo; senão VlrPenalidade
  (o campo de origem fica registrado);
- grupo: do enquadramento ("Multa do Grupo III (REN 846/2019) Art. 11"), pelo artigo da REN 846
  mapeado no catálogo de infrações; auto com mais de um grupo, ou sem REN 846, fica "não classificado";
- contam casos encerrados (termo de encerramento), decididos pela Diretoria ou pagos (SIGEC); fora os
  em andamento e os sem valor em reais;
- estrato (grupo x segmento) só tem valor provável com >= 10 casos de >= 5 empresas; senão
  "amostra insuficiente (n = X)";
- segmento só por evidência explícita: código CEG de geração (EOL, UFV, UHE...) ou natureza que cita
  transmissão/distribuição; o resto é "segmento não identificado".

Uso: python scripts/analisar_autos.py [--json saida.json]
O JSON traz CNPJ (dado público dos dados abertos) e fica fora do git; o resumo do doc é agregado.
"""

import argparse
import csv
import io
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / ".local/dados_aneel"
CATALOGO = ROOT / "athenix/data/penalidades_ren846.json"
MIN_CASOS, MIN_EMPRESAS = 10, 5
GRUPO = re.compile(r"Multa do Grupo\s+([IV]+)\b([^/]*)", re.I)
REN846 = re.compile(r"\(REN\s*846/2019\)\s*Art\.?\s*(\d+)", re.I)
CEG = re.compile(r"^(EOL|UFV|UHE|PCH|CGH|UTE|UTN|CGU|UHN)\.", re.I)


def le_csv(nome):
    raw = (DADOS / nome).read_bytes()
    texto = raw.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(texto), delimiter=";"))


def valor(txt):
    """'123456,78' e ',99' (sem inteiro) -> Decimal; vazio -> None."""
    t = (txt or "").strip()
    return (
        Decimal(t.replace(".", "").replace(",", "."))
        if t and re.fullmatch(r"-?[\d.]*,?\d*", t) and t != ","
        else None
    )


def numero_auto(txt):
    return re.sub(r"\s+", "", (txt or "")).upper()


def valor_final(r):
    for campo in ("VlrMultaAposDiretoria", "VlrMultaAposJuizo", "VlrPenalidade"):
        v = valor(r.get(campo))
        if v is not None:
            return v, campo
    return None, None


def grupo_do_caso(enquadramento, artigo_para_grupo):
    """(grupo, motivo): grupo só se todos os trechos 'Multa do Grupo X (REN 846/2019) Art. N' do auto
    levam ao mesmo grupo no catálogo; senão None e o motivo."""
    texto = " ".join((enquadramento or "").split())
    partes = [p for p in re.split(r"\s/\s", texto) if p.startswith("Multa do Grupo")]
    if not partes:
        return None, "sem multa por grupo no enquadramento"
    grupos = set()
    for p in partes:
        m = REN846.search(p)
        if not m:
            return None, "regime anterior ou sem REN 846 no enquadramento"
        g = artigo_para_grupo.get(m.group(1))
        if not g:
            return None, f"art. {m.group(1)} fora dos arts. 9º a 13 da REN 846"
        declarado = GRUPO.match(p).group(1).upper()
        if declarado != g:
            return (
                None,
                f"grupo declarado ({declarado}) difere do catálogo ({g}) para o art. {m.group(1)}",
            )
        grupos.add(g)
    return (grupos.pop(), None) if len(grupos) == 1 else (None, "mais de um grupo no mesmo auto")


def segmento_do_caso(r):
    cod = (r.get("CodObjetoFiscalizado") or "").strip().split()
    nat = (r.get("NomNaturezaFiscalizacao") or "").lower()
    if cod and CEG.match(cod[0]):
        return "geração"
    if "transmiss" in nat:
        return "transmissão"
    if "distribui" in nat:
        return "distribuição"
    return "segmento não identificado"


def pagos_sigec():
    try:
        sigec = le_csv("sigec-multa-de-fiscalizacao.csv")
    except FileNotFoundError:
        return set()
    return {
        numero_auto(r["NumAutoInfracao"])
        for r in sigec
        if (r.get("DatPagamentoTitulo") or "").strip()
    }


def estado(r, pagos):
    if numero_auto(r["NumAutoInfracao"]) in pagos:
        return "pago"
    if (r.get("NumTermoEncerramento") or "").strip():
        return "encerrado"
    if (r.get("DatDecisaoDiretoria") or "").strip():
        return "decidido pela Diretoria"
    return "em andamento"


def quartis(v):
    q = statistics.quantiles(v, n=4, method="inclusive") if len(v) > 1 else [v[0]] * 3
    return q[0], q[1], q[2]


def estrato(casos):
    n, empresas = len(casos), len({c["cnpj"] for c in casos})
    base = {"n": n, "empresas": empresas}
    if n < MIN_CASOS or empresas < MIN_EMPRESAS:
        return base | {"valor_provavel": f"amostra insuficiente (n = {n})"}
    v = sorted(c["valor"] for c in casos)
    q1, mediana, q3 = quartis(v)
    return base | {
        "valor_provavel": "estimável",
        "mediana": str(mediana), "q1": str(q1), "q3": str(q3), "minimo": str(v[0]), "maximo": str(v[-1]),
        "zeros": sum(1 for x in v if x == 0),
        "reformados_em_recurso": sum(1 for c in casos if c["reformado"]),
        "campos": dict(Counter(c["campo"] for c in casos)),
        "estados": dict(Counter(c["estado"] for c in casos)),
    }  # fmt: skip


def analisar():
    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    por_artigo = defaultdict(set)
    for i in cat["infracoes"]:
        m = re.match(r"Art\. (\d+)", i["dispositivo"].replace("º", ""))
        por_artigo[m.group(1)].add(i["grupo"])
    artigo_para_grupo = {a: next(iter(g)) for a, g in por_artigo.items() if len(g) == 1}
    rows, pagos = le_csv("auto-infracao.csv"), pagos_sigec()
    contagem, casos = Counter(), []
    motivos, estados = Counter(), Counter()
    for r in rows:
        contagem["autos no CSV"] += 1
        grupo, motivo = grupo_do_caso(r["DscEnquadramentoAI"], artigo_para_grupo)
        if grupo is None:
            motivos[motivo] += 1
            continue
        contagem["classificados em grupo (REN 846)"] += 1
        st = estado(r, pagos)
        estados[st] += 1
        v, campo = valor_final(r)
        if st == "em andamento":
            contagem["fora: em andamento"] += 1
        elif v is None:
            contagem["fora: sem valor em reais"] += 1
        else:
            casos.append(
                {
                    "auto": numero_auto(r["NumAutoInfracao"]), "cnpj": r["NumCPFCNPJAgenteFiscalizado"].strip(),
                    "grupo": grupo, "segmento": segmento_do_caso(r), "valor": v, "campo": campo, "estado": st,
                    "reformado": campo != "VlrPenalidade" and v != valor(r["VlrPenalidade"]),
                }
            )  # fmt: skip
    contagem["contam (encerrados, pagos ou decididos, com valor)"] = len(casos)
    estratos = defaultdict(list)
    for c in casos:
        estratos[(c["grupo"], c["segmento"])].append(c)
    return {
        "contagem": dict(contagem), "nao_classificados_por": dict(motivos), "estados_dos_classificados": dict(estados),
        "segmentos_dos_casos": dict(Counter(c["segmento"] for c in casos)),
        "grupos_dos_casos": dict(Counter(c["grupo"] for c in casos)),
        "estratos": {f"{g} x {s}": estrato(v) for (g, s), v in sorted(estratos.items())},
        "casos": casos, "pagos_no_sigec": len(pagos),
    }  # fmt: skip


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()
    r = analisar()
    resumo = {k: v for k, v in r.items() if k != "casos"}
    print(json.dumps(resumo, ensure_ascii=False, indent=1))
    if a.json:
        Path(a.json).write_text(
            json.dumps(r, ensure_ascii=False, indent=1, default=str), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
