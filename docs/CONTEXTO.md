# Contexto da Athenix (para agentes)

Leia isto primeiro e depois só o que a tarefa exigir. Não varra o repositório.

## O que é
Inteligência regulatória B2B para normas da ANEEL, começando por distribuição e transmissão de
energia. Lê a norma, extrai obrigações **por regras** (não por IA), cita o dispositivo com trecho
verificado na fonte, calcula prazos e o teto de multa (REN 846, grupos I–V, até 2% da ROL; teto legal
3%). A IA só **sugere** (enquadramento, título curto). A sugestão aparece marcada como
"Interpretação da IA · aguarda revisão humana" e fica fora do cálculo. É um MVP técnico, ainda não
validado comercialmente.

## Estado (17/11/2026)
- `main` em `87ba336`. CI verde em Ubuntu, Windows e macOS (284 testes + 4 pulados por falta dos
  PDFs oficiais). Gabarito 20/20, trava ok.
- PR #24, a nova `/demo` em forma de plano de ação, é rascunho e **não pode ser mergeada sem o
  fundador**. #22 e #20 estão intocados.
- Pendências do fundador: `docs/SPRINT_2026-11-17.md` §5. Progresso do sprint em curso:
  `.review/PROGRESSO.md` (fora do git).

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
- Revisão por especialista: `docs/revisao_especialista.md`.
- Último sprint: `docs/SPRINT_2026-11-17.md`.
