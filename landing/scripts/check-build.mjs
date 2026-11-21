import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { pages } from './page-meta.mjs'
for (const p of pages) {
  const html = await readFile(`dist/${p.file}`, 'utf8')
  assert.ok(html.includes(p.description), `Metadados antigos em ${p.path}`)
  assert.ok(html.includes(`property="og:description" content="${p.description}"`))
  assert.ok(html.includes(`name="twitter:description" content="${p.description}"`))
  assert.ok(!html.includes('<div id="root"></div>'), `Sem conteúdo em ${p.path}`)
  const chaves = { '/': ['Ver demonstração', '/demo/executivo'], '/demo': ['3 decisões para esta semana', 'Visão executiva →', 'Limpar filtros', 'Mostrando'], '/demo/executivo': ['Comece por', 'Plano completo →', 'Toque num item', 'por infração', 'se agir antes da fiscalização', '* preliminar · valores ilustrativos · não é parecer jurídico'] }[p.path]
  for (const c of chaves) assert.ok(html.includes(c), `Falta "${c}" em ${p.path}`)
  // Nunca "Grupo IV" sozinho na visão executiva: sempre "infração grave (Grupo IV)".
  if (p.path === '/demo/executivo') assert.ok([...html.matchAll(/Grupo (?:I|II|III|IV|V)/g)].every((m) => html[m.index - 1] === '('), 'Grupo sem o nome da gravidade')
  if (p.path === '/demo/executivo') {
    assert.equal([...html.matchAll(/aria-controls="painel"/g)].length, 5, 'cinco blocos clicáveis')
    assert.ok(html.includes('role="region"') && html.includes('aria-expanded="false"'))
    assert.ok(!/Como calculamos|Referência do setor|deveres identificados/.test(html), 'texto que sai da primeira tela')
  }
  if (p.path === '/demo') assert.ok(html.includes('Não constitui parecer jurídico') && html.includes('Iniciativa em validação'))
  assert.ok(!/R\$\s*0(?:[,.]00)?\s+a\s+R\$/.test(html))
}
console.log('HTML, metadados e pré-renderização conferidos nas três rotas')
