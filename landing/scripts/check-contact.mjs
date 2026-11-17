// Trava de publicação: o build de produção falha enquanto o e-mail de contato for o de exemplo.
import { readFile } from 'node:fs/promises'

const site = await readFile(new URL('../src/content/site.ts', import.meta.url), 'utf8')
const email = site.match(/email:\s*'([^']+)'/)?.[1] ?? ''
if (!email || /@example\.(com|org|net)$/i.test(email)) {
  console.error(
    `E-mail de contato ainda é "${email}". Defina o e-mail oficial em src/content/site.ts antes de publicar.`,
  )
  process.exit(1)
}
console.log(`contato: ${email}`)
