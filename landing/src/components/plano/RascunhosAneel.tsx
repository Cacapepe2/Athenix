import type { RascunhoAneel } from '../../content/rascunhos-aneel'

export function RascunhosAneel({ rascunhos }: { rascunhos: RascunhoAneel[] }) {
  return <ol className="space-y-4 text-sm">
    {rascunhos.map((r) => <li key={r.id} data-rascunho={r.id} className="border border-line p-3">
      <p className="font-bold">{r.rotulo}</p>
      <p className="mt-1 font-semibold">{r.duvida}</p>
      <p className="mt-2 font-semibold">Leituras possíveis · hipóteses para revisar</p>
      <ul className="mt-1 list-disc space-y-1 pl-5">{r.leituras_possiveis.map((l) => <li key={l}>{l}</li>)}</ul>
      {r.limite && <p className="mt-2 text-xs">{r.limite}</p>}
      <ul className="mt-3 space-y-3">{r.referencias.map((f, i) => <li key={i}>
        <p className="font-semibold">{f.dispositivo}</p>
        <blockquote className="mt-1 border-l-2 border-obsidian pl-3">“{f.trecho}”</blockquote>
        <p className="mt-1 break-all text-xs">{f.fonte.titulo} · SHA-256 {f.fonte.sha256}</p>
        {f.possiveis_esclarecimentos.map((e, j) => <div key={j} className="mt-2 border border-line p-2 text-xs">
          <p className="font-semibold">Possível esclarecimento · vínculo com esta dúvida ainda não confirmado</p>
          <blockquote className="mt-1">“{e.citacao}”</blockquote>
          <p className="mt-1 break-all"><a className="font-semibold underline underline-offset-4" href={e.fonte.url} target="_blank" rel="noopener noreferrer">{e.fonte.titulo}</a> · consulta {e.fonte.consultado_em} · SHA-256 {e.fonte.sha256}</p>
        </div>)}
      </li>)}</ul>
      <p className="mt-3 text-xs">Pedido ainda não enviado. Revise a pergunta e as hipóteses com o responsável regulatório.</p>
    </li>)}
  </ol>
}
