# -*- coding: utf-8 -*-
"""Programas: filmes que a Mostra exibe JUNTOS na mesma sessão (10/10/2026).

A API não traz "programa": cada curta tem suas próprias sessões, que só coincidem em
dia/hora/sala. Quem diz que passam juntos é o próprio texto da Mostra, na sinopse:
  "O filme "Fim" será exibido com "Nosso Século", "O Começo" e "Vida", dentro do
   Projeto Pelechian 2."
  "O curta "Rotação" faz parte do Displacement Film Fund e será exibido juntamente com …"
  "O filme "Tigre de Papel" será exibido junto com o curta "Sul de Teerã"."
Regra (pedido do Cainan: só o que o festival diz): o grupo vem dessas frases; o NOME vem
de "dentro do X" / "faz parte do X"; sem nome, os títulos ligados por " + " (o mais longo
primeiro). A grade confirma: os membros têm que passar no mesmo dia e hora — se não,
o grupo é descartado e o build avisa.

No app o programa vira UM card com o nome do programa; o filme mais longo é a "âncora"
(o id dele guarda ★ e agenda) e a ficha mostra a ficha de cada filme. As sessões dos
outros membros saem da grade (são a mesma sessão) e a duração da sessão vira a soma.
"""
import difflib
import re
import unicodedata

RE_JUNTO = re.compile(r"ser[áa] exibid[oa] (?:junto |juntamente )?com (.+?)(?:\.|$)", re.I)
RE_NOME = re.compile(r"(?:dentro d[oa]|faz(?: parte)? parte d[oa])\s+([A-ZÀ-Ü][^.,\"“”]+?)(?:\s+e\s+ser[áa]|[.,]|$)")
RE_ASPAS = re.compile(r"[\"“”]([^\"“”]+)[\"“”]")


def _norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\bpara\b", "pra", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _min(d):
    m = re.match(r"\s*(\d+)", str(d or ""))
    return int(m.group(1)) if m else 0


def detecta(filmes, sessoes, avisa=print):
    """Devolve lista de programas: {nome, ancora, membros:[ids], explicito:bool}."""
    por_norm = {_norm(f["titulo"]): f["id"] for f in filmes}
    nomes = list(por_norm)
    ligados, nome_de = {}, {}
    for f in filmes:
        sin = f.get("sinopse") or ""
        for frase in re.split(r"(?<=[.!?])\s+", sin):
            if not RE_JUNTO.search(frase):
                continue
            outros = []
            for t in RE_ASPAS.findall(frase):
                n = _norm(t)
                alvo = por_norm.get(n) or (difflib.get_close_matches(n, nomes, 1, 0.86) or [None])[0]
                if alvo:
                    alvo = por_norm.get(alvo, alvo) if alvo in por_norm else alvo
                    if alvo != f["id"]:
                        outros.append(alvo)
            if outros:
                ligados.setdefault(f["id"], set()).update(outros)
            m = RE_NOME.search(frase)
            if m:
                nome_de[f["id"]] = m.group(1).strip()
    # componentes conexas
    viz = {}
    for a, bs in ligados.items():
        for b in bs:
            viz.setdefault(a, set()).add(b)
            viz.setdefault(b, set()).add(a)
    vistos, grupos = set(), []
    for a in viz:
        if a in vistos:
            continue
        pilha, comp = [a], set()
        while pilha:
            x = pilha.pop()
            if x in comp:
                continue
            comp.add(x)
            pilha.extend(viz.get(x, ()))
        vistos |= comp
        grupos.append(comp)

    F = {f["id"]: f for f in filmes}
    horarios = {}
    for s in sessoes:
        horarios.setdefault(s["filme_id"], set()).add((s["data"], s["hora"]))
    progs = []
    for comp in grupos:
        membros = sorted(comp, key=lambda i: (-_min(F[i].get("duracao")), F[i]["titulo"]))
        ancora = membros[0]
        base = horarios.get(ancora, set())
        # tolera UMA sessão divergente por membro (erro de digitação no site: em 10/10/2026
        # "Nós" aparece às 12:00 em 27/10 e os outros 3 do Projeto Pelechian 1 às 16:00);
        # vale o horário da âncora e o build avisa. Mais que isso, o grupo é descartado.
        difs = {i: horarios.get(i, set()) ^ base for i in membros[1:]}
        if not base or any(len(horarios.get(i, set()) - base) > 1 or len(base - horarios.get(i, set())) > 1
                           for i in membros[1:]):
            avisa("AVISO programa descartado (horários não batem): "
                  + " + ".join(F[i]["titulo"] for i in membros))
            continue
        for i, d in difs.items():
            if d:
                avisa(f"AVISO programa: \"{F[i]['titulo']}\" diverge da âncora \"{F[ancora]['titulo']}\" "
                      f"em {sorted(d)} — usado o horário da âncora")
        nome = next((nome_de[i] for i in membros if i in nome_de), None)
        progs.append({"nome": nome or " + ".join(F[i]["titulo"] for i in membros),
                      "ancora": ancora, "membros": membros, "explicito": bool(nome)})
    return progs


def _uniao(vals, sep=", "):
    out = []
    for v in vals:
        for x in (v or "").split(","):
            x = x.strip()
            if x and x not in out:
                out.append(x)
    return sep.join(out)


def _limpa_sinopse(s):
    """Tira a frase "será exibido com…" (vira redundante dentro do programa)."""
    frases = re.split(r"(?<=[.!?])\s+", s or "")
    return " ".join(x for x in frases if not RE_JUNTO.search(x)).strip()


def aplica(filmes_slim, sessoes, progs):
    """Funde cada programa num registro (o da âncora) e tira as sessões repetidas."""
    F = {f["id"]: f for f in filmes_slim}
    sai_f, alias_s = set(), {}
    for p in progs:
        anc = F[p["ancora"]]
        ms = [F[i] for i in p["membros"]]
        total = sum(_min(m.get("duracao")) for m in ms)
        membros = []
        for m in ms:
            mm = dict(m)
            mm["sinopse"] = _limpa_sinopse(m.get("sinopse"))
            membros.append(mm)
        anos = sorted({str(m.get("ano")) for m in ms if m.get("ano")})
        festivais = []
        for m in ms:
            for x in m.get("festivais") or []:
                if x not in festivais:
                    festivais.append(x)
        prem = [m for m in ms if m.get("premiado")]
        novo = dict(anc)
        novo.update({
            "titulo": p["nome"], "titulo_original": "", "sinopse": "",
            "diretores": _uniao(m.get("diretores") for m in ms),
            "elenco": _uniao(m.get("elenco") for m in ms),
            "pais": _uniao(m.get("pais") for m in ms),
            "ano": anos[0] if len(anos) == 1 else (f"{anos[0]}–{anos[-1]}" if anos else ""),
            "duracao": f"{total} min.",
            "imagem": anc.get("imagem") or next((m.get("imagem") for m in ms if m.get("imagem")), ""),
            "trailer": "", "festivais": festivais, "premiado": bool(prem),
            "premio_txt": " ".join(m.get("premio_txt") or "" for m in prem).strip(),
            "premio_fest": prem[0].get("premio_fest") if prem else None,
            # nota do Letterboxd no card só se a âncora é longa (senão seria de um curta só)
            "lb_nota": anc.get("lb_nota") if _min(anc.get("duracao")) >= 60 else None,
            "lb_votos": anc.get("lb_votos") if _min(anc.get("duracao")) >= 60 else None,
            "lb_hist": anc.get("lb_hist") if _min(anc.get("duracao")) >= 60 else None,
            "lb_url": anc.get("lb_url") if _min(anc.get("duracao")) >= 60 else None,
            "programa": {"nome": p["nome"], "explicito": p["explicito"], "filmes": membros,
                         "membros_ids": p["membros"]},
        })
        F[p["ancora"]].clear()
        F[p["ancora"]].update(novo)
        sai_f.update(p["membros"][1:])
    # sessões: a da âncora vira a sessão do programa; as dos outros membros saem
    anc_de = {i: p for p in progs for i in p["membros"]}
    chave_anc, dia_cin = {}, {}
    for s in sessoes:
        p = anc_de.get(s["filme_id"])
        if p and s["filme_id"] == p["ancora"]:
            s["titulo"] = p["nome"]
            s["duracao"] = F[p["ancora"]]["duracao"]
            chave_anc[(p["ancora"], s["data"], s["hora"])] = s["sessao_id"]
            dia_cin[(p["ancora"], s["data"], s["cinema"])] = s["sessao_id"]
    novas = []
    for s in sessoes:
        p = anc_de.get(s["filme_id"])
        if p and s["filme_id"] != p["ancora"]:
            alvo = (chave_anc.get((p["ancora"], s["data"], s["hora"]))
                    or dia_cin.get((p["ancora"], s["data"], s["cinema"])))
            if alvo:
                alias_s[s["sessao_id"]] = alvo
            continue
        novas.append(s)
    for p in progs:   # quem já tinha ★ ou agenda num curta não perde nada (o app migra)
        F[p["ancora"]]["programa"]["alias_s"] = {k: v for k, v in alias_s.items()
                                                 if v in {x for (a, _, _), x in chave_anc.items() if a == p["ancora"]}}
    filmes_out = [f for f in filmes_slim if f["id"] not in sai_f]
    return filmes_out, novas
