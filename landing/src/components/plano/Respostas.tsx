import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { alternarProva, armazemDoNavegador, carregar, definirJaFazemos, RESPOSTAS_VAZIAS, salvar, type Respostas } from '../../content/respostas'
import type { NormaId } from '../../content/plano'

// O que a empresa escreve e marca fica só no navegador (content/respostas.ts). Sem storage, segue em memória.
interface Contexto {
  respostas: Respostas
  /** false: o navegador não deixou gravar; o que foi digitado se perde ao fechar a página. */
  persistente: boolean
  escrever: (tema: string, texto: string) => void
  marcarProva: (tema: string, prova: string) => void
}
const Ctx = createContext<Contexto>({ respostas: RESPOSTAS_VAZIAS, persistente: true, escrever: () => {}, marcarProva: () => {} })

export function RespostasProvider({ norma, children }: { norma: NormaId; children: ReactNode }) {
  const [respostas, setRespostas] = useState<Respostas>(RESPOSTAS_VAZIAS)
  const [persistente, setPersistente] = useState(true)
  const pronto = useRef(false)
  // Lê só no navegador, depois de montar (o HTML pré-renderizado nunca tem texto de ninguém).
  useEffect(() => {
    setRespostas(carregar(armazemDoNavegador(), norma))
    pronto.current = true
  }, [norma])
  // Grava DEPOIS de o estado mudar (efeito), nunca dentro do atualizador (que o StrictMode roda duas vezes).
  useEffect(() => {
    if (pronto.current) setPersistente(salvar(armazemDoNavegador(), norma, respostas))
  }, [respostas, norma])
  const aplicar = useCallback((f: (r: Respostas) => Respostas) => setRespostas((atual) => f(atual)), [])
  const valor = useMemo<Contexto>(() => ({
    respostas, persistente,
    escrever: (tema, texto) => aplicar((r) => definirJaFazemos(r, tema, texto)),
    marcarProva: (tema, prova) => aplicar((r) => alternarProva(r, tema, prova)),
  }), [respostas, persistente, aplicar])
  return <Ctx.Provider value={valor}>{children}</Ctx.Provider>
}

export const useRespostas = () => useContext(Ctx)
