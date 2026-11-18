import { StrictMode, type ReactNode } from 'react'
import { createRoot, hydrateRoot } from 'react-dom/client'
import '@fontsource-variable/newsreader/opsz.css'
import '@fontsource-variable/newsreader/opsz-italic.css'
import '@fontsource-variable/inter-tight'
import './index.css'
import App, { isDemo } from './App'

const root = document.getElementById('root')!
const path = window.location.pathname
const iniciar = (demo?: ReactNode) => {
  const app = (
    <StrictMode>
      <App path={path} demo={demo} />
    </StrictMode>
  )
  // Build de produção chega pré-renderizado (scripts/prerender.mjs): hidrata; em desenvolvimento, renderiza.
  if (root.hasChildNodes()) hydrateRoot(root, app)
  else createRoot(root).render(app)
}
// O plano da demo (dados de 168 obrigações) só é baixado em /demo; a página inicial não o carrega.
if (isDemo(path)) import('./components/plano/PlanoPage').then(({ PlanoPage }) => iniciar(<PlanoPage />))
else iniciar()
