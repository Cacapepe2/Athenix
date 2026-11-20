# Histórico de multas por dispositivo (distribuição)

Análise descritiva, sem nome de empresa e **fora da demo e do cálculo**. Fonte: CSV de autos de
infração, dicionário de dados e SIGEC (`.local/dados_aneel/`, não versionados). Regras de
`scripts/analisar_autos.py` (unidade = auto; valor final; crédito quitado/parcelado/encerrado/decidido).

## Há campo com o dispositivo infringido (artigo e inciso)?
- Autos no CSV: 1.635; de distribuição (evidência explícita): 109.
- **Nenhuma coluna traz artigo + inciso.** `DscEnquadramentoAI` traz só o grupo e o artigo.
- Autos de distribuição com inciso identificado: **0** de 109.

## Sem inciso: o que o campo permite (artigo da REN 846 citado)
Autos de distribuição por artigo citado em `DscEnquadramentoAI`: art. 9: 11, art. 10: 6, art. 11: 28, art. 12: 28, art. 13: 8.
- Art. 12 (Grupo IV; inclui os incisos XXVI, XXVII e XXVIII, sem distingui-los): 28 autos; contam 10; mediana = 22496978.59; máximo = 48654893.31.
- Desses, lavrados desde o início da vigência da RN 1.137: **5** (2025-12-05, 2026-08-28, 2026-08-28, 2026-09-11, 2026-10-01). O campo não permite saber se algum se baseia no XXVII ou no XXVIII: **não dá para confirmar nem negar**; a data da lavratura não prova a data da infração.

## Referência por Grupo IV (distribuição)
Autos de distribuição que contam e têm infração de Grupo IV (podem ter outros grupos; o valor é do auto inteiro):
- n = **10**; mediana = 22496978.59; máximo = 48654893.31.

## Limites
- O valor é do auto inteiro; o CSV não separa valor por infração.
- Distribuição pode estar subcontada (segmento só por evidência explícita).
- XXVII e XXVIII do art. 12 só existem a partir da RN 1.137/2025; autos com esses incisos dependem de fiscalização posterior à vigência.
