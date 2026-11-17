# Robustez da extração: mapa de problemas

Registro de 17/11/2026, atualizado no mesmo dia depois de duas correções. Os invariantes de
`athenix/saude.py` foram aplicados a 26 normas reais. São regras gerais, sem nada específico de uma
norma:
- numeração em sequência por nível;
- todo dispositivo presente na segunda leitura da fonte;
- nenhum dispositivo começando no meio de palavra;
- cobertura mínima do texto estruturado;
- páginas sem texto.

Nota de 0 a 100; abaixo de 70, "revisar extração".

Para refazer o mapa: `python scripts/avaliar_corpus.py --saida <pasta>`. Para refazer a
comparação entre versões: `python scripts/comparar_mapas.py`. Os mapas de cada etapa estão em
`docs/robustez/` (JSON com nota, alertas, métricas e SHA-256 de cada documento).

## Corpus

- **Planalto (HTML, atos oficiais):** 20 leis e decretos do setor elétrico. 16 estão em
  `tests/corpus_planalto/`, com URL, data de obtenção e SHA-256 em `fontes.json`; 4 já estavam no
  repositório.
- **ANEEL (PDF):** a RN 1.137/2025 (repositório).
- **DOU (PDF):** a página do DOU com a RN 1.137/2025 (repositório).
- **Cópias de terceiro:** a REH 3.348 (cópia da ISA, repositório) e as REN 846, 1.148 e 1.174
  (compilações do Leis.org, só locais, fora do repositório).
- **Não obtidos:** os PDFs oficiais da ANEEL (`www2.aneel.gov.br/cedoc/`) responderam **403 (acesso
  automatizado bloqueado)** para REN 846/2019, REN 1.000/2021, REN 956/2021 e REN 1.148/2026. Não
  houve nova tentativa nem contorno; esses PDFs precisam ser fornecidos pelo fundador.

## Evolução das notas

Três versões do mapa:
1. **Original:** o primeiro mapa.
2. **Autoria por caput:** cada bloco de nova redação passa a pertencer à lei citada no caput do
   artigo que o abre, em vez de herdar a primeira lei alterada.
3. **Vetado/revogado:** dispositivo marcado "(VETADO)", "(Revogado …)" ou riscado não conta como
   salto com o vizinho nem como repetição da nova redação.

| Documento | Original | Autoria por caput | Vetado/revogado | Anomalias de numeração |
| --- | ---: | ---: | ---: | ---: |
| Lei 8.987/1995 (concessões) | 80 | 80 | 82 | 10 → 10 → 9 |
| Lei 9.074/1995 (concessões e permissões) | 82 | 82 | 88 | 9 → 9 → 6 |
| Lei 9.427/1996 (ANEEL) | 70 | 70 | 70 | 18 → 18 → 17 |
| Lei 9.478/1997 (política energética) | 70 | 70 | 70 | 44 → 44 → 32 |
| Lei 9.648/1998 | 70 | 70 | 70 | 69 → 69 → 66 |
| Lei 9.991/2000 (P&D e eficiência) | 96 | 96 | 100 | 2 → 2 → 0 |
| Lei 10.438/2002 (Proinfa, CDE) | 70 | 70 | 70 | 29 → 27 → 25 |
| Lei 10.848/2004 (comercialização) | 70 | 70 | 70 | 30 → 30 → 27 |
| Lei 12.783/2013 (renovação de concessões) | 70 | 70 | 70 | 22 → 21 → 17 |
| Lei 13.360/2016 | 70 | 70 | 70 | 52 → 41 → 33 |
| Lei 13.848/2019 (agências reguladoras) | 70 | 70 | 70 | 24 → 16 → 16 |
| Lei 14.120/2021 | 70 | 72 | 74 | 21 → 14 → 13 |
| Lei 14.182/2021 (Eletrobras) | 84 | 90 | 94 | 8 → 5 → 3 |
| Lei 14.300/2022 (micro e minigeração) | 88 | 92 | 94 | 6 → 4 → 3 |
| Lei 15.269/2025 | 70 | 70 | 70 | 67 → 48 → 42 |
| Decreto 2.335/1997 (estrutura da ANEEL) | 98 | 98 | 98 | 1 → 1 → 1 |
| Decreto 5.163/2004 (comercialização) | 86 | 86 | 86 | 7 → 7 → 7 |
| Decreto 7.246/2010 (sistemas isolados) | 86 | 86 | 86 | 7 → 7 → 7 |
| Decreto 10.946/2022 (eólica offshore) | 86 | 88 | 88 | 7 → 6 → 6 |
| Decreto 12.068/2024 | 78 | 82 | 82 | 11 → 9 → 9 |
| RN ANEEL 1.137/2025 | 88 | 88 | 88 | 6 → 6 → 6 |
| RN 1.137/2025 no DOU | 50 | 50 | 50 | 0 → 0 → 0 |
| REH ANEEL 3.348/2024 | 98 | 98 | 98 | 0 → 0 → 0 |
| REN ANEEL 846/2019 compilada | 85 | 85 | 85 | 3 → 3 → 3 |
| REN ANEEL 1.148/2026 | 72 | 72 | 72 | 7 → 7 → 7 |
| REN ANEEL 1.174/2026 compilada | 65 | 65 | 65 | 33 → 33 → 33 |

| Versão | Média | Abaixo de 70 | Anomalias de numeração |
| --- | ---: | ---: | ---: |
| Original | 77,8 | 2 | 493 |
| Autoria por caput | 78,5 | 2 | 437 |
| Vetado/revogado | 79,2 | 2 | 388 |

Sete leis continuam em 70 porque a penalidade de numeração tem teto de −30. Elas melhoraram nas
anomalias (Lei 15.269: 67 → 42; Lei 13.360: 52 → 33), mas a nota só se move abaixo de 15 anomalias.

## Mapa atual

| Documento | Fonte | Nota | Situação | Dispositivos | Cobertura | Principais alertas |
| --- | --- | ---: | --- | ---: | ---: | --- |
| RN 1.137/2025 no DOU | DOU · PDF | 50 | revisar extração | 1 | 0% | Texto não estruturado em dispositivos; sem segunda leitura confiável |
| REN ANEEL 1.174/2026 compilada | Leis.org (local) · PDF | 65 | revisar extração | 371 | 99% | 30 saltos, 1 repetição, 2 ordens invertidas; 47 de 361 dispositivos fora da segunda leitura |
| Lei 9.427/1996 (ANEEL) | Planalto · HTML | 70 | ok (no limite) | 180 | 100% | 6 saltos, 11 repetições (ex.: inciso IV → inciso VII) |
| Lei 9.478/1997 (política energética) | Planalto · HTML | 70 | ok (no limite) | 475 | 99% | 9 saltos, 18 repetições, 5 ordens invertidas |
| Lei 9.648/1998 | Planalto · HTML | 70 | ok (no limite) | 145 | 99% | 24 saltos, 3 repetições, 39 ordens invertidas (ex.: Art. 5 → Art. 17) |
| Lei 10.438/2002 (Proinfa, CDE) | Planalto · HTML | 70 | ok (no limite) | 289 | 99% | 8 saltos, 12 repetições, 5 ordens invertidas |
| Lei 10.848/2004 (comercialização) | Planalto · HTML | 70 | ok (no limite) | 364 | 99% | 17 saltos, 7 repetições, 3 ordens invertidas |
| Lei 12.783/2013 (renovação de concessões) | Planalto · HTML | 70 | ok (no limite) | 231 | 99% | 5 saltos, 10 repetições, 2 ordens invertidas |
| Lei 13.360/2016 | Planalto · HTML | 70 | ok (no limite) | 182 | 98% | 20 saltos, 13 repetições (ex.: § 6º → § 10) |
| Lei 13.848/2019 (agências reguladoras) | Planalto · HTML | 70 | ok (no limite) | 302 | 99% | 15 saltos, 1 ordem invertida (ex.: Art. 7º → Art. 20) |
| Lei 15.269/2025 | Planalto · HTML | 70 | ok (no limite) | 368 | 98% | 34 saltos, 5 repetições, 3 ordens invertidas (ex.: Art. 8º-A → Art. 15) |
| REN ANEEL 1.148/2026 | Leis.org (local) · PDF | 72 | ok | 75 | 95% | 21 de 59 dispositivos fora da segunda leitura; 3 saltos, 2 repetições, 2 ordens invertidas |
| Lei 14.120/2021 | Planalto · HTML | 74 | ok | 123 | 97% | 3 saltos, 9 repetições, 1 ordem invertida |
| Lei 8.987/1995 (concessões) | Planalto · HTML | 82 | ok | 167 | 99% | 7 saltos, 2 ordens invertidas (ex.: inciso III → inciso VII) |
| Decreto 12.068/2024 | Planalto · HTML | 82 | ok | 135 | 95% | 6 saltos, 3 ordens invertidas |
| REN ANEEL 846/2019 compilada | Leis.org (local) · PDF | 85 | ok | 551 | 98% | 114 de 484 dispositivos fora da segunda leitura; 2 repetições, 1 ordem invertida |
| Decreto 5.163/2004 (comercialização) | Planalto · HTML | 86 | ok | 373 | 99% | 7 repetições |
| Decreto 7.246/2010 (sistemas isolados) | Planalto · HTML | 86 | ok | 130 | 98% | 7 repetições |
| Lei 9.074/1995 (concessões e permissões) | Planalto · HTML | 88 | ok | 179 | 99% | 4 saltos, 2 ordens invertidas |
| Decreto 10.946/2022 (eólica offshore) | Planalto · HTML | 88 | ok | 108 | 96% | 6 saltos (ex.: inciso VI → inciso IX) |
| RN ANEEL 1.137/2025 | ANEEL · PDF | 88 | ok | 304 | 99% | 5 saltos, 1 ordem invertida (ex.: item 1 → item 23-A); 3 de 240 fora da segunda leitura |
| Lei 14.182/2021 (Eletrobras) | Planalto · HTML | 94 | ok | 224 | 99% | 2 repetições, 1 ordem invertida |
| Lei 14.300/2022 (micro e minigeração) | Planalto · HTML | 94 | ok | 157 | 98% | 1 salto, 1 repetição, 1 ordem invertida |
| Decreto 2.335/1997 (estrutura da ANEEL) | Planalto · HTML | 98 | ok | 257 | 99% | 1 ordem invertida |
| REH ANEEL 3.348/2024 | ISA (cópia) · PDF | 98 | ok | 30 | 81% | 1 de 24 fora da segunda leitura |
| Lei 9.991/2000 (P&D e eficiência) | Planalto · HTML | 100 | ok | 54 | 100% | nenhum |

## Padrões encontrados

1. **Autoria dos blocos de alteração (corrigido).** Na Lei 15.269/2025, todos os blocos de nova
   redação ficavam com a Lei 9.074 como norma-alvo, inclusive os dos Arts. 5º, 6º e 7º, que alteram
   as Leis 9.648, 9.991 e 10.438. Agora cada bloco pertence à lei citada no caput do artigo que o
   abre: os dispositivos citados se distribuem por 15 leis.
2. **Vetados e revogados (corrigido).** "Arts. 2º a 4º (VETADOS)" e "(Revogado pela Lei …)" seguido
   da nova redação de mesmo número não contam mais como erro.
3. **Inciso fora do início da linha (aberto).** No Planalto, alguns incisos vêm no meio do parágrafo
   e não viram dispositivo: Lei 9.427, incisos V e VI (o salto IV → VII), e Decreto 10.946, inciso
   VIII. É um defeito de extração.
4. **Saltos naturais em blocos de nova redação (aberto, não é erro).** Um bloco que altera só os
   Arts. 7º e 20 de outra lei salta de 7 para 20 (Lei 13.848). O invariante ainda acusa. Para
   resolver, a sequência deveria ser conferida só fora dos blocos citados; essa mudança espera
   decisão.
5. **Compilações do Leis.org.** A segunda leitura (pypdfium2) não confirma de 15% a 36% dos
   dispositivos, porque o selo "Art. N" é lido fora de lugar. As versões oficiais da ANEEL devem
   substituir essas cópias.
6. **Página do DOU.** A diagramação em colunas não vira dispositivos (0% estruturado) e a segunda
   leitura não é confiável. O extrator não está preparado para o PDF do DOU.

## Limites desta medição

- Os pesos da nota são provisórios: servem para comparar documentos, não como certificação.
- A ausência de alerta não prova extração correta: os invariantes pegam erros de estrutura, não de
  interpretação.
- Os mapas das etapas 1 e 2 foram gravados com o código de cada etapa. O script de comparação só lê
  esses arquivos e não os refaz.
