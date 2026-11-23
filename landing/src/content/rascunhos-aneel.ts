export interface RascunhoAneel {
  id: string
  rotulo: string
  tipo: string
  duvida: string
  leituras_possiveis: string[]
  limite: string | null
  referencias: {
    dispositivo: string
    trecho: string
    itens: string[]
    fonte: { titulo: string; url: string | null; sha256: string }
    possiveis_esclarecimentos: {
      citacao: string
      fonte: { titulo: string; url: string; sha256: string; arquivo: string; consultado_em: string }
    }[]
  }[]
}

/** O item mostra só suas citações; o relatório usa os grupos completos, sem repetir perguntas. */
export function rascunhosDoItem(rascunhos: RascunhoAneel[], id: string): RascunhoAneel[] {
  return rascunhos.map((r) => ({ ...r, referencias: r.referencias.filter((f) => f.itens.includes(id)) })).filter((r) => r.referencias.length)
}
