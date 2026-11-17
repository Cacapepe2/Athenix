import { animate } from 'motion/react'

let current: { stop: () => void } | undefined

/**
 * Rolagem animada quadro a quadro. A rolagem suave nativa era encerrada antes do destino
 * ao atravessar a seção fixa "Da norma à ação" (quadros pesados), então não dependemos dela.
 */
export function scrollToY(top: number, instant = false) {
  current?.stop()
  if (instant) return window.scrollTo({ top, behavior: 'instant' })
  const stop = () => current?.stop()
  // O usuário retoma o controle ao rolar ou tocar.
  window.addEventListener('wheel', stop, { once: true, passive: true })
  window.addEventListener('touchstart', stop, { once: true, passive: true })
  const distance = Math.abs(top - window.scrollY)
  current = animate(window.scrollY, top, {
    duration: Math.min(1.4, 0.45 + distance / 7000),
    ease: [0.65, 0, 0.35, 1],
    onUpdate: (v) => window.scrollTo({ top: v, behavior: 'instant' }),
  })
}

/** Intercepta links internos (#id): rola até o alvo, atualiza a URL e move o foco para ele. */
export function handleAnchorClick(e: MouseEvent, instant: boolean) {
  if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return
  const link = (e.target as Element | null)?.closest?.('a[href^="#"]')
  const id = link?.getAttribute('href')?.slice(1)
  const target = id ? document.getElementById(id) : null
  if (!target) return
  e.preventDefault()
  const margin = parseFloat(getComputedStyle(target).scrollMarginTop) || 0
  scrollToY(target.getBoundingClientRect().top + window.scrollY - margin, instant)
  history.pushState(null, '', `#${id}`)
  if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1')
  target.focus({ preventScroll: true })
}
