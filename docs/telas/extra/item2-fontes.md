# Item 2 — citações com acesso à fonte salva

Branch `extra/citacoes-fontes`, baseada na main `e85d0a6`, sem merge. Estimativa inicial: 75 minutos.

O site passa a ligar as citações de dispositivos à cópia oficial em `landing/public/fontes/`.
PDF usa `#page=N`, com N contado a partir da primeira página física do arquivo; HTML abre o arquivo
salvo, sem número de página. Os links estão nos detalhes das obrigações, no marco do prazo,
infrações, reduções, tabela dos grupos, outros dispositivos, perguntas para o jurídico, executiva,
relatório e visualização da norma na landing.

## Fontes e localização

O script `python scripts/demo/publicar_fontes.py` confere a aprovação no catálogo oficial e o
SHA-256 antes de copiar. Gera o índice reproduzível `landing/src/content/fontes-publicas.json`.
São **7 documentos oficiais e 611 citações localizadas**. Nenhuma fonte privada ou de terceiro foi
copiada. As cópias mantêm exatamente os bytes e o hash do original já versionado.

| Arquivo público | SHA-256 do catálogo e da cópia |
| --- | --- |
| `ren20251137.pdf` | `4a581592e981158bb9a9ebbbed10a019d3c06399fd2890389bf88f3609cc5887` |
| `faq_ren20251137.html` | `a3ace3d565c44118f29952ebad2b7a5012ab1e210d3d97e687a601f3b276f4da` |
| `atren2019846.pdf` | `efe4e35fb41aa1306846677ffc32a0c2a150ee6ac44aafe5f15e475e6ad05ad9` |
| `dou_ren20261162.html` | `2e5e9962c8541a0732d4cf404b6270accb2e790654ea379a86d69105a7cb03f5` |
| `l9427cons.htm` | `ff948e3442edc619d98a3256fc6988a7c3d0dc21b27e25444a56a701082ac91b` |
| `ren20261148.pdf` | `c1bf6ff2da617d0699cc00e2abd774eabd6950bb4d7f2d76f5f86b6ee923697e` |
| `dou_ren20261174.html` | `fe1f0608ff63945912f5a37de9ffa612cbdc714cf77c231dc7df2fb4d6361507` |

A localização dos PDFs usa pypdfium2, independente do pdfplumber usado na extração do produto.
A amostra automatizada confirma o trecho completo na página apontada:

| Dispositivo | Arquivo | Página física |
| --- | --- | ---: |
| item 103 | ren20251137.pdf | 5 |
| Art. 13, VI | ren20251137.pdf | 31 |
| Art. 371-A, § 5º | ren20251137.pdf | 28 |
| Art. 24, I da REN 846 | atren2019846.pdf | 25 |

Oito citações atravessam páginas: o índice registra início e fim, e o link abre o início.
A redação futura incerta da REN 1.148 foi localizada pela abertura do trecho na página 12; o índice
registra esse método e a interface preserva **INCERTA** e `conferido_na_fonte: false`.
Localizar a página não confirma a redação nem o enquadramento.

Na demo antiga, as duas citações de infração passam a usar o texto literal já verificado no catálogo
oficial atual, inclusive a pontuação. Nenhum valor, grupo, cálculo, contagem ou enquadramento mudou.

Os HTMLs públicos mantêm seus bytes. `landing/vercel.json` bloqueia scripts, conexões, frames,
formulários e alteração da URL-base em `/fontes/`. O teste de navegador confirmou o bloqueio de
um script inserido no HTML salvo, sob o cabeçalho configurado, sem alterar o documento-fonte.

## Verificação

- Pytest: **582 aprovados, 6 pulados** por dependerem de acervo local proibido nesta rodada.
- Site: **119 testes**, TypeScript, build, pré-renderização e conferência do HTML aprovados.
- Trava vigente v2: **29/29**, sem regressão; linha de base não alterada.
- `exportar_plano_demo.py --verificar`: as duas normas reproduzidas.
- Ruff, formatação e check_secrets aprovados.
- Chrome/Playwright: larguras 1280 e 390 px, links corretos, sem rolagem horizontal ou erro JS no app;
  conteúdo servido das sete fontes com hash conferido. Clique na fonte da REN 1.174 abriu o HTML salvo.
- Relatório de impressão: links de fontes presentes e clicáveis no HTML.
- CI dos três sistemas: checks do PR deste item, vinculados ao commit enviado.

## Capturas

- [RN 1.137, 1280 px](item2-citacao-rn1137-1280.png)
- [RN 1.137, 390 px](item2-citacao-rn1137-390.png)
- [REN 1.174, 1280 px](item2-citacao-ren1174-1280.png)
- [REN 1.174, 390 px](item2-citacao-ren1174-390.png)
- [HTML oficial salvo aberto](item2-fonte-html-1280.png)
- [Relatório com links](item2-relatorio-fontes-1280.png)

## Limitações e decisão

O visualizador de PDF do usuário interpreta `#page=N`; a amostra valida o conteúdo do arquivo,
não o comportamento de todos os visualizadores. A marca de redação incerta não foi removida.
O índice acrescenta aproximadamente 33 kB gzip ao pacote inicial (186 kB contra 153 kB); o aviso de
chunk grande permanece. Não houve medição de desempenho em dispositivo móvel real.

O responsável precisa revisar a prévia e decidir o merge. Nenhuma chamada paga, leitura de `.env` ou `.local/`.
