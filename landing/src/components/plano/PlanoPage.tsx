import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { flushSync } from 'react-dom'
import { Download, Printer, Sparkles } from 'lucide-react'
import { Logo } from '../ui/Logo'
import { Tag } from '../product/Tag'
import {
  brl, csvPlano, dataBR, lacuna, motivoPosicao, nomeDiag, obrigacao, ordenarTemas, pct, plano, textoFaixa,
  type Diagnostico, type Diagnosticos, type Obrigacao, type Situacao, type Tema,
} from '../../content/plano'

const r = plano.resumo
const semData = r.por_situacao.evento + r.por_situacao.sem_prazo
const tetoGrupo = plano.obrigacoes.find((o) => o.grupo === r.grupo_mais_grave)?.faixa
const kicker = 'text-xs font-semibold tracking-widest text-bronze-deep uppercase'
// Impressão: todos os detalhes renderizados e abertos (fora dela, cada um renderiza só ao abrir).
const Imprimindo = createContext(false)

function baixarCsv(diag: Diagnosticos) {
  const url = URL.createObjectURL(new Blob([csvPlano(diag)], { type: 'text/csv;charset=utf-8' }))
  const a = Object.assign(document.createElement('a'), { href: url, download: 'athenix-plano-rn1137-ilustrativo.csv' })
  a.click()
  URL.revokeObjectURL(url)
}

export function PlanoPage() {
  const [diag, setDiag] = useState<Diagnosticos>({})
  const temas = useMemo(() => ordenarTemas(plano.temas, diag), [diag])
  const gap = lacuna(plano.temas, diag)
  const [imprimindo, setImprimindo] = useState(false)
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

  return <Imprimindo.Provider value={imprimindo}>
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
              <button type="button" onClick={() => baixarCsv(diag)} className="inline-flex min-h-11 items-center gap-2 rounded-full bg-slate-blue px-5 text-sm font-medium text-ivory hover:bg-obsidian"><Download aria-hidden="true" className="h-4 w-4" />Baixar planilha (CSV)</button>
              <button type="button" onClick={() => window.print()} className="inline-flex min-h-11 items-center gap-2 rounded-full border border-obsidian/20 bg-white px-5 text-sm font-medium hover:border-obsidian/40"><Printer aria-hidden="true" className="h-4 w-4" />Imprimir ou salvar PDF</button>
            </div>
          </section>
        </div>
        <p className="rounded-xl border border-bronze/40 bg-stone/40 p-4 text-sm leading-relaxed">Iniciativa em validação. Valores ilustrativos, que não indicam descumprimento de uma empresa real. Prazos, enquadramentos e estimativas precisam de revisão de especialista. Não constitui parecer jurídico.</p>
      </section>

      <section aria-labelledby="temas">
        <p className={kicker}>Plano por tema</p>
        <h2 id="temas" className="font-display mt-2 text-3xl sm:text-4xl">Por onde começar</h2>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-ink-soft">{plano.regra_ordem}</p>
        <ol className="mt-6 space-y-5">{temas.map((t, n) => <CartaoTema key={t.id} tema={t} posicao={n + 1} diag={diag[t.id]} marcar={marcar} />)}</ol>
      </section>

      <LinhaDoTempo />

      <section aria-labelledby="metodo"><details className="rounded-2xl border border-line bg-white p-5 sm:p-7">
        <summary className="font-display cursor-pointer text-2xl sm:text-3xl" id="metodo">Como chegamos aqui</summary>
        <div className="mt-5 max-w-3xl space-y-3 text-sm leading-relaxed">
          <p>A leitura automática da norma identificou {r.identificadas} itens. {r.fora_do_perfil} {r.fora_do_perfil === 1 ? 'vale' : 'valem'} só para transmissoras; os outros {r.aplicaveis} entram neste plano. Em {r.na_fila} o texto da obrigação nomeia o instrumento de uma infração da REN 846 e o grupo de multa é identificado; {r.a_confirmar} aguardam a confirmação do enquadramento por uma pessoa; {r.sem_multa} não têm multa estimável.</p>
          <p>Os temas seguem as seções da própria norma (por exemplo, “{plano.temas[0].fontes[0]?.titulo}”). Disposições transitórias vão para o tema do primeiro assunto que nomeiam.</p>
          <p>Prazos: calculados pelo motor temporal a partir da publicação ({dataBR(plano.norma.vigencia)}). Ficam provisórios até uma pessoa confirmar a contagem. Nenhuma data é presumida.</p>
          <p>Exposição: teto do grupo de infração (REN 846, Art. 8º) sobre a receita operacional líquida ilustrativa de {brl(plano.perfil.base_reais)}, limitado pelo teto legal. {plano.perfil.origem_base} Faturamento bruto não informado: o teto legal pode estar subestimado. Exposições de obrigações diferentes não devem ser somadas.</p>
          {plano.ia && <p><Tag kind="ai" /> {plano.ia.aviso} Modelo {plano.ia.modelo}. {plano.ia.criterio_titulos} Títulos marcados com <Sparkles aria-label="ícone de IA" className="inline h-3 w-3" /> foram resumidos com IA. Enquadramentos: {plano.ia.criterio_enquadramentos.toLowerCase()}</p>}
          <p className="break-all text-xs text-ink-soft">Documento preservado · SHA-256 {plano.norma.sha256} · gerado por {plano.gerado_por} (commit {plano.commit_origem}).</p>
        </div>
      </details></section>
      <footer className="border-t border-line pt-6 text-sm text-ink-soft">{plano.aviso} <a className="ml-2 underline print:hidden" href="/">Voltar à Athenix</a></footer>
    </main>
  </Imprimindo.Provider>
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
        <dd className="mt-1 font-semibold">{t.faixa ? textoFaixa(t.faixa) : 'Não calculada até confirmar o enquadramento'}</dd>
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
