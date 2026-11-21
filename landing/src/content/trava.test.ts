import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { GRUPO_NA_PAGINA, gruposSemNome } from './trava.ts'

test('a regex da trava termina em fronteira de palavra (\b), não em backspace', () => {
  assert.ok(!GRUPO_NA_PAGINA.source.includes('\u0008'))
  assert.ok(GRUPO_NA_PAGINA.source.endsWith('\\b'))
  assert.ok(!readFileSync(new URL('../../scripts/check-build.mjs', import.meta.url), 'utf-8').includes('\u0008'), 'nenhum backspace no script do build')
})

test('HTML certo passa e HTML errado reprova: "Grupo IV" sozinho não passa', () => {
  assert.deepEqual(gruposSemNome('<p>infração grave (Grupo IV)</p>'), [])
  assert.deepEqual(gruposSemNome('<p>infração média (Grupo II) e infração grave (Grupo IV)</p>'), [])
  assert.equal(gruposSemNome('<p>Grupo IV</p>').length, 1) // o caso do achado: antes passava (conjunto vazio)
  assert.equal(gruposSemNome('<p>Grupo II</p><p>grave (Grupo IV)</p><p>Grupo V</p>').length, 2)
  assert.deepEqual(gruposSemNome('<p>sem nada de grupo</p>'), []) // sem menção: nada a reprovar
})
