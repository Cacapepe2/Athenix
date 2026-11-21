# Contexto da Athenix (para agentes)

Leia isto primeiro e depois só o que a tarefa exigir. Não varra o repositório.

## O que é
Inteligência regulatória B2B para normas da ANEEL, começando por distribuição e transmissão de
energia. Lê a norma, extrai obrigações **por regras** (não por IA), cita o dispositivo com trecho
verificado na fonte, calcula prazos e o teto de multa (REN 846, grupos I–V, até 2% da ROL; teto legal
3%). A IA só **sugere** (enquadramento, título curto). A sugestão aparece marcada como
"Interpretação da IA · aguarda revisão humana" e fica fora do cálculo confirmado. Exceção decidida
pelo fundador (18/11/2026): no **cenário preliminar** da `/demo` e do relatório-piloto, as sugestões
entram no valor por tema, sempre marcadas ("sugerido", barra hachurada); no modo **só identificados no texto**
vale a regra antiga (só o enquadramento que o texto da obrigação nomeia). No empate de R$, o
identificado no texto vem antes do sugerido. "Confirmado" fica reservado à revisão humana, que ainda não existe. É um MVP técnico, ainda não validado comercialmente.

## Estado (20/11/2026)
- `main` em `74e0fb3` (#36 a #39 mergeados); trabalho em curso na branch `sprint/demo-executiva`.
  CI verde em Ubuntu, Windows e macOS (458 testes Python, 30 do site). Gabarito 20/20, trava ok.
- `/demo` completa (plano por tema, cenário preliminar x só identificados no texto, diagnóstico
  gerado no site, análise regulatória preliminar). A contagem principal é só de **deveres da
  distribuidora** na RN 1.137 (155); faculdades, direitos de terceiros e competências da ANEEL (12)
  ficam em "Outros dispositivos relevantes". Cada infração citada traz fonte, SHA-256 e origem da
  redação, e o export relê o arquivo para conferir o trecho. As duas redações do art. 11, XXIII
  aparecem com vigência e estado (a futura é INCERTA).
- Reprodutibilidade: o JSON da demo tem ids estáveis (chave do texto) e
  `python scripts/exportar_plano_demo.py --verificar` (também no CI) compara o export regenerado com o
  versionado, exceto `commit_origem` e `gerado_em` (`--data` e `--commit` os tornam controláveis).
- **Página executiva** `/demo/executivo` (a landing leva a ela): três números (exposição por infração,
  quanto cai se regularizar antes da fiscalização, prazos), as 5 obrigações para olhar primeiro e a
  referência do setor, em linguagem de negócio ("infração grave (Grupo IV)"; mapeamento em
  `landing/src/content/gravidade.ts`). Abre duas normas, ambas pelo mesmo motor: RN 1.137/2025 e
  **REN 1.174/2026** (abertura do mercado livre; 80 deveres da distribuidora, 1 com prazo e 2 recorrentes; enquadramento
  só por sugestão de IA, marcada, `docs/enquadramento_ia_ren1174.md`). Sem enquadramento não há valor:
  nada de teto da escala como "pior caso". A página completa `/demo?norma=ren1174` mostra a segunda norma.
- **Comando único:** `python -m athenix processar <arquivo> --agente distribuidora --saida <json>` (do
  PDF/HTML oficial ao JSON do plano, sem IA nem rede; saídas em `docs/telas/executivo/comando_*.txt`).
- Renúncia ao recurso: REN 846, **art. 38, § 2º** (redução de 25%; não é atenuante do art. 24).
- Progresso do sprint em curso: `.review/PROGRESSO.md` (fora do git). Pendências do fundador:
  `docs/SPRINT_2026-11-17.md` §5 (histórico).

## Regras
- Nunca inventar obrigação, citação ou dispositivo. Todo parâmetro precisa de documento, artigo,
  trecho e hash, nada de valor de memória.
- Separar texto normativo de interpretação da IA e manter a revisão humana. Não confirmar
  enquadramento, título ou obrigação em nome de uma pessoa.
- Nenhuma chamada paga de IA, só respostas em cache. Não ler, imprimir nem registrar o `.env`,
  chaves ou endpoint.
- Não contornar bloqueios da ANEEL ou do DOU. Não publicar PDFs do Leis.org nem respostas brutas
  de IA. Não autorizar conectores ou MCP.
- Nada de nome de empresa real em valores de multa na demo pública.
- A produção (`athenix-two.vercel.app`) não muda sem o fundador. Mudança em `landing/` ou na demo
  fica em PR com prévia, sem merge.
- Git: uma branch por bloco, sempre com PR, commits pequenos e nunca force push na `main`. Merge só
  com CI verde nos 3 sistemas e a trava passando.
- Não ler `artifacts/`, `.local/`, `node_modules/`, PDFs nem caches JSON grandes; usar `rg` e
  ler só trechos.
- Decisão irreversível ou ambígua vai para o relatório, não é tomada pelo agente.

## Comandos (na raiz do repositório; no Windows, `.venv/Scripts/python`)
```
python -m ruff check athenix tests scripts migrations
python -m ruff format --check athenix tests scripts migrations
python scripts/check_secrets.py
python scripts/avaliar.py --rotulo local --comparar tests/baseline/metricas_v1.json   # trava
python -m pytest -q
python scripts/exportar_plano_demo.py        # regenera landing/src/content/plano-rn1137.json
cd landing && npm ci && npm test && npm run build   # site; Node 24 (pode ser portátil)
```

## Onde fica cada coisa
- Código: `athenix/` (app FastAPI, `impacto`, `plano`, `remissoes`, `historico`,
  `parcela_variavel`; dados em `athenix/data/`), `scripts/`, `tests/` (gabarito e linha de base em
  `tests/baseline/`), `landing/` (site Vite/React; `/demo` em `src/components/plano/`).
- Produto e estratégia: `docs/POSICIONAMENTO.md`, `README.md`.
- Princípios e estilo de código: `AGENTS.md`.
- Avaliação e trava: `docs/avaliacao.md`. Execução e histórico: `docs/execucao.md`.
- Impacto e multas: `docs/impacto.md`, `docs/parametros_impacto.md`.
- Propostas: `docs/proposta_valor_provavel.md`, `docs/proposta_enquadramento.md`,
  `docs/parcela_variavel.md`.
- Demo: `docs/plano_acao.md` (no #24), capturas em `docs/telas/`.
- Identidade visual (tokens, como mudar uma cor, `?tema=`, contraste): `docs/IDENTIDADE_VISUAL.md`.
- Revisão por especialista: `docs/revisao_especialista.md`.
- Último sprint: `docs/SPRINT_2026-11-17.md`.
