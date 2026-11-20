"""Há campo com o dispositivo infringido (artigo e inciso da REN 846) nos dados abertos? Quantos autos
de distribuição o preenchem? Conta autos por dispositivo (principalmente art. 12, XXVI; XXVII e XXVIII
foram criados pela RN 1.137) e, sem inciso, cai para os autos de distribuição com infração de Grupo IV.

Reaproveita as regras de scripts/analisar_autos.py (unidade = auto, valor final, estado do crédito,
segmento só por evidência explícita). Saída sem nome de empresa: só contagens e valores. Análise
descritiva; não entra na demo nem no cálculo.

Uso: python scripts/autos_por_dispositivo.py [--md docs/historico_multas_por_dispositivo.md]
"""

import argparse
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import analisar_autos as aa  # noqa: E402

# "Art. 12, XXVI", "Art. 12 inciso XXVI", "art. 12º, inc. XXVI": artigo + inciso em algarismos romanos.
INCISO = re.compile(
    r"Art(?:igo)?\.?\s*(\d+)\s*[º°o]?\s*[,\-–]?\s*(?:inc(?:iso|\.)?\s*)?([IVXLC]{1,7})\b(?!\s*/)",
    re.I,
)
CAMPOS_TEXTO = ("DscEnquadramentoAI", "DscInfracao", "DscDispositivo", "DscTipificacao")


def campos_com_inciso(linhas):
    """Para cada coluna do CSV, quantas linhas têm algo no formato artigo + inciso."""
    c = Counter()
    for r in linhas:
        for campo, texto in r.items():
            if texto and INCISO.search(texto):
                c[campo] += 1
    return dict(c)


def dispositivos_do_auto(r):
    """Conjunto de dispositivos 'Art. N, INC' da REN 846 que o auto cita; só os do formato com inciso."""
    saida = set()
    for campo in CAMPOS_TEXTO:
        texto = " ".join((r.get(campo) or "").split())
        for parte in re.split(r"\s/\s", texto):
            if "REN 846" not in parte.upper() and campo == "DscEnquadramentoAI":
                continue
            for m in INCISO.finditer(parte):
                saida.add(f"Art. {m.group(1)}, {m.group(2).upper()}")
    return saida


def resumo(valores):
    if not valores:
        return {"n": 0, "mediana": None, "maximo": None}
    return {
        "n": len(valores),
        "mediana": statistics.median(valores),
        "maximo": max(valores),
    }


def analisar(rows, sigec_linhas, catalogo, vigencia=None):
    """`vigencia`: início da vigência da RN 1.137 (AAAA-MM-DD), para separar autos lavrados depois."""
    por_artigo = defaultdict(set)
    for i in catalogo["infracoes"]:
        por_artigo[re.match(r"Art\. (\d+)", i["dispositivo"].replace("º", "")).group(1)].add(i["grupo"])  # fmt: skip
    artigo_para_grupo = {a: next(iter(g)) for a, g in por_artigo.items() if len(g) == 1}
    sigec = aa.Sigec(sigec_linhas)
    out = {
        "autos": len(rows),
        "colunas_com_inciso": campos_com_inciso(rows),
        "distribuicao": 0,
        "distribuicao_com_inciso": 0,
        "autos_por_dispositivo": Counter(),  # todos os autos de distribuição, qualquer estado
        "valores_por_dispositivo": defaultdict(list),  # só os que contam (quitado etc., com valor)
        "grupo_iv": [],
        "mencoes_por_artigo": Counter(),  # distribuição: autos que citam o art. N da REN 846
        "art12_valores": [],
        "art12_depois_da_vigencia": [],
    }
    for r in rows:
        doc = aa.cnpj(r["NumCPFCNPJAgenteFiscalizado"])
        auto = aa.numero_auto(r["NumAutoInfracao"])
        seg, _ = aa.segmento_do_caso(r, sigec.nome_por_cnpj.get(doc, ""))
        if seg != "distribuição":
            continue
        out["distribuicao"] += 1
        disp = dispositivos_do_auto(r)
        if disp:
            out["distribuicao_com_inciso"] += 1
        st = aa.estado(r, sigec.situacao(auto, doc))
        v, _campo = aa.valor_final(r)
        conta = st in aa.CONTAM and v is not None
        for d in disp:
            out["autos_por_dispositivo"][d] += 1
            if conta:
                out["valores_por_dispositivo"][d].append(v)
        artigos = {m.group(1) for m in aa.REN846.finditer(r["DscEnquadramentoAI"] or "")}
        for art in artigos:
            out["mencoes_por_artigo"][art] += 1
        if "12" in artigos:
            if conta:
                out["art12_valores"].append(v)
            lavrado = (r.get("DatLavraturaAutoInfracao") or "")[:10]
            if vigencia and lavrado >= vigencia:
                out["art12_depois_da_vigencia"].append(lavrado)
        grupos, _ = aa.grupos_do_caso(r["DscEnquadramentoAI"], artigo_para_grupo)
        if conta and grupos and "IV" in grupos.split("+"):
            out["grupo_iv"].append((grupos, v))
    return out


def markdown(res):
    L = [
        "# Histórico de multas por dispositivo (distribuição)",
        "",
        "Análise descritiva, sem nome de empresa e **fora da demo e do cálculo**. Fonte: CSV de autos de",
        "infração, dicionário de dados e SIGEC (`.local/dados_aneel/`, não versionados). Regras de",
        "`scripts/analisar_autos.py` (unidade = auto; valor final; crédito quitado/parcelado/encerrado/decidido).",
        "",
        "## Há campo com o dispositivo infringido (artigo e inciso)?",
        f"- Autos no CSV: {res['autos']:,}; de distribuição (evidência explícita): {res['distribuicao']}.".replace(
            ",", "."
        ),
    ]
    if res["colunas_com_inciso"]:
        L.append("- Colunas com algo no formato artigo + inciso: " + ", ".join(f"`{c}` ({n} linhas)" for c, n in res["colunas_com_inciso"].items()) + ".")  # fmt: skip
    else:
        L.append(
            "- **Nenhuma coluna traz artigo + inciso.** `DscEnquadramentoAI` traz só o grupo e o artigo."
        )
    L.append(f"- Autos de distribuição com inciso identificado: **{res['distribuicao_com_inciso']}** de {res['distribuicao']}.")  # fmt: skip
    L.append("")
    if res["distribuicao_com_inciso"]:
        L += ["## Autos de distribuição por dispositivo", "| Dispositivo | Autos (qualquer estado) | Contam | Mediana (R$) | Máximo (R$) |", "|---|---|---|---|---|"]  # fmt: skip
        for d, n in sorted(res["autos_por_dispositivo"].items(), key=lambda x: -x[1]):
            s = resumo(res["valores_por_dispositivo"].get(d, []))
            med = f"{s['mediana']:,.0f}".replace(",", ".") if s["mediana"] is not None else "n/d"
            mx = f"{s['maximo']:,.0f}".replace(",", ".") if s["maximo"] is not None else "n/d"
            L.append(f"| {d} | {n} | {s['n']} | {med} | {mx} |")
        L.append("")
        for alvo in ("Art. 12, XXVI", "Art. 12, XXVII", "Art. 12, XXVIII"):
            n = res["autos_por_dispositivo"].get(alvo, 0)
            L.append(f"- {alvo}: **{n}** autos de distribuição.")
        L.append("")
    a12 = resumo(res["art12_valores"])
    por_art = ", ".join(
        f"art. {a}: {n}"
        for a, n in sorted(res["mencoes_por_artigo"].items(), key=lambda x: int(x[0]))
    )
    depois = sorted(res["art12_depois_da_vigencia"])
    L += [
        "## Sem inciso: o que o campo permite (artigo da REN 846 citado)",
        f"Autos de distribuição por artigo citado em `DscEnquadramentoAI`: {por_art}.",
        f"- Art. 12 (Grupo IV; inclui os incisos XXVI, XXVII e XXVIII, sem distingui-los): "
        f"{res['mencoes_por_artigo'].get('12', 0)} autos; contam {a12['n']}; mediana = {a12['mediana']}; "
        f"máximo = {a12['maximo']}.",
        f"- Desses, lavrados desde o início da vigência da RN 1.137: **{len(depois)}**"
        + (f" ({', '.join(depois)})." if depois else ".")
        + " O campo não permite saber se algum se baseia no XXVII ou no XXVIII: **não dá para confirmar nem "
        "negar**; a data da lavratura não prova a data da infração.",
        "",
    ]
    g4 = resumo([v for _, v in res["grupo_iv"]])
    L += [
        "## Referência por Grupo IV (distribuição)",
        "Autos de distribuição que contam e têm infração de Grupo IV (podem ter outros grupos; o valor é do auto inteiro):",
        f"- n = **{g4['n']}**; mediana = {g4['mediana']}; máximo = {g4['maximo']}.",
        "",
        "## Limites",
        "- O valor é do auto inteiro; o CSV não separa valor por infração.",
        "- Distribuição pode estar subcontada (segmento só por evidência explícita).",
        "- XXVII e XXVIII do art. 12 só existem a partir da RN 1.137/2025; autos com esses incisos dependem de fiscalização posterior à vigência.",
    ]
    return chr(10).join(L) + chr(10)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--md")
    a = ap.parse_args()
    import json

    cat = json.loads(aa.CATALOGO.read_text(encoding="utf-8"))
    from athenix import impacto

    vigencia = impacto.carregar()["fontes"]["1137"]["vigencia"]
    res = analisar(
        aa.le_csv("auto-infracao.csv"), aa.le_csv("sigec-multa-de-fiscalizacao.csv"), cat, vigencia
    )
    texto = markdown(res)
    print(texto)
    if a.md:
        Path(a.md).write_text(texto, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
