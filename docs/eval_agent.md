# Eval Agent da Athenix

Executor determinístico de avaliação do repositório, do smoke test ao benchmark de extração.
Reutiliza testes e gabarito existentes. Não é um novo agente autônomo de produção.

## Executar

Na raiz do repositório, instale as dependências de `requirements.lock` em um ambiente Python 3.11+.

```powershell
python scripts/eval_agent.py --perfil health
python scripts/eval_agent.py --perfil completo
```

`--saida <diretorio-novo>` define o diretório dos artefatos; o padrão cria um diretório por execução
em `artifacts/eval-agent/`. `--timeout 900` limita cada etapa. Não inicia servidor nem acessa o banco
operacional: os testes usam suas fixtures. Não testa a disponibilidade de uma implantação remota.

| Camada | Evidência |
| --- | --- |
| Health | Migrações, ingestão de PDF e verificação de evidências por testes locais |
| Precisão | Gabarito, citações e métricas por verificação; comparação com baseline existente |
| Confiabilidade | Suíte completa: reprodução, fila, modos de IA e regressões |
| Segurança | Suíte completa: autenticação, revisão humana, orçamento e validação de propostas; scanner de segredos |
| Desempenho | Duração por etapa e timeout; sem meta de latência de produção |

O perfil `health` executa apenas a primeira camada. `completo` executa todos os testes, scanner e
benchmark. O relatório JSON inclui contagens JUnit, métricas do gabarito e comandos para reproduzir
falhas. O Markdown resume as etapas. Saídas brutas dos subprocessos não são copiadas ao relatório
para evitar inclusão acidental de dados sensíveis; use o comando registrado para investigar falhas.

Código de saída 1 indica falha, timeout ou evidência ausente/inválida. Código 0 pode indicar
`aprovado` ou `ressalvas`: testes pulados ficam explícitos no JSON e não equivalem a cobertura.
O executor continua as etapas independentes após uma falha. Não atualiza o baseline.

## Limites e evolução

A aprovação vale apenas para as verificações executadas. O gabarito tem 20 casos elaborados por IA
sem revisão especializada; precisão local não é precisão global. Veja [avaliação](avaliacao.md).
Testes com transportes falsos não medem comportamento real do modelo, resistência completa a
prompt injection, custo real, vazamento real ou latência de um provedor. O modo de IA dos processos
é forçado para `off`; não há execução paga nem LLM como juiz.

Para uma avaliação de modelo real, o próximo conjunto deverá separar casos de desenvolvimento e
holdout revisado por especialista, registrar modelo/prompt/tarifa e avaliar saídas reais contra as
mesmas travas de evidência e revisão humana. Essa etapa precisa respeitar confirmação e orçamento
já exigidos pelo produto. Não se deve transformar resultados sintéticos em evidência de qualidade real.

Decisão: usar biblioteca padrão e verificações existentes evita duplicar critérios e adicionar
frameworks. O trade-off é não oferecer tracing de ferramentas ou juiz semântico: o provedor atual
não recebe ferramentas. Uma plataforma externa de eval só se justifica quando houver esse escopo.

## Quatro dimensões do agente

O JSON versão 2 e o Markdown separam quatro perguntas. O health check é um pré-requisito técnico;
a duração das etapas é uma medida operacional. Nenhum dos dois substitui estas avaliações.

| Dimensão | O que já é verificado offline | O que exige avaliação real |
| --- | --- | --- |
| Resposta final | Trecho literal, rejeição de paráfrase como citação; gabarito na etapa separada | Saída do modelo contra referência revisada por especialista |
| Caminho percorrido | Modo off sem rede, cache sem nova chamada, chamada bloqueada sem orçamento/chave | Sequência de ferramentas, autorização e minimização de acesso por execução |
| Limites de segurança | Caso sintético de injeção, proposta fora do escopo/sem evidência, autenticação/CSRF | Ataques variados ao modelo, dados sensíveis de teste e tentativas de exfiltração |
| Reconhecimento de incerteza | Fonte sem confirmação não vira verificada; datas conflitantes/ambíguas não viram certeza | Taxa de abstenção apropriada, erros com alta confiança e calibração contra referência |

Cada dimensão lista os casos JUnit realmente encontrados e seu estado. `verificado_offline` vale
somente para os testes mapeados; a lacuna permanece explícita. Casos ausentes geram `incompleto`
ou `nao_avaliado`, casos pulados geram `incompleto`, e qualquer falha gera `falhou`.
O estado geral continua sendo o resultado das etapas técnicas do perfil selecionado: `aprovado`
no health não significa que as quatro dimensões foram avaliadas.

Para reconhecimento de incerteza, não basta contar frases como “não tenho certeza”. É necessário
cruzar correção, confiança declarada e decisão de pedir revisão. Uma resposta errada e confiante
precisa ser identificada separadamente de uma resposta errada que pede ajuda. Essa medição ainda
não é realizada pelo executor offline, e não se atribui uma nota fictícia a ela.
