import { test } from 'node:test'
import assert from 'node:assert/strict'
import { provasDoTema, recomendacoesDoTema } from './recomendacoes.ts'
import { NORMAS } from './executivo.ts'
import { SIM_INICIAL } from './plano.ts'

const sim = { base: 5e9, faturamento: null }

test('cada tema: até 3 ações e até 3 provas, sem repetir', () => {
  for (const n of NORMAS) {
    for (const t of n.dados.temas) {
      const r = recomendacoesDoTema(n.dados, t, sim, 'preliminar')
      assert.ok(r.acoes.length <= 3 && new Set(r.acoes).size === r.acoes.length, `${n.id}/${t.id}`)
      assert.ok(r.provas.length <= 3 && new Set(r.provas.map((x) => x.id)).size === r.provas.length)
    }
  }
})

test('as ações vêm das recomendações específicas (com citação), nunca de frase genérica', () => {
  const generica = /definir (?:um |o |uma )?respons|designar (?:um |o |uma )?respons|com a equipe|prazo interno/i
  for (const n of NORMAS) {
    const dosDispositivos = new Set(n.dados.obrigacoes.flatMap((o) => o.recomendacoes.map((x) => x.acao)))
    for (const t of n.dados.temas) {
      for (const a of recomendacoesDoTema(n.dados, t, sim, 'preliminar').acoes) {
        assert.doesNotMatch(a, generica)
        assert.ok(dosDispositivos.has(a) || /INMET/.test(a), a)
      }
    }
  }
})

test('tipo "comunicar consumidores": entra a ideia do aviso por alerta oficial (INMET) e a prova do alerta e do aviso', () => {
  const p = NORMAS.find((n) => n.id === 'rn1137')!.dados
  const t = p.temas.find((x) => x.obrigacoes.some((id) => p.obrigacoes.find((o) => o.id === id)?.analise?.tipo?.id === 'comunicar_consumidores'))!
  const r = recomendacoesDoTema(p, t, sim, 'preliminar')
  assert.ok(r.acoes.some((a) => /alerta meteorológico oficial \(ex\.: INMET\)/.test(a)))
  assert.ok(r.provas.some((x) => /alerta recebido e do aviso enviado \(horário, região, quantidade de clientes\)/.test(x.texto)))
  // só a ideia: sem integração nem coleta de dados
  assert.doesNotMatch(r.acoes.join(' '), /integra|API|coleta/i)
})

test('efeito de agir: até 95% e o valor de partida é o do tema (nunca soma)', () => {
  for (const n of NORMAS) {
    for (const t of n.dados.temas) {
      const r = recomendacoesDoTema(n.dados, t, sim, 'preliminar')
      if (!r.efeito) continue
      assert.equal(r.efeito.reducaoPct, 95)
      if (r.efeito.de != null) assert.ok(Math.abs(r.efeito.para! - r.efeito.de * 0.05) < 1)
    }
  }
})

test('defesa e "Evite" só aparecem quando existem nos dados', () => {
  for (const n of NORMAS) {
    for (const t of n.dados.temas) {
      const r = recomendacoesDoTema(n.dados, t, SIM_INICIAL, 'preliminar')
      if (r.evite) assert.ok(n.dados.obrigacoes.some((o) => o.evite?.acao === r.evite))
      if (r.defesa) assert.ok(r.defesa.origem === 'no texto' || r.defesa.origem === 'prática conhecida')
    }
  }
  const p = NORMAS[0].dados
  assert.ok(provasDoTema(p, []).length === 0)
})
