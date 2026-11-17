# Athenix — landing page

Site institucional da Athenix (React + TypeScript + Vite + Tailwind CSS 4 + Motion + Lucide). Não tem backend: é um site estático.

## Rodar localmente

Requer Node.js 20 ou superior.

```powershell
cd landing
npm install
npm run dev        # http://localhost:5173
```

Outros comandos:

| Comando | O que faz |
| --- | --- |
| `npm run build` | Checagem de tipos + build de produção em `dist/` |
| `npm run preview` | Serve o build de produção em http://localhost:4173 |
| `npm test` | Testes (`node --test`): etapas da rolagem e rastreabilidade dos dados da demo |

## Editar textos

Todos os textos ficam em `src/content/`, separados dos componentes:

- `site.ts`: menu, hero, seções, contato e rodapé.
- `demo.ts`: norma **fictícia** usada na cena "Da norma à ação" e na demonstração interativa.

Regras de conteúdo:

- Não inclua clientes, métricas, depoimentos ou resultados que não existam.
- Em `demo.ts`, o campo `anchor` de cada obrigação precisa ser cópia literal de um trecho do artigo citado. `npm test` falha se não for, a mesma regra de rastreabilidade do produto.
- **Antes de publicar**, troque `contact.email` em `site.ts`. O valor atual (`contato@example.com`) é um domínio reservado e não recebe e-mails.

## Estrutura

```
src/
  content/            textos (site.ts) e dados fictícios (demo.ts)
  components/
    sections/         uma seção da página por arquivo, na ordem de App.tsx
    product/          peças da interface ilustrativa (documento, selos, cena, mockup)
    ui/               logo, botões, revelações de texto
  hooks/              usePointerTilt (inclinação pelo mouse)
  lib/                text.ts (realce literal, etapas) e scroll.ts (rolagem até âncoras)
```

Paleta e fontes estão em `src/index.css` (`@theme`). `bronze-deep` é um tom derivado do Bronze, usado em texto pequeno sobre fundo claro para atingir contraste AA.

## Acessibilidade e movimento

- `prefers-reduced-motion` é respeitado: o Motion usa `reducedMotion="user"`, efeitos ligados à rolagem vão direto ao estado final e a rolagem até âncoras fica instantânea.
- Abas da demonstração seguem o padrão ARIA (setas, Home e End). O menu móvel fecha com Esc. Há link "Pular para o conteúdo".
- A rolagem até âncoras é feita por `lib/scroll.ts`: no Chromium, a rolagem suave nativa parava antes do destino ao atravessar a seção fixa.

## Publicar na Vercel

1. Envie o repositório ao GitHub.
2. Na Vercel: **Add New → Project** e importe o repositório.
3. Em **Root Directory**, escolha `landing`. A Vercel detecta Vite: build `npm run build`, saída `dist`.
4. Clique em **Deploy**.

Pela CLI: `npm i -g vercel`, depois `cd landing` e `vercel` (prévia) ou `vercel --prod`.
