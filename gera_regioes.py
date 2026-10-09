# -*- coding: utf-8 -*-
"""Gera o literal JS das regioes a partir dos bairros reais dos enderecos."""
import json, collections, re
EDICAO=50
S=json.load(open(f'mostra-scraper-completo/mostra-scraper/data/mostra_{EDICAO}_sessoes.json',encoding='utf-8'))
end={}; n=collections.Counter()
for s in S:
    end.setdefault(s['cinema'], s.get('endereco_cinema','') or '')
    n[s['cinema']]+=1

# bairro = trecho entre o " - " e ", Sao Paulo"
def bairro(e):
    m=re.search(r'-\s*([^,]+),\s*S[aã]o Paulo', e)
    return m.group(1).strip() if m else ''

# 50ª Mostra (09/10/2026): cada cinema pelo bairro do endereço. Cinema que não estiver
# aqui faz o script PARAR (antes ia calado para o grupo dos CEUs).
REG=[
 ("augusta","Augusta / Consolação",
  ["Espaço Petrobras de Cinema (Espaço Itaú Augusta)","CineSesc","Sato Cinema",
   "Cine Satyros Bijou","Teatro Cultura Artística","Cine Belas Artes",
   "Cinesystem Belas Artes Frei Caneca"]),
 ("paulista","Paulista / Bela Vista",
  ["Reserva Cultural","IMS Paulista (Instituto Moreira Salles)","Itaú Cultural",
   "Sesc Paulista","Teatro Sérgio Cardoso"]),
 ("oeste","Pinheiros / Jardins / Butantã",
  ["Cinesala","Cine Tutu","MIS - Museu da Imagem e do Som",
   "Sala Petrobras (Solar Fábio Prado)","CINUSP Paulo Emílio"]),
 ("vilamariana","Vila Mariana / Paraíso",
  ["Cinemateca Brasileira","Centro Cultural São Paulo (CCSP)","Cine Segall - Museu Lasar Segall"]),
 ("centro","Centro",
  ["Multiplex PlayArte Marabá","Centro Cultural Olido","Museu da Língua Portuguesa","Sala São Paulo"]),
 ("ipiranga","Ipiranga",["Biblioteca Roberto Santos"]),
]
REG=[(r,rot,[c for c in cs if c in end]) for r,rot,cs in REG]
REG=[x for x in REG if x[2]]                    # região sem sessão nesta edição sai
usados={c for _,_,cs in REG for c in cs}
ceus=sorted(c for c in end if c not in usados and (c.startswith("CEU ") or "Cidade Tiradentes" in c))
REG.append(("ceus","CEUs",ceus))

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
