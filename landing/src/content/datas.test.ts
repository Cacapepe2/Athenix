import { test } from 'node:test'
import assert from 'node:assert/strict'
import { atualizar, diasAte, hojeISO } from './datas.ts'
import { prazoTexto, prazos, textoPrazoDoTema, top5 } from './executivo.ts'
import { planos } from './plano.ts'

test('dias contados da data de vencimento até hoje, não do número congelado no JSON', () => {
  assert.equal(diasAte('2026-04-28', '2026-11-17'), -203) // a data de referência da geração
  assert.equal(diasAte('2026-04-28', '2026-11-21'), -207) // quatro dias depois, o número muda
  assert.equal(diasAte('2026-11-21', '2026-11-21'), 0)
})

test('"hoje" no fuso de São Paulo: 23h30 em São Paulo (02h30 UTC do dia seguinte) ainda é o mesmo dia', () => {
  const quase = new Date('2026-11-23T02:30:00Z') // 22/11/2026, 23h30 em São Paulo
  assert.equal(quase.toISOString().slice(0, 10), '2026-11-23') // o dia que um build em UTC escreveria
  assert.equal(hojeISO(quase), '2026-11-22')
  assert.equal(hojeISO(new Date('2026-11-23T02:59:59Z')), '2026-11-22')
  assert.equal(hojeISO(new Date('2026-11-23T03:00:00Z')), '2026-11-23') // meia-noite em São Paulo
  // Um dia muda o que a executiva mostra; por isso o HTML pré-renderizado não traz a data (scripts/check-build.mjs).
  const bloco = (hoje: string) => top5('rn1137', null, 'preliminar', 5, hoje)[0]
  assert.equal(bloco('2026-11-22').prazoCurto, 'vencida há 298 dias')
  assert.equal(bloco('2026-11-23').prazoCurto, 'vencida há 299 dias')
  assert.deepEqual([prazos(planos.rn1137, '2026-11-22').vencidas, prazos(planos.rn1137, '2026-11-22').detalhes], [8, 11])
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
  assert.match(l.prazoCurto, /^vencida há 297 dias$/) // item 103: 28/01/2026 -> 21/11/2026; Art. 18 agora é só vigência.
  assert.match(top5('rn1137', null, 'preliminar', 5, hoje).map((x) => x.prazoCurto).join(';'), /vencida há 297 dias/) // 28/01/2026
  // 19 registros = 8 principais + 11 detalhes; incisos de prazo e vigência fora dos deveres.
  assert.deepEqual([prazos(planos.rn1137, hoje).vencidas, prazos(planos.rn1137, hoje).detalhes], [8, 11])
  const t = planos.rn1137.temas.find((x) => x.id === 'manejo')!
  assert.equal(textoPrazoDoTema(planos.rn1137, t, hoje), 'Vencido desde 28/01/2026 (297 dias)')
  const o = planos.rn1137.obrigacoes.find((x) => x.id === t.prazo_mais_urgente!.obrigacao)!
  assert.equal(prazoTexto(atualizar(o, hoje), false), 'vencida há 297 dias')
  // uma obrigação que vence entre a referência e hoje passa a "vencida"
  const futura = { ...o, prazo: { ...o.prazo, data: '2026-11-19', dias: 2 }, situacao: '90dias' as const }
  assert.equal(atualizar(futura, hoje).situacao, 'vencida')
})
