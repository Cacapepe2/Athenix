// Trava do build para a visão executiva: nunca "Grupo IV" sozinho; sempre "infração grave (Grupo IV)".
// Fica aqui (e não no script do build) para ser testada com HTML certo e errado: o escape da regex já virou
// backspace uma vez e a trava passou por conjunto vazio sem ninguém notar.
export const GRUPO_NA_PAGINA = /Grupo (?:I|II|III|IV|V)\b/g

/** Trechos "Grupo X" que NÃO vêm entre parênteses logo depois do nome da gravidade. */
export function gruposSemNome(html: string): string[] {
  return [...html.matchAll(GRUPO_NA_PAGINA)].filter((m) => html[m.index - 1] !== '(').map((m) => html.slice(Math.max(0, m.index - 30), m.index + m[0].length + 5))
}
