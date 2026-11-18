"""Relatório-piloto privado: plano de ação da RN 1.137/2025 para uma distribuidora de grande porte.

Uso (na raiz do repositório, branch com athenix/plano.py):
  .venv/Scripts/python.exe scripts/piloto/gerar_relatorio.py

O script está no git; a saída (PDF) vai para artifacts/piloto/, ignorado pelo git: material de
validação com cliente, não publicar.
Base de cálculo (ROL) e faturamento em branco: a exposição sai em % da base, com campos para o
gerente preencher. Nenhum dado de empresa. PDF gerado pelo Edge instalado (Playwright, canal msedge).
"""

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
from jinja2 import Environment  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from athenix import impacto  # noqa: E402
from exportar_plano_demo import montar  # noqa: E402

SAIDA = ROOT / "artifacts" / "piloto" / "relatorio_rn1137_distribuidora.pdf"
REFERENCIA = "2026-11-17"
PERGUNTAS = [
    ("O que ajuda a decidir", "Quais partes deste relatório ajudariam sua equipe a decidir o que fazer primeiro? O que você usaria numa reunião de diretoria?"),
    ("O que está errado", "Algum prazo, tema, enquadramento, grupo de infração ou evidência sugerida está errado ou não se aplica à sua empresa? Qual e por quê?"),
    ("O que falta", "O que faltou para este relatório ser útil no seu dia a dia (por exemplo: área responsável, custo de adequação, histórico de autuações, outras normas)?"),
    ("Quem aprovaria um piloto", "Quem na empresa aprovaria um piloto de 60 a 90 dias com uma norma real e os dados de vocês? Qual seria o critério de sucesso?"),
    ("Quanto custa hoje", "Quanto custa hoje fazer esta análise com consultoria ou equipe interna (horas, valor por norma ou contrato anual) e quanto tempo leva?"),
]  # fmt: skip

TEMPLATE = r"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Plano de ação RN 1.137/2025 — piloto</title>
<style>
@page { size: A4; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Arial, sans-serif; color: #111c2f; font-size: 9.2pt; line-height: 1.36; margin: 0; }
h1, h2, h3 { font-family: Georgia, "Times New Roman", serif; font-weight: 500; margin: 0; }
h1 { font-size: 18pt; line-height: 1.15; } h2 { font-size: 13pt; margin: 0 0 4pt; } h3 { font-size: 12pt; }
.kicker { font-size: 7.5pt; letter-spacing: .14em; text-transform: uppercase; color: #7a6650; font-weight: 600; }
.muted { color: #4f5a69; } .small { font-size: 8pt; } .page { page-break-after: always; }
.aviso { border: 1px solid #b6a38b; background: #f3efe8; border-radius: 6px; padding: 6pt 8pt; font-size: 8pt; margin-top: 8pt; }
.perfil { display: grid; grid-template-columns: 1fr 1fr; gap: 3pt 14pt; border: 1px solid #dcd7ce; border-radius: 6px; padding: 5pt 9pt; margin: 6pt 0; }
.campo { border-bottom: 1px solid #111c2f; min-height: 15pt; }
.nums { display: grid; grid-template-columns: repeat(6, 1fr); gap: 5pt; margin: 8pt 0; }
.num { border: 1px solid #dcd7ce; border-radius: 6px; padding: 5pt 6pt; } .num b { font-family: Georgia, serif; font-size: 14pt; font-weight: 500; display: block; }
.num.alerta { background: #f6ecd9; border-color: #d9b98a; } .num span { font-size: 7.3pt; color: #4f5a69; }
ol.dec { padding-left: 15pt; margin: 4pt 0; } ol.dec li { margin-bottom: 3pt; } ol.dec .itens { display: block; font-size: 8.3pt; }
table { width: 100%; border-collapse: collapse; font-size: 8.3pt; } th, td { text-align: left; vertical-align: top; padding: 3.5pt 4pt; border-bottom: 1px solid #dcd7ce; }
th { font-size: 7.5pt; color: #4f5a69; font-weight: 600; } tr { page-break-inside: avoid; } table.resumo td { padding: 2pt 4pt; font-size: 7.9pt; }
.tema { border: 1px solid #dcd7ce; border-radius: 7px; padding: 8pt 10pt; margin-bottom: 9pt; page-break-inside: avoid; }
.tema-top { display: flex; justify-content: space-between; gap: 10pt; align-items: baseline; }
.box { font-size: 8.5pt; white-space: nowrap; } .grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8pt; margin: 6pt 0; border-top: 1px solid #dcd7ce; padding-top: 6pt; }
.grid4 dt { font-size: 7.3pt; color: #4f5a69; } .grid4 dd { margin: 1pt 0 0; font-weight: 600; } .grid4 dd.n { font-weight: 400; font-size: 7.8pt; color: #4f5a69; }
.ia { color: #284b63; font-size: 7.6pt; font-weight: 600; } blockquote { margin: 2pt 0; padding: 2pt 6pt; border-left: 2px solid #b6a38b; background: #faf9f6; }
.anexo td { font-size: 7.6pt; } .q { border: 1px solid #dcd7ce; border-radius: 6px; padding: 7pt 9pt; margin-bottom: 8pt; page-break-inside: avoid; }
.linhas div { border-bottom: 1px solid #b9b3a9; height: 17pt; }
</style></head><body>

<section class="page">
 <p class="kicker">Relatório-piloto · confidencial · estimativa ilustrativa</p>
 <h1>RN ANEEL 1.137/2025: plano de ação para uma distribuidora de grande porte</h1>
 <p class="muted">O que a norma exige, o que já venceu e por onde começar. Leitura automática da norma, sem revisão de especialista. Referência: {{ ref }}.</p>
 <div class="perfil">
  <div><span class="small muted">Perfil</span><br><b>Distribuidora de grande porte</b> (sem dados de empresa)</div>
  <div><span class="small muted">Empresa (preencher)</span><div class="campo"></div></div>
  <div><span class="small muted">ROL dos 12 meses anteriores (base da REN 846, Art. 21), R$</span><div class="campo"></div></div>
  <div><span class="small muted">Faturamento bruto dos 12 meses (teto legal, dúvida D6), R$</span><div class="campo"></div></div>
 </div>
 <div class="nums">
  <div class="num"><b>{{ r.aplicaveis }}</b><span>obrigações para distribuidoras</span></div>
  <div class="num alerta"><b>{{ r.por_situacao.vencida }}</b><span>com prazo vencido</span></div>
  <div class="num"><b>{{ r.por_situacao['90dias'] }}</b><span>vencem nos próximos 90 dias</span></div>
  <div class="num"><b>{{ r.por_situacao.recorrente }}</b><span>recorrentes</span></div>
  <div class="num"><b>{{ r.por_situacao.evento + r.por_situacao.sem_prazo }}</b><span>sem data ({{ r.por_situacao.evento }} dependem de evento)</span></div>
  <div class="num"><b>Grupo {{ r.grupo_mais_grave }}</b><span>grupo mais grave identificado: até {{ pct(teto) }} da ROL por infração</span></div>
 </div>
 <h2>3 decisões para esta semana</h2>
 <ol class="dec">{% for d in p.decisoes %}<li><b>{{ d.titulo }}</b>{% if d.itens %}<span class="itens">{{ d.itens|join(' · ') }}</span>{% endif %}{% if loop.last or d.motivo != p.decisoes[loop.index].motivo %}<span class="small muted">{{ d.motivo }}</span>{% endif %}</li>{% endfor %}</ol>
 <h2 style="margin-top:6pt">Temas em ordem de prioridade</h2>
 <table class="resumo"><tr><th>#</th><th>Tema</th><th>Obrigações</th><th>Prazo mais urgente</th><th>Enquadramento</th><th>Exposição por infração</th></tr>
 {% for t in p.temas %}<tr><td>{{ loop.index }}</td><td><b>{{ t.nome }}</b></td><td>{{ t.n }}</td><td>{{ t.prazo_mais_urgente.texto if t.prazo_mais_urgente else 'Sem data no texto' }}</td>
 <td>{{ ('Grupo ' ~ t.grupos|join(', ')) if t.grupos else 'A confirmar' }}</td><td>{{ faixa(t.faixa) if t.faixa else 'Não calculada até confirmar o enquadramento' }}</td></tr>{% endfor %}</table>
 <p class="small muted" style="margin-top:3pt">Ordem: prazo vencido (mais antigo primeiro), depois grupo de infração mais grave e número de obrigações; o valor provável não é estimável (sem histórico de multas). Regra completa na página seguinte.</p>
 <div class="aviso">Iniciativa em validação. Estimativa ilustrativa com base nas premissas listadas; não indica descumprimento da empresa e não constitui parecer jurídico. Prazos são provisórios até confirmação da contagem. Interpretações da IA aguardam revisão humana e não entram no cálculo. Exposições de obrigações diferentes não devem ser somadas.</div>
</section>

<section class="page">
 <p class="kicker">Plano por tema</p>
 <h2>O que fazer em cada tema</h2>
 <p class="small muted">Marque a situação atual da empresa em cada tema. Temas pela própria norma; obrigações completas e trechos no anexo. {{ p.regra_ordem }}</p>
 {% for t in p.temas %}<div class="tema">
  <div class="tema-top"><h3>{{ loop.index }}. {{ t.nome }} <span class="small muted">· {{ t.n }} obrigações</span></h3>
   <span class="box">☐ Já temos &nbsp; ☐ Parcial &nbsp; ☐ Não temos</span></div>
  <dl class="grid4">
   <div><dt>Prazo mais urgente</dt><dd>{{ t.prazo_mais_urgente.texto if t.prazo_mais_urgente else 'Sem data no texto' }}</dd><dd class="n">{{ contagem(t) }}</dd></div>
   <div><dt>Enquadramento na REN 846</dt><dd>{% if t.grupos %}Grupo {{ t.grupos|join(', ') }} · {{ t.infracoes|join('; ') }}{% else %}A confirmar{% endif %}</dd>
    <dd class="n">{% if t.grupos %}Identificado pelo texto em {{ t.na_fila }} de {{ t.n }}; {{ t.a_confirmar }} a confirmar.{% endif %}{% if t.ia %} <span class="ia">Interpretação da IA</span>: {{ t.ia.dispositivo }} em {{ t.ia.n }} de {{ t.ia.de }} (aguarda revisão; fora do cálculo).{% endif %}</dd></div>
   <div><dt>Exposição</dt><dd>{{ faixa(t.faixa) if t.faixa else 'Não calculada até confirmar o enquadramento' }}</dd><dd class="n">Em R$: % × ROL informada. Provável não estimável (sem histórico de multas).</dd></div>
   <div><dt>Como provar que cumpriu (sugestão)</dt>{% for e in t.evidencias %}<dd class="n">• {{ p.evidencias[e.id] }} ({{ e.n }})</dd>{% else %}<dd class="n">Definir com a equipe.</dd>{% endfor %}</div>
  </dl>
  <p class="small"><b>Obrigações principais:</b> {% for id in t.principais %}{{ ob[id].titulo }}{% if ob[id].titulo_origem == 'ia' %}*{% endif %} <span class="muted">({{ ob[id].prazo.texto }})</span>{% if not loop.last %}; {% endif %}{% endfor %}</p>
  {% if t.fontes %}<p class="small muted">Tema pela norma: {% for f in t.fontes %}{{ f.rotulo }}, “{{ f.titulo }}”{% if not loop.last %}; {% endif %}{% endfor %}.</p>{% endif %}
 </div>{% endfor %}
 <p class="small muted">* Título resumido com IA a partir do texto, com citação conferida; aguarda revisão humana.</p>
</section>

<section class="page">
 <p class="kicker">Como reduzir a exposição</p>
 <h2>Atenuantes e reduções da REN 846</h2>
 <p class="small"><b>{{ p.reducao.rotulo }}.</b> Texto citado do {{ p.reducao.medidas[0].fonte }}, SHA-256 {{ p.reducao.medidas[0].sha256 }}. Condição e efeito em linguagem simples: <span class="ia">Interpretação · aguarda revisão humana</span>.</p>
 <table><tr><th style="width:20%">Medida</th><th style="width:11%">Dispositivo</th><th style="width:11%">Redução</th><th>Trecho literal</th><th style="width:26%">Condição e efeito (interpretação)</th></tr>
 {% for m in p.reducao.medidas %}<tr><td><b>{{ m.nome }}</b></td><td>{{ m.dispositivo }}</td><td>{{ ('−' ~ pct(m.percentual)) if m.percentual is not none else 'o texto não fixa percentual' }}</td><td>“{{ m.trecho }}”</td><td>{{ m.condicao }} {{ m.efeito }}</td></tr>{% endfor %}</table>
 <p class="small">{% for c in p.reducao.regras %}<b>{{ c.dispositivo }}:</b> “{{ c.trecho }}” {% endfor %}</p>
 <h3 style="margin-top:8pt">Por tema</h3>
 <table><tr><th style="width:24%">Tema</th><th style="width:24%">Com atenuante (% da ROL, pior caso)</th><th style="width:16%">Causas externas</th><th>O que guardar desde já (sugestão, não exigência da norma)</th></tr>
 {% for t in p.temas %}<tr><td><b>{{ t.nome }}</b></td>
 <td>{% if t.faixa and t.faixa.com_atenuante_pct %}{% for m in p.reducao.medidas if m.cenario and m.cenario in t.faixa.com_atenuante_pct %}{{ m.dispositivo }}: até {{ pct(t.faixa.com_atenuante_pct[m.cenario]) }}{% if not loop.last %}<br>{% endif %}{% endfor %}{% else %}Não calculada até confirmar o enquadramento{% endif %}</td>
 <td>{% if t.excludentes %}{% for e in t.excludentes %}“{{ e.trecho }}”{% endfor %}{% else %}{{ t.causa_externa }}{% endif %}</td>
 <td>{% for g in t.guardar %}• {{ p.guardar[g.id] }}<br>{% else %}Definir com a equipe.{% endfor %}</td></tr>{% endfor %}</table>
 <p class="small muted">Cenário com atenuante: valor base no teto do grupo, sem agravantes; atenuantes não se acumulam (art. 24). Em R$: % × ROL informada.</p>
</section>

<section class="page anexo">
 <p class="kicker">Anexo</p>
 <h2>Obrigações, trechos literais e fontes</h2>
 <p class="small muted">Fonte: {{ norma.titulo }} ({{ norma.url }}), SHA-256 {{ norma.sha256 }}. Infrações: {{ p.reducao.medidas[0].fonte }} (catálogo extraído pela Athenix). Teto legal: Lei 9.427/1996, Art. 3º, X, com redação da Lei 15.269/2025.</p>
 {% for t in p.temas %}<h3 style="margin-top:8pt">{{ loop.index }}. {{ t.nome }}</h3>
 <table><tr><th style="width:22%">Obrigação</th><th style="width:13%">Dispositivo · prazo</th><th>Trecho literal da norma</th><th style="width:21%">Infração (REN 846)</th></tr>
 {% for id in t.obrigacoes %}{% set o = ob[id] %}<tr><td>{{ o.titulo }}{% if o.titulo_origem == 'ia' %}*{% endif %}</td><td>{{ o.dispositivo or '—' }}<br><span class="muted">{{ o.prazo.texto }}</span></td>
 <td>{% if o.trecho %}“{{ o.trecho }}”{% else %}<span class="muted">Sem citação verificada: conferir na fonte.</span>{% endif %}</td>
 <td>{% for e in o.enquadramento %}<b>{{ e.dispositivo }} · Grupo {{ e.grupo }}</b> (o texto nomeia o instrumento da infração){% endfor %}{% if not o.enquadramento and o.ia %}<span class="ia">Interpretação da IA · aguarda revisão</span><br>{{ o.ia.dispositivo }} · Grupo {{ o.ia.grupo }}{% if o.ia.duvida %} · depende da dúvida {{ o.ia.duvida }}{% endif %}{% elif not o.enquadramento %}<span class="muted">A confirmar</span>{% endif %}</td></tr>{% endfor %}
 </table>{% endfor %}
 <h3 style="margin-top:10pt">Texto das infrações citadas</h3>
 <table>{% for d, i in p.infracoes|dictsort %}<tr><td style="width:18%"><b>{{ d }}</b> · Grupo {{ i.grupo }}</td><td>“{{ i.trecho }}”</td></tr>{% endfor %}</table>
 <h3 style="margin-top:10pt">Premissas da exposição</h3>
 <ul class="small">{% for pr in premissas %}<li>{{ pr }}</li>{% endfor %}</ul>
</section>

<section>
 <p class="kicker">Validação</p>
 <h2>O que precisamos de você</h2>
 <p class="muted">Suas respostas decidem o que melhorar antes de um piloto. Pode responder por escrito ou numa conversa de 30 minutos. Contato: contato.athenix@gmail.com.</p>
 {% for titulo, pergunta in perguntas %}<div class="q"><b>{{ loop.index }}. {{ titulo }}</b><br>{{ pergunta }}<div class="linhas"><div></div><div></div><div></div></div></div>{% endfor %}
 <div class="aviso">Material confidencial de validação, gerado em {{ hoje }} a partir do commit {{ commit }}. Iniciativa em validação; não constitui parecer jurídico. Nenhum dado interno de empresa foi usado.</div>
</section>
</body></html>"""


def main():
    p, params, perfil = montar(None, REFERENCIA)
    ob = {o["id"]: o for o in p["obrigacoes"]}
    fila = next(o for o in p["obrigacoes"] if o["faixa"])
    premissas = [pr for pr in fila["premissas"] if "data considerada" not in pr]
    premissas.append(
        "Teto legal conforme a data da infração; a data do prazo foi usada como referência."
    )
    fonte = params["fontes"]["1137"]
    import subprocess

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()  # fmt: skip

    def faixa(f):
        return f"Advertência até {impacto._pct(f['maximo_pct']['com_teto'])} da ROL por infração"

    def contagem(t):
        nomes = {"vencida": "vencida(s)", "recorrente": "recorrente(s)", "evento": "dependem de evento", "sem_prazo": "sem prazo"}  # fmt: skip
        return " · ".join(f"{t['contagem'][s]} {n}" for s, n in nomes.items() if t["contagem"][s])

    html = (
        Environment(autoescape=True)
        .from_string(TEMPLATE)
        .render(
            p=p,
            r=p["resumo"],
            ob=ob,
            teto=fila["faixa"]["teto_grupo_pct"],
            pct=impacto._pct,
            faixa=faixa,
            contagem=contagem,
            premissas=premissas,
            perguntas=PERGUNTAS,
            norma={
                "titulo": "RN ANEEL 1.137/2025",
                "url": "https://www2.aneel.gov.br/cedoc/ren20251137.pdf",
                "sha256": fonte["sha256"],
            },  # fmt: skip
            ref=date.fromisoformat(REFERENCIA).strftime("%d/%m/%Y"),
            hoje=date.today().strftime("%d/%m/%Y"),
            commit=commit,
        )
    )
    assert "R$" not in html.split("Premissas da exposição")[0].replace("ROL dos 12 meses anteriores (base da REN 846, Art. 21), R$", "").replace("Faturamento bruto dos 12 meses (teto legal, dúvida D6), R$", "").replace("Em R$", ""), "valor em reais sem base informada"  # fmt: skip
    (SAIDA.with_suffix(".html")).write_text(html, encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="msedge")
        pg = b.new_page()
        pg.set_content(html, wait_until="load")
        pg.pdf(path=str(SAIDA), format="A4", print_background=True, display_header_footer=True,
               header_template="<span></span>",
               footer_template='<div style="font-size:7pt;width:100%;text-align:center;color:#4f5a69">Athenix · confidencial · estimativa ilustrativa, não constitui parecer jurídico · <span class="pageNumber"></span>/<span class="totalPages"></span></div>',
               margin={"top": "11mm", "bottom": "14mm", "left": "13mm", "right": "13mm"})  # fmt: skip
        b.close()
    print(
        f"{SAIDA} ({SAIDA.stat().st_size // 1024} KB), {len(p['obrigacoes'])} obrigações, {len(p['temas'])} temas"
    )


if __name__ == "__main__":
    main()
