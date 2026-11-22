# Inventário técnico: o que existe e o que funciona

Conferido em **21/11/2026** no commit `887cd2f` e de novo em **22/11/2026** no código da `main` em
`d2b058b` (depois das correções C1 e A1), Windows 11, Python 3.13.14, sem IA
(`ATHENIX_AI_MODE=off`). Cada linha diz se a peça existe, se funcionou agora, como rodar e a
evidência (saída do comando). O que não foi testado está marcado como **não testado**.

## Resumo

| Peça | Existe | Funciona agora | Como rodar |
| :-- | :-- | :-- | :-- |
| API HTTP (FastAPI) | sim | **sim** | `python -m athenix serve` · `python scripts/demo/demo_api.py` |
| Rota que devolve o plano completo | **não** | — | o plano sai do comando único (abaixo) |
| Comando único (norma → plano JSON) | sim | **sim** | `python -m athenix processar <arquivo> --saida plano.json` |
| Banco SQLite + migrações Alembic | sim | **sim** | padrão; `ATHENIX_DATABASE_URL` muda |
| PostgreSQL via Docker Compose | sim | **não testado** (máquina sem Docker) | `docker compose up -d --build` |
| IA híbrida (off / cached / live) | sim | **off e cached: sim** (testes); live não rodado | `ATHENIX_AI_MODE` |
| Testes Python | sim | **sim: 513 aprovados** | `python -m pytest -q` |
| Testes do site | sim | **sim no CI: 113** (sem Node nesta máquina) | `cd landing && npm test` |
| Trava do gabarito | sim | **sim: 20/20** | `python scripts/avaliar.py --rotulo local --comparar tests/baseline/metricas_v1.json` |
| CI em 3 sistemas | sim | **sim: verde** | `.github/workflows/ci.yml` |
| Instalação limpa | — | **sim** (clone novo, venv novo) | 3 comandos do README |
| Demo web local com login | sim | **não executada agora** (grava em `.local/`); coberta por `tests/test_demo.py` | `python -m athenix demo` |
| Relatório-piloto (PDF) | sim | **não executado agora**; fora do CI (achado A2 da auditoria) | `scripts/piloto/gerar_relatorio.py` |

## API HTTP

- **Existe:** `athenix/app.py`, FastAPI 0.162.0 (`requirements.lock`). 13 rotas `/api/*`,
  mais `/export/{json,csv,html}` e `/health`, listadas em [API.md](API.md); as telas HTML do
  aplicativo usam as mesmas funções. Sessão por cookie, CSRF em toda mutação, recusa de
  `Origin` estrangeiro.
- **Recebe uma norma?** Sim: `POST /api/documents` (multipart) devolve id e SHA-256;
  `POST /api/documents/{id}/runs` com `{"kind":"rules"}` extrai; `GET /api/obligations` devolve as
  obrigações com citação verificada.
- **Devolve o plano?** **Não diretamente.** A API devolve as obrigações candidatas por regras (170 na
  RN 1.137: dever 155, faculdade 14, proibição 1). A classificação dever × faculdade × competência, o
  enquadramento, o valor e a área são montados pelo comando único, que usa a API por dentro.
- **Evidência** (`python scripts/demo/demo_api.py`, servidor real em SQLite temporário):

```text
  2. POST /api/documents                     sha256=4a581592e981158b…
  3. GET  /api/documents/{id}                31 página(s), 315 unidades estruturais
  5. GET  /api/runs/{id}                     estado=completed
  6. GET  /api/obligations                   170 obrigações, 251 de 253 citações verificadas
  7. GET  /api/evidence/verify               251 citações reconferidas, válidas=sim
Tempo total: 7.3 s (inclui subir o servidor)
```

  REN 1.174 (`--arquivo tests/fontes_impacto/dou/dou_ren20261174.html`): 368 unidades, 167
  obrigações, 241 de 243 citações verificadas, 4,0 s. Em 21/11 (antes de C1 e A1) também testado à
  mão com `curl` e com PowerShell (`Invoke-RestMethod` e `curl.exe`); `GET /export/csv` devolveu 200 e 533 linhas;
  `GET /api/audit/verify` → `{"valid":true,"events":5,…}`.

## Banco

- **Existe:** `athenix/db.py` (SQLAlchemy 2.1.8), migrações `migrations/versions/0001_initial.py` e
  `0002_supplements.py`, aplicadas ao subir (`db.initialize` → Alembic `upgrade head`).
- **Guarda:** usuários e sessões; arquivos (bytes imutáveis, chave = SHA-256); documentos; extrações
  (texto canônico, páginas, unidades); execuções da fila; interpretações (obrigações); decisões
  humanas; contestações; ligações entre normas; respostas de IA e travas de chamada paga; trilha de
  auditoria encadeada por hash (`users`, `sessions`, `artifacts`, `documents`, `extractions`, `runs`,
  `interpretations`, `decisions`, `findings`, `dependency_links`, `model_responses`, `call_claims`,
  `audit_events`).
- **SQLite:** funciona (todas as execuções acima e a suíte de testes).
- **PostgreSQL:** `compose.yaml` sobe `postgres:18` + `web` + `worker`; senha só pelo ambiente
  (`ATHENIX_DB_PASSWORD`). **Não testado nesta conferência:** a máquina não tem Docker
  (`docker: command not found`). O teste `tests/test_infra.py` confere a configuração do compose,
  não sobe o banco.

## Comando único

- **Existe:** `python -m athenix processar <arquivo> --agente distribuidora --saida <json>`
  (`athenix/__main__.py` → `scripts/exportar_plano_demo.py:processar_norma`). Sem IA, sem rede;
  sugestões de IA só do cache versionado, marcadas.
- **Evidência** (clone e venv novos de `Cacapepe2/Athenix` em `d2b058b`, 22/11/2026, RN 1.137):

```text
Athenix · processar ren20251137.pdf para distribuidora
  1. Obrigações extraídas: 170 dispositivos lidos
  2. Deveres da distribuidora: 153 · outros dispositivos (faculdades, direitos, outros agentes): 16 · fora do perfil: 1
  3. Prazos: 7 vencidas · 0 nos próximos 90 dias · 2 recorrentes · 144 sem data
  4. Enquadramento na REN 846: 42 identificados no texto · 111 a confirmar (102 com sugestão da IA em cache, marcadas) · 0 sem multa
  5. Temas: 8 · plano gravado em plano.json
Tempo total: 14.2 s
```

  REN 1.174: 167 lidos · 84 deveres · 83 outros · 0 vencidas · 2 recorrentes · 0 identificados no
  texto · 84 a confirmar (78 com sugestão da IA) · 4 temas. Sujeito implícito (a revisar): RN 64 de
  153, REN 37 de 84. Por evento: RN 21 (inclui o item 105, até 15 min / 1 h), REN 1. Tempos de 3 execuções em
  [pitch/metricas.md](pitch/metricas.md).

## IA híbrida

- **Modos** (`athenix/llm.py:modo`): `off` (padrão, nenhuma chamada de rede), `cached` (só respostas
  gravadas), `live` (só com modelo, chave, preço com fonte e data e teto de custo; senão cai para
  `off` e diz o motivo). `GET /health` mostra o modo efetivo.
- **Orçamento:** teto por execução (`ATHENIX_RUN_BUDGET_USD`), reserva conservadora antes da chamada,
  estimativa em `GET /api/documents/{id}/estimate`; 429 repetido até 3 vezes.
- **Validação de citação:** sugestão de enquadramento só vale com as duas citações literais
  encontradas na fonte (`enquadramento.validar_ia`); títulos e recomendações também citam um trecho.
- **Cache:** `athenix/data/ia_cache_*.json`, `recomendacoes_*.json`, `titulos_curtos_*.json`,
  `evite_*.json`, `tipos_ia_cache.json` (só a sugestão processada, nunca a resposta bruta).
- **Evidência:** `tests/test_modos_ia.py` (8 testes, aprovados: off sem rede mesmo com credencial,
  cached nunca chama, live respeita o teto e só repete 429). Custo registrado:
  `python scripts/demo/custo_ia.py` → **US$ 1,0209 em 6 execuções** para as duas normas (preço
  informado, a confirmar no portal; tipos ao preço-teto). O ensaio de 17/11 da RN 1.137
  (`ia_cache_rn1137.json`) não tem custo gravado no arquivo.
- **Não funciona como prometido:** o script antigo `scripts/classificar_tipos_ia.py --executar` não
  consulta o modo de IA (achado M2 da auditoria; exige `--executar`, não roda na demo).

## Testes, trava e CI

- **pytest:** `python -m pytest -q` → `513 passed in 171.20s` (máquina de desenvolvimento, 22/11). Num clone
  limpo → `507 passed, 6 skipped` (os 6 dependem de dados locais fora do Git: CSV de autos, votos da
  ANEEL, cópia de conferência, REN 846 original). 44 arquivos de teste; os maiores: `test_tipos.py`
  (50), `test_impacto.py` (34), `test_prazos_obrigacoes.py` (32).
- **Site:** 113 testes (`node --test`), aprovados no CI. Não rodados nesta máquina (sem Node).
- **Trava:** `scripts/avaliar.py` → `casos corretos: 20 / 20`, citações corretas 0,9955, sem fonte
  0,0068, "Sem regressão em relação a tests/baseline/metricas_v1.json". O gabarito
  (`tests/gabarito/`) não tem revisão humana.
- **CI:** `.github/workflows/ci.yml` em `ubuntu-latest`, `windows-latest` e `macos-15-intel`: testes
  e build do site, ruff, segredos, trava, reprodução dos dois JSONs do plano e pytest. Execução
  `45054510595` (commit `d2b058b`): verde nos três; pytest no CI 507 aprovados e 6 pulados.
- **Lint e segredos:** `ruff check` → "All checks passed!"; `ruff format --check` → 122 arquivos
  formatados; `scripts/check_secrets.py` → nenhum padrão conhecido.

## Instalação limpa

Clone novo de `Cacapepe2/Athenix` em `d2b058b` (sem `.env`, sem `.local/`) e venv novo, Python 3.13.14, 22/11/2026:

| Passo | Comando | Resultado | Tempo |
| :-- | :-- | :-- | --: |
| Instalar | `python -m pip install -r requirements-dev.lock` | ok | 38 s |
| Testar | `python -m pytest -q` | 507 passed, 6 skipped | 2 min 5 s |
| Processar | `python -m athenix processar tests/norma_poc/ren20251137.pdf --saida plano.json` | 153 deveres, 8 temas | 16 s |

Não testado: Python 3.11 local (o CI usa 3.11), Linux e macOS locais (cobertos pelo CI).
