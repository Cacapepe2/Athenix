import { StrictMode } from 'react'
import { renderToString } from 'react-dom/server'
import App from './App'

/** HTML estático da página, para buscadores e prévias de link; o navegador hidrata em main.tsx. */
export function render(): string {
  return renderToString(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}
