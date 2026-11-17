# Revisão do ensaio — 17/11/2026

Branch local: `revisao-ensaio-segunda-leitura`. A main, a demo e o site não foram alterados. Sem push, publicação ou merge.

## 1. Segunda leitura da extração

As regras continuam sendo o resultado oficial. O comando `python scripts/segunda_leitura.py` gera uma lista separada a partir do cache do ensaio, sem rede, sem carregar configuração de IA e sem tocar na avaliação do gabarito. Todas as entradas recebem **possível obrigação não detectada · revisar** e permanecem sugeridas, aguardando revisão humana.

Uma regra geral exclui atos de homologação/fixação/estabelecimento de receitas, tarifas e valores sem dever externo explícito, além de disposições de revogação, instituição e entrada em vigor. A identificação usa a redação, sem números de norma, casos do gabarito ou IDs específicos. Não se elimina uma norma inteira: deveres externos explícitos no mesmo ato permanecem elegíveis. Permissões ficam fora da lista de obrigações/proibições.

| Norma | Entradas IA-only no ensaio | Permissões excluídas | Atos sem dever externo excluídos | Restantes |
|---|---:|---:|---:|---:|
| ren20251137 | 34 | 5 | 3 | 26 |
| reh20243348 | 5 | 1 | 4 | 0 |
| dec12068 | 43 | 3 | 2 | 38 |

Total: **64** (55 possíveis obrigações e 9 possíveis proibições). O Art. 1º da REH 3.348 (G10) foi excluído. Não são obrigações confirmadas: a citação foi revalidada nas duas leituras, mas o vínculo entre o texto e a interpretação ainda exige revisão.

Novidade segue o critério do ensaio: dispositivo + tipo. Não comprova que cada entrada seja um dever novo semanticamente distinto. Não há cálculo de novas datas nem valores.

[Amostra de 10 com citações e rastreabilidade](../artifacts/revisao-ensaio/segunda_leitura.md) · [Lista completa e descartes em JSON](../artifacts/revisao-ensaio/segunda_leitura.json).

## 2. Catálogo da REN 846

Foram corrigidas as três infrações apontadas (Art. 10, IX; Art. 11, XXIV; Art. 12, XX) e mais dois casos: base ROL do Art. 21 e vigência do teto legal no Art. 24 da Lei 15.269/2025.

A origem estava no gerador: ele verificava pedaços separados e os juntava com `[…]`, conservando o selo de literal. Agora o campo `trecho` contém um único fragmento literal; o conteúdo completo interrompido por rodapé fica em `citacoes`, com as partes verificadas separadamente. Na vigência, caput, inciso IV e publicação também têm citações separadas. Não se confunde uma junção editorial com uma citação contínua.

O gerador também deixa de repetir rótulo de dispositivo que a leitura independente não confirmou. Uma parte pendente não pode herdar o estado verified da primeira parte.

A auditoria local confirmou as **163 citações verificadas** do catálogo na leitura independente das fontes disponíveis, sem `[…]` nem `[...]` verificados. Permanecem **33 parâmetros e 109 infrações**, com percentuais e datas preservados. A comparação dos 169 itens do cache também manteve todos os enquadramentos das regras. As fontes PDF locais continuam com a ressalva já existente de origem a confirmar com a ANEEL; verificação literal não certifica autenticidade oficial.

## 3. Títulos — rodada exclusiva b

Autorização posterior à estimativa: esperado US$ 0,04, máximo US$ 0,08, GPT-5-mini e reasoning medium. A configuração foi carregada somente dentro do processo do script; sua saída confirmou presença das variáveis, sem valores de chave ou endpoint.

As seis chamadas resultaram nos **42 títulos**, todos até 85 caracteres, começando com verbo e com citações literais válidas. Custo medido pelo uso retornado: **US$ 0.05505665**. Reserva conservadora do timeout: **US$ 0.0144089**. Total contabilizado: **US$ 0.06946555**, abaixo do teto. Tempo de parede das chamadas: **255.8 s**.

O primeiro prompt foi excessivamente restritivo: exigia preservar todos os detalhes em 85 caracteres, causando omissões, duas respostas que esgotaram a saída e um timeout. A recuperação pediu síntese do dever principal e citação curta. Não houve repetição cega da chamada com resultado desconhecido; seu custo máximo permaneceu reservado.

Quatro títulos têm alertas de sentido: retirar caídos ampliou o alcance da remoção; OU virou E em simulações/testes; uma permissão virou comando; e a restrição de divulgar contatos foi omitida. Os alertas e ajustes propostos estão explícitos. Os 42 continuam sugeridos; nenhum foi aplicado.

[42 títulos lado a lado, com alertas](../artifacts/revisao-ensaio/titulos/42_titulos.md) · [CSV](../artifacts/revisao-ensaio/titulos/42_titulos.csv) · [Validação das citações](../artifacts/revisao-ensaio/titulos/resultado.json).

## 4. Enquadramento — proposta, sem implementação

Mostrar uma principal por item, com as alternativas recolhidas. Priorizar correspondência entre conduta e objeto do dever e o tipo específico de manejo, contingência, comunicação ou informação. Não escolher pelo grupo mais caro. Entre opções adequadas, preferir aquela que não exige uma consequência ainda ausente. Empates ou correspondência temática fraca exigem revisão.

Marcar condicionais os casos em que falta comprovar consequência: Art. 13, II (distúrbio com desligamento ou atraso no restabelecimento) e Art. 13, VIII (prejuízo à modicidade ou ao equilíbrio econômico-financeiro). A simples obrigação de prevenir não comprova o evento. Rebaixar Art. 11, XIV e XXI para fundamentos gerais. O Art. 13, XVI exige ONS, não distribuidora; o caput do Art. 12, I isolado, terminado em dois-pontos, não contém a tipificação completa.

| Resultado da simulação do cache | Itens |
|---|---:|
| principal não condicional e não genérica | 106 |
| principal condicional | 1 |
| somente genérica | 1 |
| sem principal | 2 |

**106/110 passam essa triagem formal; isso não significa 106 enquadramentos juridicamente confirmados.** Há 23 principais com a dúvida editorial D1 do Art. 11, XXIII. A recontagem usa as 281 sugestões com citações aceitas no ensaio; a sugestão anteriormente descartada por citação inválida continua excluída.

Antes de exposição financeira, exigir confirmação humana com revisor, data, dispositivo escolhido e justificativa. Conservar a sugestão original como interpretação da IA e a versão do catálogo usada. A exposição atual continua calculada somente pelo caminho oficial existente.

[Critérios e recontagem item a item](../artifacts/revisao-ensaio/enquadramento_proposta.md) · [Dados da simulação](../artifacts/revisao-ensaio/enquadramento_proposta.json).

## 5. Por que G09 falha e como resolver remissões

O sistema percebe que o Art. 16 da RN 1.137 aponta para outro texto, mas só registra uma referência: o campo target fica vazio. Ainda não existe a etapa que abre a norma de destino e liga os dispositivos. Por isso a verificação de remissão falha, embora o Decreto já esteja no repositório. Não é necessário pagar outra leitura da IA para localizar o documento.

Há duas ressalvas reais na fonte: a RN menciona 20 de julho de 2024, enquanto o Decreto 12.068 é de 20 de junho de 2024; e a RN cita os incisos V e VI, enquanto o § 1º do Art. 4º do Decreto menciona V, VI e VII. Não se pode corrigir essa divergência silenciosamente. Na extração atual, o cabeçalho Art. 4º quebrado entre linhas também está em uma unidade Texto após título, embora seus incisos estejam abaixo dela; um índice baseado apenas no rótulo estruturado não basta.

Proposta para uma etapa futura, sem implementação:

1. Montar um índice local dos atos por tipo, número normalizado e ano, mantendo versão, fonte e hash. Reconhecer cabeçalhos quebrados entre linhas e distinguir texto próprio de redação de outra norma citada.
2. Interpretar a remissão como destino explícito: Decreto 12.068/2024, Art. 4º, incisos V e VI. Não resolver apenas por palavras parecidas, IDs transitórios ou pela posição na lista.
3. Localizar o caput e os incisos no arquivo de destino já disponível e validar as citações nas duas leituras. Manter separadas a prova literal e a decisão de que a remissão está resolvida.
4. Apresentar lado a lado o trecho de origem, os dispositivos de destino e as divergências de data e de incisos. Neste caso, manter resolução proposta/pendente até revisão humana, sem acrescentar automaticamente o inciso VII ao dever da RN.
5. Usar índice/visitas para impedir ciclos, registrar alvo ausente ou ambíguo e não inventar conteúdo quando o documento não existir. Datas continuam no motor determinístico, apenas com marcos confirmados.
6. Testar remissão válida local, documento ausente, artigo inexistente, versões concorrentes, data divergente, cabeçalho quebrado, cadeia de remissões e ciclo. Depois avaliar a eventual melhoria de G09 em mudança própria; não alterar o gabarito para mascarar falha.

## Verificação e limites

- 286 testes Python passaram; Ruff e formatação passaram.
- Trava oficial sem regressão: 19/20 casos; obrigação 11/11, prazo 8/8, autoria 10/10, vigência 4/4; remissão 0/1. Gabarito e baseline preservados.
- Respostas brutas e relatórios detalhados ficam em artifacts/, ignorados pelo Git. Nenhuma resposta bruta entra no stage.
- Nenhuma alteração em landing/, templates, static/, main ou configuração da Vercel. Nenhum push ou merge.
- Enquadramento e resolução de remissões são propostas. CI nos três sistemas não foi executado, pois não houve push; a suíte foi executada localmente no Windows.
- Citações válidas não equivalem a aprovação da interpretação. Os quatro alertas dos títulos, as sugestões da segunda leitura e a dúvida D1 aguardam revisão humana.
