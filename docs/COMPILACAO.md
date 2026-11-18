# Compilação automática de normas

Para cada norma nova ingerida, o Athenix descobre o que ela altera no acervo, aplica a alteração,
guarda a nova versão com a data de vigência e preserva as anteriores. **Sem IA** na implementação
(código: `athenix/compilacao.py`; execução: `scripts/compilar_normas.py`; testes:
`tests/test_compilacao.py`). A seção final só desenha o uso de IA.

## O que o processo faz
1. **Detecta** (`compilacao.detectar`) quais normas do acervo a norma nova altera, inclui ou revoga.
   Só conta norma-alvo explícita: o bloco de alteração (`passa a vigorar com as seguintes alterações`,
   lido por `structure.segment`) ou `Ficam revogados … da Resolução Normativa nº X`. Alvo fora do
   acervo é listado e não gera operação.
2. **Aplica** (`compilacao.compilar`): substitui, inclui ou revoga dispositivos e gera uma versão
   por data de vigência, sem apagar as anteriores. Consulta: `texto_vigente(compilado, "AAAA-MM-DD")`.
3. **Registra em cada dispositivo** a norma que deu a redação, a fonte (biblioteca da ANEEL, DOU ou
   Leis.org), o hash do arquivo, o artigo do ato e o trecho literal (início/fim no texto).
4. **Sinaliza conflito e não escolhe.** Nada é decidido no lugar de uma pessoa.

## Regras de leitura e aplicação
- **Chave do dispositivo**: caminho estável (`article:9/clause:IV`); fórmula e tabela ganham número de
  ordem sob o mesmo pai; o mesmo caminho em donos diferentes (o art. 9º do ato e o "Art. 9º" citado)
  não colide.
- **Âncora**: dispositivo cujo texto é só pontilhado (`Art. 9º ........`) não muda; serve de caminho.
- **(NR)/(AC) fecha o bloco inteiro** (LC 95): vale para todos os dispositivos entre a abertura das
  aspas e o marcador. Com (NR), existente → substitui; inexistente → inclui (com aviso).
- **Sem marcador (NR)/(AC), texto diferente, vigência POSTERIOR à da redação atual → sucessão no
  tempo** (decisão do fundador, 18/11/2026): as duas redações ficam, cada uma com a sua data; o
  histórico marca `INCERTO` (a fonte não traz o marcador) e `duvidas_para_especialista` registra a
  possível colisão de numeração. **(AC) sobre dispositivo existente, ou sem marcador com a mesma data
  ou data anterior → conflito** (`conflitos`): a redação proposta não é aplicada e vai para decisão
  humana.
- **Duas normas, mesmo dispositivo, mesma data, textos diferentes → conflito**; datas diferentes
  valem em sequência e o histórico guarda todas.
- **Subitens de dispositivo substituído** que o ato não reproduz: **não são revogados**. O pontilhado
  (`........`) da LC 95 diz que o resto continua valendo e a regra não distingue os dois casos; o
  subitem fica vigente e vai para `inferencias` (`aplicada: false`) para decisão humana.
- **Revogação de artigo** leva os subitens (`revogar_com_pai`, não inferido).
- **Revogação explícita**: só `art. N`, `§ N do art. M`, `inciso R do art. N` e `parágrafo único do
  art. N` viram caminho; o resto (`a Seção IV do Capítulo V`, `a linha referente ao art. 96-A do Anexo
  IV`, `os incisos I, II e o parágrafo único…`) é devolvido em `sem_caminho`, sem palpite.
- **Vigência**: `entra em vigor na data de sua publicação` (data do DOU), data explícita
  (`em 1º de janeiro de 2027`) ou prazo (`em N dias/meses`); as exceções de `produz efeitos` por
  artigo do ato entram quando o artigo é citado sem `na parte que`. Operação sem vigência
  determinada não é aplicada (`nao_aplicado`).
- Causas gerais corrigidas no leitor de blocos (`structure.segment`), cada uma com teste de
  regressão no arquivo real: bloco sem aspas de fechamento e sem (NR), encerrado pelo próximo
  artigo do próprio ato (RN 1.148); `(NR)` fecha o bloco mesmo sem aspas (RN 1.162); inciso, alínea e
  item aceitam aspas de abertura (`"XII - …`).

## Resultado: REN 846
Base: compilado oficial da ANEEL (`atren2019846.pdf`, sha256 `efe4e35f…`), atualizado até a RN
1.137, de 21/10/2025 (485 dispositivos; 492 com as inclusões de 2026). Alterações aplicadas em ordem de vigência. Arquivo:
`athenix/data/compilado_ren846.json` (gerado; o teste falha se divergir do gerado agora).

| Ato (fonte) | Vigência | O que faz na REN 846 | Resultado |
|---|---|---|---|
| REN 1.148/2026 (biblioteca da ANEEL) | 01/01/2027 | art. 8º: inciso XXIII do art. 11 | 1 substituição em sucessão, **marcada incerta** (abaixo) |
| REN 1.162/2026 (DOU, p. 92) | 24/06/2026 | art. 16: arts. 9º IV e VII; 10 VII, XII e XIX; 21 § 11 (+ inciso I e 4 linhas de fórmula) | 11 substituições/inclusões aplicadas; 3 subitens (alíneas a–c do art. 9º, IV) em `inferencias`, não revogados, para decisão humana |
| REN 1.174/2026 (DOU, p. 68) | 04/11/2026 | art. 10: inciso XXIV do art. 11 | 1 inclusão aplicada |

**Inciso XXIII do art. 11 (sucessão no tempo, com incerteza):** a base tem o XXIII "deixar de prestar
informações … interrupções" (incluído pela RN 1.137), vigente **até 31/12/2026**. A RN 1.148 traz um
XXIII "deixar de responder … Ouvidoria", vigente **a partir de 01/01/2027**. As duas ficam no
histórico, cada uma com a sua data (`texto_vigente` em 31/12/2026 devolve a da 1.137; em
01/01/2027, a da 1.148). **Incerteza do parsing:** o texto da RN 1.148 na biblioteca da ANEEL não
traz aspas de fechamento nem (NR)/(AC); o bloco é encerrado pelo próximo artigo do próprio ato. A
**colisão de numeração** (a 1.148 propõe, para o mesmo número, conteúdo diferente do que a 1.137
incluiu) continua como **dúvida para especialista**, junto da D1 (`duvidas_para_especialista`).
Resolver: a versão da RN 1.148 no DOU de 20/02/2026 (p. 84), que o fundador vai baixar.

Datas: as versões consultáveis vão de 21/10/2025 em diante. Antes disso o estado da norma não é
reconstituível a partir deste compilado (ver validação).

## Validação
- **(b) Aplicado depois do compilado oficial.** Conferido contra a cópia do Leis.org (compilada até a
  RN 1.174, só em `.local/`, uso interno): 6 de 8 operações têm texto idêntico (art. 9º VII; 10 VII, XII
  e XIX; 21 § 11 e inciso I). As outras 2 diferem só no layout do Leis.org (inciso IV partido em itens;
  XXIV cortado pelo rodapé de página). O Leis.org não consolida a RN 1.148 (vigência 2027), o que
  confirma que o XXIII não deve entrar hoje. Teste: `test_conferencia_independente…`.
- **(a) O que deveria coincidir com o compilado oficial.** Original de 2019 (DOU de 18/06/2019,
  p. 37, `dou_ren20190846.html`, 343 dispositivos) × compilado oficial: **todo dispositivo do original
  existe no compilado** e, dos sem nota de redação, **341 de 343 têm o mesmo texto**. As 2 diferenças
  são ruído, não conteúdo (um "26." solto no fim do art. 27 do HTML e o aviso "Este texto não substitui
  o publicado no D.O." no fim do art. 51 do compilado). O compilado tem 142 dispositivos a mais, todos
  criados por alterações até a RN 1.137. Teste: `test_original_de_2019_x_compilado_oficial`.
  **Ainda pendente:** montar o compilado a partir do original + as alteradoras e comparar o que
  mudou. Faltam as alteradoras intermediárias que as notas do compilado citam: REN 1.063 (70
  dispositivos), 1.077 (56), 852 (3), 949 (1) e 1.000 (1); só a 1.137 está no repositório. O PDF
  certificado do original é só a página 37 (o HTML é o ato completo).
- A RN 1.162 também altera a REN 905 (Parcela Variável); a REN 905 do repositório tem 3 páginas, sem
  os módulos, então essa parte não é compilada.

## Limites conhecidos
- Revogação de seção, capítulo, anexo, linha de tabela e listas misturadas não vira caminho.
- Dispositivo com mesmo rótulo repetido sob o mesmo pai recebe `#2`, `#3` (numeração do texto, não
  semântica).
- A vigência "na parte que" de um artigo do ato não é aplicada por parte: a operação usa a vigência
  padrão e fica com `nota_vigencia`.
- Texto riscado (revogado na fonte) fica fora do vigente; o compilado oficial da ANEEL não traz texto
  riscado, só a nota "(Redação dada pela …)".

## IA: só desenho (nada foi rodado)
A IA não entra no cálculo nem na aplicação. Ela só triaria o volume para decidir quais normas vão
para o processo acima, e toda saída é validada por citação literal.

**(a) Triagem em volume, modelo local (Ollama).** Pergunta única por ato: "este ato altera, inclui
ou revoga alguma norma? Qual?". GPU de 12 GB: modelos de 7–14 B quantizados (por exemplo, famílias
Qwen 2.5/3, Llama 3.x ou Mistral, em Q4/Q5), contexto de 8–16 mil tokens, ato fatiado por
artigo-caput. Saída em JSON `{altera: bool, normas: [{tipo, numero, trecho_literal}]}`. Sem rede e
sem custo por chamada. Para cada norma citada, o `trecho_literal` precisa existir no texto do ato
(`athenix.evidence.verify`); sem ele a resposta é descartada. O local decide só "olhar ou não olhar".

**(b) API Azure só para os ambíguos.** Vão para a API os atos em que o local e as regras
divergem (a regra acha alvo e o modelo não, ou o contrário), em que há mais de uma norma-alvo ou em
que o bloco vem sem aspas/(NR). Mesma validação por citação literal; resposta sempre marcada
"Interpretação da IA · aguarda revisão humana". Não toca em `.env`; usa o conector já configurado e
só quando o fundador liberar.

**Plano de comparação local × API com o gabarito.** (1) Rotular à mão um conjunto de atos reais
(os 3 de 2026 + os 20 do gabarito de interpretação + 20–40 atos do DOU que alteram normas e 20
que não) com: altera? alvo(s)? tipo de operação? (2) Medir, por tipo: acerto de "altera/não",
acerto do alvo, citação literal válida, taxa de descarte e tempo por ato. (3) Comparar três
sistemas: só regras (hoje), regras + local, regras + local + API nos ambíguos. (4) Critério de
aceitação: nenhum falso "não altera" em ato que altera norma do acervo (recall do alvo = 100% no
conjunto) e nenhuma citação inventada; custo e tempo só desempatam. (5) A trava de não regressão
do gabarito não pode piorar. Resultados em `docs/avaliacao.md`.
