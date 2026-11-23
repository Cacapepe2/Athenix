import dados from './fontes-publicas.json' with { type: 'json' }

interface Localizacao { url: string; pagina: number | null; ultima_pagina: number | null; localizacao: string }
const citacoes: Record<string, Record<string, Localizacao>> = dados.citacoes
const chave = (texto: string) => texto.normalize('NFC').replace(/\s/g, '').replace(/^[“”"]+|[“”"]+$/g, '').replace(/…$/, '')

/** Só cria link com localização registrada. Fragmentos resumidos exigem um único destino. */
export function fonteDaCitacao(sha256: string, trecho: string | null | undefined): string | undefined {
  if (!trecho) return undefined
  const fontes = citacoes[sha256]
  if (!fontes) return undefined
  const texto = chave(trecho)
  if (!texto) return undefined
  if (fontes[texto]) return fontes[texto].url
  const urls = new Set(Object.entries(fontes).filter(([t]) => t.startsWith(texto)).map(([, f]) => f.url))
  return urls.size === 1 ? [...urls][0] : undefined
}
