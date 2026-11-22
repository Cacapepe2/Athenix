import { test } from 'node:test'
import assert from 'node:assert/strict'
import { COLUNAS_TAREFAS, calendarioIcs, dobrar, recorrenciaDoTexto, tarefasCsv } from './tarefas.ts'
import { blocosDoPlano } from './filtros.ts'
import { NORMAS } from './executivo.ts'
import { planos, SIM_INICIAL } from './plano.ts'

const todos = blocosDoPlano(SIM_INICIAL, 'preliminar')
const octetos = (l: string) => new TextEncoder().encode(l).length

test('toda obrigação tem área sugerida, dentre as áreas; sem tipo vai para "A definir", não para Regulatório', () => {
  const lista = planos.rn1137.analise.areas.lista
  assert.deepEqual(lista, ['Regulatório', 'Operação/Manutenção', 'Comunicação/Atendimento', 'TI/Sistemas', 'Meio Ambiente/Arborização', 'Jurídico', 'A definir'])
  for (const b of todos) assert.ok(lista.includes(b.area), `${b.norma} ${b.dispositivo}: ${b.area}`)
  assert.ok(todos.some((b) => b.area === 'A definir'))
})

test('CSV de tarefas: aviso na primeira linha, colunas pedidas, marca de IA, uma linha por obrigação da área', () => {
  assert.deepEqual(COLUNAS_TAREFAS.slice(0, 6), ['obrigação', 'dispositivo', 'prazo', 'valor por infração', 'ação recomendada', 'o que provar'])
  const area = 'Comunicação/Atendimento'
  const csv = tarefasCsv(todos, area)
  const linhas = csv.trimEnd().split('\r\n')
  assert.equal(linhas[0], '"Análise regulatória preliminar · valores ilustrativos · não constitui parecer jurídico"')
  assert.match(linhas[1], /^"obrigação","dispositivo","prazo","valor por infração","ação recomendada","o que provar"/)
  assert.equal(linhas.length - 2, todos.filter((b) => b.area === area).length)
  assert.equal(tarefasCsv(todos, null).trimEnd().split('\r\n').length - 2, todos.length)
  assert.match(csv, /sugestão \(IA\), a revisar/)
})

test('fórmula em célula do CSV é neutralizada (aspas simples antes de = + - @)', () => {
  const blocos = todos.slice(0, 1).map((b) => ({ ...b, frase: '=HYPERLINK("http://x")', dispositivo: '+cmd', proveCom: '@SUM(A1)' }))
  const csv = tarefasCsv(blocos, null)
  assert.ok(csv.includes('"\'=HYPERLINK(""http://x"")"'))
  assert.ok(csv.includes('"\'+cmd"') && csv.includes('"\'@SUM(A1)"'))
})

test('recorrência lida do texto: semestral, anual, a cada 12 meses; "manual" e "bissemestral" não casam', () => {
  assert.equal(recorrenciaDoTexto('encaminhados à ANEEL, semestralmente, relatórios'), 'FREQ=MONTHLY;INTERVAL=6')
  assert.equal(recorrenciaDoTexto('com periodicidade anual'), 'FREQ=YEARLY')
  assert.equal(recorrenciaDoTexto('a cada período de 12 meses'), 'FREQ=YEARLY')
  assert.equal(recorrenciaDoTexto('apurados mensalmente'), 'FREQ=MONTHLY')
  assert.equal(recorrenciaDoTexto('sem periodicidade'), null)
  assert.equal(recorrenciaDoTexto('procedimento manual de revisão'), null)
  assert.equal(recorrenciaDoTexto('relatório bissemestral'), null)
})

test('calendário .ics: formato válido, prazos e recorrências, marca de IA, linhas até 75 octetos', () => {
  const entradas = NORMAS.map((n) => ({ norma: n.id, vigencia: n.dados.norma.vigencia, blocos: todos.filter((b) => b.norma === n.id), trechos: Object.fromEntries(n.dados.obrigacoes.map((o) => [o.id, o.trecho ?? ''])) }))
  const ics = calendarioIcs(entradas, null, new Date('2026-11-20T12:00:00Z'))
  assert.match(ics, /^BEGIN:VCALENDAR\r\nVERSION:2\.0\r\n/)
  assert.match(ics, /END:VCALENDAR\r\n$/)
  const comData = todos.filter((b) => b.dataPrazo).length
  assert.ok(comData > 0 && (ics.match(/BEGIN:VEVENT/g) ?? []).length >= comData)
  assert.equal((ics.match(/BEGIN:VEVENT/g) ?? []).length, (ics.match(/END:VEVENT/g) ?? []).length)
  assert.match(ics, /DTSTART;VALUE=DATE:\d{8}/)
  assert.match(ics, /RRULE:FREQ=MONTHLY;INTERVAL=6/) // art. 11, VIII da REN 1.174
  assert.ok(ics.split('\r\n').every((l) => octetos(l) <= 75), 'linhas até 75 octetos')
  const desdobrado = ics.split('\r\n ').join('')
  assert.match(desdobrado, /Análise preliminar\\, não é parecer jurídico/) // a vírgula é escapada no .ics
  assert.match(desdobrado, /sugestão \(IA\)\\, a revisar/)
  const so = calendarioIcs(entradas, 'Jurídico')
  assert.ok((so.match(/BEGIN:VEVENT/g) ?? []).length <= (ics.match(/BEGIN:VEVENT/g) ?? []).length)
})

test('dobrar corta por octetos e nunca no meio de um caractere acentuado', () => {
  const dobrada = dobrar('é'.repeat(100))
  assert.ok(dobrada.split('\r\n').every((l) => octetos(l) <= 75))
  assert.equal(dobrada.split('\r\n').join('').replaceAll(' ', ''), 'é'.repeat(100))
})

test('área vinda da IA sai marcada "área sugerida (IA)" no CSV e no .ics; as que a regra achou, não', () => {
  const ia = todos.find((b) => b.areaOrigem === 'ia')!
  const regra = todos.find((b) => b.areaOrigem === 'regra')!
  assert.ok(ia && regra)
  assert.ok(tarefasCsv([ia], null).includes(`"${ia.area} (área sugerida (IA))"`))
  assert.ok(!tarefasCsv([regra], null).includes('área sugerida (IA)'))
  const entrada = (b: typeof ia) => [{ norma: b.norma, vigencia: '2026-11-04', blocos: [b], trechos: { [b.id]: '' } }]
  const comPrazo = todos.find((b) => b.dataPrazo && b.areaOrigem === 'ia') ?? { ...ia, dataPrazo: '2027-01-01' }
  assert.match(calendarioIcs(entrada(comPrazo), null).split('\r\n ').join(''), /Área sugerida \(IA\): /)
  assert.equal(todos.filter((b) => b.areaOrigem === null).length, todos.filter((b) => b.area === 'A definir').length)
})

test('sujeito implícito (a revisar): coluna no CSV de tarefas e marca nos blocos; a contagem bate com os dados', () => {
  const implicitos = todos.filter((b) => b.sujeitoImplicito)
  assert.ok(implicitos.length > 0 && implicitos.length < todos.length)
  const csv = tarefasCsv(implicitos.slice(0, 1), null)
  assert.match(csv.split('\r\n')[1], /"sujeito"/)
  assert.ok(csv.includes('"sujeito implícito (a revisar)"'))
  const explicito = todos.find((b) => !b.sujeitoImplicito)!
  assert.ok(tarefasCsv([explicito], null).includes('"distribuidora (no texto)"'))
  for (const n of NORMAS) assert.equal(todos.filter((b) => b.norma === n.id && b.sujeitoImplicito).length, n.dados.obrigacoes.filter((o) => o.sujeito_implicito).length)
})
