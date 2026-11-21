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


def test_alinea_de_conteudo_nao_herda_o_tipo_do_caput():
    alinea = "d) A responsabilidade pelas despesas operacionais;"
    pai = "O acordo de Cessão Emergencial deve conter:"
    sozinha = tipos.classificar(alinea)
    com_pai = tipos.classificar(alinea, pai, detalhe=True)
    assert com_pai["tipo"] == sozinha["tipo"] == "outros"  # o texto do pai não dá tipo
    assert com_pai["por"] == "detalhe do dispositivo-pai (sem sinal próprio)" and com_pai[
        "pai"
    ].startswith("O acordo")
    # alínea com verbo próprio continua tendo tipo próprio, mesmo sob um caput de outro tipo
    propria = tipos.classificar(
        "b) publicar o plano no sítio eletrônico da distribuidora", pai, detalhe=True
    )
    assert propria["tipo"] == "publicar_no_site"


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


# --- dependências externas: só com ATO do terceiro ---------------------------------------------------

COM_ATO = [
    ("autorizacao_municipal", "A distribuidora deve executar a poda mediante autorização da Prefeitura."),
    ("licenciamento_ambiental", "A obra depende de licença ambiental de instalação."),
    ("sistema_aneel_indisponivel", "A distribuidora deve protocolar o documento no sistema da ANEEL."),
    ("operador_sistema", "A manobra só pode ser feita após autorização do ONS."),
    ("dado_de_terceiro", "A apuração usa dados fornecidos por terceiros."),
    ("evento_extremo_defesa_civil", "O prazo vale após decreto de situação de emergência."),
    ("ato_da_aneel", "As distribuidoras devem implantar o processo em até 60 dias, contados da publicação das instruções pela ANEEL."),
    ("ato_da_aneel", "As distribuidoras devem disponibilizar uma API, conforme instrução técnica emitida pela ANEEL, para a extração."),
]  # fmt: skip


@pytest.mark.parametrize(("dep", "texto"), COM_ATO)
def test_dependencia_so_quando_ha_ato_do_terceiro(dep, texto):
    deps = dependencias.detectar(texto)
    assert [d["id"] for d in deps] == [dep], deps
    assert deps[0]["origem"] == "texto" and deps[0]["trecho_literal"] in texto


@pytest.mark.parametrize(
    "texto",
    [
        # definições e menções sem ato do terceiro
        "94. As distribuidoras devem estabelecer um plano de manejo vegetal, em coordenação com o Poder Público Municipal.",
        "II - Até 180 dias para implementar o registro das interações com o Poder Público Municipal em relação ao manejo.",
        "Os indicadores DICRI e DISE são apurados por interrupção ocorrida em Situação de Emergência.",
        "Implantar processo de comunicação da evolução dos eventos climáticos severos.",
        "§ 2º O Comitê de Crise deverá ser estabelecido por Portaria emitida pelo Diretor-Geral.",
        "b) Município/bairro da ocorrência aberta;",
        "j) Quantidade de equipes em atividade, segregadas por município e o total na área de atuação; e",
        "Prazo de até o terceiro dia útil.",
        "Energia fornecida por geração distribuída.",
        "Supressão de cargas em caso de emergência.",
        "A distribuidora deve manter canal com os poderes públicos municipais.",
    ],
)
def test_nao_marca_dependencia_sem_ato_do_terceiro(texto):
    assert dependencias.detectar(texto, "articular_coordenar_terceiros") == []


def test_dependencia_inferida_pelo_tipo_nao_e_marcada_por_padrao():
    texto = "A distribuidora deve enviar relatório à ANEEL."
    assert dependencias.detectar(texto, "enviar_informacao_aneel") == []
    inferidas = dependencias.detectar(texto, "enviar_informacao_aneel", incluir_inferidas=True)
    assert {d["id"] for d in inferidas} == {"sistema_aneel_indisponivel", "dado_de_terceiro"}
    assert all(
        d["origem"] == "inferida_pelo_tipo" and d["trecho_literal"] is None for d in inferidas
    )


def test_trecho_literal_e_a_frase_inteira_mesmo_com_quebra_de_linha_do_pdf():
    linhas = [
        "A distribuidora deve executar a poda mediante autorização da Prefeitura",
        "Municipal, com data e hora.",
    ]
    texto = chr(10).join(linhas)
    (d,) = dependencias.detectar(texto)
    assert d["trecho_literal"] == texto.rstrip(".")  # não para na quebra de linha


def test_ponto_de_art_e_de_milhar_nao_encerra_a_frase():
    texto = "Nos termos do art. 3º do Decreto 12.068, as distribuidoras aguardam instrução técnica emitida pela ANEEL."
    (d,) = dependencias.detectar(texto)
    assert d["trecho_literal"].startswith("Nos termos do art. 3º do Decreto 12.068")


def test_verificador_de_citacao_e_chamado_com_o_trecho():
    texto = "A distribuidora deve executar a poda mediante autorização da Prefeitura."
    vistos = []
    dependencias.detectar(texto, None, verificar=lambda t: vistos.append(t) or "verified")
    assert vistos and all(t in texto for t in vistos)


def test_texto_em_nfd_nao_desloca_o_trecho():
    import unicodedata

    texto = unicodedata.normalize("NFD", "O Município só poda mediante autorização da Prefeitura.")
    (d,) = dependencias.detectar(texto)
    assert d["id"] == "autorizacao_municipal" and d["trecho_literal"].startswith("O Município")
    assert len(tipos.normalizar(texto)) == len(unicodedata.normalize("NFC", texto))


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


def test_rn_1137_ponta_a_ponta_so_dependencia_de_ato_com_citacao_verificada():
    from scripts import relatorio_tipos as rt

    itens = rt.analisar()
    r = rt.resumo(itens)
    assert (
        r["obrigacoes"] == 170
    )  # +2 com "pode"/"não pode" singular (itens 131 e 137, auditoria C1)
    assert (
        r["detalhe_do_dispositivo_pai_sem_tipo_proprio"] > 0
    )  # alíneas de conteúdo não herdam tipo
    deps = [d for i in itens for d in i["dependencias"]]
    assert deps and {d["id"] for d in deps} == {"ato_da_aneel"} and len(deps) == 4
    assert all(d["origem"] == "texto" and d["citacao"] == "verified" for d in deps)
    for i in itens:
        for d in i["dependencias"]:
            assert " ".join(d["trecho_literal"].split()) in i["texto"]  # frase inteira, literal


def test_todo_tipo_de_dependencia_traz_o_contraponto_de_pedidos_negados():
    cfg = dependencias.carregar()
    for t in cfg["tipos"]:
        assert cfg["contraponto_obrigatorio"] in t["precedentes"], t["id"]
