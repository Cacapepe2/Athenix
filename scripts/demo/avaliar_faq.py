"""Avalia afirmações objetivas do FAQ salvo contra o plano exportado, sem IA e sem alterar o motor."""

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from athenix.config import Settings  # noqa: E402
from athenix.normalizacao import espacos  # noqa: E402
from athenix.structure import extract  # noqa: E402

PASTA = ROOT / "tests/fontes_impacto/esclarecimentos"
ANOTACOES = ROOT / "tests/gabarito/faq_rn1137.json"
PLANO = ROOT / "landing/src/content/plano-rn1137.json"
SAIDA = ROOT / "docs/pitch/avaliacao_faq.md"
LISTAS = ("obrigacoes", "outros_dispositivos", "sem_dever_identificado")
IGUAL, DIVERGE, NAO_COBRE = "igual", "diverge", "o motor não cobre"
AUSENTE = object()


def perguntas(raw):
    e = extract(raw, "text/html", Settings(ai_mode="off"), "clarification")
    saida = {}
    for u in e["units"]:
        if u["kind"] != "question":
            continue
        cabecalho, separador, resposta = u["text"].partition("\n")
        if not separador or u["label"] in saida:
            raise ValueError("Pergunta duplicada ou sem resposta no FAQ salvo.")
        saida[u["label"]] = {"pergunta": espacos(cabecalho), "resposta": espacos(resposta)}
    return saida


def campo(obj, caminho):
    for chave in caminho.split("."):
        if not isinstance(obj, dict) or chave not in obj:
            return AUSENTE
        obj = obj[chave]
    return obj


def avaliar(caso, plano):
    linhas = [
        dict(o, lista=lista)
        for lista in LISTAS
        for o in plano.get(lista, [])
        if o.get("dispositivo") in caso["dispositivos"]
    ]
    verificacoes = []
    for v in caso["verificacoes"]:
        if "dever" in v:
            encontrados = [o for o in linhas if o["dispositivo"] == v["dever"]]
            estado = IGUAL if any(o["lista"] == "obrigacoes" for o in encontrados) else NAO_COBRE
            nome = f"dever contado em {v['dever']}"
        else:
            valores = [
                campo(o, v["campo"])
                for o in linhas
                if not v.get("dispositivo") or o["dispositivo"] == v["dispositivo"]
            ]
            valores = [x for x in valores if x is not AUSENTE]
            nome = v["campo"]
            if "padrao" in v:
                estado = (
                    IGUAL
                    if any(
                        isinstance(x, str) and re.search(v["padrao"], espacos(x), re.I)
                        for x in valores
                    )
                    else NAO_COBRE
                )
            elif any(x == v["valor"] for x in valores):
                estado = IGUAL
            else:
                estado = DIVERGE if any(x is not None for x in valores) else NAO_COBRE
        verificacoes.append({"criterio": nome, "veredito": estado})
    estados = {v["veredito"] for v in verificacoes}
    veredito = DIVERGE if DIVERGE in estados else NAO_COBRE if NAO_COBRE in estados else IGUAL
    return {"veredito": veredito, "verificacoes": verificacoes, "linhas": linhas}


def carregar(pasta=PASTA, anotacoes=ANOTACOES, plano=PLANO):
    docs = json.loads((pasta / "fontes.json").read_text(encoding="utf-8"))["documentos"]
    (fonte,) = [d for d in docs if d["arquivo"] == "faq_ren20251137.html"]
    raw = (pasta / fonte["arquivo"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != fonte["sha256"]:
        raise ValueError("Hash divergente no FAQ; avaliação interrompida.")
    qs = perguntas(raw)
    cfg = json.loads(anotacoes.read_text(encoding="utf-8"))
    ids = [c["numero"] for c in cfg["casos"]]
    if (
        len(ids) != len(set(ids))
        or set(ids) & set(cfg["fora"])
        or set(ids) | set(cfg["fora"]) != set(qs)
    ):
        raise ValueError("A avaliação deve classificar cada pergunta uma única vez.")
    for c in cfg["casos"]:
        if espacos(c["citacao"]) not in qs[c["numero"]]["resposta"]:
            raise ValueError(f"Citação oficial ausente na resposta {c['numero']}.")
    dados = json.loads(plano.read_text(encoding="utf-8"))
    return fonte, qs, cfg, dados


def relatorio(fonte, qs, cfg, plano):
    resultados = [(c, avaliar(c, plano)) for c in cfg["casos"]]
    totais = {
        estado: sum(r["veredito"] == estado for _, r in resultados)
        for estado in (IGUAL, DIVERGE, NAO_COBRE)
    }
    dependentes = [
        c["numero"]
        for c, r in resultados
        if any(
            espacos(c["citacao"])
            in espacos((o.get("esclarecimento") or {}).get("fonte", {}).get("trecho", ""))
            for o in r["linhas"]
        )
    ]
    independentes = [(c, r) for c, r in resultados if c["numero"] not in dependentes]
    partes = [
        "# Avaliação do FAQ oficial da RN 1.137/2025",
        f"O Athenix **acerta {totais[IGUAL]} de {len(resultados)} verificáveis**: {totais[DIVERGE]} divergem e "
        f"{totais[NAO_COBRE]} não são cobertas. Das {len(qs)} perguntas, {len(cfg['fora'])} ficaram fora deste placar.",
        f"Fonte: [{fonte['titulo']}]({fonte['url']}), consulta salva em {fonte['consultado_em']}. "
        f"SHA-256: `{fonte['sha256']}`. Nenhuma consulta à rede ou chamada de IA nesta avaliação.",
        f"Plano: `landing/src/content/plano-rn1137.json`, gerado em {plano['gerado_em']}, "
        f"origem `{plano['commit_origem']}`; norma com SHA-256 `{plano['norma']['sha256']}`. "
        "O CI também confere a reprodução do plano. O motor e a linha de base não foram alterados.",
        "## Como ler o resultado",
        cfg["nota"],
        "Cada pergunta tem uma afirmação objetiva delimitada no campo Escopo. Um acerto não significa que "
        "toda a interpretação da resposta, ou um plano operacional real, tenha sido validado. As expectativas "
        "foram anotadas manualmente a partir do FAQ; as citações são conferidas contra a resposta salva. "
        "Os campos e trechos da resposta Athenix vêm exclusivamente do plano exportado, sem títulos ou "
        "sugestões da IA. Falta de um campo, de um requisito ou de uma conclusão negativa é não cobertura, "
        "não acerto por ausência. Divergência exige um valor explícito incompatível, como uma data diferente.",
        f"**Não é um conjunto inteiramente independente:** as perguntas {', '.join(dependentes)} já "
        "alimentam esclarecimentos confirmados no plano. Retirando esses casos, são "
        f"**{sum(r['veredito'] == IGUAL for _, r in independentes)} acertos em {len(independentes)} verificáveis**. "
        "O resultado não substitui revisão regulatória humana.",
        "## Resultado por pergunta",
        "| Pergunta | Afirmação avaliada | Veredito |\n| --- | --- | --- |",
    ]
    partes[-1] += "\n" + "\n".join(
        f"| {c['numero']} | {c['escopo']} | {r['veredito']} |" for c, r in resultados
    )
    partes += ["## Divergências e lacunas"]
    if not totais[DIVERGE]:
        partes.append(
            "Nenhum valor explícito incompatível foi identificado nos campos comparados. Isso não "
            "significa cobertura completa: as lacunas abaixo permanecem abertas e não foram corrigidas para melhorar o placar."
        )
    partes += [
        f"- **{c['numero']} — {r['veredito']}:** {c['nota']}"
        for c, r in resultados
        if r["veredito"] != IGUAL
    ]
    partes += ["## Casos e evidências"]
    for c, r in resultados:
        q = qs[c["numero"]]
        partes += [
            f"### {q['pergunta']}",
            f"**Escopo:** {c['escopo']}",
            f"**Resposta oficial — pergunta {c['numero']}:**",
            f"> {q['resposta']}",
            "**Resposta do Athenix:**",
        ]
        if not r["linhas"]:
            partes.append("Nenhum dispositivo selecionado foi encontrado no plano.")
        for o in r["linhas"]:
            partes.append(
                f"- **{o['dispositivo']}** (`{o['lista']}`): “{o.get('trecho') or 'Sem trecho'}”"
            )
            if o.get("prazo"):
                partes.append(
                    f"  Prazo exportado: {o['prazo']['texto']}; data: `{o['prazo']['data']}`."
                )
            if any(v.get("campo") == "contexto" for v in c["verificacoes"]) and o.get("contexto"):
                partes.append(f"  Caput herdado: “{o['contexto']}”")
        partes += [
            f"**Veredito: {r['veredito']}.** {c['nota']}",
            "Critérios: "
            + "; ".join(f"`{v['criterio']}` — {v['veredito']}" for v in r["verificacoes"])
            + ".",
        ]
    partes += ["## Perguntas fora do placar"]
    partes += [f"- **{qs[n]['pergunta']}** {motivo}" for n, motivo in cfg["fora"].items()]
    partes += [
        "## Decisões pendentes",
        "Revisar as anotações do gabarito com especialista e decidir quais lacunas justificam trabalho "
        "no motor. O relatório só mede e explica; não aplica esclarecimentos novos, não muda o site "
        "nem transforma ausência de extração em ausência de obrigação.",
    ]
    return "\n\n".join(partes) + "\n", totais


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    texto, totais = relatorio(*carregar())
    SAIDA.write_text(texto, encoding="utf-8", newline="\n")
    print(f"FAQ: {totais}; relatório: {SAIDA.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
