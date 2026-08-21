# Mostra SP — Scraper da Programação

Banco de dados completo da programação da Mostra Internacional de Cinema em São Paulo,
raspado da API pública que alimenta https://mostra.org/programacao/.

## O que tem aqui

```
mostra-scraper/
├── scrape_mostra.py          # script reutilizável (só depende de Python 3, sem libs externas)
├── README.md
└── data/
    ├── mostra_49.db          # SQLite: filmes, sessoes, cinemas, diretores, filme_diretor
    ├── mostra_49_filmes.json # 380 filmes com sinopse, direção+bio, elenco, ficha técnica completa
    ├── mostra_49_sessoes.json# 1309 sessões: data, hora, sala, cinema, endereço, idioma, legendas
    ├── mostra_49_cinemas.json# 43 cinemas com endereço e lista de salas
    ├── mostra_49_filmes.csv  # mesmas tabelas em CSV (abre no Excel)
    ├── mostra_49_sessoes.csv
    └── raw/ed49/             # cache das respostas brutas da API (1 JSON por filme)
```

## Campos por filme
título, título original, slug, url da página, sinopse (texto limpo), seção, gênero,
país, ano, duração, cor, bitola, classificação, tags, diretores (+ bio e slug de cada um),
roteiro, fotografia, montagem, som, desenho de som, design de produção, elenco, produtor,
produção, música, world sales, distribuição, site, trailer, link de compra, imagem, nº de sessões.

## Campos por sessão
id da sessão, filme (id/slug/título), data, hora, sala (como aparece no site),
cinema normalizado, endereço do cinema, idioma, legendas, seção, diretores,
duração, país, ano, classificação, link de compra.

## Como reusar quando a 50ª Mostra sair

```bash
python3 scrape_mostra.py --edition 50
```

- A API segue o padrão `https://api.mostra.org/pt/filmes/{edição}` e
  `https://api.mostra.org/pt/filme/{edição}/{slug}`.
- O script cacheia as respostas em `data/raw/ed{N}/`; use `--refresh` para baixar tudo de novo
  (útil durante o festival, quando sessões extras são adicionadas).
- Se aparecer alguma sala nova que não está na tabela `VENUES` do script, ele lista no final
  ("Salas sem endereço") — basta adicionar o prefixo + endereço na tabela e rodar de novo
  (não precisa rebaixar nada, o cache resolve).
- `--locale en` gera a versão em inglês dos textos.

## Consultas de exemplo (SQLite)

```sql
-- sessões de um dia, em ordem
SELECT hora, titulo, cinema, endereco_cinema FROM sessoes
WHERE data = '2025-10-18' ORDER BY hora;

-- todos os filmes de uma seção com sinopse
SELECT titulo, diretores, duracao, sinopse FROM filmes
WHERE secao = 'Competição Novos Diretores';

-- em quais cinemas um filme passa
SELECT data, hora, cinema, endereco_cinema FROM sessoes
WHERE filme_slug = 'quase-o-amor-da-minha-vida';
```
