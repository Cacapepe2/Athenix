"""Classificador de tipos de obrigação e detector de dependências externas (regras, sem IA)."""

import json

import pytest

from athenix import dependencias, tipos

# (tipo esperado, texto). Trechos da RN 1.137/2025 quando a frase é do próprio texto; as demais são
# frases sintéticas no mesmo estilo (marcadas) para os tipos que a norma usa pouco.
CASOS = [
    (
        "elaborar_ou_revisar_plano",
        "94. As distribuidoras devem estabelecer um plano de manejo vegetal na sua área de atuação",
    ),
    (
        "capacitar_equipe",
        "145. A realização de simulados ou disponibilização de treinamentos atualizados deve ser feita com periodicidade máxima de um ano.",
    ),
    (
        "enviar_informacao_aneel",
        "23-A. A distribuidora deve enviar às áreas de fiscalização da ANEEL relatório contendo discriminação das despesas",
    ),
    (
        "publicar_no_site",
        "Parágrafo único. Os planos de contingência em vigor na data desta Resolução devem ser publicados em seu sítio eletrônico",
    ),
    (
        "comunicar_consumidores",
        "111. O consumidor e demais usuários podem, a qualquer tempo, solicitar a suspensão do envio da comunicação por meio de SMS",
    ),
    (
        "comunicar_poder_publico_terceiros",
        "II - interagir com demais autoridades e instituições públicas e privadas no endereçamento de ações e no compartilhamento de informações;",
    ),
    (
        "estrutura_atendimento_contingencia",
        "c) Mobilização de Recursos: Definir procedimentos para a mobilização de equipes e recursos adicionais em diferentes níveis de contingência",
    ),
    (
        "estabelecer_criterios_e_papeis",
        "i) Apoio Interdepartamental: Estabelecer diretrizes para a colaboração entre diferentes departamentos",
    ),
    (
        "manter_registro_historico",
        "As distribuidoras devem manter registro detalhado durante o período de 05 anos",
    ),
    (
        "articular_coordenar_terceiros",
        "As distribuidoras devem articular e coordenar as ações com a Defesa Civil e demais órgãos",
    ),  # sintética
    (
        "apurar_calcular_indicador",
        "A distribuidora deve apurar e calcular o indicador mensalmente",
    ),  # sintética
    (
        "inspecionar_executar_manutencao",
        "A distribuidora deve realizar a poda e a inspeção da vegetação na faixa de servidão",
    ),  # sintética
    (
        "adequar_contrato_documento",
        "Os contratos devem prever cláusula sobre a duração e a responsabilidade pelas despesas",
    ),  # sintética
    (
        "implantar_sistema_processo",
        "A distribuidora deve implantar sistema para registrar as ocorrências",
    ),  # sintética
    (
        "responder_prazo_solicitacao",
        "A distribuidora deve responder à solicitação do consumidor em até cinco dias",
    ),  # sintética
    (
        "restabelecer_ou_compensar",
        "A distribuidora deve compensar o consumidor pelo tempo sem energia",
    ),  # sintética
    ("outros", "Esta Resolução entra em vigor na data de sua publicação."),
]


@pytest.mark.parametrize(("esperado", "texto"), CASOS)
def test_um_caso_por_tipo(esperado, texto):
    r = tipos.classificar(texto)
    assert r["tipo"] == esperado, (r["tipo"], r["candidatos"])


def test_todos_os_tipos_do_arquivo_tem_manual_em_rascunho_e_sao_cobertos():
    cfg = tipos.carregar()
    ids = {t["id"] for t in cfg["tipos"]}
    assert 15 <= len(ids) <= 20 and ids == {c[0] for c in CASOS}
    for t in cfg["tipos"]:
        assert t["status"] == "rascunho — revisar" and t["ideias_cumprimento"] and t["evidencias"]
        assert 3 <= len(t["ideias_cumprimento"]) <= 5 or t["id"] == "outros"
    assert cfg["status_geral"] == "rascunho — revisar"


def test_dependencias_tipicas_apontam_para_ids_existentes():
    dep = {d["id"] for d in dependencias.carregar()["tipos"]}
    for t in tipos.carregar()["tipos"]:
        assert set(t["dependencias_tipicas"]) <= dep, t["id"]


def test_sinal_fraco_sozinho_nao_classifica():
    assert (
        tipos.classificar("Esta Resolução será publicada.")["tipo"] == "outros"
    )  # 1 sinal = 2 pontos < 3


def test_classifica_com_o_texto_do_dispositivo_pai_e_diz_que_o_fez():
    alinea = "d) A responsabilidade pelas despesas operacionais;"
    r = tipos.classificar(alinea, "O acordo de Cessão Emergencial deve conter:")
    assert r["por"] == "regra (com o texto do dispositivo-pai)" and r["tipo"] != "outros"


def test_normalizar_mantem_o_comprimento_e_nao_mexe_no_original():
    original = "Poder Público Municipal — AUTORIZAÇÃO"
    assert len(tipos.normalizar(original)) == len(original)
    assert tipos.normalizar(original).startswith("poder publico municipal")


def test_gancho_de_ia_fica_desligado_e_live_exige_confirmacao_de_custo():
    assert tipos.especializar("x", "publicar_no_site", "texto") is None  # off é o padrão
    assert tipos.especializar("id-que-nao-existe", "publicar_no_site", "t", modo="cached") in (
        None,
        "",
    )
    with pytest.raises(PermissionError):
        tipos.especializar("x", "publicar_no_site", "t", modo="live", gerador=lambda *a: "texto")
    with pytest.raises(PermissionError):
        tipos.especializar("x", "publicar_no_site", "t", modo="live", custo_confirmado=True)
    assert tipos.estimar_custo(["a", "b"]) == {"chamadas": 2, "tokens_estimados": 1800}


# --- dependências externas ---------------------------------------------------------------------

TEXTO_PODA = (
    "II - Até 180 (cento e oitenta) dias para implementar o registro das interações com o Poder Público "
    "Municipal em relação ao serviço de manejo da vegetação que apresente risco à segurança das redes elétricas;"
)


def test_dependencia_no_texto_guarda_o_trecho_literal_que_disparou():
    deps = dependencias.detectar(TEXTO_PODA, "manter_registro_historico")
    municipal = next(d for d in deps if d["id"] == "autorizacao_municipal")
    assert municipal["origem"] == "texto"
    assert municipal["trecho_literal"] in TEXTO_PODA  # literal, nada reescrito
    assert municipal["sinal"] in TEXTO_PODA and municipal["citacao"] == "nao_verificada"


def test_dependencia_so_pelo_tipo_e_inferida_e_sem_citacao():
    deps = dependencias.detectar(
        "A distribuidora deve enviar relatório à ANEEL.", "enviar_informacao_aneel"
    )
    inferida = [d for d in deps if d["origem"] == "inferida_pelo_tipo"]
    assert {d["id"] for d in inferida} == {"sistema_aneel_indisponivel", "dado_de_terceiro"}
    assert all(d["trecho_literal"] is None and d["citacao"] is None for d in inferida)


def test_sinal_no_texto_nao_vira_inferida_de_novo():
    deps = dependencias.detectar(
        "Articular com a Defesa Civil em eventos climáticos extremos.",
        "articular_coordenar_terceiros",
    )
    ids = [d["id"] for d in deps if d["id"] == "evento_extremo_defesa_civil"]
    assert ids == ["evento_extremo_defesa_civil"] and deps[0]["origem"] == "texto"


def test_verificador_de_citacao_e_chamado_com_o_trecho():
    vistos = []
    dependencias.detectar(TEXTO_PODA, None, verificar=lambda t: vistos.append(t) or "verified")
    assert vistos and all(t in TEXTO_PODA for t in vistos)


def test_manual_da_dependencia_traz_precedentes_com_url_e_contraponto():
    cfg = dependencias.carregar()
    urls_permitidas = {
        "https://canalsolar.com.br/aneel-instabilidade-sistema-protocolo-digital/",
        "https://brasilenergia.com.br/energia/governo-regulacao/aneel-prorroga-prazos-devido-a-instabilidade-em-sistema",
        "https://cenarioenergia.com.br/2025/03/18/aneel-prorroga-concessoes-da-taesa-apos-impactos-da-pandemia/",
        "https://gesel.ie.ufrj.br/wp-content/uploads/2022/08/Valle_2022_08_30.pdf",
        "https://eixos.com.br/energia-eletrica/licenciamento-ambiental-e-responsavel-por-70-dos-atrasos-em-linhas-de-transmissao/",
        "https://brasilenergia.com.br/energia/o-atraso-no-licenciamento-ambiental-e-o-direito-na-transmissao",
        "https://portal.tcu.gov.br/imprensa/noticias/tcu-aprova-solucao-consensual-em-contratos-de-transmissao-de-energia-eletrica",
        "https://www.saopaulo.sp.leg.br/iah/fulltext/leis/L17267.pdf",
        "https://legislativo.palmas.to.gov.br/media/leis/decreto-2.876-2026-03-18-23-3-2026-14-53-1.pdf",
        "https://www.jornalopcao.com.br/goiania/apos-decisao-do-mpgo-equatorial-goias-afirma-que-responsabilidade-por-podas-regulares-e-da-prefeitura-765210/",
    }
    todas = {u for p in cfg["precedentes"].values() for u in p["urls"]}
    assert todas == urls_permitidas  # só as fontes fornecidas, nenhuma a mais
    assert cfg["contraponto_obrigatorio"] in cfg["precedentes"]
    for t in cfg["tipos"]:
        m = dependencias.manual_da_dependencia(t["id"])
        assert m["precedentes"] and m["cautela"] and t["status"] == "rascunho — revisar"
        assert "garantia" not in json.dumps(m, ensure_ascii=False).lower().replace(
            "não há garantia", ""
        ).replace("não é garantia", "")


def test_rn_1137_ponta_a_ponta_dependencias_no_texto_com_citacao_verificada():
    from scripts import relatorio_tipos as rt

    itens = rt.analisar()
    r = rt.resumo(itens)
    assert r["obrigacoes"] == 168 and r["outros"] <= 10
    do_texto = [d for i in itens for d in i["dependencias"] if d["origem"] == "texto"]
    assert do_texto and all(
        d["citacao"] == "verified" for d in do_texto
    )  # trecho literal confere na norma
    assert {"autorizacao_municipal"} <= {
        d["id"] for d in do_texto
    }  # manejo vegetal / Poder Público Municipal
    por_id = {i["id"]: i for i in itens}
    for i in por_id.values():
        for d in i["dependencias"]:
            if d["origem"] == "texto":
                assert " ".join(d["trecho_literal"].split()) in i["texto"], d[
                    "trecho_literal"
                ]  # frase inteira
    assert all(
        d["trecho_literal"] is None
        for i in itens
        for d in i["dependencias"]
        if d["origem"] != "texto"
    )


def test_trecho_literal_e_a_frase_inteira_mesmo_com_quebra_de_linha_do_pdf():
    linhas = [
        "A distribuidora deve registrar as interações com o Poder Público",
        "Municipal sobre o manejo da vegetação,",
        "com data e hora.",
    ]
    texto = chr(10).join(linhas)
    (d,) = [x for x in dependencias.detectar(texto) if x["id"] == "autorizacao_municipal"]
    assert d["trecho_literal"] == texto.rstrip(".")  # não para na quebra de linha (o ponto final fica de fora)


@pytest.mark.parametrize(
    "texto",
    [
        "b) Município/bairro da ocorrência aberta;",  # município como dado, não como autorização
        "j) Quantidade de equipes em atividade, segregadas por município e o total na área de atuação; e",
        "A distribuidora deve manter canal com os poderes públicos municipais.",
        "Prazo de até o terceiro dia útil.",
        "Energia fornecida por geração distribuída.",
        "Supressão de cargas em caso de emergência.",
        "A Portaria que instituir Comitê de Crise deverá atender as demais disposições.",
    ],
)
def test_nao_marca_dependencia_em_falso_positivos_conhecidos(texto):
    assert [d for d in dependencias.detectar(texto) if d["origem"] == "texto"] == []


def test_todo_tipo_de_dependencia_traz_o_contraponto_de_pedidos_negados():
    cfg = dependencias.carregar()
    for t in cfg["tipos"]:
        assert cfg["contraponto_obrigatorio"] in t["precedentes"], t["id"]


def test_texto_em_nfd_nao_desloca_o_trecho():
    import unicodedata

    texto = unicodedata.normalize(
        "NFD", "O Município deve acionar a Prefeitura para a poda da vegetação."
    )
    (d,) = [x for x in dependencias.detectar(texto) if x["id"] == "autorizacao_municipal"]
    assert (
        d["sinal"]
        and d["trecho_literal"].startswith("O Município")
        and len(tipos.normalizar(texto)) == len(unicodedata.normalize("NFC", texto))
    )
