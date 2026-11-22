# Evidências e estado da entrega

Registro de verificações da aplicação. As seções abaixo de "Implementado e exercitado" são de
05/11 e 10/11/2026 e ficam como histórico; o estado atual está logo a seguir.

## Estado em 20/11/2026

| Verificação | Resultado |
| --- | --- |
| Testes Python | 458 aprovados (Windows local); no CI, nos três sistemas |
| Testes do site | 30 aprovados; build e pré-renderização de `/` e `/demo` conferidos |
| Gabarito (29 casos, sem revisão de especialista) | 29/29; trava `tests/baseline/metricas_v2.json` passa |
| Reprodutibilidade do export | `python scripts/exportar_plano_demo.py --verificar` (CI) |

O quadro de 17/11/2026 abaixo é histórico (19/20 no gabarito, 270 testes, normas oficiais ainda
ausentes); as normas oficiais estão versionadas em `tests/fontes_impacto/`.

## Estado em 17/11/2026 (histórico)

| Verificação | Resultado | Onde |
| --- | --- | --- |
| Testes Python | 270 aprovados no Windows local (com as cópias locais dos PDFs da REN 846, 1.148 e 1.174). No CI, 4 testes pulam sem esses PDFs: no último CI da main (`d9036bf`), 264 aprovados e 4 pulados em cada sistema | `python -m pytest`; CI `checks` |
| Testes do site | 7 aprovados; build e pré-renderização de `/` e `/demo` conferidos | `landing/`: `npm test`, `npm run build` |
| Gabarito (20 casos, sem revisão de especialista) | 19/20; obrigação 11/11, prazo 8/8, autoria 10/10, vigência 4/4, revogação 2/2, não obrigação 2/2, remissão 0/1 (G09) | [avaliacao.md](avaliacao.md) |
| Citações | Falsamente verificadas: 0 nas três normas. Encontradas na fonte: 252/254 (RN 1.137), 31/31 (REH 3.348), 145/145 (Decreto 12.068) | `scripts/avaliar.py` |
| Trava de não regressão | Passa contra `tests/baseline/metricas_v2.json` | CI, nos três sistemas |
| Lint, formatação e padrões de segredo | Passam | CI |
| CI remoto | Ubuntu, Windows e macOS (Intel) em todo push e PR, incluindo a trava e os testes do site | `.github/workflows/ci.yml` |

Mudanças em relação às pendências de 05/11 (o texto original segue abaixo, sem edição):

- **Retry-After:** implementado. O erro 429 é repetido até 3 vezes respeitando o cabeçalho
  (`athenix/llm.py`, `_espera`), com testes em `tests/test_modos_ia.py` e
  `tests/test_proposals_ai.py`. Limites de tempo/memória em processo isolado e PDFs patológicos
  continuam pendentes.
- **CI remoto:** exercitado (três sistemas).
- **Composição Docker com PostgreSQL:** segundo a revisão independente de 17/11/2026, `docker
  compose` com PostgreSQL rodou. **Não foi reexecutado neste registro** (Docker indisponível nesta
  máquina). Até 17/11 o `compose.yaml` não repassava `ATHENIX_AI_MODE`, as variáveis do Azure, o
  teto de custo nem `ATHENIX_HTTPS`; isso foi corrigido e é conferido por `tests/test_infra.py`.
  Primeiro acesso no Docker: `docker compose exec web python -m athenix create-user <usuario>`
  (README), porque `/setup` só aceita acesso local.
- **Imagem de produção:** instala só `requirements.lock`; pytest, hypothesis e ruff ficam em
  `requirements-dev.lock`.
- **Aviso de depreciação do cliente de testes:** resolvido com `httpx2` nas dependências de
  desenvolvimento (o produto continua usando `httpx`).
- **IA real:** houve execuções pagas autorizadas (ensaio regras × IA, títulos), registradas em
  [REVISAO_ENSAIO_2026-11-17.md](REVISAO_ENSAIO_2026-11-17.md). A frase "nenhuma chamada real" das
  seções antigas não vale mais para o repositório como um todo.
- **PDF oficial da norma:** a RN 1.137/2025 está em `tests/norma_poc/`. Os PDFs da REN 846
  compilada, REN 1.148 e REN 1.174 continuam sem versão oficial no repositório (as cópias locais
  são de terceiro e não podem ser publicadas).

## Implementado e exercitado

| Capacidade | Código / evidência |
| --- | --- |
| Recebimento PDF/HTML, origem, papel, hash e reenvio idempotente | `athenix/services.py`, `structure.py`; testes de upload, concorrência, PDF sintético, arquivo corrompido e igualdade de recortes |
| Originais imutáveis na mesma transação dos metadados | `athenix/db.py`; triggers para UPDATE/DELETE e testes de integridade |
| Estrutura, blocos citados, páginas, links, datas e avisos | `athenix/structure.py`; casos sintéticos novos, sem prova sobre a norma de referência |
| Regras, âncoras e normalização com mapeamento ao original | `proposals.py`, `evidence.py`; propriedade Unicode, alteração de palavras, outra unidade, ambiguidade e verificador independente |
| Prazos determinísticos, herança, esclarecimento e eventos | `temporal.py`; datas sintéticas, fim de mês, calendário ausente e marcos independentes |
| Contestações e faixas de incerteza | `proposals.py`; modalidades, definições, sujeitos, condições, exceções, dependências, agrupamento, quantidade e marco |
| Contestações humanas ancoradas e associação de dependências | `services.py`; trecho obrigatório; confirmação não controlada pelo cliente; obtido distinto de interpretado |
| Revisão técnica, travas, correção, resolução e confirmação de prazos | `auth.py`, `services.py`; identidade da sessão, justificativa, versões anteriores preservadas e concorrência otimista |
| API autenticada, CSRF, escape de HTML e CSV | `app.py`; testes HTTP e ensaio Chromium |
| Matriz, timeline, riscos, evidência realçada, histórico e exportação | templates e assets originais; capturas desktop/mobile e fluxo automatizado |
| Adaptador de IA, preço/teto, resposta bruta, cache, trava e reprodução | `llm.py`, `services.py`; apenas contratos com provedores falsos; nenhuma chamada real |
| Migrações aditivas e recuperação conservadora de jobs | Alembic 0001/0002; teste de igualdade de schema, downgrade recusado, pagamento interrompido não repetido |
| Trilha e artefato determinístico de execução | `db.py`, `reproduction.py`; encadeamento, adulteração plantada e conteúdo separado de metadados operacionais |

## Verificações registradas

Em 10/11/2026: 121 testes aprovados. Avaliação contra gabarito de 20 casos em 3 atos reais (RN 1.137/2025, REH 3.348/2024 e Decreto 12.068/2024): 6/20 casos corretos no código recebido, 13/20 após as correções. Citação só é verificada se existir numa segunda leitura independente da fonte; âncoras falsamente verificadas caíram de 3, 1 e 124 para zero. Texto de OCR, tabelas e fórmulas não confirmados ficam pendentes. O gabarito ainda não foi revisado por especialista. Método, versões e limites em [avaliacao.md](avaliacao.md). Pendente no HTML: quebra de linha em cada tag.

O resultado final da suíte está em `artifacts/tests.xml`: 80 testes aprovados, sem falhas, erros ou testes ignorados. O resultado do navegador está em `artifacts/browser-qa.json`, com conjunto rotulado `synthetic_new`. O relatório final registra seis candidatos, nove âncoras verificadas conferidas (incluindo a nova versão após correção), zero falhas no recálculo, duas versões preservadas e nenhum erro JavaScript no roteiro. O encerramento do servidor e a remoção do banco temporário também passaram. Isso não mede precisão jurídica, recall nem desempenho da IA.

`artifacts/verification.json` consolida contagens do JUnit, ambiente e hashes dos arquivos de código com LF normalizado. A suíte emite um aviso de depreciação do cliente de testes Starlette/httpx; ele está registrado e não é falha da aplicação.

Capturas em `artifacts/dashboard-desktop.png`, `dashboard-mobile.png`, `matrix-desktop.png` e `evidence-desktop.png`. O QA do navegador usa banco descartável e não semeia o ambiente principal. O inventário de terceiros está em `terceiros.json`. Lint, formatação e verificação limitada de padrões de segredos são executados localmente; a ausência de padrões não é garantia de ausência de qualquer segredo.

O FAQ oficial foi obtido por HTTPS, após robots.txt HTTP 200 e permissão explícita de coleta para a URL. A origem, instante da aquisição e hashes do arquivo/robots estão em `public_source.json`; bytes preservados em `.local/public/`. `artifacts/public-faq-check.json` registra a verificação: 32 perguntas, 28 candidatos por regras, 30 âncoras verificadas e zero falhas no recálculo, recortes íntegros em todas as unidades e zero datas finais sem norma-alvo vinculada. Isso valida comportamento sobre um esclarecimento real, sem medir correção jurídica. O comando `python scripts/check_public_faq.py` repete a verificação sem rede.

## Pendências que impedem declarar o MVP integralmente aceito

- PDF oficial da norma e seus anexos ainda não obtidos; estrutura e prazos que dependem da REN não foram verificados. A aquisição e verificação do FAQ acima não os substituem.
- PostgreSQL real, execução da composição e CI remoto: não exercitados.
- Cota, modelo, preço corrente e execução real de IA: não verificados; contratos simulados não comprovam o funcionamento do serviço real.
- Retentativas programadas com Retry-After, limites de tempo/memória em isolamento de processo e processamento seguro de PDFs patológicos: endurecimento pendente.
- Algoritmo de segmentação não foi certificado na norma real; não há promessa de número de artigos ou cobertura estrutural fora do corpus sintético.
- Versões textuais iguais preservam proveniências e extrações separadas; a deduplicação física do texto canônico entre arquivos ainda é parcial.
- Fundamentação cruzada entre várias normas, diff de versões, calendário versionado, múltiplas amostras com divergência e avaliação independente: pendentes.
- Revisão dos mecanismos críticos por outra pessoa, revisão jurídica, identidade profissional verificada e dois ensaios oficiais cronometrados: não realizados.
- A cobertura integral dos critérios de aceitação ainda não foi medida. Contagem de testes executáveis não equivale à cobertura de requisitos.
- Licença: PolyForm Noncommercial License 1.0.0 (`LICENSE`), com o aviso "Required Notice: Copyright (c) 2026 Athenix". Uso comercial depende de autorização do titular.

Os requisitos completos continuam na matriz. Uma linha implementada parcialmente não é considerada encerrada por existir uma tela ou por passar apenas no corpus sintético.
