import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { flushSync } from 'react-dom'
import { Download, Printer, Sparkles } from 'lucide-react'
import { Logo } from '../ui/Logo'
import { Tag } from '../product/Tag'
import {
  brl, comAtenuantePct, csvPlano, dataBR, lacuna, lerReais, maximoPct, motivoPosicao, nomeDiag, obrigacao, ordenarTemas, pct, plano, reaisDe,
  SIM_INICIAL, tetoLegalPct, textoFaixa,
  type Citacao, type Diagnostico, type Diagnosticos, type Medida, type Obrigacao, type Simulacao, type Situacao, type Tema,
} from '../../content/plano'

const r = plano.resumo
const semData = r.por_situacao.evento + r.por_situacao.sem_prazo
const tetoGrupo = plano.obrigacoes.find((o) => o.grupo === r.grupo_mais_grave)?.faixa
const kicker = 'text-xs font-semibold tracking-widest text-bronze-deep uppercase'
// Impressão: todos os detalhes renderizados e abertos (fora dela, cada um renderiza só ao abrir).
const Imprimindo = createContext(false)
// Receita simulada (null: valor digitado inválido, mostra só percentuais). Nada sai do navegador.
const Simulado = createContext<Simulacao | null>(SIM_INICIAL)

function baixarCsv(diag: Diagnosticos, sim: Simulacao | null) {
  const url = URL.createObjectURL(new Blob([csvPlano(diag, sim)], { type: 'text/csv;charset=utf-8' }))
  const a = Object.assign(document.createElement('a'), { href: url, download: 'athenix-plano-rn1137-ilustrativo.csv' })
  a.click()
  URL.revokeObjectURL(url)
}

export function PlanoPage() {
  const [diag, setDiag] = useState<Diagnosticos>({})
  const temas = useMemo(() => ordenarTemas(plano.temas, diag), [diag])
  const gap = lacuna(plano.temas, diag)
  const [imprimindo, setImprimindo] = useState(false)
  const [sim, setSim] = useState<Simulacao | null>(SIM_INICIAL)
  // Impressão/PDF: renderiza e abre todos os "Por quê" para o papel levar o fundamento.
  useEffect(() => {
    const antes = () => {
      flushSync(() => setImprimindo(true))
      document.querySelectorAll('#plano details').forEach((d) => d.setAttribute('open', ''))
    }
    window.addEventListener('beforeprint', antes)
    return () => window.removeEventListener('beforeprint', antes)
  }, [])
  const marcar = (id: string, d: Diagnostico) => setDiag((atual) => ({ ...atual, [id]: d }))

  return <Imprimindo.Provider value={imprimindo}><Simulado.Provider value={sim}>
    <header className="border-b border-line bg-ivory print:hidden"><div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-8"><a href="/" aria-label="Athenix, voltar ao início"><Logo /></a><a href="/" className="text-sm font-semibold text-slate-blue">← Voltar ao site</a></div></header>
    <main id="plano" className="mx-auto max-w-7xl space-y-14 px-4 py-10 sm:px-8 sm:py-14">
      <section aria-labelledby="titulo-plano" className="space-y-8">
        <div className="max-w-3xl">
          <p className={kicker}>Norma real · impacto ilustrativo</p>
          <h1 id="titulo-plano" className="font-display mt-3 text-4xl leading-tight sm:text-5xl">Plano de ação da RN 1.137/2025 para uma distribuidora</h1>
          <p className="mt-4 text-lg text-ink-soft">O que a norma exige, o que já venceu e por onde começar. {plano.perfil.rotulo} (não é empresa real) · referência {dataBR(plano.perfil.data_referencia)}.</p>
        </div>
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <Numero valor={r.aplicaveis} rotulo="obrigações para distribuidoras" />
          <Numero valor={r.por_situacao.vencida} rotulo="com prazo vencido" destaque />
          <Numero valor={r.por_situacao['90dias']} rotulo="vencem nos próximos 90 dias" />
          <Numero valor={r.por_situacao.recorrente} rotulo="recorrentes" />
          <Numero valor={semData} rotulo={`sem data no texto (${r.por_situacao.evento} dependem de um evento)`} />
          {r.grupo_mais_grave && <Numero valor={`Grupo ${r.grupo_mais_grave}`} rotulo={`grupo de infração mais grave identificado${tetoGrupo ? `: até ${pct(tetoGrupo.teto_grupo_pct)} da receita por infração` : ''}`} />}
        </dl>
        <div className="grid items-start gap-5 lg:grid-cols-[1.4fr_1fr]">
          <section aria-labelledby="decisoes" className="rounded-2xl border border-line bg-white p-5 sm:p-7">
            <h2 id="decisoes" className="font-display text-2xl sm:text-3xl">3 decisões para esta semana</h2>
            <ol className="mt-5 space-y-5">
              {plano.decisoes.map((d, n) => <li key={d.titulo} className="flex gap-4">
                <span aria-hidden="true" className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-slate-blue font-semibold text-ivory">{n + 1}</span>
                <div><p className="font-semibold leading-snug">{d.titulo}</p>
                  {d.itens.length > 0 && <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{d.itens.map((i) => <li key={i}>{i}</li>)}</ul>}
                  <p className="mt-2 text-xs text-ink-soft">{d.motivo}</p></div>
              </li>)}
            </ol>
          </section>
          <section aria-labelledby="diagnostico" className="flex flex-col gap-4 rounded-2xl border border-line bg-stone/40 p-5 sm:p-7">
            <h2 id="diagnostico" className="font-display text-2xl">Seu diagnóstico</h2>
            <p className="text-sm">Em cada tema abaixo, marque se a empresa já atende. A ordem se recalcula na hora: o que já está atendido desce.</p>
            <p aria-live="polite" className="rounded-xl bg-white p-4 text-sm">
              {gap.semResposta === plano.temas.length ? <>Nenhum tema marcado ainda.</> : <>Lacuna informada: <strong>{gap.nao} obrigações</strong> em temas que vocês não atendem e <strong>{gap.parcial}</strong> em temas parciais. {gap.semResposta} {gap.semResposta === 1 ? 'tema' : 'temas'} sem resposta.</>}
            </p>
            <p className="text-xs text-ink-soft">As marcações ficam só nesta aba do navegador: nada é salvo nem enviado.</p>
            <div className="flex flex-wrap gap-3 print:hidden">
              <button type="button" onClick={() => baixarCsv(diag, sim)} className="inline-flex min-h-11 items-center gap-2 rounded-full bg-slate-blue px-5 text-sm font-medium text-ivory hover:bg-obsidian"><Download aria-hidden="true" className="h-4 w-4" />Baixar planilha (CSV)</button>
              <button type="button" onClick={() => window.print()} className="inline-flex min-h-11 items-center gap-2 rounded-full border border-obsidian/20 bg-white px-5 text-sm font-medium hover:border-obsidian/40"><Printer aria-hidden="true" className="h-4 w-4" />Imprimir ou salvar PDF</button>
            </div>
          </section>
        </div>
        <p className="rounded-xl border border-bronze/40 bg-stone/40 p-4 text-sm leading-relaxed">Iniciativa em validação. Valores ilustrativos, que não indicam descumprimento de uma empresa real. Prazos, enquadramentos e estimativas precisam de revisão de especialista. Não constitui parecer jurídico.</p>
      </section>

      <Simulador setSim={setSim} />

      <section aria-labelledby="temas">
        <p className={kicker}>Plano por tema</p>
        <h2 id="temas" className="font-display mt-2 text-3xl sm:text-4xl">Por onde começar</h2>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-ink-soft">{plano.regra_ordem}</p>
        <ol className="mt-6 space-y-5">{temas.map((t, n) => <CartaoTema key={t.id} tema={t} posicao={n + 1} diag={diag[t.id]} marcar={marcar} />)}</ol>
      </section>

      <ComoReduzir temas={temas} />

      <LinhaDoTempo />

      <section aria-labelledby="metodo"><details className="rounded-2xl border border-line bg-white p-5 sm:p-7">
        <summary className="font-display cursor-pointer text-2xl sm:text-3xl" id="metodo">Como chegamos aqui</summary>
        <div className="mt-5 max-w-3xl space-y-3 text-sm leading-relaxed">
          <p>A leitura automática da norma identificou {r.identificadas} itens. {r.fora_do_perfil} {r.fora_do_perfil === 1 ? 'vale' : 'valem'} só para transmissoras; os outros {r.aplicaveis} entram neste plano. Em {r.na_fila} o texto da obrigação nomeia o instrumento de uma infração da REN 846 e o grupo de multa é identificado; {r.a_confirmar} aguardam a confirmação do enquadramento por uma pessoa; {r.sem_multa} não têm multa estimável.</p>
          <p>Os temas seguem as seções da própria norma (por exemplo, “{plano.temas[0].fontes[0]?.titulo}”). Disposições transitórias vão para o tema do primeiro assunto que nomeiam.</p>
          <p>Prazos: calculados pelo motor temporal a partir da publicação ({dataBR(plano.norma.vigencia)}). Ficam provisórios até uma pessoa confirmar a contagem. Nenhuma data é presumida.</p>
          <p>Exposição: teto do grupo de infração (REN 846, Art. 8º) sobre a receita operacional líquida, limitado pelo teto legal. Sem simulação, a receita é a ilustrativa de {brl(plano.perfil.base_reais)}. {plano.perfil.origem_base} Sem faturamento bruto informado, o teto legal pode estar subestimado. Exposições de obrigações diferentes não devem ser somadas.</p>
          <p>Simulador por porte: Pequena ~{brl(plano.simulador.faixas[0].base)}, Média ~{brl(plano.simulador.faixas[1].base)}, Grande ~{brl(plano.simulador.faixas[2].base)} e Muito grande ~{brl(plano.simulador.faixas[3].base)} de receita operacional líquida anual. {plano.simulador.origem_faixas} A conta é a mesma do motor da Athenix (grupos I a V, percentuais da REN 846 e teto legal sobre o faturamento), refeita no seu navegador; um teste automático confere o resultado com o motor.</p>
          <p>Como reduzir a exposição: os textos citados vêm do catálogo de multas extraído do compilado oficial da REN 846 (SHA-256 indicado em cada citação). Os cenários com atenuante são do motor, com o valor base no teto do grupo (pior caso) e sem agravantes. Condição e efeito em linguagem simples são nossa interpretação e aguardam revisão humana. Causas externas só são citadas quando o texto da própria obrigação as prevê.</p>
          {plano.ia && <p><Tag kind="ai" /> {plano.ia.aviso} Modelo {plano.ia.modelo}. {plano.ia.criterio_titulos} Títulos marcados com <Sparkles aria-label="ícone de IA" className="inline h-3 w-3" /> foram resumidos com IA. Enquadramentos: {plano.ia.criterio_enquadramentos.toLowerCase()}</p>}
          <p className="break-all text-xs text-ink-soft">Documento preservado · SHA-256 {plano.norma.sha256} · gerado por {plano.gerado_por} (commit {plano.commit_origem}).</p>
        </div>
      </details></section>
      <footer className="border-t border-line pt-6 text-sm text-ink-soft">{plano.aviso} <a className="ml-2 underline print:hidden" href="/">Voltar à Athenix</a></footer>
    </main>
  </Simulado.Provider></Imprimindo.Provider>
}

function Numero({ valor, rotulo, destaque = false }: { valor: number | string; rotulo: string; destaque?: boolean }) {
  return <div className={`flex flex-col-reverse justify-end gap-2 rounded-xl border p-4 ${destaque ? 'border-pending/40 bg-[#f6ecd9]' : 'border-line bg-white'}`}>
    <dt className="text-xs leading-snug text-ink-soft">{rotulo}</dt>
    <dd className={`font-display text-3xl leading-none sm:text-4xl ${destaque ? 'text-pending' : ''}`}>{valor}</dd>
  </div>
}

const OPCOES: [Diagnostico, string][] = [['sim', 'Já temos'], ['parcial', 'Parcial'], ['nao', 'Não temos']]

function CartaoTema({ tema: t, posicao, diag, marcar }: { tema: Tema; posicao: number; diag?: Diagnostico; marcar: (id: string, d: Diagnostico) => void }) {
  const urgente = t.prazo_mais_urgente
  const sim = useContext(Simulado)
  const cont = (s: Situacao) => t.contagem[s]
  return <li className={`rounded-2xl border bg-white p-5 sm:p-7 ${diag === 'sim' ? 'border-line opacity-80' : 'border-line'}`}>
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="flex items-start gap-3">
        <span aria-label={`Posição ${posicao}`} className="font-display grid h-10 w-10 shrink-0 place-items-center rounded-full bg-stone text-xl">{posicao}</span>
        <div><h3 className="font-display text-2xl leading-tight">{t.nome}</h3><p className="text-sm text-ink-soft">{t.n} {t.n === 1 ? 'obrigação' : 'obrigações'}</p></div>
      </div>
      <fieldset className="print:hidden">
        <legend className="mb-1 text-xs text-ink-soft">Sua situação hoje</legend>
        <div className="inline-flex rounded-full border border-line bg-ivory p-1">
          {OPCOES.map(([v, rotulo]) => <label key={v} className="cursor-pointer rounded-full px-3 py-1.5 text-sm has-checked:bg-slate-blue has-checked:text-ivory has-focus-visible:outline-2 has-focus-visible:outline-slate-blue">
            <input type="radio" className="sr-only" name={`diag-${t.id}`} value={v} checked={diag === v} onChange={() => marcar(t.id, v)} />{rotulo}
          </label>)}
        </div>
      </fieldset>
      <p className="hidden text-sm print:block">Situação informada: {nomeDiag(diag)}</p>
    </div>
    <ul className="mt-4 flex flex-wrap gap-2 text-xs" aria-label="Por que nesta posição">{motivoPosicao(t, diag).map((m) => <li key={m} className="rounded-full bg-stone px-2.5 py-1">{m}</li>)}</ul>
    <dl className="mt-5 grid gap-4 border-y border-line py-5 text-sm sm:grid-cols-2 lg:grid-cols-4">
      <div><dt className="text-ink-soft">Prazo mais urgente</dt><dd className="mt-1 font-semibold">{urgente ? urgente.texto : 'Sem data no texto'}</dd>
        <dd className="mt-1 text-xs text-ink-soft">{[cont('vencida') && `${cont('vencida')} vencida(s)`, cont('recorrente') && `${cont('recorrente')} recorrente(s)`, cont('evento') && `${cont('evento')} dependem de evento`, cont('sem_prazo') && `${cont('sem_prazo')} sem prazo`].filter(Boolean).join(' · ')}</dd></div>
      <div><dt className="text-ink-soft">Enquadramento na REN 846</dt>
        {t.grupo_mais_grave ? <><dd className="mt-1 font-semibold">Grupo {t.grupos.join(', ')} · {t.infracoes.join('; ')}</dd><dd className="mt-1 text-xs text-ink-soft">Identificado pelo texto em {t.na_fila} de {t.n}; {t.a_confirmar} a confirmar.</dd></>
          : <dd className="mt-1 font-semibold">A confirmar</dd>}
        {t.ia && <dd className="mt-2 text-xs"><Tag kind="ai" /> <span className="text-ink-soft">sugere {t.ia.dispositivo} em {t.ia.n} de {t.ia.de}. Aguarda revisão humana; fora do cálculo.</span></dd>}</div>
      <div><dt className="text-ink-soft">Exposição</dt>
        <dd className="mt-1 font-semibold">{t.faixa ? textoFaixa(t.faixa, sim) : 'Não calculada até confirmar o enquadramento'}</dd>
        <dd className="mt-1 text-xs text-ink-soft">Valor provável: não estimável (sem histórico de multas). Não somar entre obrigações.</dd></div>
      <div><dt className="text-ink-soft">Como provar que cumpriu <Tag kind="review" label="Sugestão" /></dt>
        {t.evidencias.length ? <dd><ul className="mt-1 list-disc space-y-1 pl-4">{t.evidencias.map((e) => <li key={e.id}>{plano.evidencias[e.id]} <span className="text-xs text-ink-soft">({e.n})</span></li>)}</ul></dd> : <dd className="mt-1">Definir com a equipe responsável.</dd>}</div>
    </dl>
    <div className="mt-5"><h4 className="text-sm font-semibold">Obrigações principais</h4>
      <ul className="mt-2 space-y-2">{t.principais.map((id) => { const o = obrigacao(id); return <li key={id} className="flex flex-wrap items-baseline gap-x-3 gap-y-1"><Titulo o={o} /><span className="text-xs text-ink-soft">{o.prazo.texto}</span></li> })}</ul></div>
    <details className="mt-5 border-t border-line pt-4">
      <summary className="cursor-pointer font-semibold text-slate-blue">Ver as {t.n} obrigações e o porquê</summary>
      <ul className="mt-4 space-y-3">{t.obrigacoes.map((id) => <ItemObrigacao key={id} o={obrigacao(id)} />)}</ul>
    </details>
    {t.fontes.length > 0 && <p className="mt-4 text-xs text-ink-soft">Tema pela norma: {t.fontes.map((f) => `${f.rotulo}, “${f.titulo}”`).join('; ')}.</p>}
  </li>
}

function Titulo({ o }: { o: Obrigacao }) {
  return <span className="font-medium">{o.titulo}{o.titulo_origem === 'ia' && <Sparkles role="img" aria-label="título resumido com IA, a revisar" className="ml-1 inline h-3 w-3 text-slate-blue" />}</span>
}

function ItemObrigacao({ o }: { o: Obrigacao }) {
  const [aberto, setAberto] = useState(false)
  const imprimindo = useContext(Imprimindo)
  return <li className="rounded-xl border border-line"><details className="p-4" onToggle={(e) => setAberto(e.currentTarget.open)}>
    <summary className="cursor-pointer"><Titulo o={o} /><span className="ml-2 text-xs text-ink-soft">{o.prazo.texto}{o.dispositivo ? ` · ${o.dispositivo}` : ''}</span></summary>
    {(aberto || imprimindo) && <PorQue o={o} />}
  </details></li>
}

function PorQue({ o }: { o: Obrigacao }) {
  return <div className="mt-4 space-y-4 text-sm leading-relaxed">
      <div><h5 className="font-semibold">O que a norma diz <Tag kind="source" /></h5>
        {o.trecho ? <><blockquote className="mt-2 border-l-2 border-bronze bg-ivory p-3">“{o.trecho}”</blockquote><p className="mt-1 text-xs text-ink-soft">{o.dispositivo} · trecho literal conferido na fonte · <a className="underline" href={plano.norma.url}>{plano.norma.titulo}</a></p></>
          : <p className="mt-1">Sem citação verificada: confira o dispositivo na fonte. {o.motivo_sem_calculo}</p>}</div>
      <div><h5 className="font-semibold">Infração da REN 846</h5>
        {o.enquadramento.map((e) => <blockquote key={e.dispositivo} className="mt-2 border-l-2 border-slate-blue bg-ivory p-3"><strong>{e.dispositivo} · Grupo {e.grupo}</strong> <span className="text-xs text-ink-soft">(o texto da obrigação nomeia o instrumento desta infração)</span><p>“{plano.infracoes[e.dispositivo].trecho}”</p></blockquote>)}
        {!o.enquadramento.length && o.ia && <div className="mt-2 rounded-lg border border-dashed border-slate-blue/40 p-3">
          <p className="flex flex-wrap gap-2"><Tag kind="ai" /><Tag kind="review" /></p>
          <p className="mt-2"><strong>{o.ia.dispositivo} · Grupo {o.ia.grupo}</strong>: “{plano.infracoes[o.ia.dispositivo].trecho}”</p>
          <p className="mt-1 text-ink-soft">{o.ia.justificativa}</p>
          {o.ia.duvida && <p className="mt-1 text-xs text-pending">Depende da dúvida {o.ia.duvida} (duas redações para este inciso), em consulta a especialista.</p>}
          <p className="mt-1 text-xs">Não entra no cálculo até uma pessoa confirmar.</p></div>}
        {!o.enquadramento.length && !o.ia && <p className="mt-1">Enquadramento a confirmar.</p>}</div>
      <div><h5 className="font-semibold">Prazo</h5><p>{o.prazo.texto}{o.prazo.provisorio ? '. Data provisória: calculada a partir da publicação da norma, aguarda confirmação da contagem por uma pessoa.' : '.'}</p></div>
      {o.premissas.length > 0 && <div><h5 className="font-semibold">Premissas da faixa</h5><ul className="list-disc space-y-1 pl-5">{o.premissas.map((p) => <li key={p}>{p}</li>)}</ul></div>}
      {o.evidencias.length > 0 && <div><h5 className="font-semibold">Como provar <Tag kind="review" label="Sugestão" /></h5><ul className="list-disc space-y-1 pl-5">{o.evidencias.map((e) => <li key={e.id}>{plano.evidencias[e.id]}: <span className="text-ink-soft">“…{e.trecho}…”</span></li>)}</ul></div>}
      <p className="text-xs text-ink-soft">Tema: {o.motivo_tema}.</p>
    </div>
}

function LinhaDoTempo() {
  const colunas: { titulo: string; ids: string[]; vazio: string }[] = [
    { titulo: 'Vencidas', ids: plano.linha_do_tempo.vencida, vazio: 'Nenhuma.' },
    { titulo: 'Próximos 90 dias', ids: plano.linha_do_tempo['90dias'], vazio: 'Nenhuma obrigação vence nos próximos 90 dias.' },
    { titulo: 'Recorrentes', ids: plano.linha_do_tempo.recorrente, vazio: 'Nenhuma.' },
  ]
  const nomeTema = new Map(plano.temas.map((t) => [t.id, t.nome]))
  const semData = [...plano.linha_do_tempo.evento, ...plano.linha_do_tempo.sem_prazo]
  const porTema = plano.temas.map((t) => [t.nome, semData.filter((id) => obrigacao(id).tema === t.id).length] as const).filter(([, n]) => n)
  return <section aria-labelledby="linha">
    <p className={kicker}>Linha do tempo</p>
    <h2 id="linha" className="font-display mt-2 text-3xl sm:text-4xl">Quando cada coisa vence</h2>
    <p className="mt-3 max-w-3xl text-sm text-ink-soft">Datas calculadas a partir do texto da norma; nenhuma é presumida. {plano.linha_do_tempo.depois.length > 0 && `${plano.linha_do_tempo.depois.length} vencem depois de 90 dias.`}</p>
    <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {colunas.map((c) => <div key={c.titulo} className="rounded-2xl border border-line bg-white p-5">
        <h3 className="font-semibold">{c.titulo} <span className="text-ink-soft">({c.ids.length})</span></h3>
        {c.ids.length ? <ul className="mt-3 space-y-3 text-sm">{c.ids.map((id) => { const o = obrigacao(id); return <li key={id}><Titulo o={o} /><p className="text-xs text-ink-soft">{o.prazo.texto} · {nomeTema.get(o.tema)}</p></li> })}</ul> : <p className="mt-3 text-sm text-ink-soft">{c.vazio}</p>}
      </div>)}
      <div className="rounded-2xl border border-line bg-white p-5">
        <h3 className="font-semibold">Sem data <span className="text-ink-soft">({semData.length})</span></h3>
        <p className="mt-1 text-xs text-ink-soft">{plano.linha_do_tempo.evento.length} dependem de um evento ainda sem data; {plano.linha_do_tempo.sem_prazo.length} não têm prazo no texto.</p>
        <ul className="mt-3 space-y-1 text-sm">{porTema.map(([nome, n]) => <li key={nome} className="flex justify-between gap-3"><span>{nome}</span><span className="text-ink-soft">{n}</span></li>)}</ul>
      </div>
    </div>
  </section>
}

const numeroBR = (v: number) => v.toLocaleString('pt-BR', { maximumFractionDigits: 2 })
const emReais = (v: number, s: Simulacao | null) => (s ? brl(reaisDe(v, s)) : `${pct(v)} da receita`)

function Simulador({ setSim }: { setSim: (s: Simulacao | null) => void }) {
  const sim = useContext(Simulado)
  const faixas = plano.simulador.faixas
  const [porte, setPorte] = useState(faixas.find((f) => f.base === SIM_INICIAL.base)?.id ?? 'livre')
  const [rol, setRol] = useState(numeroBR(SIM_INICIAL.base))
  const [fat, setFat] = useState('')
  const aplicar = (rolT: string, fatT: string) => {
    const base = lerReais(rolT)
    const faturamento = fatT.trim() ? lerReais(fatT) : null
    setSim(base != null && (faturamento != null || !fatT.trim()) ? { base, faturamento } : null)
  }
  const rolInvalido = lerReais(rol) == null
  const fatInvalido = fat.trim() !== '' && lerReais(fat) == null
  const f = tetoGrupo
  const lei = f?.teto_legal_lei_pct ?? 0
  const atenuantes = plano.reducao.medidas.filter((m) => m.cenario)
  const campo = 'mt-1 min-h-11 w-full rounded-xl border bg-white px-3 text-base tabular-nums'
  return <section aria-labelledby="simulador" className="rounded-2xl border border-line bg-white p-5 sm:p-7">
    <p className={kicker}>Simular para minha empresa</p>
    <h2 id="simulador" className="font-display mt-2 text-3xl sm:text-4xl">Quanto pode custar no porte da sua empresa</h2>
    <p className="mt-3 max-w-3xl text-sm text-ink-soft">Escolha uma faixa de porte ou informe a receita da empresa. A conta roda no seu navegador: nada é enviado nem salvo.</p>
    <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_1fr]">
      <div className="space-y-5">
        <fieldset>
          <legend className="text-sm font-semibold">Porte (receita operacional líquida anual) <Tag kind="estimate" label="Faixa ilustrativa" /></legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {faixas.map((x) => <label key={x.id} className="cursor-pointer rounded-full border border-line bg-ivory px-4 py-2 text-sm has-checked:border-slate-blue has-checked:bg-slate-blue has-checked:text-ivory has-focus-visible:outline-2 has-focus-visible:outline-slate-blue">
              <input type="radio" className="sr-only" name="porte" value={x.id} checked={porte === x.id} onChange={() => { setPorte(x.id); const t = numeroBR(x.base); setRol(t); aplicar(t, fat) }} />
              {x.rotulo} <span className="opacity-75">~{brl(x.base)}</span>
            </label>)}
          </div>
        </fieldset>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm"><span className="font-semibold">Receita operacional líquida, 12 meses (R$)</span> <Tag kind="review" label="Premissa do usuário" />
            <input inputMode="decimal" autoComplete="off" className={`${campo} ${rolInvalido ? 'border-pending' : 'border-line'}`} value={rol} aria-invalid={rolInvalido} aria-describedby="rol-ajuda"
              onChange={(e) => { setRol(e.target.value); setPorte('livre'); aplicar(e.target.value, fat) }} />
            <span id="rol-ajuda" className={`mt-1 block text-xs ${rolInvalido ? 'text-pending' : 'text-ink-soft'}`}>{rolInvalido ? 'Informe um valor em reais, por exemplo 7.500.000.000.' : `Base da multa (REN 846, art. 21): ${brl(lerReais(rol)!)}.`}</span>
          </label>
          <label className="block text-sm"><span className="font-semibold">Faturamento bruto, 12 meses (R$, opcional)</span> <Tag kind="review" label="Premissa do usuário" />
            <input inputMode="decimal" autoComplete="off" className={`${campo} ${fatInvalido ? 'border-pending' : 'border-line'}`} value={fat} placeholder="em branco" aria-invalid={fatInvalido} aria-describedby="fat-ajuda"
              onChange={(e) => { setFat(e.target.value); aplicar(rol, e.target.value) }} />
            <span id="fat-ajuda" className={`mt-1 block text-xs ${fatInvalido ? 'text-pending' : 'text-ink-soft'}`}>{fatInvalido ? 'Valor inválido: deixe em branco ou informe em reais.' : 'Usado só no teto legal (Lei 9.427/1996, art. 3º, X).'}</span>
          </label>
        </div>
      </div>
      <div aria-live="polite" className="rounded-xl bg-stone/50 p-4 text-sm sm:p-5">
        {f && sim ? <>
          <p className="text-ink-soft">Grupo {r.grupo_mais_grave}, o mais grave identificado no plano</p>
          <p className="font-display mt-1 text-3xl leading-tight">até {brl(reaisDe(maximoPct(f, sim), sim))}</p>
          <p className="text-xs text-ink-soft">por infração ({pct(maximoPct(f, sim))} da receita). Pode ser só advertência.</p>
          <ul className="mt-3 space-y-1">{atenuantes.map((m) => { const v = comAtenuantePct(f, sim, m.cenario!); return v == null ? null : <li key={m.parametro}>Com o atenuante do {m.dispositivo}: até <strong>{brl(reaisDe(v, sim))}</strong></li> })}</ul>
          <p className="mt-3 text-xs text-ink-soft">{sim.faturamento == null
            ? `Faturamento bruto em branco: o teto legal (${pct(lei)} do faturamento) foi aplicado sobre a receita líquida e pode estar subestimado (dúvida D6).`
            : maximoPct(f, sim) < f.teto_grupo_pct
              ? `O teto legal limitou o valor: ${pct(lei)} do faturamento equivale a ${pct(tetoLegalPct(f, sim))} da receita.`
              : `O teto legal (${pct(lei)} do faturamento, ${brl((lei / 100) * sim.faturamento)}) não limita este valor.`}</p>
        </> : <p>Informe uma receita válida para ver os valores em reais. Os temas abaixo mostram percentuais enquanto isso.</p>}
        <p className="mt-3 border-t border-line pt-3 text-xs">Estimativa com premissas do usuário, sem agravantes. Não é parecer jurídico. Os valores dos temas abaixo usam esta simulação.</p>
      </div>
    </div>
  </section>
}

function Citado({ c }: { c: Citacao }) {
  return <div className="mt-2">
    <blockquote className="border-l-2 border-bronze bg-ivory p-3 text-sm">“{c.trecho}”</blockquote>
    <p className="mt-1 break-all text-xs text-ink-soft">{c.dispositivo} · {c.fonte} · SHA-256 {c.sha256}</p>
  </div>
}

function Interpretacao({ children }: { children: ReactNode }) {
  return <div className="mt-3 rounded-lg border border-dashed border-slate-blue/40 p-3 text-sm"><Tag kind="review" label="Interpretação · aguarda revisão humana" /><div className="mt-2 space-y-1">{children}</div></div>
}

function ComoReduzir({ temas }: { temas: Tema[] }) {
  const red = plano.reducao
  return <section aria-labelledby="reduzir">
    <p className={kicker}>Defesa e atenuantes</p>
    <h2 id="reduzir" className="font-display mt-2 text-3xl sm:text-4xl">Como reduzir a exposição</h2>
    <p className="mt-3 inline-block rounded-full border border-bronze/50 bg-stone/60 px-3 py-1 text-xs font-semibold">{red.rotulo}</p>
    <p className="mt-3 max-w-3xl text-sm leading-relaxed text-ink-soft">O que a REN 846 prevê para reduzir ou trocar a multa. Cada medida traz o texto da norma e, separada em caixa tracejada, a nossa leitura da condição e do efeito.</p>
    <div className="mt-6 grid gap-4 lg:grid-cols-2">{red.medidas.map((m) => <CartaoMedida key={m.parametro} m={m} />)}</div>
    <details className="mt-4 rounded-2xl border border-line bg-white p-5 sm:p-6">
      <summary className="cursor-pointer font-semibold text-slate-blue">Regras que valem para todos os atenuantes ({red.regras.map((c) => c.dispositivo).join('; ')})</summary>
      <div className="mt-3 space-y-3">{red.regras.map((c) => <Citado key={c.parametro} c={c} />)}</div>
      <Interpretacao><p>Os atenuantes não se somam: vale um só. E só contam se a cessação e a reparação forem comprovadas à Fiscalização antes do Auto de Infração. Por isso a prova datada precisa existir desde já.</p></Interpretacao>
    </details>
    <h3 className="font-display mt-10 text-2xl">Por tema</h3>
    <p className="mt-2 max-w-3xl text-sm text-ink-soft">Valores com a receita do simulador, por infração. Pior caso: valor base no teto do grupo, sem agravantes; cada cenário usa um único atenuante.</p>
    <ol className="mt-4 space-y-4">{temas.map((t) => <ReducaoTema key={t.id} t={t} />)}</ol>
  </section>
}

function CartaoMedida({ m }: { m: Medida }) {
  return <article className="rounded-2xl border border-line bg-white p-5">
    <div className="flex flex-wrap items-baseline justify-between gap-2">
      <h3 className="font-semibold leading-snug">{m.nome}</h3>
      <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${m.percentual != null ? 'bg-slate-blue text-ivory' : 'bg-stone text-ink-soft'}`}>{m.percentual != null ? `−${pct(m.percentual)}` : 'o texto não fixa percentual'}</span>
    </div>
    <p className="mt-2"><Tag kind="source" /></p>
    <Citado c={m} />
    <Interpretacao><p><strong>Condição:</strong> {m.condicao}</p><p><strong>Efeito:</strong> {m.efeito}</p></Interpretacao>
  </article>
}

function ReducaoTema({ t }: { t: Tema }) {
  const sim = useContext(Simulado)
  const s = sim ?? SIM_INICIAL
  const medidas = plano.reducao.medidas.filter((m) => m.cenario)
  return <li className="rounded-2xl border border-line bg-white p-5 sm:p-6">
    <h4 className="font-display text-xl leading-tight">{t.nome} <span className="text-sm text-ink-soft">· {t.n} {t.n === 1 ? 'obrigação' : 'obrigações'}</span></h4>
    <dl className="mt-4 grid gap-5 text-sm md:grid-cols-3">
      <div><dt className="text-ink-soft">Exposição por infração <Tag kind="estimate" /></dt>
        {t.faixa ? <dd><ul className="mt-1 space-y-1">
          <li>Sem atenuante: até <strong>{emReais(maximoPct(t.faixa, s), sim)}</strong></li>
          {medidas.map((m) => { const v = comAtenuantePct(t.faixa!, s, m.cenario!); return v == null ? null : <li key={m.parametro}>{m.dispositivo} (−{pct(m.percentual!)}): até <strong>{emReais(v, sim)}</strong></li> })}
        </ul><p className="mt-1 text-xs text-ink-soft">Grupo {t.grupos.join(', ')}. Também pode caber advertência (art. 6º).</p></dd>
          : <dd className="mt-1">Não calculada até confirmar o enquadramento. Se houver multa, os atenuantes do art. 24 reduzem o valor calculado em {medidas.map((m) => pct(m.percentual!)).join(' ou ')}, conforme a condição.</dd>}
      </div>
      <div><dt className="text-ink-soft">Causas externas (sistema de terceiro, caso fortuito, força maior)</dt>
        {t.excludentes.length ? <dd>{t.excludentes.map((e) => <blockquote key={e.obrigacao} className="mt-2 border-l-2 border-bronze bg-ivory p-3">“{e.trecho}” <span className="block text-xs text-ink-soft">{obrigacao(e.obrigacao).dispositivo} · {plano.norma.titulo}</span></blockquote>)}</dd>
          : <dd className="mt-1 font-semibold">{t.causa_externa}</dd>}
      </div>
      <div><dt className="text-ink-soft">O que guardar desde já <Tag kind="review" label="Sugestão" /></dt>
        {t.guardar.length ? <dd><ul className="mt-1 list-disc space-y-1 pl-4">{t.guardar.map((g) => <li key={g.id}>{plano.guardar[g.id]} <span className="text-xs text-ink-soft">({g.n} {g.n === 1 ? 'obrigação' : 'obrigações'})</span></li>)}</ul></dd>
          : <dd className="mt-1">Definir com a equipe responsável.</dd>}
        <dd className="mt-1 text-xs text-ink-soft">Boa prática, não exigência da norma.</dd>
      </div>
    </dl>
  </li>
}
