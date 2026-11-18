"""Relatório-piloto privado: plano de ação da RN 1.137/2025 para uma distribuidora de grande porte.

Uso (na raiz do repositório, branch com athenix/plano.py):
  .venv/Scripts/python.exe scripts/piloto/gerar_relatorio.py

O script está no git; a saída (PDF) vai para artifacts/piloto/, ignorado pelo git: material de
validação com cliente, não publicar.
Base de cálculo (ROL) e faturamento em branco: a exposição sai em % da base, com campos para o
gerente preencher. Nenhum dado de empresa. PDF gerado pelo Edge instalado (Playwright, canal msedge).
"""

import re
from urllib.parse import urlparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
from jinja2 import Environment  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from athenix import analise, impacto, plano  # noqa: E402
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
.tema { border: 1px solid #dcd7ce; border-radius: 7px; padding: 8pt 10pt; margin-bottom: 9pt; }
.manchete { border: 1px solid #b6a38b; background: #f3efe8; border-radius: 6px; padding: 7pt 9pt; margin: 8pt 0; }
.manchete .grande { font-family: Georgia, serif; font-size: 14pt; line-height: 1.2; margin: 3pt 0 5pt; }
table.portes th, table.portes td { font-size: 8pt; padding: 2.5pt 4pt; }
.analise { border-top: 1px dashed #b6a38b; margin-top: 6pt; padding-top: 5pt; font-size: 8pt; }
.analise .ob { margin: 4pt 0; padding: 3pt 0; border-bottom: 1px solid #ece8e0; page-break-inside: avoid; }
.ato { border: 1px solid #d9b98a; background: #f6ecd9; border-radius: 5px; padding: 4pt 6pt; margin: 3pt 0; }
.pratica { border: 1px dashed #b6a38b; border-radius: 5px; padding: 4pt 6pt; margin: 4pt 0; color: #3a4452; font-size: 7.6pt; word-break: break-word; }
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
 <div class="manchete">
  <p class="small muted" style="margin:0">Cenário preliminar · faixa ilustrativa · valores por infração, nunca somados</p>
  <p class="grande">{{ vencidos }} {{ 'tema' if vencidos == 1 else 'temas' }} com prazo vencido · exposição de até <b>{{ pct(top_pct) }} da ROL</b> por infração, no tema mais exposto</p>
  <table class="portes"><tr><th>Porte (ROL anual, ilustrativo)</th>{% for f in portes %}<th>{{ f.rotulo }} ~{{ brl_curto(f.base) }}</th>{% endfor %}</tr>
  <tr><td>Até, por infração</td>{% for f in portes %}<td><b>{{ brl_curto(f.base * top_pct / 100) }}</b></td>{% endfor %}</tr></table>
  <p class="small muted" style="margin:3pt 0 0">Referência do setor: auto de infração típico em distribuição ≈ {{ brl_curto(esc.mediana_reais) }} (mediana de {{ esc.autos }} autos); maior registrado ≈ {{ brl_curto(esc.maximo_reais) }}. <i>{{ esc.rotulo }}.</i> É o valor do auto inteiro, que pode reunir várias infrações. Em reais, o valor da empresa é % × ROL informada.</p>
 </div>
 <p class="small muted" style="margin:6pt 0">{{ r.aplicaveis }} obrigações para distribuidoras · {{ r.por_situacao.vencida }} com prazo vencido · {{ r.por_situacao['90dias'] }} vencem em 90 dias · {{ r.por_situacao.recorrente }} recorrentes · {{ r.por_situacao.evento + r.por_situacao.sem_prazo }} sem data ({{ r.por_situacao.evento }} dependem de evento)</p>
 <h2>3 decisões para esta semana</h2>
 <ol class="dec">{% for d in p.decisoes.principais %}<li><b>{{ d.nome }}</b> · {% if d.exposicao_pct is not none %}até {{ pct(d.exposicao_pct) }} da ROL por infração{% if d.origem == 'sugerido' %} <span class="ia">(sugerido, aguarda confirmação)</span>{% endif %}{% else %}exposição a enquadrar{% endif %} · {{ prazo_txt(d.prazo) }}</li>{% endfor %}
 </ol>
 <p class="small muted">Confirmar enquadramentos libera o cálculo de {{ p.decisoes.confirmar.temas_sem_calculo_confirmado }} temas (hoje só há sugestão). Quem confirma: a definir pela empresa.</p>
 <h2 style="margin-top:6pt">Temas em ordem de reais em risco</h2>
 <table class="resumo"><tr><th>#</th><th>Tema</th><th>Obrigações</th><th>Prazo mais urgente</th><th>Grupo</th><th>Exposição por infração</th></tr>
 {% for t in p.temas %}{% set e = expo(t) %}<tr><td>{{ loop.index }}</td><td><b>{{ t.nome }}</b></td><td>{{ t.n }}</td><td>{{ t.prazo_mais_urgente.texto if t.prazo_mais_urgente else 'Sem data no texto' }}</td>
 <td>{% if e[1] == 'confirmado' %}Grupo {{ t.grupos|join(', ') }} (confirmado){% elif e[1] == 'sugerido' %}Grupo {{ t.grupos_sugeridos|last }} <span class="ia">(sugerido)</span>{% else %}A confirmar{% endif %}</td>
 <td>{% if e[0] is not none %}até {{ pct(e[0]) }} da ROL{% if e[1] == 'sugerido' %} <span class="ia">cenário preliminar: inclui sugestão aguardando confirmação</span>{% endif %}{% else %}Exposição a enquadrar{% endif %}</td></tr>{% endfor %}</table>
 <p class="small muted" style="margin-top:3pt">Ordem: o que a empresa marcar como já atendido vai para o fim; depois, a exposição máxima por infração do tema (maior primeiro); prazo vencido antes de a vencer; número de obrigações. O valor provável não é estimável (sem histórico de multas). Exposições de infrações diferentes não se somam.</p>
 <div class="aviso">Iniciativa em validação. Estimativa ilustrativa com base nas premissas listadas; não indica descumprimento da empresa e não constitui parecer jurídico. Prazos são provisórios até confirmação da contagem. Interpretações da IA aguardam revisão humana; só entram no valor do cenário preliminar, sempre marcadas como sugestão. Exposições de obrigações diferentes não devem ser somadas.</div>
</section>

<section class="page">
 <p class="kicker">Plano por tema</p>
 <h2>O que fazer em cada tema</h2>
 <p class="small muted">Marque a situação atual da empresa em cada tema. Temas pela própria norma; obrigações completas e trechos no anexo. {{ p.regra_ordem|replace('no porte escolhido', 'em % da ROL') }}</p>
 {% for t in p.temas %}<div class="tema">
  <div class="tema-top"><h3>{{ loop.index }}. {{ t.nome }} <span class="small muted">· {{ t.n }} obrigações</span></h3>
   <span class="box">☐ Já temos &nbsp; ☐ Parcial &nbsp; ☐ Não temos</span></div>
  <dl class="grid4">
   <div><dt>Prazo mais urgente</dt><dd>{{ t.prazo_mais_urgente.texto if t.prazo_mais_urgente else 'Sem data no texto' }}</dd><dd class="n">{{ contagem(t) }}</dd></div>
   <div><dt>Enquadramento na REN 846</dt><dd>{% if t.grupos %}Grupo {{ t.grupos|join(', ') }} · {{ t.infracoes|join('; ') }}{% else %}A confirmar{% endif %}</dd>
    <dd class="n">{% if t.grupos %}Identificado pelo texto em {{ t.na_fila }} de {{ t.n }}; {{ t.a_confirmar }} a confirmar.{% endif %}{% if t.ia %} <span class="ia">Interpretação da IA</span>: {{ t.ia.dispositivo }} em {{ t.ia.n }} de {{ t.ia.de }} (aguarda revisão; só no cenário preliminar).{% endif %}</dd></div>
   <div><dt>Exposição por infração</dt>{% set e = expo(t) %}<dd>{% if e[0] is not none %}até {{ pct(e[0]) }} da ROL (pode ser só advertência){% else %}Exposição a enquadrar{% endif %}</dd><dd class="n">{% if e[1] == 'sugerido' %}Cenário preliminar: inclui sugestões aguardando confirmação. {% endif %}Em R$: % × ROL informada. Provável não estimável (sem histórico de multas).</dd></div>
   <div><dt>Como provar que cumpriu (sugestão)</dt>{% for e in t.evidencias %}<dd class="n">• {{ p.evidencias[e.id] }} ({{ e.n }})</dd>{% else %}<dd class="n">Definir com a equipe.</dd>{% endfor %}</div>
  </dl>
  <p class="small"><b>Obrigações principais:</b> {% for id in t.principais %}{{ ob[id].titulo }}{% if ob[id].titulo_origem == 'ia' %}*{% endif %} <span class="muted">({{ ob[id].prazo.texto }})</span>{% if not loop.last %}; {% endif %}{% endfor %}</p>
  {% if t.fontes %}<p class="small muted">Tema pela norma: {% for f in t.fontes %}{{ f.rotulo }}, “{{ f.titulo }}”{% if not loop.last %}; {% endif %}{% endfor %}.</p>{% endif %}
  <div class="analise"><p class="kicker">{{ p.analise.rotulo }}</p>
   {% if t.dependencias_no_texto %}<div class="ato"><b>Prazo condicionado a ato da ANEEL: verificar se as instruções foram publicadas.</b>
    {% for d in t.dependencias_no_texto %}<blockquote>“{{ d.trecho_literal }}” <span class="muted">{{ ob[d.obrigacao].dispositivo or '—' }} · trecho literal conferido na fonte</span></blockquote>{% endfor %}</div>{% endif %}
   {% for id in t.principais %}{% set o = ob[id] %}{% set a = o.analise %}<div class="ob">
    <b>{{ o.titulo }}</b> <span class="muted">· {{ o.dispositivo or '—' }}</span>
    {% if o.trecho %}<blockquote>“{{ o.trecho }}” <span class="muted">{{ o.dispositivo }}</span></blockquote>{% endif %}
    <div><b>Tipo:</b> {% if a.tipo.situacao == 'concordam' %}{{ a.tipo.nome }}{% elif a.tipo.situacao == 'so_regra' %}{{ a.tipo.nome }} <span class="ia">só pela regra, segunda leitura da IA não feita (a revisar)</span>{% elif a.tipo.situacao == 'a_revisar' %}tipo a revisar{% else %}sem tipo próprio{% endif %}</div>
    {% if a.tipo.id %}{% set m = p.analise.manuais[a.tipo.id] %}
    <div><b>Como cumprir</b> <span class="ia">sugestão</span>: {{ m.ideias_cumprimento|join(' · ') }}</div>
    <div><b>O que provar para a ANEEL</b> <span class="ia">sugestão</span>: {{ m.evidencias|join(' · ') }}</div>{% endif %}
   </div>{% endfor %}
   {% if p.analise.pratica_por_tema.get(t.id) %}{% set dep = p.analise.dependencias[p.analise.pratica_por_tema[t.id]] %}<div class="pratica">
    <b>Prática conhecida (fora do texto da norma): {{ dep.nome }}.</b> {{ dep.cautela }}
    <div><b>Caminho:</b> {{ dep.caminho }}</div>
    <div><b>O que guardar desde já:</b> {{ dep.o_que_guardar|join(' · ') }}</div>
    <div><b>Referências públicas:</b> {% for pr in dep.precedentes if pr.titulo != p.analise.contraponto.titulo %}{{ pr.titulo }} ({% for u in pr.urls %}{{ dominio(u) }}{% if not loop.last %}; {% endif %}{% endfor %}); {% endfor %}<i>contraponto:</i> {{ p.analise.contraponto.titulo }} ({% for u in p.analise.contraponto.urls %}{{ dominio(u) }}{% if not loop.last %}; {% endif %}{% endfor %}). Links completos na demo.</div>
   </div>{% endif %}
  </div>
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
    vencidos = [t for t in p["temas"] if t["contagem"]["vencida"]]
    top_pct = max(
        (plano.exposicao_pct(t)[0] for t in vencidos if plano.exposicao_pct(t)[0] is not None),
        default=None,
    )
    assert top_pct is not None, "sem exposição nos temas vencidos"
    perfil_demo = impacto.perfil_ilustrativo()
    portes = [
        {"rotulo": f["rotulo"], "base": float(f["base"])} for f in perfil_demo["faixas_porte"]
    ]

    def brl_curto(v):
        n, u = (v / 1e9, "bi") if v >= 1e9 else (v / 1e6, "mi")
        return f"R$ {n:.1f}".replace(".0", "").replace(".", ",") + f" {u}"

    def prazo_txt(u):
        if not u:
            return "sem data no texto"
        return (
            f"prazo vencido há {abs(u['dias'])} dias" if u["situacao"] == "vencida" else u["texto"]
        )

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
            expo=plano.exposicao_pct,
            vencidos=len(vencidos),
            top_pct=top_pct,
            portes=portes,
            brl_curto=brl_curto,
            prazo_txt=prazo_txt,
            esc=analise.referencia_escala(),
            dominio=lambda u: urlparse(u).netloc,
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
    # Valor em reais só nos portes ilustrativos e na referência de escala (milhões/bilhões); a ROL da
    # empresa fica em branco para o gerente preencher.
    # Só a manchete (portes ilustrativos e referência de escala) traz R$; o resto fica em % da ROL.
    fora = re.sub(
        r'<div class="manchete">.*?</div>', "", html.split("Premissas da exposição")[0], flags=re.S
    )
    fora = fora.replace("ROL dos 12 meses anteriores (base da REN 846, Art. 21), R$", "").replace("Faturamento bruto dos 12 meses (teto legal, dúvida D6), R$", "").replace("Em R$", "")  # fmt: skip
    assert "R$" not in fora, "valor em reais sem base informada"
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
