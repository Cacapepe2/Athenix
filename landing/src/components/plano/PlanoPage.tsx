import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { flushSync } from 'react-dom'
import { AlertTriangle, Download, Printer, Sparkles } from 'lucide-react'
import { Logo } from '../ui/Logo'
import { Tag } from '../product/Tag'
import {
  brl, brlCurto, comAtenuantePct, csvPlano, dataBR, decisoesDaSemana, exposicaoTema, lacuna, lerReais, manchete, NOTA_ADVERTENCIA, nomeDiag,
  obrigacao, ordenarTemas, pct, plano, reaisDe, situacaoPrazo, SIM_INICIAL, textoFaixa,
  type Citacao, type Diagnostico, type Diagnosticos, type Exposicao, type Medida, type Modo, type Obrigacao, type Simulacao, type Situacao, type Tema,
} from '../../content/plano'

const r = plano.resumo
const semData = r.por_situacao.evento + r.por_situacao.sem_prazo
const kicker = 'text-xs font-semibold tracking-widest text-bronze-deep uppercase'
const PRELIMINAR = 'cenário preliminar: inclui sugestões aguardando confirmação'
const ATENUANTES = plano.reducao.medidas.filter((m) => m.cenario)
// Impressão: todos os detalhes renderizados e abertos (fora dela, cada um renderiza só ao abrir).
const Imprimindo = createContext(false)
// Receita simulada (null: valor digitado inválido, mostra só percentuais) e modo do cenário. Nada sai do navegador.
const Cenario = createContext<{ sim: Simulacao | null; modo: Modo }>({ sim: SIM_INICIAL, modo: 'preliminar' })

function baixarCsv(diag: Diagnosticos, sim: Simulacao | null) {
  const url = URL.createObjectURL(new Blob([csvPlano(diag, sim)], { type: 'text/csv;charset=utf-8' }))
  const a = Object.assign(document.createElement('a'), { href: url, download: 'athenix-plano-rn1137-ilustrativo.csv' })
  a.click()
  URL.revokeObjectURL(url)
}

/** "R$ 50 milhões" com receita; "1,5% da receita" sem receita válida. */
const valor = (e: Exposicao) => (e.reais != null ? brl(e.reais) : `${pct(e.pct)} da receita`)
const valorCurto = (e: Exposicao) => (e.reais != null ? brlCurto(e.reais) : `${pct(e.pct)} da receita`)
const GRAVIDADE = ['I', 'II', 'III', 'IV', 'V']
const maisGrave = (gs: string[]) => [...gs].sort((a, b) => GRAVIDADE.indexOf(b) - GRAVIDADE.indexOf(a))[0]

/** Marca de valor que vem de sugestão (hachurada; o texto diz o mesmo, sem depender de cor). */
function Sugerido({ texto = 'sugerido' }: { texto?: string }) {
  return <span className="hachura-leve inline-flex items-center rounded-md border border-slate-blue/50 px-2 py-0.5 text-xs font-medium text-obsidian">{texto}</span>
}

export function PlanoPage() {
  const [diag, setDiag] = useState<Diagnosticos>({})
  const [imprimindo, setImprimindo] = useState(false)
  const [sim, setSim] = useState<Simulacao | null>(SIM_INICIAL)
  const [modo, setModo] = useState<Modo>('preliminar')
  const temas = useMemo(() => ordenarTemas(plano.temas, diag, sim, modo), [diag, sim, modo])
  const decisoes = decisoesDaSemana(plano.temas, diag, sim, modo)
  const m = manchete(plano.temas, diag, sim, modo)
  const gap = lacuna(plano.temas, diag)
  // Escala das barras: a maior exposição entre os temas visíveis vale 100%. Relativa (e não contra
  // os 3% do teto legal) para que as diferenças entre temas fiquem legíveis; o número vem escrito ao lado.
  const maiorPct = Math.max(0, ...temas.map((t) => exposicaoTema(t, sim, modo)?.pct ?? 0))
  // Impressão/PDF: renderiza e abre todos os detalhes para o papel levar o fundamento.
  useEffect(() => {
    const antes = () => {
      flushSync(() => setImprimindo(true))
      document.querySelectorAll('#plano details').forEach((d) => d.setAttribute('open', ''))
    }
    window.addEventListener('beforeprint', antes)
    return () => window.removeEventListener('beforeprint', antes)
  }, [])
  const marcar = (id: string, d: Diagnostico) => setDiag((atual) => ({ ...atual, [id]: d }))
  const vencidos = m.temasVencidos === 0 ? 'Nenhum tema com prazo vencido em aberto' : `${m.temasVencidos} ${m.temasVencidos === 1 ? 'tema' : 'temas'} com prazo vencido (data provisória)`
  const esc = plano.referencia_escala

  return <Imprimindo.Provider value={imprimindo}><Cenario.Provider value={{ sim, modo }}>
    <header className="border-b border-line bg-ivory print:hidden"><div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-8"><a href="/" aria-label="Athenix, voltar ao início"><Logo /></a><a href="/" className="text-sm font-semibold text-slate-blue">← Voltar ao site</a></div></header>
    <main id="plano" className="mx-auto max-w-7xl space-y-14 px-4 pt-6 pb-28 sm:px-8 sm:pt-10 print:pb-10">
      <section aria-labelledby="titulo-plano" className="space-y-6">
        <p className={kicker}>Plano de ação · RN 1.137/2025 · {plano.perfil.rotulo.toLowerCase()} (não é empresa real)</p>
        <Porte setSim={setSim} />

        <div className="grid items-start gap-5 lg:grid-cols-[1.45fr_1fr]">
        <div className="space-y-3">
        <div className="rounded-2xl border border-line bg-white p-5 shadow-soft sm:p-7">
          <p className="flex flex-wrap items-center gap-2 text-sm text-ink-soft">
            <Tag kind="pending" label="preliminar" />
            <span>Distribuidora de {sim ? brlCurto(sim.base) : 'receita a informar'} · RN 1.137/2025</span>
          </p>
          <h1 id="titulo-plano" aria-live="polite" className="font-display mt-3 text-[1.75rem] leading-tight sm:text-[2.6rem] sm:leading-[1.12]">
            {vencidos} · {m.maximo
              ? <>exposição de até <span className="whitespace-nowrap text-slate-blue">{valorCurto(m.maximo)}</span> por infração, no tema vencido mais exposto</>
              : 'exposição a enquadrar'}
          </h1>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            {modo === 'preliminar' && m.sugeridos > 0 && <Sugerido texto={PRELIMINAR} />}
            {modo === 'confirmados' && <span className="text-sm text-ink-soft">Só enquadramentos que o texto da obrigação nomeia.</span>}
            <button type="button" aria-pressed={modo === 'confirmados'} onClick={() => setModo(modo === 'preliminar' ? 'confirmados' : 'preliminar')}
              className="inline-flex min-h-11 items-center rounded-full border border-obsidian/20 bg-white px-4 text-sm font-medium hover:border-obsidian/40 print:hidden">
              {modo === 'preliminar' ? 'Mostrar só confirmados' : 'Voltar ao cenário preliminar'}
            </button>
          </div>
          <p className="mt-5 border-t border-line pt-4 text-sm">Referência do setor: mediana de {esc.autos} autos de infração publicados em distribuição (amostra pequena) ≈ <strong>{brlCurto(esc.mediana_reais)}</strong>; maior na amostra ≈ <strong>{brlCurto(esc.maximo_reais)}</strong>.</p>
          <p className="mt-1 text-xs text-ink-soft">{esc.rotulo}. É valor do auto inteiro, que pode reunir várias infrações. Detalhes em “Como chegamos aqui”.</p>
        </div>
        <p className="px-1 text-sm text-ink-soft">{r.aplicaveis} obrigações para distribuidoras · {r.por_situacao.vencida} com prazo vencido · {r.por_situacao['90dias']} vencem em 90 dias · {r.por_situacao.recorrente} recorrentes · {semData} sem data ({r.por_situacao.evento} dependem de evento)</p>
        </div>

          <section aria-labelledby="decisoes" className="rounded-2xl border border-line bg-white p-5 sm:p-7">
            <h2 id="decisoes" className="font-display text-2xl sm:text-3xl">{`${decisoes.length} ${decisoes.length === 1 ? 'decisão' : 'decisões'} para esta semana`}</h2>
            <ol className="mt-5 space-y-4">
              {decisoes.map((t, n) => { const e = exposicaoTema(t, sim, modo); return <li key={t.id} className="flex gap-3">
                <span aria-hidden="true" className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-slate-blue font-semibold text-ivory">{n + 1}</span>
                <div className="min-w-0">
                  <a href={`#tema-${t.id}`} className="font-semibold leading-snug text-slate-blue underline decoration-slate-blue/30 underline-offset-4 hover:decoration-slate-blue">{t.nome}</a>
                  <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
                    <span>{e ? <>até <strong>{valor(e)}</strong> por infração</> : 'exposição a enquadrar'}</span>
                    <span aria-hidden="true" className="text-ink-soft">·</span>
                    <span className="text-ink-soft">{situacaoPrazo(t)}</span>
                    {e?.origem === 'sugerido' && <Sugerido />}
                  </p>
                </div>
              </li> })}
            </ol>
            <p className="mt-5 border-t border-line pt-4 text-sm text-ink-soft">Designar quem confirma o enquadramento: confirmar enquadramentos libera o cálculo de {plano.decisoes.confirmar.temas_sem_calculo_confirmado} temas.</p>
          </section>
        </div>
          <section aria-labelledby="diagnostico" className="grid gap-4 rounded-2xl border border-line bg-stone/40 p-5 sm:p-6 lg:grid-cols-[1fr_1fr_auto] lg:items-center">
            <div><h2 id="diagnostico" className="font-display text-xl sm:text-2xl">Seu diagnóstico</h2>
              <p className="mt-1 text-sm">Em cada tema abaixo, marque se a empresa já atende. A ordem se recalcula na hora: o que já está atendido desce.</p></div>
            <div><p aria-live="polite" className="rounded-xl bg-white p-4 text-sm">
              {gap.semResposta === plano.temas.length ? <>Nenhum tema marcado ainda.</> : <>Lacuna informada: <strong>{gap.nao} obrigações</strong> em temas que vocês não atendem e <strong>{gap.parcial}</strong> em temas parciais. {gap.semResposta} {gap.semResposta === 1 ? 'tema' : 'temas'} sem resposta.</>}
            </p>
            <p className="mt-2 text-xs text-ink-soft">As marcações ficam só nesta aba do navegador: nada é salvo nem enviado.</p></div>
            <div className="flex flex-wrap gap-3 lg:flex-col print:hidden">
              <button type="button" onClick={() => baixarCsv(diag, sim)} className="inline-flex min-h-11 items-center gap-2 rounded-full bg-slate-blue px-5 text-sm font-medium text-ivory hover:bg-obsidian"><Download aria-hidden="true" className="h-4 w-4" />Baixar planilha (CSV)</button>
              <button type="button" onClick={() => window.print()} className="inline-flex min-h-11 items-center gap-2 rounded-full border border-obsidian/20 bg-white px-5 text-sm font-medium hover:border-obsidian/40"><Printer aria-hidden="true" className="h-4 w-4" />Imprimir ou salvar PDF</button>
            </div>
          </section>
      </section>

      <section aria-labelledby="temas">
        <p className={kicker}>Plano por tema</p>
        <h2 id="temas" className="font-display mt-2 text-3xl sm:text-4xl">Temas por valor em risco</h2>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-ink-soft">{plano.regra_ordem}</p>
        <p className="mt-2 max-w-3xl text-sm font-medium">Exposições de infrações diferentes não se somam: cada valor é o máximo de uma única infração.</p>
        <ol className="mt-6 space-y-5">{temas.map((t, n) => <CartaoTema key={t.id} tema={t} posicao={n + 1} diag={diag[t.id]} marcar={marcar} maiorPct={maiorPct} />)}</ol>
      </section>

      <ComoReduzir temas={temas} />

      <LinhaDoTempo />

      <section aria-labelledby="metodo"><details className="rounded-2xl border border-line bg-white p-5 sm:p-7">
        <summary className="font-display cursor-pointer text-2xl sm:text-3xl" id="metodo">Como chegamos aqui</summary>
        <div className="mt-5 max-w-3xl space-y-3 text-sm leading-relaxed">
          <p>A leitura automática da norma identificou {r.identificadas} itens. {r.fora_do_perfil} {r.fora_do_perfil === 1 ? 'vale' : 'valem'} só para transmissoras; os outros {r.aplicaveis} entram neste plano. Em {r.na_fila} o texto da obrigação nomeia o instrumento de uma infração da REN 846 e o grupo de multa é identificado; {r.a_confirmar} aguardam a confirmação do enquadramento por uma pessoa; {r.sem_multa} não têm multa estimável.</p>
          <p>Os temas seguem as seções da própria norma (por exemplo, “{plano.temas[0].fontes[0]?.titulo}”). Disposições transitórias vão para o tema do primeiro assunto que nomeiam.</p>
          <p>Prazos: calculados pelo motor temporal a partir da publicação ({dataBR(plano.norma.vigencia)}). Ficam provisórios até uma pessoa confirmar a contagem. Nenhuma data é presumida.</p>
          <p>Exposição: teto do grupo de infração (REN 846, Art. 8º) sobre a receita operacional líquida, limitado pelo teto legal. Sem simulação, a receita é a ilustrativa de {brl(plano.perfil.base_reais)}. {plano.perfil.origem_base} Sem faturamento bruto informado, o teto legal pode estar subestimado. Exposições de infrações diferentes não devem ser somadas. A manchete mostra a maior exposição por infração entre os temas com prazo vencido, nunca uma soma.</p>
          <p>Cenário preliminar e confirmados: no cenário preliminar (padrão), os enquadramentos sugeridos pela IA também contam, sempre marcados como “sugerido” e com barra hachurada; o cálculo continua sendo o do motor, só com o grupo sugerido. Em “Mostrar só confirmados” entram apenas os enquadramentos que o texto da obrigação nomeia. Nenhuma sugestão é confirmada em nome de uma pessoa.</p>
          <p>Porte, no topo da página: Pequena ~{brl(plano.simulador.faixas[0].base)}, Média ~{brl(plano.simulador.faixas[1].base)}, Grande ~{brl(plano.simulador.faixas[2].base)} e Muito grande ~{brl(plano.simulador.faixas[3].base)} de receita operacional líquida anual; em “Ajustar premissas” dá para informar a receita e o faturamento bruto. {plano.simulador.origem_faixas} A conta é a mesma do motor da Athenix (grupos I a V, percentuais da REN 846 e teto legal sobre o faturamento), refeita no seu navegador; um teste automático confere o resultado com o motor.</p>
          <p>Referência do setor: {esc.limites} Unidade: {esc.unidade}.</p>
          <p>Como reduzir a exposição: os textos citados vêm do catálogo de multas extraído do compilado oficial da REN 846 (SHA-256 indicado em cada citação). Os cenários com atenuante são do motor, com o valor base no teto do grupo (pior caso) e sem agravantes. Condição e efeito em linguagem simples são nossa interpretação e aguardam revisão humana. Causas externas só são citadas quando o texto da própria obrigação as prevê.</p>
          <p>Análise regulatória preliminar (em cada tema): tipo da obrigação por regras, com ideias de cumprimento e de evidência em rascunho, e dependências de terceiros só quando o trecho literal da norma as nomeia. Prática conhecida fora do texto da norma aparece separada, com referências públicas e o contraponto.</p>
          {plano.ia && <p><Tag kind="ai" /> {plano.ia.aviso} Modelo {plano.ia.modelo}. {plano.ia.criterio_titulos} Títulos marcados com <Sparkles aria-label="ícone de IA" className="inline h-3 w-3" /> foram resumidos com IA. Enquadramentos: {plano.ia.criterio_enquadramentos.toLowerCase()}</p>}
          <p className="break-all text-xs text-ink-soft">Documento preservado · SHA-256 {plano.norma.sha256} · gerado por {plano.gerado_por} (commit {plano.commit_origem}).</p>
        </div>
      </details></section>
      <footer className="border-t border-line pt-6 text-sm text-ink-soft">{plano.aviso} Iniciativa em validação. Valores ilustrativos, que não indicam descumprimento de uma empresa real. Não constitui parecer jurídico. <a className="ml-2 underline print:hidden" href="/">Voltar à Athenix</a></footer>
    </main>
    <div role="note" className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-obsidian/95 px-4 py-2.5 text-center text-xs leading-snug text-ivory print:hidden">
      Iniciativa em validação · valores ilustrativos · não constitui parecer jurídico
    </div>
  </Cenario.Provider></Imprimindo.Provider>
}

const numeroBR = (v: number) => v.toLocaleString('pt-BR', { maximumFractionDigits: 2 })

/** Porte no topo; receita e faturamento recolhidos em "Ajustar premissas". A conta roda no navegador. */
function Porte({ setSim }: { setSim: (s: Simulacao | null) => void }) {
  const { sim } = useContext(Cenario)
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
  const campo = 'mt-1 min-h-11 w-full rounded-xl border bg-white px-3 text-base tabular-nums'
  return <div className="space-y-3">
    <fieldset>
      <legend className="flex flex-wrap items-center gap-2 text-sm font-semibold">Porte da distribuidora (receita operacional líquida anual) <Tag kind="estimate" label="Faixa ilustrativa" /></legend>
      <div className="mt-2 grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
        {faixas.map((x) => <label key={x.id} className="inline-flex min-h-11 cursor-pointer flex-col items-center justify-center rounded-2xl border border-line bg-white px-3 py-1 text-center text-sm leading-tight sm:flex-row sm:gap-1 sm:rounded-full sm:px-4 has-checked:border-slate-blue has-checked:bg-slate-blue has-checked:text-ivory has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-slate-blue">
          <input type="radio" className="sr-only" name="porte" value={x.id} checked={porte === x.id} onChange={() => { setPorte(x.id); const t = numeroBR(x.base); setRol(t); aplicar(t, fat) }} />
          <span className="font-medium sm:font-normal">{x.rotulo}</span> <span className="text-xs whitespace-nowrap sm:text-sm">~{brlCurto(x.base)}</span>
        </label>)}
      </div>
    </fieldset>
    <details className="rounded-xl border border-line bg-white/60 print:hidden">
      <summary className="flex min-h-11 cursor-pointer items-center px-4 text-sm font-semibold text-slate-blue">Ajustar premissas{porte === 'livre' && sim ? ` · receita informada: ${brl(sim.base)}` : ''}</summary>
      <div className="grid gap-4 px-4 pb-4 sm:grid-cols-2">
        <label className="block text-sm"><span className="font-semibold">Receita operacional líquida, 12 meses (R$)</span> <Tag kind="review" label="Premissa do usuário" />
          <input inputMode="decimal" autoComplete="off" className={`${campo} ${rolInvalido ? 'border-pending' : 'border-line'}`} value={rol} aria-invalid={rolInvalido} aria-describedby="rol-ajuda"
            onChange={(e) => { setRol(e.target.value); setPorte('livre'); aplicar(e.target.value, fat) }} />
          <span id="rol-ajuda" className={`mt-1 block text-xs ${rolInvalido ? 'text-pending' : 'text-ink-soft'}`}>{rolInvalido ? 'Informe um valor em reais, por exemplo 7.500.000.000. Enquanto isso, os valores aparecem em % da receita.' : `Base da multa (REN 846, art. 21): ${brl(lerReais(rol)!)}.`}</span>
        </label>
        <label className="block text-sm"><span className="font-semibold">Faturamento bruto, 12 meses (R$, opcional)</span> <Tag kind="review" label="Premissa do usuário" />
          <input inputMode="decimal" autoComplete="off" className={`${campo} ${fatInvalido ? 'border-pending' : 'border-line'}`} value={fat} placeholder="em branco" aria-invalid={fatInvalido} aria-describedby="fat-ajuda"
            onChange={(e) => { setFat(e.target.value); aplicar(rol, e.target.value) }} />
          <span id="fat-ajuda" className={`mt-1 block text-xs ${fatInvalido ? 'text-pending' : 'text-ink-soft'}`}>{fatInvalido ? 'Valor inválido: deixe em branco ou informe em reais.' : 'Usado só no teto legal (Lei 9.427/1996, art. 3º, X). Em branco, o teto legal é aplicado sobre a receita líquida e pode estar subestimado (dúvida D6).'}</span>
        </label>
        <p className="text-xs text-ink-soft sm:col-span-2">Estimativa com premissas do usuário, sem agravantes. A conta roda no seu navegador: nada é enviado nem salvo.</p>
      </div>
    </details>
  </div>
}

const OPCOES: [Diagnostico, string][] = [['sim', 'Já temos'], ['parcial', 'Parcial'], ['nao', 'Não temos']]

function CartaoTema({ tema: t, posicao, diag, marcar, maiorPct }: { tema: Tema; posicao: number; diag?: Diagnostico; marcar: (id: string, d: Diagnostico) => void; maiorPct: number }) {
  const urgente = t.prazo_mais_urgente
  const { sim, modo } = useContext(Cenario)
  const e = exposicaoTema(t, sim, modo)
  const grupo = e && maisGrave(e.origem === 'confirmado' ? t.grupos : t.grupos_sugeridos)
  const cont = (s: Situacao) => t.contagem[s]
  return <li id={`tema-${t.id}`} className={`rounded-2xl border border-line bg-white p-5 sm:p-7 ${diag === 'sim' ? 'opacity-80' : ''}`}>
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="flex min-w-0 items-start gap-3">
        <span aria-label={`Posição ${posicao}`} className="font-display grid h-10 w-10 shrink-0 place-items-center rounded-full bg-stone text-xl">{posicao}</span>
        <div className="min-w-0"><h3 className="font-display text-2xl leading-tight">{t.nome}</h3>
          <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-ink-soft">
            <span>{situacaoPrazo(t)}</span><span aria-hidden="true">·</span>
            <span>{t.n} {t.n === 1 ? 'obrigação' : 'obrigações'}</span>
            {grupo && <><span aria-hidden="true">·</span><span>Grupo {grupo}</span>{e!.origem === 'confirmado' ? <span className="rounded-full bg-slate-blue px-2 py-0.5 text-xs font-medium text-ivory">confirmado</span> : <Sugerido />}</>}
            {diag === 'sim' && <><span aria-hidden="true">·</span><span>você marcou como já atendido</span></>}
          </p>
        </div>
      </div>
      <fieldset className="print:hidden">
        <legend className="mb-1 text-xs text-ink-soft">Sua situação hoje</legend>
        <div className="inline-flex rounded-full border border-line bg-ivory p-1">
          {OPCOES.map(([v, rotulo]) => <label key={v} className="inline-flex min-h-11 cursor-pointer items-center rounded-full px-3 text-sm has-checked:bg-slate-blue has-checked:text-ivory has-focus-visible:outline-2 has-focus-visible:outline-slate-blue">
            <input type="radio" className="sr-only" name={`diag-${t.id}`} value={v} checked={diag === v} onChange={() => marcar(t.id, v)} />{rotulo}
          </label>)}
        </div>
      </fieldset>
      <p className="hidden text-sm print:block">Situação informada: {nomeDiag(diag)}</p>
    </div>

    <div className="mt-5">
      {e ? <>
        <p className="text-lg"><span className="font-display text-2xl font-semibold sm:text-3xl">até {valor(e)}</span> <span className="text-ink-soft">por infração</span></p>
        <div className="mt-2 flex items-center gap-3">
          <div aria-hidden="true" className="h-3 flex-1 overflow-hidden rounded-full bg-stone print:border print:border-line">
            <div className={`h-full rounded-full ${e.origem === 'sugerido' ? 'hachura' : 'bg-slate-blue'}`} style={{ width: `${maiorPct ? Math.max(2, (e.pct / maiorPct) * 100) : 0}%` }} />
          </div>
          <span className="shrink-0 text-sm tabular-nums">{pct(e.pct)} da receita</span>
        </div>
        <p className="mt-1 text-xs text-ink-soft">{textoFaixa(e.faixa, sim)} ({NOTA_ADVERTENCIA}){e.origem === 'sugerido' ? ` · ${PRELIMINAR}` : ''}</p>
      </> : <p className="text-lg font-semibold">exposição a enquadrar <span className="block text-xs font-normal text-ink-soft">Sem enquadramento identificado nem sugerido: não há valor a mostrar.</span></p>}
    </div>

    <dl className="mt-5 grid gap-4 border-y border-line py-5 text-sm sm:grid-cols-3">
      <div><dt className="text-ink-soft">Prazo mais urgente</dt><dd className="mt-1 font-semibold">{urgente ? urgente.texto : 'Sem data no texto'}</dd>
        <dd className="mt-1 text-xs text-ink-soft">{[cont('vencida') && `${cont('vencida')} vencida(s)`, cont('recorrente') && `${cont('recorrente')} recorrente(s)`, cont('evento') && `${cont('evento')} dependem de evento`, cont('sem_prazo') && `${cont('sem_prazo')} sem prazo`].filter(Boolean).join(' · ')}</dd></div>
      <div><dt className="text-ink-soft">Enquadramento na REN 846</dt>
        {t.grupo_mais_grave ? <><dd className="mt-1 font-semibold">Grupo {t.grupos.join(', ')} · {t.infracoes.join('; ')}</dd><dd className="mt-1 text-xs text-ink-soft">Identificado pelo texto em {t.na_fila} de {t.n}; {t.a_confirmar} a confirmar.</dd></>
          : <dd className="mt-1 font-semibold">A confirmar</dd>}
        {t.ia && <dd className="mt-2 text-xs"><Tag kind="ai" /> <span className="text-ink-soft">sugere {t.ia.dispositivo} em {t.ia.n} de {t.ia.de}. Aguarda revisão humana; entra só no cenário preliminar, marcada.</span></dd>}</div>
      <div><dt className="text-ink-soft">Como provar que cumpriu <Tag kind="review" label="Sugestão" /></dt>
        {t.evidencias.length ? <dd><ul className="mt-1 list-disc space-y-1 pl-4">{t.evidencias.map((x) => <li key={x.id}>{plano.evidencias[x.id]} <span className="text-xs text-ink-soft">({x.n})</span></li>)}</ul></dd> : <dd className="mt-1">Definir com a equipe responsável.</dd>}</div>
    </dl>
    <div className="mt-5"><h4 className="text-sm font-semibold">Obrigações principais</h4>
      <ul className="mt-2 space-y-2">{t.principais.map((id) => { const o = obrigacao(id); return <li key={id} className="flex flex-wrap items-baseline gap-x-3 gap-y-1"><Titulo o={o} /><span className="text-xs text-ink-soft">{o.prazo.texto}</span></li> })}</ul></div>

    <AnalisePreliminar t={t} />

    <details className="mt-4 border-t border-line pt-4">
      <summary className="flex min-h-11 cursor-pointer items-center font-semibold text-slate-blue">Ver as {t.n} obrigações e o porquê</summary>
      {e && <Atenuantes e={e} />}
      <p className="mt-3 text-xs text-ink-soft">Valor provável: não estimável (sem histórico de multas). Não somar entre obrigações.</p>
      <ul className="mt-4 space-y-3">{t.obrigacoes.map((id) => <ItemObrigacao key={id} o={obrigacao(id)} />)}</ul>
    </details>
    {t.fontes.length > 0 && <p className="mt-4 text-xs text-ink-soft">Tema pela norma: {t.fontes.map((f) => `${f.rotulo}, “${f.titulo}”`).join('; ')}.</p>}
  </li>
}

/** Atenuantes do art. 24 sobre a faixa do tema (só no detalhe, nunca na manchete). */
function Atenuantes({ e }: { e: Exposicao }) {
  const { sim } = useContext(Cenario)
  const s = sim ?? SIM_INICIAL
  const itens = ATENUANTES.map((m) => [m, comAtenuantePct(e.faixa, s, m.cenario!)] as const).filter(([, v]) => v != null)
  if (!itens.length) return null
  return <p className="mt-3 text-sm">Com atenuante do {itens.map(([m, v], i) => <span key={m.parametro}>{i ? '; ' : ''}{m.dispositivo}: até <strong>{emReais(v!, sim)}</strong></span>)}. Vale um atenuante só; pior caso, sem agravantes{e.origem === 'sugerido' ? `; ${PRELIMINAR}` : ''}.</p>
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
          <p className="mt-1 text-xs">Entra só no cenário preliminar, marcada como sugerida, até uma pessoa confirmar.</p></div>}
        {!o.enquadramento.length && !o.ia && <p className="mt-1">Enquadramento a confirmar.</p>}</div>
      <div><h5 className="font-semibold">Prazo</h5><p>{o.prazo.texto}{o.prazo.provisorio ? '. Data provisória: calculada a partir da publicação da norma, aguarda confirmação da contagem por uma pessoa.' : '.'}</p></div>
      {o.premissas.length > 0 && <div><h5 className="font-semibold">Premissas da faixa</h5><ul className="list-disc space-y-1 pl-5">{o.premissas.map((p) => <li key={p}>{p}</li>)}</ul></div>}
      {o.evidencias.length > 0 && <div><h5 className="font-semibold">Como provar <Tag kind="review" label="Sugestão" /></h5><ul className="list-disc space-y-1 pl-5">{o.evidencias.map((e) => <li key={e.id}>{plano.evidencias[e.id]}: <span className="text-ink-soft">“…{e.trecho}…”</span></li>)}</ul></div>}
      <p className="text-xs text-ink-soft">Tema: {o.motivo_tema}.</p>
    </div>
}

const SELO_ANALISE = plano.analise.rotulo.includes('revisar com o jurídico') ? plano.analise.rotulo : `${plano.analise.rotulo} · revisar com o jurídico`

/** Análise regulatória preliminar do tema: recolhida; o conteúdo só é montado ao abrir (ou na impressão). */
function AnalisePreliminar({ t }: { t: Tema }) {
  const [aberto, setAberto] = useState(false)
  const imprimindo = useContext(Imprimindo)
  return <details className="mt-5 rounded-xl border border-line bg-ivory" onToggle={(e) => setAberto(e.currentTarget.open)}>
    <summary className="flex min-h-11 cursor-pointer flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2 font-semibold text-slate-blue">Análise regulatória preliminar <span className="text-xs font-normal text-ink-soft">tipo de obrigação, como cumprir, o que provar</span></summary>
    {(aberto || imprimindo) && <ConteudoAnalise t={t} />}
  </details>
}

function DependenciaAto({ itens }: { itens: { obrigacao?: string; id: string; trecho_literal: string }[] }) {
  const ato = itens.filter((d) => d.id === 'ato_da_aneel')
  const outros = itens.filter((d) => d.id !== 'ato_da_aneel')
  const bloco = (titulo: string, lista: typeof itens) => lista.length > 0 && <div className="rounded-lg border border-pending/50 bg-[#f6ecd9] p-3">
    <p className="flex items-start gap-2 font-semibold text-obsidian"><AlertTriangle aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-pending" />{titulo}</p>
    {lista.map((d) => <figure key={`${d.obrigacao ?? ''}${d.trecho_literal}`} className="mt-2">
      <blockquote className="border-l-2 border-bronze bg-white p-2 text-sm">“{d.trecho_literal}”</blockquote>
      <figcaption className="mt-1 text-xs text-ink-soft">{d.obrigacao ? `${obrigacao(d.obrigacao).dispositivo ?? 'dispositivo a confirmar'} · ` : ''}trecho literal conferido na fonte</figcaption>
    </figure>)}
  </div>
  return <>
    {bloco('Prazo condicionado a ato da ANEEL: verificar se as instruções foram publicadas', ato)}
    {outros.length > 0 && bloco(`Cumprimento depende de terceiro: ${plano.analise.dependencias[outros[0].id]?.nome ?? 'a avaliar'}`, outros)}
  </>
}

function ConteudoAnalise({ t }: { t: Tema }) {
  const a = plano.analise
  const pratica = a.pratica_por_tema[t.id] ? a.dependencias[a.pratica_por_tema[t.id]] : undefined
  return <div className="space-y-5 px-4 pb-4 text-sm leading-relaxed">
    <p className="inline-block rounded-md border border-pending/50 bg-[#f6ecd9] px-2.5 py-1 text-xs font-semibold text-pending">{SELO_ANALISE}</p>
    {t.dependencias_no_texto.length > 0 && <DependenciaAto itens={t.dependencias_no_texto} />}
    {t.principais.map((id) => <AnaliseObrigacao key={id} o={obrigacao(id)} />)}
    {pratica && <div className="rounded-lg border border-dashed border-line p-3 text-xs">
      <h5 className="text-sm font-semibold">Prática conhecida (fora do texto da norma) <Tag kind="review" label="Sugestão" /></h5>
      <p className="mt-1 font-medium">{pratica.nome}</p>
      <p className="mt-1 text-ink-soft">{pratica.cautela}</p>
      <p className="mt-2"><strong>Caminho:</strong> {pratica.caminho}</p>
      <p className="mt-2 font-semibold">O que guardar desde já</p>
      <ul className="mt-1 list-disc space-y-0.5 pl-4">{pratica.o_que_guardar.map((g) => <li key={g}>{g}</li>)}</ul>
      <p className="mt-2 font-semibold">Referências públicas</p>
      <ul className="mt-1 space-y-1">
        {pratica.precedentes.filter((p) => p.titulo !== a.contraponto.titulo).map((p) => <Referencia key={p.id} titulo={p.titulo} urls={p.urls} nota={p.a_confirmar} />)}
        <Referencia titulo={a.contraponto.titulo} urls={a.contraponto.urls} nota={a.contraponto.a_confirmar} rotulo="Contraponto" />
      </ul>
    </div>}
  </div>
}

function Referencia({ titulo, urls, nota, rotulo }: { titulo: string; urls: string[]; nota: string; rotulo?: string }) {
  const host = (u: string) => { try { return new URL(u).hostname.replace(/^www\./, '') } catch { return u } }
  return <li>{rotulo && <strong>{rotulo}: </strong>}{titulo}{' '}
    {urls.map((u, i) => <span key={u}>{i ? ', ' : '('}<a className="break-all text-slate-blue underline" href={u} rel="noopener noreferrer" target="_blank">{host(u)}</a>{i === urls.length - 1 ? ')' : ''}</span>)}
    <span className="block text-ink-soft">{nota}</span></li>
}

function AnaliseObrigacao({ o }: { o: Obrigacao }) {
  const an = o.analise
  const tipo = an?.tipo
  const manual = tipo && tipo.id && (tipo.situacao === 'concordam' || tipo.situacao === 'so_regra') ? plano.analise.manuais[tipo.id] : undefined
  const nomeTipo = !tipo ? 'tipo a revisar'
    : tipo.situacao === 'concordam' ? tipo.nome
      : tipo.situacao === 'so_regra' ? `${tipo.nome} · só pela regra, segunda leitura da IA não feita (a revisar)`
        : tipo.situacao === 'a_revisar' ? 'tipo a revisar' : 'sem tipo próprio'
  return <article className="border-t border-line pt-4">
    <h5 className="font-semibold"><Titulo o={o} /> <span className="text-xs font-normal text-ink-soft">· {o.dispositivo ?? 'dispositivo a confirmar'}</span></h5>
    <p className="mt-2 text-xs font-semibold tracking-wide text-ink-soft uppercase">O que a norma exige <Tag kind="source" /></p>
    {o.trecho ? <><blockquote className="mt-1 border-l-2 border-bronze bg-white p-3">“{o.trecho}”</blockquote><p className="mt-1 text-xs text-ink-soft">{o.dispositivo} · trecho literal conferido na fonte</p></>
      : <p className="mt-1">Sem citação verificada: confira o dispositivo na fonte.</p>}
    {an && an.dependencias_no_texto.some((d) => d.id === 'ato_da_aneel') && <p className="mt-2 flex items-start gap-2 text-xs font-semibold text-pending"><AlertTriangle aria-hidden="true" className="mt-0.5 h-3.5 w-3.5 shrink-0" />Prazo condicionado a ato da ANEEL: verificar se as instruções foram publicadas.</p>}
    <p className="mt-3"><span className="text-ink-soft">Tipo:</span> {nomeTipo}</p>
    {manual && <div className="mt-3 grid gap-4 sm:grid-cols-2">
      <div><p className="font-semibold">Como cumprir <Tag kind="review" label="Sugestão" /></p><ul className="mt-1 list-disc space-y-1 pl-4">{manual.ideias_cumprimento.map((x) => <li key={x}>{x}</li>)}</ul></div>
      <div><p className="font-semibold">O que provar para a ANEEL <Tag kind="review" label="Sugestão" /></p><ul className="mt-1 list-disc space-y-1 pl-4">{manual.evidencias.map((x) => <li key={x}>{x}</li>)}</ul></div>
    </div>}
  </article>
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

const emReais = (v: number, s: Simulacao | null) => (s ? brl(reaisDe(v, s)) : `${pct(v)} da receita`)

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
    <p className="mt-2 max-w-3xl text-sm text-ink-soft">Valores com a receita escolhida no topo, por infração. Pior caso: valor base no teto do grupo, sem agravantes; cada cenário usa um único atenuante.</p>
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
  const { sim, modo } = useContext(Cenario)
  const s = sim ?? SIM_INICIAL
  const e = exposicaoTema(t, sim, modo)
  const f = e?.faixa
  return <li className="rounded-2xl border border-line bg-white p-5 sm:p-6">
    <h4 className="font-display text-xl leading-tight">{t.nome} <span className="text-sm text-ink-soft">· {t.n} {t.n === 1 ? 'obrigação' : 'obrigações'}</span></h4>
    <dl className="mt-4 grid gap-5 text-sm md:grid-cols-3">
      <div><dt className="flex flex-wrap items-center gap-1 text-ink-soft">Exposição por infração <Tag kind="estimate" />{e?.origem === 'sugerido' && <Sugerido />}</dt>
        {e && f ? <dd><ul className="mt-1 space-y-1">
          <li>Sem atenuante: até <strong>{valor(e)}</strong></li>
          {ATENUANTES.map((m) => { const v = comAtenuantePct(f, s, m.cenario!); return v == null ? null : <li key={m.parametro}>{m.dispositivo} (−{pct(m.percentual!)}): até <strong>{emReais(v, sim)}</strong></li> })}
        </ul><p className="mt-1 text-xs text-ink-soft">Grupo {maisGrave(e.origem === 'confirmado' ? t.grupos : t.grupos_sugeridos)}{e.origem === 'sugerido' ? ` (${PRELIMINAR})` : ''}. Também pode caber advertência (art. 6º).</p></dd>
          : <dd className="mt-1">Exposição a enquadrar. Se houver multa, os atenuantes do art. 24 reduzem o valor calculado em {ATENUANTES.map((m) => pct(m.percentual!)).join(' ou ')}, conforme a condição.</dd>}
      </div>
      <div><dt className="text-ink-soft">Causas externas (sistema de terceiro, caso fortuito, força maior)</dt>
        {t.excludentes.length ? <dd>{t.excludentes.map((x) => <blockquote key={x.obrigacao} className="mt-2 border-l-2 border-bronze bg-ivory p-3">“{x.trecho}” <span className="block text-xs text-ink-soft">{obrigacao(x.obrigacao).dispositivo} · {plano.norma.titulo}</span></blockquote>)}</dd>
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
