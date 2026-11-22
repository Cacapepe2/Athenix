import { test } from 'node:test'
import assert from 'node:assert/strict'
import { atualizar, diasAte, hojeISO } from './datas.ts'
import { prazoTexto, prazos, textoPrazoDoTema, top5 } from './executivo.ts'
import { planos } from './plano.ts'

test('dias contados da data de vencimento até hoje, não do número congelado no JSON', () => {
  assert.equal(diasAte('2026-04-28', '2026-11-17'), -203) // a data de referência da geração
  assert.equal(diasAte('2026-04-28', '2026-11-21'), -207) // quatro dias depois, o número muda
  assert.equal(diasAte('2026-11-21', '2026-11-21'), 0)
  assert.equal(hojeISO(new Date(2026, 10, 20, 23, 30)), '2026-11-20') // à noite, no fuso local
})

test('a situação acompanha o dia: vence hoje ainda não venceu; amanhã sim; fora de 90 dias é "depois"', () => {
  const o = planos.rn1137.obrigacoes.find((x) => x.prazo.data)!
  assert.equal(atualizar(o, o.prazo.data!).situacao, '90dias') // dia do vencimento
  const dia = (n: number) => { const d = new Date(`${o.prazo.data}T12:00:00Z`); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10) }
  assert.equal(atualizar(o, dia(1)).situacao, 'vencida')
  assert.equal(atualizar(o, dia(-200)).situacao, 'depois')
  assert.equal(atualizar(o, dia(-30)).situacao, '90dias')
  const sem = planos.rn1137.obrigacoes.find((x) => !x.prazo.data)!
  assert.equal(atualizar(sem, '2030-01-01'), sem) // sem data, nada muda
})

test('"vencida há N dias" na executiva, nos blocos e no prazo do tema usam a mesma data de hoje', () => {
  const hoje = '2026-11-21'
  const l = top5('rn1137', null, 'preliminar', 5, hoje)[0]
  assert.match(l.prazoCurto, /^vencida há 387 dias$/) // art. 18: 30/10/2025 -> 21/11/2026 (a mais antiga primeiro)
  assert.match(top5('rn1137', null, 'preliminar', 5, hoje).map((x) => x.prazoCurto).join(';'), /vencida há 297 dias/) // 28/01/2026
  // 25 deveres vencidos = 14 obrigações principais (item ou dispositivo) + 11 alíneas de detalhe do item 107
  assert.deepEqual([prazos(planos.rn1137, hoje).vencidas, prazos(planos.rn1137, hoje).detalhes], [14, 11])
  const t = planos.rn1137.temas.find((x) => x.id === 'manejo')!
  assert.equal(textoPrazoDoTema(planos.rn1137, t, hoje), 'Vencido desde 28/01/2026 (297 dias)')
  const o = planos.rn1137.obrigacoes.find((x) => x.id === t.prazo_mais_urgente!.obrigacao)!
  assert.equal(prazoTexto(atualizar(o, hoje), false), 'vencida há 297 dias')
  // uma obrigação que vence entre a referência e hoje passa a "vencida"
  const futura = { ...o, prazo: { ...o.prazo, data: '2026-11-19', dias: 2 }, situacao: '90dias' as const }
  assert.equal(atualizar(futura, hoje).situacao, 'vencida')
})
