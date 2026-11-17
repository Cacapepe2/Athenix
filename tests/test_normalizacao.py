"""Normalização única (athenix.normalizacao): só para comparar e estruturar; o original não muda."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from athenix.normalizacao import chave, espacos, intervalo_original, normalizar


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("a  b\t\nc", "a b c"),  # espaços, tabulação e quebra de linha
        ("a b\r\nc", "a b c"),  # espaço não separável e CRLF
        ("  borda  ", "borda"),
        ("manu-\ntenção", "manutenção"),  # hifenização de quebra de linha
        ("manu- \n  tenção", "manutenção"),
        ("Art. 3º-D da Lei", "Art. 3º-D da Lei"),  # hífen de dispositivo fica
        ("I -\nfixar", "I - fixar"),  # travessão de inciso não é hifenização
        ("auto-\nProdução", "auto- Produção"),  # maiúscula: não junta
        ("“aspas” e ‘simples’", "\"aspas\" e 'simples'"),
        ("a – b — c", "a - b - c"),
        ("cinqüenta e freqüência", "cinquenta e frequência"),  # trema da grafia antiga
        ("pala­vra​", "palavra"),  # hífen condicional e largura zero
    ],
)
def test_normalizar(entrada, esperado):
    assert normalizar(entrada)[0] == esperado


def test_trema_preserva_outros_acentos_e_compoe_acento_separado():
    assert normalizar("freqüência")[0] == "frequência"  # só o trema sai; o circunflexo fica
    decomposto = "ação"  # "ação" com acentos separados
    assert normalizar(decomposto)[0] == "ação"
    assert normalizar("cinqüenta", trema=False)[0] == "cinqüenta"


def test_mapa_volta_ao_trecho_original_exato():
    original = "O plano de manu-\n  tenção  deve “ser” publicado."
    texto, mapa = normalizar(original)
    inicio = texto.index("manutenção deve")
    a, b = intervalo_original(mapa, inicio, inicio + len("manutenção deve"))
    assert original[a:b] == "manu-\n  tenção  deve"
    i = texto.index('"ser"')
    a, b = intervalo_original(mapa, i, i + 5)
    assert original[a:b] == "“ser”"


def test_chave_ignora_espacos_e_caixa_opcional():
    assert chave("A  b\nc") == "Abc"
    assert normalizar("ÁBC", caixa=True)[0] == "ábc"
    assert espacos("  a \n b ") == "a b"


def test_original_nao_muda():
    original = "texto “original”\n com quebra"
    copia = str(original)
    normalizar(original)
    chave(original)
    assert original == copia


@given(st.text(max_size=200))
def test_idempotente_e_mapa_valido(texto):
    normal, mapa = normalizar(texto)
    assert normalizar(normal)[0] == normal
    assert len(mapa) == len(normal)
    assert mapa == sorted(mapa) and all(0 <= p < len(texto) for p in mapa)


def test_acento_que_nao_compoe_nao_quebra_o_mapa():
    # Achado pelo hypothesis: "0" + virama não compõe em NFC; o mapa perdia uma posição.
    for texto in ("0्", "्", "á"):
        normal, mapa = normalizar(texto)
        assert len(mapa) == len(normal) and normalizar(normal)[0] == normal
