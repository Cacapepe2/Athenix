import { useEffect, type ReactNode } from 'react'
import { MotionConfig, useReducedMotion } from 'motion/react'
import { handleAnchorClick } from './lib/scroll'
import { Header } from './components/sections/Header'
import { Hero } from './components/sections/Hero'
import { BusinessSummary } from './components/sections/BusinessSummary'
import { Challenge } from './components/sections/Challenge'
import { NormToAction } from './components/sections/NormToAction'
import { ProductDemo } from './components/sections/ProductDemo'
import { Approach } from './components/sections/Approach'
import { Audience } from './components/sections/Audience'
import { Stakes } from './components/sections/Stakes'
import { Opportunity } from './components/sections/Opportunity'
import { Closing } from './components/sections/Closing'

export const isDemo = (path: string) => /^\/demo\/?$/.test(path)
export const isExecutivo = (path: string) => /^\/demo\/executivo\/?$/.test(path)

/** `demo` e `executivo`: as páginas /demo e /demo/executivo, passadas pelo ponto de entrada (no navegador, carregadas à parte). */
export default function App({ path = '/', demo, executivo }: { path?: string; demo?: ReactNode; executivo?: ReactNode }) {
  const reduce = useReducedMotion() ?? false
  useEffect(() => {
    const onClick = (e: MouseEvent) => handleAnchorClick(e, reduce)
    document.addEventListener('click', onClick)
    return () => document.removeEventListener('click', onClick)
  }, [reduce])

  return (
    // reducedMotion="user": respeita prefers-reduced-motion em todas as animações do Motion.
    <MotionConfig reducedMotion="user">
      {isExecutivo(path) ? executivo : isDemo(path) ? demo : <>
      <Header />
      <main id="conteudo">
        <Hero />
        <BusinessSummary />
        <Challenge />
        <NormToAction />
        <ProductDemo />
        <Approach />
        <Audience />
        <Stakes />
        <Opportunity />
      </main>
      <Closing />
      </>}
    </MotionConfig>
  )
}
