import { test } from 'node:test'
import assert from 'node:assert/strict'
import { fraseProntidao, prontidao } from './prontidao.ts'
import { recomendacoesDoTema } from './recomendacoes.ts'
import { alternarProva, RESPOSTAS_VAZIAS, type Respostas } from './respostas.ts'
import { plano } from './plano.ts'

test('sem marcar nada, prontidão é zero e o indicador não aparece', () => {
  const p = prontidao(plano, RESPOSTAS_VAZIAS)
  assert.equal(p.geral.x, 0)
  assert.equal(p.geral.n, plano.obrigacoes.length)
  assert.equal(p.algumaMarcada, false)
})

test('marcar todas as provas do checklist faz contar as obrigações que têm prova; o total nunca passa de N', () => {
  let r: Respostas = RESPOSTAS_VAZIAS
  for (const t of plano.temas) for (const pv of recomendacoesDoTema(plano, t).provas) r = alternarProva(r, t.id, pv.id)
  const p = prontidao(plano, r)
  assert.ok(p.algumaMarcada && p.geral.x > 0 && p.geral.x <= p.geral.n)
  for (const t of plano.temas) assert.ok(p.porTema[t.id].x <= p.porTema[t.id].n)
  assert.equal(p.geral.x, Object.values(p.porTema).reduce((s, v) => s + v.x, 0))
})

test('marcar só parte das provas de um tipo não conta a obrigação (todas as provas dela são exigidas)', () => {
  const t = plano.temas.find((x) => recomendacoesDoTema(plano, x).provas.length >= 2)!
  const provas = recomendacoesDoTema(plano, t).provas
  const completo = prontidao(plano, provas.reduce((r, pv) => alternarProva(r, t.id, pv.id), RESPOSTAS_VAZIAS)).porTema[t.id].x
  const parcial = prontidao(plano, alternarProva(RESPOSTAS_VAZIAS, t.id, provas[0].id)).porTema[t.id].x
  assert.ok(parcial <= completo)
})

test('frase do indicador', () => {
  assert.equal(fraseProntidao(12, 80), 'Se a ANEEL fiscalizar amanhã, vocês têm prova para 12 de 80 obrigações')
})
