# D1 — consulta ao especialista

17/11/2026 · Athenix em validação · questão aberta, sem mudança da demo ou do cálculo.

**Decisão solicitada:** qual redação do inciso XXIII do Art. 11 da REN 846 deve ser aplicada a cada período e conduta? O catálogo encontrou dois textos. Não presumimos que sejam simultaneamente aplicáveis; pode haver sucessão temporal.

| Fonte disponível no repositório/acervo local | Redação encontrada | Vigência extraída — confirmar |
|---|---|---|
| RN 1.137/2025 | XXIII - deixar de prestar informações decorrentes de interrupções no fornecimento de energia elétrica aos consumidores ou usuários, nos termos da regulação vigente. | 2025-10-30 |
| REN 1.148/2026 | XXIII - deixar de responder ou responder de forma não conclusiva as demandas relacionadas ao Sistema de Gestão de Ouvidoria da ANEEL-SGO/ANEEL, ou outro que vier a substituí-lo, no prazo específico definido pela ANEEL. | 2027-01-01 |

**Escopo afetado: 23 itens**, dentre os 110 analisados, escolheram esse inciso como principal na simulação do cache. São sugestões da IA, não 23 infrações autuadas ou 23 multas somáveis. Os 23 tratam de comunicação de interrupções e não mencionam SGO/ouvidoria. [Relação dos 23 e alternativas](ensaios/itens_dependentes_D1.csv).

## O que muda no cálculo

- **Leitura de interrupções (RN 1.137):** se o especialista confirmar a aplicabilidade ao fato, esses itens podem manter a hipótese do Grupo III. O teto nominal do grupo é **0,5% da base** do Art. 21 (em regra, ROL dos 12 meses anteriores ao auto).
- **Leitura de ouvidoria (REN 1.148):** o inciso continua no **Grupo III, com o mesmo percentual de 0,5%**. Muda a conduta exigida: os textos desses 23 itens não demonstram, por si, demanda no SGO. Aplicar essa leitura ao período em análise exige rever o enquadramento, em vez de conservar o número do inciso por identidade de rótulo.
- **Sem D1 confirmado:** 22 itens têm alternativas no cache e um não tem. As alternativas incluem Grupos I/II e, em um item, IV/V. A confirmação de outro tipo pode reduzir ou aumentar o teto. Não trocar automaticamente de dispositivo e não lançar multa zero por falta de enquadramento.
- **Ilustração, sem agravantes/atenuantes:** para base hipotética de R$ 1.000.000, o teto nominal do Grupo III é R$ 5.000: **de advertência (sem multa) até R$ 5.000 (teto do Grupo III)**. Isso não é multa provável. Fração de valor base, dosimetria e teto legal continuam sujeitos às premissas e cenários já declarados.

**Efeito hoje: nenhum.** As 23 sugestões da IA não entram na exposição antes de confirmação humana. O cálculo existente não foi alterado. A data extraída para a REN 1.148 é futura em relação a esta nota; confirmar vigência, transição e tratamento dos fatos anteriores antes de substituir redação.

## Perguntas para fechar D1

1. Os textos representam substituição temporal, coexistência ou problema de numeração/consolidação? Quais períodos e fatos recebem cada redação?
2. Para os 23 itens, a comunicação de interrupções se enquadra no inciso da RN 1.137? Quais alternativas do anexo são adequadas e quais devem ser rejeitadas?
3. Há regra de transição/retroatividade relevante? Como registrar a data do fato, a versão normativa escolhida e a confirmação humana?

**Fontes:** PDFs da RN 1.137/2025 (`tests/norma_poc/ren20251137.pdf`) e da REN 1.148/2026 (`.local/fontes_impacto/ren20261148.pdf`), cotejados por leitura independente e registrados no catálogo `athenix/data/penalidades_ren846.json`, seção D1. A cópia local da REN 1.148 mantém a ressalva de origem oficial a confirmar. Validar os atos oficiais com o especialista; a confirmação literal não resolve a vigência nem o enquadramento.
