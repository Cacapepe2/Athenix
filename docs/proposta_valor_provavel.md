# Proposta: referência histórica para o valor provável

Status: **proposta para aprovação; não implementada**. Pesquisa em 17/11/2026.
O produto continua sem referência histórica no campo provável. O ponto médio usado na ordenação não é uma previsão de multa.

## Fontes públicas encontradas

| Fonte primária | Informação disponível | Limite verificado |
|---|---|---|
| [Auto de Infração — ANEEL](https://dadosabertos.aneel.gov.br/dataset/auto-de-infracao) | Catálogo de autuações, com cobertura declarada desde maio de 2018 e atualização mensal. | Cadastro de autuação não comprova decisão definitiva nem pagamento. |
| [Recurso CSV Auto de Infração](https://dadosabertos.aneel.gov.br/dataset/auto-de-infracao/resource/f221158a-93a3-423f-b794-4312b6985a24) | Schema publicado: VlrPenalidade, VlrMultaAposJuizo, VlrMultaAposDiretoria, datas e atos de decisão, encerramento e DscEnquadramentoAI. Metadados indexados indicam atualização em 02/11/2026. | A obtenção do CSV deu timeout. Não há base de cálculo/ROL no schema consultado. Os valores agregados por auto não são necessariamente valores por infração. |
| [Dicionário de Auto de Infração](https://dadosabertos.aneel.gov.br/dataset/4d690c9d-8158-4b04-ae44-7d3de8616271/resource/3e8feb4d-5d33-4b1f-8c19-a1e89f127c12/download/dm-auto-de-infracao.pdf) | Excerto indexado descreve DscEnquadramentoAI como texto livre dos dispositivos infringidos/enquadramento. | PDF integral não obtido; não tratar o campo como grupo estruturado. |
| [SIGEC — ANEEL](https://dadosabertos.aneel.gov.br/dataset/sigec-sistema-de-gestao-de-creditos) | Catálogo informa atualização em 16/11/2026 e frequência diária; útil para conciliar cobrança e pagamento. | Não substitui a decisão que fixou a multa. |
| [Dicionário SIGEC — Multa de Fiscalização](https://dadosabertos.aneel.gov.br/dataset/da3d8da5-bdc0-471a-b57e-09e49f557c9a/resource/dcd6f294-0ec7-4a81-b759-c2d4a81be7b0/download/dm-sigec-sistema-de-gestao-de-creditos-multa-de-fiscalizacao.pdf) | PDF integral acessível, versão 1.0 de 09/10/2023. Separa principal previsto (VlrPcpPrvArr), total previsto, total pago, situação, pagamento e Selic. | Não traz grupo nem base. Arrecadação pode incluir juros, descontos e parcelas. |
| [Voto — Despacho 3.244/2022](https://www2.aneel.gov.br/cedoc/adsp20223244_1.pdf) e [Voto — Despacho 2.090/2024](https://www2.aneel.gov.br/cedoc/adsp20242090_1.pdf) | Pistas de decisões com discussão de multa e base de cálculo. | HTTP 403 na leitura integral. Excertos de busca não foram usados como amostra estatística nem como percentuais de referência. |

**Amostra elegível efetivamente verificada: n = 0 infrações** com grupo, principal final e base correspondente comprovados. Catálogos, schemas e excertos não contam como observações. Não há mediana, média nem percentual típico a publicar hoje.

## Método proposto, sujeito à aprovação

1. Montar base por infração, com AI, processo, agente/CNPJ, segmento, dispositivo, grupo, regime normativo, datas, base usada e sua janela temporal, valor principal inicial, principal após recursos e estado processual. Guardar fonte, página, trecho, data de coleta e hash do arquivo.
2. Cruzar o cadastro de AI com decisões e exposições de motivos. Usar SIGEC para conciliar cobrança/pagamento. Não tomar o último campo preenchido automaticamente como decisão definitiva.
3. Admitir uma observação somente quando grupo, valor por infração e denominador forem verificáveis. Se um AI tem diversas infrações e apenas total agregado, excluí-lo do cálculo por grupo; não dividir seu total arbitrariamente.
4. Separar autuado, reformado em recurso, encerrado administrativamente e pago. O percentual de sanção usa o principal da decisão elegível; arrecadação é análise distinta. Advertências devem ser contadas separadamente, sem misturar automaticamente multa pecuniária e chance de advertência.
5. Normalizar: **percentual da base = 100 × principal da infração / base da infração**. Não substituir base ausente por ROL atual, RAP ou receita genérica da empresa. Separar bases e regimes; dados antigos não se tornam automaticamente referência do regime vigente.
6. Calcular mediana e intervalo interquartil por grupo, segmento e regime. Mostrar n de infrações, agentes distintos, período, corte, concentração por empresa, casos extremos e exclusões. Grupo sem amostra suficiente permanece não estimável.
7. Política de qualidade proposta: pelo menos 30 infrações verificadas e diversidade de agentes por estrato antes de publicar referência operacional. Esse limiar é uma decisão de produto a validar, não uma regra da ANEEL. Abaixo disso, apenas estudo exploratório, sem preencher o provável.
8. Após aprovação e revisão especializada, converter a mediana em reais com a base informada: **base × mediana percentual / 100**. Rótulo: “Referência histórica — não é previsão da sanção”, com n, período, dispersão e fontes. Não aplicar novamente agravantes que já estejam incorporados à mediana de multas finais.

## Como apresentar até lá

- Mínimo: advertência (sem multa).
- Provável: não estimável com os dados disponíveis; a premissa manual já existente permanece identificada como premissa do usuário.
- Máximo: teto do grupo/cenários e limite legal, com premissas rastreáveis.

A referência histórica não estima probabilidade de autuação e não autoriza somar multas de obrigações correlatas. Revisar com especialista também os vieses de seleção (apenas casos autuados, publicados e obtidos).

## Arquivos necessários do fundador

Sem contornar os bloqueios de acesso, solicitar:

- CSV de Auto de Infração e seu dicionário, baixados no portal acima.
- CSV SIGEC de multas e dicionário, se a análise de pagamento for desejada.
- PDFs das decisões/votos e exposições de motivos correspondentes, começando pelos dois despachos indicados.

Nenhum percentual histórico foi implementado ou presumido nesta proposta.
