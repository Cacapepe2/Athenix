"""Contagem de autos por dispositivo (dados sintéticos; os dados reais ficam em .local/, fora do git)."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import autos_por_dispositivo as apd  # noqa: E402

CAT = json.loads((ROOT / "athenix/data/penalidades_ren846.json").read_text(encoding="utf-8"))


def auto(n, enq, valor="1.000,00", nome="Distribuidora Teste S.A.", doc="11111111000111"):
    return {
        "NumAutoInfracao": f"{n:04d}/2026-SFE", "NumCPFCNPJAgenteFiscalizado": doc,
        "SigAgenteFiscalizador": "ANEEL", "NomAgenteFiscalizado": nome, "CodObjetoFiscalizado": "",
        "NomNaturezaFiscalizacao": "Técnica", "DscEnquadramentoAI": enq, "NumTermoEncerramento": "x",
        "DatDecisaoDiretoria": "", "VlrMultaAposDiretoria": "", "VlrMultaAposJuizo": "", "VlrPenalidade": valor,
    }  # fmt: skip


def test_inciso_so_quando_o_campo_traz_artigo_e_inciso():
    sem = auto(1, "Multa do Grupo IV (REN 846/2019) Art. 12")
    com = auto(2, "Multa do Grupo IV (REN 846/2019) Art. 12, XXVI / Multa do Grupo III (REN 846/2019) Art. 11, IV")  # fmt: skip
    assert apd.dispositivos_do_auto(sem) == set()
    assert apd.dispositivos_do_auto(com) == {"Art. 12, XXVI", "Art. 11, IV"}
    assert apd.campos_com_inciso([sem, com]) == {"DscEnquadramentoAI": 1}


def test_conta_so_distribuicao_e_resume_n_mediana_maximo():
    rows = [
        auto(1, "Multa do Grupo IV (REN 846/2019) Art. 12, XXVI", "1.000,00"),
        auto(2, "Multa do Grupo IV (REN 846/2019) Art. 12, XXVI", "3.000,00", doc="22222222000122"),
        auto(3, "Multa do Grupo IV (REN 846/2019) Art. 12, XXVI", "9.000,00", doc="33333333000133"),
        auto(
            4,
            "Multa do Grupo IV (REN 846/2019) Art. 12, XXVI",
            "5.000,00",
            nome="Geradora X",
            doc="44444444000144",
        ),  # fmt: skip
    ]
    res = apd.analisar(rows, [], CAT)
    assert res["distribuicao"] == 3 and res["distribuicao_com_inciso"] == 3
    assert res["autos_por_dispositivo"]["Art. 12, XXVI"] == 3
    s = apd.resumo(res["valores_por_dispositivo"]["Art. 12, XXVI"])
    assert (s["n"], str(s["mediana"]), str(s["maximo"])) == (3, "3000.00", "9000.00")
    assert len(res["grupo_iv"]) == 3
    texto = apd.markdown(res)
    assert "Distribuidora Teste" not in texto and "Geradora" not in texto  # sem nome de empresa
    assert "Art. 12, XXVIII" in texto


def test_sem_inciso_no_campo_o_relatorio_diz_e_cai_para_o_grupo_iv():
    rows = [auto(i, "Multa do Grupo IV (REN 846/2019) Art. 12", f"{i},00", doc=f"{i:014d}") for i in range(1, 6)]  # fmt: skip
    res = apd.analisar(rows, [], CAT)
    assert res["distribuicao_com_inciso"] == 0 and len(res["grupo_iv"]) == 5
    texto = apd.markdown(res)
    assert "Nenhuma coluna traz artigo + inciso" in texto and "n = **5**" in texto
