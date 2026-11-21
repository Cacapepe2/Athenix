import { test } from 'node:test'
import assert from 'node:assert/strict'
import { fraseProntidao, prontidao } from './prontidao.ts'
import { recomendacoesDoTema } from './recomendacoes.ts'
import { alternarProva, RESPOSTAS_VAZIAS, type Respostas } from './respostas.ts'
import { plano } from './plano.ts'

test('sem marcar nada, o indicador não aparece e Y é o tamanho do checklist (não o número de obrigações)', () => {
  const p = prontidao(plano, RESPOSTAS_VAZIAS)
  assert.equal(p.geral.x, 0)
  assert.equal(p.algumaMarcada, false)
  assert.equal(p.geral.y, plano.temas.reduce((s, t) => s + recomendacoesDoTema(plano, t).provas.length, 0))
  assert.ok(p.geral.y <= plano.temas.length * 3 && p.geral.y < plano.obrigacoes.length)
})

test('marcar todo o checklist leva X até Y (100%): o gerente consegue fazer o número chegar ao fim', () => {
  let r: Respostas = RESPOSTAS_VAZIAS
  for (const t of plano.temas) for (const pv of recomendacoesDoTema(plano, t).provas) r = alternarProva(r, t.id, pv.id)
  const p = prontidao(plano, r)
  assert.equal(p.geral.x, p.geral.y)
  for (const t of plano.temas) assert.equal(p.porTema[t.id].x, p.porTema[t.id].y)
})

test('cada prova marcada sobe X em 1 e desmarcar desce; prova de outro tema não conta', () => {
  const t = plano.temas.find((x) => recomendacoesDoTema(plano, x).provas.length >= 2)!
  const provas = recomendacoesDoTema(plano, t).provas
  const um = alternarProva(RESPOSTAS_VAZIAS, t.id, provas[0].id)
  assert.equal(prontidao(plano, um).porTema[t.id].x, 1)
  assert.equal(prontidao(plano, alternarProva(um, t.id, provas[1].id)).porTema[t.id].x, 2)
  assert.equal(prontidao(plano, alternarProva(um, t.id, provas[0].id)).porTema[t.id].x, 0)
  const outro = plano.temas.find((x) => x.id !== t.id)!
  assert.equal(prontidao(plano, alternarProva(RESPOSTAS_VAZIAS, outro.id, provas[0].id)).porTema[t.id].x, 0 + (recomendacoesDoTema(plano, t).provas.some((c) => c.id === provas[0].id) && false ? 1 : 0))
})

test('frase: nunca "prova para N de 155 obrigações"', () => {
  assert.equal(fraseProntidao(4, 12), 'Provas em mãos: 4 de 12 (checklist sugerido)')
  assert.doesNotMatch(fraseProntidao(4, 12), /obrigações/)
})
