import { StrictMode, type ReactNode } from 'react'
import { createRoot, hydrateRoot } from 'react-dom/client'
import '@fontsource-variable/newsreader/opsz.css'
import '@fontsource-variable/newsreader/opsz-italic.css'
import '@fontsource-variable/inter-tight'
import './index.css'
import App, { isDemo, isExecutivo } from './App'

const root = document.getElementById('root')!
const path = window.location.pathname
const iniciar = (demo?: ReactNode, executivo?: ReactNode) => {
  const app = (
    <StrictMode>
      <App path={path} demo={demo} executivo={executivo} />
    </StrictMode>
  )
  // Build de produção chega pré-renderizado (scripts/prerender.mjs): hidrata; em desenvolvimento, renderiza.
  // O HTML pré-renderizado (/demo e /demo/executivo) é o da RN 1.137: com ?norma= de outra norma, renderiza do zero (sem hidratar).
  if (root.hasChildNodes() && !new URLSearchParams(window.location.search).has('norma')) hydrateRoot(root, app)
  else createRoot(root).render(app)
}
// O plano da demo (dados de 168 obrigações) só é baixado em /demo e /demo/executivo; a página inicial não o carrega.
if (isExecutivo(path)) import('./components/executivo/ExecutivoPage').then(({ ExecutivoPage }) => iniciar(undefined, <ExecutivoPage />))
else if (isDemo(path)) import('./components/plano/PlanoPage').then(({ PlanoPage }) => iniciar(<PlanoPage />))
else iniciar()
