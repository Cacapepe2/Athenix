import test from 'node:test'
import assert from 'node:assert/strict'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative, sep } from 'node:path'
import { temaDaUrl } from '../tema.ts'

const SRC = new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')
const TOKENS = join(SRC, 'styles', 'tokens.css')

function arquivos(dir: string): string[] {
  return readdirSync(dir).flatMap((nome) => {
    const caminho = join(dir, nome)
    return statSync(caminho).isDirectory() ? arquivos(caminho) : [caminho]
  })
}

// ---------- nada de cor, fonte ou raio fora de tokens.css ----------

const COR = /#[0-9a-fA-F]{3,8}(?![0-9a-zA-Z])|\brgba?\(|\bhsla?\(/
const FONTE = /\b(?:Inter Tight|Helvetica|Arial|Georgia|Newsreader|Times New Roman|Roboto|Segoe UI)\b|font-family\s*:(?!\s*var\()/
const EXCECAO = /token-ok:\s*\S+/ // comentário explícito na mesma linha, com o motivo

test('nenhuma cor (hex, rgb, hsl) nem nome de fonte em landing/src fora de styles/tokens.css', () => {
  const achados: string[] = []
  for (const arq of arquivos(SRC)) {
    if (arq === TOKENS || !/\.(?:tsx?|css|html)$/.test(arq) || /\.test\.ts$/.test(arq)) continue
    readFileSync(arq, 'utf-8').split('\n').forEach((linha, i) => {
      if (EXCECAO.test(linha)) return
      if (COR.test(linha) || FONTE.test(linha)) achados.push(`${relative(SRC, arq).split(sep).join('/')}:${i + 1}: ${linha.trim().slice(0, 100)}`)
    })
  }
  assert.deepEqual(achados, [], `mova para styles/tokens.css:\n${achados.join('\n')}`)
})

test('raio e sombra: nada de rounded arbitrário nem sombra com cor fora dos tokens', () => {
  const achados: string[] = []
  for (const arq of arquivos(SRC)) {
    if (!/\.tsx$/.test(arq)) continue
    readFileSync(arq, 'utf-8').split('\n').forEach((linha, i) => {
      const pontinho = /\bh-(?:1\.5|2|3|4)\b[^"`]*\bw-(?:1\.5|2|3|4)\b|animate-ping|inset-0|absolute rounded-full/.test(linha)
      if ((/\brounded-\[|\bshadow-(?:\[|sm|md|lg|xl|2xl)|\bfont-serif\b|\btracking-\[|\buppercase\b/.test(linha) || (/\brounded-full\b/.test(linha) && !pontinho)) && !EXCECAO.test(linha)) achados.push(`${relative(SRC, arq)}:${i + 1}`)
    })
  }
  assert.deepEqual(achados, [])
})

// ---------- contraste dos pares de texto e fundo (WCAG, mínimo 4,5:1) ----------

function lerTokens(css: string): Map<string, Record<string, string>> {
  const blocos = new Map<string, Record<string, string>>()
  for (const [, seletor, corpo] of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    const vars: Record<string, string> = {}
    for (const [, nome, valor] of corpo.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) vars[nome] = valor.trim()
    blocos.set(seletor.replace(/\/\*[\s\S]*?\*\//g, '').trim(), vars)
  }
  return blocos
}

function luminancia(hex: string): number {
  const n = parseInt(hex.slice(1), 16)
  const canais = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((c) => {
    const v = c / 255
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * canais[0] + 0.7152 * canais[1] + 0.0722 * canais[2]
}

export function contraste(a: string, b: string): number {
  const [x, y] = [luminancia(a), luminancia(b)].sort((m, n) => n - m)
  return (x + 0.05) / (y + 0.05)
}

const PARES: [string, string][] = [
  ['--cor-texto', '--cor-fundo'],
  ['--cor-texto-invertido', '--cor-texto'],
  ['--cor-destaque-texto', '--cor-fundo'],
  ['--cor-destaque', '--cor-fundo'],
  ['--cor-evite', '--cor-fundo'],
  ['--cor-texto', '--cor-hover'],
  ['--cor-destaque-texto', '--cor-hover'],
  ['--cor-texto-invertido', '--cor-destaque'],
  ['--cor-barra-media', '--cor-fundo'],
]

const css = readFileSync(TOKENS, 'utf-8')
const blocos = lerTokens(css)
const base = blocos.get(':root')!
const temas = [...blocos.entries()].filter(([sel]) => /\[data-tema=/.test(sel))

test('tokens.css tem o bloco base com todos os tokens pedidos', () => {
  for (const nome of ['--cor-fundo', '--cor-texto', '--cor-texto-invertido', '--cor-destaque', '--cor-destaque-texto', '--cor-evite', '--cor-linha-suave', '--cor-hover', '--cor-barra-teto', '--cor-barra-media', '--cor-barra-reducao', '--cor-trilho', '--fonte-base', '--raio', '--borda-forte', '--borda-titulo', '--sombra-hover', '--duracao-rapida', '--duracao-painel', '--curva']) assert.ok(base[nome], nome)
  assert.equal(base['--raio'], '0px')
})

for (const [nome, vars] of [[':root', base] as const, ...temas.map(([sel, v]) => [sel, { ...base, ...v }] as const)]) {
  test(`contraste ≥ 4,5:1 nos pares de texto e fundo (${nome})`, () => {
    for (const [fg, bg] of PARES) {
      const r = contraste(vars[fg], vars[bg])
      assert.ok(r >= 4.5, `${fg} sobre ${bg}: ${r.toFixed(2)}:1`)
    }
  })
}

test('tema alternativo existe e muda o destaque', () => {
  const alt = temas.find(([sel]) => sel.includes('"alternativo"'))
  assert.ok(alt, 'bloco [data-tema="alternativo"]')
  assert.notEqual(alt[1]['--cor-destaque'], base['--cor-destaque'])
})

test('?tema= só aceita nome simples (aplicado como data-tema)', () => {
  assert.equal(temaDaUrl('?tema=alternativo'), 'alternativo')
  assert.equal(temaDaUrl('?norma=ren1174&tema=alternativo'), 'alternativo')
  assert.equal(temaDaUrl(''), null)
  assert.equal(temaDaUrl('?tema=<script>'), null)
  assert.equal(temaDaUrl('?tema=a b'), null)
})

test('o tema alternativo é aplicado no <html> e removido sem o parâmetro', async () => {
  const { aplicarTema } = await import('../tema.ts')
  const doc = { documentElement: { dataset: {} as Record<string, string> } } as unknown as Document
  aplicarTema(doc, '?tema=alternativo')
  assert.equal(doc.documentElement.dataset.tema, 'alternativo')
  aplicarTema(doc, '')
  assert.equal(doc.documentElement.dataset.tema, undefined)
})
