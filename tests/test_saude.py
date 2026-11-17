"""Saúde da extração: invariantes gerais aplicados a qualquer documento."""

import copy

from athenix import saude
from athenix.config import Settings
from athenix.structure import extract


def html(*paragrafos):
    corpo = "".join(f"<p>{p}</p>" for p in paragrafos)
    return extract(f"<html><body>{corpo}</body></html>".encode(), "text/html", Settings(), "norm")


LIMPO = (
    "Art. 1º As distribuidoras devem manter o cadastro atualizado.",
    "§ 1º O cadastro inclui os dados de contato.",
    "§ 2º O cadastro é público.",
    "Art. 2º Compete à distribuidora:",
    "I - publicar o plano;",
    "II - informar a ANEEL.",
    "Art. 3º Esta Resolução entra em vigor na data de sua publicação.",
)


def tipos(resultado):
    return {a["tipo"] for a in resultado["alertas"]}


def test_documento_bem_estruturado_tem_nota_maxima():
    r = saude.avaliar(html(*LIMPO))
    assert r["nota"] == 100 and r["situacao"] == "ok" and r["alertas"] == []
    assert r["metricas"]["cobertura"] >= 0.8


def test_salto_repeticao_e_ordem_na_numeracao():
    salto = saude.avaliar(html("Art. 1º Texto um.", "Art. 3º Texto três."))
    assert "numeracao" in tipos(salto) and "1 salto" in salto["alertas"][0]["mensagem"]
    repetido = saude.avaliar(html("Art. 1º A.", "I - um;", "I - outro;", "II - dois."))
    assert "repetição" in repetido["alertas"][0]["mensagem"]
    ordem = saude.avaliar(html("Art. 2º Dois.", "Art. 1º Um."))
    assert "ordem invertida" in ordem["alertas"][0]["mensagem"]
    # Sufixo não é salto ("Art. 23" → "Art. 23-A" → "Art. 24").
    assert (
        saude.avaliar(html("Art. 23. Um.", "Art. 23-A. Dois.", "Art. 24. Três."))["alertas"] == []
    )


def test_dispositivo_que_nao_existe_na_fonte_e_acusado():
    extracao = html(*LIMPO)
    alterada = copy.deepcopy(extracao)
    art = next(u for u in alterada["units"] if u["label"].startswith("2"))
    art["text"] = "Art. 2º Compete à distribuidora inventar obrigações:"
    r = saude.avaliar(alterada)
    assert "literal" in tipos(r) and "Art. 2º" in r["alertas"][0]["exemplos"][0]


def test_sem_segunda_leitura_perde_nota():
    extracao = html(*LIMPO)
    extracao["source"] = None
    r = saude.avaliar(extracao)
    assert r["nota"] == 80 and "literal" in tipos(r)


def test_dispositivo_no_meio_de_palavra():
    extracao = html(*LIMPO)
    u = next(x for x in extracao["units"] if x["kind"] == "clause")
    u["start"] -= 3  # "distribuido|ra:\nI -": começa dentro da palavra anterior
    assert extracao["text"][u["start"] - 1 : u["start"] + 1] == "ra"
    assert "meio_de_palavra" in tipos(saude.avaliar(extracao))


def test_texto_pouco_estruturado_fica_para_revisar():
    solto = "Texto corrido sem dispositivo algum, como um ofício ou uma nota técnica. " * 30
    r = saude.avaliar(html(solto, "Art. 1º Único artigo."))
    assert "cobertura" in tipos(r)
    pior = saude.avaliar(
        {"text": solto, "units": [], "warnings": ["Página 1 sem texto: requer OCR."]}
    )
    assert pior["nota"] < saude.LIMITE and pior["situacao"] == "revisar extração"
    assert {"cobertura", "ocr", "literal"} <= tipos(pior)


def test_saude_aparece_no_documento_na_tela_de_impacto_e_no_relatorio(env):
    from conftest import propose

    app, client, settings = env
    norma = "<html><body>" + "".join(f"<p>{p}</p>" for p in LIMPO) + "</body></html>"
    doc, _ = propose(env, norma.encode())
    for url in (f"/documents/{doc['id']}", "/impacto", "/impacto/relatorio"):
        pagina = client.get(url)
        assert pagina.status_code == 200 and "Qualidade da extração" in pagina.text, url
        assert "nota 100/100" in pagina.text, url
