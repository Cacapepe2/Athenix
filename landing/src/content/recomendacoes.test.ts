import { test } from 'node:test'
import assert from 'node:assert/strict'
import { provasDoTema, recomendacoesDoTema } from './recomendacoes.ts'
import { NORMAS, eGerencial } from './executivo.ts'
import { comAtenuantePct, exposicaoTema, reaisDe, SIM_INICIAL } from './plano.ts'

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
      if (r.defesa) assert.ok(['no texto', 'marco do texto', 'prática conhecida'].includes(r.defesa.origem))
    }
  }
  const p = NORMAS[0].dados
  assert.ok(provasDoTema(p, []).length === 0)
})

test('recomendações por tema: só ações de nível gerencial; o detalhe operacional vai à parte e nada cita produto fora do texto', () => {
  const produto = /scada|erp|crm|\bgis\b|call ?center/i
  for (const n of NORMAS) {
    for (const t of n.dados.temas) {
      const r = recomendacoesDoTema(n.dados, t, sim, 'preliminar')
      for (const a of r.acoes) assert.ok(eGerencial(a) || /INMET/.test(a), `gerencial: ${a}`)
      for (const a of r.operacionais) assert.ok(!eGerencial(a), `operacional: ${a}`)
      for (const o of n.dados.obrigacoes) for (const x of o.recomendacoes) assert.doesNotMatch(x.acao, produto, x.acao)
    }
  }
})

test('C2: o efeito de agir usa a mesma conta do motor (comAtenuantePct), inclusive limitado pelo faturamento', () => {
  // Faturamento bruto R$ 500 mi com ROL R$ 5 bi: o teto legal (3% do faturamento = R$ 15 mi) limita o valor sem atenuante,
  // mas o atenuante parte do teto do GRUPO (R$ 50 mi × 5% = R$ 2,5 mi), não de R$ 15 mi × 5% = R$ 750 mil.
  const limitado = { base: 5e9, faturamento: 500e6 }
  const p = NORMAS.find((n) => n.id === 'rn1137')!.dados
  for (const t of p.temas) {
    const e = exposicaoTema(t, limitado, 'preliminar')
    if (!e) continue
    const r = recomendacoesDoTema(p, t, limitado, 'preliminar')
    const esperado = reaisDe(comAtenuantePct(e.faixa, limitado, 'espontanea')!, limitado)
    assert.equal(r.efeito!.para, esperado, t.id)
    assert.ok(r.efeito!.de! <= 15_000_000 + 1) // o valor "de" já vem limitado pelo teto legal
    const grupoIV = e.faixa.grupos.includes('IV') && e.faixa.teto_grupo_pct === 1
    if (grupoIV) assert.ok(Math.abs(r.efeito!.para! - 2_500_000) < 1) // e não R$ 750 mil
  }
})
