# Comparação histórica do Anexo IV — pendente de fonte

Item 4 da rodada extra de 22/11/2026. Estimativa anunciada: 15 minutos para verificar a fonte; mais 60 minutos de implementação somente se ela já estivesse no acervo.

**Estado: parado por ausência do texto oficial anterior no repositório.** Não foram atribuídos rótulos de novo, alterado ou já existente, nem contagens dessas categorias.

## Conferência local

Base: `main` em `e85d0a62147a0c08f0828bac925f0ca77f3d26d9`.

- `tests/fontes_impacto/` e seu catálogo `fontes.json`: há atos de sanções, transmissão, leis, DOU e FAQ; não há o Anexo IV da REN 956/2021 anterior à RN 1.137.
- `athenix/compilacao.py`: contém funções para ler uma base e aplicar alterações; código de compilação não substitui o documento-base ausente.
- `athenix/data/compilado_ren846.json`: a compilação disponível é da REN 846, não do Anexo IV da REN 956.
- Os dispositivos que a RN 1.137 altera e suas marcas `(NR)`/`(AC)` não demonstram o texto anterior integral nem permitem classificar todos os deveres como já existentes ou novos.

Nenhum arquivo de `.local/` ou material do Leis.org foi consultado. A verificação não baixou o anexo ausente nem alterou o motor, os planos ou o site.

## Documento oficial a obter

**Nome:** Anexo IV da Resolução Normativa ANEEL nº 956, de 7 de dezembro de 2021 — Procedimentos de Distribuição de Energia Elétrica no Sistema Elétrico Nacional (PRODIST), Módulo 4 — Procedimentos Operativos do Sistema de Distribuição, na redação vigente em **29/10/2025**, imediatamente anterior à publicação da RN 1.137 em 30/10/2025. Se a redação nessa data depender de atos alteradores não incorporados ao PDF, eles também precisarão compor a fonte anterior.

**Onde:** [ANEEL → Procedimentos Regulatórios → PRODIST](https://www.gov.br/aneel/pt-br/centrais-de-conteudos/procedimentos-regulatorios/prodist), linha “Módulo 4”, opção “todas as versões”. Em 22/11/2026, essa opção aponta para o [histórico oficial do Módulo 4](https://git.aneel.gov.br/publico/centralconteudo/-/tree/main/procreg/prodist/modulo04). A opção “versão vigente” aponta para `aren20251137_Prodist_modulo_4_v3.pdf`, que já é a redação da RN 1.137 e não serve como base anterior.

**Formato:** PDF integral oficial do módulo, com as seções e os itens, identificação da revisão, ato de aprovação e período de vigência. A capa da REN 956 ou seu extrato no DOU não substitui o anexo. Guardar também a origem, a data de consulta e o SHA-256 no catálogo.

O índice histórico retornou HTTP 403 nesta consulta; não houve tentativa de contornar o bloqueio. Por isso, não se afirma aqui um número de revisão ou nome de arquivo histórico ainda não conferido. O recorte temporal e o documento exigido acima identificam a fonte necessária.

**Decisão do fundador:** fornecer essa versão oficial para retomar a comparação em outra rodada. Até lá, a ausência da fonte permanece explícita e nenhum resultado comparativo é apresentado.

## Validação

PR somente documental, sem alteração de contagens: RN 1.137 com 147 deveres principais, 8 obrigações vencidas e 11 detalhamentos vencidos; REN 1.174 com 75 deveres principais e 10 condicionais. As verificações de pytest, testes/build do site, trava v2, exportações reproduzíveis e segredos são executadas para este PR; a aprovação do CI deve ser conferida no commit final nos três sistemas.
