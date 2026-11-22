import copy

import pytest

from scripts.demo import avaliar_faq as faq


def test_prazo_real_do_dise_igual_e_data_incorreta_diverge():
    _, _, cfg, plano = faq.carregar()
    caso = next(c for c in cfg["casos"] if c["numero"] == "3.2")
    assert faq.avaliar(caso, plano)["veredito"] == faq.IGUAL
    errado = copy.deepcopy(plano)
    for o in errado["obrigacoes"]:
        if o["dispositivo"] == "Art. 13, inciso VI":
            o["prazo"]["data"] = "2026-05-28"
    assert faq.avaliar(caso, errado)["veredito"] == faq.DIVERGE
    fonte, perguntas, _, _ = faq.carregar()
    texto, totais = faq.relatorio(fonte, perguntas, cfg, errado)
    assert totais[faq.DIVERGE] == 1
    assert "acerta 9 de 10 cobertas · 16 não cobertas" in texto


def test_resposta_negativa_sem_campo_nao_vira_acerto_por_ausencia():
    caso = {"dispositivos": ["item 1"], "verificacoes": [{"campo": "aprovacao", "valor": False}]}
    plano = {"obrigacoes": [{"dispositivo": "item 1", "trecho": "A distribuidora deve publicar."}]}
    assert faq.avaliar(caso, plano)["veredito"] == faq.NAO_COBRE
    plano["obrigacoes"][0]["aprovacao"] = True
    assert faq.avaliar(caso, plano)["veredito"] == faq.DIVERGE


def test_faq_real_inteiro_classificado_e_hash_divergente_interrompe(tmp_path):
    fonte, perguntas, cfg, plano = faq.carregar()
    assert len(perguntas) == len(cfg["casos"]) + len(cfg["fora"]) == 32
    texto, totais = faq.relatorio(fonte, perguntas, cfg, plano)
    assert texto == faq.SAIDA.read_text(encoding="utf-8")
    assert sum(totais.values()) == len(cfg["casos"])
    assert "não é um conjunto inteiramente independente" in texto.lower()
    assert "acerta 10 de 10 cobertas · 16 não cobertas" in texto
    assert "acerta 8 de 8 cobertas · 16 não cobertas" in texto
    assert "Cobertura: 10 de 26" in texto
    assert "Cobertura independente: 8 de 24" in texto
    for n in perguntas:
        assert perguntas[n]["pergunta"] in texto
    (tmp_path / "fontes.json").write_bytes((faq.PASTA / "fontes.json").read_bytes())
    (tmp_path / fonte["arquivo"]).write_text("FAQ modificado", encoding="utf-8")
    with pytest.raises(ValueError, match="Hash divergente"):
        faq.carregar(pasta=tmp_path)
