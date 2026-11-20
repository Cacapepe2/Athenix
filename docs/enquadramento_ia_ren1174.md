# Sugestões de enquadramento por IA: REN 1.174/2026

Execução autorizada pelo fundador em 20/11/2026, para a página executiva. **Interpretação da IA ·
aguarda revisão humana**: as sugestões entram só no cenário preliminar, marcadas como "sugerido" (barra
hachurada); sem sugestão, a obrigação fica "a enquadrar" e sem valor (não se mostra teto da escala).

| Item | Valor |
|---|---|
| Norma | REN 1.174/2026 (`tests/fontes_impacto/dou/dou_ren20261174.html`, DOU de 04/11/2026) |
| Obrigações enviadas | 91 deveres da distribuidora, uma por chamada |
| Modelo | gpt-5-mini (Azure), raciocínio `medium` |
| Resultado | 91 chamadas, 0 falhas, **90 com sugestão**, 1 sem |
| Custo real (uso informado pelo provedor) | **US$ 0,5171**, com reserva de US$ 0,10 por uma 1ª tentativa interrompida por timeout (custo não registrado) |
| Estimativa antes de rodar | esperado US$ 0,41; máximo US$ 1,32 (teto da execução: US$ 2,00) |
| Preço usado | US$ 0,25 por milhão de entrada e US$ 2 por milhão de saída |
| Fonte e data do preço | tabela de preço do Azure OpenAI (<https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/>), 20/11/2026. **O fundador vai confirmar no portal.** |
| Critério | só a 1ª sugestão (a mais provável) de cada obrigação, com dispositivo da lista da REN 846 e justificativa não vazia; nada é confirmado |

Reproduzir (só com autorização e estimativa): `python scripts/sugerir_enquadramento.py --arquivo
tests/fontes_impacto/dou/dou_ren20261174.html`, que só estima; para chamar, `ATHENIX_AI_MODE=live`, preço
com fonte e data, `ATHENIX_RUN_BUDGET_USD` e `--confirmo-custo-usd` maior ou igual ao custo máximo. O script
grava o progresso a cada chamada (retoma sem repetir) e para ao atingir o teto. O cache do plano é
`athenix/data/ia_cache_dou_ren20261174.json` (só dispositivo, grupo e justificativa; sem resposta bruta).
