"""Copia fontes oficiais já versionadas e localiza as citações exibidas no site, sem rede ou IA."""

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from athenix import impacto  # noqa: E402
from athenix.config import Settings  # noqa: E402
from athenix.structure import extract  # noqa: E402
from scripts.demo.conferir_citacoes import compacto  # noqa: E402

PUBLICO = ROOT / "landing/public/fontes"
INDICE = ROOT / "landing/src/content/fontes-publicas.json"


def chave(texto):
    return compacto(texto).strip('“”"').removesuffix("…")


def documentos():
    catalogo = json.loads((ROOT / "tests/fontes_impacto/fontes.json").read_text(encoding="utf-8"))
    aprovados = {
        d["sha256"]: ROOT / "tests/fontes_impacto" / d["arquivo"]
        for d in catalogo["documentos"]
        if d.get("fonte", "").startswith("oficial")
    }
    gabarito = json.loads((ROOT / "tests/gabarito/fontes.json").read_text(encoding="utf-8"))
    aprovados.update(
        {
            d["sha256"]: ROOT / "tests/gabarito" / d["arquivo"]
            for d in gabarito["documentos"]
            if d.get("fonte") == "oficial_previamente_obtida"
        }
    )
    docs = {d["sha256"]: d for d in impacto.carregar()["fontes"].values()}
    for norma in ("rn1137", "ren1174"):
        p = json.loads(
            (ROOT / f"landing/src/content/plano-{norma}.json").read_text(encoding="utf-8")
        )
        for d in p.get("comparacao_anterior", {}).get("fontes", {}).values():
            docs[d["sha256"]] = d
    pasta = ROOT / "tests/fontes_impacto/esclarecimentos"
    for d in json.loads((pasta / "fontes.json").read_text(encoding="utf-8"))["documentos"]:
        aprovados[d["sha256"]] = pasta / d["arquivo"]
        docs[d["sha256"]] = dict(d, arquivo=(pasta / d["arquivo"]).relative_to(ROOT).as_posix())
    for sha, d in docs.items():
        arquivo = (ROOT / d["arquivo"]).resolve()
        if sha not in aprovados or arquivo != aprovados[sha].resolve() or ".local" in arquivo.parts:
            raise ValueError(f"Fonte sem aprovação no catálogo oficial: {d['arquivo']}")
        if hashlib.sha256(arquivo.read_bytes()).hexdigest() != sha:
            raise ValueError(f"Hash divergente: {d['arquivo']}")
    return docs


def paginas(arquivo):
    import pypdfium2

    with pypdfium2.PdfDocument(str(arquivo)) as pdf:
        return [compacto(p.get_textpage().get_text_range()) for p in pdf]


def localizar(texto, folhas, incerta=False):
    agulha = compacto(texto)
    tudo = "".join(folhas)
    inicio = tudo.find(agulha)
    metodo = "trecho literal"
    if inicio < 0 and incerta:
        # Localiza a página, sem converter uma redação incerta em citação confirmada.
        agulha = agulha[:100]
        inicio = tudo.find(agulha)
        metodo = "início do trecho; redação permanece incerta"
    if inicio < 0:
        raise ValueError(f"Trecho não localizado no PDF: {texto[:100]}")
    acumulado = 0
    primeira = ultima = None
    for n, folha in enumerate(folhas, 1):
        fim = acumulado + len(folha)
        if acumulado <= inicio < fim:
            primeira = n
        if acumulado < inicio + len(agulha) <= fim:
            ultima = n
        acumulado = fim
    return {"pagina": primeira, "ultima_pagina": ultima, "localizacao": metodo}


def citacoes(p):
    comparacao = p.get("comparacao_anterior")
    if comparacao:
        for item in comparacao["itens"].values():
            if item["classe"] == "alterado":
                yield comparacao["fontes"]["v2"]["sha256"], item["anterior"]["trecho"], False
                yield comparacao["fontes"]["v3"]["sha256"], item["atual"]["trecho"], False
        for r in comparacao["registros"].values():
            if not r["confere_v3"]:
                yield (
                    comparacao["fontes"]["v3"]["sha256"],
                    comparacao["itens"][r["item"]]["atual"]["trecho"],
                    False,
                )
    for r in p.get("rascunhos_aneel", []):
        for f in r["referencias"]:
            yield f["fonte"]["sha256"], f["trecho"], False
            for e in f["possiveis_esclarecimentos"]:
                yield e["fonte"]["sha256"], e["citacao"], False
    sha = p["norma"]["sha256"]
    for lista in ("obrigacoes", "outros_dispositivos", "sem_dever_identificado"):
        for o in p[lista]:
            yield sha, o.get("trecho"), False
            for k in ("marco", "condicao"):
                yield sha, (o.get(k) or {}).get("trecho"), False
            f = (o.get("esclarecimento") or {}).get("fonte")
            if f:
                yield f["sha256"], f["trecho"], False
    for i in p["infracoes"].values():
        yield i["fonte"]["sha256"], i["trecho"], False
    for c in (
        p["reducao"]["regras"] + p["reducao"]["medidas"] + list(p["escala_de_gravidade"].values())
    ):
        yield c["sha256"], c["trecho"], False
    for s in p["sucessao_no_tempo"]:
        for r in s["redacoes"]:
            yield r["fonte"]["sha256"], r["trecho"], r["estado"] == "incerta"
    for c in p["a_confirmar"]["casos"]:
        yield sha, c.get("trecho"), False
        for e in c.get("possiveis_esclarecimentos", []):
            yield e["fonte"]["sha256"], e["citacao"], False


def compilar():
    docs = documentos()
    saida = {"documentos": {}, "citacoes": {}, "infracoes_demo": {}}
    cache = {}
    vistos = set()
    for norma in ("rn1137", "ren1174"):
        p = json.loads(
            (ROOT / f"landing/src/content/plano-{norma}.json").read_text(encoding="utf-8")
        )
        entradas = list(citacoes(p))
        if norma == "rn1137":
            demo = json.loads(
                (ROOT / "landing/src/content/demo-rn1137.json").read_text(encoding="utf-8")
            )
            entradas += [(p["norma"]["sha256"], u["texto"], False) for u in demo["unidades"]]
            for o in demo["obrigacoes"]:
                for f in o["impacto"]["enquadramentos"]:
                    atual = p["infracoes"][f["dispositivo"]]
                    saida["infracoes_demo"][f["dispositivo"]] = {
                        "trecho": atual["trecho"],
                        "sha256": atual["fonte"]["sha256"],
                    }
                entradas += [
                    (
                        p["infracoes"][f["dispositivo"]]["fonte"]["sha256"],
                        p["infracoes"][f["dispositivo"]]["trecho"],
                        False,
                    )
                    for f in o["impacto"]["enquadramentos"]
                ]
        for sha, texto, incerta in entradas:
            if not texto or (sha, texto) in vistos:
                continue
            vistos.add((sha, texto))
            d = docs[sha]
            arquivo = ROOT / d["arquivo"]
            url = "/fontes/" + arquivo.name
            saida["documentos"][sha] = {"arquivo": d["arquivo"], "url": url, "sha256": sha}
            local = {
                "url": url,
                "pagina": None,
                "ultima_pagina": None,
                "localizacao": "HTML oficial salvo",
            }
            if arquivo.suffix.lower() == ".pdf":
                if sha not in cache:
                    cache[sha] = paginas(arquivo)
                local.update(localizar(texto, cache[sha], incerta))
                local["url"] += f"#page={local['pagina']}"
            else:
                if sha not in cache:
                    cache[sha] = compacto(
                        extract(
                            arquivo.read_bytes(),
                            "text/html",
                            Settings(ai_mode="off", model="", api_key=""),
                            "norm",
                        )["text"]
                    )
                if compacto(texto) not in cache[sha]:
                    raise ValueError(f"Trecho não localizado no HTML: {texto[:100]}")
            saida["citacoes"].setdefault(sha, {})[chave(texto)] = local
    return saida


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    indice = compilar()
    PUBLICO.mkdir(exist_ok=True)
    for d in indice["documentos"].values():
        destino = PUBLICO / Path(d["arquivo"]).name
        shutil.copyfile(ROOT / d["arquivo"], destino)
        assert hashlib.sha256(destino.read_bytes()).hexdigest() == d["sha256"]
    INDICE.write_text(
        json.dumps(indice, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        f"{len(indice['documentos'])} fontes oficiais; {sum(len(v) for v in indice['citacoes'].values())} citações localizadas"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
