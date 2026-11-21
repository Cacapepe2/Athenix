/** `?tema=<nome>` ativa o bloco `[data-tema="<nome>"]` de styles/tokens.css (teste de identidade visual). */
export function temaDaUrl(search: string): string | null {
  const nome = new URLSearchParams(search).get('tema')
  return nome && /^[a-z0-9-]{1,30}$/.test(nome) ? nome : null
}

export function aplicarTema(doc: Document = document, search: string = window.location.search) {
  const nome = temaDaUrl(search)
  if (nome) doc.documentElement.dataset.tema = nome
  else delete doc.documentElement.dataset.tema
}
