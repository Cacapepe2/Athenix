// Dados 100% FICTÍCIOS usados na demonstração. Não representam norma real, órgão real
// nem análise regulatória. Cada `anchor` deve ser cópia literal de um trecho do artigo
// citado (verificado em demo.test.ts) — a demo segue a mesma regra de rastreabilidade do produto.

export type RiskLevel = 'Alta' | 'Média' | 'Baixa'
export type ImpactArea = 'Regulatório' | 'Operacional' | 'Financeiro' | 'Reputacional'

export interface Article {
  id: string
  label: string
  text: string
}

export interface Change {
  id: string
  title: string
  detail: string
  articleId: string
}

export interface Obligation {
  id: string
  short: string
  title: string
  articleId: string
  anchor: string
  deadline: string
  deadlineKind: 'Por evento' | 'Contínuo' | 'Anual'
  /** Quando a norma não permite fixar a data, ela fica pendente — nunca é inventada. */
  pending?: string
  owner: string
  risks: Record<ImpactArea, RiskLevel>
  impactNote: string
}

export const demoNorm = {
  badge: 'Norma fictícia',
  kind: 'Resolução Demonstrativa',
  number: 'nº 042/2026',
  issuer: 'Órgão regulador fictício',
  published: '14/10/2026',
  effective: '01/03/2027',
  subject:
    'Estabelece procedimentos para registro e comunicação de interrupções em instalações de transmissão.',
  fingerprint: 'sha256 9f2c…e41a',
  articles: [
    {
      id: 'art1',
      label: 'Art. 1º',
      text: 'Esta Resolução estabelece procedimentos para o registro e a comunicação de interrupções em instalações de transmissão de energia elétrica.',
    },
    {
      id: 'art3',
      label: 'Art. 3º',
      text: 'A concessionária deverá comunicar ao órgão regulador, em até 48 (quarenta e oito) horas, toda interrupção com duração superior a 30 (trinta) minutos.',
    },
    {
      id: 'art5',
      label: 'Art. 5º',
      text: 'Os registros de que trata o art. 3º deverão ser mantidos por, no mínimo, 5 (cinco) anos, à disposição da fiscalização.',
    },
    {
      id: 'art7',
      label: 'Art. 7º',
      text: 'A concessionária deverá publicar em seu sítio eletrônico, anualmente, relatório consolidado das interrupções do ano anterior.',
    },
    {
      id: 'art9',
      label: 'Art. 9º',
      text: 'O descumprimento do disposto nesta Resolução sujeita o agente às penalidades previstas na regulamentação vigente.',
    },
    {
      id: 'art12',
      label: 'Art. 12',
      text: 'Esta Resolução entra em vigor em 1º de março de 2027.',
    },
  ] satisfies Article[],
}

export const changes: Change[] = [
  {
    id: 'c1',
    title: 'Novo prazo de comunicação',
    detail: 'Interrupções acima de 30 minutos passam a exigir comunicação em até 48 horas.',
    articleId: 'art3',
  },
  {
    id: 'c2',
    title: 'Retenção mínima de registros',
    detail: 'Os registros das interrupções devem ser guardados por pelo menos 5 anos.',
    articleId: 'art5',
  },
  {
    id: 'c3',
    title: 'Relatório público anual',
    detail: 'Um relatório consolidado do ano anterior deve ser publicado no site da empresa.',
    articleId: 'art7',
  },
]

export const obligations: Obligation[] = [
  {
    id: 'o1',
    short: 'Comunicar interrupções',
    title: 'Comunicar ao regulador interrupções com mais de 30 minutos',
    articleId: 'art3',
    anchor: 'deverá comunicar ao órgão regulador, em até 48 (quarenta e oito) horas',
    deadline: 'Até 48 h após cada ocorrência',
    deadlineKind: 'Por evento',
    owner: 'Operação do sistema',
    risks: { Regulatório: 'Alta', Operacional: 'Média', Financeiro: 'Média', Reputacional: 'Baixa' },
    impactNote: 'Exige rotina de detecção e comunicação contínua; atraso pode caracterizar descumprimento (Art. 9º).',
  },
  {
    id: 'o2',
    short: 'Manter registros',
    title: 'Manter registros das interrupções por no mínimo 5 anos',
    articleId: 'art5',
    anchor: 'deverão ser mantidos por, no mínimo, 5 (cinco) anos',
    deadline: 'Contínuo, a partir de 01/03/2027',
    deadlineKind: 'Contínuo',
    owner: 'Regulatório + TI',
    risks: { Regulatório: 'Média', Operacional: 'Baixa', Financeiro: 'Baixa', Reputacional: 'Baixa' },
    impactNote: 'Pode exigir ajuste na política de retenção e nos sistemas de registro.',
  },
  {
    id: 'o3',
    short: 'Publicar relatório',
    title: 'Publicar relatório anual consolidado das interrupções',
    articleId: 'art7',
    anchor: 'deverá publicar em seu sítio eletrônico, anualmente, relatório consolidado',
    deadline: 'Anual',
    deadlineKind: 'Anual',
    pending: 'A norma não fixa a data-base da primeira publicação. Data pendente de revisão.',
    owner: 'Regulatório + Comunicação',
    risks: { Regulatório: 'Média', Operacional: 'Baixa', Financeiro: 'Baixa', Reputacional: 'Média' },
    impactNote: 'Exposição pública dos indicadores; requer consolidação anual dos dados.',
  },
]

export const impactAreas: ImpactArea[] = ['Regulatório', 'Operacional', 'Financeiro', 'Reputacional']

export const articleById = (id: string) => demoNorm.articles.find((a) => a.id === id)!
