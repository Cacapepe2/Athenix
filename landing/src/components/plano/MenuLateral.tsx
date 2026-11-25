import { useEffect, useState, type ReactNode } from 'react'
import { ChevronDown } from 'lucide-react'

export interface ItemMenu { rotulo: string; href: string }
export interface GrupoMenu { id: string; rotulo: string; itens?: ItemMenu[]; conteudo?: ReactNode }

/** Abre o bloco recolhido (<details>) do destino antes de rolar até ele. */
function abrirDestino(href: string) {
  const d = document.getElementById(href.slice(1))?.closest('details')
  if (d) d.open = true
}

/** Menu do plano: tópicos principais; o tópico em leitura se abre sozinho e mostra os seus subtópicos. Fixo ao lado no
 *  computador; no celular, recolhido acima do conteúdo. */
export function MenuLateral({ grupos }: { grupos: GrupoMenu[] }) {
  const [atual, setAtual] = useState(grupos[0].id)
  const [aberto, setAberto] = useState<string | null>(grupos[0].id)
  const [visivel, setVisivel] = useState(false) // só no celular
  const ids = grupos.map((g) => g.id).join(' ')
  // Tópico em leitura: o último cujo início já passou do primeiro terço da tela.
  useEffect(() => {
    let quadro = 0
    const medir = () => {
      quadro = 0
      const passou = ids.split(' ').filter((id) => (document.getElementById(id)?.getBoundingClientRect().top ?? Infinity) < window.innerHeight / 3)
      setAtual(passou.at(-1) ?? ids.split(' ')[0])
    }
    const rolar = () => { quadro ||= requestAnimationFrame(medir) }
    medir()
    window.addEventListener('scroll', rolar, { passive: true })
    return () => { window.removeEventListener('scroll', rolar); cancelAnimationFrame(quadro) }
  }, [ids])
  useEffect(() => setAberto(atual), [atual])

  const ir = (id: string, i?: ItemMenu) => {
    abrirDestino(i?.href ?? `#${id}`)
    setVisivel(false)
  }
  return <nav aria-label="Tópicos do plano" className="menu-lateral print:hidden">
    <button type="button" className="botao menu-abrir" aria-expanded={visivel} aria-controls="menu-topicos" onClick={() => setVisivel(!visivel)}>Tópicos do plano<ChevronDown aria-hidden="true" className={`h-4 w-4 ${visivel ? 'rotate-180' : ''}`} /></button>
    <ul id="menu-topicos" className={`menu-topicos ${visivel ? '' : 'hidden'} xl:block`}>
      {grupos.map((g) => <li key={g.id} className="border-b border-line">
        <div className="flex items-stretch">
          <a href={`#${g.id}`} aria-current={atual === g.id ? 'location' : undefined} className="menu-topico" onClick={() => ir(g.id)}>{g.rotulo}</a>
          <button type="button" className="grid min-h-11 w-10 shrink-0 cursor-pointer place-items-center hover:bg-stone" aria-expanded={aberto === g.id} aria-controls={`menu-${g.id}`} aria-label={`Subtópicos de ${g.rotulo}`} onClick={() => setAberto(aberto === g.id ? null : g.id)}><ChevronDown aria-hidden="true" className={`h-4 w-4 transition-transform ${aberto === g.id ? 'rotate-180' : ''}`} /></button>
        </div>
        <div id={`menu-${g.id}`} className="menu-sub" data-aberto={aberto === g.id} inert={aberto !== g.id}>
          <div>{g.conteudo}{g.itens && <ul>{g.itens.map((i) => <li key={i.rotulo}><a href={i.href} className="block py-2 pr-2 pl-4 text-[13px] leading-snug hover:underline" onClick={() => ir(g.id, i)}>{i.rotulo}</a></li>)}<li aria-hidden="true" className="h-2" /></ul>}</div>
        </div>
      </li>)}
    </ul>
  </nav>
}
