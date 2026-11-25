import { test } from 'node:test'
import assert from 'node:assert/strict'
import { planos } from './plano.ts'
import { fraseComparacao, resumoComparacao, textoDeveresCriados } from './comparacao.ts'
import { fonteDaCitacao } from './fontes.ts'

test('comparação real explicita escopo, dados sem fonte e divergências sem alterar deveres', () => {
  const p = planos.rn1137
  const c = p.comparacao_anterior!
  assert.equal(resumoComparacao(p), '112 novos · 0 alterados · 0 já existiam')
  assert.equal(c.resumo.novo + c.resumo.alterado + c.resumo.ja_existia + c.resumo.sem_fonte, p.resumo.aplicaveis)
  assert.equal(c.resumo.sem_fonte, 35)
  const o = p.obrigacoes.find((o) => o.dispositivo === 'item 115')!
  assert.equal(c.registros[o.id].confere_v3, false)
  assert.match(o.trecho!, /aos Poderes Públicos/)
  assert.match(c.itens['115'].atual.trecho, /ao Poder Público/)
  assert.equal(c.itens['1'].classe, 'alterado')
  assert.match(fonteDaCitacao(c.fontes.v2.sha256, c.itens['1'].anterior!.trecho)!, /\.pdf#page=1$/)
  assert.match(fonteDaCitacao(c.fontes.v3.sha256, c.itens['115'].atual.trecho)!, /\.pdf#page=\d+$/)
  assert.equal(c.itens['92'].classe, 'ja_existia')
  assert.equal(resumoComparacao(planos.ren1174), null)
  assert.equal(textoDeveresCriados(p), `${c.resumo.novo} deveres criados pela RN 1.137 no PRODIST`)
  assert.equal(textoDeveresCriados(planos.ren1174), null)
  for (const k of ['novo', 'alterado', 'ja_existia'] as const) assert.doesNotMatch(fraseComparacao(k), /v[123]\b|SHA/)
})
