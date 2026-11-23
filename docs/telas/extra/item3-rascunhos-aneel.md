# Item 3 — rascunhos de perguntas para a ANEEL

Branch `extra/rascunhos-aneel`, baseada na main `e85d0a6`, sem merge. Estimativa inicial: 60 minutos.

Os sinais de incerteza já existentes geram pedidos identificados como **rascunho — revisar antes de
enviar**, sem chamada de IA e sem envio. Cada pedido contém dúvida em uma frase, leituras ou
hipóteses já registradas, dispositivo, citação literal, fonte/SHA-256 e possíveis esclarecimentos do
FAQ, quando encontrados. A relação com o FAQ permanece marcada como não confirmada para aquela dúvida.

| Norma | Sinais a confirmar | Pedidos agrupados | Referências preservadas |
| --- | ---: | ---: | ---: |
| RN 1.137 | 171 | 28 | 171 |
| REN 1.174 | 118 | 24 | 118 |

A pergunta repetida fica em um único grupo por tipo de dúvida e leituras registradas. O item mostra
apenas suas referências; o relatório, na seção **Perguntas para a ANEEL**, mostra todos os grupos.
Os 289 sinais têm item correspondente: nenhuma referência ficou sem acesso no plano.

## O que mudou

- `esclarecimentos.casos_a_confirmar` compartilha os sinais antes do filtro por FAQ, evitando perder
  dúvidas sem uma possível resposta encontrada. O relatório anterior mantém seus resultados.
- `athenix/rascunhos_aneel.py` monta e agrupa os pedidos a partir desses sinais. O export inclui
  `rascunhos_aneel` nas duas normas.
- O detalhe de cada obrigação tem um bloco recolhido de rascunhos. O relatório usa os grupos completos,
  preservando todos os dispositivos e citações.
- Nenhum valor, prazo, sujeito, enquadramento ou classificação é corrigido pelo rascunho.

A comparação com os JSONs da main mostrou que os campos existentes permaneceram iguais, exceto os
metadados de geração. Deveres principais continuam 147/75; vencidas RN: 8 principais e 11 detalhes.

## Esclarecimentos confirmados e limites das leituras

O Art. 13, VI e o Art. 14 já têm esclarecimento confirmado sobre prazo. Não foi gerada nova pergunta
sobre esse prazo. Seus enquadramentos continuam sem confirmação, e somente essa dúvida permanece
nos respectivos rascunhos (além da remissão externa do Art. 13, VI).

Os dados não fornecem sempre duas interpretações normativas concorrentes. Nesses casos o rascunho
mostra a hipótese já usada pelo plano ou sugerida pela IA, a falta de confirmação e a indicação
expressa de que as alternativas precisam de revisão. Não se inventa agente responsável, infração,
artigo ou data alternativa. Uma sugestão preexistente da IA continua identificada como sugestão.

Os esclarecimentos possíveis do FAQ não mudam os cálculos nem são promovidos a confirmação.
Nenhuma pergunta foi enviada, e a interface não oferece envio automático.

## Validação

- Pytest: 580 aprovados e 6 pulados por dependerem de acervo privado não acessado.
- Site: 119 testes, TypeScript, build, pré-renderização e verificação do HTML aprovados.
- Trava v2 vigente: 29/29, sem regressão; linha de base preservada.
- `exportar_plano_demo.py --verificar`: ambas as normas reproduzidas.
- Ruff, formatação e check_secrets aprovados.
- Chrome/Playwright: 1280 e 390 px, sem rolagem horizontal ou erro JavaScript. Rótulos, dispositivo,
  citação e filtro pelo item conferidos; nenhuma requisição de escrita/envio observada.
- Relatório: 28 grupos/171 referências na RN e 24/118 na REN, sem omissão ao agrupar.
- CI: checks dos três sistemas vinculados ao commit do PR.

## Capturas

- [RN 1.137, 1280 px](item3-rascunho-rn1137-1280.png)
- [RN 1.137, 390 px](item3-rascunho-rn1137-390.png)
- [REN 1.174, 1280 px](item3-rascunho-ren1174-1280.png)
- [REN 1.174, 390 px](item3-rascunho-ren1174-390.png)
- [Relatório RN 1.137](item3-relatorio-rn1137-1280.png)
- [Relatório REN 1.174](item3-relatorio-ren1174-1280.png)

A equipe precisa revisar as perguntas e formular/validar leituras alternativas quando os dados forem
insuficientes. O relatório preserva todas as citações e pode ficar extenso. O bundle compartilhado
cresce cerca de 27 kB gzip (154 kB contra 127 kB); o aviso de chunk grande permanece e não foi medida
performance em dispositivo real. Sem IA paga, sem acesso a `.env` ou `.local/`, sem merge.
