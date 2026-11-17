import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { pages } from './page-meta.mjs'
for (const p of pages) {
  const html = await readFile(`dist/${p.file}`, 'utf8')
  assert.ok(html.includes(p.description), `Metadados antigos em ${p.path}`)
  assert.ok(html.includes(`property="og:description" content="${p.description}"`))
  assert.ok(html.includes(`name="twitter:description" content="${p.description}"`))
  assert.ok(!html.includes('<div id="root"></div>'), `Sem conteúdo em ${p.path}`)
  assert.ok(html.includes(p.path === '/' ? 'Ver demonstração completa' : 'Como chegamos aqui'))
  assert.ok(!/R\$\s*0(?:[,.]00)?\s+a\s+R\$/.test(html))
}
console.log('HTML, metadados e pré-renderização conferidos nas duas rotas')
