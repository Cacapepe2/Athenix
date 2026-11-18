# Tipos de obrigação e dependências externas na RN 1.137/2025

Gerado por `python scripts/relatorio_tipos.py` (regras, sem IA). Manuais e dependências estão como
**rascunho — revisar**. Texto normativo = citação; tipo e dependência inferida = interpretação.

**Precisão:** classificar por regra não é o mesmo que classificar certo. Em revisão manual de duas
amostras (28 e 34 obrigações, de 3 em 3 e de 5 em 5) lidas pelo Claude em 18/11/2026 (não é conjunto rotulado por
especialista e pode ficar desatualizada se as regras mudarem), cerca de 65% a 75% dos tipos eram plausíveis.
Erros típicos: dispositivo que lista conteúdo (alínea) herda o tipo do caput; verbo genérico vence o
verbo principal. "outros" é o resultado honesto quando falta sinal. A revisão humana dos tipos é necessária.

- Obrigações: **168**; classificadas por regra: **163 (97.0%)**, das quais 64 só com o texto do dispositivo-pai; em "outros": **5**.

| Tipo | Obrigações |
|---|---|
| Elaborar ou revisar plano | 24 |
| Manter estrutura de atendimento ou contingência | 23 |
| Publicar no site | 21 |
| Comunicar Poder Público e terceiros | 17 |
| Inspecionar ou executar manutenção | 14 |
| Comunicar consumidores | 13 |
| Enviar informação à ANEEL | 13 |
| Estabelecer critérios, regras ou responsáveis | 10 |
| Articular e coordenar com terceiros | 7 |
| Adequar contrato ou documento | 5 |
| Capacitar equipe | 5 |
| Outros | 5 |
| Apurar ou calcular indicador | 5 |
| Manter registro ou histórico | 2 |
| Restabelecer fornecimento ou compensar | 2 |
| Implantar sistema ou processo | 2 |

## Dependências externas
- Sinal **no próprio texto**: 9 obrigações. Por dependência: {'autorizacao_municipal': 4, 'evento_extremo_defesa_civil': 5}.
- Só **inferida pelo tipo** (sem sinal no texto): 123 obrigações.
- Citação do trecho que disparou (verificação literal): {'verified': 9}.

## Obrigações em "outros" (com a citação)

- **item 23-C**: "23-C. A distribuidora deve disponibilizar aos consumidores o número total de unidades consumidoras afetadas por interrupções."
- **item 23-K**: "23-K. A distribuidora deve disponibilizar à ANEEL uma API (Application Programming Interface) que possibilite a consulta de dados de interrupção do fornecimento diretamente dos sistemas das distribuidoras."
- **Art. 10 › §3º**: "§3º A Portaria que instituir Comitê de Crise deverá atender as demais disposições da Portaria nº 6.803, de 30 de janeiro de 2023, no que couber."
- **Art. 15**: "Art. 15. As distribuidoras devem disponibilizar a API de que trata item 113 do Anexo IV da Resolução Normativa nº 956, de 7 de dezembro de 2021, com redação dada pelo art. 3º desta Resolução Normativa em até 60 (sessenta) dias, contados da publicação das instr"
- **Art. 17**: "Art. 17. As transmissoras têm 90 (noventa) dias, a partir da publicação, para implementar as disposições dos artigos 6º e 7º desta Resolução Normativa."
