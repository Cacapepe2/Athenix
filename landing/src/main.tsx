import { StrictMode, type ReactNode } from 'react'
import { createRoot, hydrateRoot } from 'react-dom/client'
import '@fontsource-variable/inter-tight'
import './index.css'
import { aplicarTema } from './tema'
import App, { isDemo, isExecutivo } from './App'
import { hojeISO } from './content/datas'

aplicarTema()
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
  // O plano completo (/demo) conta prazos até "hoje" em todo lugar: se o dia em São Paulo mudou desde o build
  // (data-dia), o HTML pré-renderizado já não confere e hidratar daria o erro 418 do React; renderiza do zero.
  // A executiva não precisa disso: as partes com data só aparecem depois da montagem (hooks/useHoje).
  const mesmoDia = !isDemo(path) || root.dataset.dia === hojeISO()
  if (root.hasChildNodes() && !window.location.search && mesmoDia) hydrateRoot(root, app)
  else createRoot(root).render(app)
}
// O plano da demo (dados de 168 obrigações) só é baixado em /demo e /demo/executivo; a página inicial não o carrega.
if (isExecutivo(path)) import('./components/executivo/ExecutivoPage').then(({ ExecutivoPage }) => iniciar(undefined, <ExecutivoPage />))
else if (isDemo(path)) import('./components/plano/PlanoPage').then(({ PlanoPage }) => iniciar(<PlanoPage />))
else iniciar()
