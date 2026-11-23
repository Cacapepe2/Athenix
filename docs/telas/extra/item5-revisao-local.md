# Item 5 — revisão pessoal no navegador

Estimativa anunciada: 45 minutos. Implementação em branch própria a partir da `main` (`e85d0a6`); sem merge e sem mudança do motor ou dos exports normativos.

Os detalhes da obrigação, tanto nos blocos do plano completo quanto nos temas, oferecem confirmar/corrigir para enquadramento e área, e para sujeito quando ele é implícito. Correção de até 200 caracteres, sem envio; pode ser cancelada ou a revisão limpa. O valor original continua visível. A confirmação é um registro pessoal, não validação jurídica nem promoção de sugestão da IA a dado do motor.

As revisões usam localStorage com try/catch, separado por norma e SHA-256 da fonte. Registros inválidos, de itens desconhecidos ou cujo valor original mudou são descartados. Se o navegador bloquear a gravação, o aviso informa que ficam só em memória e podem ser exportadas antes de fechar. Não há sincronização, importação ou conta de usuário nesta rodada.

O botão JSON exporta todas as revisões da norma com hash, item, dispositivo, trecho literal, campo, original, estado e valor registrado. O relatório inclui esses mesmos registros em “Revisões pessoais deste navegador”, sem recalcular exposição, prazos ou áreas automáticas.

## Verificação

- Três testes novos: confirmação/correção/limpeza e imutabilidade; persistência por norma/hash, dados inválidos e falhas; JSON/relatório rastreáveis e números preservados. Testes do site: **119 aprovados**.
- Navegação real no Chrome, com build local, em **1280 e 390 px**, nas duas normas: confirmou sujeito e enquadramento, corrigiu área, exportou e leu o JSON (três registros), recarregou e conferiu a persistência. A RN 1.137 usa o item 148; a REN 1.174, Art. 159-B, § 1º.
- Conferido o relatório das duas normas com os três registros. Nenhum erro JavaScript, estouro horizontal ou requisição de escrita durante os cenários.
- Acesso ao localStorage forçado a lançar erro: aviso visível, confirmação continua em memória e exportação fica disponível.
- Build e pré-renderização passaram; permanece o aviso já existente de chunk acima de 500 kB. Sem dependência nova nem estilo fora dos tokens.
- Pytest, trava v2, dois exports com `--verificar`, Ruff, segredos e CI Linux/Windows/macOS compõem a validação do PR; conferir resultados finais no commit publicado.

## Prints

| Tela | 1280 px | 390 px |
|---|---|---|
| RN 1.137, item 148 | [revisões](item5-revisoes-rn1137-1280.png) | [revisões](item5-revisoes-rn1137-390.png) |
| REN 1.174, Art. 159-B, § 1º | [revisões](item5-revisoes-ren1174-1280.png) | [revisões](item5-revisoes-ren1174-390.png) |
| Relatório RN 1.137 | [relatório](item5-relatorio-rn1137-1280.png) | — |
| Relatório REN 1.174 | [relatório](item5-relatorio-ren1174-1280.png) | — |
| Armazenamento bloqueado | — | [aviso](item5-armazenamento-bloqueado-390.png) |

**Limites:** dados podem ser apagados pelo navegador ou pelo usuário; exportar o JSON preserva uma cópia manual. Revisões de uma norma selecionada no filtro de outra página devem ser feitas na página da própria norma. Não foi testado em aparelho físico nem em todos os navegadores. Os screenshots usam dados de revisão fictícios, criados em contexto isolado.

**Decisão:** avaliar esse fluxo antes de aprovar qualquer publicação; o PR permanece draft.
