# Item 4 — comparação com o Módulo 4 oficial anterior

Retomada autorizada com os PDFs fornecidos pelo fundador em 22/11/2026. Estimativa anunciada: 75 minutos de implementação e validação local, fora das esperas dos merges/CI. O PR #52 permanece draft; não houve autorização para seu merge.

Fonte, origem, data e SHA-256 registrados em `tests/fontes_impacto/fontes.json`. A v2 tem 16 páginas e a v3, 30. Os arquivos originais são preservados; cópias públicas mantêm os mesmos bytes e hashes, com links para a página da citação.

**Escopo do plano:** 112 registros novos em relação ao Módulo 4 v2; zero alterados e zero já existentes entre esses registros. Os outros 35 ficam explicitamente sem fonte anterior. A comparação usa o bloco da RN que altera o Anexo IV, não apenas um número de item coincidente em outro módulo. São registros da lista existente, incluindo detalhamentos; não é uma nova contagem de infrações.

**Inventário do módulo completo:** 55 itens novos, um alterado (item 1, índice das seções) e 92 já existentes. O índice alterado não é contado como dever. O relatório reproduzível está em [`docs/pitch/comparacao_anexo_iv.md`](../../pitch/comparacao_anexo_iv.md), com todos os itens, páginas e texto anterior/atual do alterado.

**Conferência da v3 com a RN:** 92 dos 112 registros do plano conferem literalmente; 20 divergem. Há remissões diferentes (itens 110/112: item 103 na v3 e 105 na RN), além de mudanças de pontuação/concordância. Foram conferidas visualmente as páginas 7 da RN e 23 da v3. O plano mantém a fonte RN, os textos, os prazos, os enquadramentos e as contagens. Os detalhes mostram as duas redações com dispositivo, hash e link, sob aviso de revisão; nenhuma delas foi adotada silenciosamente em lugar da outra.

## Validação visual

Chrome com build local, fontes carregadas e contextos isolados, 1280×900 e 390×844. Conferidos resumo na executiva, item 103 novo, item 115 com divergência e Art. 13, VI sem fonte anterior. Sem erro JavaScript ou rolagem horizontal. As duas cópias públicas foram servidas e seus hashes conferidos.

| Caso | 1280 px | 390 px |
|---|---|---|
| Executiva | [resumo](item4-executiva-1280.png) | [resumo](item4-executiva-390.png) |
| Item 103, novo | [detalhe](item4-novo-1280.png) | [detalhe](item4-novo-390.png) |
| Item 115, divergência | [fontes](item4-divergencia-1280.png) | [fontes](item4-divergencia-390.png) |
| Art. 13, VI, sem fonte anterior | [detalhe](item4-sem-fonte-1280.png) | [detalhe](item4-sem-fonte-390.png) |

Testes reais cobrem novo/alterado/já existente, limites de seção/bloco, hash adulterado, fonte desconhecida, remissão divergente, não mutação do plano, relatório reproduzível e links das fontes. As verificações completas e o CI final são registrados no PR após incorporar a main com os quatro merges autorizados.

**Decisão:** revisar as divergências entre as fontes oficiais antes de adotar qualquer redação diferente. Sem fonte dos demais módulos, não se presume sua novidade histórica. Não houve teste em aparelho físico.
