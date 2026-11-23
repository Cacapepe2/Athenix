import { test } from 'node:test'
import assert from 'node:assert/strict'
import { MIN_AUTOS_REFERENCIA, NORMAS, acaoGerencial, eGerencial, textoMaiorMulta, contagemDeEnquadramentos, defesa, destaqueDaNorma, frase, prazoTexto, idDaObrigacao, norma, prazos, queda, referenciaDoSetor, simplificar, tabelaDeGrupos, textoContagem, top5, urlDetalhe, urlPlanoCompleto, valorDaObrigacao, valorGeral } from './executivo.ts'
import { GRUPOS, NOME_DA_GRAVIDADE, nomeDaGravidade, rotuloDoGrupo } from './gravidade.ts'
import { SIM_INICIAL, planos as planosDaPagina, type Simulacao } from './plano.ts'
import { planoEm } from './referencia.ts'

// Data FIXA dos testes de cenário: nenhum teste depende do relógio. A passagem do vencimento é coberta à parte (datas.test.ts).
const DIA = '2026-11-21'
const planos = { rn1137: planoEm(planosDaPagina.rn1137, DIA), ren1174: planoEm(planosDaPagina.ren1174, DIA) }

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
    const linhas = top5(id, SIM_INICIAL, 'preliminar', 5, DIA)
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
    // depois das vencidas vêm as a vencer COM DATA (a mais próxima antes); o resto, por maior valor
    const aVencer = linhas.filter((l) => l.situacao !== 'vencida' && por.get(l.id)!.prazo.data)
    const datasAVencer = aVencer.map((l) => por.get(l.id)!.prazo.data!)
    assert.deepEqual(datasAVencer, [...datasAVencer].sort(), `${id}: a vencer, a mais próxima primeiro`)
    const resto = linhas.filter((l) => l.situacao !== 'vencida' && !por.get(l.id)!.prazo.data).map((l) => l.valor?.pct ?? -1)
    assert.deepEqual(resto, [...resto].sort((a, b) => b - a))
  }
  // mesmo prazo e mesmo valor: identificado no texto vem antes de sugerido
  const rank = { identificado: 0, sugerido: 1 }
  const l = top5('rn1137', SIM_INICIAL, 'preliminar', 5, DIA)
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
  const a = top5('rn1137', SIM_INICIAL, 'preliminar', 5, DIA).map((l) => l.id)
  const b = top5('ren1174', SIM_INICIAL, 'preliminar', 5, DIA).map((l) => l.id)
  assert.notDeepEqual(a, b)
  const [m, g] = [valorGeral(planos.rn1137, porte(5e9), 'preliminar')!.reais!, valorGeral(planos.rn1137, porte(10e9), 'preliminar')!.reais!]
  assert.ok(Math.abs(g / m - 2) < 1e-9)
  const q = queda(planos.rn1137, SIM_INICIAL, 'preliminar')!
  assert.equal(q.reducaoPct, 95)
  assert.ok(q.para! < q.de! && /Art\. 24, I/.test(q.dispositivo) && q.sha256.length === 64)
  // por obrigação principal: as alíneas de detalhe ficam fora do número grande
  assert.equal(prazos(planos.rn1137, DIA).vencidas + prazos(planos.rn1137, DIA).detalhes, planos.rn1137.resumo.por_situacao.vencida)
})

test('sem enquadramento (nem sugerido) não há valor: nada de teto da escala como pior caso', () => {
  const semFaixa = { ...planos.ren1174, obrigacoes: planos.ren1174.obrigacoes.map((o) => ({ ...o, faixa: null, faixa_preliminar: null })) }
  assert.equal(valorGeral(semFaixa, SIM_INICIAL, 'preliminar'), null)
  assert.equal(queda(semFaixa, SIM_INICIAL, 'preliminar'), null)
  for (const o of semFaixa.obrigacoes) assert.equal(valorDaObrigacao(o, SIM_INICIAL, 'preliminar'), null)
  // só identificados no texto: sugestão da IA não entra no valor
  for (const o of planos.rn1137.obrigacoes.filter((x) => !x.faixa)) assert.equal(valorDaObrigacao(o, SIM_INICIAL, 'confirmados'), null)
  // a página mostra as linhas sem valor como "a enquadrar"
  for (const x of top5('ren1174', SIM_INICIAL, 'preliminar', 5, DIA)) if (!x.valor) assert.match(x.textoValor, /sem valor/)
})

test('links "detalhes" caem na âncora da obrigação certa, na página da norma selecionada', () => {
  for (const id of NORMAS_IDS) {
    const p = norma(id).dados
    for (const l of top5(id, SIM_INICIAL, 'preliminar', 5, DIA)) {
      assert.ok(p.obrigacoes.some((x) => x.id === l.id), `obrigação ${l.id} não existe em ${id}`)
      assert.equal(l.link, `${urlPlanoCompleto(id)}${id === 'rn1137' ? '?' : '&'}item=${l.id}#${idDaObrigacao(l.id)}`)
      assert.ok(new URL(l.link, 'https://x.test').searchParams.get('item') === l.id)
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

test('defesa possível: marco do texto (instruções da ANEEL) e prática conhecida só quando ligada à ação; senão "—"', () => {
  const p = planos.rn1137
  const comAto = p.obrigacoes.find((o) => o.analise?.dependencias_no_texto.some((d) => d.id === 'ato_da_aneel'))!
  // não afirma o estado atual ("ainda por publicar"): manda verificar, com a origem "marco do texto"
  assert.deepEqual(defesa(p, comAto), { texto: 'verificar se as instruções da ANEEL foram publicadas', origem: 'marco do texto' })
  const manejo = p.obrigacoes.find((o) => o.tema === 'manejo' && !o.analise?.dependencias_no_texto.length && !o.excludente)!
  // dever que é a PODA: a autorização municipal liga à ação
  const poda = { ...manejo, titulo_completo: 'Realizar a poda de árvores sob a rede', trecho: 'A distribuidora deve realizar a poda de árvores sob a rede.' }
  assert.match(defesa(p, poda).texto, /autoriza/)
  assert.equal(defesa(p, poda).origem, 'prática conhecida')
  // menção ao município sem a ação de poda não basta
  assert.equal(defesa(p, { ...manejo, titulo_completo: 'Registrar as interações com o Poder Público Municipal', trecho: 'registro das interações com o Poder Público Municipal' }).texto, '—')
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
  // 32 -> 31 com data: Art. 166, § 6º, I passa a condicional; a data de adequação permanece nos outros deveres.
  assert.equal(d.texto, 'publicada em 04/11/2026 · 75 deveres identificados · 31 com prazo · 1 recorrente')
  assert.equal(d.deveres, planos.ren1174.resumo.aplicaveis)
  assert.equal(d.comPrazo, planos.ren1174.obrigacoes.filter((o) => o.prazo.data).length)
  assert.match(destaqueDaNorma(planos.rn1137).texto, /^em vigor desde 30\/10\/2025 · 147 deveres identificados · \d+ com prazo · \d+ recorrentes?$/)
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
  const v = planos.rn1137.obrigacoes.find((o) => o.situacao === 'vencida')!
  assert.match(prazoTexto(v), /^vencida há \d+ dias \(provisória, contada de \d{2}\/\d{2}\/\d{4}\)$/)
  assert.equal(prazoTexto({ ...v, prazo: { ...v.prazo, base: null } }), prazoTexto(v).replace(/ \(provisória.*\)$/, ''))
  // Art. 18 é vigência geral: fica fora dos deveres e da contagem de vencidas.
  assert.ok(!planos.rn1137.obrigacoes.some((o) => o.dispositivo === 'Art. 18'))
  assert.ok(planos.rn1137.outros_dispositivos.some((o) => o.dispositivo === 'Art. 18' && o.natureza === 'regra_de_transicao'))
  // art. 14, § 1º, II da REN 1.174: o maior entre 12 meses da publicação e o prazo informado; sem data única
  const a14 = planos.ren1174.obrigacoes.find((o) => o.dispositivo === 'Art. 14, § 1º, inciso II')!
  assert.equal(a14.prazo.data, null)
  assert.equal(a14.prazo.condicional, true)
  assert.equal(a14.situacao, 'evento')
  assert.match(a14.prazo.texto, /maior entre 12 meses da publicação \(04\/11\/2027\) e o prazo informado pela distribuidora/i)
})

test('linha de enquadramentos: identificados no texto e sugeridos pela IA, contados por obrigação', () => {
  const c = contagemDeEnquadramentos(planos.rn1137)
  assert.equal(c.identificados, planos.rn1137.obrigacoes.filter((o) => o.faixa).length)
  assert.equal(c.sugeridos, planos.rn1137.obrigacoes.filter((o) => !o.faixa && o.faixa_preliminar).length)
  assert.equal(c.texto, `${c.identificados} enquadramentos identificados no texto · ${c.sugeridos} sugeridos pela IA, aguardando revisão`)
  const d = contagemDeEnquadramentos(planos.ren1174)
  assert.equal(d.identificados, 0)
  assert.ok(d.sugeridos > 0 && d.sugeridos <= planos.ren1174.resumo.aplicaveis)
})

test('Art. 13, § 3º da REN 1.174 é recorrente, não prazo único', () => {
  const o = planos.ren1174.obrigacoes.find((x) => x.dispositivo === 'Art. 13, § 3º')!
  assert.equal(o.situacao, 'recorrente')
  assert.equal(o.prazo.data, null)
})

test('REN 1.174: a primeira reunião do grupo de trabalho (art. 12, § 11) não é dever da distribuidora', () => {
  const p = planos.ren1174
  const l = top5('ren1174', SIM_INICIAL, 'preliminar', 5, DIA)
  assert.ok(!p.obrigacoes.some((o) => o.dispositivo === 'Art. 12, § 11'))
  assert.ok(p.outros_dispositivos.some((o) => o.dispositivo === 'Art. 12, § 11'))
  assert.ok(!l.some((x) => /primeira reunião/i.test(x.frase)))
  // o próximo prazo é a vigência diferida do art. 18, II (02/02/2027); o art. 14, § 1º, II segue condicional
  assert.equal(prazos(p, DIA).proxima?.data, '2027-02-02')
  assert.equal(p.resumo.aplicaveis, 75)  // 85 - 9 condicionais do sandbox - 1 condição de prazos opcionais.
})

test('títulos com contexto: nada de título que comece por "Ser ", "Até " ou "Em até " no top 5', () => {
  for (const n of NORMAS) for (const l of top5(n.id, SIM_INICIAL, 'preliminar', 5, DIA)) assert.doesNotMatch(l.frase, /^(?:Ser|Até|Em até)(?:\s|$)/, l.frase)
  const o = planos.ren1174.obrigacoes.find((x) => x.dispositivo === 'Art. 14, § 1º, inciso II')!
  assert.match(o.titulo_completo, /^A aplicação do benefício tarifário deve ser realizada/)
})

test('recomendação em revisão quando a IA não deu ação específica; nunca frase genérica no top 5', () => {
  const generica = /definir (?:um |o |uma )?respons|designar (?:um |o |uma )?respons|com a equipe|prazo interno/i
  for (const n of NORMAS) {
    for (const l of top5(n.id, SIM_INICIAL, 'preliminar', 5, DIA)) {
      if (l.fazer) for (const a of l.fazer.todas) assert.doesNotMatch(a, generica, a)
    }
    for (const o of n.dados.obrigacoes) for (const r of o.recomendacoes) assert.ok(r.trecho_citado.length >= 8 && !generica.test(r.acao))
  }
})

test('defesa possível: registrar interações com o município (Art. 13, II) não mostra autorização municipal', () => {
  const o = planos.rn1137.obrigacoes.find((x) => x.dispositivo === 'item 104')!
  assert.deepEqual(defesa(planos.rn1137, o), { texto: '—', origem: null })
})

test('maior multa aplicada a uma distribuidora até fev/2024, segundo a ANEEL, sem nome de empresa', () => {
  assert.equal(textoMaiorMulta(planos.rn1137), 'maior multa aplicada a uma distribuidora até fev/2024, segundo a ANEEL: R$ 165,8 mi')
  const m = planos.rn1137.referencia_escala.maior_multa
  assert.equal(m.fonte, 'notícia pública, Agência Brasil, 09/02/2024; multa mantida pela diretoria da ANEEL em 09/04/2024')
  assert.ok(!('link' in m) && !/https?:|www\./.test(JSON.stringify(m)), 'sem URL')
  assert.doesNotMatch(`${textoMaiorMulta(planos.rn1137)} ${m.fonte}`, /enel|light|cemig|copel|cpfl/i)
})

test('blocos da executiva: título curto (até 5 palavras), prazo, valor e barras, sem somar infrações', () => {
  for (const n of NORMAS) {
    const linhas = top5(n.id, porte(5e9), 'preliminar', 5, DIA)
    assert.equal(linhas.length, 5)
    for (const l of linhas) {
      assert.ok(l.titulo.length > 0)
      const o = n.dados.obrigacoes.find((x) => x.id === l.id)!
      if (o.titulo_curto) assert.ok(o.titulo_curto.split(/\s+/).length <= 5, o.titulo_curto)
      if (l.valor?.reais != null) {
        assert.equal(l.barras[0].rotulo, 'teto')
        assert.equal(l.barras[0].reais, l.valor.reais) // a barra do teto é o valor do bloco, nunca uma soma
        for (const b of l.barras) assert.ok(b.reais! <= l.valor.reais && b.fracao <= 1)
        const [, ii, i] = l.barras
        assert.match(ii.rotulo, /^art\. 24, II$/)
        assert.match(i.rotulo, /^art\. 24, I$/)
        assert.ok(i.reais! < ii.reais! && ii.reais! < l.barras[0].reais!)
      } else assert.deepEqual(l.barras, [])
      if (l.situacaoPrazo === 'vencida') assert.match(l.prazoCurto, /^vencida há \d+ dias$/)
      if (l.prazoBase) assert.match(l.prazoBase, /^contada de \d{2}\/\d{2}\/\d{4}( · provisória)?$/)
    }
  }
})

test('trocar a norma troca os cinco blocos; trocar o porte muda o valor e mantém a ordem', () => {
  const a = top5('rn1137', porte(5e9), 'preliminar', 5, DIA).map((l) => l.id)
  const b = top5('ren1174', porte(5e9), 'preliminar', 5, DIA).map((l) => l.id)
  assert.ok(a.every((id) => !b.includes(id)))
  const g1 = top5('rn1137', porte(1e9), 'preliminar', 5, DIA)
  const g20 = top5('rn1137', porte(20e9), 'preliminar', 5, DIA)
  assert.deepEqual(g1.map((l) => l.id), g20.map((l) => l.id))
  const comValor = (ls: typeof g1) => ls.find((l) => l.valor)!.valor!.reais!
  assert.equal(comValor(g20), comValor(g1) * 20) // a primeira com enquadramento
})

test('terceiro número: sem vencidas e sem prazo com data, "nenhum prazo a vencer"; com vencidas, a contagem', () => {
  const pz = prazos(planos.ren1174, DIA)
  assert.equal(pz.vencidas, 0)
  // sem vencidas: o próximo marco da transição (art. 18, II) e a contagem por situação
  assert.deepEqual(pz.proximoMarco, { data: '2027-02-02', tipo: 'vigência' })
  // 44: saíram 9 deveres condicionais em vigor; 6 artigos continuam inferidos (a confirmar).
  assert.equal(textoContagem(pz.contagem!), '44 em vigor desde 04/11/2026 · 1 condicional · 1 recorrente')
  // 14 -> 8 principais: cinco incisos de prazo e Art. 18 (vigência) não são deveres próprios; 11 detalhes permanecem.
  assert.deepEqual([prazos(planos.rn1137, DIA).vencidas, prazos(planos.rn1137, DIA).detalhes], [8, 11])
})

test('top 5: vencidas → em vigor sem adequação (já exigíveis) → próximos marcos → condicionais → o resto', () => {
  const grupo = (l: { situacao: string; prazo: string; dataPrazo: string | null }) =>
    l.situacao === 'vencida' ? 0 : /^em vigor desde/.test(l.prazo) ? 1 : l.dataPrazo ? 2 : /maior entre/.test(l.prazo) ? 3 : 4
  for (const n of NORMAS) {
    const g = top5(n.id, SIM_INICIAL, 'preliminar', 500, DIA).map(grupo)
    assert.deepEqual(g, [...g].sort((a, b) => a - b), n.id)
  }
  const ren = top5('ren1174', SIM_INICIAL, 'preliminar', 500, DIA)
  assert.ok([1, 2, 3].every((k) => ren.some((l) => grupo(l) === k)))
  const marco = ren.find((l) => grupo(l) === 2)!
  assert.match(marco.prazo, /^(?:vigência a partir de|adequação até) \d{2}\/\d{2}\/\d{4} \(em \d+ dias\)$/)
})

test('REN 1.174, Art. 12 (grupo de trabalho): fora dos deveres, com nota; Art. 13, § 1º conta como dever da distribuidora', () => {
  const p = planos.ren1174
  assert.ok(!p.obrigacoes.some((o) => o.dispositivo?.startsWith('Art. 12')))
  for (const d of ['Art. 12, § 1º', 'Art. 12, § 5º', 'Art. 12, § 11']) assert.ok(p.outros_dispositivos.some((o) => o.dispositivo === d), d)
  assert.equal(p.notas_outros['Art. 12'], 'Grupo de trabalho sobre faturas, coordenado provisoriamente pela Abradee; primeira reunião até 03/01/2027 (§ 11).')
  assert.ok(p.obrigacoes.some((o) => o.dispositivo === 'Art. 13, § 1º' && /celebrado entre o consumidor parcialmente livre e a distribuidora/.test(o.trecho ?? '')))
  assert.equal(p.resumo.aplicaveis, 75)
})

test('deveres condicionais ficam visíveis com o caput, fora do top 5 e da exposição principal', () => {
  const p = planos.ren1174
  const condicionais = p.outros_dispositivos.filter((o) => o.natureza === 'dever_condicional')
  assert.equal(condicionais.length, 10) // 9 do sandbox e 1 de prazos menores opcionais (Art. 166, § 6º, I).
  const sandbox = condicionais.filter((o) => o.condicao?.dispositivo === 'Art. 11')
  assert.equal(sandbox.length, 9)
  assert.ok(sandbox.some((o) => o.dispositivo === 'Art. 11, inciso I'))
  assert.ok(sandbox.some((o) => o.dispositivo === 'Art. 11, inciso VIII'))
  for (const o of condicionais) {
    assert.ok(o.condicao?.trecho && o.trecho)
    assert.ok(!p.obrigacoes.some((d) => d.id === o.id))
    assert.ok(!p.temas.some((t) => t.obrigacoes.includes(o.id)))
    assert.ok(!top5('ren1174', SIM_INICIAL, 'preliminar', 500, DIA).some((d) => d.id === o.id))
  }
  for (const o of sandbox) assert.equal(o.rotulo, 'Dever condicional: se aderir ao sandbox')
  assert.equal(valorGeral(p, SIM_INICIAL, 'preliminar')?.pct,
    Math.max(...p.obrigacoes.map((o) => valorDaObrigacao(o, SIM_INICIAL, 'preliminar')?.pct ?? -1)))
})

test('executiva: recomendação de nível gerencial; detalhe operacional só no plano completo', () => {
  assert.equal(eGerencial('Equipe de campo com motosserra e guincho para remover galhos'), false)
  assert.equal(eGerencial('Publique o plano de manejo aprovado no site, com data de aprovação.'), true)
  assert.equal(acaoGerencial(['Acione imediatamente equipe de campo com motosserra e guincho para remover árvores.', 'Publique o plano revisado no site.']), 'Publique o plano revisado no site.')
  // sem versão gerencial: a mais genérica (a mais curta) das válidas
  assert.equal(acaoGerencial(['Acione imediatamente a equipe de campo com guincho no local afetado hoje.', 'Acione equipe de campo.']), 'Acione equipe de campo.')
  for (const n of NORMAS) {
    for (const l of top5(n.id, porte(5e9), 'preliminar', 5, DIA)) {
      if (!l.fazer) continue
      const todasOperacionais = l.fazer.todas.every((a) => !eGerencial(a))
      if (!todasOperacionais) assert.ok(eGerencial(l.fazer.texto), `${n.id}: ${l.fazer.texto}`)
      assert.ok(l.fazer.todas.includes(l.fazer.texto)) // continua sendo uma ação validada, não texto novo
    }
  }
})

test('motor: futuro só vira dever quando a distribuidora age explicitamente; o resto vai para "sem dever identificado"', () => {
  const p = planos.ren1174
  const deveres = new Map(p.obrigacoes.map((o) => [o.dispositivo, o.trecho ?? '']))
  // entraram (REN 1.174), com citação
  assert.match(deveres.get('Art. 166-A, § 4º') ?? '', /será encerrada pela distribuidora/)
  assert.match(deveres.get('Art. 167-A, Parágrafo único') ?? '', /devendo a distribuidora efetuar a cobrança/)
  assert.match(deveres.get('Art. 170, § 5º') ?? '', /somente será realizada pela distribuidora/)
  // não entraram: futuro sem a distribuidora como agente
  const textoDeveres = p.obrigacoes.map((o) => o.trecho ?? '').join(' ')
  for (const frag of ['terá dois suplentes', 'correrão por conta', 'a Abradee exercerá', 'será composto', 'A ANEEL estabelecerá']) assert.ok(!textoDeveres.includes(frag), frag)
  // nada some em silêncio: o § 10 do Art. 12 está em "sem dever identificado", com o motivo
  const s10 = p.sem_dever_identificado.find((o) => /Abradee exercerá a coordenação/.test(o.trecho ?? ''))!
  assert.ok(s10 && s10.motivo === 'sem dever identificado' && s10.dispositivo === 'Art. 12, § 10')
  for (const o of p.sem_dever_identificado) assert.ok(o.trecho && o.dispositivo && o.motivo === 'sem dever identificado')
  // um dispositivo nunca está em duas listas
  const ids = [...p.obrigacoes, ...p.outros_dispositivos, ...p.sem_dever_identificado].map((o) => o.id)
  assert.equal(new Set(ids).size, ids.length)
  // RN 1.137: 153 - 5 incisos de prazo - Art. 18 (vigência).
  assert.equal(planos.rn1137.resumo.aplicaveis, 147)
})
