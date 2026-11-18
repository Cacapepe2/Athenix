"""Valor provável de multa a partir dos dados abertos da ANEEL (Auto de Infração + SIGEC). Sem IA.

Resultado de ANÁLISE: não entra na demo nem no cálculo do produto até revisão do fundador.

Unidade de análise: o AUTO. O CSV tem uma linha por auto, com um único valor (VlrPenalidade e os
valores após Juízo e Diretoria) para todas as infrações dele; o enquadramento lista os grupos, sem
valor por infração. Não é possível separar penalidades; o valor não é dividido. Por isso o estrato é a
COMBINAÇÃO de grupos do auto ("III", "III+V"), e o auto com mais de um grupo não é descartado.

Regras:
- valor final = VlrMultaAposDiretoria se houver; senão VlrMultaAposJuizo; senão VlrPenalidade
  (campo de origem registrado). Limitação: o valor "após a Diretoria" pode faltar em caso já decidido;
- grupos: do enquadramento "Multa do Grupo III (REN 846/2019) Art. 11", pelo artigo da REN 846 mapeado
  no catálogo e conferido com o grupo declarado; sem REN 846 no enquadramento, "não classificado";
- estado: o SIGEC (cruzado por número do auto + CNPJ) dá a situação do crédito: quitado conta;
  suspenso (judicial/seguro), convertido em advertência e cancelado ficam fora; sem SIGEC valem o
  termo de encerramento e a decisão da Diretoria; sem nenhum deles, em andamento (fora);
- estrato (grupos x segmento) só tem valor provável com >= 10 casos de >= 5 empresas;
- segmento só por evidência explícita: código CEG de geração, natureza da fiscalização, ou o nome do
  agente (no CSV de autos ou, pelo CNPJ, no SIGEC) citando distribuição/transmissão; senão "segmento
  não identificado".

Uso: python scripts/analisar_autos.py [--json saida.json]
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
GRUPO = re.compile(r"Multa do Grupo\s+([IV]+)\b", re.I)
REN846 = re.compile(r"\(REN\s*846/2019\)\s*Art\.?\s*(\d+)", re.I)
CEG = re.compile(r"^(EOL|UFV|UHE|PCH|CGH|UTE|UTN|CGU|UHN)\.", re.I)
ORDEM = "IV"  # só para documentar: os grupos são I a V
FORA_SIGEC = {
    "Multa Convertida em Advertência": "convertida em advertência",
    "Cancelada": "cancelada",
}


def le_csv(nome):
    raw = (DADOS / nome).read_bytes().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(raw), delimiter=";"))


def valor(txt):
    """'123456,78' e ',99' (sem inteiro) -> Decimal; vazio -> None."""
    t = (txt or "").strip()
    ok = t and t != "," and re.fullmatch(r"-?[\d.]*,?\d*", t)
    return Decimal(t.replace(".", "").replace(",", ".")) if ok else None


def numero_auto(txt):
    return re.sub(r"\s+", "", (txt or "")).upper()


def cnpj(txt):
    return re.sub(r"\D", "", txt or "")


def valor_final(r):
    for campo in ("VlrMultaAposDiretoria", "VlrMultaAposJuizo", "VlrPenalidade"):
        v = valor(r.get(campo))
        if v is not None:
            return v, campo
    return None, None


def grupos_do_caso(enquadramento, artigo_para_grupo):
    """(grupos, motivo): conjunto ordenado de grupos da REN 846 do auto, ou (None, motivo). Cada
    trecho 'Multa do Grupo X (REN 846/2019) Art. N' precisa bater com o catálogo."""
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
    return "+".join(sorted(grupos, key=lambda x: ["I", "II", "III", "IV", "V"].index(x))), None


def segmento_do_nome(nome):
    d, t = (
        bool(re.search(r"distribui", nome or "", re.I)),
        bool(re.search(r"transmiss", nome or "", re.I)),
    )
    if d and t:
        return "ambíguo"
    return "distribuição" if d else ("transmissão" if t else None)


def segmento_do_caso(r, nome_sigec=""):
    """(segmento, evidência)."""
    cod = (r.get("CodObjetoFiscalizado") or "").strip().split()
    nat = (r.get("NomNaturezaFiscalizacao") or "").lower()
    if cod and CEG.match(cod[0]):
        return "geração", "código CEG"
    for tipo in ("transmiss", "distribui"):
        if tipo in nat:
            return (
                "transmissão" if tipo == "transmiss" else "distribuição"
            ), "natureza da fiscalização"
    for nome, fonte in (
        (r.get("NomAgenteFiscalizado"), "nome no CSV de autos"),
        (nome_sigec, "nome no SIGEC"),
    ):
        seg = segmento_do_nome(nome)
        if seg == "ambíguo":
            return "segmento não identificado", "nome cita distribuição e transmissão"
        if seg:
            return seg, fonte
    return "segmento não identificado", "sem evidência"


class Sigec:
    """Títulos do SIGEC por (auto, CNPJ): situação do crédito e nome do agente."""

    def __init__(self, linhas):
        self.por_auto = defaultdict(list)
        self.nome_por_cnpj = {}
        for r in linhas:
            self.por_auto[(numero_auto(r["NumAutoInfracao"]), cnpj(r["NumCPFCNPJ"]))].append(r)
            self.nome_por_cnpj.setdefault(cnpj(r["NumCPFCNPJ"]), r["SigNomAgente"])

    def situacao(self, auto, doc):
        linhas = self.por_auto.get((auto, doc))
        if not linhas:
            return None
        s = {x["DscSituacaoCredito"] for x in linhas}
        for chave, rotulo in FORA_SIGEC.items():
            if chave in s and s <= {chave, "Cancelada"}:
                return rotulo
        if any(x.startswith("Suspenso") for x in s):
            return "suspenso (judicial ou seguro)"
        if "Quitada" in s:
            return "quitado"
        if "Parcelamento" in s:
            return "parcelado"
        return "outra: " + "/".join(sorted(s))[:40]


def estado(r, sigec_situacao):
    if sigec_situacao in {"quitado", "parcelado"}:
        return sigec_situacao
    if sigec_situacao:
        return sigec_situacao  # suspenso, convertida, cancelada, outra: fora
    if (r.get("NumTermoEncerramento") or "").strip():
        return "encerrado"
    if (r.get("DatDecisaoDiretoria") or "").strip():
        return "decidido pela Diretoria"
    return "em andamento"


CONTAM = {"quitado", "parcelado", "encerrado", "decidido pela Diretoria"}


def estrato(casos):
    n, empresas = len(casos), len({c["cnpj"] for c in casos})
    base = {"n": n, "empresas": empresas}
    if n < MIN_CASOS or empresas < MIN_EMPRESAS:
        return base | {"valor_provavel": f"amostra insuficiente (n = {n})"}
    v = sorted(c["valor"] for c in casos)
    q = statistics.quantiles(v, n=4, method="inclusive")
    return base | {
        "valor_provavel": "estimável", "mediana": str(q[1]), "q1": str(q[0]), "q3": str(q[2]),
        "minimo": str(v[0]), "maximo": str(v[-1]), "zeros": sum(1 for x in v if x == 0),
        "reformados_em_recurso": sum(1 for c in casos if c["reformado"]),
    }  # fmt: skip


def analisar():
    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    por_artigo = defaultdict(set)
    for i in cat["infracoes"]:
        por_artigo[re.match(r"Art\. (\d+)", i["dispositivo"].replace("º", "")).group(1)].add(
            i["grupo"]
        )
    artigo_para_grupo = {a: next(iter(g)) for a, g in por_artigo.items() if len(g) == 1}
    rows = le_csv("auto-infracao.csv")
    sigec = Sigec(le_csv("sigec-multa-de-fiscalizacao.csv"))
    contagem, motivos, estados = Counter(), Counter(), Counter()
    casos, todos_segmentos = [], Counter()
    for r in rows:
        contagem["autos no CSV"] += 1
        doc = cnpj(r["NumCPFCNPJAgenteFiscalizado"])
        auto = numero_auto(r["NumAutoInfracao"])
        seg, evidencia = segmento_do_caso(r, sigec.nome_por_cnpj.get(doc, ""))
        todos_segmentos[seg] += 1
        origem = (
            "ANEEL"
            if r["SigAgenteFiscalizador"].strip() == "ANEEL"
            else "agência estadual conveniada"
        )
        if (r["SigAgenteFiscalizador"] or "").strip() != "ANEEL":
            contagem["autos de agência estadual conveniada"] += 1
        if (auto, doc) in sigec.por_auto:
            contagem["autos com título no SIGEC (auto + CNPJ)"] += 1
        grupos, motivo = grupos_do_caso(r["DscEnquadramentoAI"], artigo_para_grupo)
        if grupos is None:
            motivos[motivo] += 1
            continue
        contagem["classificados (grupos da REN 846)"] += 1
        if "+" in grupos:
            contagem["  dos quais com mais de um grupo"] += 1
        st = estado(r, sigec.situacao(auto, doc))
        estados[st] += 1
        v, campo = valor_final(r)
        if st not in CONTAM:
            contagem["fora: " + st] += 1
        elif v is None:
            contagem["fora: sem valor em reais"] += 1
        else:
            casos.append(
                {
                    "auto": auto, "cnpj": doc, "grupos": grupos, "segmento": seg, "evidencia_segmento": evidencia,
                    "origem": origem, "valor": v, "campo": campo, "estado": st,
                    "sem_valor_da_diretoria": campo != "VlrMultaAposDiretoria" and bool((r["DatDecisaoDiretoria"] or "").strip()),
                    "reformado": campo != "VlrPenalidade" and v != valor(r["VlrPenalidade"]),
                }
            )  # fmt: skip
    contagem["contam"] = len(casos)
    estratos = defaultdict(list)
    for c in casos:
        estratos[(c["grupos"], c["segmento"])].append(c)
    por_origem = defaultdict(list)
    for c in casos:
        por_origem[(c["origem"], c["segmento"])].append(c)
    return {
        "contagem": dict(contagem), "nao_classificados_por": dict(motivos), "estados": dict(estados),
        "segmento_de_todos_os_autos": dict(todos_segmentos),
        "segmentos_dos_casos": dict(Counter(c["segmento"] for c in casos)),
        "origem_dos_casos": dict(Counter(c["origem"] for c in casos)),
        "caso_decidido_sem_valor_da_diretoria": sum(c["sem_valor_da_diretoria"] for c in casos),
        "estratos": {f"{g} x {s}": estrato(v) for (g, s), v in sorted(estratos.items())},
        "por_origem_e_segmento": {f"{o} x {s}": estrato(v) for (o, s), v in sorted(por_origem.items())},
        "casos": casos,
    }  # fmt: skip


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()
    r = analisar()
    print(json.dumps({k: v for k, v in r.items() if k != "casos"}, ensure_ascii=False, indent=1))
    if a.json:
        Path(a.json).write_text(
            json.dumps(r, ensure_ascii=False, indent=1, default=str), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
