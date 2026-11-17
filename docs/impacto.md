# Módulo de impacto e prioridade

Registro de 11/11/2026, atualizado em 17/11/2026. Estima a consequência financeira de cada obrigação e sugere uma ordem de
ação. **Estimativa com base nas premissas listadas, não constitui parecer jurídico.**

## Como usar

1. Envie a norma (ex.: `tests/norma_poc/ren20251137.pdf`) em **Documentos** e execute a extração
   por regras.
2. Abra **Impacto** (`/impacto`). Preencha o perfil (segmento, base de cálculo, agravantes,
   atenuante, valor base) e clique em **Recalcular**. Em cada obrigação dá para escolher o grupo
   de multa (premissa).
3. **Exportar relatório** gera o HTML com as mesmas premissas (`/impacto/relatorio?…&download=1`
   baixa um arquivo autocontido; para PDF, imprima pelo navegador). A primeira página é o resumo
   para decisão; o detalhe começa na página 2.

Exemplos reproduzíveis: `python scripts/gerar_exemplo_relatorio.py` grava
`docs/exemplos/relatorio_impacto_rn1137.html` (RN 1.137, transmissora, base não informada) e
`python scripts/capturar_impacto.py` (requer `requirements-qa.txt`) grava as capturas de
`docs/telas/` e o PDF `docs/exemplos/relatorio_impacto_rn1137.pdf` em navegador real.

Funciona sem IA e sem chave de API.

## De onde vem cada número

| Origem | O que fornece |
| --- | --- |
| `athenix/data/penalidades_ren846.json` | 30 parâmetros da REN 846 e o teto legal da Lei 9.427/1996 (limites dos grupos, base, agravantes, atenuantes), 113 infrações tipificadas (arts. 9º–13) com grupo, as duas leituras do Art. 11, XXIII (D1), as alterações da régua e os alertas da fonte. Cada item tem dispositivo, trecho literal, estado da âncora e hash do PDF de origem. |
| `tests/fontes_impacto/l9427cons.htm` | Lei 9.427/1996, texto compilado do planalto.gov.br (sha256 `ff948e3442ed…`, obtido em 17/11/2026). Fonte do teto legal por infração (Art. 3, X da Lei 9.427/1996, redação dada pela Lei nº 15.269, de 2025): “X - fixar as multas administrativas a serem impostas aos concessionários, permissionários e autorizados de instalações e serviços de energia elétrica,…”. Versionado no repositório (ato oficial). |
| Usuário | Segmento, base de cálculo (ROL ou RAP), número de reincidências, TN não atendidos e antecedentes, soma das multas anteriores, atenuante esperada, valor base como % do teto e grupo de cada obrigação. |

O arquivo de parâmetros é gerado por `scripts/extrair_parametros.py` (pipeline do Athenix sobre os
PDFs de `tests/fontes_impacto/` ou, na falta, de `.local/fontes_impacto/`). Percentuais são lidos do trecho citado, nunca digitados. Um
parâmetro só entra no cálculo com âncora **verificada** (segunda leitura do PDF) e redação **não
revogada** (sem risco no PDF compilado); caso contrário a faixa fica "não estimável".

**Origem dos parâmetros: a confirmar com a fonte oficial da ANEEL.** Os parâmetros atuais foram extraídos de três PDFs
compilados por terceiro (Leis.org), baixados manualmente pelo fundador. Os termos de uso do site
proíbem reproduzir ou armazenar esses textos em outros sites sem autorização escrita (cláusula 9),
então os PDFs ficam só em `.local/fontes_impacto/` (ignorado pelo git). O Leis.org é usado apenas
para consulta manual: o Athenix não baixa nem coleta nada dele. Quando as versões oficiais da ANEEL
forem colocadas em `tests/fontes_impacto/`, os parâmetros são refeitos e comparados com os atuais. Sem
os PDFs, o app e os testes usam o arquivo de parâmetros versionado; só a regeneração e os testes sobre
o PDF real são pulados, com mensagem.

## Regras de cálculo

- **Consequência** (regra determinística, com o motivo na tela): dever → *penalidade/multa*
  (Art. 5º); verbo de implantação → *custo de adequação*; Parcela Variável, RAP ou Fator X →
  *perda de receita* (também disponibilidade de instalações, equipamentos, ativos, linhas ou funções
  de transmissão, quando o perfil é transmissão ou a obrigação nomeia a transmissora); informar, registrar, publicar → *risco de fiscalização*; faculdade → *sem
  consequência financeira identificável*.
- **Enquadramento:** grupo escolhido pelo usuário; senão, infração da REN 846 cujos instrumentos
  nomeados ("Plano de Contingência", "Poder Público" + "Situações de Emergência"…) aparecem todos no
  texto da obrigação; senão, todos os grupos (I a V). A ANEEL decide o enquadramento.
- **Faixa** (% da base do Art. 21; em R$ só se a base for informada — nunca estimada):
  - mínimo **0** (advertência do Art. 6º ou atenuante do Art. 24; metodologia do valor base fora do
    repositório);
  - máximo = teto do grupo, sem atenuante, em **dois cenários** (D5): "com teto do grupo" (resultado
    após agravantes limitado ao teto do grupo) e "sem teto do grupo após agravantes, limitado ao teto
    legal" (teto × (1 + agravantes), até o teto legal);
  - provável só com valor base informado e grupo único: valor base + agravantes (Art. 23, somados)
    − atenuante (Art. 24), nos dois cenários;
  - **teto legal** (Lei 9.427/1996, Art. 3º, X, lido do parâmetro verificado): limite final nos dois
    cenários. Aplicado sobre a mesma base informada (dúvida D6: a lei fala em faturamento). Sem o
    parâmetro verificado, nada é limitado e a premissa diz isso.
- **Prazo:** vencido → exposição atual; aberto → dias restantes; recorrente ou sem data → dito.
- **Prioridade:** vencidas, depois as que vencem em até 90 dias, depois as demais e por fim as sem
  data; dentro de cada faixa, maior exposição (provável, se houver; senão máxima), no cenário sem
  teto do grupo (limitado ao teto legal). A frase de decisão diz o peso e o prazo.
- **Abertura do relatório e da tela:** de 3 a 5 obrigações nessa ordem, primeiro as que nomeiam o
  segmento do perfil (sem segmento: transmissoras, quando houver); as de sujeito genérico só
  completam até 3 e vêm marcadas. A mesma regra repetida (Anexo e bloco "(NR)") aparece uma vez.
  Logo abaixo, o quadro da Parcela Variável: principal impacto para transmissoras, não estimável,
  com as obrigações que tocam disponibilidade de instalações.
- **Confiança:** *alto* só com base, grupo escolhido pelo usuário e valor base informados; *médio*
  com base informada e uma premissa faltando, ou grupo só por coincidência de termos; *baixo* nos
  demais casos (inclui o perfil vazio e obrigação sem citação verificada).
- **Aplicabilidade:** obrigação cujo sujeito é de outro segmento fica fora da prioridade, com o motivo.

## Alertas na tela e no relatório

- Norma analisada que altera a REN 846 (ex.: RN 1.137, Art. 9º), com link ao dispositivo.
- D1: Art. 11, XXIII com duas redações (RN 1.137, vigente desde 30/10/2025; REN 1.148, desde
  01/01/2027). Dúvida para especialista.
- D3 (regra geral): a mesma norma citada no documento com dia, mês ou ano diferentes, com os trechos
  e links (na RN 1.137: RN 948 "de 16 de novembro de 2021" × "de 21 de novembro").
- D5: os dois cenários de teto, ambos limitados ao teto legal.
- D6: teto legal sobre o faturamento × base da REN 846 (ROL). Dúvida para especialista.
- Inconsistência da fonte: Art. 45-I, § 4º ("25% (cinco por cento)").
- Aviso de origem dos parâmetros (a confirmar com a ANEEL; cópia secundária) visível no topo.

## Não estimável

Metodologia do valor base; Parcela Variável de transmissoras (norma ausente; quadro próprio na
primeira página); Fator X da distribuidora (anexos da REN 1.148 ausentes); REN 1.162/2026 e Despacho
1.293/2026 (ausentes); custo de adequação (dado interno da empresa).

## Limites conhecidos

- Enquadramento por coincidência de termos é indício, não decisão: instrumentos citados com outra
  grafia ou plural em "-ões" não casam (`shortcut` em `impacto._singular`).
- Classificação por verbos e termos: pode marcar custo de adequação ou fiscalização onde não há.
- Prazos herdam as limitações do `temporal` (datas provisórias, calculadas da publicação).
- Antecedentes sem soma informada usam a faixa máxima (5% cada), dito na premissa.
- Teto legal aplicado sobre a mesma base informada (ROL); se o faturamento for maior que a ROL, o
  teto em reais fica subestimado (D6). A vigência da redação dada pela Lei 15.269/2025 não foi
  conferida: infrações anteriores a ela podem seguir o limite anterior (2%, riscado no texto).
- "Nomeia o segmento" é busca por termos (transmissor, distribuidor…) no sujeito e na ação.
