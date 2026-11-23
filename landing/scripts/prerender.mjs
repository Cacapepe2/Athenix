import { mkdir, readFile, rm, writeFile } from 'node:fs/promises'
import { pathToFileURL } from 'node:url'
import { dirname, resolve } from 'node:path'
import { pages } from './page-meta.mjs'

const empty = '<div id="root"></div>'
const template = await readFile(resolve('dist/index.html'), 'utf8')
const { render, diaDoBuild } = await import(pathToFileURL(resolve('dist-ssr/entry-server.js')).href)
const escape = (s) => s.replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;')
if (!template.includes(empty)) throw new Error('HTML sem ponto de pré-renderização')
for (const page of pages) {
  const body = render(page.path)
  if (body.length < 1000) throw new Error(`Pré-renderização incompleta: ${page.path}`)
  let html = template.replace(empty, `<div id="root" data-dia="${diaDoBuild}">${body}</div>`)
    .replace(/<title>.*?<\/title>/, `<title>${escape(page.title)}</title>`)
    .replace(/<meta name="description"[^>]*>/, `<meta name="description" content="${escape(page.description)}" />`)
    .replace(/<meta property="og:title"[^>]*>/, `<meta property="og:title" content="${escape(page.title)}" />`)
    .replace(/<meta property="og:description"[^>]*>/, `<meta property="og:description" content="${escape(page.description)}" />`)
    .replace('</head>', `<link rel="canonical" href="https://athenix-two.vercel.app${page.path}" /><meta property="og:url" content="https://athenix-two.vercel.app${page.path}" /><meta name="twitter:title" content="${escape(page.title)}" /><meta name="twitter:description" content="${escape(page.description)}" /></head>`)
  const file = resolve('dist', page.file)
  await mkdir(dirname(file), { recursive: true })
  await writeFile(file, html)
  console.log(`Pré-renderizado ${page.path}: ${body.length} caracteres`)
}
await rm(resolve('dist-ssr'), { recursive: true, force: true })
