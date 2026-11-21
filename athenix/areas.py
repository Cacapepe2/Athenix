"""Área responsável SUGERIDA para cada obrigação (quem faz o quê), a partir do tipo da obrigação.
O mapeamento fica num único arquivo de dados (data/areas_por_tipo.json), fácil de revisar: é sugestão."""

import json
import re
from pathlib import Path

ARQUIVO = Path(__file__).parent / "data" / "areas_por_tipo.json"


def carregar(path=ARQUIVO):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def area_de(tipo_id, texto, cfg=None):
    """Área sugerida: palavra-chave do texto (ex.: vegetação) vence; senão o tipo; senão o padrão."""
    cfg = cfg or carregar()
    for regra in cfg["por_palavra"]:
        if re.search(regra["padrao"], texto or "", re.I):
            return regra["area"]
    return cfg["por_tipo"].get(tipo_id or "", cfg["padrao"])


def area_com_origem(tipo_id, ia_tipo, texto, cfg=None):
    """(área, origem): origem "regra" (tipo achado pela regra ou palavra-chave), "ia" (tipo sugerido pela IA quando a
    regra não achou; sai marcada "área sugerida (IA)") ou None quando continua "A definir"."""
    cfg = cfg or carregar()
    for regra in cfg["por_palavra"]:
        if re.search(regra["padrao"], texto or "", re.I):
            return regra["area"], "regra"
    if tipo_id and cfg["por_tipo"].get(tipo_id, cfg["padrao"]) != cfg["padrao"]:
        return cfg["por_tipo"][tipo_id], "regra"
    if (
        ia_tipo
        and ia_tipo != "outros"
        and cfg["por_tipo"].get(ia_tipo, cfg["padrao"]) != cfg["padrao"]
    ):
        return cfg["por_tipo"][ia_tipo], "ia"
    return cfg["padrao"], None
