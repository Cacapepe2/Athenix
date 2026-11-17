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

test('demo usa dados reais gerados pelo pipeline, com perfil ilustrativo marcado', async () => {
  const { demoNorm, obligations, profile, notices } = await import('../content/demo.ts')
  const dados = (await import('../content/demo-rn1137.json', { with: { type: 'json' } })).default
  assert.equal(dados.gerado_por, 'scripts/exportar_demo_site.py')
  assert.match(dados.commit_origem, /^[0-9a-f]{7,}$/)
  assert.equal(demoNorm.sha256.length, 64)
  assert.ok(obligations.length >= 3)
  for (const o of obligations) {
    assert.ok(o.impact.max >= o.impact.min && o.impact.min === 0, `faixa inválida em ${o.id}`)
    assert.ok(o.impact.premises.length > 0 && o.impact.sources.length > 0, `sem premissa ou fonte em ${o.id}`)
    assert.ok(['alto', 'médio', 'baixo'].includes(o.confidence))
  }
  assert.match(profile.notice, /não corresponde a nenhuma empresa real/)
  // Regra da fila: enquadramento desconhecido fica fora dela (verificar), com confiança baixa.
  for (const o of obligations.filter((x) => x.verifyFraming)) {
    assert.equal(o.position, null)
    assert.equal(o.confidence, 'baixo')
  }
  assert.ok(obligations.some((o) => o.verifyFraming) && obligations.some((o) => !o.verifyFraming))
  assert.match(notices.order, /peso do prazo/)
  assert.match(notices.estimate, /não constitui parecer jurídico/)
})

test('textos do site não afirmam o que o produto ainda não sustenta', async () => {
  const { readFile } = await import('node:fs/promises')
  // Só o texto publicado: comentários de código (que listam o que é proibido) ficam fora.
  const texto = (await readFile(new URL('../content/site.ts', import.meta.url), 'utf8')).replace(/^\s*\/\/.*$/gm, '')
  const proibidos = [
    /detectad[ao]/i, // captura automática de publicações ainda não existe
    /valida(ção)? automática|valida automaticamente/i,
    /\d+\s?%\s+de\s+(precisão|acurácia|acerto)/i,
    /\b(concorrentes?|melhor que|líder)\b/i,
    /clientes atendidos|empresas atendidas|depoimento/i,
    /ferramentas genéricas/i,
  ]
  for (const re of proibidos) assert.doesNotMatch(texto, re)
  assert.match(texto, /Iniciativa em validação/)
})
