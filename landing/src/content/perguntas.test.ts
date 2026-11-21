import { test } from 'node:test'
import assert from 'node:assert/strict'
import { ABERTURA_PERGUNTAS, perguntasParaOJuridico } from './perguntas.ts'
import { NORMAS, top5 } from './executivo.ts'

const sim = { base: 5e9, faturamento: null }

test('abertura: o Athenix prepara a conversa, não substitui o jurídico', () => {
  assert.equal(ABERTURA_PERGUNTAS, 'O Athenix prepara a conversa com o jurídico; não a substitui.')
})

test('toda pergunta traz dispositivo e citação e nasce de um sinal de incerteza dos dados', () => {
  for (const n of NORMAS) {
    const qs = perguntasParaOJuridico(n.dados, n.id, sim, 'preliminar')
    assert.ok(qs.length > 0)
    for (const q of qs) {
      assert.ok(q.pergunta.length > 20 && q.dispositivo && q.citacao.length > 3, JSON.stringify(q))
      if (q.origem === 'enquadramento_topo') {
        const o = n.dados.obrigacoes.find((x) => x.dispositivo === q.dispositivo && x.ia && !x.faixa)
        assert.ok(o, `sem sugestão da IA pendente: ${q.dispositivo}`)
      }
      if (q.origem === 'sucessao_no_tempo') assert.ok(n.dados.sucessao_no_tempo.some((s) => s.dispositivo === q.dispositivo))
      if (q.origem === 'excludente' || q.origem === 'instrucao_aneel') assert.ok(n.dados.temas.some((t) => t.dependencias_no_texto.length > 0))
    }
  }
})

test('enquadramentos sugeridos das 5 primeiras obrigações vêm antes dos demais', () => {
  for (const n of NORMAS) {
    const qs = perguntasParaOJuridico(n.dados, n.id, sim, 'preliminar')
    const ordem = qs.map((q) => q.origem)
    const ultimoTopo = ordem.lastIndexOf('enquadramento_topo')
    if (ultimoTopo >= 0) assert.ok(ordem.slice(0, ultimoTopo + 1).every((o) => o === 'enquadramento_topo'))
    const topo = top5(n.id, sim, 'preliminar').filter((l) => n.dados.obrigacoes.find((o) => o.id === l.id)?.ia && !n.dados.obrigacoes.find((o) => o.id === l.id)?.faixa)
    assert.equal(ordem.filter((o) => o === 'enquadramento_topo').length, topo.length)
  }
})

test('as duas redações do art. 11, XXIII entram como pergunta na RN 1.137 e não aparecem sem os dados', () => {
  const rn = NORMAS.find((n) => n.id === 'rn1137')!
  const q = perguntasParaOJuridico(rn.dados, 'rn1137', sim, 'preliminar').find((x) => x.origem === 'sucessao_no_tempo')!
  assert.match(q.dispositivo, /XXIII/)
  assert.match(q.citacao, /RN 1\.137\/2025.*REN 1\.148\/2026/)
  const sem = { ...rn.dados, sucessao_no_tempo: [] }
  assert.ok(!perguntasParaOJuridico(sem, 'rn1137', sim, 'preliminar').some((x) => x.origem === 'sucessao_no_tempo'))
})
