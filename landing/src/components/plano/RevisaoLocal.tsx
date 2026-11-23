import { useState } from 'react'
import { normaDaUrl, plano, type Obrigacao } from '../../content/plano'
import { camposDaObrigacao, exportarRevisoes, LIMITE_CORRECAO, ROTULOS_REVISAO, type CampoRevisao } from '../../content/revisoes'
import { useRespostas } from './Respostas'
import { LinkFonte } from '../ui/LinkFonte'

const BOTAO = 'min-h-11 cursor-pointer rounded-lg border border-slate-blue/40 px-3 py-2 text-sm font-semibold text-slate-blue hover:bg-slate-blue/5 disabled:cursor-default disabled:opacity-50'

function Campo({ o, campo, original }: { o: Obrigacao; campo: CampoRevisao; original: string }) {
  const { revisoes, revisar, limpar } = useRespostas()
  const [editando, setEditando] = useState(false)
  const [texto, setTexto] = useState('')
  const r = revisoes[o.id]?.[campo]
  return <div className="border-t border-line pt-3" data-campo-revisao={campo}>
    <p><strong>{ROTULOS_REVISAO[campo]}:</strong> {original}</p>
    <p aria-live="polite" className="mt-1 text-sm">{r ? r.estado === 'confirmado' ? 'Confirmado por você neste navegador.' : `Corrigido por você: ${r.valor}` : 'Sem revisão pessoal.'}</p>
    {editando ? <form className="mt-2 space-y-2" onSubmit={(e) => { e.preventDefault(); if (texto.trim()) { revisar(o, campo, texto); setEditando(false) } }}>
      <label className="block text-sm">Correção de {ROTULOS_REVISAO[campo].toLowerCase()}
        <input autoFocus type="text" value={texto} required maxLength={LIMITE_CORRECAO} onChange={(e) => setTexto(e.target.value)} className="mt-1 block min-h-11 w-full rounded-lg border border-slate-blue/40 bg-white px-3 text-obsidian" />
      </label>
      <div className="flex flex-wrap gap-2"><button className={BOTAO} disabled={!texto.trim()} type="submit">Salvar correção</button><button className={BOTAO} type="button" onClick={() => setEditando(false)}>Cancelar</button></div>
    </form> : <div className="mt-2 flex flex-wrap gap-2">
      <button className={BOTAO} type="button" onClick={() => revisar(o, campo)}>Confirmar</button>
      <button className={BOTAO} type="button" onClick={() => { setTexto(r?.valor ?? ''); setEditando(true) }}>Corrigir</button>
      {r && <button className={BOTAO} type="button" onClick={() => limpar(o.id, campo)}>Limpar revisão</button>}
    </div>}
  </div>
}

export function RevisaoLocal({ o }: { o: Obrigacao }) {
  const { revisoes, revisoesPersistentes } = useRespostas()
  const baixar = () => {
    const url = URL.createObjectURL(new Blob([exportarRevisoes(revisoes, normaDaUrl(), plano)], { type: 'application/json;charset=utf-8' }))
    Object.assign(document.createElement('a'), { href: url, download: `athenix-revisoes-${normaDaUrl()}.json` }).click()
    URL.revokeObjectURL(url)
  }
  return <section aria-label="Revisão pessoal" className="space-y-3 rounded-xl border border-slate-blue/30 bg-ivory p-4 print:hidden">
    <h5 className="font-semibold">Sua revisão neste navegador</h5>
    <p className="text-sm text-ink-soft">Confirme ou corrija sua leitura. Fica só neste navegador e aparece no relatório; os cálculos e as sugestões da análise automática continuam com os valores originais.</p>
    {!revisoesPersistentes && <p role="status" className="text-sm font-semibold">O navegador bloqueou o armazenamento. Suas revisões ficam em memória e serão perdidas ao fechar; exporte o JSON para guardá-las.</p>}
    {Object.entries(camposDaObrigacao(o)).map(([campo, original]) => <Campo key={campo} o={o} campo={campo as CampoRevisao} original={original} />)}
    {o.area_ia && <p className="text-sm" data-area-ia><strong>{o.area_ia.rotulo}</strong> · Sugestão, aguarda revisão humana. Trecho citado: <LinkFonte sha256={plano.norma.sha256} trecho={o.area_ia.trecho}>“{o.area_ia.trecho}”</LinkFonte></p>}
    {o.area_motivo && <p className="text-sm" data-area-motivo>Área continua “A definir”: {o.area_motivo}.</p>}
    <button className={BOTAO} type="button" onClick={baixar} disabled={!Object.keys(revisoes).length}>Exportar revisões desta norma (JSON)</button>
  </section>
}
