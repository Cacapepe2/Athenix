# Classificação de tipos por IA: estimativa de custo e comparação com as regras

**Nenhuma chamada de IA foi feita.** Este arquivo traz a estimativa para o seu "ok" e, depois de uma
execução autorizada, a comparação regra × IA. Resposta da IA é interpretação
("Interpretação da IA · aguarda revisão humana"), validada contra a lista de tipos.

## Estimativa (168 obrigações da RN 1.137)
| Plano | Chamadas | Tokens de entrada | Saída (JSON) | Saída (teto com raciocínio) |
|---|---|---|---|---|
| Lotes de 12 | 14 | 24,191 | 5,320 | 42,000 |
| Uma por obrigação | 168 | 114,795 | 8,400 | 504,000 |

Método: 1 token ≈ 3 caracteres (heurística do projeto, `athenix/llm.py`); o teto de saída é de 3.000
tokens por chamada (modelo de raciocínio gasta tokens pensando). **Preço em US$: não calculado**, porque
este ambiente não tem modelo nem preço configurados (`ATHENIX_INPUT_PRICE`, `ATHENIX_OUTPUT_PRICE`, fonte e
data do preço). Fórmula: `custo = (entrada × preço_entrada + saída × preço_saída) / 1.000.000`.

Exemplos ILUSTRATIVOS de preço (não são os do seu deployment), plano de lotes de 12:
| Preço (entrada / saída por 1 M) | Custo mínimo (saída JSON) | Custo máximo (teto de saída) |
|---|---|---|
| US$ 0.15 / US$ 0.6 | US$ 0.01 | US$ 0.03 |
| US$ 1.0 / US$ 4.0 | US$ 0.05 | US$ 0.19 |
| US$ 2.5 / US$ 10.0 | US$ 0.11 | US$ 0.48 |

Com lotes de 12 a entrada é menor (o prompt de tipos se repete 14 vezes, não 168).

## Comparação regra × IA
Ainda sem respostas de IA em cache.

