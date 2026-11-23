import hashlib
import json

import pytest

from scripts.demo import publicar_fontes as fontes


def test_indice_reproduz_e_copias_mantem_hash_das_fontes_oficiais():
    indice = json.loads(fontes.INDICE.read_text(encoding="utf-8"))
    assert indice == fontes.compilar()
    assert len(indice["documentos"]) == 7
    for sha, f in indice["documentos"].items():
        copia = fontes.PUBLICO / f["url"].split("/")[-1]
        assert hashlib.sha256(copia.read_bytes()).hexdigest() == sha
        assert copia.read_bytes() == (fontes.ROOT / f["arquivo"]).read_bytes()
        assert ".local" not in f["arquivo"] and "leisorg" not in f["arquivo"].lower()


@pytest.mark.parametrize("dispositivo", ["item 103", "Art. 13, inciso VI", "Art. 371-A, § 5º"])
def test_pagina_linkada_contem_citacao_real_da_rn1137(dispositivo):
    p = json.loads(
        (fontes.ROOT / "landing/src/content/plano-rn1137.json").read_text(encoding="utf-8")
    )
    o = next(o for o in p["obrigacoes"] if o["dispositivo"] == dispositivo)
    indice = json.loads(fontes.INDICE.read_text(encoding="utf-8"))
    sha = p["norma"]["sha256"]
    c = indice["citacoes"][sha][fontes.chave(o["trecho"])]
    folhas = fontes.paginas(fontes.ROOT / indice["documentos"][sha]["arquivo"])
    assert c["pagina"] == c["ultima_pagina"]
    assert fontes.compacto(o["trecho"]) in folhas[c["pagina"] - 1]
    assert c["url"].endswith(f"#page={c['pagina']}")


def test_atenuante_da_ren846_na_pagina_certa_e_html_sem_pagina():
    p = json.loads(
        (fontes.ROOT / "landing/src/content/plano-ren1174.json").read_text(encoding="utf-8")
    )
    indice = json.loads(fontes.INDICE.read_text(encoding="utf-8"))
    c = next(m for m in p["reducao"]["medidas"] if m["cenario"] == "espontanea")
    local = indice["citacoes"][c["sha256"]][fontes.chave(c["trecho"])]
    folhas = fontes.paginas(fontes.ROOT / indice["documentos"][c["sha256"]]["arquivo"])
    assert fontes.compacto(c["trecho"]) in folhas[local["pagina"] - 1]
    for local in indice["citacoes"][p["norma"]["sha256"]].values():
        assert local["pagina"] is None and "#page=" not in local["url"]


def test_trecho_entre_paginas_indica_o_inicio_e_o_fim_sem_inventar_localizacao():
    local = fontes.localizar("dever legal", ["iníciodever", "legalfim"])
    assert (local["pagina"], local["ultima_pagina"]) == (1, 2)
    with pytest.raises(ValueError, match="não localizado"):
        fontes.localizar("trecho ausente", ["outra página"])


def test_redacao_incerta_tem_apenas_localizacao_nao_e_confirmada():
    p = json.loads(
        (fontes.ROOT / "landing/src/content/plano-rn1137.json").read_text(encoding="utf-8")
    )
    r = next(r for s in p["sucessao_no_tempo"] for r in s["redacoes"] if r["estado"] == "incerta")
    indice = json.loads(fontes.INDICE.read_text(encoding="utf-8"))
    local = indice["citacoes"][r["fonte"]["sha256"]][fontes.chave(r["trecho"])]
    assert "redação permanece incerta" in local["localizacao"]
    assert r["conferido_na_fonte"] is False


def test_html_original_publicado_com_scripts_bloqueados():
    config = json.loads((fontes.ROOT / "landing/vercel.json").read_text(encoding="utf-8"))
    headers = next(h["headers"] for h in config["headers"] if h["source"] == "/fontes/(.*)")
    csp = next(h["value"] for h in headers if h["key"] == "Content-Security-Policy")
    assert "script-src 'none'" in csp and "connect-src 'none'" in csp
