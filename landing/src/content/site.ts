// Todos os textos do site. Edite aqui sem tocar nos componentes.
// Referência: docs/POSICIONAMENTO.md. Regra: nada de clientes, métricas, depoimentos ou resultados que não
// existam; o que ainda está em validação é dito como tal.

export const contact = {
  // E-mail oficial a definir pelo fundador. `npm run build` falha enquanto for example.com (não publicar).
  email: 'contato@example.com',
  subject: 'Conversa sobre piloto — Athenix',
}

export const nav = {
  tagline: 'Inteligência regulatória',
  links: [
    { href: '#negocio', label: 'O negócio' },
    { href: '#desafio', label: 'O desafio' },
    { href: '#da-norma-a-acao', label: 'Como funciona' },
    { href: '#demonstracao', label: 'Demonstração' },
    { href: '#abordagem', label: 'Abordagem' },
    { href: '#para-quem', label: 'Para quem' },
  ],
  cta: { href: '#contato', label: 'Conversar com o time' },
}

export const hero = {
  eyebrow: 'Inteligência regulatória para o setor elétrico',
  // Frase curta do posicionamento (docs/POSICIONAMENTO.md), em três linhas.
  titleLines: ['Quanto cada mudança regulatória', 'pode custar à sua empresa,', 'e o que priorizar.'],
  subtitle:
    'A Athenix estima, para cada obrigação de uma norma da ANEEL, a faixa de impacto em reais e o prazo, com premissas visíveis, nível de confiança e o trecho exato da fonte. Assim, quem decide sabe o que fazer primeiro.',
  primary: { href: '#demonstracao', label: 'Ver a demonstração' },
  secondary: { href: '#contato', label: 'Conversar sobre um piloto' },
  status: 'Iniciativa em validação · MVP em desenvolvimento',
  principles: [
    'Cada número com premissa, confiança e fonte',
    'Rastreável até o trecho da norma',
    'Revisão humana antes de qualquer conclusão',
  ],
}

// Resumo de negócio (apresentação de empreendedorismo). Cada item aponta para a seção que o aprofunda.
export const business = {
  eyebrow: 'O negócio em resumo',
  title: 'A Athenix em seis respostas.',
  intro: 'A tese do negócio, de forma direta. Cada resposta é aprofundada ao longo da página.',
  note: 'Iniciativa em validação: as respostas descrevem hipóteses e direção, não resultados comprovados.',
  more: 'Ver detalhes',
  items: [
    {
      question: 'Qual o problema e a oportunidade?',
      answer:
        'Normas da ANEEL mudam com frequência e cada mudança pode gerar obrigações, prazos e multas. Saber o que cada uma pode custar exige leitura especializada e cálculo manual.',
      href: '#desafio',
    },
    {
      question: 'Qual necessidade queremos resolver?',
      answer:
        'Saber quanto cada mudança regulatória pode custar à empresa e o que priorizar, com cada estimativa ligada ao trecho da fonte.',
      href: '#da-norma-a-acao',
    },
    {
      question: 'Quem é o público-alvo?',
      answer:
        'Quem usa: Assuntos Regulatórios. Quem decide e compra: gerência ou diretoria de Regulação, Compliance ou Riscos.',
      href: '#para-quem',
    },
    {
      question: 'Quem são os potenciais clientes?',
      answer:
        'Distribuidoras e transmissoras de energia no Brasil. Outros setores regulados são possibilidade futura, condicionada à validação.',
      href: '#potenciais-clientes',
    },
    {
      question: 'Por que o problema importa?',
      answer:
        'Uma obrigação não percebida pode virar multa, retrabalho e atraso. Sem estimativa, a priorização depende de intuição.',
      href: '#por-que-importa',
    },
    {
      question: 'Qual é a oportunidade de negócio?',
      answer:
        'Uma plataforma B2B de uso recorrente, começando pelo setor elétrico. A disposição a pagar ainda está em validação: não há piloto pago até agora.',
      href: '#oportunidade',
    },
  ],
}

export const challenge = {
  eyebrow: 'O desafio',
  title: 'A regulação não chega em linguagem de custo nem de prioridade.',
  body: 'Resoluções, despachos e procedimentos são publicados em ritmos e canais diferentes. Cada mudança precisa ser lida, convertida em obrigações e, então, avaliada: quanto pode custar, até quando e o que fazer primeiro. É um trabalho especializado, em grande parte manual e difícil de rastrear.',
  sources: [
    'Diário Oficial da União',
    'Resoluções normativas',
    'Despachos',
    'Consultas públicas',
    'Procedimentos de Rede',
    'Ofícios circulares',
    'Notas técnicas',
    'Audiências públicas',
  ],
  flowLabel: 'Um fluxo organizado',
  points: [
    {
      title: 'Volume e dispersão',
      text: 'Fontes diferentes, formatos diferentes e atualizações frequentes, sem um ponto único de acompanhamento.',
    },
    {
      title: 'Impacto difícil de estimar',
      text: 'Transformar texto normativo em obrigação e em faixa de multa exige conhecer a régua da ANEEL e o teto legal.',
    },
    {
      title: 'Pouca rastreabilidade',
      text: 'Planilhas e e-mails raramente preservam a ligação entre a estimativa e o trecho da norma que a originou.',
    },
  ],
  need: {
    label: 'A necessidade',
    text: 'Saber o que cada mudança pode custar e o que priorizar, com informação rastreável que apoie decisões.',
  },
}

export const story = {
  eyebrow: 'Da norma à ação',
  title: 'Cinco movimentos entre a norma e a decisão.',
  intro:
    'Trechos reais da RN ANEEL 1.137/2025 mostram o caminho. Os valores de impacto usam um perfil ilustrativo de empresa.',
  steps: [
    {
      title: 'Norma carregada',
      text: 'O documento oficial é carregado e preservado sem alteração, com hash e origem registrados. A captura automática de publicações ainda não faz parte do produto.',
    },
    {
      title: 'Alertas da própria norma',
      text: 'Regras apontam o que pede atenção: alterações na régua de multa e inconsistências do texto, como a mesma norma citada com datas diferentes.',
    },
    {
      title: 'Obrigações identificadas',
      text: 'Cada obrigação candidata nasce ligada ao trecho exato que a fundamenta. Sem trecho, não há obrigação.',
    },
    {
      title: 'Prazos',
      text: 'Prazos são calculados a partir do texto e marcados como provisórios. Quando a norma não fixa a data, ela não é inventada.',
    },
    {
      title: 'Impacto e prioridade',
      text: 'Faixa de impacto em reais por obrigação, com premissas, confiança e fonte (REN 846 e Lei 9.427), e a ordem do que fazer primeiro.',
    },
  ],
}

export const demo = {
  eyebrow: 'Demonstração interativa',
  title: 'Uma norma real, do texto ao impacto estimado.',
  description:
    'Navegue pelas etapas com trechos reais da RN ANEEL 1.137/2025: alertas, obrigações com o trecho de origem, prazos e a faixa de impacto com premissas, confiança e fonte. Aceitar ou rejeitar é sempre decisão de uma pessoa.',
  disclaimer:
    'Trechos reais da RN ANEEL 1.137/2025, processados por regras, sem IA. Os valores de impacto são estimativa ilustrativa, com um perfil ilustrativo de distribuidora que não é empresa real. Não constitui parecer jurídico.',
  tabs: ['Norma', 'Alertas', 'Obrigações', 'Prazos', 'Impacto estimado'],
}

export const approach = {
  eyebrow: 'Nossa abordagem',
  title: 'Quatro pilares. Um foco: impacto e prioridade.',
  description:
    'O MVP concentra-se em estimar riscos e impactos de normas da ANEEL e priorizar o que fazer. Monitoramento e interpretação são a base que garante a fonte de cada número. Gestão da conformidade é direção futura, não funcionalidade disponível.',
  scopeLabels: {
    base: 'Base · em desenvolvimento',
    foco: 'Foco do MVP',
    futuro: 'Visão de produto · etapa futura',
  },
  pillars: [
    {
      title: 'Monitoramento regulatório',
      text: 'Insumo da análise: documentos oficiais carregados e preservados com origem verificável. Sem captura automática de fontes por enquanto.',
      scope: 'base',
    },
    {
      title: 'Interpretação e obrigações',
      text: 'Obrigações candidatas, cada uma ancorada ao trecho de origem, com alertas de inconsistência da própria norma.',
      scope: 'base',
    },
    {
      title: 'Riscos e impactos',
      text: 'Faixa de impacto em reais e prazo por obrigação, com premissas, confiança e fonte, para priorizar o que fazer primeiro.',
      scope: 'foco',
    },
    {
      title: 'Gestão da conformidade',
      text: 'Responsáveis, evidências e fluxo de cumprimento em um só lugar.',
      scope: 'futuro',
    },
  ] as const,
  principlesTitle: 'O que não negociamos',
  principles: [
    'Texto normativo e interpretação sempre separados.',
    'Todo número aponta para premissa, confiança e fonte.',
    'Nenhuma conclusão regulatória sem revisão humana.',
  ],
}

export const audience = {
  eyebrow: 'Para quem construímos',
  title: 'Para quem responde pela regulação dentro da empresa.',
  description:
    'Começamos pelo setor elétrico brasileiro, em distribuidoras e transmissoras, onde a densidade normativa é alta e o custo de um descuido também. Quem usa: Assuntos Regulatórios. Quem decide: gerência ou diretoria de Regulação, Compliance ou Riscos.',
  roles: [
    { title: 'Assuntos Regulatórios', text: 'Ver o que muda, quanto pode custar e o que fazer primeiro.' },
    { title: 'Gerência de Regulação', text: 'Decidir prioridades com faixa de impacto, premissas e fonte.' },
    { title: 'Compliance', text: 'Saber o que precisa ser cumprido e até quando.' },
    { title: 'Jurídico', text: 'Conferir a fundamentação com acesso direto ao texto da norma.' },
    { title: 'Gestão de Riscos', text: 'Comparar a exposição entre obrigações com premissas explícitas.' },
  ],
  sectorsTitle: 'Potenciais clientes',
  sectors: [
    {
      title: 'Energia elétrica',
      text: 'Distribuidoras e transmissoras de energia no Brasil.',
      tag: 'Foco inicial',
      now: true,
    },
    {
      title: 'Telecomunicações',
      text: 'Operadoras sujeitas a regulação setorial intensa.',
      tag: 'Possibilidade futura',
      now: false,
    },
    {
      title: 'Petróleo e gás',
      text: 'Ambiente com múltiplos órgãos e normas técnicas.',
      tag: 'Possibilidade futura',
      now: false,
    },
    {
      title: 'Outros setores regulados',
      text: 'Expansão condicionada à validação de mercado.',
      tag: 'Visão de longo prazo',
      now: false,
    },
  ],
}

export const stakes = {
  eyebrow: 'Por que importa',
  title: 'Um detalhe não percebido hoje pode virar um problema caro amanhã.',
  chain: ['Mudança não identificada', 'Obrigação não cumprida', 'Não conformidade', 'Consequências'],
  consequences: [
    { title: 'Penalidades', text: 'Multas previstas na regulamentação da ANEEL, limitadas pelo teto legal.' },
    { title: 'Retrabalho', text: 'Correções às pressas e revisão de processos já executados.' },
    { title: 'Atrasos', text: 'Projetos e operações impactados por adequações tardias.' },
    { title: 'Impactos financeiros', text: 'Custos não planejados e efeitos sobre a reputação.' },
  ],
  note: 'Por isso cada estimativa da Athenix mostra premissas, confiança e o trecho da fonte: ela precisa poder ser conferida.',
}

export const opportunity = {
  eyebrow: 'Oportunidade',
  title: 'Regulação é contínua. A necessidade de entendê-la também.',
  paragraphs: [
    'Empresas reguladas convivem com mudanças normativas permanentes, o que favorece uma plataforma B2B de uso recorrente.',
    'Equipes regulatórias precisam de respostas que possam conferir: cada número ligado à norma, com premissas explícitas e revisão humana.',
    'A estratégia é começar por um segmento específico, aprofundar o conhecimento do domínio e expandir conforme a validação de mercado.',
  ],
  hypothesis:
    'Hipóteses de negócio em validação, não resultados comprovados: disposição a pagar (sem piloto pago até agora), confiabilidade das estimativas e qual segmento entra primeiro.',
  rings: [
    { label: 'Distribuição e transmissão', tag: 'Ponto de partida' },
    { label: 'Telecom, petróleo e gás', tag: 'Possibilidade futura' },
    { label: 'Outros setores regulados', tag: 'Visão de longo prazo' },
  ],
}

export const closing = {
  eyebrow: 'Contato',
  title: 'Vamos entender juntos a sua rotina regulatória.',
  text: 'Estamos conversando com profissionais do setor elétrico para validar o problema e desenhar um piloto exploratório. Se esse tema faz parte do seu dia a dia, queremos ouvir você.',
  primary: 'Conversar sobre um piloto',
  secondary: { href: '#demonstracao', label: 'Rever a demonstração' },
  footer: {
    rights: 'Athenix · Iniciativa em fase de validação',
    disclaimer:
      'A demonstração usa trechos reais de norma da ANEEL e um perfil ilustrativo de empresa; os valores são estimativa ilustrativa. A Athenix não presta consultoria jurídica e não substitui a análise de profissionais habilitados.',
  },
}
