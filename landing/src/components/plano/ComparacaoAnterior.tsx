import { plano, type Obrigacao } from '../../content/plano'
import { CLASSES_HISTORICAS } from '../../content/comparacao'
import { LinkFonte } from '../ui/LinkFonte'

export function ComparacaoAnterior({ o }: { o: Obrigacao }) {
  const c = plano.comparacao_anterior
  if (!c) return null
  const r = c.registros[o.id]
  if (!r) return <section aria-label="Comparação histórica" className="border-t border-line pt-3 text-sm"><strong>Sem fonte anterior para este dispositivo.</strong><p>A comparação disponível cobre apenas o Módulo 4 do PRODIST; este registro permanece sem classificação histórica.</p></section>
  const item = c.itens[r.item]
  return <section aria-label="Comparação histórica" className="space-y-3 border-t border-line pt-3 text-sm">
    <h5 className="font-semibold">{CLASSES_HISTORICAS[r.classe]} · item {r.item} do Módulo 4</h5>
    <p>Comparação documental v2 × v3, anterior e posterior à RN 1.137. {r.classe === 'novo' ? 'O item não consta da v2 fornecida; isso não afirma ausência de dever equivalente em outro ato.' : 'Classificação pela redação do item completo.'}</p>
    <p><a className="font-semibold underline underline-offset-4" href={c.fontes.v2.url + (item.anterior ? `#page=${item.anterior.pagina}` : '')} target="_blank" rel="noopener noreferrer">Fonte oficial anterior: v2</a> · SHA-256 <code className="break-all">{c.fontes.v2.sha256}</code></p>
    {r.classe === 'alterado' && item.anterior && <div className="grid gap-4 sm:grid-cols-2">
      <div><strong>Antes · v2, item {r.item}</strong><blockquote><LinkFonte sha256={c.fontes.v2.sha256} trecho={item.anterior.trecho}>“{item.anterior.trecho}”</LinkFonte></blockquote></div>
      <div><strong>Atual · v3, item {r.item}</strong><blockquote><LinkFonte sha256={c.fontes.v3.sha256} trecho={item.atual.trecho}>“{item.atual.trecho}”</LinkFonte></blockquote></div>
    </div>}
    {!r.confere_v3 && <details className="border border-slate-blue/30 p-3">
      <summary className="min-h-11 cursor-pointer font-semibold">Divergência entre a v3 e a RN 1.137 — revisar</summary>
      <p>As fontes atuais não conferem literalmente. A redação usada no plano e sua contagem foram preservadas.</p>
      <div className="mt-3 grid gap-4 sm:grid-cols-2">
        <div><strong>Fonte usada no plano · {o.dispositivo}</strong><blockquote><LinkFonte sha256={plano.norma.sha256} trecho={o.trecho ?? ''}>“{o.trecho}”</LinkFonte></blockquote></div>
        <div><strong>v3 · item {r.item}</strong><blockquote><LinkFonte sha256={c.fontes.v3.sha256} trecho={item.atual.trecho}>“{item.atual.trecho}”</LinkFonte></blockquote></div>
      </div>
    </details>}
  </section>
}
