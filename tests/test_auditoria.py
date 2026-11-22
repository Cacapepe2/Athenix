"""Correções da auditoria independente: ids estáveis e export reproduzível (A4), sujeito e modalidade
(A1), proveniência das infrações (A2), sucessão do art. 11, XXIII (A3), aviso de IA (M4), regra x IA
quando a regra não acha tipo (M1)."""

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import exportar_plano_demo as exp  # noqa: E402

from athenix import analise, plano, proposals, tipos  # noqa: E402

PLANO = json.loads((ROOT / "landing/src/content/plano-rn1137.json").read_text(encoding="utf-8"))


# --- A4: ids estáveis e reprodutibilidade
def test_ids_sao_chaves_de_texto_estaveis_e_unicos():
    ids = [o["id"] for o in PLANO["obrigacoes"]] + [o["id"] for o in PLANO["outros_dispositivos"]]
    assert all(re.fullmatch(r"[0-9a-f]{16}", i) for i in ids)  # chave do texto, não uuid4
    assert len(set(ids)) == len(ids)
    for t in PLANO["temas"]:
        assert set(t["obrigacoes"]) <= set(ids)


def test_verificacao_ignora_so_data_e_commit(tmp_path):
    base = {"commit_origem": "a", "gerado_em": "2026-01-01", "x": [{"id": "1", "v": 1}]}
    arq = tmp_path / "plano.json"
    arq.write_text(json.dumps(base), encoding="utf-8")
    assert exp.verificar(arq, base | {"commit_origem": "b", "gerado_em": "2030-05-05"}) == 0
    assert exp.verificar(arq, base | {"x": [{"id": "2", "v": 1}]}) == 1
    assert exp.diferencas({"a": [1, 2]}, {"a": [1, 3]}) == ["/a[1]"]


# --- A1: sujeito e modalidade
def test_modalidade_vem_da_oracao_principal():
    dossie = (
        "b) a cessionária deverá manter dossiê individualizado em sua sede contendo os documentos "
        "comprobatórios, que poderão ser requisitados pela fiscalização"
    )
    assert proposals.modality(dossie) == "duty"  # a permissão é da fiscalização, subordinada
    assert proposals.modality("125. As distribuidoras ou transmissoras podem promover o auxílio") == "permission"  # fmt: skip
    assert proposals.modality("111. O consumidor e demais usuários podem solicitar a suspensão") == "permission"  # fmt: skip
    assert proposals.modality("As distribuidoras não poderão cobrar") == "prohibition"
    assert proposals.modality("As distribuidoras devem publicar o plano") == "duty"


@pytest.mark.parametrize(
    ("sujeito", "modalidade", "esperado"),
    [
        ("As distribuidoras", "duty", "dever"),
        ("a cessionária", "duty", "dever"),
        ("O consumidor e demais usuários", "permission", "direito_de_terceiro"),
        (
            "Colaboração e Solidariedade: As distribuidoras ou transmissoras",
            "permission",
            "faculdade",
        ),  # fmt: skip
        ("A Agência", "permission", "competencia_aneel"),
        ("A Agência", "duty", "competencia_aneel"),
    ],
)
def test_natureza_pelo_sujeito_e_modalidade(sujeito, modalidade, esperado):
    assert plano.natureza({"subject": sujeito, "modality": modalidade}) == esperado


def test_casos_da_auditoria_no_plano():
    deveres = " ".join(o["trecho"] or "" for o in PLANO["obrigacoes"])
    outros = {o["natureza"]: [] for o in PLANO["outros_dispositivos"]}
    for o in PLANO["outros_dispositivos"]:
        outros[o["natureza"]].append(o["trecho"] or "")
    juntos = " ".join(t for ts in outros.values() for t in ts)
    assert "111. O consumidor" in juntos and "125. Colaboração" in juntos  # item 111 e 125
    assert any("articular, coordenar" in t for t in outros["competencia_aneel"])  # art. 10, I
    assert any("interagir com demais" in t for t in outros["competencia_aneel"])  # art. 10, II
    assert deveres.count("manter dossiê individualizado") == 2  # 139(b) e art. 19, XIII(b): deveres
    r = PLANO["resumo"]
    assert r["identificadas"] == r["aplicaveis"] + r["fora_do_perfil"] + r["outros_dispositivos"]
    assert r["aplicaveis"] == len(PLANO["obrigacoes"]) == sum(t["n"] for t in PLANO["temas"])


# --- A2: proveniência das infrações
def test_infracoes_trazem_fonte_hash_e_origem_conferidos():
    assert PLANO["infracoes"]
    for disp, i in PLANO["infracoes"].items():
        assert i["conferido_na_fonte"] is True, disp
        assert re.fullmatch(r"[0-9a-f]{64}", i["fonte"]["sha256"]) and i["origem_da_redacao"]
        arquivo = ROOT / i["fonte"]["arquivo"]
        if not arquivo.exists():
            pytest.skip(f"fonte oficial ausente: {i['fonte']['arquivo']}")
        assert hashlib.sha256(arquivo.read_bytes()).hexdigest() == i["fonte"]["sha256"]


# --- A3: as duas redações do art. 11, XXIII
def test_sucessao_do_xxiii_mostra_as_duas_redacoes_datadas():
    s = PLANO["sucessao_no_tempo"][0]
    assert s["dispositivo"] == "Art. 11, XXIII" and s["duvida"] == "D1"
    atual, futura = s["redacoes"]
    assert (atual["vigencia_de"], atual["vigencia_ate"]) == ("2025-10-30", "2026-12-31")
    assert (futura["vigencia_de"], futura["vigencia_ate"]) == ("2027-01-01", None)
    assert atual["estado"] == "verified" and atual["conferido_na_fonte"] is True
    assert futura["estado"] == "incerta" and futura["conferido_na_fonte"] is False
    assert "SGO" in futura["trecho"] and "interrupções" in atual["trecho"]
    assert futura["fonte"]["sha256"] != atual["fonte"]["sha256"]


# --- M4 e M1
def test_aviso_da_ia_explica_os_dois_modos():
    aviso = PLANO["ia"]["aviso"]
    assert "só identificados no texto" in aviso and "cenário preliminar" in aviso
    assert "não entram no cálculo." not in aviso.replace("não entram no cálculo; no", "")


def test_regra_sem_tipo_com_ia_com_tipo_vira_tipo_a_revisar():
    cfg = tipos.carregar()
    r = analise._tipo("a) o horário do evento;", True, {"k": "publicar_no_site"}, "k", cfg)
    assert r["situacao"] == "a_revisar" and r["id"] is None and "IA:" in r["por"]
    sem = analise._tipo("a) o horário do evento;", True, {"k": "outros"}, "k", cfg)
    assert sem["situacao"] == "sem_tipo"


# --- Auditoria de 21/11 (2ª rodada): C1 "pode" singular e A1 prazos em minutos/horas
@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("A distribuidora pode manter o registro.", "permission"),
        ("As distribuidoras podem manter o registro.", "permission"),
        ("A distribuidora poderá manter o registro.", "permission"),
        ("As distribuidoras poderão manter o registro.", "permission"),
        ("A distribuidora não pode cobrar a taxa.", "prohibition"),
        ("As distribuidoras não podem cobrar a taxa.", "prohibition"),
        ("A distribuidora deve manter o registro e pode publicá-lo.", "duty"),
    ],
)
def test_c1_pode_na_oracao_principal_e_faculdade(texto, esperado):
    assert proposals.modality(texto) == esperado


def test_c1_item_145a_e_faculdade_e_o_caput_segue_dever():
    # 145(a), antes id 8c54ec11a2e41126 em obrigacoes: "a periodicidade máxima pode ser contada..."
    marca = "periodicidade máxima pode ser contada da sua última aplicação"
    assert not [o for o in PLANO["obrigacoes"] if marca in o["trecho"]]
    (item,) = [o for o in PLANO["outros_dispositivos"] if marca in o["trecho"]]
    assert item["natureza"] == "faculdade"
    caput = [o for o in PLANO["obrigacoes"] if o["trecho"].startswith("145.")]
    assert caput, "o dever do caput 145 continua na contagem"


ITEM_105 = (
    "105. As distribuidoras devem comunicar aos consumidores, por meio dos canais disponíveis, a "
    "provável causa da interrupção, a área afetada e o tempo previsto para a normalização do "
    "fornecimento em até 15 (quinze) minutos após o conhecimento da causa da interrupção. "
    "Independentemente do momento em que a causa for identificada, a comunicação contendo essas "
    "informações deve ser realizada em até 1 (uma) hora após o reconhecimento da ocorrência da "
    "interrupção no fornecimento de energia elétrica."
)


def test_a1_minutos_e_horas_apos_evento_sao_prazo_por_evento_sem_data():
    from athenix.temporal import rules

    publicacao = [{"kind": "publication", "date": "2025-10-01"}]
    prazos = rules(ITEM_105, "u", publicacao)
    assert [(d["quantity"], d["unit"], d["state"], d["date"]) for d in prazos] == [
        (15, "minutos", "awaiting_event", None),
        (1, "hora", "awaiting_event", None),
    ]
    # Sem evento, minutos/horas nunca viram data civil (nem contados da publicação).
    (d,) = rules("A distribuidora deve responder em 48 horas da publicação.", "u", publicacao)
    assert d["date"] is None and d["state"] == "not_calculated"
    # Casos reais da RN 1.137 que não são prazo: periodicidade e disponibilidade.
    for texto in (
        "disponibilizar em sítio eletrônico, com atualização a cada 30 minutos, o número total",
        "disponibilidade ininterrupta durante 24 horas por dia",
    ):
        assert all(
            d["date"] is None and d["state"] != "awaiting_event"
            for d in rules(texto, "u", publicacao)
        )


def test_a1_item_105_no_plano_mostra_os_dois_limites():
    (item,) = [o for o in PLANO["obrigacoes"] if o["id"] == "c3b421e728c88b65"]
    # Art. 13, III da RN 1.137: 180 dias da publicação para implementar o item 105 (vigencia.py); o prazo
    # de adequação já passou e o texto mantém os dois limites por evento.
    assert item["marco"]["dispositivo"] == "Art. 13, III" and item["prazo"]["data"] == "2026-04-28"
    assert "por evento: até 15 min após o conhecimento da causa" in item["prazo"]["texto"]
    assert "até 1 h após o reconhecimento da ocorrência" in item["prazo"]["texto"]


# --- M1 (auditoria de 21/11): tipo "a revisar" não leva a área do tipo da regra
@pytest.mark.parametrize(
    ("dispositivo", "area"),
    [("item 132, alínea l", "TI/Sistemas"), ("Art. 19, inciso XIII, alínea c", "Jurídico")],
)
def test_m1_tipo_a_revisar_usa_area_da_ia_ou_a_definir(dispositivo, area):
    (o,) = [x for x in PLANO["obrigacoes"] if x["dispositivo"] == dispositivo]
    assert o["analise"]["tipo"]["situacao"] == "a_revisar"
    assert o["analise"]["tipo"]["regra_id"] == "estrutura_atendimento_contingencia"
    assert (o["area"], o["area_origem"]) == (
        area,
        "ia",
    )  # antes: Comunicação/Atendimento pela regra


def test_m1_nenhum_tipo_a_revisar_tem_area_pelo_tipo_da_regra():
    from athenix import areas

    for o in PLANO["obrigacoes"]:
        if o["analise"]["tipo"]["situacao"] != "a_revisar":
            continue
        assert o["area_origem"] in ("ia", None) or areas.area_com_origem(None, None, o["trecho"]) == (o["area"], "regra"), o["dispositivo"]  # fmt: skip
