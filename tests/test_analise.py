"""Análise regulatória preliminar: tipo só com regra e IA de acordo, dependência só com ato do terceiro
(citação verificada), referências só da lista versionada e nenhuma empresa real no JSON da demo."""

import json
import re
from pathlib import Path

from athenix import analise, dependencias, tipos

ROOT = Path(__file__).resolve().parents[1]
PLANO = json.loads((ROOT / "landing/src/content/plano-rn1137.json").read_text(encoding="utf-8"))
TEXTO_PLANO = "A distribuidora deve elaborar o plano de contingência e revisá-lo anualmente."
EMPRESAS = (
    "Equatorial|Taesa|Enel|CPFL|Cemig|Energisa|Copel|Celesc|Eletrobras|Eletropaulo|Neoenergia|"
    "Coelba|Celpe|Light|Celg|CEEE|Elektro|EDP|Iberdrola|Engie|Cteep|ISA|Alupar|Equatorial"
)


def folhas(v):
    if isinstance(v, dict):
        for x in v.values():
            yield from folhas(x)
    elif isinstance(v, list):
        for x in v:
            yield from folhas(x)
    elif isinstance(v, str):
        yield v


def test_tipo_so_regra_quando_a_ia_nao_foi_consultada():
    t = analise._tipo(TEXTO_PLANO, False, {}, "x", tipos.carregar())
    assert t["id"] and t["situacao"] == "so_regra" and "IA não feita" in t["por"]


def test_tipo_definitivo_so_quando_regra_e_ia_concordam():
    cfg = tipos.carregar()
    regra = analise._tipo(TEXTO_PLANO, False, {}, "x", cfg)["id"]
    ok = analise._tipo(TEXTO_PLANO, False, {"x": regra}, "x", cfg)
    assert ok["situacao"] == "concordam" and ok["id"] == regra
    outro = next(t["id"] for t in cfg["tipos"] if t["id"] not in (regra, "outros"))
    nao = analise._tipo(TEXTO_PLANO, False, {"x": outro}, "x", cfg)
    assert nao["situacao"] == "a_revisar" and nao["id"] is None and nao["nome"] is None
    assert analise._tipo(TEXTO_PLANO, False, {"y": regra}, "x", cfg)["situacao"] == "a_revisar"


def test_alinea_de_conteudo_sem_verbo_proprio_fica_sem_tipo():
    t = analise._tipo("a data e a hora do evento;", True, {}, "x", tipos.carregar())
    assert t["id"] is None and t["situacao"] == "sem_tipo"


def test_dependencia_no_texto_so_com_citacao_verificada_e_ato_da_aneel():
    achadas = [d for t in PLANO["temas"] for d in t["dependencias_no_texto"]]
    assert len(achadas) == 4 and {d["id"] for d in achadas} == {"ato_da_aneel"}
    for d in achadas:
        assert "contados da publicação das instruções pela ANEEL" in d["trecho_literal"] or "instrução" in d["trecho_literal"]  # fmt: skip
        assert "\n" not in d["trecho_literal"]


def test_pratica_do_manejo_traz_referencia_publica_e_o_contraponto():
    a = PLANO["analise"]
    dep = a["dependencias"][a["pratica_por_tema"]["manejo"]]
    assert dep["id"] == "autorizacao_municipal" and dep["caminho"] and dep["cautela"]
    assert "disputada" in dep["cautela"] and "negados" in dep["cautela"]
    assert {p["id"] for p in dep["precedentes"]} >= {"poda_municipal", "contraponto_tcu"}
    assert a["contraponto"]["urls"]


def test_todo_link_de_referencia_vem_da_lista_versionada():
    cfg = dependencias.carregar()
    permitidos = {u for p in cfg["precedentes"].values() for u in p["urls"]}
    for dep in PLANO["analise"]["dependencias"].values():
        for p in dep["precedentes"]:
            assert set(p["urls"]) <= permitidos
    assert set(PLANO["analise"]["contraponto"]["urls"]) <= permitidos


def test_manual_so_para_tipo_mostrado_e_marcado_como_sugestao():
    for o in PLANO["obrigacoes"]:
        a = o.get("analise")
        if not a:
            continue
        t = a["tipo"]
        assert (t["id"] in PLANO["analise"]["manuais"]) == (t["id"] is not None)
    assert PLANO["analise"]["rotulo"].startswith("Análise regulatória preliminar")


def test_json_da_demo_nao_traz_nome_de_empresa_real():
    padrao = re.compile(rf"\b({EMPRESAS})\b")
    for texto in folhas(PLANO):
        if texto.startswith("http"):
            continue
        assert not padrao.search(texto), texto[:120]
    ref = PLANO["referencia_escala"]
    assert (
        ref["autos"] == 21 and ref["mediana_reais"] == 10349703 and ref["maximo_reais"] == 48654893
    )


def test_manchete_usa_valor_por_infracao_e_nunca_soma():
    for t in PLANO["temas"]:
        f = t["faixa_preliminar"] or t["faixa"]
        if f:
            assert f["maximo_pct"]["com_teto"] <= max(
                f["teto_grupo_pct"], f["teto_legal_lei_pct"] or 0
            )


def test_causas_externas_por_tema_so_com_origem_declarada():
    temas = {t["id"] for t in PLANO["temas"]}
    a = PLANO["analise"]
    assert set(a["causas_por_tema"]) <= temas and set(a["pratica_por_tema"]) <= temas
    for causa in a["causas_por_tema"].values():
        assert "sem citação" in causa["nota"] and "jurídico" in causa["nota"]
    com_ato = {t["id"] for t in PLANO["temas"] if t["dependencias_no_texto"]}
    assert com_ato == {"poder_publico", "outros"}  # os prazos dos arts. 14 a 16 estão nestes temas


def test_titulo_completo_nao_corta_o_texto_e_o_curto_so_abrevia():
    for o in PLANO["obrigacoes"]:
        assert not o["titulo_completo"].endswith("…")
        if o["titulo"].endswith("…"):
            inicio = o["titulo"][:-1].rstrip()
            assert o["titulo_completo"].startswith(inicio) and len(o["titulo_completo"]) > len(
                inicio
            )
        else:
            assert o["titulo_completo"] == o["titulo"]
