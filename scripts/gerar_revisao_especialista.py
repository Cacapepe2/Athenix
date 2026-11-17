"""Gera o material para revisão por especialista: docs/revisao_especialista.md e .csv (planilha).

Uso: python scripts/gerar_revisao_especialista.py
Tudo vem dos dados versionados (gabarito, arquivo de parâmetros, perfil ilustrativo e a RN 1.137 por
regras): trechos, números e grupos não são redigitados. Linguagem simples, perguntas de sim/não.
O CSV usa ";" e UTF-8 com BOM para abrir direto no Excel em português.
"""

import csv
import json
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient  # noqa: E402

from athenix import impacto  # noqa: E402
from athenix.app import create_app  # noqa: E402
from athenix.config import Settings  # noqa: E402
from athenix.demo import USUARIO, preparar  # noqa: E402
from athenix.normalizacao import espacos  # noqa: E402

MD = ROOT / "docs" / "revisao_especialista.md"
CSV = ROOT / "docs" / "revisao_especialista.csv"
GABARITO = ROOT / "tests" / "gabarito" / "gabarito.json"
FONTES = ROOT / "tests" / "gabarito" / "fontes.json"
NOME_DOC = {
    "ren20251137": "RN ANEEL 1.137/2025",
    "reh20243348": "REH ANEEL 3.348/2024",
    "dec12068": "Decreto 12.068/2024",
}
AUTORIA = {"956": ("da", "REN ANEEL 956/2021"), "62724": ("do", "Decreto 62.724/1968")}


def sem_pontilhado(texto):
    """Exibição: corta o pontilhado de texto compilado ("....") e marca o corte; o literal fica nos dados."""
    m = re.search(r"\s*[”\"]?\s*\.{3,}", texto)
    return espacos(texto[: m.start()]) + " […]" if m else espacos(texto)


def data_br(iso):
    return "/".join(reversed(iso.split("-"))) if iso else None


def pct(v):
    return f"{v:g}".replace(".", ",") + "%"


def perguntas_do_caso(caso):
    """[(resposta esperada em linguagem simples, pergunta de sim/não)] para cada item esperado."""
    e, out = caso["esperado"], []
    if ob := e.get("obrigacao"):
        sujeito = ob.get("sujeito")
        if ob["modalidade"] == "permission":
            out.append(
                (
                    "É uma faculdade (pode), não um dever.",
                    f"Isto é uma permissão{f' para {sujeito}' if sujeito else ''}, e não uma obrigação?",
                )
            )
        else:
            out.append((f"É uma obrigação{f' de {sujeito}' if sujeito else ''}.",
                        f"Este trecho cria uma obrigação{f' que vale para {sujeito}' if sujeito else ''}?"))  # fmt: skip
    if e.get("nao_obrigacao"):
        out.append(("Não cria obrigação.", "Este trecho NÃO cria obrigação para a empresa?"))
    if pz := e.get("prazo"):
        if pz.get("periodico"):
            out.append(
                (
                    f"Prazo periódico: {pz['periodico']}.",
                    f"O prazo é periódico ({pz['periodico']})?",
                )
            )
        elif pz.get("sem_data"):
            out.append(
                (
                    "Não tem prazo com data.",
                    "O texto não fixa uma data para cumprir esta obrigação?",
                )
            )
        else:
            marco = {"publication": "da publicação da norma", "event": "de um evento ainda sem data", "effective": "do início da vigência"}[pz["marco"]]  # fmt: skip
            final = (
                f", vencendo em {data_br(pz['data'])}"
                if pz.get("data")
                else " (sem data final até o evento ocorrer)"
            )
            out.append((f"Prazo de {pz['quantidade']} {pz['unidade']} contados {marco}{final}.",
                        f"O prazo é de {pz['quantidade']} {pz['unidade']} contados {marco}{final}?"))  # fmt: skip
    if "autoria" in e:
        if e["autoria"] == "self":
            out.append(
                (
                    "Texto da própria norma.",
                    "Este trecho é texto da própria norma (e não nova redação de outra norma)?",
                )
            )
        else:
            artigo, alvo = AUTORIA.get(e["autoria"], ("da", f"norma nº {e['autoria']}"))
            out.append(
                (
                    f"Nova redação de outra norma: {alvo}.",
                    f"Este trecho é nova redação {artigo} {alvo}, e não texto da própria norma?",
                )
            )
    if "vigencia" in e:
        d = e["vigencia"]["data"]
        out.append((f"Vigência a partir de {data_br(d)}." if d else "A norma não fixa data de vigência neste trecho.",
                    f"A norma entra em vigor em {data_br(d)}?" if d else "Este trecho não fixa uma data de vigência?"))  # fmt: skip
    if e.get("revogacao"):
        out.append(
            (
                "Revoga dispositivo de outra norma.",
                "Este trecho revoga dispositivos (deixa de valer o texto citado)?",
            )
        )
    if rm := e.get("remissao"):
        alvo = f"{rm['alvo_dispositivo']} do {NOME_DOC.get(rm['alvo_doc'], rm['alvo_doc'])}"
        out.append((f"Remete a {alvo}.", f"Este trecho remete a {alvo}?"))
    return out


def rn1137():
    """Obrigações da RN 1.137 pelo pipeline, para levantar os enquadramentos usados no relatório."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        settings = Settings(model="", api_key="", ai_mode="off")
        senha = preparar(settings, banco=Path(tmp) / "demo.db")
        with TestClient(create_app(settings)) as client:
            client.post("/api/login", json={"username": USUARIO, "password": senha})
            return client.get("/api/obligations").json()["items"]


def main():
    params = impacto.carregar()
    gabarito = json.loads(GABARITO.read_text(encoding="utf-8"))
    linhas_csv, md = [], []
    P = params["parametros"]

    def linha(secao, ident, norma, dispositivo, trecho, esperado, pergunta):
        linhas_csv.append(
            [secao, ident, norma, dispositivo, espacos(trecho), esperado, pergunta, "", ""]
        )

    md += [
        "# Revisão por especialista",
        "",
        f"Material gerado em {date.today().strftime('%d/%m/%Y')} por `scripts/gerar_revisao_especialista.py`, a partir dos",
        "dados do Athenix (trechos literais das normas, gabarito e parâmetros de multa). **Situação: ainda",
        "não revisado por especialista** (`revisado_por_humano: false`). A planilha",
        "`docs/revisao_especialista.csv` tem as mesmas perguntas, com colunas para a resposta",
        "(Sim / Não / Não sei) e um comentário.",
        "",
        '**Como responder:** leia o trecho da norma e responda à pergunta. Se a resposta for "não" ou',
        '"depende", o comentário é o mais importante: diga o que está certo e por quê. Não é preciso',
        "conhecer o sistema.",
        "",
        "## Parte 1. Decisões de método (D1, D5, D6 e priorização)",
        "",
    ]

    # D1
    d1 = next(d for d in params["duvidas"] if d["id"] == "D1")
    grupo11 = next(
        (i["grupo"] for i in params["infracoes"] if i["dispositivo"].startswith("Art. 11,")), "?"
    )
    md += [f"### D1. Duas redações para o inciso XXIII do Art. 11 da REN 846 (infração do Grupo {grupo11})", "",
           "O mesmo inciso aparece com textos diferentes em duas normas:", ""]  # fmt: skip
    for leitura in d1["leituras"]:
        md.append(
            f"- **{leitura['ato']}**, vigente desde {data_br(leitura['vigencia_desde']) or 'data a conferir'}: “{sem_pontilhado(leitura['trecho'])}”"
        )
    pergunta = "Hoje vale a redação da RN 1.137 e, a partir de 01/01/2027, a da REN 1.148?"
    md += ["", f"**Pergunta:** {pergunta} Ou as duas condutas continuam como infração?", "",
           "**Opções:** (a) uma substitui a outra na data de vigência; (b) as duas valem (uma delas foi ou será renumerada); (c) outra leitura.", "",
           f"**O que muda no cálculo:** qual conduta entra como infração do Grupo {grupo11}. Hoje o Athenix mostra as duas e não escolhe.", ""]  # fmt: skip
    linha("Método", "D1", "REN 846/2019", "Art. 11, XXIII", " / ".join(f"{x['ato']}: {x['trecho']}" for x in d1["leituras"]),
          "Não decidido: o sistema mostra as duas redações.", pergunta)  # fmt: skip

    # D5
    teto_iv = P["limite_grupo_IV"]["percentuais"][0]
    reinc = P["agravante_reincidencia"]["percentuais"][0]
    legal = P["teto_legal_lei"]["percentuais"][0]
    pergunta = "Depois de somar os agravantes, a multa continua limitada ao teto do grupo?"
    md += ["### D5. Teto do grupo depois dos agravantes", "",
           f"A REN 846 define um teto por grupo (Art. 8º; Grupo IV: {pct(teto_iv)} da base) e agravantes que aumentam a multa (Art. 23; ex.: {pct(reinc)} por reincidência).",
           f"A norma não diz se, depois dos agravantes, a multa pode passar do teto do grupo. Nos dois casos, o teto legal ({pct(legal)} do faturamento, Lei 9.427/1996) continua valendo.", "",
           f"**Pergunta:** {pergunta}", "",
           "**Opções:** (a) sim, o teto do grupo vale depois dos agravantes; (b) não, só o teto legal limita.", "",
           f"**O que muda no cálculo:** Grupo IV com 1 reincidência fica em {pct(teto_iv)} da base em (a) e {pct(teto_iv * (1 + reinc / 100))} em (b). Hoje o Athenix mostra os dois cenários.", ""]  # fmt: skip
    linha(
        "Método",
        "D5",
        "REN 846/2019",
        "Arts. 8º e 23",
        P["ordem_calculo"]["trecho"],
        "Não decidido: dois cenários.",
        pergunta,
    )

    # D6
    pergunta = (
        "O teto legal por infração deve ser calculado sobre o faturamento bruto ou sobre a ROL?"
    )
    md += ["### D6. Teto legal: faturamento bruto ou Receita Operacional Líquida (ROL)?", "",
           f"A Lei 9.427/1996 (Art. 3º, X) limita a multa a {pct(legal)} do **faturamento**; a REN 846 (Art. 21) calcula a multa sobre a **ROL**.", "",
           f"**Pergunta:** {pergunta}", "",
           "**Opções:** (a) faturamento bruto (o teto em reais fica maior); (b) ROL; (c) outra base.", "",
           f"**O que muda no cálculo:** com (a), o Athenix usa o faturamento bruto informado no perfil; sem ele, aplica {pct(legal)} sobre a ROL e avisa que o teto pode estar subestimado.", ""]  # fmt: skip
    linha(
        "Método",
        "D6",
        "Lei 9.427/1996 e REN 846/2019",
        "Art. 3º, X e Art. 21",
        P["teto_legal_lei"]["trecho"],
        "Hoje: faturamento, se informado; senão ROL com aviso.",
        pergunta,
    )

    # Priorização
    pesos = "; ".join(
        f"{n} {str(v).replace('.', ',')}"
        for n, v in zip(
            ("vencida", "vence em até 90 dias", "vence depois", "sem data"),
            impacto.PESO_URGENCIA.values(),
        )
    )
    p1 = "Ordenar por exposição provável × peso do prazo ajuda a decidir o que fazer primeiro? Os pesos fazem sentido?"
    p2 = "Obrigação sem enquadramento identificado deve ficar fora da fila até alguém confirmar o grupo de multa?"
    md += ["### Priorização: o que fazer primeiro", "", f"Regra atual: {impacto.REGRA_ORDEM}", "",
           f"Pesos do prazo: {pesos}. Esses pesos são uma escolha do produto, não vêm de norma.", "",
           f"**Pergunta 1:** {p1}", "", "**Opções:** (a) sim; (b) ajustar os pesos (quais?); (c) ordenar só pelo prazo; (d) ordenar só pela exposição.", "",
           f"**Pergunta 2:** {p2}", "",
           "**O que muda:** sem essa regra, obrigações sem grupo valiam o máximo de todos os grupos e passavam à frente das que têm grupo identificado.", ""]  # fmt: skip
    linha("Método", "P1", "—", "—", impacto.REGRA_ORDEM, "Regra em uso hoje.", p1)
    linha(
        "Método",
        "P2",
        "—",
        "—",
        'Enquadramento desconhecido fica em "Verificar enquadramento".',
        "Regra em uso hoje.",
        p2,
    )

    # Parte 2: gabarito
    md += ["## Parte 2. Os 20 casos do gabarito", "",
           "Cada caso é um trecho real de norma e a leitura que o Athenix considera correta. Responda sim ou não a cada pergunta.", ""]  # fmt: skip
    for caso in gabarito["casos"]:
        norma = NOME_DOC[caso["doc"]]
        md += [
            f"### {caso['id']}. {norma}, {caso['dispositivo']}",
            "",
            f"> {espacos(caso['trecho'])}",
            "",
        ]
        for esperado, pergunta in perguntas_do_caso(caso):
            md.append(
                f"- **Leitura do Athenix:** {esperado} **Pergunta:** {pergunta} ( ) Sim ( ) Não ( ) Não sei"
            )
            linha(
                "Gabarito",
                caso["id"],
                norma,
                caso["dispositivo"],
                caso["trecho"],
                esperado,
                pergunta,
            )
        md.append("")

    # Parte 3: enquadramentos usados no relatório
    rows = rn1137()
    usados = {}
    for seg in ("distribuicao", "transmissao"):
        p = impacto.perfil(
            {"segmento": seg, "data_referencia": impacto.perfil_ilustrativo()["data_referencia"]}
        )
        for item in impacto.avaliar(params, rows, p)["ranking"]:
            for e in item["enquadramentos"]:
                registro = usados.setdefault(
                    e["dispositivo"],
                    {
                        "grupo": e["grupo"],
                        "trecho": e["trecho"],
                        "termos": e.get("termos", []),
                        "exemplos": [],
                    },
                )
                acao = espacos(item["row"]["action"])
                if acao not in registro["exemplos"]:
                    registro["exemplos"].append(acao)
    md += ["## Parte 3. Enquadramento das infrações usadas no relatório", "",
           "O Athenix liga uma obrigação a uma infração da REN 846 quando os instrumentos citados na infração aparecem no texto da obrigação. Para cada infração abaixo, diga se concorda com o grupo e com a ligação.", ""]  # fmt: skip
    for dispositivo, r in sorted(usados.items(), key=lambda x: (x[1]["grupo"], x[0])):
        pergunta = f"Descumprir as obrigações abaixo se enquadra no {dispositivo} da REN 846 (Grupo {r['grupo']})?"
        md += [f"### {dispositivo} da REN 846: Grupo {r['grupo']}", "", f"> {espacos(r['trecho'])}", "",
               f"Obrigações da RN 1.137 ligadas a esta infração ({len(r['exemplos'])}), por exemplo:", ""]  # fmt: skip
        md += [f"- “{a[:220]}{'…' if len(a) > 220 else ''}”" for a in r["exemplos"][:3]]
        md += [
            "",
            f"**Pergunta:** {pergunta} ( ) Sim ( ) Não, o grupo certo é ____ ( ) Não sei",
            "",
        ]
        linha(
            "Enquadramento",
            dispositivo,
            "REN 846/2019",
            dispositivo,
            r["trecho"],
            f"Grupo {r['grupo']}; {len(r['exemplos'])} obrigação(ões) da RN 1.137 ligadas.",
            pergunta,
        )

    md += ["---", "", "Estimativa com base nas premissas listadas, não constitui parecer jurídico. Depois da revisão, as respostas entram no gabarito e nas decisões (`docs/parametros_impacto.md`), e `revisado_por_humano` passa a `true` só para o que foi revisado.", ""]  # fmt: skip
    MD.write_text("\n".join(md), encoding="utf-8", newline="\n")
    with CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(
            [
                "secao",
                "id",
                "norma",
                "dispositivo",
                "trecho",
                "leitura_do_athenix",
                "pergunta",
                "resposta (Sim/Não/Não sei)",
                "comentario",
            ]
        )
        w.writerows(linhas_csv)
    print(
        f"{MD.relative_to(ROOT)} e {CSV.relative_to(ROOT)}: {len(linhas_csv)} perguntas ({len(usados)} enquadramentos)"
    )


if __name__ == "__main__":
    main()
