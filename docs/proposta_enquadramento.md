# Enquadramento sugerido nas infrações da REN 846

Status: **implementado.** Proposta aprovada pelo fundador em 17/11/2026. A IA nunca rodou em modo
live: isso depende da confirmação do custo na hora da execução.

## Problema

No relatório da RN 1.137/2025 (perfil ilustrativo), 110 obrigações ficam em "Verificar
enquadramento": o Athenix não sabe em qual infração da REN 846/2019 (arts. 9º a 13) o
descumprimento cairia. Antes, só havia enquadramento quando o usuário escolhia o grupo (premissa
não gravada) ou quando o texto da obrigação nomeava o instrumento da infração por inteiro
(`termos` em `athenix/data/penalidades_ren846.json`).

## Como funciona

O sistema **sugere** e uma pessoa **confirma**. Nada entra na fila de prioridade sem confirmação.

1. **Sugestões** (`athenix/enquadramento.py`): até 3 por obrigação em "Verificar", cada uma com
   - o lado da obrigação: o trecho com âncora verificada e o link para o documento;
   - o lado da infração: o trecho literal da REN 846, com dispositivo, grupo, origem da redação e
     os itens do inciso, quando houver. O trecho vem de `penalidades_ren846.json`; só entra
     infração com âncora verificada e redação vigente;
   - o motivo: o da regra curada, ou a justificativa da IA marcada como **"Interpretação da
     IA"**, com modelo e data. O motivo não substitui as duas citações.

   Sem trecho verificado da obrigação, não há sugestão.
2. **Confirmação humana** na tela de impacto: "Confirmar enquadramento" ou "Rejeitar sugestão",
   sempre com justificativa. As duas ações usam o registro de revisão que já existe
   (`services.review`, ações `frame` e `reject_frame`), que guarda autor, data e trilha de
   auditoria. O dispositivo é conferido contra a lista de infrações, e um dispositivo inexistente
   é recusado.
3. **Efeito:** a obrigação confirmada sai de "Verificar" e entra na fila, com o grupo da infração.
   A tela e o relatório mostram "Enquadramento confirmado por <pessoa> em <data> (sugerido por
   regra curada | IA | pessoa)". A sugestão rejeitada não volta para aquela obrigação.

## Regras curadas (sem custo)

Ficam em `athenix/data/enquadramento_regras.json`: cada regra liga um instrumento nomeado na
obrigação a uma infração.

| Regra | Infração | Obrigações sugeridas na RN 1.137 |
|---|---|---|
| Manejo da vegetação | Art. 12, XXVII (Plano de Manejo Vegetal) | 13 |
| Comunicar ou notificar o Poder Público | Art. 12, XXVIII | 5 |
| À disposição nos postos de atendimento presencial | Art. 9º, II | 4 |

As regras cobrem **20 das 110** obrigações; em duas delas, sugerem duas infrações. Na minha leitura
(não é de especialista), 19 são plausíveis. A fraca é "c) Remoção de vegetação de risco",
sugerida no Art. 12, XXVIII só por "comunicar" + "Poder Público". A pessoa que revisa decide.

A semelhança genérica de palavras foi medida e descartada: das 46 sugestões que ela fazia, cerca
de 30 estavam erradas. Por exemplo, as 13 alíneas da Cessão Emergencial caíam no Art. 12, XXVIII só
por causa da palavra "emergencial".

## IA (as 90 restantes)

`scripts/sugerir_enquadramento.py` usa o adaptador de IA do projeto (`athenix/llm.py`, provedor
compatível com OpenAI ou Azure OpenAI, com modelo e preço vindos da configuração) e as travas que
ele já tem.

- **Sem configuração, ou com `ATHENIX_AI_MODE` diferente de `live`:** o script só imprime a
  estimativa e não faz nenhuma chamada.
- **Em `live`:** a chamada exige `--confirmo-custo-usd X`. X tem de ser maior ou igual ao custo
  máximo estimado, e esse custo tem de caber no teto `ATHENIX_RUN_BUDGET_USD`.
- **Durante a execução:** o custo real é somado pelo uso que o provedor informa, e a execução para
  se passar do teto.
- **O pedido:** a lista de infrações vai fixa no início, para aproveitar o cache de prefixo do
  provedor. O dispositivo da resposta é restrito por esquema às 109 infrações, então a IA não tem
  como citar um dispositivo que não existe. Cada resposta ainda é validada antes de ser gravada.
- **O resultado** fica em `athenix/data/sugestoes_enquadramento_ia.json`, com modelo, versão e hash
  do prompt, hash dos parâmetros, preço com fonte, data e custo real. A tela só mostra essas
  sugestões com `ATHENIX_AI_MODE` em `cached` ou `live`.

**Custo:** o valor certo depende do modelo e do preço configurados, e é calculado pelo script na
hora. Pela medição de hoje:
- são 90 chamadas, de cerca de 7 a 8 mil tokens de entrada cada (instruções e lista de
  infrações, que se repete, mais a obrigação), com no máximo 800 tokens de saída cada;
- o teto que o script usa para confirmar é mais conservador, porque estima por bytes:
  2,35 milhões de tokens de entrada e 72 mil de saída;
- com um modelo de US$ 2 por milhão de tokens de entrada e US$ 8 por milhão de saída (valores
  ilustrativos, não são preços pesquisados), esse teto fica em cerca de US$ 5,30, e o custo real
  esperado é de cerca de US$ 1,90 sem cache.

**Correção desta proposta:** a primeira versão trazia preços de modelos Claude, mas o adaptador do
projeto não usa esse provedor. Esses valores foram retirados.

## Defeito corrigido junto

Em `penalidades_ren846.json`, os 4 itens da lista do Art. 9º, IV ("I - unidades consumidoras;" …)
estavam gravados como infrações próprias, com rótulos repetidos. Agora são itens do inciso IV.
Antes eram 113 infrações; agora são 109, e os parâmetros não mudaram.

## Fora do escopo

- Escolher na tela um dispositivo que não foi sugerido. Hoje, o caminho para isso é a escolha do
  grupo como premissa.
- Sugestões para normas além da RN 1.137: o script processa só a demo.
- Validação das regras e dos grupos por especialista. Entra no material do Bloco 5.
