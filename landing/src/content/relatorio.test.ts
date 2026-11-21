import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { AVISO_RELATORIO, extrasDoCsv, montarRelatorio } from './relatorio.ts'
import { definirJaFazemos, alternarProva, RESPOSTAS_VAZIAS } from './respostas.ts'
import { csvPlano, plano, SIM_INICIAL } from './plano.ts'
import { provasDoTema } from './recomendacoes.ts'
import { prazos, queda, valorGeral } from './executivo.ts'

const sim = { base: 5e9, faturamento: null }
const hoje = new Date(2026, 10, 20, 23, 30) // 20/11/2026, 23h30 no fuso local

test('relatório vazio é legível: cabeçalho, números, temas, áreas e aviso, sem nada preenchido', () => {
  const r = montarRelatorio({ sim, modo: 'preliminar', diag: {}, respostas: RESPOSTAS_VAZIAS, hoje })
  assert.equal(r.cabecalho.aviso, AVISO_RELATORIO)
  assert.equal(r.cabecalho.data, '20/11/2026')
  assert.equal(r.temas.length, plano.temas.length)
  for (const t of r.temas) assert.ok(t.nome && t.dispositivo && t.provas.every((p) => !p.marcada) && t.jaFazemos === '' && t.situacao === 'Não informado')
  assert.ok(r.areas.length > 0 && r.areas.every((a) => /obrigações/.test(a.frase)))
  assert.ok(r.decisoes.length <= 3 && r.decisoes.length > 0)
})

test('os três números do relatório são os da executiva (nunca somados)', () => {
  const r = montarRelatorio({ sim, modo: 'preliminar', diag: {}, respostas: RESPOSTAS_VAZIAS, hoje })
  const v = valorGeral(plano, sim, 'preliminar')!
  const q = queda(plano, sim, 'preliminar')!
  assert.match(r.numeros.exposicao, /^R\$ /)
  assert.equal(r.numeros.reducao, `−${Math.round(q.reducaoPct)}%`)
  const pz = prazos(plano)
  assert.equal(r.numeros.prazo.valor, pz.vencidas > 0 ? String(pz.vencidas) : pz.proxima ? `${pz.proxima.dias} dias` : '—')
  assert.ok(v.reais != null)
})

test('o texto e as provas marcadas aparecem no relatório e a situação informada também', () => {
  const t = plano.temas[0]
  const prova = provasDoTema(plano, t.obrigacoes.map((id) => plano.obrigacoes.find((o) => o.id === id)!))[0]
  let resp = definirJaFazemos(RESPOSTAS_VAZIAS, t.id, 'Plano aprovado em 2025, sem revisão anual.')
  resp = alternarProva(resp, t.id, prova.id)
  const r = montarRelatorio({ sim, modo: 'preliminar', diag: { [t.id]: 'parcial' }, respostas: resp, hoje })
  const linha = r.temas.find((x) => x.id === t.id)!
  assert.equal(linha.jaFazemos, 'Plano aprovado em 2025, sem revisão anual.')
  assert.equal(linha.situacao, 'Parcial')
  assert.ok(linha.provas.find((p) => p.id === prova.id)!.marcada)
  assert.ok(r.lacunas.some((l) => l.nome === t.nome && /Parcial/.test(l.motivo)))
})

test('CSV: colunas novas (o_que_ja_fazemos, situacao, provas_marcadas, area, sujeito) com o que foi escrito e marcado', () => {
  const t = plano.temas[0]
  const os = t.obrigacoes.map((id) => plano.obrigacoes.find((o) => o.id === id)!)
  const prova = provasDoTema(plano, os)[0]
  const resp = alternarProva(definirJaFazemos(RESPOSTAS_VAZIAS, t.id, 'Já temos o registro.'), t.id, prova.id)
  const csv = csvPlano({ [t.id]: 'sim' }, SIM_INICIAL, extrasDoCsv(resp, { [t.id]: 'sim' }))
  const linhas = csv.replace('﻿', '').trimEnd().split('\r\n')
  const cab = linhas.find((l) => l.includes('o_que_ja_fazemos'))!
  assert.match(cab, /"o_que_ja_fazemos";"situacao";"provas_marcadas";"area";"sujeito"$/)
  assert.ok(csv.includes('"Já temos o registro."') && csv.includes(`"${prova.texto}"`) && csv.includes('"Já temos"'))
  assert.ok(os.every((o) => csv.includes(`"${o.area}"`)))
  // sem respostas, as colunas existem e ficam vazias
  assert.match(csvPlano({}, SIM_INICIAL, extrasDoCsv(RESPOSTAS_VAZIAS)), /"o_que_ja_fazemos";"situacao";"provas_marcadas";"area";"sujeito"/)
})

test('o relatório não usa rede', () => {
  for (const arq of ['./relatorio.ts', '../components/plano/Relatorio.tsx']) {
    assert.doesNotMatch(readFileSync(new URL(arq, import.meta.url), 'utf-8'), /\bfetch\s*\(|XMLHttpRequest|sendBeacon/)
  }
})
