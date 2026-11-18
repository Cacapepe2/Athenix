# Valor provável a partir dos dados abertos (análise revista, 18/11/2026)

**Resultado de análise. Não foi levado à demo nem ao cálculo do produto**; depende de revisão do
fundador. Reproduzir: `python scripts/analisar_autos.py` (testes: `tests/test_analisar_autos.py`).
Fontes (baixadas em 17/11/2026, em `.local/dados_aneel/`): CSV de Auto de Infração (sha256
`453451f4…`, 1.635 linhas, 06/2018 a 11/2026), dicionário v1.0 e CSV SIGEC de multa de fiscalização
(`4724c458…`, 15.568 linhas). Esta versão **substitui** a de 18/11 manhã, que concluía "sem amostra
para distribuição" com um método mais restrito (descartava o auto com mais de um grupo e exigia o
segmento pelo código/natureza apenas).

## a) Unidade de análise: penalidade ou auto?
**O CSV não permite separar penalidades.** Há uma linha por auto (1.624 números distintos em 1.635
linhas; os repetidos são de agências diferentes) e um único valor por auto (`VlrPenalidade`,
`VlrMultaAposJuizo`, `VlrMultaAposDiretoria`) para todas as infrações dele. O enquadramento
(`DscEnquadramentoAI`) lista os grupos e artigos, por exemplo "Multa do Grupo III (REN 846/2019) Art.
11 / Multa do Grupo V (REN 846/2019) Art. 13", sem valor por infração nem inciso. O SIGEC também não
separa: uma linha por título de cobrança, sem grupo. Dividir o valor entre as infrações seria
inventar dado, então a unidade é o **auto**, e o estrato é a **combinação de grupos** ("III",
"III+V"). O auto com mais de um grupo (738 de 1.635) **não é mais descartado**: é um estrato próprio
e a limitação fica explícita (o valor é do auto inteiro).

## b) SIGEC: o que é e o que acrescenta
Colunas: `Codcvnarr` (código do título), `AnmArrecadacao` (competência), `DatVencimentoTitulo`,
`DatIncidenciaMultaMora`, `DatPagamentoTitulo`, `QtdDiasEmAtraso`, `SigNomAgente` (sigla e razão
social), `NumCPFCNPJ`, `NomEmpreendimento`, `NumProcessoSIC`, `NumAutoInfracao`,
`DscSituacaoArrecadacao` (quitada, pendente, cancelada), `DscSituacaoCredito` (quitada, parcelamento,
suspenso com depósito judicial ou seguro garantia, multa convertida em advertência, CADIN/dívida
ativa, cancelada), `VlrPcpPrvArr` (principal previsto), `VlrTotPvrArr`, `VlrTotPagArr`,
`VlrTotDifPvrPagArr`, `VlrSelic`.
- Cobre 4.145 autos (inclui anteriores a 2018 e agências estaduais), mas **só 485 cruzam com o CSV de
  autos**. O cruzamento precisa de **número do auto + CNPJ**: o mesmo número existe em agências
  diferentes.
- **Acrescenta:** (1) situação do crédito, que o CSV de autos não tem: quitado, parcelado, suspenso
  por decisão judicial ou seguro, convertido em advertência, cancelado; (2) a razão social, que
  ajuda a identificar o segmento; (3) pagamento efetivo.
- **Não acrescenta valor confiável:** a soma de `VlrPcpPrvArr` por auto não reproduz o valor do auto
  (só 2 de 496 coincidem; os títulos vêm em duplicidade, por exemplo cancelado + reemitido). O SIGEC
  serve para situação e pagamento, não para o valor da multa. Também não traz grupo.
- Regra usada: crédito **quitado** (ou **parcelado**) conta; **suspenso** (judicial ou seguro),
  **convertido em advertência** e **cancelado** ficam fora; sem SIGEC valem o termo de
  encerramento e a decisão da Diretoria; sem nada, em andamento (fora).

## c) Como o segmento foi classificado, e 10 exemplos de distribuidoras
Evidência explícita, nesta ordem: (1) código CEG de empreendimento de geração (EOL, UFV, UHE…);
(2) natureza da fiscalização que cita transmissão ou distribuição; (3) nome do agente no CSV de
autos citando "distribuição/distribuidora" ou "transmissão/transmissora"; (4) o mesmo, pelo nome no
SIGEC (por CNPJ). Nome que cita os dois fica "não identificado". Resultado nos 1.635 autos:
geração 1.090, transmissão 130, **distribuição 109**, não identificado 306. A regra de nome só
enxerga quem escreve "Distribuição/Distribuidora" na razão social: distribuidora cujo nome não traz
a palavra (por exemplo, nomes só com a sigla da empresa) fica como "não identificado", então
**distribuição está subcontada**. Os 109 têm 50 razões sociais distintas, todas de distribuidoras de
energia (algumas são cooperativas de distribuição); não há falso positivo de outro setor na lista.

Dez exemplos (sem valores; agência, natureza, grupos do enquadramento, evidência, estado):
| Auto | Agência | Natureza | Grupos (REN 846) | Evidência | Estado |
|---|---|---|---|---|---|
| 0001/2019-AGEPAN-SFE | AGEPAN | Indicadores de Continuidade | não classificado (regime anterior) | nome | encerrado |
| 0001/2021-SFF | ANEEL | Apoio ao Processo Decisório… | não classificado | nome | quitado |
| 0001/2024-AGR-SFT | AGR | Técnica | I+III+IV | nome | em andamento |
| 0002/2019-ARSESP-SFE | ARSESP | Indicadores de Continuidade | não classificado | nome | decidido pela Diretoria |
| 0002/2025-AGERGS-SFT | AGERGS | Comercial | I+III | nome | encerrado |
| 0004/2019-AGR-SFE | AGR | Comercial | não classificado | nome | em andamento |
| 0006/2023-AGERGS-SFT | AGERGS | Técnica | IV | nome | decidido pela Diretoria |
| 0012/2021-SFF | ANEEL | Apoio ao Processo Decisório… | não classificado | nome | suspenso |
| 0019/2024-SFT | ANEEL | Técnica | III | nome | suspenso |
| 0026/2026-SFT | ANEEL | Comercial | I+II+III+IV | nome | quitado |

Dos 109 autos de distribuição, 55 têm grupo da REN 846; desses, 26 estão em andamento, 11
quitados, 8 suspensos, 5 encerrados e 5 decididos pela Diretoria. **Contam 21** (de 14 empresas).

## d) Agências estaduais conveniadas
**Sim, o conjunto inclui.** 342 dos 1.635 autos (21%) foram lavrados por agências estaduais
(AGERGS 89, ARPE 63, ARSEP 45, ARSESP 42, AGER-MT 32, ARCE 31, AGR 16, AGEPAN, ARPB, ARSAL, AGRESE,
AGEMS; o dicionário diz que o conjunto reúne ANEEL e agências conveniadas). Entre os que contam, 135
de 406 são estaduais. A comparação por origem está na tabela abaixo.

## Quantos casos foram classificados
| Etapa | Autos |
|---|---|
| No CSV | 1.635 |
| Não classificados: regime anterior (sem REN 846 no enquadramento) | 253 |
| Não classificados: sem multa por grupo (advertência ou vazio) | 106 |
| Não classificados: art. 45 da REN 846, fora dos arts. 9º a 13 | 28 |
| **Classificados em grupos da REN 846** (738 com mais de um grupo) | **1.248** |
| Fora: em andamento | 784 |
| Fora: crédito suspenso, cancelado ou outra situação no SIGEC | 58 |
| **Contam** (quitado, parcelado, encerrado, decidido pela Diretoria) | **406** (ANEEL 271; estaduais 135) |

## Resultados (valores em R$ do auto; limiar ≥ 10 casos de ≥ 5 empresas)
Por **grupos × segmento** (só os que passam o limiar):
| Estrato | Casos | Empresas | Mediana | Q1–Q3 |
|---|---|---|---|---|
| III × geração | 121 | 109 | 40.000 | 29.326–49.734 |
| III × segmento não identificado | 20 | 19 | 36.760 | 28.240–112.701 |
| IV × geração | 88 | 75 | 97.530 | 32.430–156.051 |
| IV × segmento não identificado | 61 | 21 | 49.587 | 49.587–178.217 |
| IV × transmissão | 24 | 22 | 258.304 | 109.474–483.346 |

Por **segmento, qualquer combinação de grupos** (valor do auto inteiro):
| Segmento | Casos | Empresas | Mediana | Máximo |
|---|---|---|---|---|
| **Distribuição** | **21** | **14** | **10.349.703** | **48.654.893** |
| Transmissão | 50 | 38 | 258.304 | 20.616.830 |
| Geração | 234 | 203 | 47.424 | 6.653.035 |
| Segmento não identificado | 101 | 48 | 56.529 | 48.277.709 |

Por origem × segmento (qualquer grupo): distribuição ANEEL 11 casos/11 empresas, mediana 6.386.919;
distribuição de agência estadual 10 casos/5 empresas, mediana 11.419.732; geração ANEEL 154 casos,
mediana 50.161; geração estadual 80, mediana 36.654; transmissão (só ANEEL) 50, mediana 258.304.

**Distribuição × grupo isolado continua "amostra insuficiente"**: o maior estrato (IV) tem 7 casos,
o seguinte (III), 6. Os 21 casos de distribuição se espalham em 9 combinações de grupos. Só a
distribuição **com qualquer grupo** passa o limiar, e por pouco (14 empresas; 10 e 11 casos por
origem). **Mudança em relação à versão anterior:** distribuição passa de "1 caso" para 21.

## O que isso significa
- A ordem de grandeza de distribuição (mediana ≈ R$ 10 milhões por auto) é cerca de 200 vezes a de
  geração, coerente com os votos vistos (dezenas de milhões). **Não use a mediana de geração ou de
  "segmento não identificado" para distribuidoras.**
- A mediana de distribuição é de **auto com um ou vários grupos**: não é valor por infração, não é
  por grupo e não separa agravantes. Serve no máximo como **ordem de grandeza descritiva**, com n=21
  e 14 empresas, e não como "valor provável" por obrigação. Decisão sobre uso na demo: do fundador.
- Subcontagem de distribuição (nome sem a palavra) e viés de seleção: só entram autos publicados e
  já decididos, quitados ou encerrados; os suspensos (judicial) e em andamento, que tendem a ser os
  maiores, ficam fora, então a mediana pode estar subestimada.

## e) Limitação: valor "após a Diretoria" ausente em caso já decidido
- Dos 207 autos com data de decisão da Diretoria, **12 não têm `VlrMultaAposDiretoria`**; entre os
  406 que contam, 4. O valor final cai no do Juízo ou no inicial.
- Pior: o CSV pode **não ter a decisão** da Diretoria. Dos 457 autos com recurso, só 207 têm
  decisão da Diretoria; 100 têm decisão do Juízo e nenhuma da Diretoria. **AI 0018/2023-SFT**
  (transmissora, Proc. 48500.006992/2022-98): o CSV tem recurso (10/07/2023), valor inicial
  R$ 8.370.790,66 e valor após o Juízo R$ 8.163.820,53, sem data nem valor da Diretoria; o voto da
  Diretoria nega provimento e fixa **R$ 8.738.737,50** (diferença de R$ 574.917). O auto também não
  tem título no SIGEC. **AI 002/2022-SFE** (distribuidora, Proc. 48500.004507/2021-61): o voto mantém
  R$ 32.949.775,22, mas o auto **não consta** no CSV.
- Efeito: o valor final do caso pode estar desatualizado; só os votos publicados (3.4) corrigem.

## Outras limitações
- Valor quitado pode ter desconto de pagamento; usa-se o valor da decisão, não o arrecadado.
- Grupo vem do enquadramento do auto, sem inciso; auto com vários grupos tem valor misto.
- 253 autos antigos (regime anterior) ficam de fora porque os percentuais do grupo eram outros.
- Nenhum dos 3 atos do DOU do acervo decide multa (3.4).
