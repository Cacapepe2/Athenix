import { test } from 'node:test'
import assert from 'node:assert/strict'
import { splitAnchor, stepAt } from './text.ts'
import { articleById, changes, obligations } from '../content/demo.ts'

test('stepAt limita o índice ao intervalo das etapas', () => {
  assert.equal(stepAt(-0.2, 5), 0)
  assert.equal(stepAt(0, 5), 0)
  assert.equal(stepAt(0.21, 5), 1)
  assert.equal(stepAt(0.99, 5), 4)
  assert.equal(stepAt(1, 5), 4)
})

test('splitAnchor só aceita trecho literal', () => {
  assert.deepEqual(splitAnchor('abc def ghi', 'def'), ['abc ', 'def', ' ghi'])
  assert.equal(splitAnchor('abc def ghi', 'xyz'), null)
  assert.equal(splitAnchor('abc', ''), null)
})

test('toda obrigação da demo aponta para trecho literal do artigo citado', () => {
  for (const o of obligations) {
    assert.ok(splitAnchor(articleById(o.articleId).text, o.anchor), `âncora ausente em ${o.id}`)
  }
  for (const c of changes) assert.ok(articleById(c.articleId), `artigo ausente em ${c.id}`)
})
