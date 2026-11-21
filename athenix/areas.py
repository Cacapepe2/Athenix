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
