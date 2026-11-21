import { useEffect, useState } from 'react'
import { AnimatePresence, motion, useMotionValueEvent, useScroll, useSpring } from 'motion/react'
import { Menu, X } from 'lucide-react'
import { Logo } from '../ui/Logo'
import { ButtonLink } from '../ui/Button'
import { nav } from '../../content/site'

export function Header() {
  const { scrollY, scrollYProgress } = useScroll()
  const progress = useSpring(scrollYProgress, { stiffness: 200, damping: 40 })
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)
  const [under, setUnder] = useState(false)
  useMotionValueEvent(scrollY, 'change', (y) => {
    setScrolled(y > 24)
    // O tema do header acompanha a seção que está sob ele (seções escuras levam data-dark).
    setUnder(document.elementsFromPoint(window.innerWidth / 2, 40).some((el) => el instanceof HTMLElement && 'dark' in el.dataset))
  })
  const dark = under && !open

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-[background-color,border-color] duration-500 ${
        dark
          ? 'on-dark border-b border-ivory/10 bg-obsidian/80 backdrop-blur-xl'
          : scrolled || open
            ? 'border-b border-obsidian/8 bg-ivory/85 backdrop-blur-xl'
            : 'border-b border-transparent'
      }`}
    >
      <a
        href="#conteudo"
        className="sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:focus:bg-obsidian focus:px-4 focus:py-2 focus:text-ivory"
      >
        Pular para o conteúdo
      </a>
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-6 px-5 sm:px-8">
        <a href="#topo" className="flex items-center gap-4" aria-label="Athenix, voltar ao início">
          <Logo tone={dark ? 'light' : 'dark'} />
          <span aria-hidden="true" className={`hidden h-6 w-px xl:block ${dark ? 'bg-ivory/20' : 'bg-obsidian/15'}`} />
          <span className={`hidden text-[0.8rem] xl:block ${dark ? 'text-ivory/60' : 'text-ink-soft'}`}>{nav.tagline}</span>
        </a>

        <nav aria-label="Principal" className="hidden lg:block">
          <ul className={`flex items-center gap-7 text-[0.88rem] ${dark ? 'text-ivory/75' : 'text-obsidian/80'}`}>
            {nav.links.map((l) => (
              <li key={l.href}>
                <a
                  href={l.href}
                  className="relative py-1 transition-colors after:absolute after:inset-x-0 after:-bottom-0.5 after:h-px after:origin-left after:scale-x-0 after:bg-bronze after:transition-transform after:duration-300 hover:opacity-100 hover:after:scale-x-100"
                >
                  {l.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="flex items-center gap-2">
          <ButtonLink href={nav.cta.href} arrow={false} className="!min-h-10 !px-4 text-[0.85rem] max-sm:!hidden">
            {nav.cta.label}
          </ButtonLink>
          <button
            type="button"
            className={`grid h-11 w-11 place-items-center lg:hidden ${dark ? 'text-ivory hover:bg-ivory/10' : 'text-obsidian hover:bg-obsidian/5'}`}
            aria-expanded={open}
            aria-controls="menu-movel"
            aria-label={open ? 'Fechar menu' : 'Abrir menu'}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {open && (
          <motion.nav
            id="menu-movel"
            aria-label="Menu"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden lg:hidden"
          >
            <ul className="mx-auto max-w-7xl space-y-1 px-5 pt-2 pb-6 sm:px-8">
              {[...nav.links, nav.cta].map((l) => (
                <li key={l.href}>
                  <a
                    href={l.href}
                    onClick={() => setOpen(false)}
                    className="font-display block border-b border-obsidian/8 py-3 text-xl text-obsidian"
                  >
                    {l.label}
                  </a>
                </li>
              ))}
            </ul>
          </motion.nav>
        )}
      </AnimatePresence>

      <motion.div
        aria-hidden="true"
        style={{ scaleX: progress }}
        className="absolute inset-x-0 bottom-[-1px] h-px origin-left bg-bronze"
      />
    </header>
  )
}
