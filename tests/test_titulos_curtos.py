"""Título curto (até 5 palavras) de cada obrigação dos planos e a validação do script que o gera."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import titulos_curtos as tc  # noqa: E402

PLANOS = [
    json.loads((ROOT / f"landing/src/content/plano-{n}.json").read_text(encoding="utf-8"))
    for n in ("rn1137", "ren1174")
]


def test_titulo_curto_tem_ate_cinco_palavras_e_quase_toda_obrigacao_o_tem():
    """Título que a validação recusa (ex.: número que o dispositivo não traz) fica None: a tela encurta o título completo."""
    total = sem = 0
    for p in PLANOS:
        for o in p["obrigacoes"]:
            total += 1
            t = o["titulo_curto"]
            if t is None:
                sem += 1
                continue
            assert len(t.split()) <= tc.MAX_PALAVRAS and not t.endswith("."), (o["id"], t)
    # 6 = 2 antigos + 3 deveres novos da correção C1 + Art. 16, p. único da REN 1.174 (vigência), sem título
    # no cache e sem chamada paga.
    # Os 6 sem título permanecem; a base caiu de 238 para 222 com marcos e condicionais fora do principal.
    assert sem <= 6 and sem < total * 0.028


def test_validacao_recusa_mais_de_cinco_palavras_e_produto_fora_do_texto():
    o = {
        "trecho": "A distribuidora deve publicar o plano.",
        "titulo_completo": "Publicar o plano",
        "contexto": "",
    }
    assert tc.validar("Publicar o plano.", o) == "Publicar o plano"
    assert tc.validar("Publicar o plano de contingência no site", o) is None
    assert tc.validar("Publicar plano em PDF", o) is None
    assert tc.validar("", o) is None


def test_numero_e_extenso_sao_equivalentes_na_validacao():
    from athenix.normalizacao import numeros

    assert numeros("prazo de doze meses") == numeros("prazo de 12 meses") == {12}
    assert 180 in numeros("180 (cento e oitenta) dias") and 180 in numeros("cento e oitenta dias")
    assert 21 in numeros("vinte e um dias") and 2500 in numeros("dois mil e quinhentos")
    assert numeros("um plano de uma área") == set()  # "um"/"uma" sozinhos são artigo
    o = {
        "trecho": "O ressarcimento não deve ultrapassar o prazo de doze meses.",
        "titulo_completo": "Ressarcimento",
        "contexto": "",
    }
    assert tc.validar("Ressarcimento até 12 meses", o) == "Ressarcimento até 12 meses"
    assert tc.validar("Ressarcimento até doze meses", o) == "Ressarcimento até doze meses"
    assert tc.validar("Ressarcimento até 24 meses", o) is None  # número que o dispositivo não traz
    assert tc.validar("Ressarcimento até vinte meses", o) is None
    o12 = {**o, "trecho": "O prazo é de 12 (doze) meses."}
    assert tc.validar("Prazo de doze meses", o12) == "Prazo de doze meses"
