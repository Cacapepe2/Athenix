import { useState } from 'react'
import { Eraser, PenLine } from 'lucide-react'
import { normaDaUrl, plano, type Obrigacao } from '../../content/plano'
import { camposDaObrigacao, exportarRevisoes, LIMITE_CORRECAO, ROTULOS_REVISAO, type CampoRevisao } from '../../content/revisoes'
import { useRespostas } from './Respostas'
import { LinkFonte } from '../ui/LinkFonte'

const BOTAO = 'min-h-11 cursor-pointer rounded-lg border border-slate-blue/40 px-3 py-2 text-sm font-semibold text-slate-blue hover:bg-slate-blue/5 disabled:cursor-default disabled:opacity-50'
const ESCOLHA = `${BOTAO} escolha`

function Campo({ o, campo, original }: { o: Obrigacao; campo: CampoRevisao; original: string }) {
  const { revisoes, revisar, limpar } = useRespostas()
  const [editando, setEditando] = useState(false)
  const [texto, setTexto] = useState('')
  const r = revisoes[o.id]?.[campo]
  return <div className="border-t border-line pt-3" data-campo-revisao={campo}>
    <p><strong>{ROTULOS_REVISAO[campo]}:</strong> {original}</p>
    <p aria-live="polite" className={`mt-1 text-sm ${r ? '' : 'font-semibold text-bronze-deep'}`}>{r ? r.estado === 'confirmado' ? 'Confirmado por você neste navegador.' : `Corrigido por você: ${r.valor}` : 'Aguardando você: confirme ou corrija.'}</p>
    {editando ? <form className="mt-2 space-y-2" onSubmit={(e) => { e.preventDefault(); if (texto.trim()) { revisar(o, campo, texto); setEditando(false) } }}>
      <label className="block text-sm">Correção de {ROTULOS_REVISAO[campo].toLowerCase()}
        <input autoFocus type="text" value={texto} required maxLength={LIMITE_CORRECAO} onChange={(e) => setTexto(e.target.value)} className="mt-1 block min-h-11 w-full rounded-lg border border-slate-blue/40 bg-white px-3 text-obsidian" />
      </label>
      <div className="flex flex-wrap gap-2"><button className={BOTAO} disabled={!texto.trim()} type="submit">Salvar correção</button><button className={BOTAO} type="button" onClick={() => setEditando(false)}>Cancelar</button></div>
    </form> : <div className="mt-2 flex flex-wrap items-center gap-2">
      <button className={ESCOLHA} type="button" aria-pressed={r?.estado === 'confirmado'} onClick={() => revisar(o, campo)}>Confirmar</button>
      <button className={ESCOLHA} type="button" aria-pressed={r?.estado === 'corrigido'} onClick={() => { setTexto(r?.valor ?? ''); setEditando(true) }}>Corrigir</button>
      {r && <button className="botao-limpar" type="button" onClick={() => limpar(o.id, campo)}><Eraser aria-hidden="true" className="h-3.5 w-3.5" />Limpar revisão</button>}
    </div>}
  </div>
}

export function RevisaoLocal({ o }: { o: Obrigacao }) {
  const { revisoes, revisoesPersistentes } = useRespostas()
  const campos = Object.entries(camposDaObrigacao(o))
  const revisados = campos.filter(([c]) => revisoes[o.id]?.[c as CampoRevisao]).length
  const falta = campos.length - revisados
  const baixar = () => {
    const url = URL.createObjectURL(new Blob([exportarRevisoes(revisoes, normaDaUrl(), plano)], { type: 'application/json;charset=utf-8' }))
    Object.assign(document.createElement('a'), { href: url, download: `athenix-revisoes-${normaDaUrl()}.json` }).click()
    URL.revokeObjectURL(url)
  }
  return <section aria-label="Revisão pessoal" className="space-y-3 rounded-xl border border-slate-blue/30 bg-ivory p-4 print:hidden">
    {campos.length > 0 && <div className="flex items-start gap-3 rounded-lg border-2 border-bronze-deep p-3.5" data-participacao>
      <PenLine aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-bronze-deep" />
      <div className="min-w-0" aria-live="polite">
        <p className="text-base leading-snug font-bold text-bronze-deep">{falta ? 'Precisamos da sua leitura' : 'Sua leitura está completa'}</p>
        <p className="mt-0.5 text-sm">{falta ? 'A análise automática só sugere. Leia o texto da norma e, em cada ponto abaixo, confirme ou corrija.' : 'Você pode mudar de ideia a qualquer momento.'} <strong>{revisados} de {campos.length} {campos.length === 1 ? 'ponto revisado' : 'pontos revisados'}.</strong></p>
      </div>
    </div>}
    <h5 className="font-semibold">Sua revisão neste navegador</h5>
    <p className="text-sm text-ink-soft">Confirme ou corrija sua leitura. Fica só neste navegador e aparece no relatório; os cálculos e as sugestões da análise automática continuam com os valores originais.</p>
    {!revisoesPersistentes && <p role="status" className="text-sm font-semibold">O navegador bloqueou o armazenamento. Suas revisões ficam em memória e serão perdidas ao fechar; exporte o JSON para guardá-las.</p>}
    {campos.map(([campo, original]) => <Campo key={campo} o={o} campo={campo as CampoRevisao} original={original} />)}
    {o.area_ia && <p className="text-sm" data-area-ia><strong>{o.area_ia.rotulo}</strong> · Sugestão, aguarda revisão humana. Trecho citado: <LinkFonte sha256={plano.norma.sha256} trecho={o.area_ia.trecho}>“{o.area_ia.trecho}”</LinkFonte></p>}
    {o.area_motivo && <p className="text-sm" data-area-motivo>Área continua “A definir”: {o.area_motivo}.</p>}
    <button className={BOTAO} type="button" onClick={baixar} disabled={!Object.keys(revisoes).length}>Exportar revisões desta norma (JSON)</button>
  </section>
}
