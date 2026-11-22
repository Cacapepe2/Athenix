import test from 'node:test'
import assert from 'node:assert/strict'
import { planos, SIM_INICIAL } from './plano.ts'
import { rascunhosDoItem } from './rascunhos-aneel.ts'
import { montarRelatorio } from './relatorio.ts'
import { RESPOSTAS_VAZIAS } from './respostas.ts'

test('todo enquadramento ou sujeito incerto aparece dentro do item, com dispositivo e trecho literal', () => {
  for (const p of Object.values(planos)) for (const o of p.obrigacoes) {
    const grupos = rascunhosDoItem(p.rascunhos_aneel, o.id)
    if (!o.enquadramento.length) assert.ok(grupos.some((g) => g.tipo === 'enquadramento sem texto'), o.id)
    if (o.sujeito_implicito) assert.ok(grupos.some((g) => g.tipo === 'sujeito incerto'), o.id)
    for (const g of grupos) {
      assert.equal(g.rotulo, 'rascunho — revisar antes de enviar')
      assert.ok(g.referencias.every((r) => r.itens.includes(o.id)))
      for (const r of g.referencias) assert.ok(r.trecho && r.dispositivo && r.fonte.sha256)
    }
  }
})

test('filtrar pelo item não altera os grupos completos e o relatório contém as perguntas agrupadas', () => {
  const p = planos.rn1137
  const antes = JSON.stringify(p.rascunhos_aneel)
  rascunhosDoItem(p.rascunhos_aneel, p.obrigacoes[0].id)
  assert.equal(JSON.stringify(p.rascunhos_aneel), antes)
  const r = montarRelatorio({ sim: SIM_INICIAL, modo: 'preliminar', diag: {}, respostas: RESPOSTAS_VAZIAS, hoje: '2026-11-22' })
  assert.deepEqual(r.perguntasAneel, p.rascunhos_aneel)
  assert.equal(new Set(r.perguntasAneel.map((p) => p.id)).size, r.perguntasAneel.length)
})

test('prazo já esclarecido do DISE não gera pergunta de prazo; a dúvida de enquadramento permanece', () => {
  const p = planos.rn1137
  const o = p.obrigacoes.find((o) => o.dispositivo === 'Art. 13, inciso VI')!
  const grupos = rascunhosDoItem(p.rascunhos_aneel, o.id)
  assert.ok(grupos.some((g) => g.tipo === 'enquadramento sem texto'))
  assert.ok(grupos.every((g) => g.tipo !== 'possível erro material' && g.tipo !== 'transição ambígua'))
})
