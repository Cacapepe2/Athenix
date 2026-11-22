import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { plano, SIM_INICIAL } from './plano.ts'
import { RESPOSTAS_VAZIAS, type Armazem } from './respostas.ts'
import { carregarRevisoes, camposDaObrigacao, exportarRevisoes, LIMITE_CORRECAO, limparRevisao, linhasDeRevisao, revisarCampo, revisoesValidas, salvarRevisoes, type Revisoes } from './revisoes.ts'
import { montarRelatorio } from './relatorio.ts'

const implicita = plano.obrigacoes.find((o) => o.sujeito_implicito)!
const memoria = () => {
  const dados = new Map<string, string>()
  return { dados, getItem: (k: string) => dados.get(k) ?? null, setItem: (k: string, v: string) => { dados.set(k, v) } }
}

test('confirma os três campos reais, corrige sem mutar o plano e permite desfazer', () => {
  assert.ok(implicita)
  const antes = JSON.stringify(plano)
  let r: Revisoes = {}
  for (const campo of ['sujeito', 'enquadramento', 'area'] as const) r = revisarCampo(r, implicita, campo)
  assert.equal(linhasDeRevisao(r, plano).length, 3)
  for (const v of linhasDeRevisao(r, plano)) assert.equal(v.valor, v.original)
  const corrigidas = revisarCampo(r, implicita, 'area', '  Equipe responsável pela operação  ')
  assert.equal(corrigidas[implicita.id].area?.valor, 'Equipe responsável pela operação')
  assert.equal(corrigidas[implicita.id].area?.estado, 'corrigido')
  assert.equal(r[implicita.id].area?.estado, 'confirmado')
  assert.equal(revisarCampo(corrigidas, implicita, 'area', '   '), corrigidas)
  assert.equal(revisarCampo({}, implicita, 'area', 'x'.repeat(300))[implicita.id].area?.valor.length, LIMITE_CORRECAO)
  assert.ok(!limparRevisao(corrigidas, implicita.id, 'area')[implicita.id].area)
  assert.equal(JSON.stringify(plano), antes)
  const explicita = plano.obrigacoes.find((o) => !o.sujeito_implicito)!
  assert.ok(!camposDaObrigacao(explicita).sujeito)
  assert.deepEqual(revisarCampo({}, explicita, 'sujeito'), {})
})

test('armazenamento separa norma e SHA, tolera erro e descarta dados inválidos ou desatualizados', () => {
  const a = memoria()
  const r = revisarCampo({}, implicita, 'sujeito')
  assert.equal(salvarRevisoes(a, 'rn1137', plano, r), true)
  assert.deepEqual(carregarRevisoes(a, 'rn1137', plano), r)
  assert.deepEqual(carregarRevisoes(a, 'ren1174', plano), {})
  assert.deepEqual(carregarRevisoes(a, 'rn1137', { ...plano, norma: { ...plano.norma, sha256: 'outro' } }), {})
  const bloqueado: Armazem = { getItem() { throw Error('SecurityError') }, setItem() { throw Error('QuotaExceededError') } }
  assert.deepEqual(carregarRevisoes(bloqueado, 'rn1137', plano), {})
  assert.equal(salvarRevisoes(bloqueado, 'rn1137', plano, r), false)
  assert.equal(salvarRevisoes(null, 'rn1137', plano, r), false)
  const k = [...a.dados.keys()][0]
  a.dados.set(k, '{ inválido')
  assert.deepEqual(carregarRevisoes(a, 'rn1137', plano), {})
  for (const v of [null, [], 'x', { [implicita.id]: { area: { estado: 'confirmado', original: implicita.area, valor: 'outro valor' } } }, { [implicita.id]: { area: { estado: 'corrigido', original: 'valor antigo', valor: 'outro' } } }]) assert.deepEqual(revisoesValidas(v, plano), {})
})

test('JSON e relatório incluem valor original, revisão, dispositivo e trecho; números permanecem os mesmos', () => {
  const r = revisarCampo(revisarCampo({}, implicita, 'sujeito'), implicita, 'area', 'Revisão pessoal de teste')
  const json = JSON.parse(exportarRevisoes(r, 'rn1137', plano))
  assert.equal(json.sha256, plano.norma.sha256)
  assert.equal(json.norma, 'rn1137')
  assert.equal(json.revisoes.length, 2)
  for (const v of json.revisoes) {
    assert.equal(v.dispositivo, implicita.dispositivo)
    assert.equal(v.trecho, implicita.trecho)
  }
  const args = { sim: SIM_INICIAL, modo: 'preliminar' as const, diag: {}, respostas: RESPOSTAS_VAZIAS }
  const antes = montarRelatorio(args)
  const depois = montarRelatorio({ ...args, revisoes: r })
  assert.deepEqual(depois.revisoes, json.revisoes)
  assert.deepEqual({ ...depois, revisoes: [] }, antes)
  for (const arquivo of ['./revisoes.ts', '../components/plano/RevisaoLocal.tsx']) {
    const src = readFileSync(new URL(arquivo, import.meta.url), 'utf-8')
    assert.doesNotMatch(src, /\bfetch\s*\(|XMLHttpRequest|sendBeacon|WebSocket|dangerouslySetInnerHTML/)
  }
})
