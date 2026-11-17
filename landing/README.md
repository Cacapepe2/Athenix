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
| `npm run build` | Build de **publicação**: falha enquanto o e-mail de contato for `example.com`; depois roda `build:site` |
| `npm run build:site` | Checagem de tipos + build em `dist/` + pré-renderização (`scripts/prerender.mjs`): o HTML já sai com o conteúdo |
| `npm run preview` | Serve o build de produção em http://localhost:4173 |
| `npm test` | Testes (`node --test`): etapas da rolagem, rastreabilidade dos dados da demo e textos sem afirmações que o produto não sustenta |

## Editar textos

Todos os textos ficam em `src/content/`, separados dos componentes:

- `site.ts`: menu, hero, seções, contato e rodapé.
- `demo.ts`: lê `demo-rn1137.json`, com **trechos reais da RN ANEEL 1.137/2025** e impacto calculado pelo Athenix com o perfil ilustrativo (distribuidora que não é empresa real). O JSON é gerado por `python scripts/exportar_demo_site.py` na raiz do repositório (requer o módulo de impacto) e registra o commit de origem. Não edite números à mão.

Regras de conteúdo:

- Não inclua clientes, métricas, depoimentos ou resultados que não existam.
- Em `demo.ts`, o campo `anchor` de cada obrigação precisa ser cópia literal de um trecho do artigo citado. `npm test` falha se não for, a mesma regra de rastreabilidade do produto.
- Referência de mensagem: `docs/POSICIONAMENTO.md` (raiz do repositório).
- **Antes de publicar**, troque `contact.email` em `site.ts`. O valor atual (`contato@example.com`) é um domínio reservado e não recebe e-mails; `npm run build` falha enquanto ele estiver lá.

## Estrutura

```
src/
  content/            textos (site.ts) e dados da demo (demo.ts + demo-rn1137.json)
  components/
    sections/         uma seção da página por arquivo, na ordem de App.tsx
    product/          peças da interface ilustrativa (documento, selos, cena, mockup)
    ui/               logo, botões, revelações de texto
  hooks/              usePointerTilt (inclinação pelo mouse)
  lib/                text.ts (realce literal, etapas) e scroll.ts (rolagem até âncoras)
  entry-server.tsx    renderização estática usada na pré-renderização
scripts/              check-contact.mjs (trava de publicação) e prerender.mjs
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
