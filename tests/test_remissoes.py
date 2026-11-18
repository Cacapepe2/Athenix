"""Remissão a outro ato: resolve só com destino local, como proposta, e nunca corrige a fonte."""

from athenix.config import Settings
from athenix.remissoes import Indice, resolver, resolver_itens
from athenix.structure import extract

DESTINO = """<html><body><p>DECRETO Nº 9.999, DE 20 DE JUNHO DE 2024</p>
<p>CAPÍTULO II</p><p>DAS DIRETRIZES</p>
<p>Art. 4º A agência definirá a minuta do termo aditivo, que contemplará:</p>
<p>V - qualidade na prestação do serviço de distribuição, por meio de indicadores;</p>
<p>VI - obrigação de dar publicidade à qualidade na prestação do serviço de distribuição;</p>
<p>VII - definição de metas de eficiência na recomposição do serviço;</p>
<p>Art. 5º As cláusulas observarão o disposto neste Decreto.</p>
</body></html>"""
ORIGEM = "manter os indicadores estabelecidos nos incisos V e VI do caput do art. 4º; do Decreto 9.999, de 20 de julho de 2024, em até 30 dias."  # fmt: skip


def indice(*docs):
    extraidos = {d["id"]: extract(d["html"].encode(), "text/html", Settings()) for d in docs}
    return Indice(docs, lambda d: extraidos[d["id"]]), extraidos


DEC = {"id": "dec9999", "ato": "Decreto nº 9.999, de 20 de junho de 2024", "html": DESTINO}


def pos(texto, trecho):
    return texto.index(trecho)


def test_remissao_local_vira_proposta_com_citacoes_e_divergencia_de_data():
    idx, _ = indice(DEC)
    r = resolver(ORIGEM, pos(ORIGEM, "art. 4º"), idx)
    assert r["estado"] == "proposta" and r["revisao"] == "aguarda revisão humana"
    assert (r["doc"], r["dispositivo"]) == ("dec9999", "Art. 4º, V e VI")
    # O destino lista também o VII: a remissão não ganha o inciso VII sozinha.
    assert len(r["citacoes"]) == 3 and "VII" not in r["dispositivo"]
    assert any("20/07/2024" in d and "20/06/2024" in d for d in r["divergencias"])
    # A parte do ato no mesmo trecho resolve para o mesmo alvo.
    assert resolver(ORIGEM, pos(ORIGEM, "Decreto 9.999"), idx)["dispositivo"] == r["dispositivo"]


def test_documento_ausente_artigo_ou_inciso_inexistente_ficam_nao_resolvidos():
    idx, _ = indice(DEC)
    outro = ORIGEM.replace("9.999", "1.234")
    assert resolver(outro, pos(outro, "art. 4º"), idx)["motivo"] == "ato citado ausente do acervo local"  # fmt: skip
    sem_art = ORIGEM.replace("art. 4º", "art. 8º")
    assert "Art. 8 não encontrado" in resolver(sem_art, pos(sem_art, "art. 8º"), idx)["motivo"]
    sem_inc = ORIGEM.replace("V e VI", "V e IX")
    assert "inciso IX" in resolver(sem_inc, pos(sem_inc, "art. 4º"), idx)["motivo"]
    # Sem ato explícito não há remissão a resolver (nada é inferido por palavras parecidas).
    assert resolver("conforme o art. 4º desta Resolução", 13, idx) is None


def test_versoes_concorrentes_do_mesmo_ato_nao_resolvem():
    idx, _ = indice(DEC, DEC | {"id": "dec9999b"})
    r = resolver(ORIGEM, pos(ORIGEM, "art. 4º"), idx)
    assert r["estado"] == "nao_resolvida" and "ambígua" in r["motivo"]


def test_cadeia_nao_e_seguida_e_itens_recebem_alvo():
    # O destino cita outro ato; a resolução para no primeiro salto e não percorre cadeia (sem ciclos).
    ciclo = DESTINO.replace("neste Decreto", "no art. 4º do Decreto 9.999")
    idx, ext = indice(DEC | {"html": ciclo})
    unidade = {"id": "u1", "text": ORIGEM}
    itens = [{"type": "reference", "anchors": [{"unit_id": "u1"}], "reference": {"offset": pos(ORIGEM, "art. 4º"), "target": None}}]  # fmt: skip
    resolver_itens(itens, {"units": [unidade]}, idx)
    alvo = itens[0]["reference"]["target"]
    assert alvo == {"doc": "dec9999", "dispositivo": "Art. 4º, V e VI", "estado": "proposta"}
    assert len(ext["dec9999"]["units"]) > 0
