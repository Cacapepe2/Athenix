import { test } from 'node:test'
import assert from 'node:assert/strict'
import { brl, brlCurto, textoVencidas, celula, comAtenuantePct, csvPlano, decisoesDaSemana, exposicaoTema, lacuna, lerReais, manchete, maximoPct, resumoDiagnostico, obrigacao, ordenarTemas, plano, reaisDe, SIM_INICIAL, situacaoPrazo, textoFaixa, type Cenario, type Simulacao } from './plano.ts'

test('plano vem do produto, com perfil ilustrativo e sem números soltos', () => {
  assert.equal(plano.gerado_por, 'scripts/exportar_plano_demo.py')
  assert.match(plano.commit_origem, /^[0-9a-f]{7,}$/)
  assert.match(plano.perfil.aviso, /não corresponde a nenhuma empresa real/)
  const r = plano.resumo
  assert.equal(r.aplicaveis, r.na_fila + r.a_confirmar + r.sem_multa)
  assert.equal(r.aplicaveis, Object.values(r.por_situacao).reduce((a, b) => a + b, 0))
  assert.equal(r.identificadas, r.aplicaveis + r.fora_do_perfil + r.outros_dispositivos)
  assert.equal(plano.outros_dispositivos.length, r.outros_dispositivos)
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
    // A faixa preliminar só existe para sugestão da IA e nunca se confunde com a confirmada.
    if (o.faixa_preliminar) assert.ok(o.ia && !o.faixa, `faixa preliminar sem sugestão em ${o.id}`)
    if (o.faixa) assert.equal(o.calculo, 'fila')
    // Sem citação verificada não há trecho, e a obrigação fica fora de qualquer cálculo.
    if (!o.trecho) assert.ok(o.calculo === 'sem_multa' && !o.ia && !o.faixa, `sem trecho em ${o.id}`)
    else assert.ok(o.dispositivo, `sem dispositivo em ${o.id}`)
    for (const e of o.evidencias) assert.ok(e.trecho.length > 0)
  }
  for (const t of plano.temas) for (const id of t.obrigacoes) assert.equal(obrigacao(id).tema, t.id)
})

test('faixa diz "até R$ X por infração" e nunca "R$ 0 a"', () => {
  const f = plano.obrigacoes.find((o) => o.faixa)!.faixa!
  assert.match(textoFaixa(f), /^até R\$ .* por infração$/)
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

const porte = (base: number): Simulacao => ({ base, faturamento: null })

test('temas ordenados por R$ em risco: maior primeiro, sem enquadramento por último, atendido no fim', () => {
  const ordem = ordenarTemas(plano.temas, {}, SIM_INICIAL, 'preliminar')
  const valores = ordem.map((t) => exposicaoTema(t, SIM_INICIAL, 'preliminar')?.reais ?? -1)
  assert.deepEqual(valores, [...valores].sort((a, b) => b - a))
  const diag = { [ordem[0].id]: 'sim' as const }
  assert.equal(ordenarTemas(plano.temas, diag, SIM_INICIAL, 'preliminar').at(-1)!.id, ordem[0].id)
  // empate de R$: o prazo vencido vem antes do que não tem data
  const empate = ordem.filter((t) => exposicaoTema(t, SIM_INICIAL)?.reais === valores[0])
  const vencidoAntes = empate.map((t) => (t.contagem.vencida ? 0 : 1))
  assert.deepEqual(vencidoAntes, [...vencidoAntes].sort((a, b) => a - b))
})

test('modo preliminar inclui sugestões (hachurado) e só confirmados volta ao cálculo anterior', () => {
  const sem = plano.temas.filter((t) => !t.faixa && t.faixa_preliminar)
  assert.ok(sem.length > 0, 'precisa haver tema só com sugestão')
  for (const t of sem) {
    assert.equal(exposicaoTema(t, SIM_INICIAL, 'confirmados'), null)
    const e = exposicaoTema(t, SIM_INICIAL, 'preliminar')!
    assert.equal(e.origem, 'sugerido')
    assert.ok(e.reais! > 0)
  }
  for (const t of plano.temas.filter((x) => x.faixa)) {
    const c = exposicaoTema(t, SIM_INICIAL, 'confirmados')!
    assert.equal(c.origem, 'confirmado')
    assert.equal(c.faixa, t.faixa)
  }
  // a ordem em "só confirmados" põe os temas sem enquadramento confirmado depois dos confirmados
  const ordem = ordenarTemas(plano.temas, {}, SIM_INICIAL, 'confirmados')
  const primeiroSem = ordem.findIndex((t) => !t.faixa)
  assert.ok(ordem.slice(primeiroSem).every((t) => !t.faixa))
})

test('exposição do tema é a maior por infração, nunca a soma, e escala com o porte', () => {
  for (const t of plano.temas) {
    const e = exposicaoTema(t, SIM_INICIAL, 'preliminar')
    if (!e) continue
    const maximos = [t.faixa, t.faixa_preliminar].filter(Boolean).map((f) => maximoPct(f!, SIM_INICIAL))
    assert.equal(e.pct, Math.max(...maximos))
    assert.ok(e.pct <= 3)
  }
  const t = plano.temas.find((x) => x.faixa)!
  const [a, b] = [1e9, 5e9].map((base) => exposicaoTema(t, porte(base), 'confirmados')!.reais!)
  assert.ok(Math.abs(b / a - 5) < 1e-9)
})

test('ordem inicial do Python vale para o porte padrão e as decisões saem dos 3 primeiros temas', () => {
  const d = decisoesDaSemana(plano.temas, {}, SIM_INICIAL, 'preliminar')
  assert.deepEqual(d.map((t) => t.id), plano.ordem_inicial.slice(0, 3))
  const marcado = decisoesDaSemana(plano.temas, { [d[0].id]: 'sim' }, SIM_INICIAL, 'preliminar')
  assert.ok(!marcado.some((t) => t.id === d[0].id))
  for (const t of d) assert.match(situacaoPrazo(t), /^(prazo vencido há \d+ dias|vence em|obrigação recorrente|sem data)/)
})

test('manchete: temas vencidos, maior exposição por infração e os 4 portes', () => {
  const nVencidos = plano.temas.filter((t) => t.contagem.vencida).length
  const valores = plano.simulador.faixas.map((f) => {
    const m = manchete(plano.temas, {}, porte(f.base), 'preliminar')
    assert.equal(m.temasVencidos, nVencidos)
    assert.ok(m.maximo && m.maximo.reais! > 0)
    return m.maximo!.reais!
  })
  assert.deepEqual(valores, [...valores].sort((a, b) => a - b))
  assert.equal(brlCurto(50e6), 'R$ 50 mi')
  assert.equal(brlCurto(48654893), 'R$ 48,7 mi')
  // abaixo de R$ 10 mi, duas casas fixas
  assert.equal(brlCurto(1250000), 'R$ 1,25 mi')
  assert.equal(brlCurto(2500000), 'R$ 2,50 mi')
  assert.equal(brlCurto(9990000), 'R$ 9,99 mi')
  assert.equal(brl(2500000), 'R$ 2,50 milhões')
  assert.equal(brl(1500000), 'R$ 1,50 milhão')
  assert.equal(brl(48654893), 'R$ 48,7 milhões')
  assert.equal(brl(50e6), 'R$ 50 milhões')
  // em "só confirmados", sem enquadramento confirmado não se inventa valor
  const nenhum = manchete(plano.temas.map((t) => ({ ...t, faixa: null })), {}, SIM_INICIAL, 'confirmados')
  assert.equal(nenhum.maximo, null)
})

test('referência de escala é por auto (n = 21) e não traz empresa', () => {
  const r = plano.referencia_escala
  assert.equal(r.autos, 21)
  assert.match(r.rotulo, /não estimativa por obrigação/)
  assert.ok(r.mediana_reais < r.maximo_reais)
  assert.doesNotMatch(JSON.stringify(r), /Equatorial|Enel|CPFL|Cemig|Energisa|Light|Neoenergia|Copel/)
})

test('análise preliminar: só obrigações principais, dependência no texto com trecho e rótulo', () => {
  assert.match(plano.analise.rotulo, /não constitui parecer jurídico/)
  for (const t of plano.temas) for (const id of t.principais) assert.ok(obrigacao(id).analise, `sem análise em ${id}`)
  const deps = plano.temas.flatMap((t) => t.dependencias_no_texto)
  assert.equal(deps.length, 4)
  assert.ok(deps.every((d) => d.id === 'ato_da_aneel' && d.trecho_literal.length > 20))
  const manejo = plano.analise.dependencias[plano.analise.pratica_por_tema.manejo]
  assert.match(manejo.cautela, /disputada/)
})

test('empate de R$: confirmado antes de sugerido, depois mais obrigações vencidas; manchete e decisões usam o mesmo dado', () => {
  const ordem = ordenarTemas(plano.temas, {}, SIM_INICIAL, 'preliminar')
  const par = ordem.map((t) => {
    const e = exposicaoTema(t, SIM_INICIAL, 'preliminar')
    return [e ? e.pct : -1, e?.origem === 'sugerido' ? 1 : 0, t.contagem.vencida] as const
  })
  for (let i = 1; i < par.length; i++) {
    const [a, b] = [par[i - 1], par[i]]
    if (a[0] === b[0]) {
      assert.ok(a[1] <= b[1], 'confirmado antes de sugerido')
      if (a[1] === b[1]) assert.ok(a[2] >= b[2], 'mais obrigações vencidas primeiro')
    }
  }
  const m = manchete(plano.temas, {}, SIM_INICIAL, 'preliminar')
  assert.equal(m.obrigacoesVencidas, plano.resumo.por_situacao.vencida)
  assert.equal(textoVencidas(1), '1 obrigação vencida')
  assert.equal(textoVencidas(3), '3 obrigações vencidas')
})

test('resumo do diagnóstico: tema mais exposto em aberto, lacuna e nada de promessa', () => {
  const ordem = ordenarTemas(plano.temas, {}, SIM_INICIAL, 'preliminar')
  const topo = ordem.find((t) => exposicaoTema(t, SIM_INICIAL, 'preliminar'))!
  const s = resumoDiagnostico(plano.temas, {}, SIM_INICIAL, 'preliminar')
  assert.ok(s.startsWith(`Neste porte, o tema mais exposto é ${topo.nome}, com até R$`), s)
  assert.ok(s.includes(`libera o cálculo de ${plano.decisoes.confirmar.temas_sem_calculo_confirmado}`))
  assert.ok(!s.includes('lacuna'), 'sem marcação, sem lacuna')
  assert.doesNotMatch(s, /multad|garantid|isent|evita a multa/i)
  // Marcar o primeiro como atendido troca o tema da frase e traz a lacuna em obrigações.
  const outro = resumoDiagnostico(plano.temas, { [topo.id]: 'sim' }, SIM_INICIAL, 'preliminar')
  assert.ok(!outro.includes(`mais exposto é ${topo.nome},`))
  assert.match(outro, /lacuna informada é de 0 obrigações em temas não atendidos e 0 em temas parciais/)
  // Sem receita válida: em % da receita.
  assert.match(resumoDiagnostico(plano.temas, {}, null, 'confirmados'), /da receita por infração|nenhum tema em aberto/)
})

test('título completo nunca termina em reticências', () => {
  for (const o of plano.obrigacoes) assert.ok(o.titulo_completo && !o.titulo_completo.endsWith('…'), o.id)
})

test('infrações citadas trazem fonte, SHA-256 e origem da redação, conferidos pelo export', () => {
  const todas = Object.entries(plano.infracoes)
  assert.ok(todas.length > 0)
  for (const [d, i] of todas) {
    assert.ok(i.conferido_na_fonte, `sem conferência em ${d}`)
    assert.match(i.fonte.sha256, /^[0-9a-f]{64}$/)
    assert.ok(i.fonte.arquivo && i.origem_da_redacao)
  }
})

test('art. 11, XXIII: as duas redações aparecem com vigência e estado; a futura segue incerta', () => {
  const s = plano.sucessao_no_tempo.find((x) => x.dispositivo === 'Art. 11, XXIII')!
  assert.equal(s.redacoes.length, 2)
  assert.equal(s.redacoes[0].vigencia_ate, '2026-12-31')
  assert.equal(s.redacoes[1].estado, 'incerta')
  assert.equal(s.redacoes[1].conferido_na_fonte, false)
})

test('outros dispositivos não entram nos deveres nem nos temas', () => {
  const deveres = new Set(plano.obrigacoes.map((o) => o.id))
  for (const o of plano.outros_dispositivos) assert.ok(!deveres.has(o.id), `${o.id} contado como dever`)
  assert.equal(plano.temas.reduce((n, t) => n + t.n, 0), plano.resumo.aplicaveis)
})
