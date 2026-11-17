# Revisão por especialista

Material gerado em 17/11/2026 por `scripts/gerar_revisao_especialista.py`, a partir dos
dados do Athenix (trechos literais das normas, gabarito e parâmetros de multa). **Situação: ainda
não revisado por especialista** (`revisado_por_humano: false`). A planilha
`docs/revisao_especialista.csv` tem as mesmas perguntas, com colunas para a resposta
(Sim / Não / Não sei) e um comentário.

**Como responder:** leia o trecho da norma e responda à pergunta. Se a resposta for "não" ou
"depende", o comentário é o mais importante: diga o que está certo e por quê. Não é preciso
conhecer o sistema.

## Parte 1. Decisões de método (D1, D5, D6 e priorização)

### D1. Duas redações para o inciso XXIII do Art. 11 da REN 846 (infração do Grupo III)

O mesmo inciso aparece com textos diferentes em duas normas:

- **RN 1.137/2025**, vigente desde 30/10/2025: “XXIII - deixar de prestar informações decorrentes de interrupções no fornecimento de energia elétrica aos consumidores ou usuários, nos termos da regulação vigente. […]”
- **REN 1.148/2026**, vigente desde 01/01/2027: “XXIII - deixar de responder ou responder de forma não conclusiva as demandas relacionadas ao Sistema de Gestão de Ouvidoria da ANEEL-SGO/ANEEL, ou outro que vier a substituí-lo, no prazo específico definido pela ANEEL. ..”

**Pergunta:** Hoje vale a redação da RN 1.137 e, a partir de 01/01/2027, a da REN 1.148? Ou as duas condutas continuam como infração?

**Opções:** (a) uma substitui a outra na data de vigência; (b) as duas valem (uma delas foi ou será renumerada); (c) outra leitura.

**O que muda no cálculo:** qual conduta entra como infração do Grupo III. Hoje o Athenix mostra as duas e não escolhe.

### D5. Teto do grupo depois dos agravantes

A REN 846 define um teto por grupo (Art. 8º; Grupo IV: 1% da base) e agravantes que aumentam a multa (Art. 23; ex.: 40% por reincidência).
A norma não diz se, depois dos agravantes, a multa pode passar do teto do grupo. Nos dois casos, o teto legal (3% do faturamento, Lei 9.427/1996) continua valendo.

**Pergunta:** Depois de somar os agravantes, a multa continua limitada ao teto do grupo?

**Opções:** (a) sim, o teto do grupo vale depois dos agravantes; (b) não, só o teto legal limita.

**O que muda no cálculo:** Grupo IV com 1 reincidência fica em 1% da base em (a) e 1,4% em (b). Hoje o Athenix mostra os dois cenários.

### D6. Teto legal: faturamento bruto ou Receita Operacional Líquida (ROL)?

A Lei 9.427/1996 (Art. 3º, X) limita a multa a 3% do **faturamento**; a REN 846 (Art. 21) calcula a multa sobre a **ROL**.

**Pergunta:** O teto legal por infração deve ser calculado sobre o faturamento bruto ou sobre a ROL?

**Opções:** (a) faturamento bruto (o teto em reais fica maior); (b) ROL; (c) outra base.

**O que muda no cálculo:** com (a), o Athenix usa o faturamento bruto informado no perfil; sem ele, aplica 3% sobre a ROL e avisa que o teto pode estar subestimado.

### Priorização: o que fazer primeiro

Regra atual: Ordem: exposição provável (o valor provável, se informado; senão, o ponto médio da faixa) multiplicada pelo peso do prazo (vencida 1; vence em até 90 dias 0,8; depois 0,5; sem data 0,3); obrigações com enquadramento desconhecido ficam fora da fila, em "Verificar enquadramento".

Pesos do prazo: vencida 1,0; vence em até 90 dias 0,8; vence depois 0,5; sem data 0,3. Esses pesos são uma escolha do produto, não vêm de norma.

**Pergunta 1:** Ordenar por exposição provável × peso do prazo ajuda a decidir o que fazer primeiro? Os pesos fazem sentido?

**Opções:** (a) sim; (b) ajustar os pesos (quais?); (c) ordenar só pelo prazo; (d) ordenar só pela exposição.

**Pergunta 2:** Obrigação sem enquadramento identificado deve ficar fora da fila até alguém confirmar o grupo de multa?

**O que muda:** sem essa regra, obrigações sem grupo valiam o máximo de todos os grupos e passavam à frente das que têm grupo identificado.

## Parte 2. Os 20 casos do gabarito

Cada caso é um trecho real de norma e a leitura que o Athenix considera correta. Responda sim ou não a cada pergunta.

### G01. RN ANEEL 1.137/2025, Art. 17

> As transmissoras têm 90 (noventa) dias, a partir da publicação, para implementar as disposições dos artigos 6º e 7º desta Resolução Normativa.

- **Leitura do Athenix:** É uma obrigação de transmissoras. **Pergunta:** Este trecho cria uma obrigação que vale para transmissoras? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Prazo de 90 dias contados da publicação da norma, vencendo em 28/01/2026. **Pergunta:** O prazo é de 90 dias contados da publicação da norma, vencendo em 28/01/2026? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Texto da própria norma. **Pergunta:** Este trecho é texto da própria norma (e não nova redação de outra norma)? ( ) Sim ( ) Não ( ) Não sei

### G02. RN ANEEL 1.137/2025, Art. 13, I

> Até 90 (noventa) dias para revisar e publicar os planos de manejo vegetal, de comunicação e de contingência

- **Leitura do Athenix:** É uma obrigação de distribuidoras. **Pergunta:** Este trecho cria uma obrigação que vale para distribuidoras? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Prazo de 90 dias contados da publicação da norma, vencendo em 28/01/2026. **Pergunta:** O prazo é de 90 dias contados da publicação da norma, vencendo em 28/01/2026? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Texto da própria norma. **Pergunta:** Este trecho é texto da própria norma (e não nova redação de outra norma)? ( ) Sim ( ) Não ( ) Não sei

### G03. RN ANEEL 1.137/2025, Art. 15

> As distribuidoras devem disponibilizar a API de que trata item 113 do Anexo IV

- **Leitura do Athenix:** É uma obrigação de distribuidoras. **Pergunta:** Este trecho cria uma obrigação que vale para distribuidoras? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Prazo de 60 dias contados de um evento ainda sem data (sem data final até o evento ocorrer). **Pergunta:** O prazo é de 60 dias contados de um evento ainda sem data (sem data final até o evento ocorrer)? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Texto da própria norma. **Pergunta:** Este trecho é texto da própria norma (e não nova redação de outra norma)? ( ) Sim ( ) Não ( ) Não sei

### G04. RN ANEEL 1.137/2025, Art. 21

> Esta Resolução entra em vigor na data de sua publicação.

- **Leitura do Athenix:** Vigência a partir de 30/10/2025. **Pergunta:** A norma entra em vigor em 30/10/2025? ( ) Sim ( ) Não ( ) Não sei

### G05. RN ANEEL 1.137/2025, Art. 19

> Revoga-se o inciso VIII do art. 621 da Resolução Normativa nº 1.000 de 2021.

- **Leitura do Athenix:** Texto da própria norma. **Pergunta:** Este trecho é texto da própria norma (e não nova redação de outra norma)? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Revoga dispositivo de outra norma. **Pergunta:** Este trecho revoga dispositivos (deixa de valer o texto citado)? ( ) Sim ( ) Não ( ) Não sei

### G06. RN ANEEL 1.137/2025, Anexo IV da RN 956, item 110 (redação dada pelo Art. 3º)

> A comunicação de que trata o item 105 deve ser realizada, obrigatoriamente, por meio de SMS e aplicativos de mensagens

- **Leitura do Athenix:** É uma obrigação. **Pergunta:** Este trecho cria uma obrigação? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Nova redação de outra norma: REN ANEEL 956/2021. **Pergunta:** Este trecho é nova redação da REN ANEEL 956/2021, e não texto da própria norma? ( ) Sim ( ) Não ( ) Não sei

### G07. RN ANEEL 1.137/2025, Anexo IV da RN 956, item 122

> Situação de Crise: Evento que afeta significativamente a capacidade operacional da distribuidora

- **Leitura do Athenix:** Não cria obrigação. **Pergunta:** Este trecho NÃO cria obrigação para a empresa? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Nova redação de outra norma: REN ANEEL 956/2021. **Pergunta:** Este trecho é nova redação da REN ANEEL 956/2021, e não texto da própria norma? ( ) Sim ( ) Não ( ) Não sei

### G08. RN ANEEL 1.137/2025, Art. 10

> A Agência poderá instituir Comitê de Crise quando da ocorrência de eventos climáticos severos

- **Leitura do Athenix:** É uma faculdade (pode), não um dever. **Pergunta:** Isto é uma permissão para Agência, e não uma obrigação? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Texto da própria norma. **Pergunta:** Este trecho é texto da própria norma (e não nova redação de outra norma)? ( ) Sim ( ) Não ( ) Não sei

### G09. RN ANEEL 1.137/2025, Art. 16

> os indicadores estabelecidos nos incisos V e VI do caput do art. 4º; do Decreto 12.068, de 20 de julho de 2024

- **Leitura do Athenix:** Prazo de 30 dias contados de um evento ainda sem data (sem data final até o evento ocorrer). **Pergunta:** O prazo é de 30 dias contados de um evento ainda sem data (sem data final até o evento ocorrer)? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Remete a Art. 4º, V e VI do Decreto 12.068/2024. **Pergunta:** Este trecho remete a Art. 4º, V e VI do Decreto 12.068/2024? ( ) Sim ( ) Não ( ) Não sei

### G10. REH ANEEL 3.348/2024, Art. 1º

> Estabelecer, com vigência a partir de 1º de julho de 2024, as Receitas Anuais Permitidas pela disponibilização das instalações sob responsabilidade

- **Leitura do Athenix:** Não cria obrigação. **Pergunta:** Este trecho NÃO cria obrigação para a empresa? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Vigência a partir de 01/07/2024. **Pergunta:** A norma entra em vigor em 01/07/2024? ( ) Sim ( ) Não ( ) Não sei

### G11. REH ANEEL 3.348/2024, Art. 3º, § 1º

> As Concessionárias alcançadas por esta Resolução deverão informar à ANEEL e ao ONS, em janeiro e, sempre que houver alteração, o seu regime de apuração do PIS/Pasep e da Cofins

- **Leitura do Athenix:** É uma obrigação de Concessionárias. **Pergunta:** Este trecho cria uma obrigação que vale para Concessionárias? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Prazo periódico: anual, em janeiro, e a cada alteração. **Pergunta:** O prazo é periódico (anual, em janeiro, e a cada alteração)? ( ) Sim ( ) Não ( ) Não sei

### G12. REH ANEEL 3.348/2024, Art. 7º

> Os agentes deverão aditar o Contrato de Prestação de Serviços de Transmissão – CPST no ONS

- **Leitura do Athenix:** É uma obrigação de agentes. **Pergunta:** Este trecho cria uma obrigação que vale para agentes? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Não tem prazo com data. **Pergunta:** O texto não fixa uma data para cumprir esta obrigação? ( ) Sim ( ) Não ( ) Não sei

### G13. REH ANEEL 3.348/2024, Art. 3º, caput

> O Operador Nacional do Sistema Elétrico – ONS deverá incluir nos Avisos de Crédito

- **Leitura do Athenix:** É uma obrigação de Operador Nacional do Sistema Elétrico. **Pergunta:** Este trecho cria uma obrigação que vale para Operador Nacional do Sistema Elétrico? ( ) Sim ( ) Não ( ) Não sei

### G14. REH ANEEL 3.348/2024, Art. 8º

> Esta Resolução entra em vigor na data de sua publicação.

- **Leitura do Athenix:** A norma não fixa data de vigência neste trecho. **Pergunta:** Este trecho não fixa uma data de vigência? ( ) Sim ( ) Não ( ) Não sei

### G15. Decreto 12.068/2024, Art. 9º, § 1º

> será disponibilizada pela Aneel à concessionária, que deverá assiná-lo no prazo de noventa dias, contado da convocação

- **Leitura do Athenix:** É uma obrigação de concessionária. **Pergunta:** Este trecho cria uma obrigação que vale para concessionária? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Prazo de 90 dias contados de um evento ainda sem data (sem data final até o evento ocorrer). **Pergunta:** O prazo é de 90 dias contados de um evento ainda sem data (sem data final até o evento ocorrer)? ( ) Sim ( ) Não ( ) Não sei

### G16. Decreto 12.068/2024, Art. 10, § 1º

> deverá ser aprovada e divulgada pela Aneel no prazo de cento e vinte dias, contado da publicação deste Decreto

- **Leitura do Athenix:** É uma obrigação. **Pergunta:** Este trecho cria uma obrigação? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Prazo de 120 dias contados da publicação da norma, vencendo em 19/10/2024. **Pergunta:** O prazo é de 120 dias contados da publicação da norma, vencendo em 19/10/2024? ( ) Sim ( ) Não ( ) Não sei

### G17. Decreto 12.068/2024, Art. 4º, § 1º

> As distribuidoras deverão informar e manter, por até cinco anos, em seu sítio eletrônico, os indicadores estabelecidos nos incisos V, VI e VII do caput

- **Leitura do Athenix:** É uma obrigação de distribuidoras. **Pergunta:** Este trecho cria uma obrigação que vale para distribuidoras? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Texto da própria norma. **Pergunta:** Este trecho é texto da própria norma (e não nova redação de outra norma)? ( ) Sim ( ) Não ( ) Não sei

### G18. Decreto 12.068/2024, Art. 22

> Fica revogado o art. 1º do Decreto nº 11.835, de 20 de dezembro de 2023

- **Leitura do Athenix:** Texto da própria norma. **Pergunta:** Este trecho é texto da própria norma (e não nova redação de outra norma)? ( ) Sim ( ) Não ( ) Não sei
- **Leitura do Athenix:** Revoga dispositivo de outra norma. **Pergunta:** Este trecho revoga dispositivos (deixa de valer o texto citado)? ( ) Sim ( ) Não ( ) Não sei

### G19. Decreto 12.068/2024, Art. 23

> Este Decreto entra em vigor na data de sua publicação.

- **Leitura do Athenix:** Vigência a partir de 21/06/2024. **Pergunta:** A norma entra em vigor em 21/06/2024? ( ) Sim ( ) Não ( ) Não sei

### G20. Decreto 12.068/2024, Art. 19 (nova redação do art. 22 do Decreto 62.724/1968)

> regiões de elevada complexidade ao combate às perdas não técnicas

- **Leitura do Athenix:** Nova redação de outra norma: Decreto 62.724/1968. **Pergunta:** Este trecho é nova redação do Decreto 62.724/1968, e não texto da própria norma? ( ) Sim ( ) Não ( ) Não sei

## Parte 3. Enquadramento das infrações usadas no relatório

O Athenix liga uma obrigação a uma infração da REN 846 quando os instrumentos citados na infração aparecem no texto da obrigação. Para cada infração abaixo, diga se concorda com o grupo e com a ligação.

### Art. 12, XXVI da REN 846: Grupo IV

> XXVI - a ausência, inadequação ou descumprimento do Plano de Contingência, nos termos da regulação vigente;

Obrigações da RN 1.137 ligadas a esta infração (35), por exemplo:

- “k) Estágio da operação (conforme etapas definidas no plano de contingência).”
- “140. O plano de contingência deve ser elaborado de forma a garantir a continuidade do fornecimento de energia elétrica, minimizar os impactos das contingências e responder a eventos críticos de forma eficaz, sempre asseg…”
- “141. O plano de contingência deve conter os nomes e telefones de contato dos responsáveis. Princípios Norteadores”

**Pergunta:** Descumprir as obrigações abaixo se enquadra no Art. 12, XXVI da REN 846 (Grupo IV)? ( ) Sim ( ) Não, o grupo certo é ____ ( ) Não sei

### Art. 12, XXVII da REN 846: Grupo IV

> XXVII - a ausência, inadequação ou descumprimento do Plano de Manejo Vegetal, nos termos da regulação vigente; e

Obrigações da RN 1.137 ligadas a esta infração (4), por exemplo:

- “I - Até 90 (noventa) dias para revisar e publicar os planos de manejo vegetal, de comunicação e de contingência de que tratam os itens 103, 108 e 148 do Anexo IV da Resolução Normativa nº 956, de 7 de dezembro de 2021, c…”
- “94. As distribuidoras devem estabelecer um plano de manejo vegetal na sua área de atuação, que contemple a vegetação que interfira em suas redes de distribuição, em coordenação com o Poder Público Municipal e em articula…”
- “103. As distribuidoras devem disponibilizar a versão mais atualizada de seu plano de manejo vegetal em seu sítio eletrônico na Internet e nos postos de atendimento presencial, de forma acessível ao público, com uso de li…”

**Pergunta:** Descumprir as obrigações abaixo se enquadra no Art. 12, XXVII da REN 846 (Grupo IV)? ( ) Sim ( ) Não, o grupo certo é ____ ( ) Não sei

### Art. 12, XXVIII da REN 846: Grupo IV

> XXVIII - comunicar-se de forma ineficiente com o Poder Público em Situações de Emergência, nos termos da regulação vigente.

Obrigações da RN 1.137 ligadas a esta infração (3), por exemplo:

- “96. As distribuidoras devem garantir a rápida remoção de árvores ou galhos caídos sobre a rede, atuando de forma coordenada com o Poder Público Estadual, Distrital ou Municipal, dispondo de autonomia necessária para adot…”
- “115. A comunicação deve ser clara e transparente com o intuito de gerar confiança no relacionamento entre as distribuidoras e o Poder Público, essencial para a efetividade das ações em conjunto. Para esse fim, a distribu…”
- “118. As distribuidoras devem garantir que os canais de comunicação oficiais estejam acessíveis e operacionais em situações de emergência em comum acordo com o Poder Público.”

**Pergunta:** Descumprir as obrigações abaixo se enquadra no Art. 12, XXVIII da REN 846 (Grupo IV)? ( ) Sim ( ) Não, o grupo certo é ____ ( ) Não sei

---

Estimativa com base nas premissas listadas, não constitui parecer jurídico. Depois da revisão, as respostas entram no gabarito e nas decisões (`docs/parametros_impacto.md`), e `revisado_por_humano` passa a `true` só para o que foi revisado.
