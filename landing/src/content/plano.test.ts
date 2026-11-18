import { test } from 'node:test'
import assert from 'node:assert/strict'
import { celula, comAtenuantePct, csvPlano, lacuna, lerReais, maximoPct, obrigacao, ordenarTemas, plano, reaisDe, SIM_INICIAL, textoFaixa, type Cenario } from './plano.ts'

test('plano vem do produto, com perfil ilustrativo e sem números soltos', () => {
  assert.equal(plano.gerado_por, 'scripts/exportar_plano_demo.py')
  assert.match(plano.commit_origem, /^[0-9a-f]{7,}$/)
  assert.match(plano.perfil.aviso, /não corresponde a nenhuma empresa real/)
  const r = plano.resumo
  assert.equal(r.aplicaveis, r.na_fila + r.a_confirmar + r.sem_multa)
  assert.equal(r.aplicaveis, Object.values(r.por_situacao).reduce((a, b) => a + b, 0))
  assert.equal(r.identificadas, r.aplicaveis + r.fora_do_perfil)
  assert.equal(plano.temas.reduce((n, t) => n + t.n, 0), r.aplicaveis)
})

test('ordem inicial dos temas é a mesma calculada no Python', () => {
  assert.deepEqual(ordenarTemas(plano.temas).map((t) => t.id), plano.ordem_inicial)
})

test('marcar "já temos" manda o tema para o fim e a lacuna soma obrigações', () => {
  const primeiro = plano.ordem_inicial[0]
  const ordem = ordenarTemas(plano.temas, { [primeiro]: 'sim' }).map((t) => t.id)
  assert.equal(ordem.at(-1), primeiro)
  const [a, b] = plano.temas
  const l = lacuna(plano.temas, { [a.id]: 'nao', [b.id]: 'parcial' })
  assert.deepEqual([l.nao, l.parcial, l.semResposta], [a.n, b.n, plano.temas.length - 2])
})

test('IA nunca entra no cálculo e cada obrigação tem trecho literal', () => {
  for (const o of plano.obrigacoes) {
    if (o.ia) assert.equal(o.faixa, null, `IA com faixa em ${o.id}`)
    if (o.faixa) assert.equal(o.calculo, 'fila')
    // Sem citação verificada não há trecho, e a obrigação fica fora de qualquer cálculo.
    if (!o.trecho) assert.ok(o.calculo === 'sem_multa' && !o.ia && !o.faixa, `sem trecho em ${o.id}`)
    else assert.ok(o.dispositivo, `sem dispositivo em ${o.id}`)
    for (const e of o.evidencias) assert.ok(e.trecho.length > 0)
  }
  for (const t of plano.temas) for (const id of t.obrigacoes) assert.equal(obrigacao(id).tema, t.id)
})

test('faixa diz advertência e nunca "R$ 0 a"', () => {
  const f = plano.obrigacoes.find((o) => o.faixa)!.faixa!
  assert.match(textoFaixa(f), /^De advertência \(sem multa\) até R\$ /)
  assert.doesNotMatch(textoFaixa(f), /R\$\s*0/)
})

test('CSV traz aviso, neutraliza fórmulas e cobre todas as obrigações', () => {
  assert.equal(celula('=HYPERLINK("x")'), `"'=HYPERLINK(""x"")"`)
  assert.equal(celula('-1'), `"'-1"`)
  const csv = csvPlano({})
  assert.ok(csv.startsWith('﻿'))
  assert.match(csv, /ESTIMATIVA ILUSTRATIVA/)
  const linhas = csv.trim().split('\r\n')
  assert.equal(linhas.length, 5 + plano.resumo.aplicaveis)
})

test('simulador refaz no navegador a conta do motor Python (casos de conferência)', () => {
  const casos = plano.simulador.conferencia
  assert.ok(casos.length >= plano.simulador.faixas.length + 1)
  assert.ok(casos.some((c) => c.faturamento != null), 'falta caso com faturamento (teto legal)')
  for (const c of casos) {
    const f = obrigacao(c.obrigacao).faixa!
    const s = { base: c.base, faturamento: c.faturamento }
    assert.ok(Math.abs(reaisDe(maximoPct(f, s), s) - c.maximo_reais) < 0.01, `máximo com base ${c.base}`)
    for (const [cen, v] of Object.entries(c.com_atenuante_reais)) {
      const pct = comAtenuantePct(f, s, cen as Cenario)!
      assert.ok(Math.abs(reaisDe(pct, s) - v!) < 0.01, `${cen} com base ${c.base}`)
    }
  }
})

test('faixas de porte ilustrativas, sem nome de empresa e sem fonte inventada', () => {
  assert.deepEqual(plano.simulador.faixas.map((f) => f.base), [1e9, 5e9, 10e9, 20e9])
  assert.match(plano.simulador.origem_faixas, /^Faixa ilustrativa, definida pela Athenix/)
  assert.equal(SIM_INICIAL.base, plano.perfil.base_reais)
  assert.equal(textoFaixa(plano.obrigacoes.find((o) => o.faixa)!.faixa!, null).includes('da base'), true)
})

test('lê valores em reais no formato brasileiro e recusa o resto', () => {
  assert.equal(lerReais('7.500.000.000'), 7.5e9)
  assert.equal(lerReais('R$ 7.500.000.000,50'), 7500000000.5)
  assert.equal(lerReais('7500000000'), 7.5e9)
  for (const t of ['', 'abc', '-5', '0', '1e30']) assert.equal(lerReais(t), null, t)
})

test('como reduzir: texto citado com hash, IA ausente e causa externa sem citação inventada', () => {
  const r = plano.reducao
  assert.equal(r.rotulo, 'Análise regulatória preliminar · não constitui parecer jurídico')
  for (const c of [...r.regras, ...r.medidas]) {
    assert.match(c.sha256, /^[0-9a-f]{64}$/)
    assert.ok(c.trecho.length > 20 && c.dispositivo)
  }
  const nao = r.medidas.filter((m) => m.percentual == null)
  assert.ok(nao.length && nao.every((m) => m.efeito.includes('não fixa percentual')))
  for (const t of plano.temas) {
    if (!t.excludentes.length) assert.equal(t.causa_externa, 'argumento a confirmar com advogado')
    for (const g of t.guardar) assert.ok(plano.guardar[g.id])
  }
})
