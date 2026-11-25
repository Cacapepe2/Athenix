import { OPCOES, FILTROS_TODAS, type Filtros } from '../../content/filtros'

/** Filtros da seção "Obrigações", dentro do menu lateral. */
export function FiltrosMenu({ filtros, mudar }: { filtros: Filtros; mudar: (f: Filtros) => void }) {
  return <div className="flex flex-col gap-3 pt-1 pb-4 pl-4">
    {OPCOES.map((g) => <fieldset key={g.chave} className="flex flex-col">
      <legend className="mb-1 p-0 text-[13px] font-bold">{g.titulo}</legend>
      {g.opcoes.map((o) => <button key={o.valor} type="button" className="filtro" aria-pressed={filtros[g.chave] === o.valor} onClick={() => mudar({ ...filtros, [g.chave]: o.valor })}>{o.rotulo}</button>)}
    </fieldset>)}
    <button type="button" className="seg" disabled={OPCOES.every((g) => filtros[g.chave] === 'todas')} onClick={() => mudar(FILTROS_TODAS)}>Limpar filtros</button>
  </div>
}
