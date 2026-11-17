import { articleById, brl, demoNorm, profile, type Obligation } from '../../content/demo'

export function ImpactExample({ item: o, explain = false }: { item: Obligation; explain?: boolean }) {
  const group = o.impact.groups.join(', ')
  return (
    <article className="impact-example lg:has-[details[open]]:col-span-3 rounded-2xl border border-line bg-white p-5 sm:p-7">
      <p className="mb-2 text-xs font-semibold tracking-widest text-bronze-deep uppercase">{o.position ? `Prioridade ${o.position}` : 'Enquadramento a confirmar'}</p>
      <h3 className="font-display text-2xl leading-tight text-obsidian">{o.short}</h3>
      <p className="mt-3 text-sm font-semibold text-slate-blue">{o.deadline}</p>
      <p className="mt-4 text-lg font-semibold leading-snug text-obsidian">De advertência (sem multa) até {brl(o.impact.groupCapPct / 100 * profile.base)} (teto do Grupo {group})</p>
      <dl className="mt-5 grid gap-4 border-y border-line py-4 text-sm sm:grid-cols-3">
        <div><dt className="text-ink-soft">Mínimo</dt><dd className="mt-1 font-medium">Advertência (sem multa)</dd></div>
        <div><dt className="text-ink-soft">Provável</dt><dd className="mt-1 font-medium">{o.impact.probable === null ? 'Não estimável' : brl(o.impact.probable)}</dd></div>
        <div><dt className="text-ink-soft">Máximo estimado</dt><dd className="mt-1 font-medium">{brl(o.impact.max)}</dd></div>
      </dl>
      <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
        <p>Confiança: <strong className="rounded-full bg-stone px-2 py-1">{o.confidence}</strong></p>
        <p>{o.impact.framings.length ? o.impact.framings.map((f) => `${f.dispositivo} · Grupo ${f.grupo}`).join('; ') : 'Infração ainda não identificada'}</p>
      </div>
      <p className="mt-3 text-xs text-ink-soft">Fonte: <a className="underline" href={demoNorm.url}>RN ANEEL 1.137/2025 · {articleById(o.articleId).label}</a></p>
      {explain && <details className="why mt-5 border-t border-line pt-4">
        <summary className="cursor-pointer font-semibold text-slate-blue">Por quê — veja o fundamento</summary>
        <div className="space-y-5 pt-5 text-sm leading-relaxed">
          <div><h4 className="font-semibold">O que a norma diz</h4><blockquote className="mt-2 border-l-2 border-bronze bg-ivory p-4">“{o.anchor}”</blockquote><p className="mt-2 text-xs">{articleById(o.articleId).label} · trecho literal, conferido na fonte.</p></div>
          <div><h4 className="font-semibold">Infração da REN 846</h4>{o.impact.framings.map((f) => <blockquote key={f.dispositivo} className="mt-2 border-l-2 border-slate-blue bg-ivory p-4"><strong>{f.dispositivo} · Grupo {f.grupo}</strong><p>“{f.trecho}”</p></blockquote>)}{!o.impact.framings.length && <p>Sem enquadramento identificado. Exige análise antes de entrar nas prioridades.</p>}</div>
          <div><h4 className="font-semibold">O que limita esta estimativa</h4><p>{o.confidenceReason}</p><p>{o.impact.probableReason}</p><p>{o.deadlineDetail} Data de referência: {profile.referenceDate}.</p></div>
          <div><h4 className="font-semibold">Premissas</h4><ul className="list-disc space-y-1 pl-5">{o.impact.premises.map((p) => <li key={p}>{p}</li>)}</ul></div>
          <div><h4 className="font-semibold">Fontes do cálculo</h4><p>{o.impact.sources.join(' · ')}</p><p className="mt-2">Parâmetros da REN 846 obtidos de cópia secundária; conferência com a fonte oficial e revisão de especialista pendentes. O máximo considera os cenários e o teto legal descritos nas premissas.</p><p className="mt-2">A descrição curta é um resumo de apresentação; o texto normativo é o trecho literal acima.</p></div>
        </div>
      </details>}
    </article>
  )
}
