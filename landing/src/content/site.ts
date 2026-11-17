// Todos os textos do site. Edite aqui sem tocar nos componentes.
// Regra: nada de clientes, métricas, depoimentos ou resultados que não existam.

export const contact = {
  // Substitua pelo e-mail oficial do time antes de publicar (example.com é domínio reservado).
  email: 'contato@example.com',
  subject: 'Conversa sobre piloto exploratório — Athenix',
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
  titleLines: ['Clareza para decisões', 'que não podem esperar.'],
  subtitle:
    'A Athenix está construindo uma plataforma que transforma mudanças normativas em informação organizada: o que mudou, quais obrigações surgem, quem responde e até quando. Sempre com o trecho da fonte ao lado.',
  primary: { href: '#da-norma-a-acao', label: 'Ver como funciona' },
  secondary: { href: '#contato', label: 'Conversar sobre um piloto' },
  status: 'Iniciativa em validação · MVP em desenvolvimento',
  principles: [
    'Rastreável até o trecho da norma',
    'Interpretação da IA sempre identificada',
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
        'Mudanças normativas complexas, publicadas em fontes dispersas, exigem esforço significativo para serem interpretadas e transformadas em ações.',
      href: '#desafio',
    },
    {
      question: 'Qual necessidade queremos resolver?',
      answer:
        'Reduzir o esforço de identificar, compreender e organizar mudanças regulatórias relevantes, com informação rastreável que apoie decisões.',
      href: '#da-norma-a-acao',
    },
    {
      question: 'Quem é o público-alvo?',
      answer:
        'Profissionais de Assuntos Regulatórios, Compliance, Jurídico, Gestão de Riscos e áreas operacionais de empresas reguladas.',
      href: '#para-quem',
    },
    {
      question: 'Quem são os potenciais clientes?',
      answer:
        'Inicialmente, transmissoras e distribuidoras de energia no Brasil. No futuro, telecom, petróleo e gás e outros setores regulados.',
      href: '#potenciais-clientes',
    },
    {
      question: 'Por que o problema importa?',
      answer:
        'Falhas de acompanhamento ou interpretação podem gerar não conformidade, penalidades, retrabalho, atrasos e impactos financeiros e operacionais.',
      href: '#por-que-importa',
    },
    {
      question: 'Qual é a oportunidade de negócio?',
      answer:
        'Uma plataforma B2B recorrente que transforma informação normativa em conhecimento aplicável, começando por um segmento e expandindo com a validação de mercado.',
      href: '#oportunidade',
    },
  ],
}

export const challenge = {
  eyebrow: 'O desafio',
  title: 'A regulação não chega em um só lugar, nem em linguagem de ação.',
  body: 'Resoluções, despachos, consultas públicas e procedimentos são publicados em ritmos e canais diferentes. Cada mudança precisa ser localizada, lida, interpretada e convertida em tarefas. É um trabalho especializado, em grande parte manual e difícil de rastrear.',
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
      title: 'Interpretação custosa',
      text: 'Transformar texto normativo em obrigação concreta consome tempo de especialistas e depende de quem leu.',
    },
    {
      title: 'Pouca rastreabilidade',
      text: 'Planilhas e e-mails raramente preservam a ligação entre a tarefa e o trecho da norma que a originou.',
    },
  ],
  need: {
    label: 'A necessidade',
    text: 'Reduzir o esforço de identificar, compreender e organizar mudanças regulatórias relevantes, com informação rastreável que apoie decisões e ações internas.',
  },
}

export const story = {
  eyebrow: 'Da norma à ação',
  title: 'Cinco movimentos entre a publicação e a decisão.',
  intro: 'Um exemplo fictício mostra o caminho que a Athenix pretende percorrer com cada nova publicação.',
  steps: [
    {
      title: 'Norma publicada',
      text: 'Uma nova publicação é detectada. O documento original é preservado, com origem e data registradas.',
    },
    {
      title: 'Mudança destacada',
      text: 'Os trechos que alteram a rotina da empresa são marcados e resumidos. O resumo é identificado como interpretação da IA.',
    },
    {
      title: 'Obrigações identificadas',
      text: 'Cada obrigação candidata nasce ligada ao trecho exato que a fundamenta. Sem trecho, não há obrigação.',
    },
    {
      title: 'Prazos e responsáveis',
      text: 'Prazos são organizados a partir do texto. Quando a norma é ambígua, a data fica pendente em vez de ser inventada.',
    },
    {
      title: 'Riscos e impactos',
      text: 'Uma avaliação preliminar aponta impactos regulatórios, operacionais e financeiros, para validação da equipe.',
    },
  ],
}

export const demo = {
  eyebrow: 'Demonstração interativa',
  title: 'Explore uma análise, da publicação ao impacto.',
  description:
    'Navegue pelas etapas, selecione uma obrigação e veja de onde ela vem. Experimente aceitar ou rejeitar: a decisão final é sempre de uma pessoa.',
  disclaimer:
    'Demonstração conceitual com norma e dados fictícios. Não representa análise regulatória real nem funcionalidade comercial disponível.',
  tabs: ['Norma', 'Resumo', 'Obrigações', 'Prazos e responsáveis', 'Riscos e impactos'],
}

export const approach = {
  eyebrow: 'Nossa abordagem',
  title: 'Quatro pilares. Um começo deliberadamente estreito.',
  description:
    'A visão de produto cobre o ciclo regulatório completo. O MVP concentra-se nos dois primeiros pilares, aplicados a documentos regulatórios públicos. Os demais são direção, não funcionalidade disponível.',
  scopeLabels: { now: 'Foco do MVP · em desenvolvimento', later: 'Visão de produto · etapas futuras' },
  pillars: [
    {
      title: 'Monitoramento regulatório',
      text: 'Acompanhar publicações relevantes e preservar cada documento com origem verificável.',
      now: true,
    },
    {
      title: 'Interpretação e obrigações',
      text: 'Converter texto normativo em obrigações candidatas, cada uma ancorada ao trecho de origem.',
      now: true,
    },
    {
      title: 'Gestão da conformidade',
      text: 'Organizar responsáveis, prazos e evidências de cumprimento em um só lugar.',
      now: false,
    },
    {
      title: 'Riscos e impactos',
      text: 'Estimar efeitos operacionais e financeiros das mudanças para apoiar a priorização.',
      now: false,
    },
  ],
  principlesTitle: 'O que não negociamos',
  principles: [
    'Texto normativo e interpretação da IA sempre separados.',
    'Toda obrigação aponta para o trecho que a originou.',
    'Nenhuma conclusão regulatória sem revisão humana.',
  ],
}

export const audience = {
  eyebrow: 'Para quem construímos',
  title: 'Para quem responde pela regulação dentro da empresa.',
  description:
    'Começamos pelo setor elétrico brasileiro, em transmissoras e distribuidoras, onde a densidade normativa é alta e o custo de um descuido também.',
  roles: [
    { title: 'Assuntos Regulatórios', text: 'Acompanhar publicações e consolidar o que muda para a empresa.' },
    { title: 'Compliance', text: 'Saber o que precisa ser cumprido, por quem e até quando.' },
    { title: 'Jurídico', text: 'Conferir a fundamentação com acesso direto ao texto da norma.' },
    { title: 'Gestão de Riscos', text: 'Priorizar mudanças pelo potencial de impacto.' },
    { title: 'Áreas operacionais', text: 'Receber obrigações claras, ligadas à própria rotina.' },
  ],
  sectorsTitle: 'Potenciais clientes',
  sectors: [
    {
      title: 'Energia elétrica',
      text: 'Transmissoras e distribuidoras de energia no Brasil.',
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
    { title: 'Penalidades', text: 'Sanções previstas na regulamentação setorial.' },
    { title: 'Retrabalho', text: 'Correções às pressas e revisão de processos já executados.' },
    { title: 'Atrasos', text: 'Projetos e operações impactados por adequações tardias.' },
    { title: 'Impactos financeiros', text: 'Custos não planejados e efeitos sobre a reputação.' },
  ],
  note: 'Por isso a Athenix prioriza confiabilidade sobre velocidade: cada informação precisa poder ser conferida.',
}

export const opportunity = {
  eyebrow: 'Oportunidade',
  title: 'Regulação é contínua. A necessidade de entendê-la também.',
  paragraphs: [
    'Empresas reguladas convivem com mudanças normativas permanentes, o que favorece uma plataforma B2B de uso recorrente.',
    'Ferramentas genéricas de IA não garantem rastreabilidade nem separam texto normativo de interpretação. É justamente disso que equipes regulatórias precisam para confiar em uma resposta.',
    'A estratégia é começar por um segmento específico, aprofundar o conhecimento do domínio e expandir conforme a validação de mercado.',
  ],
  hypothesis: 'Hipóteses de negócio em validação, não resultados comprovados.',
  rings: [
    { label: 'Transmissão e distribuição', tag: 'Ponto de partida' },
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
      'As demonstrações usam dados fictícios. A Athenix não presta consultoria jurídica e não substitui a análise de profissionais habilitados.',
  },
}
