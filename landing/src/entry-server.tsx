import { StrictMode } from 'react'
import { renderToString } from 'react-dom/server'
import App from './App'
import { PlanoPage } from './components/plano/PlanoPage'
import { ExecutivoPage } from './components/executivo/ExecutivoPage'

/** O dia (America/Sao_Paulo) em que o HTML foi pré-renderizado; o /demo só hidrata se ainda for esse dia. */
export { HOJE as diaDoBuild } from './content/plano'

/** HTML estático da página, para buscadores e prévias de link; o navegador hidrata em main.tsx. */
export function render(path = "/"): string {
  return renderToString(
    <StrictMode>
      <App path={path} demo={<PlanoPage />} executivo={<ExecutivoPage />} />
    </StrictMode>,
  )
}
