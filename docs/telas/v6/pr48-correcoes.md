# PR #48 — vencidas, data da executiva e sandbox

Conferência em 22/11/2026 na branch `fix/auditoria-m1-m2-a2`. Correções por regras e leitura das
fontes versionadas; nenhuma chamada paga de IA. Sem merge.

## Contagens e transição

| Norma | Deveres na contagem principal | Condicionais separados | Vencidas (N) | Detalhes das vencidas (M) |
| --- | ---: | ---: | ---: | ---: |
| RN 1.137/2025 | 147 (antes 153) | 0 | 8 (antes 14) | 11 |
| REN 1.174/2026 | 75 (antes 85) | 10 | 0 | 0 |

Na RN 1.137, os incisos I–V do Art. 13 apenas fixam o prazo dos itens que citam; passam a regras de
transição em Outros dispositivos. Os itens conservam a data, o dispositivo e a citação literal do
inciso. O Art. 18 é vigência geral, também em Outros dispositivos. O inciso VI mantém o dever próprio
de apuração do DISE, sem item correspondente no texto. Os testes anotam o motivo das novas contagens.
O detalhe do prazo no plano completo mostra a citação literal do inciso junto à obrigação do item.

As oito obrigações principais vencidas são:

| Obrigação | Prazo de adequação | Fonte do prazo |
| --- | --- | --- |
| item 103 | 28/01/2026 | Art. 13, I |
| item 108 | 28/01/2026 | Art. 13, I |
| item 148 | 28/01/2026 | Art. 13, I |
| item 104 | 28/04/2026 | Art. 13, II |
| item 105 | 28/04/2026 | Art. 13, III |
| item 106 | 28/04/2026 | Art. 13, IV |
| item 107 | 28/04/2026 | Art. 13, V |
| Art. 13, VI (DISE) | 28/04/2026 | próprio inciso; esclarecimento oficial já registrado |

São 19 registros vencidos no export: 8 principais e 11 alíneas de detalhe do item 107. A contagem
principal agrupa os registros pelo dispositivo, inclusive os dois trechos extraídos do item 106.
O prazo de comunicação por evento do item 105 continua presente junto ao marco de adequação.

A regra não enumera normas, artigos nem itens no código: usa as referências lidas pela transição,
os alvos encontrados e a remissão explícita do inciso. Referência ausente e dever adicional expresso
não são descartados. Os Arts. 14 e 15 da RN mantêm os deveres próprios por evento.

Na REN 1.174, os Arts. 16 e 18 já são marcos de adequação e vigência dos dispositivos citados,
sem dever principal adicional. Permanece o dever próprio de isonomia do Art. 16, parágrafo único.
Os testes com o HTML real mantêm adequação em 03/05/2027 e 04/11/2027 e vigência em 02/02/2027 e
03/05/2027, conforme cada remissão.

## Art. 11 da REN 1.174: texto e decisão

Fonte: [`tests/fontes_impacto/dou/dou_ren20261174.html`](../../../tests/fontes_impacto/dou/dou_ren20261174.html),
linha 2710. SHA-256: `fe1f0608ff63945912f5a37de9ffa612cbdc714cf77c231dc7df2fb4d6361507`.

> Art. 11. As distribuidoras podem desenvolver Sandbox Regulatório para emissão de fatura unificada pelo agente comercializador para unidade consumidora livre e especial, contendo a cobrança da distribuidora e do comercializador, observadas as seguintes disposições:

Sujeito do caput: **As distribuidoras**. Modalidade: **faculdade**, expressa por **podem**.

> I - a distribuidora deve apresentar à ANEEL, previamente ao início, a proposta do Sandbox contendo, no mínimo:

Sujeito do inciso I: **a distribuidora**; modalidade **dever**, subordinado à opção do caput.

> VIII - a partir da autorização do Sandbox até o fim da vigência devem ser encaminhados à ANEEL, semestralmente, relatórios informativos contemplando o acompanhamento, os resultados, as dificuldades enfrentadas e as soluções adotadas no período.

O inciso VIII usa obrigação na voz passiva (**devem ser encaminhados**), com relatórios semestrais
**a partir da autorização do Sandbox**. A leitura não transforma a faculdade de participar em dever.

Decisão: dever dentro de faculdade da distribuidora, inclusive em ancestral acima do inciso,
é **condicional**. Os nove registros do Art. 11 anteriormente na lista principal (dois trechos do
inciso I e cinco alíneas, divulgação do inciso III e relatórios do VIII) aparecem em Outros dispositivos
como **“Dever condicional: se aderir ao sandbox”**, com o texto completo do caput e seu dispositivo.
Saem do top 5, dos temas que alimentam a exposição principal e da agenda principal.

A mesma regra alcança o Art. 166, § 6º, I, da REN 1.000 alterada pela REN 1.174: a distribuidora
**pode praticar prazos menores**, sob condições. Esse décimo registro também fica separado como
condicional. Portanto a REN conserva **85 registros de dever**, sendo **75 principais e 10 condicionais**.
A classificação continua sujeita à revisão humana.

## Layout e capturas

A data completa foi preservada. Seu tamanho usa exclusivamente o novo token
`--tamanho-data-executiva: 48px` de `landing/src/styles/tokens.css`, sem fonte ou cor adicional.

Chrome via Playwright, build local de produção, fontes carregadas, 1280×900 e 390×844, escala 1.
Asserções verificaram os valores 8 e 02/02/2027, os limites do texto no cartão, ausência de rolagem
horizontal e de erros JavaScript. Também verificaram os nove rótulos condicionais do sandbox.

| Largura | Largura do cartão da data | Largura do texto da data | Resultado |
| ---: | ---: | ---: | --- |
| 1280 px | 357,34 px | 269,75 px | cabe no cartão |
| 390 px | 358 px | 269,75 px | cabe no cartão |

- [REN 1.174 — 1280 px](pr48-executiva-ren1174-1280.png)
- [REN 1.174 — 390 px](pr48-executiva-ren1174-390.png)
- [RN 1.137 — 1280 px](pr48-executiva-rn1137-1280.png)
- [RN 1.137 — 390 px](pr48-executiva-rn1137-390.png)
- [Sandbox em Outros dispositivos](pr48-sandbox-condicional-1280.png)
- [Item 103 com o prazo e a citação do Art. 13, I](pr48-item103-fonte-prazo-1280.png)

## Verificação

- Trava vigente `tests/baseline/metricas_v2.json`: 29/29, sem regressão; linha de base preservada.
- Pytest: 574 aprovados, 6 pulados por dependerem de `.local/` (sem acesso a esse acervo).
- Site: 116 testes e build com TypeScript, pré-renderização e verificação do HTML aprovados.
- `exportar_plano_demo.py --verificar`: ambas as normas reproduzidas.
- Ruff e `check_secrets`: aprovados.
- CI dos três sistemas: conferir os checks vinculados ao commit no [PR #48](https://github.com/Cacapepe2/Athenix/pull/48).

Não acessados: `.env` e `.local/`. Os testes que exigem acervo privado local são pulados, com
proteção temporária externa ao repositório que bloqueia sua leitura. O aviso já existente de chunk
grande no build permanece; não foi medida performance móvel. Sem merge ou deploy em produção.
