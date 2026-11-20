import { test } from 'node:test'
import assert from 'node:assert/strict'
import { MIN_AUTOS_REFERENCIA, NORMAS, defesa, destaqueDaNorma, frase, prazoTexto, idDaObrigacao, norma, prazos, queda, referenciaDoSetor, simplificar, tabelaDeGrupos, top5, urlDetalhe, urlPlanoCompleto, valorDaObrigacao, valorGeral } from './executivo.ts'
import { GRUPOS, NOME_DA_GRAVIDADE, nomeDaGravidade, rotuloDoGrupo } from './gravidade.ts'
import { SIM_INICIAL, planos, type Simulacao } from './plano.ts'

const porte = (base: number): Simulacao => ({ base, faturamento: null })
const NORMAS_IDS = NORMAS.map((n) => n.id)

test('mapeamento de gravidade cobre os 5 grupos, num lugar só, e nunca deixa "Grupo IV" sozinho', () => {
  assert.deepEqual(GRUPOS.map((g) => NOME_DA_GRAVIDADE[g]), ['leve', 'média', 'séria', 'grave', 'gravíssima'])
  assert.equal(rotuloDoGrupo('IV'), 'infração grave (Grupo IV)')
  assert.equal(rotuloDoGrupo(null), 'infração a enquadrar')
  assert.equal(nomeDaGravidade('X'), 'a enquadrar')
  for (const n of NORMAS) {
    const t = tabelaDeGrupos(n.dados)
    assert.equal(t.grupos.length, 5)
    for (const g of t.grupos) assert.ok(g.pct != null && g.dispositivo && g.trecho, `grupo ${g.grupo} sem dado citado`)
    const pcts = t.grupos.map((g) => g.pct!)
    assert.deepEqual(pcts, [...pcts].sort((a, b) => a - b)) // o teto cresce com a gravidade
    assert.ok(t.tetoLegal && t.tetoLegal.pct && t.tetoLegal.trecho)
  }
})

test('top 5: vencidas primeiro (a mais antiga antes), depois maior valor por infração, depois identificado antes de sugerido', () => {
  for (const id of NORMAS_IDS) {
    const linhas = top5(id, SIM_INICIAL, 'preliminar')
    assert.equal(linhas.length, 5)
    const p = norma(id).dados
    const por = new Map(p.obrigacoes.map((o) => [o.id, o]))
    const sit = linhas.map((l) => (l.situacao === 'vencida' ? 0 : 1))
    assert.deepEqual(sit, [...sit].sort((a, b) => a - b), `${id}: vencida depois de não vencida`)
    const datas = linhas.filter((l) => l.situacao === 'vencida').map((l) => por.get(l.id)!.prazo.data!)
    assert.deepEqual(datas, [...datas].sort(), `${id}: vencida mais antiga primeiro`)
    // se sobrou vencida fora do top 5, o top 5 é todo de vencidas
    const ids = new Set(linhas.map((l) => l.id))
    if (p.obrigacoes.some((o) => o.situacao === 'vencida' && !ids.has(o.id))) assert.ok(linhas.every((l) => l.situacao === 'vencida'))
    // entre as não vencidas, o valor por infração não cresce ao descer a lista
    const naoVenc = linhas.filter((l) => l.situacao !== 'vencida').map((l) => l.valor?.pct ?? -1)
    assert.deepEqual(naoVenc, [...naoVenc].sort((a, b) => b - a))
  }
  // mesmo prazo e mesmo valor: identificado no texto vem antes de sugerido
  const rank = { identificado: 0, sugerido: 1 }
  const l = top5('rn1137', SIM_INICIAL, 'preliminar')
  const por = new Map(planos.rn1137.obrigacoes.map((o) => [o.id, o]))
  for (let i = 1; i < l.length; i++) {
    const [a, b] = [l[i - 1], l[i]]
    if (a.situacao === b.situacao && a.valor && b.valor && a.valor.pct === b.valor.pct && por.get(a.id)!.prazo.data === por.get(b.id)!.prazo.data) {
      assert.ok(rank[a.valor.origem] <= rank[b.valor.origem])
    }
  }
})

test('nunca soma: o valor geral é o maior por infração, limitado ao teto legal', () => {
  for (const n of NORMAS) {
    const v = valorGeral(n.dados, SIM_INICIAL, 'preliminar')
    const vs = n.dados.obrigacoes.map((o) => valorDaObrigacao(o, SIM_INICIAL, 'preliminar')).filter((x) => x != null)
    if (!vs.length) {
      assert.equal(v, null) // sem enquadramento, sem valor
      continue
    }
    assert.ok(v && v.reais! > 0)
    assert.equal(v.reais, Math.max(...vs.map((x) => x.reais!))) // o maior, nunca a soma
    assert.ok(v.pct <= 3 && v.reais! <= SIM_INICIAL.base * 0.03)
  }
})

test('trocar a norma ou o porte recalcula; o texto de cada cartão vem dos dados', () => {
  const a = top5('rn1137', SIM_INICIAL, 'preliminar').map((l) => l.id)
  const b = top5('ren1174', SIM_INICIAL, 'preliminar').map((l) => l.id)
  assert.notDeepEqual(a, b)
  const [m, g] = [valorGeral(planos.rn1137, porte(5e9), 'preliminar')!.reais!, valorGeral(planos.rn1137, porte(10e9), 'preliminar')!.reais!]
  assert.ok(Math.abs(g / m - 2) < 1e-9)
  const q = queda(planos.rn1137, SIM_INICIAL, 'preliminar')!
  assert.equal(q.reducaoPct, 95)
  assert.ok(q.para! < q.de! && /Art\. 24, I/.test(q.dispositivo) && q.sha256.length === 64)
  assert.equal(prazos(planos.rn1137).vencidas, planos.rn1137.resumo.por_situacao.vencida)
})

test('sem enquadramento (nem sugerido) não há valor: nada de teto da escala como pior caso', () => {
  const semFaixa = { ...planos.ren1174, obrigacoes: planos.ren1174.obrigacoes.map((o) => ({ ...o, faixa: null, faixa_preliminar: null })) }
  assert.equal(valorGeral(semFaixa, SIM_INICIAL, 'preliminar'), null)
  assert.equal(queda(semFaixa, SIM_INICIAL, 'preliminar'), null)
  for (const o of semFaixa.obrigacoes) assert.equal(valorDaObrigacao(o, SIM_INICIAL, 'preliminar'), null)
  // só identificados no texto: sugestão da IA não entra no valor
  for (const o of planos.rn1137.obrigacoes.filter((x) => !x.faixa)) assert.equal(valorDaObrigacao(o, SIM_INICIAL, 'confirmados'), null)
  // a página mostra as linhas sem valor como "a enquadrar"
  for (const x of top5('ren1174', SIM_INICIAL, 'preliminar')) if (!x.valor) assert.match(x.textoValor, /sem valor/)
})

test('links "detalhes" caem na âncora da obrigação certa, na página da norma selecionada', () => {
  for (const id of NORMAS_IDS) {
    const p = norma(id).dados
    for (const l of top5(id, SIM_INICIAL, 'preliminar')) {
      assert.ok(p.obrigacoes.some((x) => x.id === l.id), `obrigação ${l.id} não existe em ${id}`)
      assert.equal(l.link, `${urlPlanoCompleto(id)}#${idDaObrigacao(l.id)}`)
      assert.equal(l.link, urlDetalhe(id, l.id))
    }
  }
  assert.equal(urlPlanoCompleto('rn1137'), '/demo')
  assert.equal(urlPlanoCompleto('ren1174'), '/demo?norma=ren1174')
})

test('frases curtas: sem reticências, sem jargão de publicação e sem sigla solta', () => {
  assert.equal(simplificar('Disponibilizar em sítio eletrônico o plano'), 'Publicar no site o plano')
  assert.match(simplificar('Apurar o DISE mensalmente'), /DISE \(duração da interrupção/)
  for (const n of NORMAS) {
    for (const o of n.dados.obrigacoes) {
      const f = frase(o)
      assert.ok(f.length > 0 && f.length <= 110 && !f.endsWith('…'), `${o.id}: ${f}`)
      assert.doesNotMatch(f, /sítio eletrônico/i)
    }
  }
})

test('defesa possível: instruções da ANEEL (no texto) e autorização municipal (prática conhecida); senão "—"', () => {
  const p = planos.rn1137
  const comAto = p.obrigacoes.find((o) => o.analise?.dependencias_no_texto.some((d) => d.id === 'ato_da_aneel'))!
  assert.equal(defesa(p, comAto).origem, 'no texto')
  const manejo = p.obrigacoes.find((o) => o.tema === 'manejo' && !o.analise?.dependencias_no_texto.length && !o.excludente)!
  assert.match(defesa(p, manejo).texto, /autoriza/)
  assert.equal(defesa(p, manejo).origem, 'prática conhecida')
  assert.equal(defesa(p, p.obrigacoes.find((o) => o.tema === 'contingencia' && !o.excludente)!).texto, '—')
})

test('referência do setor: infração grave (Grupo IV, n = 10) quando o valor é do Grupo IV; senão a geral (n = 21)', () => {
  const p = planos.rn1137
  const r = referenciaDoSetor(p, 'IV')
  assert.equal(r.usouGeral, false)
  assert.equal(r.n, p.referencia_escala.infracao_grave.autos)
  assert.ok(r.n >= MIN_AUTOS_REFERENCIA && /infração grave \(Grupo IV\)/.test(r.texto) && /n = 10/.test(r.texto))
  assert.match(r.nota, /valor do auto inteiro, não estimativa por obrigação/)
  for (const g of ['III', 'II', null, undefined]) {
    const geral = referenciaDoSetor(p, g)
    assert.equal(geral.usouGeral, true)
    assert.equal(geral.n, p.referencia_escala.autos)
    assert.match(geral.texto, /n = 21/)
  }
  // com poucos autos por infração grave, mesmo o Grupo IV cai para a geral
  const e = p.referencia_escala
  const pequena = { ...p, referencia_escala: { ...e, infracao_grave: { ...e.infracao_grave, autos: 4 } } }
  assert.equal(referenciaDoSetor(pequena, 'IV').usouGeral, true)
})

test('destaque da norma: data, deveres identificados e quantos têm prazo, tudo dos dados', () => {
  const d = destaqueDaNorma(planos.ren1174)
  assert.equal(d.texto, 'publicada em 04/11/2026 · 91 deveres identificados · 3 com prazo')
  assert.equal(d.deveres, planos.ren1174.resumo.aplicaveis)
  assert.equal(d.comPrazo, planos.ren1174.obrigacoes.filter((o) => o.prazo.data).length)
  assert.match(destaqueDaNorma(planos.rn1137).texto, /^em vigor desde 30\/10\/2025 · 155 deveres identificados · \d+ com prazo$/)
})

test('nenhum nome de empresa real nos JSONs exportados', () => {
  const empresas = /\b(Equatorial|Taesa|Enel|CPFL|Cemig|Energisa|Copel|Celesc|Eletrobras|Eletropaulo|Neoenergia|Coelba|Celpe|Elektro|Iberdrola|Engie|Cteep|Alupar)\b/
  const varre = (v: unknown, caminho: string): void => {
    if (typeof v === 'string') {
      if (!v.startsWith('http')) assert.doesNotMatch(v, empresas, caminho)
    } else if (Array.isArray(v)) v.forEach((x, i) => varre(x, `${caminho}[${i}]`))
    else if (v && typeof v === 'object') Object.entries(v).forEach(([k, x]) => varre(x, `${caminho}.${k}`))
  }
  for (const [id, p] of Object.entries(planos)) varre(p, id)
})

test('frase não termina em "; e", "; ou" nem em vírgula; "subgrupo AS ou A4" é explicado', () => {
  const o = { ...planos.ren1174.obrigacoes[0], titulo_completo: 'Ser realizada no caso de migração na modalidade regular; e' }
  assert.equal(frase(o), 'Ser realizada no caso de migração na modalidade regular')
  assert.equal(frase({ ...o, titulo_completo: 'Ser feita para o consumidor,' }), 'Ser feita para o consumidor')
  assert.ok(simplificar('90 dias: para o consumidor do subgrupo AS ou A4').includes('subgrupo AS ou A4 (alta tensão)'))
  for (const n of NORMAS) for (const x of n.dados.obrigacoes) assert.doesNotMatch(frase(x), /[;,:]$|;\s+(?:e|ou)$/i, x.id)
})

test('prazo provisório diz de onde a data é contada; dias contados até a data de referência', () => {
  const v = planos.ren1174.obrigacoes.find((o) => o.situacao === 'vencida')!
  assert.match(prazoTexto(v), /^vencida há \d+ dias \(provisória, contada de \d{2}\/\d{2}\/\d{4}\)$/)
  assert.equal(prazoTexto({ ...v, prazo: { ...v.prazo, base: null } }), prazoTexto(v).replace(/ \(provisória.*\)$/, ''))
})
