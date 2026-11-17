# Proposta: sugerir o enquadramento das obrigações nas infrações da REN 846

Status: **proposta, não implementada.** Aguarda decisão do fundador.

## Problema

No relatório da RN 1.137/2025 (perfil ilustrativo), 110 obrigações ficam em "Verificar
enquadramento": o Athenix não sabe em qual infração da REN 846/2019 (arts. 9º a 13) o
descumprimento cairia. Hoje só há enquadramento quando o usuário escolhe o grupo ou quando o
texto da obrigação nomeia o instrumento da infração por inteiro (`termos` em
`athenix/data/penalidades_ren846.json`, preenchido em 20 das 113 infrações). Exemplo: "Plano de
Contingência" leva ao Art. 12, XXVI.

## Proposta

O sistema **sugere** e uma pessoa **confirma**. Nada entra na fila de prioridade sem confirmação.

1. **Candidatos.** Para cada obrigação em "Verificar", até 3 infrações candidatas, cada uma com:
   - o lado da obrigação: trecho literal com âncora verificada (dispositivo da norma de origem);
   - o lado da infração: trecho literal da REN 846 (dispositivo, grupo, redação e origem, já
     versionados com hash em `penalidades_ren846.json`);
   - o motivo da sugestão: os termos em comum (regra) ou a justificativa marcada como
     "interpretação da IA" (IA). A justificativa nunca substitui as duas citações.
2. **Confirmação humana.** Na tela de impacto, cada candidato tem "confirmar", "rejeitar" e
   "outro dispositivo". Só a confirmação grava o enquadramento, com autor e data, no mesmo
   registro de revisão que já existe para as obrigações. A obrigação então sai de "Verificar" e
   entra na fila.
3. **Rastreabilidade.** O relatório mostra "enquadramento confirmado por <pessoa> em <data>,
   sugerido por <regra|IA>". Sugestões rejeitadas ficam no histórico, para medir a precisão.

## Medição nas 110 obrigações (feita localmente, sem IA)

Regra testada: termos em comum entre o texto da obrigação e o trecho de cada infração, com peso
maior para termos raros entre as infrações. Uma sugestão conta como "única" quando o melhor
candidato tem pelo menos 2 termos e pontua 1,5 vez acima do segundo.

| Resultado da regra | Obrigações |
|---|---|
| Candidato único | 37 |
| Grupo único, dispositivo ambíguo | 9 |
| Ambíguo: exige leitura | 64 |
| **Total** | **110** |

Leitura manual (minha, não de especialista) das 46 sugestões da regra:

- **cerca de 16 plausíveis**: 9 do relatório de manejo vegetal → Art. 12, XXVII (Plano de
  Manejo Vegetal); 3 de notificação ao Poder Público → Art. 12, XXVIII; cerca de 3 de
  disponibilizar documento nos postos de atendimento → Art. 9º, II; 1 do plano de contingência
  → Art. 12, XXVI;
- **cerca de 30 erradas ou fracas**: por exemplo, as 13 alíneas da Cessão Emergencial caem no
  Art. 12, XXVIII só porque "emergencial" se parece com "Situações de Emergência".

**Conclusão:** uma regra simples cobre bem só cerca de 16 das 110 (15%), e só se for restrita a
**termos curados**: instrumentos nomeados, como "Manejo Vegetal", "Poder Público" + "notificar",
e "postos de atendimento", acrescentados a `termos` com citação. A semelhança genérica de
palavras erra demais para ser mostrada, mesmo com confirmação, porque gasta tempo da revisora.
As **cerca de 94 restantes exigem leitura** (IA ou humano).

## Custo estimado da IA (as 110, teto)

Tamanho medido: texto das 110 obrigações = 54.984 caracteres (cerca de 500 por obrigação);
trechos das 113 infrações = 16.962 caracteres. Estimativa de 3,5 caracteres por token em
português (aproximada; confirmar com `count_tokens` antes de aprovar).

Por obrigação: cerca de 800 tokens de instruções, cerca de 4.900 de lista de infrações
(idêntica em todas as chamadas, portanto em cache) e cerca de 160 da obrigação. Saída de
cerca de 750 tokens: até 3 dispositivos por código, mais a justificativa curta e o raciocínio.
O trecho literal **não** é redigitado pela IA: o sistema busca o literal pelo código do
dispositivo.

Preços por milhão de tokens (tabela da Anthropic de 03/11/2026, consultada em 17/11/2026;
**reconfirmar em platform.claude.com antes de aprovar**):

| Modelo | Entrada | Leitura de cache | Saída | Custo estimado para as 110 |
|---|---|---|---|---|
| Claude Opus 5.5 | US$ 4,00 | US$ 0,20 | US$ 20,00 | cerca de US$ 1,90 (US$ 4,30 sem cache) |
| Claude Sonnet 5.5 | US$ 2,00 | US$ 0,10 | US$ 10,00 | cerca de US$ 0,95 |
| Claude Haiku 5.5 | US$ 0,10 | — | US$ 0,50 | cerca de US$ 0,10 |

Conta (Opus 5.5): a parte fixa (instruções + infrações, cerca de 5.700 tokens) fica em cache.
- Leitura de cache: 110 × 5.700 ≈ 627 mil tokens × US$ 0,20/M = US$ 0,13.
- Gravação da cache: uma vez, cerca de US$ 0,03.
- Entrada nova: 110 × 160 ≈ 18 mil tokens × US$ 4/M = US$ 0,07.
- Saída: 110 × 750 = 82,5 mil tokens × US$ 20/M = US$ 1,65.

Total: cerca de US$ 1,90. Sem cache, cerca de 645 mil tokens de entrada × US$ 4/M + US$ 1,65 =
US$ 4,30. A API de lotes (Batch) reduz o valor pela metade. Reprocessar só
quando a norma ou a lista de infrações muda (resultado guardado, modo `cached`).

**Recomendação:** começar pelos termos curados (sem custo; cerca de 16 obrigações) e rodar a IA
uma vez nas cerca de 94 restantes com o Opus 5.5 (abaixo de US$ 5 com margem), medindo a precisão
contra as confirmações da revisora antes de decidir rodar em outras normas. **Nenhuma chamada
paga foi feita.**

## Defeito encontrado durante a medição (não corrigido)

Em `penalidades_ren846.json`, os 4 itens da lista do Art. 9º, IV ("I - unidades consumidoras;",
"II - centrais geradoras;", "III - instalações…", "IV - sistemas de armazenamento…") foram
gravados como infrações próprias, com os rótulos "Art. 9º, I" a "IV". Esses rótulos colidem com
os incisos verdadeiros. São 4 das 113 "infrações": o total real é 109, e uma sugestão poderia
apontar "Art. 9º, II" para o item errado. A correção é rotulá-los como itens do inciso IV
(por exemplo, "Art. 9º, IV, 2") e tirá-los da lista de infrações. Ela depende de aprovação,
porque muda o arquivo de parâmetros (PR #8/#9).

## Fora do escopo desta proposta

- Implementação, telas e testes.
- Enquadramento de normas além da RN 1.137.
- Validação por especialista dos grupos sugeridos: entra no material do Bloco 5 (#16) depois.
