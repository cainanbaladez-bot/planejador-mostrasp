# -*- coding: utf-8 -*-
"""Mapa de países da aba 🌍 Mapa (09/10/2026).

Lê o contorno dos países do world-atlas (Natural Earth 1:110m, `mapa/countries-110m.json`,
baixado de cdn.jsdelivr.net/npm/world-atlas@2.0.2 — TopoJSON) e devolve, já projetado em
Equal Earth (área proporcional: a Europa não fica inflada), o desenho SVG de cada país.
Vai embutido no HTML pelo build, então o app continua abrindo offline.

O "pais" de cada filme da Mostra vem como "Brasil, Portugal" (coprodução = vírgula). O
dicionário PAISES liga cada nome da Mostra a um país do mapa:
  · território pequeno demais para 1:110m (Singapura, Hong Kong) vira um PONTO;
  · país que não existe mais (União Soviética, Alemanha Ocidental) não tem desenho e
    aparece só na lista, marcado como histórico;
  · nome que não estiver aqui não some: o build avisa e ele entra na lista sem mapa.
"""
import json
import math
from pathlib import Path

ARQ = Path(__file__).parent / "mapa" / "countries-110m.json"

# nome na Mostra → (nome no world-atlas | ponto (lon, lat) | None, região)
EU, LAT, NAM, AFR, ASI, MOR, OCE = ("Europa", "América Latina", "América do Norte", "África",
                                    "Ásia", "Oriente Médio", "Oceania")
PAISES = {
    "Brasil": ("Brazil", LAT), "França": ("France", EU), "EUA": ("United States of America", NAM),
    "Alemanha": ("Germany", EU), "Portugal": ("Portugal", EU), "Itália": ("Italy", EU),
    "Bélgica": ("Belgium", EU), "Reino Unido": ("United Kingdom", EU), "Espanha": ("Spain", EU),
    "Dinamarca": ("Denmark", EU), "México": ("Mexico", LAT), "Chile": ("Chile", LAT),
    "Luxemburgo": ("Luxembourg", EU), "Argentina": ("Argentina", LAT), "Áustria": ("Austria", EU),
    "Suécia": ("Sweden", EU), "Países Baixos": ("Netherlands", EU), "Holanda": ("Netherlands", EU),
    "Catar": ("Qatar", MOR), "Armênia": ("Armenia", ASI), "Suíça": ("Switzerland", EU),
    "Canadá": ("Canada", NAM), "Canadá (Québec)": ("Canada", NAM), "Japão": ("Japan", ASI),
    "Irã": ("Iran", MOR), "Arábia Saudita": ("Saudi Arabia", MOR), "Polônia": ("Poland", EU),
    "Coreia do Sul": ("South Korea", ASI), "Irlanda": ("Ireland", EU), "Eslovênia": ("Slovenia", EU),
    "Bulgária": ("Bulgaria", EU), "Singapura": ((103.82, 1.35), ASI), "Noruega": ("Norway", EU),
    "China": ("China", ASI), "Índia": ("India", ASI), "União Soviética": (None, EU),
    "Colômbia": ("Colombia", LAT), "Cuba": ("Cuba", LAT), "Grécia": ("Greece", EU),
    "Palestina": ("Palestine", MOR), "Turquia": ("Turkey", MOR), "Sérvia": ("Serbia", EU),
    "Lituânia": ("Lithuania", EU), "República Tcheca": ("Czechia", EU), "Tchéquia": ("Czechia", EU),
    "Letônia": ("Latvia", EU), "Macedônia do Norte": ("Macedonia", EU), "Taiwan": ("Taiwan", ASI),
    "Indonésia": ("Indonesia", ASI), "Romênia": ("Romania", EU), "Uruguai": ("Uruguay", LAT),
    "Argélia": ("Algeria", AFR), "Filipinas": ("Philippines", ASI), "Camboja": ("Cambodia", ASI),
    "Senegal": ("Senegal", AFR), "Montenegro": ("Montenegro", EU), "Croácia": ("Croatia", EU),
    "Guatemala": ("Guatemala", LAT), "Ucrânia": ("Ukraine", EU), "Líbano": ("Lebanon", MOR),
    "Peru": ("Peru", LAT), "Rússia": ("Russia", EU), "Alemanha Ocidental": (None, EU),
    "Estônia": ("Estonia", EU), "Camarões": ("Cameroon", AFR), "Benim": ("Benin", AFR),
    "Vietnã": ("Vietnam", ASI), "Tailândia": ("Thailand", ASI), "Venezuela": ("Venezuela", LAT),
    "Síria": ("Syria", MOR), "Malásia": ("Malaysia", ASI), "Mauritânia": ("Mauritania", AFR),
    "Nigéria": ("Nigeria", AFR), "Finlândia": ("Finland", EU), "Eslováquia": ("Slovakia", EU),
    "Guiné-Bissau": ("Guinea-Bissau", AFR), "Egito": ("Egypt", AFR), "Nepal": ("Nepal", ASI),
    "Bangladesh": ("Bangladesh", ASI), "Quirguistão": ("Kyrgyzstan", ASI), "Angola": ("Angola", AFR),
    "Hungria": ("Hungary", EU), "Bósnia e Herzegovina": ("Bosnia and Herz.", EU),
    "Chipre": ("Cyprus", EU), "Costa Rica": ("Costa Rica", LAT), "Panamá": ("Panama", LAT),
    "Israel": ("Israel", MOR), "Iêmen": ("Yemen", MOR), "Jordânia": ("Jordan", MOR),
    "Geórgia": ("Georgia", ASI), "Paraguai": ("Paraguay", LAT), "Cazaquistão": ("Kazakhstan", ASI),
    "Somália": ("Somalia", AFR), "África do Sul": ("South Africa", AFR), "Kosovo": ("Kosovo", EU),
    "Albânia": ("Albania", EU), "Austrália": ("Australia", OCE), "Hong Kong": ((114.17, 22.32), ASI),
    "Nova Zelândia": ("New Zealand", OCE), "Marrocos": ("Morocco", AFR), "Tunísia": ("Tunisia", AFR),
    "Bolívia": ("Bolivia", LAT), "Equador": ("Ecuador", LAT), "Islândia": ("Iceland", EU),
    "Iraque": ("Iraq", MOR), "Afeganistão": ("Afghanistan", ASI), "Paquistão": ("Pakistan", ASI),
    "Mongólia": ("Mongolia", ASI), "Quênia": ("Kenya", AFR), "Etiópia": ("Ethiopia", AFR),
    "Gana": ("Ghana", AFR), "Moçambique": ("Mozambique", AFR), "Bielorrússia": ("Belarus", EU),
    "Moldávia": ("Moldova", EU), "Azerbaijão": ("Azerbaijan", ASI), "Uzbequistão": ("Uzbekistan", ASI),
    "Tajiquistão": ("Tajikistan", ASI), "Mali": ("Mali", AFR), "Burkina Faso": ("Burkina Faso", AFR),
    "Costa do Marfim": ("Côte d'Ivoire", AFR), "República Dominicana": ("Dominican Rep.", LAT),
    "Haiti": ("Haiti", LAT), "Porto Rico": ("Puerto Rico", LAT), "Emirados Árabes Unidos": ("United Arab Emirates", MOR),
}
HISTORICO = {"União Soviética": "existiu de 1922 a 1991", "Alemanha Ocidental": "existiu de 1949 a 1990"}


def paises_do_filme(txt):
    """'Brasil, Portugal' → ['Brasil', 'Portugal'] (só vírgula: 'Bósnia e Herzegovina' é um país)."""
    return [p.strip() for p in (txt or "").split(",") if p.strip()]


# ── Equal Earth (Šavrič, Patterson & Jenny, 2018) ──
A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
M = math.sqrt(3) / 2
ESCALA = 165


def projeta(lon, lat):
    lam, phi = math.radians(lon), math.radians(lat)
    th = math.asin(M * math.sin(phi))
    t2 = th * th
    t6 = t2 ** 3
    x = 2 * math.sqrt(3) * lam * math.cos(th) / (3 * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2)))
    y = th * (A1 + A2 * t2 + t6 * (A3 + A4 * t2))
    return x * ESCALA, -y * ESCALA


def dados_mapa(filmes):
    topo = json.loads(ARQ.read_text(encoding="utf-8"))
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    arcos = []
    for arco in topo["arcs"]:                      # TopoJSON quantizado e em deltas
        x = y = 0
        pts = []
        for dx, dy in arco:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcos.append(pts)

    def anel(idx):
        pts = []
        for i in idx:
            a = arcos[i] if i >= 0 else arcos[~i][::-1]
            pts.extend(a if not pts else a[1:])
        return pts

    def lados(pts):
        """Fiji e o leste da Rússia cruzam os 180° neste arquivo: o anel ligaria 179° a -179°
        e riscaria o mapa de ponta a ponta. Divide em dois anéis, um de cada lado."""
        if not any(abs(pts[i][0] - pts[i - 1][0]) > 180 for i in range(1, len(pts))):
            return [pts]
        leste = [(min(lon if lon > 0 else lon + 360, 180), lat) for lon, lat in pts]
        oeste = [(max(lon if lon < 0 else lon - 360, -180), lat) for lon, lat in pts]
        return [leste, oeste]

    xs, ys, desenhos, centros = [], [], {}, {}
    for g in topo["objects"]["countries"]["geometries"]:
        nome = g["properties"]["name"]
        if nome in ("Antarctica", "Fr. S. Antarctic Lands"):
            continue
        poligonos = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"]
        partes, maior = [], (0, None)              # maior anel = de onde saem os pôsteres
        for poli in poligonos:
            for pts_anel in (a for idx in poli for a in lados(anel(idx))):
                ant, seg = None, []
                for lon, lat in pts_anel:
                    px, py = projeta(lon, lat)
                    xs.append(px)
                    ys.append(py)
                    p = (round(px, 1), round(py, 1))
                    if p != ant:
                        seg.append(f"{p[0]:g},{p[1]:g}")
                        ant = p
                if len(seg) > 2:
                    partes.append("M" + "L".join(seg) + "Z")
                    qs = [projeta(lo, la) for lo, la in pts_anel]
                    area = abs(sum(qs[i - 1][0] * q[1] - q[0] * qs[i - 1][1] for i, q in enumerate(qs))) / 2
                    if area > maior[0]:
                        bx, by = [q[0] for q in qs], [q[1] for q in qs]
                        maior = (area, [round((min(bx) + max(bx)) / 2, 1), round((min(by) + max(by)) / 2, 1)])
        desenhos[nome] = "".join(partes)
        centros[nome] = maior[1]

    x0, y0 = math.floor(min(xs)), math.floor(min(ys))
    vb = [x0, y0, math.ceil(max(xs)) - x0, math.ceil(max(ys)) - y0]

    usados, sem_mapa, paises = set(), [], {}
    for f in filmes:
        for p in paises_do_filme(f.get("pais")):
            usados.add(p)
    for p in sorted(usados):
        alvo, regiao = PAISES.get(p, (None, ""))
        reg = {"r": regiao}
        if isinstance(alvo, str):
            reg["m"] = alvo
        elif isinstance(alvo, tuple):
            px, py = projeta(*alvo)
            reg["p"] = [round(px, 1), round(py, 1)]
        if p in HISTORICO:
            reg["h"] = HISTORICO[p]
        if p not in PAISES:
            sem_mapa.append(p)
        paises[p] = reg
    return {"vb": vb, "d": desenhos, "c": centros, "paises": paises}, sem_mapa


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    F = json.loads((Path(__file__).parent / "mostra-scraper-completo" / "mostra-scraper" / "data" /
                    "mostra_50_filmes.json").read_text(encoding="utf-8"))
    d, falta = dados_mapa(F)
    print(f"viewBox {d['vb']} · {len(d['d'])} países desenhados · {len(d['paises'])} citados · "
          f"{len(json.dumps(d, ensure_ascii=False)) / 1024:.0f} KB")
    print("sem mapa:", falta or "nenhum")
    print("só ponto:", [p for p, r in d["paises"].items() if "p" in r])
    print("históricos:", [p for p, r in d["paises"].items() if "h" in r])
    print("nome do mapa que não existe:", [p for p, r in d["paises"].items() if "m" in r and r["m"] not in d["d"]])
