import test from 'node:test'
import assert from 'node:assert/strict'
import { fonteDaCitacao } from './fontes.ts'
import { planos } from './plano.ts'
import { demoNorm, obligations } from './demo.ts'
import { perguntasParaOJuridico } from './perguntas.ts'

test('toda citação dos dispositivos dos dois planos abre a fonte salva, com página só para PDF', () => {
  for (const [id, p] of Object.entries(planos)) {
    for (const o of [...p.obrigacoes, ...p.outros_dispositivos, ...p.sem_dever_identificado]) {
      const url = fonteDaCitacao(p.norma.sha256, o.trecho)
      assert.ok(url?.startsWith('/fontes/'), `${id}: ${o.dispositivo}`)
      if (id === 'rn1137') assert.match(url!, /\.pdf#page=\d+$/)
      else assert.match(url!, /\.html$/)
    }
    for (const o of p.obrigacoes) if (o.marco?.trecho) assert.ok(fonteDaCitacao(p.norma.sha256, o.marco.trecho))
    for (const i of Object.values(p.infracoes)) assert.ok(fonteDaCitacao(i.fonte.sha256, i.trecho))
    for (const m of [...p.reducao.medidas, ...p.reducao.regras]) assert.ok(fonteDaCitacao(m.sha256, m.trecho))
  }
})

test('perguntas e demo antiga usam a citação da fonte correta, inclusive redação incerta', () => {
  for (const id of ['rn1137', 'ren1174'] as const) {
    for (const q of perguntasParaOJuridico(planos[id], id, null, 'preliminar', '2026-11-22')) {
      assert.ok(q.fontes.length)
      for (const f of q.fontes) assert.ok(fonteDaCitacao(f.sha256, f.trecho), q.dispositivo)
    }
    for (const s of planos[id].sucessao_no_tempo) for (const r of s.redacoes) assert.ok(fonteDaCitacao(r.fonte.sha256, r.trecho))
  }
  for (const a of demoNorm.articles) assert.ok(fonteDaCitacao(demoNorm.sha256, a.text), a.label)
  for (const o of obligations) for (const f of o.impact.framings) {
    const atual = planos.rn1137.infracoes[f.dispositivo]
    assert.equal(f.trecho, atual.trecho)
    assert.ok(fonteDaCitacao(atual.fonte.sha256, f.trecho))
  }
})

test('resumo mantém a página; texto vazio, fonte desconhecida ou fragmento ambíguo não inventam link', () => {
  const p = planos.rn1137
  const o = p.obrigacoes.find((o) => o.dispositivo === 'item 103')!
  const inteira = fonteDaCitacao(p.norma.sha256, o.trecho)
  assert.equal(fonteDaCitacao(p.norma.sha256, `“${o.trecho!.slice(0, 220)}…”`), inteira)
  assert.equal(fonteDaCitacao('fonte desconhecida', o.trecho), undefined)
  assert.equal(fonteDaCitacao(planos.ren1174.norma.sha256, '“”'), undefined)
  assert.equal(fonteDaCitacao(p.norma.sha256, 'Art.'), undefined)
})
