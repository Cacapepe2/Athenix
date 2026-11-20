// Nome de negócio de cada grupo de infração da REN 846, num ÚNICO lugar (revise aqui).
// O teto de multa de cada grupo (% da receita) NÃO é digitado: vem do plano
// (plano.escala_de_gravidade, com dispositivo, trecho literal, fonte e SHA-256).
// Regra de linguagem: nunca "Grupo IV" sozinho; sempre "infração grave (Grupo IV)".

export const GRUPOS = ['I', 'II', 'III', 'IV', 'V'] as const
export type Grupo = (typeof GRUPOS)[number]

/** I = leve, II = média, III = séria, IV = grave, V = gravíssima. */
export const NOME_DA_GRAVIDADE: Record<Grupo, string> = {
  I: 'leve',
  II: 'média',
  III: 'séria',
  IV: 'grave',
  V: 'gravíssima',
}

export const nomeDaGravidade = (g: string | null | undefined): string => (g && g in NOME_DA_GRAVIDADE ? NOME_DA_GRAVIDADE[g as Grupo] : 'a enquadrar')

/** "infração grave (Grupo IV)"; sem grupo, "infração a enquadrar". */
export const rotuloDoGrupo = (g: string | null | undefined): string => (g && g in NOME_DA_GRAVIDADE ? `infração ${NOME_DA_GRAVIDADE[g as Grupo]} (Grupo ${g})` : 'infração a enquadrar')

/** Só o nome ("grave") para a tabela, onde o texto é curto. */
export const gravidadeCurta = (g: string | null | undefined): string => nomeDaGravidade(g)
