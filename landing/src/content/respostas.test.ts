import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { LIMITE_JA_FAZEMOS, RESPOSTAS_VAZIAS, alternarProva, carregar, chaveDeArmazenamento, definirJaFazemos, limitar, salvar, type Armazem } from './respostas.ts'

const memoria = (): Armazem & { dados: Record<string, string> } => {
  const dados: Record<string, string> = {}
  return { dados, getItem: (k) => dados[k] ?? null, setItem: (k, v) => { dados[k] = v } }
}

test('"o que já fazemos" tem limite de 300 caracteres', () => {
  assert.equal(LIMITE_JA_FAZEMOS, 300)
  assert.equal(limitar('a'.repeat(500)).length, 300)
  assert.equal(definirJaFazemos(RESPOSTAS_VAZIAS, 'tema', 'x'.repeat(301)).jaFazemos.tema.length, 300)
})

test('salva e lê no armazém; sem armazém ou com erro, avisa em vez de quebrar', () => {
  const a = memoria()
  const r = alternarProva(definirJaFazemos(RESPOSTAS_VAZIAS, 't1', 'plano aprovado'), 't1', 'elaborar_ou_revisar_plano:0')
  assert.equal(salvar(a, 'rn1137', r), true)
  assert.deepEqual(carregar(a, 'rn1137'), r)
  assert.deepEqual(carregar(a, 'ren1174'), { jaFazemos: {}, provas: {} }) // cada norma tem o seu
  assert.equal(salvar(null, 'rn1137', r), false)
  const cheio: Armazem = { getItem: () => null, setItem: () => { throw new Error('QuotaExceededError') } }
  assert.equal(salvar(cheio, 'rn1137', r), false)
  assert.deepEqual(carregar({ getItem: () => { throw new Error('SecurityError') }, setItem() {} }, 'rn1137'), { jaFazemos: {}, provas: {} })
})

test('dado ruim no armazém (JSON quebrado, tipos errados, texto longo) não passa', () => {
  const a = memoria()
  a.dados[chaveDeArmazenamento('rn1137')] = '{nao e json'
  assert.deepEqual(carregar(a, 'rn1137'), { jaFazemos: {}, provas: {} })
  a.dados[chaveDeArmazenamento('rn1137')] = JSON.stringify({ jaFazemos: { t: 'y'.repeat(900), u: 5 }, provas: { t: ['a', 3], u: 'x' } })
  const r = carregar(a, 'rn1137')
  assert.equal(r.jaFazemos.t.length, 300)
  assert.ok(!('u' in r.jaFazemos) && !('u' in r.provas))
  assert.deepEqual(r.provas.t, ['a'])
})

test('marcar a mesma prova duas vezes desmarca', () => {
  const um = alternarProva(RESPOSTAS_VAZIAS, 't', 'p:0')
  assert.deepEqual(um.provas.t, ['p:0'])
  assert.deepEqual(alternarProva(um, 't', 'p:0').provas.t, [])
})

test('nada sai por rede: o código das respostas não usa fetch, XHR nem beacon', () => {
  for (const arq of ['./respostas.ts', '../components/plano/Respostas.tsx']) {
    const src = readFileSync(new URL(arq, import.meta.url), 'utf-8')
    assert.doesNotMatch(src, /\bfetch\s*\(|XMLHttpRequest|sendBeacon|WebSocket/)
  }
})
