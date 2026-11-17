import { test } from 'node:test'
import assert from 'node:assert/strict'
import { celula, csvPlano, lacuna, obrigacao, ordenarTemas, plano, textoFaixa } from './plano.ts'

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
