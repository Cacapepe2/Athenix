import { test } from 'node:test'
import assert from 'node:assert/strict'
import { FILTROS_INICIAIS, blocosDoPlano, filtrar, filtrosDaUrl, gravidadeDoBloco, situacaoDoBloco, urlComFiltros } from './filtros.ts'
import { NORMAS } from './executivo.ts'
import { SIM_INICIAL } from './plano.ts'

const todos = blocosDoPlano(SIM_INICIAL, 'preliminar')

test('o plano lista todas as obrigações das duas normas, sem somar nada', () => {
  assert.equal(todos.length, NORMAS.reduce((s, n) => s + n.dados.obrigacoes.length, 0))
  assert.equal(filtrar(todos, FILTROS_INICIAIS).length, todos.length)
  assert.equal(new Set(todos.map((b) => `${b.norma}-${b.id}`)).size, todos.length)
})

test('filtro de norma, situação, gravidade e enquadramento; combinados cortam por interseção', () => {
  for (const n of NORMAS) assert.equal(filtrar(todos, { ...FILTROS_INICIAIS, norma: n.id }).length, n.dados.obrigacoes.length)
  const vencidas = filtrar(todos, { ...FILTROS_INICIAIS, situacao: 'vencida' })
  assert.ok(vencidas.length > 0 && vencidas.every((b) => situacaoDoBloco(b) === 'vencida'))
  const graves = filtrar(todos, { ...FILTROS_INICIAIS, gravidade: 'grave' })
  assert.ok(graves.length > 0 && graves.every((b) => b.valor?.grupo === 'IV'))
  const semEnquadrar = filtrar(todos, { ...FILTROS_INICIAIS, gravidade: 'a-enquadrar' })
  assert.ok(semEnquadrar.every((b) => !b.valor))
  const sug = filtrar(todos, { ...FILTROS_INICIAIS, enquadramento: 'sugerido' })
  const ident = filtrar(todos, { ...FILTROS_INICIAIS, enquadramento: 'identificado' })
  assert.ok(sug.every((b) => b.valor?.origem === 'sugerido') && ident.every((b) => b.valor?.origem === 'identificado'))
  const comb = filtrar(todos, { ...FILTROS_INICIAIS, norma: 'rn1137', situacao: 'vencida', gravidade: 'grave' })
  assert.ok(comb.every((b) => b.norma === 'rn1137' && situacaoDoBloco(b) === 'vencida' && gravidadeDoBloco(b) === 'grave'))
  assert.ok(comb.length <= vencidas.length)
})

test('as vencidas vêm antes das demais, na ordem da executiva', () => {
  for (const n of NORMAS) {
    const sit = todos.filter((b) => b.norma === n.id).map((b) => (b.situacaoPrazo === 'vencida' ? 0 : 1))
    assert.deepEqual(sit, [...sit].sort((a, b) => a - b))
  }
})

test('filtros na URL: ida e volta, "todas" sai da URL e os outros parâmetros ficam', () => {
  const f = filtrosDaUrl('?so_norma=ren1174&situacao=a-vencer&gravidade=grave&enquadramento=sugerido')
  assert.deepEqual(f, { norma: 'ren1174', situacao: 'a-vencer', gravidade: 'grave', enquadramento: 'sugerido' })
  assert.equal(urlComFiltros('', f), '?so_norma=ren1174&situacao=a-vencer&gravidade=grave&enquadramento=sugerido')
  // ?norma= escolhe o plano da página e nunca é tocado pelos filtros
  assert.equal(urlComFiltros('?norma=ren1174&so_norma=rn1137', { ...FILTROS_INICIAIS }), '?norma=ren1174')
  assert.equal(urlComFiltros('?tema=alternativo&situacao=vencida', { ...FILTROS_INICIAIS }), '?tema=alternativo')
  assert.equal(urlComFiltros('', FILTROS_INICIAIS), '')
  // valor desconhecido (link antigo ou adulterado) vira "todas"
  assert.deepEqual(filtrosDaUrl('?so_norma=xyz&situacao=<script>&gravidade=&enquadramento=1'), FILTROS_INICIAIS)
})

test('as opções de gravidade cobrem todos os blocos (nenhuma obrigação some com um filtro)', () => {
  const cobertos = filtrar(todos, { ...FILTROS_INICIAIS, gravidade: 'grave' }).length + ['seria', 'media', 'leve', 'gravissima', 'a-enquadrar'].reduce((s, g) => s + filtrar(todos, { ...FILTROS_INICIAIS, gravidade: g as never }).length, 0)
  assert.equal(cobertos, todos.length)
})

test('o contador "Mostrando N de M" bate com o filtro', () => {
  const f = filtrosDaUrl('?situacao=vencida')
  assert.equal(filtrar(todos, f).length, todos.filter((b) => b.situacaoPrazo === 'vencida').length)
})
