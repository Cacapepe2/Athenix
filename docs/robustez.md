# Robustez da extração: mapa de problemas

Registro de 17/11/2026. Os invariantes de `athenix/saude.py` foram aplicados a 26 normas reais. Os
invariantes são regras gerais, sem nada específico de uma norma:
- numeração em sequência por nível;
- todo dispositivo presente na segunda leitura da fonte;
- nenhum dispositivo começando no meio de palavra;
- cobertura mínima do texto estruturado;
- páginas sem texto.

Nota de 0 a 100; abaixo de 70, "revisar extração". **Nada foi corrigido ainda:** este é o mapa para
decidir as correções.

## Corpus

- **Planalto (HTML, acesso permitido):** 20 leis e decretos do setor elétrico. 16 foram baixados em
  17/11/2026 para uma pasta local, fora do repositório; 4 já estão no repositório.
- **ANEEL (PDF):** a RN 1.137/2025 (repositório).
- **DOU (PDF):** a página do DOU com a RN 1.137/2025 (repositório).
- **Cópias de terceiro:** a REH 3.348 (cópia da ISA, repositório) e as REN 846, 1.148 e 1.174
  (compilações do Leis.org, só locais).
- **Não obtidos:** os PDFs oficiais da ANEEL (`www2.aneel.gov.br/cedoc/`) responderam **403 (acesso
  automatizado bloqueado)** para REN 846/2019, REN 1.000/2021, REN 956/2021 e REN 1.148/2026. Não
  houve nova tentativa nem contorno. Esses PDFs precisam ser fornecidos pelo fundador.

## Tabela

| Documento | Fonte | SHA-256 (12) | Nota | Situação | Dispositivos | Cobertura | Principais alertas |
| --- | --- | --- | ---: | --- | ---: | ---: | --- |
| RN 1.137/2025 no DOU | DOU · PDF | ca2dbbb8ffda | 50 | revisar extração | 1 | 0% | Texto não estruturado em dispositivos; sem segunda leitura confiável |
| REN 1.174/2026 compilada | Leis.org (local) · PDF | a2f89f9e431e | 65 | revisar extração | 371 | 99% | 30 saltos, 1 repetição, 2 ordens invertidas (ex.: Art. 1º → Art. 42); 47 de 361 dispositivos fora da segunda leitura |
| Lei 9.427/1996 | Planalto · HTML | ff948e3442ed | 70 | ok (no limite) | 180 | 100% | 7 saltos, 11 repetições (ex.: inciso IV → inciso VII) |
| Lei 9.478/1997 | Planalto · HTML | 75863c37450a | 70 | ok (no limite) | 475 | 99% | 15 saltos, 24 repetições, 5 ordens invertidas |
| Lei 9.648/1998 | Planalto · HTML | 42e8c5f486f6 | 70 | ok (no limite) | 145 | 99% | 27 saltos, 3 repetições, 39 ordens invertidas (ex.: Art. 5 → Art. 17) |
| Lei 10.438/2002 | Planalto · HTML | 0ceb644391b0 | 70 | ok (no limite) | 289 | 99% | 9 saltos, 14 repetições, 6 ordens invertidas |
| Lei 10.848/2004 | Planalto · HTML | 63ad9c363c88 | 70 | ok (no limite) | 364 | 99% | 20 saltos, 7 repetições, 3 ordens invertidas |
| Lei 12.783/2013 | Planalto · HTML | a3e96c6f5952 | 70 | ok (no limite) | 231 | 99% | 8 saltos, 12 repetições, 2 ordens invertidas |
| Lei 13.360/2016 | Planalto · HTML | e076f446a314 | 70 | ok (no limite) | 182 | 98% | 27 saltos, 17 repetições, 8 ordens invertidas |
| Lei 13.848/2019 | Planalto · HTML | e7188b1953f0 | 70 | ok (no limite) | 302 | 99% | 17 saltos, 7 ordens invertidas |
| Lei 14.120/2021 | Planalto · HTML | 0590ff4e5908 | 70 | ok (no limite) | 123 | 97% | 6 saltos, 9 repetições, 6 ordens invertidas |
| Lei 15.269/2025 | Planalto · HTML | acd97004cd30 | 70 | ok (no limite) | 368 | 98% | 43 saltos, 7 repetições, 17 ordens invertidas (ex.: Art. 4º → Art. 7º) |
| REN 1.148/2026 | Leis.org (local) · PDF | 00f8c4a41605 | 72 | ok | 75 | 95% | 21 de 59 dispositivos fora da segunda leitura; 3 saltos, 2 repetições |
| Decreto 12.068/2024 | Planalto · HTML | 74f0e0d54568 | 78 | ok | 135 | 95% | 7 saltos, 4 ordens invertidas (ex.: Art. 1º → Art. 3º) |
| Lei 8.987/1995 | Planalto · HTML | 481e8c87a4b0 | 80 | ok | 167 | 99% | 8 saltos, 2 ordens invertidas (ex.: § 2 → § 5º) |
| Lei 9.074/1995 | Planalto · HTML | b3d3032dc59f | 82 | ok | 179 | 99% | 6 saltos, 1 repetição, 2 ordens invertidas |
| Lei 14.182/2021 | Planalto · HTML | ceb8da3c5f9b | 84 | ok | 224 | 99% | 3 saltos, 3 repetições, 2 ordens invertidas (ex.: § 12 → § 14) |
| REN 846/2019 compilada | Leis.org (local) · PDF | d8b6fae9322f | 85 | ok | 551 | 98% | 114 de 484 dispositivos fora da segunda leitura; 2 repetições |
| Decreto 5.163/2004 | Planalto · HTML | 647b12722333 | 86 | ok | 373 | 99% | 7 repetições (ex.: inciso I repetido) |
| Decreto 7.246/2010 | Planalto · HTML | 97bb2c79637e | 86 | ok | 130 | 98% | 7 repetições (ex.: inciso II repetido) |
| Decreto 10.946/2022 | Planalto · HTML | 0a034217b79c | 86 | ok | 108 | 96% | 7 saltos (ex.: inciso II → inciso IV) |
| Lei 14.300/2022 | Planalto · HTML | 1ea82253b42a | 88 | ok | 157 | 98% | 2 saltos, 2 repetições, 2 ordens invertidas |
| RN 1.137/2025 | ANEEL · PDF | 4a581592e981 | 88 | ok | 304 | 99% | 5 saltos, 1 ordem invertida (ex.: item 1 → item 23-A); 3 de 240 fora da segunda leitura |
| Lei 9.991/2000 | Planalto · HTML | d9cebcc3ce08 | 96 | ok | 54 | 100% | 1 salto, 1 repetição |
| Decreto 2.335/1997 | Planalto · HTML | 0873efbb7262 | 98 | ok | 257 | 99% | 1 ordem invertida |
| REH 3.348/2024 | ISA (cópia) · PDF | c074ee9a23af | 98 | ok | 30 | 81% | 1 de 24 fora da segunda leitura |

Média 78. Dois documentos abaixo do limite; 10 no limite de penalidade da numeração (-30).

## Padrões encontrados

1. **Blocos de alteração com norma-alvo errada.** Confirmado na Lei 15.269/2025: os Arts. 4º a 7º
   da própria lei foram lidos corretamente, mas **todos** os blocos de nova redação ficaram com a Lei
   9.074 como norma-alvo. Isso inclui os blocos dos Arts. 5º, 6º e 7º, que alteram as Leis 9.648,
   9.991 e 10.438. A norma-alvo não é atualizada a cada artigo que altera outra lei. Assim, artigos
   de leis diferentes viram uma só sequência, com saltos e ordem invertida. O efeito vai além da
   numeração: a **autoria** do dispositivo citado fica errada. Afeta as leis que alteram várias
   outras (15.269, 9.648, 13.360, 14.120, 10.438, 10.848). É provavelmente a mesma causa do "item 1 →
   item 23-A" na RN 1.137, cujo Anexo traz nova redação de itens de outra resolução.
2. **Textos compilados do Planalto.** Há incisos e artigos ausentes ou repetidos em leis compiladas
   (Lei 9.427, inciso IV → VII; repetições na Lei 9.478). Hipótese a conferir: dispositivos revogados
   marcados só com a nota "(Revogado)", sem `<strike>`, e redações antigas sem marcação.
3. **Compilações do Leis.org.** A segunda leitura (pypdfium2) não confirma de 15% a 36% dos
   dispositivos. Esse risco já estava registrado: o selo "Art. N" é lido fora de lugar. As versões
   oficiais da ANEEL devem substituir essas cópias.
4. **Página do DOU.** A diagramação em colunas não vira dispositivos (0% estruturado) e a segunda
   leitura não é confiável. O extrator não está preparado para o PDF do DOU.
5. **Documentos bem lidos:** Decreto 2.335, Lei 9.991, REH 3.348, RN 1.137 e Lei 14.300 (88 a 98).

## Limites desta medição

- Os pesos da nota são provisórios; servem para comparar documentos, não como certificação.
- A ausência de alerta não prova extração correta: os invariantes pegam erros de estrutura, não de
  interpretação.
- Os arquivos do Planalto baixados não foram versionados. Se forem entrar no repositório como corpus
  de teste (são atos oficiais), isso fica para decisão do fundador.
