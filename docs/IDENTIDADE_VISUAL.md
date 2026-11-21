# Identidade visual

Uma única fonte: `landing/src/styles/tokens.css`. Nenhuma cor, fonte, raio, borda, sombra ou tempo de
animação nasce em outro arquivo de `landing/src/`. O Tailwind aponta para esses tokens (`landing/src/index.css`,
bloco `@theme`), então `bg-obsidian`, `text-white` etc. também mudam quando o token muda.

Linguagem: fundo branco, texto quase preto, **um** acento vermelho, cantos retos, bordas fortes, sombra
dura no hover, uma família (Inter Tight). Nada de serifa decorativa, bege, terracota, pílulas coloridas,
cantos arredondados, sombra suave, rótulos em caixa-alta espaçada. Os protótipos de referência estão em
`docs/referencias/design/` (só aparência: os dados vêm sempre do motor).

## Tokens

| Token | Valor | Uso |
|---|---|---|
| `--cor-fundo` | `#ffffff` | fundo de tudo; também o `white` do Tailwind |
| `--cor-texto` | `#111111` | texto, bordas fortes, bloco aberto |
| `--cor-texto-invertido` | `#ffffff` | texto sobre `--cor-texto` ou `--cor-destaque` |
| `--cor-destaque` | `#c8261a` | o único acento: número de exposição, ponto de vencida, foco, barra de redução |
| `--cor-destaque-texto` | `#b3241a` | acento quando é texto pequeno (prazo vencido) |
| `--cor-evite` | `#a11f15` | texto de "Evite" |
| `--cor-linha-suave` | `#dddddd` | divisórias finas |
| `--cor-hover` | `#ededed` | fundo ao passar o mouse |
| `--cor-barra-teto` / `-media` / `-reducao` | `#111111` / `#555555` / `#c8261a` | três barras do painel |
| `--cor-trilho` | `#eeeeee` | fundo das barras |
| `--fonte-base` | Inter Tight, Helvetica Neue, Arial | única família |
| `--raio` | `0px` | cantos retos (`--raio-ponto: 50%` só para o pontinho de status) |
| `--borda-forte` / `--borda-titulo` | `2px` / `3px` | bloco e seletor / linha sob o título |
| `--sombra-hover` | `5px 5px 0 var(--cor-texto)` | sombra dura do bloco no hover |
| `--duracao-rapida` / `--duracao-painel` / `--curva` | `160ms` / `320ms` / `cubic-bezier(.2,.7,.2,1)` | animações |

## Como mudar uma cor

Edite o valor em `:root` de `landing/src/styles/tokens.css`. Exemplo: acento verde, troque
`--cor-destaque`, `--cor-destaque-texto` e `--cor-barra-reducao`. Depois rode `npm test` (dentro de `landing/`):
o teste de contraste avisa se algum par de texto e fundo ficou abaixo de 4,5:1.

## Como testar um tema

Cada tema é um bloco `:root[data-tema="nome"]` no fim de `tokens.css`, que só sobrescreve o que muda. O
exemplo `alternativo` troca o acento por azul-petróleo (`#0e4a5a`). Para ver: abra
`/demo/executivo?tema=alternativo` (ou `/demo?tema=alternativo`). Sem o parâmetro, o tema base. O nome só
aceita letras minúsculas, números e hífen (`landing/src/tema.ts`).

## Regras que o CI confere (`landing/src/styles/tokens.test.ts`)

1. Nenhum `#hex`, `rgb(`, `hsl(` nem nome de fonte em `landing/src/` fora de `tokens.css`. Exceção só com
   comentário explícito na mesma linha: `token-ok: <motivo>`.
2. Sem `rounded-[...]`, `shadow-[...]` nem `font-serif` nos componentes.
3. Contraste mínimo de 4,5:1 (WCAG AA, texto normal) nos pares: texto/fundo, invertido/texto,
   destaque-texto/fundo, destaque/fundo, evite/fundo, texto/hover, destaque-texto/hover, invertido/destaque,
   barra-média/fundo; no tema base e em cada tema `[data-tema]`.
4. O bloco `[data-tema="alternativo"]` existe e muda o destaque; `?tema=` só aceita nome simples.

## Componentes

- Bloco clicável (`.bloco`): fundo branco, borda forte, levanta 3 px com sombra dura no hover, afunda ao
  clicar, foco com contorno de acento; aberto, inverte (fundo `--cor-texto`).
- Seletor segmentado (`.seg`, `aria-pressed`): norma e porte; na vertical (`.pilha`) nos filtros.
- Painel (`.painel`): abre deslizando (`grid-template-rows` 0fr → 1fr) com fade; ao fechar, mantém o último
  conteúdo até terminar. Com `prefers-reduced-motion` não há animação.
