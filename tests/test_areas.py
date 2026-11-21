"""Quem faz o quê: o mapeamento tipo -> área cobre todos os tipos e só usa áreas conhecidas."""

from athenix import areas, tipos


def test_mapeamento_cobre_todos_os_tipos_de_obrigacao():
    cfg = areas.carregar()
    todos = {t["id"] for t in tipos.carregar()["tipos"]}
    assert todos <= set(cfg["por_tipo"]), todos - set(cfg["por_tipo"])
    assert set(cfg["por_tipo"].values()) <= set(cfg["areas"])
    assert cfg["padrao"] in cfg["areas"] and "sugestão" in cfg["rotulo"]


def test_palavra_de_vegetacao_vence_o_tipo_e_o_padrao_cobre_o_desconhecido():
    cfg = areas.carregar()
    assert (
        areas.area_de("elaborar_ou_revisar_plano", "plano de manejo da vegetação", cfg)
        == "Meio Ambiente/Arborização"
    )
    assert (
        areas.area_de("comunicar_consumidores", "avisar o consumidor", cfg)
        == "Comunicação/Atendimento"
    )
    assert areas.area_de("tipo_novo", "qualquer coisa", cfg) == "A definir"
    assert areas.area_de(None, "", cfg) == "A definir"  # sem tipo: a definir, não "Regulatório"
    assert areas.area_de("outros", "texto", cfg) == "A definir"


def test_area_pela_ia_quando_a_regra_nao_acha_o_tipo_e_marca_a_origem():
    cfg = areas.carregar()
    assert areas.area_com_origem("comunicar_consumidores", None, "texto", cfg) == (
        "Comunicação/Atendimento",
        "regra",
    )
    assert areas.area_com_origem(None, "capacitar_equipe", "texto", cfg) == (
        "Operação/Manutenção",
        "ia",
    )
    assert areas.area_com_origem(None, "outros", "texto", cfg) == ("A definir", None)
    assert areas.area_com_origem(None, None, "texto", cfg) == ("A definir", None)
    # palavra-chave (vegetação) vence a IA e vale como regra
    assert areas.area_com_origem(None, "capacitar_equipe", "poda de vegetação", cfg) == (
        "Meio Ambiente/Arborização",
        "regra",
    )
