# Avaliação do FAQ oficial da RN 1.137/2025

O Athenix **acerta 10 de 10 cobertas · 16 não cobertas**. Cobertura: 10 de 26 afirmações verificáveis; 0 das cobertas divergem. Das 32 perguntas, 6 ficaram fora deste placar.

Fonte: [FAQ - Resolução Normativa nº 1.137/2025 (ANEEL)](https://www.gov.br/aneel/pt-br/acesso-a-informacao/perguntas-frequentes/faq-resolucao-normativa-no-1-137-2025), consulta salva em 2026-11-22. SHA-256: `a3ace3d565c44118f29952ebad2b7a5012ab1e210d3d97e687a601f3b276f4da`. Nenhuma consulta à rede ou chamada de IA nesta avaliação.

Plano: `landing/src/content/plano-rn1137.json`, gerado em 2026-11-22, origem `14c7e2e`; norma com SHA-256 `4a581592e981158bb9a9ebbbed10a019d3c06399fd2890389bf88f3609cc5887`. O CI também confere a reprodução do plano. O motor e a linha de base não foram alterados.

## Como ler o resultado

Anotações manuais de avaliação, não revisadas por especialista. Expectativas vêm do FAQ oficial salvo; nenhum parâmetro altera o motor. Campo ausente é não cobertura, nunca uma negativa correta. O escopo de cada caso delimita a afirmação objetiva testada, não aprova a resposta inteira.

Cada pergunta tem uma afirmação objetiva delimitada no campo Escopo. Um acerto não significa que toda a interpretação da resposta, ou um plano operacional real, tenha sido validado. As expectativas foram anotadas manualmente a partir do FAQ; as citações são conferidas contra a resposta salva. Os campos e trechos da resposta Athenix vêm exclusivamente do plano exportado, sem títulos ou sugestões da IA. Falta de um campo, de um requisito ou de uma conclusão negativa é não cobertura, não acerto por ausência. Divergência exige um valor explícito incompatível, como uma data diferente.

Cobertura e acerto são medidas separadas: uma pergunta é coberta quando todos os critérios da afirmação delimitada têm resposta explícita comparável, igual ou divergente. Se algum critério não é coberto, a pergunta fica em não cobertura. Acerto é a concordância entre as perguntas cobertas; as não cobertas não entram nesse denominador.

**Não é um conjunto inteiramente independente:** as perguntas 1.8, 3.2 já alimentam esclarecimentos confirmados no plano. Retirando esses casos, são **acerta 8 de 8 cobertas · 16 não cobertas**. Cobertura independente: 8 de 24 afirmações verificáveis. O resultado não substitui revisão regulatória humana.

## Resultado por pergunta

| Pergunta | Afirmação avaliada | Veredito |
| --- | --- | --- |
| 1.1 | Formalização da indicação dos interlocutores (não avalia a definição de órgão central). | o motor não cobre |
| 1.2 | Destinatários dos canais exclusivos. | igual |
| 1.4 | Disponibilidade e atendimento humano do telefone em urgência/emergência. | igual |
| 1.7 | Gatilho do envio obrigatório de alertas à ANEEL. | o motor não cobre |
| 1.8 | Ausência de prazo estabelecido para a ANEEL publicar instruções, na consulta salva. | igual |
| 1.9 | Existência e data das orientações preliminares da API. | o motor não cobre |
| 2.1 | Conteúdo mínimo obrigatório do plano de manejo. | o motor não cobre |
| 2.2 | Vedação de plano apenas conceitual. | o motor não cobre |
| 2.3 | Ausência de exigência de aprovação formal por cada município. | o motor não cobre |
| 2.4 | Convênio estadual não substitui pactuação municipal quando esta for aplicável. | o motor não cobre |
| 2.5 | Requisitos de responsabilidades e procedimentos do instrumento formal. | igual |
| 2.6 | Manutenção das obrigações, registros por cinco anos e atuação emergencial. | o motor não cobre |
| 3.1 | Data inicial dos efeitos retroativos do DISE. | o motor não cobre |
| 3.2 | Data final para início das apurações do DISE. | igual |
| 3.3 | Início dos eventos considerados na apuração retroativa do DISE. | o motor não cobre |
| 3.4 | Último mês para crédito das compensações iniciais. | o motor não cobre |
| 4.3 | Publicação sem contatos dos responsáveis e com infraestrutura/localização dos recursos. | o motor não cobre |
| 4.4 | Envio de alertas depende de procedimento da ANEEL; manutenção de evidências internas até sua publicação. | o motor não cobre |
| 5.1 | Comunicação automática aos consumidores afetados. | igual |
| 5.2 | Comunicação até uma hora do reconhecimento, independentemente da identificação da causa. | igual |
| 5.3 | Canais mínimos obrigatórios: SMS e aplicativos, com envio automático. | igual |
| 5.4 | Ausência de novo indicador específico de efetividade. | o motor não cobre |
| 5.5 | Linguagem clara, acessível e adequada na disponibilização do plano. | igual |
| 5.6 | Acesso público e irrestrito, sem autenticação prévia. | o motor não cobre |
| 6.1 | Prazo para envio do relatório circunstanciado à fiscalização. | igual |
| 6.2 | Periodicidade dos treinamentos não fixada na norma, a definir no acordo. | o motor não cobre |

## Divergências e lacunas

Nenhum valor explícito incompatível foi identificado nos campos comparados. Isso não significa cobertura completa: as lacunas abaixo permanecem abertas e não foram corrigidas para melhorar o placar.

- **1.1 — o motor não cobre:** O plano identifica os canais e contatos; isso não comprova a exigência específica de formalização da indicação.

- **1.7 — o motor não cobre:** A Tabela 25 não está representada como dever com esse gatilho no plano; não se infere equivalência por proximidade temática.

- **1.9 — o motor não cobre:** O prazo por evento não responde se o ofício preliminar já foi publicado; não se trata o ofício como gatilho definitivo sem fonte/decisão.

- **2.1 — o motor não cobre:** Publicar o plano não comprova a extração dos requisitos da Tabela 20.

- **2.2 — o motor não cobre:** A granularidade operacional esclarecida pelo FAQ não tem uma resposta expressa no plano.

- **2.3 — o motor não cobre:** Ausência da palavra aprovação na extração não prova que ela seja dispensada; o motor não oferece essa conclusão.

- **2.4 — o motor não cobre:** A lista de entes no item 95 não resolve a substituição de competências esclarecida no FAQ.

- **2.6 — o motor não cobre:** O item 98/98.1 está em sem dever identificado, não na contagem de deveres; o plano cobre registros e emergência, mas não a resposta inteira.

- **3.1 — o motor não cobre:** O plano conserva a expressão dois meses, mas não calcula nem distingue a incidência diária e a primeira apuração completa.

- **3.3 — o motor não cobre:** O prazo de implantação de abril não responde ao início do período retroativo.

- **3.4 — o motor não cobre:** O plano não calcula a janela de crédito na fatura, distinta do prazo de implantação.

- **4.3 — o motor não cobre:** O plano cobre a retirada dos contatos, mas não demonstra o conteúdo de infraestrutura exigido pela resposta completa.

- **4.4 — o motor não cobre:** O motor cobre o prazo dependente de evento, mas não extrai o dever provisório de evidências que o FAQ acrescenta.

- **5.4 — o motor não cobre:** Não encontrar indicador no plano não comprova sua inexistência na norma inteira.

- **5.6 — o motor não cobre:** Acesso público no trecho normativo não basta para afirmar que o motor verifica autenticação.

- **6.2 — o motor não cobre:** O plano extrai capacitação e acordo, mas não responde expressamente à ausência de periodicidade; ausência de prazo não é comprovação.

## Casos e evidências

### 1.1 Como deve ser interpretado o conceito de “órgão central” previsto no art. 371-A?

**Escopo:** Formalização da indicação dos interlocutores (não avalia a definição de órgão central).

**Resposta oficial — pergunta 1.1:**

> Para fins do art. 371-A, entende-se por “órgão central” o órgão do respectivo ente (municipal, distrital ou estadual) responsável pela coordenação institucional e pela interlocução centralizada com a distribuidora em situações de interesse público (especialmente em contingências), além dos “representantes designados” por cada ente. A indicação desses interlocutores deve ser formalizada junto ao Poder Público.

**Resposta do Athenix:**

- **Art. 371-A** (`obrigacoes`): “Art. 371-A A distribuidora deve estabelecer canais adicionais de comunicação exclusivos ao atendimento de órgão central e representantes designados dos poderes públicos municipal, distrital e estadual.”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

- **Art. 371-A, § 7º** (`obrigacoes`): “§ 7º A distribuidora deve entregar e manter atualizado junto aos poderes públicos municipal, distrital e estadual a relação dos canais exclusivos e as informações de contato dos representantes institucionais estabelecidos com os horários de atendimento. ....................................................................................................”(NR)”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

**Veredito: o motor não cobre.** O plano identifica os canais e contatos; isso não comprova a exigência específica de formalização da indicação.

Critérios: `trecho` — o motor não cobre.

### 1.2 O atendimento diferenciado deve ser prestado a todo o Poder Público ou apenas aos interlocutores formalmente designados?

**Escopo:** Destinatários dos canais exclusivos.

**Resposta oficial — pergunta 1.2:**

> O tratamento deve ser prestado ao “órgão central” e aos “representantes designados” pelos poderes públicos municipal, distrital e estadual, conforme redação do art. 371-A. Assim, os canais exclusivos são direcionados aos interlocutores formalmente indicados por cada ente, sem prejuízo de a distribuidora manter outros canais gerais de relacionamento institucional.

**Resposta do Athenix:**

- **Art. 371-A** (`obrigacoes`): “Art. 371-A A distribuidora deve estabelecer canais adicionais de comunicação exclusivos ao atendimento de órgão central e representantes designados dos poderes públicos municipal, distrital e estadual.”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

**Veredito: igual.** Compara os destinatários expressos; não avalia a adequação de um cadastro real.

Critérios: `trecho` — igual; `trecho` — igual.

### 1.4 O que caracteriza situações de urgência ou emergência para fins do §5º do art. 371-A?

**Escopo:** Disponibilidade e atendimento humano do telefone em urgência/emergência.

**Resposta oficial — pergunta 1.4:**

> “Urgência/emergência” no contexto do §5º do art. 371-A refere-se a situações que demandem atuação imediata pela distribuidora em coordenação com o Poder Público, usualmente associadas a interrupções emergenciais de longa duração, eventos críticos e situações de risco à segurança, tais como risco à vida, a bens, a instalações essenciais, ou necessidade de ações imediatas de restabelecimento. Nessas hipóteses, o canal telefônico exclusivo deve estar disponível 24 horas por dia, 7 dias por semana, com atendimento humano.

**Resposta do Athenix:**

- **Art. 371-A, § 5º** (`obrigacoes`): “§ 5º O atendimento telefônico exclusivo previsto no §1º deve ter, no caso de urgência/emergência, disponibilidade ininterrupta durante 24 horas por dia e 7 dias por semana, com atendimento humano durante todo o período de funcionamento.”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

**Veredito: igual.** Não valida a classificação de um evento concreto como urgência/emergência.

Critérios: `trecho` — igual; `trecho` — igual.

### 1.7 Quais alertas meteorológicos devem ser encaminhados à ANEEL e por qual canal?

**Escopo:** Gatilho do envio obrigatório de alertas à ANEEL.

**Resposta oficial — pergunta 1.7:**

> Não é todo e qualquer alerta meteorológico. A obrigação criada na Tabela 25 do Módulo 6 é enviar à ANEEL os alertas meteorológicos que justifiquem o acionamento do Plano de Contingência, em qualquer nível. Assim, o gatilho é o acionamento (ou a justificativa objetiva para acionamento) do Plano de Contingência. A ANEEL definirá oportunamente o canal de comunicação para o envio desses alertas.

**Resposta do Athenix:**

- **Art. 14** (`obrigacoes`): “Art. 14. As distribuidoras devem implantar processo de comunicação e acompanhamento da evolução dos eventos climáticos severos de que trata o item 114 do Anexo IV da Resolução Normativa nº 956, de 7 de dezembro de 2021, em até 30 (trinta) dias, contados da publicação das instruções pela ANEEL.”

  Prazo exportado: Prazo conta de um evento ainda sem data · esclarecido (FAQ da ANEEL); data: `None`.

- **item 114** (`sem_dever_identificado`): “114. A ANEEL estabelecerá procedimento para comunicação e acompanhamento das situações de crise enfrentadas pelas distribuidoras. Diretrizes de Comunicação”

**Veredito: o motor não cobre.** A Tabela 25 não está representada como dever com esse gatilho no plano; não se infere equivalência por proximidade temática.

Critérios: `trecho` — o motor não cobre.

### 1.8 Qual o prazo previsto para a ANEEL publicar as instruções complementares sobre comunicação de eventos climáticos severos?

**Escopo:** Ausência de prazo estabelecido para a ANEEL publicar instruções, na consulta salva.

**Resposta oficial — pergunta 1.8:**

> Ainda não há prazo estabelecido para a publicação das instruções pela ANEEL.

**Resposta do Athenix:**

- **Art. 14** (`obrigacoes`): “Art. 14. As distribuidoras devem implantar processo de comunicação e acompanhamento da evolução dos eventos climáticos severos de que trata o item 114 do Anexo IV da Resolução Normativa nº 956, de 7 de dezembro de 2021, em até 30 (trinta) dias, contados da publicação das instruções pela ANEEL.”

  Prazo exportado: Prazo conta de um evento ainda sem data · esclarecido (FAQ da ANEEL); data: `None`.

**Veredito: igual.** Esclarecimento do próprio FAQ já confirmado no plano; este caso não é validação independente.

Critérios: `esclarecimento.leitura` — igual.

### 1.9 As instruções quanto disponibilização da API de que trata item 113 do Módulo 4 do PRODIST já foram publicadas pela ANEEL?

**Escopo:** Existência e data das orientações preliminares da API.

**Resposta oficial — pergunta 1.9:**

> A ANEEL encaminhou às distribuidoras o Ofício Conjunto Circular nº 1/2025‑SMA‑STD/ANEEL (SEI nº 48500.008437/2025-43), contendo orientações e especificações técnicas preliminares voltadas à implantação da API (Application Programming Interface), em 05 de agosto de 2025.

**Resposta do Athenix:**

- **Art. 15** (`obrigacoes`): “Art. 15. As distribuidoras devem disponibilizar a API de que trata item 113 do Anexo IV da Resolução Normativa nº 956, de 7 de dezembro de 2021, com redação dada pelo art. 3º desta Resolução Normativa em até 60 (sessenta) dias, contados da publicação das instruções pela ANEEL.”

  Prazo exportado: Prazo conta de um evento ainda sem data; data: `None`.

**Veredito: o motor não cobre.** O prazo por evento não responde se o ofício preliminar já foi publicado; não se trata o ofício como gatilho definitivo sem fonte/decisão.

Critérios: `instrucoes.data` — o motor não cobre.

### 2.1 Quais são os elementos mínimos que devem compor o Plano de Manejo Vegetal?

**Escopo:** Conteúdo mínimo obrigatório do plano de manejo.

**Resposta oficial — pergunta 2.1:**

> O Plano de Manejo Vegetal deve conter, no mínimo, os elementos da Tabela 20 do Módulo 6: métodos de monitoramento e controle da execução das podas, cronograma das práticas de poda, periodicidade das ações e cuidados ambientais, além de refletir as responsabilidades e diretrizes estabelecidas nos itens 94 a 104 do Módulo 4.

**Resposta do Athenix:**

- **item 103** (`obrigacoes`): “103. As distribuidoras devem disponibilizar a versão mais atualizada de seu plano de manejo vegetal em seu sítio eletrônico na Internet e nos postos de atendimento presencial, de forma acessível ao público, com uso de linguagem clara e adequada, conforme prazo constante do Módulo 6.”

  Prazo exportado: Vencido desde 28/01/2026 (293 dias); data: `2026-01-28`.

- **item 94** (`obrigacoes`): “94. As distribuidoras devem estabelecer um plano de manejo vegetal na sua área de atuação, que contemple a vegetação que interfira em suas redes de distribuição, em coordenação com o Poder Público Municipal e em articulação com os órgãos competentes do Poder Público Estadual e Distrital, e com vistas a garantir a segurança da rede de distribuição, a qualidade, eficiência e a continuidade do fornecimento de energia elétrica.”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

**Veredito: o motor não cobre.** Publicar o plano não comprova a extração dos requisitos da Tabela 20.

Critérios: `trecho` — o motor não cobre; `trecho` — o motor não cobre; `trecho` — o motor não cobre.

### 2.2 O Plano de Manejo Vegetal pode ter caráter apenas conceitual, sem detalhamento operacional ou quantitativo?

**Escopo:** Vedação de plano apenas conceitual.

**Resposta oficial — pergunta 2.2:**

> Ressalta-se que o entendimento apresentado não está integralmente correto. O Plano de Manejo Vegetal não deve limitar-se a uma abordagem apenas conceitual. Embora o documento deva estabelecer diretrizes institucionais, responsabilidades e mecanismos de coordenação com os entes públicos competentes, ele também deve contemplar elementos operacionais e de planejamento que indiquem as ações que as empresas pretendam realizar quanto à execução das atividades de manejo vegetal, delimitando, sempre que possível, com o maior nível de detalhamento, os locais ou áreas prioritárias onde serão realizadas as intervenções. Adicionalmente, o plano deve apresentar critérios de priorização das áreas de intervenção, diretrizes para o planejamento das ações preventivas e corretivas, bem como procedimentos voltados ao acompanhamento e à avaliação da execução das atividades de manejo vegetal ao longo do período de vigência do plano. Dessa forma, o documento deve funcionar como instrumento de planejamento e orientação das ações da distribuidora, enquanto o Relatório Anual de Gestão do Manejo Vegetal se destina a consolidar e apresentar os resultados, dados analíticos e informações quantitativas decorrentes da execução das atividades previstas.

**Resposta do Athenix:**

- **item 103** (`obrigacoes`): “103. As distribuidoras devem disponibilizar a versão mais atualizada de seu plano de manejo vegetal em seu sítio eletrônico na Internet e nos postos de atendimento presencial, de forma acessível ao público, com uso de linguagem clara e adequada, conforme prazo constante do Módulo 6.”

  Prazo exportado: Vencido desde 28/01/2026 (293 dias); data: `2026-01-28`.

- **item 94** (`obrigacoes`): “94. As distribuidoras devem estabelecer um plano de manejo vegetal na sua área de atuação, que contemple a vegetação que interfira em suas redes de distribuição, em coordenação com o Poder Público Municipal e em articulação com os órgãos competentes do Poder Público Estadual e Distrital, e com vistas a garantir a segurança da rede de distribuição, a qualidade, eficiência e a continuidade do fornecimento de energia elétrica.”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

**Veredito: o motor não cobre.** A granularidade operacional esclarecida pelo FAQ não tem uma resposta expressa no plano.

Critérios: `trecho` — o motor não cobre.

### 2.3 O Plano de Manejo Vegetal precisa ser aprovado formalmente pelos municípios?

**Escopo:** Ausência de exigência de aprovação formal por cada município.

**Resposta oficial — pergunta 2.3:**

> A regulamentação não exige aprovação formal do Plano de Manejo Vegetal por cada município. O plano é um instrumento de planejamento da distribuidora, elaborado em coordenação com o Poder Público (item 94) e operacionalizado, quando necessário, por meio de convênios, acordos de cooperação ou outros instrumentos formais (item 95) e demais autorizações locais. Caso haja entraves por parte do ente público, a distribuidora deve manter atuação diligente e tempestiva, registrando tratativas e solicitações e buscando instrumentos formais de coordenação, sem prejuízo das suas obrigações de continuidade (item 98.1) e da autonomia para medidas urgentes em emergência (item 96).

**Resposta do Athenix:**

- **item 94** (`obrigacoes`): “94. As distribuidoras devem estabelecer um plano de manejo vegetal na sua área de atuação, que contemple a vegetação que interfira em suas redes de distribuição, em coordenação com o Poder Público Municipal e em articulação com os órgãos competentes do Poder Público Estadual e Distrital, e com vistas a garantir a segurança da rede de distribuição, a qualidade, eficiência e a continuidade do fornecimento de energia elétrica.”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

- **item 95** (`obrigacoes`): “95. As distribuidoras deverão celebrar convênios, acordos de cooperação ou outros instrumentos formais com os entes públicos municipais, distritais e estaduais, com vistas à definição de protocolos de atuação coordenada para o manejo da vegetação que interfira na segurança e continuidade do serviço público de distribuição de energia elétrica, devendo prever, de forma clara, as responsabilidades de cada parte quanto à inspeção, poda preventiva, remoção e substituição de árvores, respeitando as competências legais e ambientais de cada ente federativo, bem como os procedimentos técnicos e operacionais necessários à execução das ações.”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

**Veredito: o motor não cobre.** Ausência da palavra aprovação na extração não prova que ela seja dispensada; o motor não oferece essa conclusão.

Critérios: `aprovacao_municipal_obrigatoria` — o motor não cobre.

### 2.4 Convênios ou autorizações estaduais substituem a necessidade de pactuação com municípios? Associações municipais atendem à exigência regulatória?

**Escopo:** Convênio estadual não substitui pactuação municipal quando esta for aplicável.

**Resposta oficial — pergunta 2.4:**

> O item 95 prevê instrumentos formais com entes municipais, distritais e estaduais. Um convênio ou autorização estadual pode atender à parcela de coordenação com o Estado, mas não substitui, em regra, a necessidade de pactuação com municípios quando a competência municipal for aplicável, a exemplo da arborização urbana. Instrumentos como consórcios públicos intermunicipais (Lei nº 11.107/2005) ou entidades que detenham delegação formal dos municípios podem ser aceitos como forma de pactuação coletiva; já associações sem delegação de competência pública, em princípio, não substituem o instrumento pactuado com o ente público.

**Resposta do Athenix:**

- **item 95** (`obrigacoes`): “95. As distribuidoras deverão celebrar convênios, acordos de cooperação ou outros instrumentos formais com os entes públicos municipais, distritais e estaduais, com vistas à definição de protocolos de atuação coordenada para o manejo da vegetação que interfira na segurança e continuidade do serviço público de distribuição de energia elétrica, devendo prever, de forma clara, as responsabilidades de cada parte quanto à inspeção, poda preventiva, remoção e substituição de árvores, respeitando as competências legais e ambientais de cada ente federativo, bem como os procedimentos técnicos e operacionais necessários à execução das ações.”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

**Veredito: o motor não cobre.** A lista de entes no item 95 não resolve a substituição de competências esclarecida no FAQ.

Critérios: `trecho` — o motor não cobre.

### 2.5 Autorizações genéricas emitidas pelo município são suficientes para cumprimento da obrigação de celebração de convênios?

**Escopo:** Requisitos de responsabilidades e procedimentos do instrumento formal.

**Resposta oficial — pergunta 2.5:**

> Em geral, não. O item 95 exige que o instrumento formal preveja, de forma clara, as responsabilidades de cada parte quanto à inspeção, poda preventiva, remoção e substituição de árvores, além de procedimentos técnicos e operacionais. Uma autorização genérica que não trate das responsabilidades tende a ser insuficiente para cumprir integralmente o requisito regulatório.

**Resposta do Athenix:**

- **item 95** (`obrigacoes`): “95. As distribuidoras deverão celebrar convênios, acordos de cooperação ou outros instrumentos formais com os entes públicos municipais, distritais e estaduais, com vistas à definição de protocolos de atuação coordenada para o manejo da vegetação que interfira na segurança e continuidade do serviço público de distribuição de energia elétrica, devendo prever, de forma clara, as responsabilidades de cada parte quanto à inspeção, poda preventiva, remoção e substituição de árvores, respeitando as competências legais e ambientais de cada ente federativo, bem como os procedimentos técnicos e operacionais necessários à execução das ações.”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

**Veredito: igual.** Confere os requisitos expressos; não avalia a suficiência de uma autorização real.

Critérios: `trecho` — igual; `trecho` — igual; `trecho` — igual.

### 2.6 Como fica a responsabilidade da distribuidora quando não há avanço nas negociações com o Poder Público ou quando há demora injustificada?

**Escopo:** Manutenção das obrigações, registros por cinco anos e atuação emergencial.

**Resposta oficial — pergunta 2.6:**

> A ausência de avanço injustificado na pactuação não exime a distribuidora de suas obrigações de continuidade e segurança (item 98.1). Nesses casos, a distribuidora deve: (i) manter registros das solicitações e tratativas por 5 anos (item 104); (ii) adotar medidas preventivas e corretivas dentro das competências e autorizações aplicáveis; e (iii) em situações de emergência, atuar de forma coordenada, com autonomia para medidas urgentes para rápida recomposição do serviço (item 96), inclusive buscando apoio técnico e operacional do ente competente, bem como documentando as razões e impedimentos enfrentados.

**Resposta do Athenix:**

- **item 104** (`obrigacoes`): “104. As distribuidoras devem manter registro detalhado durante o período de 05 anos de todas as solicitações relacionadas ao serviço de manejo da vegetação que ofereça risco à segurança das redes elétricas e à continuidade do fornecimento de energia elétrica, incluídas tanto as solicitações realizadas pelo Poder Público Municipal quanto aquelas registradas pelas próprias distribuidoras e enviadas ao Poder Público Municipal, devendo o compartilhamento de informações estar em conformidade com as disposições da Lei Geral de Proteção de Dados (LGPD).”

  Prazo exportado: Vencido desde 28/04/2026 (203 dias); data: `2026-04-28`.

- **item 96** (`obrigacoes`): “96. As distribuidoras devem garantir a rápida remoção de árvores ou galhos caídos sobre a rede, atuando de forma coordenada com o Poder Público Estadual, Distrital ou Municipal, dispondo de autonomia necessária para adotar medidas urgentes que assegurem a rápida recuperação do serviço em situações de emergência.”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

- **item 98** (`sem_dever_identificado`): “98. As distribuidoras são responsáveis pela realização de ações preventivas, devendo atuar junto ao Poder Público Estadual, Distrital e Municipal e manter os registros das solicitações conforme dispõe o item 104, e corretivas, visando garantir a segurança da rede de distribuição, a qualidade, a eficiência e a continuidade do fornecimento de energia elétrica, por meio do manejo adequado da vegetação, sempre seguindo às legislações pertinentes. 98.1. A notificação da distribuidora ao Poder Público Municipal não a exime de suas obrigações quanto à qualidade, eficiência e continuidade na prestação do serviço de distribuição de energia elétrica, devendo manter atuação diligente e tempestiva. Diretrizes para o manejo vegetal”

**Veredito: o motor não cobre.** O item 98/98.1 está em sem dever identificado, não na contagem de deveres; o plano cobre registros e emergência, mas não a resposta inteira.

Critérios: `dever contado em item 98` — o motor não cobre; `trecho` — igual; `trecho` — igual.

### 3.1 Como deve ser interpretado o comando regulatório “2 meses após a publicação da norma” para fins de aplicação retroativa do DISE?

**Escopo:** Data inicial dos efeitos retroativos do DISE.

**Resposta oficial — pergunta 3.1:**

> Considerando a publicação da norma em 30/10/2025, o marco de 2 meses ocorre em 30/12/2025, de modo que os efeitos retroativos passam a incidir a partir de 31/12/2025. Contudo, como a apuração dos indicadores de continuidade no âmbito do PRODIST é realizada em base mensal, embora haja incidência a partir de 31/12/2025, a primeira apuração completa se dá no mês de janeiro de 2026, razão pela qual não se considera o dia isolado de 31/12/2025 como um período autônomo de apuração.

**Resposta do Athenix:**

- **Art. 13, inciso VI** (`obrigacoes`): “VI - Até 180 (cento e oitenta) dias mês para iniciar as apurações do Duração da Interrupção Individual ocorrida em Situação de Emergência por Unidade Consumidora ou por Ponto de Conexão – DISE e observar as disposições da Seção 8.2 do Módulo 8 do PRODIST com o corresponde pagamento de compensações por transgressão desse indicador, com efeitos retroativos a 2 meses após a publicação da norma;”

  Prazo exportado: Vencido desde 28/04/2026 (203 dias) · esclarecido (FAQ da ANEEL); data: `2026-04-28`.

**Veredito: o motor não cobre.** O plano conserva a expressão dois meses, mas não calcula nem distingue a incidência diária e a primeira apuração completa.

Critérios: `retroatividade.inicio` — o motor não cobre.

### 3.2 Qual é o prazo para início das apurações do indicador DISE?

**Escopo:** Data final para início das apurações do DISE.

**Resposta oficial — pergunta 3.2:**

> O prazo é de até 180 dias contados da data de publicação da norma. No caso da publicação em 30/10/2025, o prazo final para início das apurações é 28/04/2026.

**Resposta do Athenix:**

- **Art. 13, inciso VI** (`obrigacoes`): “VI - Até 180 (cento e oitenta) dias mês para iniciar as apurações do Duração da Interrupção Individual ocorrida em Situação de Emergência por Unidade Consumidora ou por Ponto de Conexão – DISE e observar as disposições da Seção 8.2 do Módulo 8 do PRODIST com o corresponde pagamento de compensações por transgressão desse indicador, com efeitos retroativos a 2 meses após a publicação da norma;”

  Prazo exportado: Vencido desde 28/04/2026 (203 dias) · esclarecido (FAQ da ANEEL); data: `2026-04-28`.

**Veredito: igual.** O prazo já foi esclarecido pelo próprio FAQ e confirmado pelo fundador; não é validação independente.

Critérios: `prazo.data` — igual.

### 3.3 Quais meses devem ser considerados na apuração do DISE em razão do efeito retroativo?

**Escopo:** Início dos eventos considerados na apuração retroativa do DISE.

**Resposta oficial — pergunta 3.3:**

> Devem ser considerados os eventos ocorridos a partir de 1º/1/2026.

**Resposta do Athenix:**

- **Art. 13, inciso VI** (`obrigacoes`): “VI - Até 180 (cento e oitenta) dias mês para iniciar as apurações do Duração da Interrupção Individual ocorrida em Situação de Emergência por Unidade Consumidora ou por Ponto de Conexão – DISE e observar as disposições da Seção 8.2 do Módulo 8 do PRODIST com o corresponde pagamento de compensações por transgressão desse indicador, com efeitos retroativos a 2 meses após a publicação da norma;”

  Prazo exportado: Vencido desde 28/04/2026 (203 dias) · esclarecido (FAQ da ANEEL); data: `2026-04-28`.

**Veredito: o motor não cobre.** O prazo de implantação de abril não responde ao início do período retroativo.

Critérios: `apuracao.eventos_desde` — o motor não cobre.

### 3.4 Como devem ser realizadas as compensações financeiras relativas às violações do DISE nesse período inicial?

**Escopo:** Último mês para crédito das compensações iniciais.

**Resposta oficial — pergunta 3.4:**

> As compensações devem observar os procedimentos e prazos estabelecidos no Módulo 8 do PRODIST, sendo calculadas com base nas apurações dos meses abrangidos pelo efeito retroativo. Uma vez iniciadas as apurações dentro do prazo regulamentar (até 28/04/2026), as distribuidoras devem proceder ao pagamento das compensações conforme dispõe o item 219 da Seção 8.2 do Módulo 8 do PRODIST. Tendo em vista que os meses de janeiro, fevereiro, março e abril se encontram no período de vigência da norma, as compensações apuradas relativas a esses meses devem ser creditadas na fatura apresentada em até 2 meses após o período de apuração do mês de abril. Assim, a fatura apresentada no mês de junho é a última na qual podem ser efetuadas as compensações de janeiro a abril.

**Resposta do Athenix:**

- **Art. 13, inciso VI** (`obrigacoes`): “VI - Até 180 (cento e oitenta) dias mês para iniciar as apurações do Duração da Interrupção Individual ocorrida em Situação de Emergência por Unidade Consumidora ou por Ponto de Conexão – DISE e observar as disposições da Seção 8.2 do Módulo 8 do PRODIST com o corresponde pagamento de compensações por transgressão desse indicador, com efeitos retroativos a 2 meses após a publicação da norma;”

  Prazo exportado: Vencido desde 28/04/2026 (203 dias) · esclarecido (FAQ da ANEEL); data: `2026-04-28`.

**Veredito: o motor não cobre.** O plano não calcula a janela de crédito na fatura, distinta do prazo de implantação.

Critérios: `compensacao.ultimo_mes` — o motor não cobre.

### 4.3 Informações detalhadas sobre infraestrutura de apoio e localização de recursos devem constar na versão pública do Plano de Contingência?

**Escopo:** Publicação sem contatos dos responsáveis e com infraestrutura/localização dos recursos.

**Resposta oficial — pergunta 4.3:**

> A obrigação de disponibilização pública do Plano de Contingência (item 147) prevê sua publicação sem a identificação e os contatos dos responsáveis. Contudo, essa previsão não afasta a necessidade de que o plano apresente os elementos mínimos requeridos para possibilitar a adequada compreensão e avaliação de sua implementação. Nesse sentido, considerando que a alínea d) Infraestrutura de Apoio estabelece a necessidade de indicação do inventário, especificação e localização de equipamentos disponíveis e sobressalentes, bem como dos veículos operacionais, tais informações devem constar no Plano de Contingência. A indicação da localização desses recursos é relevante para permitir a verificação da aderência entre o planejamento previamente estabelecido e a atuação da distribuidora em situações de contingência, possibilitando avaliar a capacidade de mobilização e de resposta da empresa diante de eventos que afetem o sistema elétrico.

**Resposta do Athenix:**

- **item 147** (`obrigacoes`): “147. As distribuidoras devem disponibilizar a versão mais atualizada, sem a identificação e contato dos seus responsáveis pelo seu plano de contingência, em seu sítio eletrônico na Internet e nos postos de atendimento presencial, de forma acessível ao público com uso de linguagem clara e adequada.”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

**Veredito: o motor não cobre.** O plano cobre a retirada dos contatos, mas não demonstra o conteúdo de infraestrutura exigido pela resposta completa.

Critérios: `trecho` — igual; `trecho` — o motor não cobre.

### 4.4 Quais são o gatilho, o prazo e o canal para envio de alertas meteorológicos à ANEEL no contexto do Plano de Contingência?

**Escopo:** Envio de alertas depende de procedimento da ANEEL; manutenção de evidências internas até sua publicação.

**Resposta oficial — pergunta 4.4:**

> O envio de alertas meteorológicos à ANEEL (Tabela 25 do Módulo 6) tem como gatilho os alertas que justifiquem o acionamento do Plano de Contingência, em qualquer nível. O prazo e o canal devem seguir o Plano de Comunicação e o procedimento a ser estabelecido pela ANEEL (item 114), que serão publicados oportunamente. Até a publicação desse procedimento, a distribuidora deve manter registro e evidências internas do acionamento e dos alertas correlatos, para apresentação à fiscalização quando demandado.

**Resposta do Athenix:**

- **Art. 14** (`obrigacoes`): “Art. 14. As distribuidoras devem implantar processo de comunicação e acompanhamento da evolução dos eventos climáticos severos de que trata o item 114 do Anexo IV da Resolução Normativa nº 956, de 7 de dezembro de 2021, em até 30 (trinta) dias, contados da publicação das instruções pela ANEEL.”

  Prazo exportado: Prazo conta de um evento ainda sem data · esclarecido (FAQ da ANEEL); data: `None`.

- **item 114** (`sem_dever_identificado`): “114. A ANEEL estabelecerá procedimento para comunicação e acompanhamento das situações de crise enfrentadas pelas distribuidoras. Diretrizes de Comunicação”

**Veredito: o motor não cobre.** O motor cobre o prazo dependente de evento, mas não extrai o dever provisório de evidências que o FAQ acrescenta.

Critérios: `prazo.data` — igual; `trecho` — o motor não cobre.

### 5.1 A comunicação deve ser feita a todos os consumidores afetados ou apenas àqueles que registraram reclamação?

**Escopo:** Comunicação automática aos consumidores afetados.

**Resposta oficial — pergunta 5.1:**

> Deve ser feita aos consumidores afetados pela interrupção, independentemente de terem ou não registrado reclamação. O item 105 estabelece comunicação após o reconhecimento da ocorrência (com prazos), e o item 110 determina o envio automático aos consumidores afetados.

**Resposta do Athenix:**

- **item 105** (`obrigacoes`): “105. As distribuidoras devem comunicar aos consumidores, por meio dos canais disponíveis, a provável causa da interrupção, a área afetada e o tempo previsto para a normalização do fornecimento em até 15 (quinze) minutos após o conhecimento da causa da interrupção. Independentemente do momento em que a causa for identificada, a comunicação contendo essas informações deve ser realizada em até 1 (uma) hora após o reconhecimento da ocorrência da interrupção no fornecimento de energia elétrica.”

  Prazo exportado: Vencido desde 28/04/2026 (203 dias) · por evento: até 15 min após o conhecimento da causa; até 1 h após o reconhecimento da ocorrência; data: `2026-04-28`.

- **item 110** (`obrigacoes`): “110. A comunicação de que trata o item 105 deve ser realizada, obrigatoriamente, por meio de SMS e aplicativos de mensagens, com envio de mensagens automáticas aos consumidores afetados.”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

**Veredito: igual.** Compara destinatários e envio automático; não simula uma interrupção concreta.

Critérios: `trecho` — igual.

### 5.2 A comunicação é obrigatória também em casos de reclamação individual ou apenas em eventos coletivos?

**Escopo:** Comunicação até uma hora do reconhecimento, independentemente da identificação da causa.

**Resposta oficial — pergunta 5.2:**

> A obrigação é vinculada à ocorrência de interrupção que afete o consumidor (individual ou coletiva). Não se restringe a eventos coletivos nem à existência de reclamação individual. Assim, uma vez reconhecida a interrupção e identificadas sua causa, a área afetada e o tempo previsto, ou, independentemente do momento em que a causa for identificada, se transcorrida 1 (uma) hora após o reconhecimento da ocorrência da interrupção, a comunicação deve alcançar os consumidores afetados.

**Resposta do Athenix:**

- **item 105** (`obrigacoes`): “105. As distribuidoras devem comunicar aos consumidores, por meio dos canais disponíveis, a provável causa da interrupção, a área afetada e o tempo previsto para a normalização do fornecimento em até 15 (quinze) minutos após o conhecimento da causa da interrupção. Independentemente do momento em que a causa for identificada, a comunicação contendo essas informações deve ser realizada em até 1 (uma) hora após o reconhecimento da ocorrência da interrupção no fornecimento de energia elétrica.”

  Prazo exportado: Vencido desde 28/04/2026 (203 dias) · por evento: até 15 min após o conhecimento da causa; até 1 h após o reconhecimento da ocorrência; data: `2026-04-28`.

**Veredito: igual.** Afirmação objetiva de prazo e marco; não mede entrega efetiva das mensagens.

Critérios: `trecho` — igual; `prazo.texto` — igual.

### 5.3 Notificações via “push” podem substituir o envio por SMS e aplicativos de mensagens?

**Escopo:** Canais mínimos obrigatórios: SMS e aplicativos, com envio automático.

**Resposta oficial — pergunta 5.3:**

> Notificações via “push” podem ser usadas como canal complementar, mas não substituem o requisito mínimo do item 110: a comunicação do item 105 deve ser realizada obrigatoriamente por SMS e aplicativos de mensagens (com envio automático). Portanto, é possível adotar push para reforço do aviso, desde que as comunicações obrigatórias por SMS e app de mensagens sejam realizadas dentro dos prazos.

**Resposta do Athenix:**

- **item 110** (`obrigacoes`): “110. A comunicação de que trata o item 105 deve ser realizada, obrigatoriamente, por meio de SMS e aplicativos de mensagens, com envio de mensagens automáticas aos consumidores afetados.”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

**Veredito: igual.** Confere o requisito mínimo; a possibilidade de push complementar não é convertida em nova obrigação.

Critérios: `trecho` — igual; `trecho` — igual.

### 5.4 Haverá algum indicador específico para verificar a efetividade do Plano de Comunicação?

**Escopo:** Ausência de novo indicador específico de efetividade.

**Resposta oficial — pergunta 5.4:**

> A REN nº 1.137/2025 não institui, neste momento, um indicador específico de efetividade do Plano de Comunicação. A verificação tende a ocorrer por fiscalização do cumprimento das obrigações (prazos, canais mínimos, atualização a cada 30 min, completude das informações) e pela análise de evidências de execução do plano.

**Resposta do Athenix:**

- **item 108** (`obrigacoes`): “108. As distribuidoras devem disponibilizar a versão mais atualizada de seu plano de comunicação em seu sítio eletrônico na Internet e nos postos de atendimento presencial, de forma acessível ao público, com uso de linguagem clara e adequada. Informações Detalhadas”

  Prazo exportado: Vencido desde 28/01/2026 (293 dias); data: `2026-01-28`.

**Veredito: o motor não cobre.** Não encontrar indicador no plano não comprova sua inexistência na norma inteira.

Critérios: `indicador_especifico_instituido` — o motor não cobre.

### 5.5 Qual deve ser a linguagem e a abrangência das informações no Plano de Comunicação?

**Escopo:** Linguagem clara, acessível e adequada na disponibilização do plano.

**Resposta oficial — pergunta 5.5:**

> O Plano de Comunicação deve empregar linguagem clara, acessível e adequada ao público-alvo. Sendo desejável que descreva: (i) canais e responsabilidades; (ii) fluxos desde o reconhecimento da ocorrência até a normalização; (iii) periodicidade de atualização; (iv) gatilhos e conteúdos mínimos de mensagens; (v) fluxos de acionamento e comunicação de alertas meteorológicos e eventos críticos; e (vi) integração com o Plano de Contingência e com a comunicação ao Poder Público e mídia.

**Resposta do Athenix:**

- **item 108** (`obrigacoes`): “108. As distribuidoras devem disponibilizar a versão mais atualizada de seu plano de comunicação em seu sítio eletrônico na Internet e nos postos de atendimento presencial, de forma acessível ao público, com uso de linguagem clara e adequada. Informações Detalhadas”

  Prazo exportado: Vencido desde 28/01/2026 (293 dias); data: `2026-01-28`.

**Veredito: igual.** Só a exigência objetiva de linguagem; os seis elementos apresentados como desejáveis não são tratados como dever.

Critérios: `trecho` — igual; `trecho` — igual.

### 5.6 Para fins da REN nº 1.137/2025, o termo “sítio eletrônico” refere-se exclusivamente ao site público da distribuidora ou pode incluir ambientes com acesso restrito (ex.: agência virtual)?

**Escopo:** Acesso público e irrestrito, sem autenticação prévia.

**Resposta oficial — pergunta 5.6:**

> Entende-se que tais informações devem ser disponibilizadas em ambiente de acesso público e irrestrito, de modo a permitir a consulta por qualquer interessado, inclusive consumidores e Poder Público, sem a necessidade de autenticação prévia.

**Resposta do Athenix:**

- **item 103** (`obrigacoes`): “103. As distribuidoras devem disponibilizar a versão mais atualizada de seu plano de manejo vegetal em seu sítio eletrônico na Internet e nos postos de atendimento presencial, de forma acessível ao público, com uso de linguagem clara e adequada, conforme prazo constante do Módulo 6.”

  Prazo exportado: Vencido desde 28/01/2026 (293 dias); data: `2026-01-28`.

- **item 108** (`obrigacoes`): “108. As distribuidoras devem disponibilizar a versão mais atualizada de seu plano de comunicação em seu sítio eletrônico na Internet e nos postos de atendimento presencial, de forma acessível ao público, com uso de linguagem clara e adequada. Informações Detalhadas”

  Prazo exportado: Vencido desde 28/01/2026 (293 dias); data: `2026-01-28`.

- **item 147** (`obrigacoes`): “147. As distribuidoras devem disponibilizar a versão mais atualizada, sem a identificação e contato dos seus responsáveis pelo seu plano de contingência, em seu sítio eletrônico na Internet e nos postos de atendimento presencial, de forma acessível ao público com uso de linguagem clara e adequada.”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

**Veredito: o motor não cobre.** Acesso público no trecho normativo não basta para afirmar que o motor verifica autenticação.

Critérios: `trecho` — o motor não cobre.

### 6.1 Como deve ser apresentada a comprovação do atingimento do limite operacional crítico para fins de cessão emergencial?

**Escopo:** Prazo para envio do relatório circunstanciado à fiscalização.

**Resposta oficial — pergunta 6.1:**

> A demonstração do limite operacional crítico (item 131) deve integrar o conjunto documental do relatório circunstanciado do evento e/ou do relatório enviado à fiscalização em até 60 dias após o fim da situação emergencial (item 132), podendo constar como seção específica ou anexo, desde que clara, objetiva e auditável. Um relatório nos moldes do relatório do ISE pode ser utilizado como base, desde que contenha evidências do atingimento do limite (recursos disponíveis em comparação com os mobilizados, critérios objetivos do acionamento do Plano de Contingência em seus diversos patamares até atingir o nível mais crítico, impacto na capacidade operacional e justificativa da necessidade de cessão).

**Resposta do Athenix:**

- **item 132, alínea a** (`obrigacoes`): “a) valor global da contratação com detalhamento dos recursos envolvidos, segregados por tipo de gasto;”

  Prazo exportado: Prazo conta de um evento ainda sem data; data: `None`.

  Caput herdado: “132. Ao acionar o mecanismo de Cessão Emergencial de recursos, a distribuidora cessionária deve enviar às áreas de fiscalização da ANEEL, em até 60 dias após o fim da situação emergencial, relatório contendo discriminação das despesas ou custos incorridos a serem reembolsados à cedente, contendo as ”

**Veredito: igual.** Confere apenas o prazo e seu marco no caput herdado; não avalia o conteúdo probatório do limite operacional crítico.

Critérios: `contexto` — igual.

### 6.2 Qual a periodicidade dos treinamentos das equipes a serem cedidas e de quem é a responsabilidade por essa capacitação?

**Escopo:** Periodicidade dos treinamentos não fixada na norma, a definir no acordo.

**Resposta oficial — pergunta 6.2:**

> O item 135 estabelece que as equipes cedidas devem possuir capacitação e experiência compatíveis, mas não fixa periodicidade de treinamento. A periodicidade e as responsabilidades devem ser definidas no Acordo de Cessão Emergencial Prévio (item 133), que deve prever procedimentos de integração e treinamentos necessários (item 133, g).

**Resposta do Athenix:**

- **item 133, alínea g** (`obrigacoes`): “g) Procedimentos claros para a integração de equipes externas, com definição de treinamentos, capacitações e preparação prévia adequada para garantir que todos os envolvidos estejam alinhados com as práticas de segurança e operação da distribuidora requisitante.”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

- **item 135** (`obrigacoes`): “135. As equipes cedidas devem possuir capacitação e experiência compatíveis com as atividades a serem desenvolvidas na distribuidora cedente.”

  Prazo exportado: Em vigor desde 30/10/2025 (sem período de adequação); data: `None`.

**Veredito: o motor não cobre.** O plano extrai capacitação e acordo, mas não responde expressamente à ausência de periodicidade; ausência de prazo não é comprovação.

Critérios: `periodicidade_treinamento_fixada` — o motor não cobre; `trecho` — igual.

## Perguntas fora do placar

- **1.3 O escopo do art. 371-A abrange temas técnicos, comerciais ou ambos?** Escopo temático e natureza das demandas: interpretação qualitativa, sem um prazo, data ou comando objetivo delimitado para este avaliador.

- **1.5 Qual é a finalidade do canal telefônico exclusivo previsto na regulamentação?** Finalidade e uso operacional do canal: exige avaliação qualitativa de processos, não a conferência de um prazo ou requisito fechado.

- **1.6 Quais critérios caracterizam um evento crítico que deve ser comunicado ao Poder Público?** Caracterização de evento crítico e risco relevante depende da avaliação de um evento concreto pela distribuidora.

- **3.5 Ajustes retroativos no XML de compensações por DISE impactam a avaliação da governança regulatória?** Impacto de ajustes XML na avaliação de governança não é prazo, vigência, sujeito ou obrigatoriedade coberto por esta avaliação.

- **4.1 O que deve ser entendido como “demandas extraordinárias” no contexto do atendimento ao consumidor durante contingências?** Definição exemplificativa de demandas extraordinárias: depende de caracterização operacional do evento.

- **4.2 Qual o nível de detalhamento esperado para a matriz de riscos do Plano de Contingência?** Nível suficiente de granularidade de uma matriz de riscos: exige revisão de conteúdo de um plano real.

## Decisões pendentes

Revisar as anotações do gabarito com especialista e decidir quais lacunas justificam trabalho no motor. O relatório só mede e explica; não aplica esclarecimentos novos, não muda o site nem transforma ausência de extração em ausência de obrigação.
