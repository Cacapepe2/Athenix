// Pré-renderização: injeta o HTML do app em dist/index.html (o conteúdo aparece sem JavaScript).
import { readFile, rm, writeFile } from 'node:fs/promises'
import { pathToFileURL } from 'node:url'
import { resolve } from 'node:path'

const vazio = '<div id="root"></div>'
const pagina = resolve('dist/index.html')
const { render } = await import(pathToFileURL(resolve('dist-ssr/entry-server.js')).href)
const html = await readFile(pagina, 'utf8')
if (!html.includes(vazio)) throw new Error('dist/index.html sem <div id="root"></div>: pré-renderização não aplicada')
const corpo = render()
if (corpo.length < 1000) throw new Error('HTML pré-renderizado curto demais: confira entry-server')
await writeFile(pagina, html.replace(vazio, `<div id="root">${corpo}</div>`))
await rm(resolve('dist-ssr'), { recursive: true, force: true })
console.log(`pré-renderizado: ${corpo.length} caracteres em dist/index.html`)
