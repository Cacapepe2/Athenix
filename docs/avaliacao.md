# Avaliação da interpretação contra gabarito

Registro de 10/11/2026. Mede o pipeline determinístico (sem IA) em dispositivos anotados; não é
parecer jurídico nem medida de precisão global.

## Conjunto

`tests/gabarito/`: 20 casos em 3 atos de tipos e formatos diferentes (proveniência e hashes em
`fontes.json`):

| Ato | Tipo / formato | Afeta | Casos |
| --- | --- | --- | --- |
| RN ANEEL 1.137/2025 | resolução normativa, PDF compilado | distribuidoras, transmissoras | 9 |
| REH ANEEL 3.348/2024 | resolução homologatória, PDF (cópia secundária, ver ressalva) | transmissoras, ONS | 5 |
| Decreto 12.068/2024 | decreto federal, HTML windows-1252 | distribuidoras, ANEEL | 6 |

Cada caso tem um `trecho` literal e o esperado para obrigação (modalidade e sujeito), não obrigação,
prazo (quantidade, unidade, marco e data), autoria (norma dona do bloco), vigência, revogação e
remissão. **O gabarito foi elaborado por IA a partir do texto e ainda não foi revisado por especialista**
(`revisado_por_humano: false`). `tests/test_gabarito.py` garante que todo trecho existe uma única vez
na fonte, extraída sem o segmentador do sistema.

## Executar

```powershell
.\.venv\Scripts\python.exe scripts/avaliar.py --rotulo atual   # ~1 min; grava artifacts/avaliacao/atual.{json,md}
```

## Métricas

- **Acertos por verificação**: o item do sistema cobre o trecho (por qualquer âncora verificada) e o campo bate.
- **Citações corretas**: proporção de itens cujo texto literal existe na fonte real. Pega texto
  corrompido que o sistema "verifica" contra a própria extração.
- **Falsas verificadas**: âncoras que o sistema marcou como verificadas, mas cujo trecho não existe
  na fonte lida por outro motor. Tem de ser zero.
- **Sem fonte**: itens sem âncora verificada.
- Precisão é **local** (só os dispositivos anotados), não global.
- Referência da fonte: PDF pelo pypdfium2 (o extrator usa pdfplumber); HTML pelo HTMLParser da
  biblioteca padrão com a codificação conferida à mão. A comparação ignora espaços. Até a versão
  `fase2` a referência de PDF era o próprio pdfplumber, o que tornava as citações de PDF circulares.

## Versões do parser

| Versão | Mudança | Casos corretos | Falsas verificadas (RN / REH / Decreto) | Citações na fonte (RN / REH / Decreto) |
| --- | --- | --- | --- | --- |
| `inicial` | código recebido | 6/20 | não medido com referência independente | 254/254 · 29/29 · 4/92 (método circular para PDF) |
| `fase2` | prazo "têm N dias", datas, aspas aninhadas, vigência | 11/20 | 3/364 · 1/31 · 124/128 | 256/259 · 28/29 · 4/92 |
| `item0` | decodificação HTML (BOM → cabeçalho → meta → UTF-8 → windows-1252), detector de mojibake, citação confirmada por segunda leitura | 13/20 | **0/360 · 0/30 · 0/160** | 256/258 · 29/29 · 126/126 |
| `etapa1` | prazos por extenso, publicação própria × outro evento, assinatura × publicação, prazo herdado sem duplicar, obrigação periódica, título encerra dispositivo, dever + permissão por frase, sujeito sem rótulo | 18/20 | 0/336 · 0/32 · 0/173 | 252/254 · 31/31 · 140/140 |
| `art-minusculo` | "art." minúsculo no início da linha é remissão, não artigo | 19/20 | 0 · 0 · 0 | 252/254 · 31/31 · 145/145 |
| `remissoes` | remissão explícita a ato do acervo local resolvida como proposta (`athenix/remissoes.py`); o avaliador passa a exigir o alvo do gabarito, não qualquer alvo | 20/20 | 0 · 0 · 0 | 252/254 · 31/31 · 145/145 |

Em `etapa1`, na RN 1.137: prazos duplicados 12 → 0, sujeitos com rótulo ("132.", "a)") 135 → 0, penalidades 4 → 3 (as 3 restantes são "Constitui infração" da RN 846), prazos recorrentes 0 → 2. Decreto: sujeitos com rótulo 9 → 0.

Em `item0`, ficam pendentes (e não verificadas) 2 âncoras da RN (itens 23-G e 23-H, cuja unidade
engole uma tabela) e 1 da REH (fórmula). Mojibake no texto do Decreto: 634 → 0.

## Resultado

Linha de base medida numa cópia do código com as quatro correções desfeitas, com o mesmo avaliador.

| Verificação | Antes | Depois |
| --- | --- | --- |
| obrigação | 6/11 | 7/11 |
| prazo | 3/8 | 5/8 |
| autoria | 5/10 | 7/10 |
| vigência | 1/4 | 3/4 |
| revogação | 1/2 | 1/2 |
| não obrigação | 2/2 | 2/2 |
| remissão | 0/1 | 0/1 |
| **casos totalmente corretos** | **6/20** | **11/20** |
| citações corretas: RN / REH / Decreto | 254/254, 29/29, 4/92 | 259/259, 29/29, 4/92 |
| sem fonte | 0% | 0% |

Correções: "têm N dias para" como dever (RN 1.137, Art. 17); datas `30.10.2025`, `21.6.2024` e
`1º de julho de 2024`; aspas internas não encerram bloco citado, "(NR)" encerra; vigência "na data de
sua publicação" derivada só com data de publicação única e marcada `basis: publication`.

## Limites conhecidos

- Gabarito elaborado por IA, sem revisão de especialista; 20 casos não medem cobertura global.
- No HTML, a segunda leitura compartilha a decodificação com o extrator. A garantia vem do detector
  de mojibake (limiar fixo de 3 ocorrências), não de um segundo decodificador.
- Tabelas e fórmulas raramente são confirmadas por outro motor (ordem das células diverge): ficam
  pendentes. Texto de OCR não tem segunda leitura: fica pendente.
- Âncoras gravadas antes de `item0` não são reconferidas automaticamente; é preciso reprocessar.
- REH 3.348 vem de cópia secundária (ver `fontes.json`).
- Fontes da REN 846 e alteradoras: origem a confirmar com a ANEEL; os PDFs não estão no repositório
  (ver `docs/parametros_impacto.md`) e os testes sobre o texto real pulam sem eles.

Itens da revisão técnica fora do escopo atual (decisão de 11/11/2026: priorizar o módulo de impacto):

1. **Identidade do arquivo**: SHA-256, assinatura `%PDF-` e limite de tamanho existem; falta marcar "apenas layout" por hash do texto normalizado e registrar falha de download.
2. **Extração**: offsets e avisos por página e motor registrado existem; falta NFC na extração e mapa de posição da normalização.
3. **Ruído de layout**: texto riscado (redação revogada em PDF compilado e `<strike>`/`<s>`/`<del>`
   em HTML compilado) tratado: fica fora da interpretação, com citação pendente. Não tratado (rodapé de compilação de terceiro e número de página dentro do dispositivo, sumário colado na ementa, "1. ......", rodapé web, hifenização, cabeçalho repetido, duas colunas, HTML que quebra linha em cada tag e separa "Art." do número).
4. **Estrutura**: "art. N" minúsculo no início de linha corrigido (`art-minusculo`); "§ N do art."
   quebrado em linhas (HTML do planalto.gov.br) é remissão, não parágrafo (Bloco 2); ordinais 5o/5º/5°, validação de inciso romano, itens fora de anexos, caminhos duplicados e separação de epígrafe/ementa não tratados.
5. **Blocos de alteração**: aspas aninhadas e "(NR)" tratados; falta fechar no próximo artigo próprio ou título, norma-alvo só pelo caput ("INDETERMINADO") e marcas explícitas de inclusão/revogação.
6. **Tabelas**: marcador "Tabela N" existe; unidade anterior ainda engole a tabela seguinte (itens 23-G/23-H) e não há reconstrução de células.
7. **FAQ**: perguntas separadas e origem "esclarecimento" marcada; "Publicado em/Atualizado em" não capturados.
8. **Remissões**: resolvidas só quando o ato citado está no acervo local, uma única vez, e o artigo e os incisos são localizados no destino (cabeçalho pelo início do texto, que pode estar quebrado). O resultado é proposta para revisão humana, com as citações do destino e as divergências (ex.: data do ato citada errada). Um salto só, sem cadeia. No gabarito, 1 remissão resolvida (G09) e 18 continuam "ato citado ausente do acervo local". O produto (banco) ainda não usa o índice: só o avaliador.
11. **IA**: schema estrito, resposta bruta, cache, prompt versionado, estimativa e teto existem; nenhuma chamada real feita, divisão de ações e tratamento de truncamento não exercitados.
12. **Verificação**: estados verificada/pendente/inválida e mínimo de 16 caracteres existem; falta cobertura % do texto, versão do parser nos resultados e alerta de inconsistência da fonte (necessário para a demo, Etapa 3).

## Falhas restantes (causa raiz)

| Casos | Causa |
| --- | --- |
| G09 | Resolvido em `remissoes` como proposta: Decreto 12.068, Art. 4º, V e VI, com a divergência "20/07/2024" × "20/06/2024" listada. O § 1º do Art. 4º do Decreto cita V, VI e VII; o sistema não acrescenta o VII à remissão da RN. Aguarda revisão humana. |
| — | Sujeito com oração relativa no Decreto ("…à concessionária, que"): o sujeito correto está contido, mas não isolado. |

## Trava de não regressão

`tests/baseline/metricas_v1.json` congela os números de hoje: 20/20 casos corretos; obrigação 11/11,
prazo 8/8, autoria 10/10, vigência 4/4, remissão 1/1 (e as demais verificações); citações falsamente verificadas 0 nas
três normas; citações encontradas na fonte 252/254 (RN), 31/31 (REH) e 145/145 (Decreto).

- `python scripts/avaliar.py --comparar tests/baseline/metricas_v1.json` sai com erro se qualquer
  métrica piorar. O mesmo roda como etapa "Não regressão do gabarito" no CI (Ubuntu, Windows e macOS) e como
  teste (`tests/test_nao_regressao.py`).
- Falha se: um caso ou verificação acerta menos; uma citação deixa de ser encontrada na fonte; sobem
  as citações não encontradas, as falsamente verificadas, os itens sem âncora verificada, os prazos
  duplicados ou os sujeitos com rótulo; ou o tamanho do gabarito muda (aí a linha de base precisa ser
  atualizada de propósito).
- **Melhoria atualiza a linha de base só em commit próprio**, explicando o porquê:
  `python scripts/avaliar.py --rotulo <nome> --congelar tests/baseline/metricas_v1.json` (ou uma
  nova versão `metricas_v2.json` e o caminho trocado no CI).
- Limite: a trava só vê os 20 casos do gabarito, que não foi revisado por especialista.

## Teste de tabelas (dicionário de dados do Auto de Infração)
Fonte: `tests/fontes_impacto/dados_abertos/dm-auto-de-infracao.pdf` (dicionário v1.0, 03/05/2022,
4 págs., sha256 `8c13d4f7…`) contra `auto-infracao.csv` (dados abertos da ANEEL, 1.635 linhas, 28
colunas, baixado em 17/11/2026, em `.local/`). Pipeline do Athenix (pdfplumber), sem IA.
Reproduzir: `python scripts/testar_tabelas.py`; regressão: `tests/test_tabelas_dicionario.py`.

| Medida | Resultado |
|---|---|
| Campos extraídos / campos do CSV | 28 / 28; mesma ordem; nenhum duplicado |
| Linhas de dado perdidas entre páginas | 0 (9 campos na pág. 2, 19 na pág. 3) |
| Palavras do PDF na área da tabela perdidas ou acrescentadas | 0 de 475 |
| Tipos reconhecidos (texto, data, numérico) | 28 / 28 |
| Descrições que viraram outro campo | 0 |
| Campo do dicionário ausente do CSV | `DatLavramentoTE`; no CSV a coluna é `DatLavraturaTE` (grafia diverge: erro do dicionário ou da publicação) |

Defeitos do pipeline encontrados:
1. **Continuação sem cabeçalho.** A tabela da pág. 3 continua a da pág. 2 sem repetir o cabeçalho, e
   o leitor tratava a 1ª linha de dado (`NumProcessoPunitivo`) como cabeçalho. Corrigido de forma
   geral (`link_continuations`, `athenix/poc/reader.py`): a 1ª tabela de uma página com a mesma
   moldura horizontal (±3 pt) da última da página anterior, e que não repete o cabeçalho, é
   continuação e herda o cabeçalho (`continuation_of`, `header_inherited`). As linhas lidas não
   mudam; só metadado. Teste de regressão com o arquivo real.
2. **Célula mesclada no cabeçalho.** Na pág. 2 a tabela tem 5 colunas e o cabeçalho "Tamanho do
   Campo" fica na coluna 3, enquanto os valores (7 de 9 linhas) caem na coluna 2; a pág. 3 tem 4
   colunas. Nenhum texto se perde, mas o índice de coluna não identifica o campo. Não corrigido no
   leitor: o consumo por posição não é seguro; `scripts/testar_tabelas.py` lê as células não vazias
   na ordem nome, tipo, tamanho opcional, descrição. Limite conhecido.
3. A nota "Os caracteres de máscara não são armazenados." (pág. 4) vira uma tabela de 1 linha: ruído
   rotulado, não é campo.

Dicionário x dados reais (a conferir no Bloco 4, afetam o cálculo):
- `VlrPenalidade`, `VlrMultaAposJuizo`, `VlrMultaAposDiretoria`: vírgula decimal, sem separador de
  milhar; 87, 5 e 3 valores vêm como `,99` (sem inteiro) e precisam de leitura própria.
  `VlrMultaAposJuizo` declara tamanho `16` (sem decimais), mas os dados têm 2 decimais.
- `DscObjetoFiscalizado` (declarado 120): 10 valores maiores, até 3.197 caracteres.
- `CodObjetoFiscalizado` (declarado 21): 56 valores maiores, até 561 (vários códigos concatenados).
  Os valores trazem espaço à esquerda; comparar sempre depois de `strip`.
- Datas no CSV estão em `AAAA-MM-DD`.

## Consistência HTML × PDF: atos do DOU (3.2)
Pares em `tests/fontes_impacto/dou/` (HTML da matéria + "versão certificada" em PDF), baixados em
17/11/2026. Pipeline do Athenix, sem IA. Reproduzir: `python scripts/comparar_dou.py`; regressão:
`tests/test_dou.py`. Texto guardado intacto; normalização (`athenix.normalizacao`) só na comparação.

**O PDF certificado é a página do DOU, não o ato.** Só o Despacho 1.293 cabe inteiro na página. As
resoluções continuam nas páginas seguintes, então a comparação vale para a parte que o PDF cobre
(o resto é "fora da cobertura", não diferença de leitura). Faltam as páginas seguintes para fechar os
pares da REN 1.162 (cobertura 26%) e da REN 1.174 (9%).

| Ato | Par completo? | Antes → depois | Status |
|---|---|---|---|
| Despacho 1.293/2026 (DOU 23/04, p. 66) | sim (100%) | palavras do PDF achadas em ordem no HTML 5,2% → 98,8%; unidades sem par 2 → 0; itens sem par 4 → 0 | 2 diferenças restantes: 1 de espaçamento (`36 a`/`36a`); órgão ausente no PDF |
| REN 1.162/2026 (DOU 24/06, p. 92) | não (26%; falta pág. 93+) | 97,5% → 99,9%; unidades sem par 7 → 0; texto de unidade diferente 2 → 0; itens sem par 3 → 0 | 3 restantes: 2 de espaçamento (`n o`/`no`, `da`/`decorrentesda`); órgão ausente no PDF |
| REN 1.174/2026 (DOU 04/11, p. 68) | não (9%; falta pág. 69+) | 45,2% → 100%; unidades sem par 14 → 0; texto diferente 13 → 0; itens sem par 34 → 0 | sem diferença na parte coberta |

Na área coberta, estrutura (artigos, parágrafos, incisos, alíneas, caminhos), normas alteradas e
citadas, obrigações/prazos extraídos e citações literais são iguais nos dois formatos. Cabeçalho:
tipo, número, data, edição, página e ementa batem; o PDF omite o órgão em 2 dos 3 atos.

**Causas gerais corrigidas (cada uma com teste de regressão no arquivo real):**
1. *Layout em colunas (leitura do PDF).* A página do DOU tem 2 colunas e os atos se intercalavam
   linha a linha. `structure.page_sides` detecta o corredor (faixa livre ≥ 8 pt, linhas largas dos
   dois lados, nenhuma tabela cruzando) e lê coluna a coluna; coluna única, tabela e os PDFs do
   acervo saem idênticos. Cada palavra fica na coluna do seu centro (o número da página fica no meio).
2. *Ruído do DOU como conteúdo.* `athenix/dou.py` isola como ruído rotulado: cabeçalho
   (`Seção 1 · ISSN · Nº/edição/data`), rodapé (verificação, assinatura ICP-Brasil, selo), número da
   página, cabeçalho de órgão e, no HTML, navegação, botões e rodapé do portal (o extrator geral
   punha "Caminho de Navegação…" no preâmbulo).
3. *Vários atos na mesma página.* O ato pedido é conteúdo; os outros são "outros atos na página",
   separados pelo título. Requisito para o INLABS (`docs/INLABS.md`). Título do DOU com o "DE"
   omitido (`27 OUTUBRO DE 2026`, nas Resoluções Autorizativas 16.820 e 16.822) é aceito.
4. *Texto invisível.* O PDF traz texto branco sobre branco (`W:0.0035cm H:0.0035cm` sob as linhas
   de pontos; conferido por renderização): ruído "texto_invisivel".
5. *Norma-alvo do bloco citado (`segment`).* A 1ª linha de um bloco citado que cita outra norma
   ("…art. 2º da Resolução Normativa nº 1.029…") trocava a norma-alvo no HTML (linha inteira) mas
   não no PDF (a linha quebra): o art. 35-A saía como da RN 1.029, e não da RN 875. A linha que abre
   aspas não troca mais o alvo. Causa geral de qualquer norma com blocos de alteração.
6. *Remissão a "Anexo" no início de linha quebrada (`segment`).* "Anexo I do Decreto nº 2.335…"
   virava um anexo falso no PDF (e truncava o preâmbulo). A continuação em minúscula (`do`, `da`,
   `ao`…) denuncia a remissão, como já se fazia para `§ … do art.`.

**O que continua diferente (sem correção geral segura):**
- *Espaços perdidos no PDF* (`36a`, `decorrentesda`): a camada de texto do DOU justifica o texto
  sem emitir espaço entre algumas palavras. Causa: leitura do PDF/layout do DOU. A comparação trata
  como equivalente depois de normalizar; o texto guardado do PDF mantém a leitura original.
- *Órgão ausente no PDF* (REN 1.162 e Despacho 1.293): o órgão é título de seção na página, e
  nesses dois a página não o traz junto do ato. Causa: layout do DOU. O órgão vem do HTML.
- *Ementa da REN 1.162*: o PDF traz um glifo `q` solto antes da ementa; igual no HTML, então não
  gera diferença entre os formatos (observado, não tratado).
- Os pares só fecham com as páginas seguintes das resoluções (o botão "Diário Completo").

## Decisão de penalidade (3.4)
`athenix/penalidade.py` lê, por regras, voto/despacho de recurso contra auto de infração: agente
(INTERESSADO), processo, auto de infração, efeito, valor decidido e dispositivos citados como
infringidos, cada campo com trecho literal e página (`tests/test_penalidade.py`). Nenhum dos três
atos do DOU do acervo decide multa: o Despacho 1.293 indefere uma súmula sobre os arts. 36 a 45 da
REN 846, sem agente nem valor. Os dois votos da ANEEL em `.local/dados_aneel/` são decisões:
- Proc. 48500.006992/2022-98, Taesa, AI 0018/2023-SFT: multa reformada para R$ 8.738.737,50.
- Proc. 48500.004507/2021-61, Neoenergia Pernambuco, AI 002/2022-SFE: multa mantida em
  R$ 32.949.775,22.
Resultado "pendente de revisão humana". Ainda não conferido com o CSV (Bloco 4).
