# Valor provável a partir dos dados abertos (análise, 18/11/2026)

**Resultado de análise. Não foi levado à demo nem ao cálculo do produto**; depende de revisão do
fundador. Reproduzir: `python scripts/analisar_autos.py` (testes: `tests/test_analisar_autos.py`).
Fontes (baixadas em 17/11/2026, em `.local/dados_aneel/`): CSV de Auto de Infração (sha256
`453451f4…`, 1.635 autos, lavrados de 06/2018 a 11/2026), dicionário v1.0 (03/05/2022) e CSV SIGEC
de multa de fiscalização (`4724c458…`, usado só para saber se o título foi pago).

## Regras aplicadas
- **Valor final** do caso: `VlrMultaAposDiretoria`; senão `VlrMultaAposJuizo`; senão `VlrPenalidade`
  (o campo fica registrado). Valores têm vírgula decimal e, em 95 linhas, vêm como `,99` (sem inteiro).
- **Grupo**: o enquadramento diz, por exemplo, "Multa do Grupo IV (REN 846/2019) Art. 12", sem o
  inciso. O artigo (9º a 13) é mapeado ao grupo pelo catálogo (`penalidades_ren846.json`) e o grupo
  declarado precisa coincidir. O que não mapeia fica "não classificado", sem palpite.
- **Conta** caso pago (SIGEC com data de pagamento), encerrado (termo de encerramento) ou decidido
  pela Diretoria; **fora** os em andamento e os sem valor em reais.
- **Estrato** (grupo × segmento) só tem valor provável com ≥ 10 casos de ≥ 5 empresas (CNPJ
  distintos); senão "amostra insuficiente (n = X)".
- **Segmento** só por evidência explícita: código de empreendimento de geração (EOL, UFV, UHE…) ou
  natureza da fiscalização que cita transmissão ou distribuição. O resto: "segmento não identificado".

## Quantos casos foram classificados
| Etapa | Autos |
|---|---|
| No CSV | 1.635 |
| Não classificados: mais de um grupo no mesmo auto | 738 |
| Não classificados: regime anterior (sem REN 846 no enquadramento) | 253 |
| Não classificados: sem multa por grupo (advertência ou vazio) | 106 |
| Não classificados: art. 45 da REN 846, fora dos arts. 9º a 13 | 28 |
| **Classificados em um grupo da REN 846** | **510** |
| Fora: em andamento | 156 |
| **Contam** (pagos 219, encerrados 127, decididos pela Diretoria 8) | **354** |

Estados dos 510 classificados: pago 219, encerrado 127, decidido pela Diretoria 8, em andamento 156.
Dos 354 que contam, 28 foram **reformados** (valor final diferente do inicial) e 3 têm valor final
zero (nenhum nos estratos estimáveis). Origem do valor: `VlrPenalidade` 226, `VlrMultaAposDiretoria`
122, `VlrMultaAposJuizo` 6.

## Resultados por grupo e segmento (valores em R$)
| Estrato | Casos | Empresas | Resultado |
|---|---|---|---|
| III × geração | 122 | 110 | mediana 39.943; Q1–Q3 29.128–49.654; mín. 7.273; máx. 4.568.946 |
| III × segmento não identificado | 33 | 30 | mediana 34.569; Q1–Q3 25.082–123.260; mín. 1.041; máx. 12.790.089 |
| IV × geração | 88 | 75 | mediana 97.530 |
| IV × segmento não identificado | 89 | 45 | mediana 79.674 |
| I × geração / não identificado | 1 / 5 | 1 / 5 | amostra insuficiente |
| II × geração | 7 | 7 | amostra insuficiente (n = 7) |
| III × transmissão | 1 | 1 | amostra insuficiente (n = 1) |
| IV × distribuição | 1 | 1 | amostra insuficiente (n = 1) |
| IV × transmissão | 4 | 4 | amostra insuficiente (n = 4) |
| V × segmento não identificado | 3 | 3 | amostra insuficiente (n = 3) |

## O que isso significa para o produto
- **Não há valor provável para distribuidoras nem transmissoras**: a base é quase toda de geração
  (eólicas e fotovoltaicas). Distribuição tem 1 caso e transmissão 5. O foco do produto (distribuição)
  fica "amostra insuficiente".
- Os estratos estimáveis são de geração e de segmento não identificado, com multas de dezenas de
  milhares de reais, muito abaixo das multas de distribuidoras e transmissoras vistas nos votos (na
  casa de dezenas de milhões). **Não usar essas medianas para distribuidoras.**
- 45% dos autos listam mais de um grupo no enquadramento; o CSV não separa o valor por infração, e o
  valor não é dividido. Ficam de fora.
- Valor pago pode ter desconto de pagamento; o estrato usa o valor da decisão, não o arrecadado.
- Viés de seleção: só entram autos publicados e já decididos, pagos ou encerrados.

## Conferência com as decisões (votos da ANEEL, 3.4)
- **AI 0018/2023-SFT (transmissora, Proc. 48500.006992/2022-98):** o CSV tem penalidade inicial
  R$ 8.370.790,66 e valor após o Juízo R$ 8.163.820,53, **sem** valor após a Diretoria. O voto da
  Diretoria nega provimento e reforma para **R$ 8.738.737,50**. O CSV está **desatualizado/divergente**
  (diferença de R$ 574.917). Pelas regras, o valor final do caso no CSV seria o do Juízo.
- **AI 002/2022-SFE (distribuidora, Proc. 48500.004507/2021-61):** o voto mantém R$ 32.949.775,22, mas
  o auto **não consta** no CSV desta data.
- Nenhum dos 3 atos do DOU do acervo decide multa (3.4): não há conferência por esse lado.
