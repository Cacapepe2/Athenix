// "O que recomendamos" por tema (plano completo): até 3 ações, o que guardar como prova (até 3), defesa
// possível (só se houver), "Evite" (só se houver) e o efeito financeiro de agir. Tudo vem dos dados do plano:
// as ações são as recomendações ESPECÍFICAS por dispositivo (IA, "Sugestão"); as provas, do manual do tipo.
import { defesa } from './executivo.ts'
import { exposicaoTema, planos, reaisDe, SIM_INICIAL, type Modo, type Obrigacao, type PlanoDados, type Simulacao, type Tema } from './plano.ts'

export interface ProvaSugerida { id: string; texto: string }
export interface EfeitoDeAgir { reducaoPct: number; de: number | null; para: number | null; dispositivo: string }
export interface RecomendacaoDoTema {
  acoes: string[]
  provas: ProvaSugerida[]
  defesa: { texto: string; origem: 'no texto' | 'prática conhecida' } | null
  evite: string | null
  efeito: EfeitoDeAgir | null
}

const INMET = /INMET/
const PROVA_INMET = /alerta recebido/i

const idDoTipo = (o: Obrigacao) => o.analise?.tipo?.id ?? o.analise?.tipo?.regra_id ?? null

export function provasDoTema(p: PlanoDados, obrigacoes: Obrigacao[]): ProvaSugerida[] {
  const vistas = new Set<string>()
  const todas: ProvaSugerida[] = []
  for (const o of obrigacoes) {
    const tipo = idDoTipo(o)
    p.analise.manuais[tipo ?? '']?.evidencias.forEach((texto, i) => {
      const id = `${tipo}:${i}`
      if (!vistas.has(id)) { vistas.add(id); todas.push({ id, texto }) }
    })
  }
  return todas
}

export function recomendacoesDoTema(p: PlanoDados, t: Tema, s: Simulacao | null = SIM_INICIAL, modo: Modo = 'preliminar'): RecomendacaoDoTema {
  const por = new Map(p.obrigacoes.map((o) => [o.id, o]))
  const ordem = [...t.principais, ...t.obrigacoes.filter((id) => !t.principais.includes(id))].map((id) => por.get(id)!).filter(Boolean)

  const acoes: string[] = []
  for (const o of ordem) {
    const a = o.recomendacoes[0]?.acao
    if (a && !acoes.includes(a) && acoes.length < 3) acoes.push(a)
  }
  // Tipo "comunicar consumidores": acrescenta a ideia do aviso preventivo por alerta meteorológico oficial (só a ideia).
  const comunica = ordem.find((o) => idDoTipo(o) === 'comunicar_consumidores')
  const ideiaInmet = comunica ? p.analise.manuais.comunicar_consumidores?.ideias_cumprimento.find((x) => INMET.test(x)) : undefined
  if (ideiaInmet && !acoes.includes(ideiaInmet)) {
    if (acoes.length >= 3) acoes[2] = ideiaInmet
    else acoes.push(ideiaInmet)
  }

  let provas = provasDoTema(p, ordem).slice(0, 3)
  if (ideiaInmet) {
    const inmet = provasDoTema(p, ordem).find((x) => PROVA_INMET.test(x.texto))
    if (inmet && !provas.some((x) => x.id === inmet.id)) provas = [...provas.slice(0, 2), inmet]
  }

  let def: RecomendacaoDoTema['defesa'] = null
  for (const o of ordem) {
    const d = defesa(p, o)
    if (d.origem) { def = { texto: d.texto, origem: d.origem }; break }
  }
  const evite = ordem.find((o) => o.evite)?.evite?.acao ?? null

  const e = exposicaoTema(t, s, modo)
  const m = p.reducao.medidas.find((x) => x.cenario === 'espontanea')
  const efeito = e && m?.percentual != null
    ? { reducaoPct: m.percentual, de: e.reais, para: s ? reaisDe(e.pct * (1 - m.percentual / 100), s) : null, dispositivo: m.dispositivo }
    : null
  return { acoes, provas, defesa: def, evite, efeito }
}

export const planoDaNorma = (id: 'rn1137' | 'ren1174') => planos[id]
