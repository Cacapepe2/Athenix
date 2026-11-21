// O que a empresa escreve e marca no plano ("o que já fazemos", provas que já tem). Fica SÓ no navegador
// (localStorage, com try/catch); nada é enviado. Se o navegador não deixar gravar, a página segue em memória
// e avisa que o texto se perde ao fechar. Lógica pura (recebe o "storage"), testada em respostas.test.ts.
import type { NormaId } from './plano.ts'

export const LIMITE_JA_FAZEMOS = 300

export interface Respostas {
  /** Texto livre por tema (até 300 caracteres). */
  jaFazemos: Record<string, string>
  /** Provas já marcadas ("temos isto") por tema: ids `${tipo}:${n}`. */
  provas: Record<string, string[]>
}
export const RESPOSTAS_VAZIAS: Respostas = { jaFazemos: {}, provas: {} }

export interface Armazem { getItem(k: string): string | null; setItem(k: string, v: string): void }

export const chaveDeArmazenamento = (norma: NormaId) => `athenix:v6:${norma}`
export const limitar = (texto: string) => texto.slice(0, LIMITE_JA_FAZEMOS)

/** Lê as respostas; qualquer falha (sem storage, JSON ruim, formato errado) devolve vazio. */
export function carregar(armazem: Armazem | null, norma: NormaId): Respostas {
  try {
    const bruto = armazem?.getItem(chaveDeArmazenamento(norma))
    if (!bruto) return { jaFazemos: {}, provas: {} }
    const d = JSON.parse(bruto) as Partial<Respostas>
    const jaFazemos: Record<string, string> = {}
    for (const [k, v] of Object.entries(d.jaFazemos ?? {})) if (typeof v === 'string') jaFazemos[k] = limitar(v)
    const provas: Record<string, string[]> = {}
    for (const [k, v] of Object.entries(d.provas ?? {})) if (Array.isArray(v)) provas[k] = v.filter((x): x is string => typeof x === 'string')
    return { jaFazemos, provas }
  } catch {
    return { jaFazemos: {}, provas: {} }
  }
}

/** Grava; devolve false se não deu (a tela então avisa que o texto se perde ao fechar). */
export function salvar(armazem: Armazem | null, norma: NormaId, r: Respostas): boolean {
  try {
    if (!armazem) return false
    armazem.setItem(chaveDeArmazenamento(norma), JSON.stringify(r))
    return true
  } catch {
    return false
  }
}

/** O localStorage do navegador, ou null se o acesso a ele já lança erro (modo privado, dados bloqueados). */
export function armazemDoNavegador(): Armazem | null {
  try {
    return typeof localStorage === 'undefined' ? null : localStorage
  } catch {
    return null
  }
}

export const alternarProva = (r: Respostas, tema: string, prova: string): Respostas => {
  const atual = r.provas[tema] ?? []
  return { ...r, provas: { ...r.provas, [tema]: atual.includes(prova) ? atual.filter((x) => x !== prova) : [...atual, prova] } }
}
export const definirJaFazemos = (r: Respostas, tema: string, texto: string): Respostas => ({ ...r, jaFazemos: { ...r.jaFazemos, [tema]: limitar(texto) } })
