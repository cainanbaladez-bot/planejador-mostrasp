#!/usr/bin/env python3
"""
Scraper da programação da Mostra Internacional de Cinema em São Paulo
=====================================================================

Raspa a API pública (api.mostra.org) que alimenta https://mostra.org/programacao/
e monta um banco de dados completo com:

  - Filmes: título, título original, sinopse, direção (com bio), duração, país,
    ano, seção, gênero, elenco, roteiro, fotografia, montagem, som, produção,
    música, distribuição, trailer, imagens, tags etc.
  - Sessões: data, hora, sala, idioma, legendas, link de compra.
  - Cinemas: nome normalizado + endereço (tabela VENUES, editável).

Saídas (em ./data/):
  - raw/filme_<slug>.json ......... resposta bruta da API por filme (cache)
  - mostra_<ed>_filmes.json ....... filmes normalizados
  - mostra_<ed>_sessoes.json ...... sessões normalizadas (com dados do cinema)
  - mostra_<ed>_cinemas.json ...... cinemas/salas com endereço
  - mostra_<ed>.db ................ SQLite (tabelas filmes, sessoes, cinemas, diretores)
  - mostra_<ed>_sessoes.csv / _filmes.csv

Uso:
  python3 scrape_mostra.py                # edição padrão (EDITION abaixo)
  python3 scrape_mostra.py --edition 50   # quando a 50ª Mostra sair
  python3 scrape_mostra.py --edition 50 --refresh   # ignora cache raw/

Quando a nova programação for publicada, normalmente basta trocar o número da
edição. Se aparecerem salas novas, o script avisa quais não estão na tabela
VENUES para você completar o endereço.
"""

import argparse
import csv
import html
import json
import re
import sqlite3
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

API_BASE = "https://api.mostra.org"
STATIC_BASE = "https://static.mostra.org"
EDITION = 49          # edição padrão (49ª Mostra = 2025). Troque via --edition.
LOCALE = "pt"
WORKERS = 8           # requisições paralelas (seja gentil com o servidor)
RETRY = 3
TIMEOUT = 30
UA = "Mozilla/5.0 (compatible; mostra-db-pessoal/1.0)"

# ---------------------------------------------------------------------------
# Tabela de cinemas/endereços. A API só devolve o nome da sala (pro_sala),
# ex.: "ESPAÇO PETROBRAS DE CINEMA SALA 2". O casamento é feito por prefixo
# normalizado (sem acentos, maiúsculas). Complete/ajuste quando surgirem
# salas novas — o script lista as que ficarem sem match.
# ---------------------------------------------------------------------------
VENUES = [
    # (prefixo de match, nome do cinema, endereço)
    ("ESPACO PETROBRAS DE CINEMA", "Espaço Petrobras de Cinema (Espaço Itaú Augusta)",
     "Rua Augusta, 1475 - Consolação, São Paulo - SP"),
    ("MULTIPLEX PLAYARTE MARABA", "Multiplex PlayArte Marabá",
     "Avenida Ipiranga, 757 - República, São Paulo - SP"),
    ("MULTIPLEX MARABA", "Multiplex PlayArte Marabá",
     "Avenida Ipiranga, 757 - República, São Paulo - SP"),
    ("CINEMATECA BRASILEIRA", "Cinemateca Brasileira",
     "Largo Senador Raul Cardoso, 207 - Vila Clementino, São Paulo - SP"),
    ("CINESESC", "CineSesc",
     "Rua Augusta, 2075 - Cerqueira César, São Paulo - SP"),
    ("CINESALA", "Cinesala",
     "Rua Fradique Coutinho, 361 - Pinheiros, São Paulo - SP"),
    ("CINE SATYROS BIJOU", "Cine Satyros Bijou",
     "Praça Franklin Roosevelt, 172 - Consolação, São Paulo - SP"),
    ("CINE SEGALL", "Cine Segall - Museu Lasar Segall",
     "Rua Berta, 111 - Vila Mariana, São Paulo - SP"),
    ("MUSEU LASAR SEGALL", "Cine Segall - Museu Lasar Segall",
     "Rua Berta, 111 - Vila Mariana, São Paulo - SP"),
    ("IMS PAULISTA", "IMS Paulista (Instituto Moreira Salles)",
     "Avenida Paulista, 2424 - Bela Vista, São Paulo - SP"),
    ("RESERVA CULTURAL", "Reserva Cultural",
     "Avenida Paulista, 900 - Bela Vista, São Paulo - SP"),
    ("SATO CINEMA", "Sato Cinema",
     "Rua Augusta, 1470/1475 - Consolação, São Paulo - SP"),
    ("CULTURA ARTISTICA", "Teatro Cultura Artística",
     "Rua Nestor Pestana, 196 - Consolação, São Paulo - SP"),
    ("CCSP", "Centro Cultural São Paulo (CCSP)",
     "Rua Vergueiro, 1000 - Paraíso, São Paulo - SP"),
    ("CENTRO CULTURAL SAO PAULO", "Centro Cultural São Paulo (CCSP)",
     "Rua Vergueiro, 1000 - Paraíso, São Paulo - SP"),
    ("CENTRO CULTURAL OLIDO", "Centro Cultural Olido",
     "Avenida São João, 473 - Centro, São Paulo - SP"),
    ("BIBLIOTECA ROBERTO SANTOS", "Biblioteca Roberto Santos",
     "Rua Cisplatina, 505 - Ipiranga, São Paulo - SP"),
    ("CENTRO DE FORMACAO CULTURAL CIDADE TIRADENTES", "Centro de Formação Cultural Cidade Tiradentes",
     "Rua Inácio Monteiro, 6900 - Cidade Tiradentes, São Paulo - SP"),
    ("AUDITORIO IBIRAPUERA", "Auditório Ibirapuera",
     "Avenida Pedro Álvares Cabral - Parque Ibirapuera, São Paulo - SP"),
    ("VALE DO ANHANGABAU", "Vale do Anhangabaú (sessão ao ar livre)",
     "Vale do Anhangabaú - Centro, São Paulo - SP"),
    # CEUs (circuito Spcine gratuito) — endereços dos principais
    ("CEU ARICANDUVA", "CEU Aricanduva", "Rua Olga Fadel Abarca, s/n - Jd. Santa Terezinha, São Paulo - SP"),
    ("CEU BARRO BRANCO", "CEU Barro Branco", "Rua Numa Pompílio, s/n - Conj. Hab. Barro Branco II, Cidade Tiradentes, São Paulo - SP"),
    ("CEU BUTANTA", "CEU Butantã", "Avenida Engenheiro Heitor Antônio Eiras García, 1870 - Jd. Esmeralda, São Paulo - SP"),
    ("CEU CAMINHO DO MAR", "CEU Caminho do Mar", "Avenida Engenheiro Armando de Arruda Pereira, 5241 - Jabaquara, São Paulo - SP"),
    ("CEU CARRAO", "CEU Carrão", "Rua Monte Serrat, 380 - Tatuapé, São Paulo - SP"),
    ("CEU FEITICO DA VILA", "CEU Feitiço da Vila", "Rua Feitiço da Vila, 399 - Capão Redondo, São Paulo - SP"),
    ("CEU FREGUESIA DO O", "CEU Freguesia do Ó", "Rua Crespo de Carvalho, 71 - Freguesia do Ó, São Paulo - SP"),
    ("CEU JACANA", "CEU Jaçanã", "Rua Antônio César Neto, 105 - Jaçanã, São Paulo - SP"),
    ("CEU JAMBEIRO", "CEU Jambeiro", "Avenida José Pinheiro Borges, 60 - Guaianases, São Paulo - SP"),
    ("CEU MENINOS", "CEU Meninos", "Rua Barbinos, 111 - São João Clímaco, São Paulo - SP"),
    ("CEU PARQUE DO CARMO", "CEU Parque do Carmo", "Rua Gaspar da Silva, 240 - Parque do Carmo, São Paulo - SP"),
    ("CEU PARQUE NOVO MUNDO", "CEU Parque Novo Mundo", "Avenida Ernesto Augusto Lopes, 100 - Parque Vila Maria, São Paulo - SP"),
    ("CEU PARQUE VEREDAS", "CEU Parque Veredas", "Rua Daniel Muller, 347 - Itaim Paulista, São Paulo - SP"),
    ("CEU PAZ", "CEU Paz", "Rua Daniel Cerri, 1549 - Jd. Paraná, São Paulo - SP"),
    ("CEU PERUS", "CEU Perus", "Rua Bernardo José de Lorena, s/n - Perus, São Paulo - SP"),
    ("CEU PINHEIRINHO", "CEU Pinheirinho", "Rua Camillo Zanotti, 92 - Conjunto City Jaraguá, São Paulo - SP"),
    ("CEU QUINTA DO SOL", "CEU Quinta do Sol", "Avenida Luís Imparato, 564 - Parque Cisper, São Paulo - SP"),
    ("CEU SAO MATEUS", "CEU São Mateus", "Rua Curumatim, 201 - Parque Boa Esperança, São Paulo - SP"),
    ("CEU SAO RAFAEL", "CEU São Rafael", "Rua Cinira Polônio, 100 - Jd. da Conquista, São Paulo - SP"),
    ("CEU TRES LAGOS", "CEU Três Lagos", "Estrada do Barro Branco, 205 - Três Lagos, São Paulo - SP"),
    ("CEU TIQUATIRA", "CEU Tiquatira", "Avenida Condessa Elisabeth de Robiano, 5605 - Penha, São Paulo - SP"),
    ("CEU UIRAPURU", "CEU Uirapuru", "Rua Nazir Miguel, 849 - Jd. Educandário, São Paulo - SP"),
    ("CEU VILA ATLANTICA", "CEU Vila Atlântica", "Rua Coronel José Venâncio Dias, 840 - Vila Atlântica, São Paulo - SP"),
    ("CEU VILA DO SOL", "CEU Vila do Sol", "Avenida dos Funcionários Públicos, 369 - Jd. Vila do Sol, São Paulo - SP"),
    ("CEU SAO MIGUEL", "CEU São Miguel - Luiz Melodia", "Rua José Ferreira Crespo, 475 - Jardim São Vicente, São Paulo - SP"),
    ("CEU SAO PEDRO", "CEU São Pedro", "Rua Professora Lucila Cerqueira, 194 - Jardim São Pedro, São Paulo - SP"),
    ("CEU TAIPAS", "CEU Taipas", "Rua João Amado Coutinho, 240 - Conj. Res. Elisio Teixeira Leite, São Paulo - SP"),
    ("CEU TREMEMBE", "CEU Tremembé", "Rua Adauto Bezerra Delgado, 140 - Parque Casa de Pedra, São Paulo - SP"),
    ("CEU VILA ALPINA", "CEU Vila Alpina", "Rua João Pedro Lecór, 141 - Jardim Avelino, São Paulo - SP"),
    ("CINEMATECA", "Cinemateca Brasileira", "Largo Senador Raul Cardoso, 207 - Vila Clementino, São Paulo - SP"),
    ("INSTITUTO MOREIRA SALLES", "IMS Paulista (Instituto Moreira Salles)", "Avenida Paulista, 2424 - Bela Vista, São Paulo - SP"),
    ("MUSEU DA LINGUA PORTUGUESA", "Museu da Língua Portuguesa", "Praça da Luz, s/n - Centro, São Paulo - SP"),
    ("SALA SAO PAULO", "Sala São Paulo", "Praça Júlio Prestes, 16 - Campos Elíseos, São Paulo - SP"),
    ("BIBLIO. ROBERTO SANTOS", "Biblioteca Roberto Santos", "Rua Cisplatina, 505 - Ipiranga, São Paulo - SP"),
    ("CFC CIDADE TIRADENTES", "Centro de Formação Cultural Cidade Tiradentes", "Rua Inácio Monteiro, 6900 - Cidade Tiradentes, São Paulo - SP"),
]


def norm(s: str) -> str:
    """Maiúsculas, sem acento, espaços colapsados — para casar nomes de sala."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().upper()


def match_venue(sala: str):
    """Retorna (nome_cinema, endereco) para uma pro_sala, ou (None, None)."""
    n = norm(sala)
    best = None
    for prefix, nome, end in VENUES:
        if n.startswith(prefix) or prefix in n:
            if best is None or len(prefix) > len(best[0]):
                best = (prefix, nome, end)
    if best:
        return best[1], best[2]
    return None, None


def clean_html(s):
    """Remove tags HTML e decodifica entidades (para sinopse, bio etc.)."""
    if not s:
        return ""
    s = html.unescape(s)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</p>\s*<p>", "\n\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"[ \t]+", " ", s).replace("\r\n", "\n").strip()


def fetch_json(url: str):
    last_err = None
    for attempt in range(RETRY):
        try:
            req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Falha ao buscar {url}: {last_err}")


def main():
    ap = argparse.ArgumentParser(description="Scraper da programação da Mostra SP")
    ap.add_argument("--edition", type=int, default=EDITION, help="número da edição (ex.: 49, 50)")
    ap.add_argument("--locale", default=LOCALE, choices=["pt", "en"])
    ap.add_argument("--refresh", action="store_true", help="ignora cache raw/ e baixa tudo de novo")
    ap.add_argument("--workers", type=int, default=WORKERS)
    args = ap.parse_args()

    ed, loc = args.edition, args.locale
    base_dir = Path(__file__).resolve().parent / "data"
    raw_dir = base_dir / "raw" / f"ed{ed}"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # 1) Lista de filmes -----------------------------------------------------
    print(f">> Buscando lista de filmes da {ed}ª Mostra ({loc})...")
    listing = fetch_json(f"{API_BASE}/{loc}/filmes/{ed}")
    if not listing.get("status") or not listing.get("data"):
        sys.exit(f"API não retornou filmes para a edição {ed}. "
                 "A programação pode não ter sido publicada ainda.")
    films_list = listing["data"]
    print(f"   {len(films_list)} filmes encontrados.")

    # 2) Detalhe de cada filme (paralelo, com cache) -------------------------
    def get_detail(item):
        slug = item["url"]
        cache = raw_dir / f"filme_{slug}.json"
        if cache.exists() and not args.refresh:
            return slug, json.loads(cache.read_text(encoding="utf-8"))
        d = fetch_json(f"{API_BASE}/{loc}/filme/{ed}/{slug}")
        cache.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        time.sleep(0.15)  # educação com o servidor
        return slug, d

    details = {}
    errors = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(get_detail, it): it["url"] for it in films_list}
        done = 0
        for fut in as_completed(futures):
            slug = futures[fut]
            try:
                s, d = fut.result()
                details[s] = d
            except Exception as e:  # noqa: BLE001
                errors.append((slug, str(e)))
            done += 1
            if done % 40 == 0 or done == len(futures):
                print(f"   detalhes: {done}/{len(futures)}")
    if errors:
        print(f"   !! {len(errors)} filmes falharam: {[e[0] for e in errors][:10]}")

    # 3) Normalização --------------------------------------------------------
    filmes, sessoes = [], []
    cinemas_map = {}       # nome_cinema -> dict
    salas_sem_match = set()
    diretores_map = {}     # id -> dict

    FILM_FIELDS = [
        "titulo_original", "genero", "pais", "ano", "duracao", "cor", "bitola",
        "classificacao", "secao", "secao_sec", "tags", "roteiro", "fotografia",
        "montagem", "som", "desenho_de_som", "design_de_producao", "elenco",
        "produtor", "producao", "pesquisa", "musica", "narracao", "vozes",
        "depoimentos", "codirecao", "world_sales", "distribuicao", "site",
        "trailer", "trailer2", "link_compra", "link_exibicao", "esgotado",
    ]

    for item in films_list:
        slug = item["url"]
        resp = details.get(slug)
        data = (resp or {}).get("data") or {}
        f = {
            "id": data.get("id") or item.get("id"),
            "slug": slug,
            "url_pagina": f"https://mostra.org/filmes/{ed}/{slug}"
                          if loc == "pt" else f"https://mostra.org/en/filmes/{ed}/{slug}",
            "titulo": data.get("titulo") or item.get("titulo"),
            "sinopse": clean_html(data.get("sinopse")),
        }
        for k in FILM_FIELDS:
            f[k] = data.get(k) or item.get(k) or ""
        dirs = data.get("diretores") or []
        f["diretores"] = ", ".join(d.get("nome", "") for d in dirs)
        f["diretores_detalhe"] = [
            {"id": d.get("id"), "nome": d.get("nome"),
             "bio": clean_html(d.get("bio")), "slug": d.get("url")} for d in dirs
        ]
        for d in f["diretores_detalhe"]:
            if d["id"]:
                diretores_map[d["id"]] = d
        img = item.get("film_image_large") or ""
        f["imagem"] = f"{STATIC_BASE}/{img.lstrip('/')}" if img else ""
        f["n_sessoes"] = len(data.get("programacao") or [])
        filmes.append(f)

        for s in data.get("programacao") or []:
            sala = s.get("pro_sala", "")
            cinema, endereco = match_venue(sala)
            if cinema is None:
                salas_sem_match.add(sala)
                cinema = sala.title()
                endereco = ""
            if cinema not in cinemas_map:
                cinemas_map[cinema] = {"cinema": cinema, "endereco": endereco, "salas": set()}
            cinemas_map[cinema]["salas"].add(sala)
            sessoes.append({
                "sessao_id": s.get("pro_id"),
                "filme_id": f["id"],
                "filme_slug": slug,
                "titulo": f["titulo"],
                "titulo_original": f["titulo_original"],
                "data": s.get("pro_data"),
                "hora": (s.get("pro_hora") or "")[:5],
                "sala": sala,
                "cinema": cinema,
                "endereco_cinema": endereco,
                "idioma": s.get("pro_idioma", ""),
                "legendas": s.get("pro_legendas", ""),
                "secao": f["secao"],
                "diretores": f["diretores"],
                "duracao": f["duracao"],
                "pais": f["pais"],
                "ano": f["ano"],
                "classificacao": f["classificacao"],
                "link_compra": f["link_compra"],
            })

    sessoes.sort(key=lambda s: (s["data"] or "", s["hora"] or "", s["cinema"]))
    cinemas = [{**c, "salas": sorted(c["salas"])} for c in
               sorted(cinemas_map.values(), key=lambda c: c["cinema"])]

    if salas_sem_match:
        print("\n!! Salas sem endereço na tabela VENUES (adicione-as no script):")
        for s in sorted(salas_sem_match):
            print("   -", s)

    # 4) Gravação ------------------------------------------------------------
    def dump(name, obj):
        p = base_dir / name
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"   -> {p.relative_to(base_dir.parent)}")

    print("\n>> Gravando saídas...")
    dump(f"mostra_{ed}_filmes.json", filmes)
    dump(f"mostra_{ed}_sessoes.json", sessoes)
    dump(f"mostra_{ed}_cinemas.json", cinemas)

    # CSVs
    for name, rows in [(f"mostra_{ed}_sessoes.csv", sessoes),
                       (f"mostra_{ed}_filmes.csv",
                        [{k: v for k, v in f.items() if k != "diretores_detalhe"} for f in filmes])]:
        p = base_dir / name
        with p.open("w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"   -> data/{name}")

    # SQLite
    dbp = base_dir / f"mostra_{ed}.db"
    if dbp.exists():
        dbp.unlink()
    con = sqlite3.connect(dbp)
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE filmes (
      id TEXT PRIMARY KEY, slug TEXT, url_pagina TEXT, titulo TEXT,
      titulo_original TEXT, sinopse TEXT, diretores TEXT, genero TEXT,
      pais TEXT, ano TEXT, duracao TEXT, cor TEXT, bitola TEXT,
      classificacao TEXT, secao TEXT, secao_sec TEXT, tags TEXT,
      roteiro TEXT, fotografia TEXT, montagem TEXT, som TEXT,
      desenho_de_som TEXT, design_de_producao TEXT, elenco TEXT,
      produtor TEXT, producao TEXT, pesquisa TEXT, musica TEXT,
      narracao TEXT, vozes TEXT, depoimentos TEXT, codirecao TEXT,
      world_sales TEXT, distribuicao TEXT, site TEXT, trailer TEXT,
      trailer2 TEXT, link_compra TEXT, link_exibicao TEXT,
      esgotado TEXT, imagem TEXT, n_sessoes INTEGER
    );
    CREATE TABLE diretores (
      id TEXT PRIMARY KEY, nome TEXT, bio TEXT, slug TEXT
    );
    CREATE TABLE filme_diretor (
      filme_id TEXT, diretor_id TEXT,
      FOREIGN KEY(filme_id) REFERENCES filmes(id),
      FOREIGN KEY(diretor_id) REFERENCES diretores(id)
    );
    CREATE TABLE cinemas (
      cinema TEXT PRIMARY KEY, endereco TEXT, salas TEXT
    );
    CREATE TABLE sessoes (
      sessao_id TEXT PRIMARY KEY, filme_id TEXT, filme_slug TEXT,
      titulo TEXT, titulo_original TEXT, data TEXT, hora TEXT,
      sala TEXT, cinema TEXT, endereco_cinema TEXT, idioma TEXT,
      legendas TEXT, secao TEXT, diretores TEXT, duracao TEXT,
      pais TEXT, ano TEXT, classificacao TEXT, link_compra TEXT,
      FOREIGN KEY(filme_id) REFERENCES filmes(id),
      FOREIGN KEY(cinema) REFERENCES cinemas(cinema)
    );
    CREATE INDEX idx_sessoes_data ON sessoes(data, hora);
    CREATE INDEX idx_sessoes_cinema ON sessoes(cinema);
    CREATE INDEX idx_sessoes_filme ON sessoes(filme_id);
    """)
    film_cols = [c[1] for c in cur.execute("PRAGMA table_info(filmes)")]
    cur.executemany(
        f"INSERT OR REPLACE INTO filmes VALUES ({','.join('?' * len(film_cols))})",
        [tuple(f.get(c, "") for c in film_cols) for f in filmes])
    cur.executemany("INSERT OR REPLACE INTO diretores VALUES (?,?,?,?)",
                    [(d["id"], d["nome"], d["bio"], d["slug"]) for d in diretores_map.values()])
    fd_rows = [(f["id"], d["id"]) for f in filmes for d in f["diretores_detalhe"] if d["id"]]
    cur.executemany("INSERT INTO filme_diretor VALUES (?,?)", fd_rows)
    cur.executemany("INSERT OR REPLACE INTO cinemas VALUES (?,?,?)",
                    [(c["cinema"], c["endereco"], json.dumps(c["salas"], ensure_ascii=False))
                     for c in cinemas])
    sess_cols = [c[1] for c in cur.execute("PRAGMA table_info(sessoes)")]
    cur.executemany(
        f"INSERT OR REPLACE INTO sessoes VALUES ({','.join('?' * len(sess_cols))})",
        [tuple(s.get(c, "") for c in sess_cols) for s in sessoes])
    con.commit()
    con.close()
    print(f"   -> data/mostra_{ed}.db")

    print(f"\n== Resumo ==\nFilmes: {len(filmes)} | Sessões: {len(sessoes)} | "
          f"Cinemas: {len(cinemas)} | Diretores: {len(diretores_map)}")


if __name__ == "__main__":
    main()
