# Athenix — regras e comandos para o Claude

Contexto, estado e mapa dos documentos: `docs/CONTEXTO.md`. Princípios completos e estilo de
código (Ponytail): `AGENTS.md`, lido antes de editar código. Progresso do sprint em curso:
`.review/PROGRESSO.md`.

## Regras
- Nunca inventar obrigação, citação, dispositivo ou parâmetro; tudo com fonte (documento, artigo,
  trecho, hash).
- Separar texto normativo de interpretação da IA; a IA fica fora do cálculo; a revisão humana não é
  pulada nem confirmada em nome de ninguém.
- Sem chamadas pagas de IA; nunca ler/imprimir `.env`, chaves ou endpoint.
- Não contornar bloqueios de sites (ANEEL/DOU); não publicar PDFs do Leis.org nem respostas brutas
  de IA; não autorizar conectores/MCP.
- Produção não muda sem o fundador: PR que toca `landing/` ou a demo fica sem merge.
- Git: branch por bloco a partir da `main`, PR, commits pequenos; merge só com CI verde nos 3 SO e
  trava passando; nunca force push na `main`.
- Divergência entre documentos ou decisão irreversível: informar o fundador, não escolher.
- Economia: não ler `artifacts/`, `.local/`, `node_modules/`, PDFs, caches JSON grandes; buscar com
  `rg` e ler trechos; não reler o que já foi lido; de testes e builds, só resumo e erros.
- Ao fim de cada bloco, atualizar `.review/PROGRESSO.md` com feito, branches, PRs e próximo passo.

## Subagentes (`.claude/agents/`)
`designer-demo` (demo e relatório-piloto), `revisor` (revisão final, só leitura), `verificador`
(testes, lint, trava, build). Passar só `docs/CONTEXTO.md` e a especificação da tarefa.

## Comandos (raiz do repositório; Windows: `.venv/Scripts/python`)
```
python -m ruff check athenix tests scripts migrations
python -m ruff format --check athenix tests scripts migrations
python scripts/check_secrets.py
python scripts/avaliar.py --rotulo local --comparar tests/baseline/metricas_v2.json   # trava
python -m pytest -q
python scripts/exportar_plano_demo.py
cd landing && npm ci && npm test && npm run build
```
