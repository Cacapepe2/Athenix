import { test } from 'node:test'
import assert from 'node:assert/strict'
import { planoEm } from './referencia.ts'
import { montarRelatorio } from './relatorio.ts'
import { prazos, prazoTexto, textoPrazoDoTema, top5 } from './executivo.ts'
import { blocosDoPlano } from './filtros.ts'
import { RESPOSTAS_VAZIAS } from './respostas.ts'
import { planos } from './plano.ts'

const sim = { base: 5e9, faturamento: null }

test('uma referência de data: bloco, tema e detalhe da obrigação dizem os mesmos dias', () => {
  for (const hoje of ['2026-11-17', '2026-11-21', '2027-03-01']) {
    const p = planoEm(planos.rn1137, hoje)
    const t = p.temas.find((x) => x.id === 'manejo')!
    const o = p.obrigacoes.find((x) => x.id === t.prazo_mais_urgente!.obrigacao)!
    const dias = Math.abs(o.prazo.dias!)
    assert.match(o.prazo.texto, new RegExp(`\(${dias} dias\)`)) // o detalhe (prazo.texto) não é o texto congelado de 17/11
    assert.equal(textoPrazoDoTema(p, t, hoje), o.prazo.texto)
    assert.equal(prazoTexto(o, false), `vencida há ${dias} dias`)
    const bloco = top5('rn1137', sim, 'preliminar', 5, hoje).find((l) => l.id === o.id)
    if (bloco) assert.equal(bloco.prazoCurto, `vencida há ${dias} dias`)
  }
})

test('o plano inteiro acompanha a data: totais, contagem do tema e linha do tempo recalculados', () => {
  const antes = planoEm(planos.ren1174, '2026-11-21')
  const depois = planoEm(planos.rn1137, '2030-01-01')
  const comData = depois.obrigacoes.filter((o) => o.prazo.data)
  assert.ok(comData.length > 0 && comData.every((o) => o.situacao === 'vencida')) // 2030: tudo com data venceu
  assert.equal(depois.resumo.por_situacao.vencida, comData.length)
  assert.deepEqual(depois.linha_do_tempo.vencida.sort(), comData.map((o) => o.id).sort())
  for (const t of depois.temas) assert.equal(t.contagem.vencida, t.obrigacoes.filter((id) => comData.some((o) => o.id === id)).length)
  assert.equal(antes.resumo.por_situacao.vencida, 0)
})

test('montarRelatorio respeita a data recebida em TODOS os trechos (cabeçalho, números, temas, áreas)', () => {
  const r = (hoje: string) => montarRelatorio({ sim, modo: 'preliminar', diag: {}, respostas: RESPOSTAS_VAZIAS, hoje })
  const a = r('2026-11-21')
  const b = r('2025-01-01') // antes de qualquer vencimento da RN 1.137 (o primeiro é 30/10/2025)
  assert.equal(a.cabecalho.data, '21/11/2026')
  assert.equal(b.cabecalho.data, '01/01/2025')
  assert.equal(b.cabecalho.prazosAte, '01/01/2025')
  // com referência em 01/01/2025 não há vencida; o primeiro prazo é o de 30/10/2025 (302 dias)
  assert.deepEqual(b.numeros.prazo, { valor: '302 dias', legenda: 'até o próximo prazo' })
  assert.deepEqual(a.numeros.prazo, { valor: '7', legenda: 'obrigações vencidas' })
  assert.ok(b.areas.every((x) => x.vencidas === 0))
  assert.ok(a.areas.some((x) => x.vencidas > 0))
  assert.ok(b.temas.every((t) => !/^Vencido/.test(t.prazo)), 'nenhum tema vencido em 01/01/2025')
  assert.ok(a.temas.some((t) => /^Vencido desde \d{2}\/\d{2}\/\d{4} \(\d+ dias\)$/.test(t.prazo)))
  assert.ok(b.decisoes.every((d) => !/vencido/i.test(d.porque)))
  // Date também vale (hora local não troca o dia)
  assert.equal(montarRelatorio({ sim, modo: 'preliminar', diag: {}, respostas: RESPOSTAS_VAZIAS, hoje: new Date(2026, 10, 21, 23, 59) }).cabecalho.data, '21/11/2026')
})

test('blocos do plano e prazos usam a data recebida; a passagem do vencimento muda a situação', () => {
  const antes = blocosDoPlano(sim, 'preliminar', '2025-01-01')
  const depois = blocosDoPlano(sim, 'preliminar', '2026-11-21')
  assert.equal(antes.filter((b) => b.situacaoPrazo === 'vencida').length, 0)
  assert.equal(depois.filter((b) => b.situacaoPrazo === 'vencida').length, 7)
  assert.equal(prazos(planos.rn1137, '2025-01-01').proxima?.dias, 302)
  assert.equal(prazos(planos.rn1137, '2026-11-21').proxima, null)
})
