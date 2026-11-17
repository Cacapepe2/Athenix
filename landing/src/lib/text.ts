/** Mapeia o progresso de rolagem (0–1) para o índice da etapa ativa. */
export function stepAt(progress: number, count: number): number {
  return Math.min(count - 1, Math.max(0, Math.floor(progress * count)))
}

/** Divide o texto em [antes, trecho, depois]; null se o trecho não for literal — nunca realça aproximações. */
export function splitAnchor(text: string, anchor: string): [string, string, string] | null {
  const start = anchor ? text.indexOf(anchor) : -1
  if (start < 0) return null
  return [text.slice(0, start), anchor, text.slice(start + anchor.length)]
}
