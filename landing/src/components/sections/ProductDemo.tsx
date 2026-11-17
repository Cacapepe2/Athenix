import { demoNorm, priorities } from '../../content/demo'
import { ImpactExample } from '../product/ImpactExample'
import { ButtonLink } from '../ui/Button'

export function ProductDemo() {
  return <section id="demonstracao" className="bg-stone/55 py-20 sm:py-28">
    <div className="mx-auto grid max-w-7xl gap-10 px-5 sm:px-8 lg:grid-cols-2 lg:items-center">
      <div>
        <p className="text-xs font-semibold tracking-widest text-bronze-deep uppercase">{demoNorm.badge}</p>
        <h2 className="font-display mt-5 text-4xl leading-tight sm:text-5xl">Uma obrigação. O prazo. O impacto.</h2>
        <p className="mt-5 max-w-lg leading-relaxed text-ink-soft">Veja o que uma mudança da ANEEL pede à empresa e o que merece atenção primeiro. Cada estimativa mostra confiança e fonte.</p>
        <p className="mt-4 text-sm leading-relaxed text-ink-soft">Exemplo da RN 1.137/2025 com uma distribuidora ilustrativa. Iniciativa em validação; estimativas e enquadramentos ainda sem revisão de especialista. Não constitui parecer jurídico.</p>
        <ButtonLink href="/demo" className="mt-7">Ver demonstração completa</ButtonLink>
      </div>
      <ImpactExample item={priorities[0]} />
    </div>
  </section>
}
