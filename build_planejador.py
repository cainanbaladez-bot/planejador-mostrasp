# -*- coding: utf-8 -*-
"""Gera planejador.html: injeta os dados da 49ª Mostra (enxutos) no template.

Uso:  py -3.10 build_planejador.py
Reuso p/ 50ª edição: rode o scraper, aponte DATA para a nova pasta e ajuste o título no template.
"""
import json
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "mostra-scraper-completo" / "mostra-scraper" / "data"
TEMPLATE = BASE / "planejador.template.html"
SAIDA = BASE / "planejador.html"
# docs/ é o que o GitHub Pages publica (o PWA mora lá: manifesto, sw.js, ícones)
SAIDA_SITE = BASE / "docs" / "index.html"

CAMPOS_FILME = [
    "id", "slug", "titulo", "titulo_original", "sinopse", "genero", "pais",
    "ano", "duracao", "secao", "classificacao", "diretores", "elenco",
    "roteiro", "fotografia", "montagem", "musica", "producao", "distribuicao",
    "imagem", "trailer", "link_compra", "url_pagina", "n_sessoes",
]
CAMPOS_SESSAO = [
    "sessao_id", "filme_id", "titulo", "data", "hora", "sala", "cinema",
    "endereco_cinema", "idioma", "legendas", "secao", "duracao", "link_compra",
]

def enxuga(lista, campos):
    return [{c: item.get(c, "") for c in campos} for item in lista]

filmes = json.loads((DATA / "mostra_49_filmes.json").read_text(encoding="utf-8"))
sessoes = json.loads((DATA / "mostra_49_sessoes.json").read_text(encoding="utf-8"))

# enriquecimento opcional (festivais + Letterboxd) — gerado por enrich_filmes.py
arq_enriq = DATA / "enriquecimento.json"
enriq = json.loads(arq_enriq.read_text(encoding="utf-8")) if arq_enriq.exists() else {}

filmes_slim = enxuga(filmes, CAMPOS_FILME)
for f in filmes_slim:
    e = enriq.get(f["id"], {})
    f["festivais"] = e.get("festivais", [])
    f["premiado"] = e.get("premiado", False)
    f["premio_txt"] = e.get("premio_txt", "")
    f["lb_nota"] = e.get("lb_nota")
    f["lb_votos"] = e.get("lb_votos")
    f["lb_url"] = e.get("lb_url")

filmes_js = json.dumps(filmes_slim, ensure_ascii=False, separators=(",", ":"))
sessoes_js = json.dumps(enxuga(sessoes, CAMPOS_SESSAO), ensure_ascii=False, separators=(",", ":"))

# </script> dentro de string JS quebraria o parser HTML
filmes_js = filmes_js.replace("</", "<\\/")
sessoes_js = sessoes_js.replace("</", "<\\/")

html = TEMPLATE.read_text(encoding="utf-8")
html = html.replace("/*__FILMES__*/[]", filmes_js).replace("/*__SESSOES__*/[]", sessoes_js)
SAIDA.write_text(html, encoding="utf-8")
SAIDA_SITE.parent.mkdir(parents=True, exist_ok=True)
SAIDA_SITE.write_text(html, encoding="utf-8")

print(f"OK: {SAIDA.name} + docs/{SAIDA_SITE.name} — {len(filmes)} filmes, "
      f"{len(sessoes)} sessões, {SAIDA.stat().st_size/1024:.0f} KB")
