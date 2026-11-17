import { StrictMode } from 'react'
import { createRoot, hydrateRoot } from 'react-dom/client'
import '@fontsource-variable/newsreader/opsz.css'
import '@fontsource-variable/newsreader/opsz-italic.css'
import '@fontsource-variable/inter-tight'
import './index.css'
import App from './App'

const root = document.getElementById('root')!
const app = (
  <StrictMode>
    <App />
  </StrictMode>
)
// Build de produção chega pré-renderizado (scripts/prerender.mjs): hidrata; em desenvolvimento, renderiza.
if (root.hasChildNodes()) hydrateRoot(root, app)
else createRoot(root).render(app)
