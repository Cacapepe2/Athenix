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


def test_toda_obrigacao_tem_titulo_curto_de_ate_cinco_palavras():
    for p in PLANOS:
        for o in p["obrigacoes"]:
            t = o["titulo_curto"]
            assert t and len(t.split()) <= tc.MAX_PALAVRAS and not t.endswith("."), (o["id"], t)


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
