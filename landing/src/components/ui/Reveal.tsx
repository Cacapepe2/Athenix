import { motion, type HTMLMotionProps } from 'motion/react'

const ease = [0.16, 1, 0.3, 1] as const

interface Props extends HTMLMotionProps<'div'> {
  delay?: number
  y?: number
}

/** Entrada discreta ao entrar na viewport; reservada para textos de apoio, não para tudo. */
export function Reveal({ delay = 0, y = 18, children, ...rest }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '0px 0px -12% 0px' }}
      transition={{ duration: 0.9, ease, delay }}
      {...rest}
    >
      {children}
    </motion.div>
  )
}

/** Mesmo comportamento de Reveal, para itens de lista. */
export function RevealLi({ delay = 0, y = 18, children, ...rest }: HTMLMotionProps<'li'> & { delay?: number; y?: number }) {
  return (
    <motion.li
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '0px 0px -12% 0px' }}
      transition={{ duration: 0.9, ease, delay }}
      {...rest}
    >
      {children}
    </motion.li>
  )
}

/** Título revelado palavra a palavra por máscara (o texto completo continua acessível). */
export function MaskedTitle({
  text,
  as: Tag = 'h2',
  className = '',
  delay = 0,
}: {
  text: string
  as?: 'h1' | 'h2' | 'h3'
  className?: string
  delay?: number
}) {
  const words = text.split(' ')
  return (
    <Tag className={className} aria-label={text}>
      {words.map((word, i) => (
        <span key={i} aria-hidden="true" className="inline-block overflow-hidden pb-[0.12em] align-top -mb-[0.12em]">
          <motion.span
            className="inline-block"
            initial={{ y: '105%' }}
            whileInView={{ y: '0%' }}
            viewport={{ once: true, margin: '0px 0px -10% 0px' }}
            transition={{ duration: 0.9, ease, delay: delay + i * 0.035 }}
          >
            {word}
            {i < words.length - 1 ? ' ' : ''}
          </motion.span>
        </span>
      ))}
    </Tag>
  )
}

export function Eyebrow({ children, tone = 'dark' }: { children: string; tone?: 'dark' | 'light' }) {
  return (
    <p
      className={`flex items-center gap-3 text-[0.72rem] font-semibold tracking-[0.2em] uppercase ${
        tone === 'dark' ? 'text-bronze-deep' : 'text-bronze'
      }`}
    >
      <span aria-hidden="true" className="h-px w-8 bg-current" />
      {children}
    </p>
  )
}
