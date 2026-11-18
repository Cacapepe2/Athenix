# Ingestão diária do DOU pelo INLABS (desenho)

**Só desenho.** Nenhum login, download ou chamada foi feito. Tudo que depende do formato dos arquivos
ou do endereço do serviço está marcado **(a confirmar)** na documentação do repositório oficial da
Imprensa Nacional no GitHub, que não foi lida aqui.

## Objetivo
Todo dia útil: baixar a edição do DOU, achar os atos da ANEEL, separar cada ato, ingeri-lo no pipeline,
deduplicar, compilar o que altera normas do acervo (`docs/COMPILACAO.md`) e avisar quando sair
"norma nova relevante". Fecha o buraco que o piloto mostrou: o PDF certificado traz só a página do
jornal e o ato pode continuar na seguinte.

## Fluxo
1. **Autenticação por variáveis de ambiente** (o fundador configura; nada em arquivo, log ou git):
   `INLABS_USUARIO`, `INLABS_SENHA` (nomes sugeridos). Sessão em memória, sem gravar cookie em
   disco. O script de coleta não imprime as variáveis nem o corpo da resposta de login, e falha se
   faltarem (`check_secrets.py` já varre o repositório).
2. **Janela e agenda.** Uma execução por dia (e uma de reforço no fim da tarde, pelas edições
   extras), pedindo a data de ontem e a de hoje; reexecução é segura (passo 6). Respeitar limites e
   termos do serviço (a confirmar) e nunca contornar bloqueio: erro 403/429 encerra a execução e
   avisa. Sem retentativa agressiva.
3. **Seleção.** O INLABS entrega a edição por seção (formato do pacote **a confirmar**; a
   expectativa é um arquivo por seção e dia, com um XML por matéria e/ou PDF). Filtro: seção 1;
   órgão com "Agência Nacional de Energia Elétrica" no caminho (`Ministério de Minas e Energia/
   Agência Nacional de Energia Elétrica/...`, como em `detalhes-dou` do HTML); mantém também atos de
   outro órgão que **citem** norma do acervo (ex.: Portaria do MME que altere a REN 846), por
   `compilacao.detectar`. O filtro registra o que descartou (contagem), não só o que guardou.
4. **Separação dos atos dentro da edição** (requisito vindo do 3.2; ver `docs/avaliacao.md`):
   - Se o pacote vier por matéria (um ato por arquivo): usa direto; metadados (edição, seção,
     página, órgão, data) vêm dos campos, não do texto.
   - Se vier só a página em PDF: `athenix.dou.ler_pdf` separa **por título** (tipo, número, data,
     inclusive título sem o "DE" antes do mês), lê coluna a coluna e isola como **ruído rotulado**
     cabeçalho, rodapé, número da página, selo ICP-Brasil, cabeçalho de órgão, texto branco invisível e
     os **outros atos da mesma página**. O ato pedido é conteúdo; o resto fica registrado, nunca
     misturado.
   - **Ato que continua na página seguinte:** juntar as páginas pela ordem do DOU até o próximo
     título; se a página seguinte não vier no pacote, marcar "ato parcial" (cobertura conhecida) e
     não compilar a partir dele; preferir a matéria completa em HTML/XML quando existir.
5. **Ingestão no pipeline.** Cada ato vira um documento com: hash do arquivo original, origem
   "DOU via INLABS", data do download, edição/seção/página, formato. Leitura com
   `athenix.dou`/`structure` (sem IA). O texto lido nunca é alterado; normalização só na comparação.
6. **Deduplicação por hash** em dois níveis: hash do arquivo (evita reprocessar o mesmo pacote) e hash
   do **texto normalizado do ato** (`normalizacao.chave`), para que o mesmo ato em HTML, XML e PDF
   seja um só registro com as três leituras como "pares". Republicação/retificação com texto
   diferente vira nova versão ligada à anterior, nunca sobrescrita.
7. **Compilação automática** (Bloco 5): `compilacao.detectar` diz o que o ato altera no acervo;
   `compilacao.compilar` aplica por data de vigência, com conflito sinalizado e sem escolha. Ato com
   vigência não determinada fica em `nao_aplicado`. A origem da redação passa a ser "DOU".
8. **Alerta de "norma nova relevante".** Relevante = (a) altera, inclui ou revoga dispositivo de norma
   do acervo; (b) é da ANEEL e trata de multa, penalidade, fiscalização ou dos temas monitorados;
   (c) gera conflito de compilação. O alerta traz: ato, órgão, data, link do DOU, o que altera
   (dispositivos), vigência e o trecho literal. Entrega por e-mail ou relatório diário a configurar
   pelo fundador; sem envio automático a terceiros. Nada é marcado como revisado em nome de ninguém.

## Testes (base: os pares HTML × PDF do Bloco 3.2)
Os três pares de `tests/fontes_impacto/dou/` viram o conjunto de teste, sem rede:
- separação de atos: página com 6 atos (REN 1.174, números 3258, 16820, 16822, 16823, 16824, 1174) e
  com 16 (Despacho 1.293 entre outros);
- ruído isolado: cabeçalho, rodapé, página 68/66/92, texto invisível da REN 1.162;
- HTML × PDF: cobertura (despacho 100%, REN 1.162 26%, REN 1.174 9%) e diferença só de espaços;
- dedupe: o mesmo ato nos dois formatos dá um registro;
- um "pacote falso" montado a partir desses arquivos exercita filtro, separação e compilação ponta a
  ponta. O cliente do INLABS fica atrás de uma interface (`baixar(data)`), substituída por arquivos
  locais nos testes; nenhum teste usa credencial.

## Riscos e pendências
- Formato do pacote, endereço, limites e termos do INLABS: **a confirmar** com a documentação oficial.
- Credenciais: o fundador cria e configura; este desenho não as usa.
- Páginas seguintes de atos longos (REN 1.162, REN 1.174) continuam faltando nos pares de teste.
- Revogação por lista complexa e anexos não compilam sozinhos (`docs/COMPILACAO.md`): vão para revisão.
- Hoje o DOU de 2026 só foi lido em 3 atos; calibrar a seleção por órgão com um mês de edições antes
  de ligar o alerta.
