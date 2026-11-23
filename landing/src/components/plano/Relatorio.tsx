import { LinkFonte } from '../ui/LinkFonte'
import { plano } from '../../content/plano'
import { useEffect } from 'react'
import { montarRelatorio } from '../../content/relatorio'
import { ABERTURA_PERGUNTAS } from '../../content/perguntas'
import type { Diagnosticos, Modo, Simulacao } from '../../content/plano'
import { useRespostas } from './Respostas'
import { RascunhosAneel } from './RascunhosAneel'

// Relatório de trabalho para imprimir ou salvar em PDF (A4). Fica fora da tela e só existe enquanto imprime:
// o botão "Baixar meu relatório" monta, abre a impressão e desmonta. Nada sai do navegador.
export function Relatorio({ ativo, fim, diag, sim, modo }: { ativo: boolean; fim: () => void; diag: Diagnosticos; sim: Simulacao | null; modo: Modo }) {
  const { respostas, revisoes } = useRespostas()
  useEffect(() => {
    if (!ativo) return
    const espera = setTimeout(() => window.print(), 300) // dá tempo de as respostas do navegador carregarem
    window.addEventListener('afterprint', fim)
    return () => { clearTimeout(espera); window.removeEventListener('afterprint', fim) }
  }, [ativo, fim])
  if (!ativo) return null
  const r = montarRelatorio({ sim, modo, diag, respostas, revisoes })
  const vazio = !Object.values(respostas.jaFazemos).some(Boolean) && !Object.values(respostas.provas).some((p) => p.length) && !Object.keys(diag).length
  return <section id="relatorio" aria-label="Relatório de trabalho" className="relatorio">
    <header>
      <h1>Relatório de trabalho · {r.cabecalho.norma}</h1>
      <p>{r.cabecalho.porte} · {r.cabecalho.data} · dias dos prazos contados até {r.cabecalho.prazosAte}</p>
      <p><strong>{r.cabecalho.aviso}</strong></p>
    </header>

    <h2>Resumo executivo</h2>
    <div className="rel-numeros">
      <p><span>{r.numeros.exposicao}</span>{r.numeros.porInfracao}</p>
      <p><span>{r.numeros.reducao}</span>se agir antes da fiscalização</p>
      <p><span>{r.numeros.prazo.valor}</span>{r.numeros.prazo.legenda}</p>
    </div>
    {r.prontidao && <p><strong>{r.prontidao}</strong></p>}
    <h3>3 decisões para esta semana</h3>
    <ol>{r.decisoes.map((d) => <li key={d.nome}><strong>{d.nome}</strong> · {d.porque}</li>)}</ol>
    {vazio && <p className="rel-nota">Nada foi preenchido ainda: as colunas “O que vocês já fazem” e “Situação” ficam em branco para completar à mão ou no site.</p>}

    <h2>Por tema</h2>
    <table>
      <thead><tr><th>O que a norma exige</th><th>Prazo</th><th>Exposição por infração</th><th>O que recomendamos <small>(Sugestão da IA, a revisar)</small></th><th>O que provar</th><th>O que vocês já fazem</th><th>Situação</th></tr></thead>
      <tbody>{r.temas.map((t) => <tr key={t.id}>
        <td><strong>{t.nome}</strong><br />{t.citacao}<br /><small><LinkFonte sha256={plano.norma.sha256} trecho={t.citacao}>{t.dispositivo}</LinkFonte></small></td>
        <td>{t.prazo}</td>
        <td>{t.exposicao ? <>teto {t.exposicao.teto}{t.exposicao.preliminar ? '*' : ''}{t.exposicao.ii && <><br />art. 24, II: {t.exposicao.ii}</>}{t.exposicao.i && <><br />art. 24, I: {t.exposicao.i}</>}</> : 'a enquadrar'}</td>
        <td>{t.acoes.length ? <ul>{t.acoes.map((a) => <li key={a}>{a}</li>)}</ul> : 'em revisão'}</td>
        <td><ul className="rel-provas">{t.provas.map((p) => <li key={p.id}>{p.marcada ? '✓' : '☐'} {p.texto}</li>)}</ul></td>
        <td>{t.jaFazemos || ' '}</td>
        <td>{t.situacao}</td>
      </tr>)}</tbody>
    </table>
    <p className="rel-nota">* preliminar: enquadramento sugerido pela IA, aguardando revisão humana. Valores por infração, nunca somados; ilustrativos.</p>

    <h2>Lacunas a tratar</h2>
    {r.lacunas.length ? <ol>{r.lacunas.map((l) => <li key={l.nome}><strong>{l.nome}</strong> · {l.motivo}</li>)}</ol> : <p>Nenhuma lacuna marcada. Marque “Já temos”, “Parcial” ou “Não temos” em cada tema para listar as lacunas.</p>}

    <h2>Quem faz o quê <small>(áreas sugeridas; títulos resumidos por IA, a revisar)</small></h2>
    <ul>{r.areas.map((a) => <li key={a.area}>{a.frase}</li>)}</ul>

    <h2>Revisões pessoais deste navegador</h2>
    <p>Informações confirmadas ou corrigidas por você; não alteram os cálculos nem validam juridicamente a análise automática.</p>
    {r.revisoes.length ? <ul>{r.revisoes.map((v) => <li key={`${v.id}:${v.campo}`}>
      <strong>{v.dispositivo} · {v.campo} · {v.estado === 'confirmado' ? 'confirmado por você' : 'corrigido por você'}</strong>
      <p>Valor original: {v.original}. Sua revisão: {v.valor}.</p>
      <blockquote><LinkFonte sha256={plano.norma.sha256} trecho={v.trecho}>“{v.trecho}”</LinkFonte></blockquote>
    </li>)}</ul> : <p>Nenhuma revisão pessoal registrada.</p>}

    {r.errosMateriais.length > 0 && <><h2>Possíveis erros materiais da norma</h2><ul>{r.errosMateriais.map((e, i) => <li key={e}><LinkFonte sha256={plano.norma.sha256} trecho={plano.erros_materiais?.[i]?.trecho}>{e}</LinkFonte></li>)}</ul></>}

    <h2>Perguntas para levar ao jurídico</h2>
    <p>{ABERTURA_PERGUNTAS}</p>
    <ol>{r.perguntas.map((q, i) => <li key={i}>{q.pergunta} <small>({q.dispositivo}) {q.citacao} · {q.fontes.map((f, j) => <span key={j}>{j > 0 && ' · '}<LinkFonte sha256={f.sha256} trecho={f.trecho}>{f.rotulo}</LinkFonte></span>)}</small></li>)}</ol>
    <h2>Perguntas para a ANEEL</h2>
    <p>Rascunhos agrupados por dúvida e leituras registradas. Revisar antes de enviar; não foram enviados à ANEEL.</p>
    <RascunhosAneel rascunhos={r.perguntasAneel} />
  </section>
}
