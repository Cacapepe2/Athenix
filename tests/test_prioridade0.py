"""Prioridade 0 do v6: tipo "manter registro", regra de transição, título com contexto e recomendações
específicas por obrigação (validação), com trechos reais da RN 1.137 e da REN 1.174."""

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import recomendar_acoes as ra  # noqa: E402

from athenix import plano, tipos  # noqa: E402

P1137 = json.loads((ROOT / "landing/src/content/plano-rn1137.json").read_text(encoding="utf-8"))
P1174 = json.loads((ROOT / "landing/src/content/plano-ren1174.json").read_text(encoding="utf-8"))
ART16_CAPUT = "Art. 16. A adequação às alterações promovidas por esta Resolução deve ser realizada nos seguintes prazos:"


def test_registro_das_interacoes_com_o_poder_publico_e_manter_registro_nao_inspecao():
    # RN 1.137, art. 13, II (texto real)
    texto = (
        "II - Até 180 (cento e oitenta) dias para implementar o registro das interações com o Poder Público "
        "Municipal em relação ao serviço de manejo da vegetação que apresente risco à segurança das redes elétricas"
    )
    assert tipos.classificar(texto)["tipo"] == "manter_registro_historico"
    # e o serviço de manejo em si continua sendo manutenção
    assert tipos.classificar("A distribuidora deve executar a poda e o manejo da vegetação na faixa de servidão")["tipo"] == "inspecionar_executar_manutencao"  # fmt: skip


def test_art_16_da_ren_1174_e_regra_de_transicao_nao_dever():
    for texto in (
        "I - até doze meses da data de sua publicação, quanto ao art. 2º, na parte que inclui o § 1º no art. 166",
        "II - em até 180 (cento e oitenta) dias da data de sua publicação, quanto ao:",
    ):
        assert plano.natureza({"subject": "não identificado", "modality": "duty", "action": texto}, ART16_CAPUT) == "regra_de_transicao"  # fmt: skip
    assert plano.natureza({"subject": "A distribuidora", "modality": "duty", "action": "A distribuidora deve publicar o plano"}, "") == "dever"  # fmt: skip
    na_lista = {o["dispositivo"] for o in P1174["obrigacoes"]}
    assert "Art. 16, inciso I" not in na_lista and "Art. 16, inciso II" not in na_lista
    transicao = [o for o in P1174["outros_dispositivos"] if o["natureza"] == "regra_de_transicao"]
    assert {o["dispositivo"] for o in transicao} >= {"Art. 16, inciso I", "Art. 16, inciso II"}
    assert (
        P1137["resumo"]["aplicaveis"] == 147
    )  # RN 1.137: 153 - cinco incisos de prazo - Art. 18 (vigência).


def test_titulo_ganha_o_sujeito_e_o_deve_do_caput():
    row = {"subject": "a aplicação do benefício tarifário", "action": "x"}
    t = plano.titulo_com_contexto(
        "Ser realizada até o maior prazo entre doze meses e o prazo reduzido", row, ""
    )
    assert t == "A aplicação do benefício tarifário deve ser realizada até o maior prazo entre doze meses e o prazo reduzido"  # fmt: skip
    caput = "Art. 16. A adequação às alterações promovidas por esta Resolução deve ser realizada nos seguintes prazos:"
    t2 = plano.titulo_com_contexto(
        "Até doze meses da data de sua publicação", {"subject": "não identificado"}, caput
    )
    assert t2.startswith("A adequação às alterações promovidas por esta Resolução deve ser realizada") and "até doze meses" in t2  # fmt: skip
    assert plano.titulo_com_contexto("Revisar e publicar planos de manejo", row, "") == "Revisar e publicar planos de manejo"  # fmt: skip
    for p in (P1137, P1174):
        for o in p["obrigacoes"]:
            assert not o["titulo_completo"].startswith(("Ser ", "Até ", "Em até ")), o[
                "titulo_completo"
            ][:60]


def test_validacao_das_recomendacoes_exige_trecho_literal_e_barra_frase_generica():
    o = {"trecho": "§ 1º A distribuidora deve disponibilizar o mapa de ocorrências no sítio eletrônico.", "titulo_completo": "Publicar o mapa de ocorrências", "contexto": ""}  # fmt: skip
    ok = [{"acao": "Publicar o mapa de ocorrências abertas na página inicial do sítio eletrônico.", "trecho_citado": "mapa de ocorrências no sítio eletrônico"}]  # fmt: skip
    assert len(ra.validar(ok, o)) == 1
    inventado = [
        {
            "acao": "Publicar o mapa de ocorrências",
            "trecho_citado": "relatório trimestral ao conselho",
        }
    ]
    assert ra.validar(inventado, o) == []  # o trecho citado não está no dispositivo
    generica = [{"acao": "Designar responsável e prazo para o mapa de ocorrências", "trecho_citado": "mapa de ocorrências no sítio eletrônico"}]  # fmt: skip
    assert ra.validar(generica, o) == []
    sem_ligacao = [{"acao": "Treinar a equipe de atendimento", "trecho_citado": "mapa de ocorrências no sítio eletrônico"}]  # fmt: skip
    assert ra.validar(sem_ligacao, o) == []
    assert ra.validar("não é lista", o) == []


def test_recomendacoes_no_plano_citam_o_proprio_dispositivo():
    cache = json.loads(
        (ROOT / "athenix/data/recomendacoes_dou_ren20261174.json").read_text(encoding="utf-8")
    )
    assert (
        float(cache["custo_total_da_execucao_usd"]) <= 2
        and "a confirmar no portal" in cache["nota_preco"]
    )
    for p in (P1137, P1174):
        com = [o for o in p["obrigacoes"] if o["recomendacoes"]]
        assert com
        for o in com:
            assert 1 <= len(o["recomendacoes"]) <= 3
            base = tipos.normalizar(f"{o['trecho']} {o['titulo_completo']} {o['contexto']}")
            for r in o["recomendacoes"]:
                assert tipos.normalizar(r["trecho_citado"]) in base, (
                    o["dispositivo"],
                    r["trecho_citado"],
                )


def test_distribuicao_dos_grupos_sugeridos_pela_ia_na_ren_1174():
    grupos = Counter(o["ia"]["grupo"] for o in P1174["obrigacoes"] if o["ia"])
    total = sum(grupos.values())
    assert total > 0
    assert (
        grupos.get("IV", 0) / total <= 0.8
    )  # acima disso a IA estaria exagerando: o fundador confere exemplos
