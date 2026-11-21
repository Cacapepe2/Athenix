import { test } from 'node:test'
import assert from 'node:assert/strict'
import { COLUNAS_TAREFAS, calendarioIcs, dobrar, recorrenciaDoTexto, tarefasCsv } from './tarefas.ts'
import { blocosDoPlano } from './filtros.ts'
import { NORMAS } from './executivo.ts'
import { planos, SIM_INICIAL } from './plano.ts'

const todos = blocosDoPlano(SIM_INICIAL, 'preliminar')

test('toda obrigação tem área sugerida, dentre as seis áreas', () => {
  const lista = planos.rn1137.analise.areas.lista
  assert.deepEqual(lista, ['Regulatório', 'Operação/Manutenção', 'Comunicação/Atendimento', 'TI/Sistemas', 'Meio Ambiente/Arborização', 'Jurídico'])
  for (const b of todos) assert.ok(lista.includes(b.area), `${b.norma} ${b.dispositivo}: ${b.area}`)
})

test('CSV de tarefas: colunas pedidas, uma linha por obrigação da área, fórmula neutralizada', () => {
  assert.deepEqual(COLUNAS_TAREFAS.slice(0, 6), ['obrigação', 'dispositivo', 'prazo', 'valor por infração', 'ação recomendada', 'o que provar'])
  const area = 'Comunicação/Atendimento'
  const csv = tarefasCsv(todos, area)
  const linhas = csv.trimEnd().split('\r\n')
  assert.equal(linhas.length - 1, todos.filter((b) => b.area === area).length)
  assert.match(linhas[0], /^"obrigação","dispositivo","prazo","valor por infração","ação recomendada","o que provar"/)
  assert.equal(tarefasCsv(todos, null).trimEnd().split('\r\n').length - 1, todos.length)
  assert.doesNotMatch(csv, /\n[=+@]/) // nada começa por fórmula
})

test('recorrência lida do texto: semestral, anual, a cada 12 meses; sem periodicidade, nada', () => {
  assert.equal(recorrenciaDoTexto('encaminhados à ANEEL, semestralmente, relatórios'), 'FREQ=MONTHLY;INTERVAL=6')
  assert.equal(recorrenciaDoTexto('com periodicidade anual'), 'FREQ=YEARLY')
  assert.equal(recorrenciaDoTexto('a cada período de 12 meses'), 'FREQ=YEARLY')
  assert.equal(recorrenciaDoTexto('apurados mensalmente'), 'FREQ=MONTHLY')
  assert.equal(recorrenciaDoTexto('sem periodicidade'), null)
})

test('calendário .ics: formato válido, prazos com data e recorrências com RRULE; linhas até 75 caracteres', () => {
  const entradas = NORMAS.map((n) => ({ norma: n.id, vigencia: n.dados.norma.vigencia, blocos: todos.filter((b) => b.norma === n.id), trechos: Object.fromEntries(n.dados.obrigacoes.map((o) => [o.id, o.trecho ?? ''])) }))
  const ics = calendarioIcs(entradas, null, new Date('2026-11-20T12:00:00Z'))
  assert.match(ics, /^BEGIN:VCALENDAR\r\nVERSION:2\.0\r\n/)
  assert.match(ics, /END:VCALENDAR\r\n$/)
  const comData = todos.filter((b) => b.dataPrazo).length
  assert.ok(comData > 0 && (ics.match(/BEGIN:VEVENT/g) ?? []).length >= comData)
  assert.equal((ics.match(/BEGIN:VEVENT/g) ?? []).length, (ics.match(/END:VEVENT/g) ?? []).length)
  assert.match(ics, /DTSTART;VALUE=DATE:\d{8}/)
  assert.match(ics, /RRULE:FREQ=MONTHLY;INTERVAL=6/) // art. 11, VIII da REN 1.174
  assert.ok(ics.split('\r\n').every((l) => l.length <= 75))
  assert.match(ics.split('\r\n ').join(''), /Análise preliminar\\, não é parecer jurídico/) // a vírgula é escapada no .ics
  // filtro por área
  const so = calendarioIcs(entradas, 'Jurídico')
  assert.ok((so.match(/BEGIN:VEVENT/g) ?? []).length <= (ics.match(/BEGIN:VEVENT/g) ?? []).length)
  assert.equal(dobrar('x'.repeat(160)).split('\r\n').every((l) => l.length <= 75), true)
})
