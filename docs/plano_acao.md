# Plano de ação de uma norma

Status: **em validação** (17/11/2026). Usado na demo `/demo` do site; não alterou o cálculo do produto.

`athenix/plano.py` reorganiza o resultado de `impacto.avaliar` para quem decide: resumo, temas,
linha do tempo, três decisões e o porquê de cada obrigação. Não calcula multa nova.

## Regras

| Parte | Como é feita | Fonte |
|---|---|---|
| Obrigações | As aplicáveis ao segmento do perfil (distribuição na demo) | `impacto.avaliar` |
| Tema | Seção da própria norma; o título da seção é conferido literalmente no texto. Disposições transitórias e itens sem seção vão para o tema do primeiro assunto nomeado (padrão em `plano_temas.json`), com o termo registrado | `athenix/data/plano_temas.json` |
| Prazo | Situação pela data do motor temporal: vencida, próximos 90 dias, depois, recorrente, depende de evento, sem prazo. Data provisória até confirmação humana | `impacto.urgencia` |
| Enquadramento e exposição | Só os que o produto já calcula (texto da obrigação nomeia o instrumento da infração). Faixa por infração, de advertência até o teto do grupo, limitado pelo teto legal | `impacto.multa` |
| Ordem dos temas | Ver `ORDEM_PLANO`: atendido vai para o fim; exposição máxima por infração do tema no porte escolhido (a maior, nunca a soma; sem enquadramento depois); prazo vencido antes de a vencer; número de obrigações. Valor provável não entra (não estimável) | `plano.ordenar_temas` e `plano.exposicao_pct`, repetidas em `landing/src/content/plano.ts` e testadas contra `ordem_inicial` |
| Cenário preliminar | Sugestões de enquadramento da IA (cache, aguardam confirmação) entram no valor do tema SÓ neste modo (padrão na demo), hachuradas e rotuladas; "só confirmados" volta ao cálculo anterior. O valor passa pelo mesmo motor (`impacto.multa`) com o grupo sugerido | `plano._faixa_preliminar`, `exposicaoTema` |
| Referência de escala | Mediana (≈ R$ 10,3 mi) e maior (≈ R$ 48,7 mi) auto de infração de distribuição, n = 21; é valor do auto inteiro, não por infração nem por obrigação; sem empresa | `athenix/data/referencia_escala.json`, `docs/valor_provavel_csv.md` |
| Análise regulatória preliminar | Por obrigação prioritária do tema: trecho literal, tipo (só definitivo se regra e IA concordam; sem IA no cache, "só pela regra"), ideias de cumprimento e evidências do manual (sugestão), dependência de ato da ANEEL no texto (citação verificada) e prática conhecida por tema (referência pública, sem citação da norma). Selo: não constitui parecer jurídico | `athenix/analise.py` |
| Decisões da semana | Os 3 primeiros temas da ordem (tema, R$ por infração, situação do prazo); item secundário: confirmar enquadramentos libera o cálculo de N temas | `plano.decisoes`, `decisoesDaSemana` |
| Como provar | Sugestão da Athenix por palavras do dever (sítio eletrônico, registro, plano, envio à ANEEL…), sempre com o trecho literal que a motivou. Não é exigência normativa | `plano_temas.json`, `evidencias` |

## IA (cache, sem chamada)

`athenix/data/ia_cache_rn1137.json` é gerado por `python scripts/exportar_plano_demo.py --importar-ia artifacts/revisao-ensaio`
a partir do cache do ensaio de 17/11/2026 (gpt-5-mini, reasoning medium). Guarda só as sugestões
processadas e o hash dos arquivos de origem; nenhuma resposta bruta.

- **Títulos:** aplicados só sem alerta de sentido, com verbo no início, até 85 caracteres e citação
  literal presente no texto (38 de 42). Os 4 com alerta ficam com o título por regras e estão
  listados em `docs/SPRINT_2026-11-17.md`. Na tela, um ícone marca o título resumido com IA.
- **Enquadramento:** só a sugestão principal não condicional e não genérica (106 de 110), mostrada
  como "Interpretação da IA · aguarda revisão humana", com o trecho da infração do catálogo da
  REN 846. Nunca entra na faixa, no grupo ou na ordem. 23 dependem da dúvida D1 e dizem isso.

## Gerar

```powershell
.\.venv\Scripts\python.exe scripts/exportar_plano_demo.py   # grava landing/src/content/plano-rn1137.json
```

## Limites

- Os temas valem para a estrutura da RN 1.137 (seções do Anexo IV da RN 956 e da própria norma).
  Outra norma precisa do seu `plano_temas.json`; um título de seção ausente interrompe a exportação.
- O diagnóstico ("já temos / parcial / não temos") fica só no navegador e não é validado.
- A área responsável (Operação, Regulatório, Atendimento, TI) não é sugerida: o texto da norma não a
  indica de forma direta, e um palpite seria interpretação sem fonte.
