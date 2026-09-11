# -*- coding: utf-8 -*-
"""Gera o literal JS das regioes a partir dos bairros reais dos enderecos."""
import json, collections, re
S=json.load(open('mostra-scraper-completo/mostra-scraper/data/mostra_49_sessoes.json',encoding='utf-8'))
end={}; n=collections.Counter()
for s in S:
    end.setdefault(s['cinema'], s.get('endereco_cinema','') or '')
    n[s['cinema']]+=1

# bairro = trecho entre o " - " e ", Sao Paulo"
def bairro(e):
    m=re.search(r'-\s*([^,]+),\s*S[aã]o Paulo', e)
    return m.group(1).strip() if m else ''

REG=[
 ("augusta","Augusta / Consolação",
  ["Espaço Petrobras de Cinema (Espaço Itaú Augusta)","CineSesc","Sato Cinema",
   "Cine Satyros Bijou","Teatro Cultura Artística"]),
 ("vilamariana","Vila Mariana / Paraíso",
  ["Cinemateca Brasileira","Centro Cultural São Paulo (CCSP)","Cine Segall - Museu Lasar Segall"]),
 ("centro","Centro",
  ["Multiplex PlayArte Marabá","Centro Cultural Olido","Museu da Língua Portuguesa","Sala São Paulo"]),
 ("paulista","Paulista",["Reserva Cultural","IMS Paulista (Instituto Moreira Salles)"]),
 ("pinheiros","Pinheiros",["Cinesala"]),
 ("ipiranga","Ipiranga",["Biblioteca Roberto Santos"]),
]
usados={c for _,_,cs in REG for c in cs}
resto=sorted([c for c in end if c not in usados])
REG.append(("ceus","CEUs",resto))

falta=[c for c in end if c not in {c for _,_,cs in REG for c in cs}]
assert not falta, falta

linhas=[]
for rid,rot,cs in REG:
    tot=sum(n[c] for c in cs)
    itens=",".join('{n:%s,b:%s}'%(json.dumps(c,ensure_ascii=False),json.dumps(bairro(end[c]),ensure_ascii=False)) for c in cs)
    linhas.append('  {id:%s,rot:%s,ses:%d,cinemas:[%s]}'%(json.dumps(rid),json.dumps(rot,ensure_ascii=False),tot,itens))
js="const REGIOES=[\n"+",\n".join(linhas)+"\n];\n"
open('regioes.js','w',encoding='utf-8').write(js)
print(js[:400])
for rid,rot,cs in REG: print(f"{sum(n[c] for c in cs):>5} sessoes | {len(cs):>2} cinemas | {rot}".encode('ascii','replace').decode())
