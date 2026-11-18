# Parcela Variável das transmissoras: estrutura pronta, norma ausente

Status: **não estimável** (17/11/2026). `athenix/parcela_variavel.py` e
`athenix/data/parcela_variavel.json`. Não está ligado à tela de impacto.

Nenhuma fórmula, fator ou limite foi escrito de memória. O arquivo de parâmetros tem os componentes
`base`, `PVI`, `PVRO`, `PVA` e `limite`, todos vazios, e os `fatores` a preencher. Cada um precisa de
expressão transcrita da norma, dispositivo e trecho literal; a norma precisa de ato e SHA-256. Sem
isso, `calcular` responde "não estimável" e lista o que falta.

- **Entradas do usuário:** RAP anual (R$) e eventos (tipo PVI/PVRO/PVA, duração em minutos e as
  variáveis extras que a expressão da norma pedir).
- **Expressões:** só números, variáveis declaradas, `+ - * /`, sinal e `min`/`max`; nada é executado
  (`tests/test_parcela_variavel.py`, inclusive tentativas de injeção).
- **Saída:** base, parcela por evento, total antes e depois do limite, e a citação de cada componente.

## O que procurar e conferir

Listas `procurar` e `conferir` em `athenix/data/parcela_variavel.json`. Em resumo:

1. A versão vigente (compilada) da **REN ANEEL 905/2020** (Regras dos Serviços de Transmissão). A
   RN 1.137/2025, Art. 6º, revisa o "Módulo 4 – Prestação do Serviço" do Anexo IV dessa norma:
   conferir se PVI, PVRO e PVA estão lá.
2. Qualquer ato a que ela remeta para a PV (por exemplo, a norma histórica REN 729/2016 ou
   Procedimentos de Rede do ONS), confirmando a vigência. **Hipótese a confirmar, não verificada.**
3. A resolução homologatória da RAP do ciclo, com anexos (a REH 3.348/2024 do repositório tem só o
   corpo do ato).
4. Para cada componente: definição do pagamento base e relação com a RAP; fórmulas de PVI, PVRO e
   PVA; fatores e franquias; limites por período; período de apuração e transição.
