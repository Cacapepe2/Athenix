import { Eraser } from 'lucide-react'
import { OPCOES, FILTROS_TODAS, type Filtros } from '../../content/filtros'

/** Filtros da seção "Obrigações", dentro do menu lateral. */
export function FiltrosMenu({ filtros, mudar }: { filtros: Filtros; mudar: (f: Filtros) => void }) {
  return <div className="pb-3">
    {OPCOES.map((g) => <fieldset key={g.chave} aria-label={g.titulo} className="filtro-grupo">
      <span aria-hidden="true" className="filtro-titulo">{g.titulo}</span>
      <div className="flex min-w-0 flex-col">
      {g.opcoes.map((o) => <button key={o.valor} type="button" className="filtro" aria-pressed={filtros[g.chave] === o.valor} onClick={() => mudar({ ...filtros, [g.chave]: o.valor })}>{o.rotulo}</button>)}
      </div>
    </fieldset>)}
    <button type="button" className="botao-limpar" disabled={OPCOES.every((g) => filtros[g.chave] === 'todas')} onClick={() => mudar(FILTROS_TODAS)}><Eraser aria-hidden="true" className="h-3.5 w-3.5" />Limpar filtros</button>
  </div>
}
