import { StrictMode } from 'react'
import { renderToString } from 'react-dom/server'
import App from './App'
import { PlanoPage } from './components/plano/PlanoPage'

/** HTML estático da página, para buscadores e prévias de link; o navegador hidrata em main.tsx. */
export function render(path = "/"): string {
  return renderToString(
    <StrictMode>
      <App path={path} demo={<PlanoPage />} />
    </StrictMode>,
  )
}
