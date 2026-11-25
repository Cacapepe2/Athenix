import { plano, type Obrigacao } from '../../content/plano'
import { fraseComparacao } from '../../content/comparacao'
import { LinkFonte } from '../ui/LinkFonte'

/** Uma frase sobre a origem da obrigação no PRODIST. Sem histórico: nada. A divergência entre fontes atuais continua à mostra. */
export function ComparacaoAnterior({ o }: { o: Obrigacao }) {
  const c = plano.comparacao_anterior
  const r = c?.registros[o.id]
  if (!c || !r) return null
  const item = c.itens[r.item]
  return <section aria-label="Comparação histórica" className="space-y-3 text-sm text-ink-soft">
    <p>{fraseComparacao(r.classe)}</p>
    {r.classe === 'alterado' && item.anterior && <div className="grid gap-4 text-obsidian sm:grid-cols-2">
      <div><strong>Antes · item {r.item}</strong><blockquote><LinkFonte sha256={c.fontes.v2.sha256} trecho={item.anterior.trecho}>“{item.anterior.trecho}”</LinkFonte></blockquote></div>
      <div><strong>Atual · item {r.item}</strong><blockquote><LinkFonte sha256={c.fontes.v3.sha256} trecho={item.atual.trecho}>“{item.atual.trecho}”</LinkFonte></blockquote></div>
    </div>}
    {!r.confere_v3 && <details className="border border-slate-blue/30 p-3 text-obsidian">
      <summary className="min-h-11 cursor-pointer font-semibold">Divergência entre o texto publicado da RN e a versão compilada do PRODIST — revisar</summary>
      <p>As fontes atuais não conferem literalmente. A redação usada no plano e sua contagem foram preservadas.</p>
      <div className="mt-3 grid gap-4 sm:grid-cols-2">
        <div><strong>Fonte usada no plano · {o.dispositivo}</strong><blockquote><LinkFonte sha256={plano.norma.sha256} trecho={o.trecho ?? ''}>“{o.trecho}”</LinkFonte></blockquote></div>
        <div><strong>PRODIST compilado · item {r.item}</strong><blockquote><LinkFonte sha256={c.fontes.v3.sha256} trecho={item.atual.trecho}>“{item.atual.trecho}”</LinkFonte></blockquote></div>
      </div>
    </details>}
  </section>
}
