# Planejador da Mostra

**→ [Abrir o planejador](https://cainanbaladez-bot.github.io/planejador-mostrasp/)**

Planejador pessoal da programação da Mostra Internacional de Cinema de São Paulo.
A pessoa explora os filmes, marca os que quer ver (★ quero muito / ★ quero ver / ☆ se sobrar) e
monta a agenda — com detecção de conflito de horário, encaixe automático das sessões
dentro da disponibilidade dela e exportação para o calendário.

Funciona no celular, instala como app (PWA) e abre offline. **Não pede cadastro nem
senha**: a agenda fica no navegador da pessoa, e o botão *🔗 Link* leva tudo para
outro aparelho dentro da própria URL.

> **Projeto independente.** Não é um site oficial da Mostra. A programação é lida do
> site da Mostra; horários e ingressos devem ser confirmados em [mostra.org](https://mostra.org).

## Como rodar / publicar

```bash
py -3.10 build_planejador.py    # gera planejador.html e docs/index.html
```

O GitHub Pages publica a pasta `docs/` (Settings → Pages → branch `main`, pasta `/docs`).
Ao publicar uma versão nova, suba o `VERSAO` em `docs/sw.js` para descartar o cache antigo
nos aparelhos que já instalaram.

## Arquivos

| Arquivo | O que é |
|---|---|
| **`planejador.html`** | O app final — **arquivo único, basta abrir no navegador** (duplo clique). Dados embutidos, não precisa de servidor nem internet (só as imagens dos pôsteres vêm da web). |
| `planejador.template.html` | Template (HTML/CSS/JS) sem dados. Edite este e rode o build. |
| `build_planejador.py` | Injeta os dados enxutos no template → gera `planejador.html`. Rodar: `py -3.10 build_planejador.py` |
| `enrich_filmes.py` | Enriquece os filmes: **festivais/prêmios** (regex na sinopse, offline) + **nota do Letterboxd** (raspagem do autocomplete + JSON-LD, casando título original+ano+diretor; cache em `data/letterboxd_cache.json`). Gera `data/enriquecimento.json`, que o build embute. Rodar ANTES do build: `py -3.10 enrich_filmes.py` (~10 min na 1ª vez; `--so-festivais` p/ pular o Letterboxd). |
| **`docs/`** | O que o GitHub Pages publica: `index.html` (o app), `manifest.webmanifest`, `sw.js` (service worker) e os ícones. Gerado pelo build — não editar `docs/index.html` à mão. |
| `gera_regioes.py` | Regenera o literal `REGIOES` (agrupamento de cinemas por região) a partir dos bairros dos endereços. Rodar só quando os cinemas mudarem. |
| `mostra-scraper-completo/mostra-scraper/data/` | Fonte dos dados (49ª edição: 380 filmes, 1309 sessões, 16/10–05/11/2025). Ver README do scraper para re-raspar. |

## Funcionalidades do planejador

- **Filmes**: busca (título/direção/elenco/país, sem acento) e filtros por seção
  (chips coloridos), dia, cinema, festival e **marcação** — *só os que marquei · ★ quero
  muito · ☆ se sobrar · só os que ainda não marquei · já com sessão na agenda*.
  Ordenação por **A–Z · ★ minha prioridade · dia e hora da sessão · nota Letterboxd · ano**
  (a ordem cronológica usa a 1ª sessão que ainda passa pelos filtros de dia/cinema —
  filtrando por 21/10, a lista sai das 12h às 22h daquele dia).
  **Limpar**: *limpar marcações* ao lado do contador e *🗑 Limpar agenda* na Minha Agenda —
  as duas listas são independentes e as duas pedem confirmação.
- **Dados p/ escolher melhor**: selo **★ nota Letterboxd** no pôster (verde, com link
  e nº de avaliações no modal), louros de **festivais** (CANNES, BERLIM, VENEZA…) no
  card, caixa 🏆 com a frase do prêmio no modal; **filtro por festival / premiados** e
  **ordenação por nota Letterboxd** na toolbar. A nota também aparece na lateral do
  calendário e nos ingressos da agenda.
- **Modal do filme**: sinopse, ficha técnica, trailer, link da Mostra e todas as
  sessões agrupadas por dia com botão **+ AGENDA** — já avisa "⚠ choca com X"
  antes de adicionar.
- **Minha Agenda** (uma aba só, com alternador **▦ Calendário / ☰ Lista** no topo —
  os mesmos dados e as mesmas estatísticas/exportação nos dois modos):
  - **▦ Calendário** (padrão, estilo Outlook): grade mensal do festival com as sessões
    como eventos; na **lateral, todos os filmes selecionados (★ ou já com sessão) e
    TODOS os horários clicáveis** — ✓ = na agenda, ⚠ vermelho = chocaria com algo já
    marcado. É a tela de *composição*: testar combinações e ver o encaixe na hora.
  - **☰ Lista**: as sessões viram *ingressos* por dia; conflito fica vermelho;
    intervalo entre sessões mostra "troca de cinema — APERTADO" quando < 40 min;
    filmes marcados com ★ sem sessão aparecem como pendência.
  - Estatísticas (sessões, filmes, dias, horas de cinema) e **exportar** (ver abaixo).

- **Exportar pro calendário (.ics)** — duas saídas, só:
  - **uma sessão**: botão 📅 no ingresso (modo Lista) e na linha da sessão dentro do
    modal do filme (só aparece se a sessão já está na agenda);
  - **a agenda inteira**: botão *📅 Agenda inteira (.ics)* no topo da Minha Agenda.

  **No celular**: o app do Google Agenda **não tem "importar"** — isso só existe no site,
  no computador. Por isso cada sessão tem também um botão **G** (*Adicionar ao Google
  Agenda*), que abre o app já com o evento preenchido. O `.ics` continua sendo o caminho
  no desktop e para Apple/Outlook.

  O arquivo abre no Google Agenda, Apple Calendário e Outlook. Detalhes que importam:
  `UID` estável por sessão + `SEQUENCE` que cresce a cada exportação — então
  **reexportar atualiza os eventos em vez de duplicar**; `VTIMEZONE` de
  America/Sao_Paulo; `DTSTAMP`; dobra de linha em 75 octetos contando UTF-8 (não
  parte acento nem emoji). **Sem `VALARM` de propósito**: assim vale o lembrete
  padrão que a pessoa já configurou no calendário dela.
- **Mobile**: layout mobile-first até 640px — a grade mensal de 7 colunas vira uma
  **lista vertical de dias** (estilo "agenda" do Google, sem rolagem lateral), a grade
  de filmes vira 2 colunas, o modal ocupa a tela inteira e os alvos de toque vão a 40px.
  Testado a 375px: nenhuma tela rola pro lado.
- **Persistência**: localStorage — chaves derivadas de `LS_PREFIX` no template. Escritas e
  leituras inválidas são tratadas sem impedir a abertura do app. O botão **⇩ Backup** baixa
  agenda, marcações, disponibilidade, cinemas e preferências; **⇧ Restaurar** importa o arquivo.

## Quando sair a 50ª Mostra

1. `python mostra-scraper-completo/mostra-scraper/scrape_mostra.py --edition 50`
2. Apontar `DATA` no `build_planejador.py` para os novos JSONs (e renomear campos se mudar).
3. Rodar `py -3.10 gera_regioes.py` se os cinemas mudarem (regenera o literal
   `REGIOES` a partir dos bairros dos endereços) e conferir os agrupamentos.
4. Ajustar título/datas no `planejador.template.html`: o header, a legenda do mês em
   `calBody()` e — numa linha só — `const LS_PREFIX="mostra49", EDICAO="49ª Mostra";`,
   que já governa as chaves do localStorage, o nome dos arquivos .ics e o `UID` dos eventos.
5. Apagar a faixa **BETA** (`<div class="beta">` logo abaixo do `.strip` + o bloco `.beta`
   do CSS) — ela avisa que a versão no ar ainda usa a programação de 2025.
6. `py -3.10 build_planejador.py`

## Disponibilidade, geografia e encaixe automático

Aba **Disponibilidade** (entre *Filmes* e *Minha Agenda*). É a peça que mais muda o
resultado: medido com 20 filmes marcados, quem está livre encaixa os 20; quem só pode
no fim de semana encaixa 9. O catálogo continua grande (mesmo só no fim de semana dá
pra alcançar 280 dos 373 filmes) — o que estrangula é a combinação.

1. **Perfis prontos** — *Estou de férias · Trabalho de dia · Só à noite · Só fim de
   semana · Vou com criança*. Cada um preenche a grade, que continua editável.
2. **Grade dia × faixa** — 21 dias × 5 faixas (10–13, 13–16, 16–19, 19–21, 21h+).
   Clique e arraste para pintar; clique no cabeçalho do dia ou no rótulo da faixa para
   ligar/desligar a linha inteira. As faixas foram cortadas nos limites que as pessoas
   usam de verdade ("a partir das 19h"). No celular a grade **transpõe**: os dias viram
   linhas e as faixas viram colunas, com célula de 50×38px.
3. **Geografia** — 7 regiões derivadas dos bairros reais dos endereços
   (Augusta/Consolação 474 sessões, Vila Mariana/Paraíso 263, Centro 227, Paulista 205,
   Pinheiros 32, Ipiranga 14, CEUs 94 — o grupo inclui o Centro de Formação
   Cultural Cidade Tiradentes). Cada região abre em "ajustar" com a
   lista de cinemas e o bairro de cada um. As 6 primeiras saem do bairro do endereço;
   os CEUs ficam num grupo só, com o bairro ao lado de cada um, porque atribuir zona a
   cada CEU seria chute meu.

O contador no topo mostra quanto sobrou: *"X de 1309 sessões · Y filmes ao seu alcance"*,
e fica vermelho abaixo de 25%.

### ★ com três níveis

**★ Quero muito ver · ★ Quero ver · ☆ Se sobrar tempo** — mais "não marcado".
O nível do meio é o caso mais comum e faltava.

No **card** o botão ★ cicla pelos quatro estados (o _title_ diz o que o próximo
clique faz; a cor separa os três: cheio, contornado, apagado). No **modal** é um
combobox rotulado *QUERO VER?*, com "Não marcado" explícito como opção — ali o
ciclo confundia, porque sem marcação o botão dizia "★ Quero ver", que lia como
estado em vez de ação, e desmarcar exigia dar a volta inteira.

O nível só decide alguma coisa quando algo precisa ser cortado: o encaixe maximiza
os "quero muito" primeiro, depois os "quero ver", depois os "se sobrar"
(comparação lexicográfica). Verificado nos três cenários — resolvendo só com o
nível 1 dá o mesmo número que o nível 1 alcança na solução completa, ou seja,
nunca se sacrifica um nível alto para caber um baixo.

O `localStorage` migra sozinho: a chave passou a ser `mostra49_watch3`, e o valor
2 do formato antigo (que queria dizer "se sobrar tempo") vira 3.

### ⚡ Montar minha agenda

O botão no topo da Minha Agenda abre primeiro as escolhas do planejamento. A pessoa
seleciona o objetivo principal antes de gerar a proposta:

- **máximo de filmes**;
- **minhas prioridades** — protege os três níveis de marcação;
- **menos deslocamentos** — reduz trocas de cinema, pois a programação não traz
  coordenadas verificadas para calcular quilômetros;
- **menos dias**, **menos espera** ou **melhores notas**.

Também é possível manter as sessões já escolhidas, configurar 20/30/40/60 minutos para
troca de cinema, limitar filmes por dia, definir o último horário aceitável e permitir
uma tolerância de 0–2 filmes quando o objetivo reduz um custo. Para esses objetivos, o
planejador encontra primeiro o máximo possível e só aceita uma agenda dentro da tolerância.

A proposta mostra filmes, dias, trocas de cinema, espera e cobertura de notas, além das
sessões escolhidas e do motivo de cada exclusão. Ela só altera a agenda quando a pessoa
pressiona **Aplicar**. **Buscar combinação melhor** amplia a busca de 1,2 para 5 segundos.
Todas as edições importantes oferecem **↶ Desfazer**.

Por dentro: busca em profundidade com poda otimista, semeada por uma solução gulosa
(a sessão que termina mais cedo), ordenando os filmes do mais restrito para o menos.
Teto de 1,2 s — se estourar, devolve a melhor que achou e a proposta avisa
("≈ melhor que achei em 1,2 s"). Achar a boa resposta é rápido; o que custa é *provar*
que é a melhor, e isso só aparece marcando 40+ filmes.

## 🔗 Link da agenda (em vez de login)

Não há cadastro, senha nem servidor. A agenda mora no `localStorage` do navegador, e o
botão **🔗 Link** copia um endereço versionado que carrega **a agenda inteira e os três
níveis de prioridade dentro da própria URL** (ids em base 36: uma agenda de 20 sessões mais
20 filmes marcados dá cerca de 200 caracteres).
A pessoa manda o link para si mesma e abre no celular — ou manda para um amigo.

Abrir um link desses **nunca sobrescreve calado**: se já houver agenda no aparelho,
aparece uma barra perguntando *"abrir a do link"* ou *"manter a minha"*.

## Medição de uso (GoatCounter)

Mesma conta dos outros sites (`fsa-fomento.goatcounter.com`), sem cookie e sem banner.
Além da abertura da página, desde 17/09/2026 o app manda **eventos** `mostra/<ação>`
pela função `medir()` do template — **uma vez por abertura da página** (repetir a ação
não conta de novo), então o número lido é de *pessoas que fizeram*, não de cliques.

| evento | quando |
|---|---|
| `marcou-filme` | primeira marcação ★ (estrela ou combobox) |
| `aba-disponibilidade` / `aba-agenda` | abriu a aba |
| `disponibilidade` · `perfil-<id>` | mexeu na grade/cinemas · aplicou um perfil pronto |
| `sessao-manual` | pôs sessão na agenda à mão |
| `montar-abriu` · `montar-gerou` · `objetivo-<id>` | abriu o montador · gerou proposta · objetivo escolhido |
| `proposta-aplicada` / `proposta-descartada` | decidiu a proposta |
| `ics-sessao` · `ics-agenda` · `google-agenda` | levou pro calendário |
| `link-copiado` · `chegou-por-link` | compartilhou · abriu um link de agenda |
| `agenda-copiada` · `backup` · `restaurou` | texto, backup e restauração |
| `pwa-instalou` · `abriu-como-app` | instalou / abriu pelo ícone |

Quem lê: o painel privado `analise-empirica-fsa-2014-2023/scripts/27_uso.py`
(localhost:8790), ripa do Planejador → "O que fizeram lá dentro" e "Como quiseram montar".
Evento novo = chamar `medir("nome")` aqui e pôr o rótulo em `ACAO_MOSTRA` lá.

## PWA (instalar no celular, abrir offline)

`docs/` traz `manifest.webmanifest`, `sw.js` e os ícones. Servido por HTTPS, o app instala
na tela inicial e abre sem internet. O service worker usa **stale-while-revalidate** para o
app (abre na hora do cache e atualiza em segundo plano — o HTML tem 1,3 MB com os dados
dentro, esperar a rede deixaria a abertura lenta à toa) e **cache-first** para os pôsteres,
que são guardados conforme aparecem. Em `file://` o registro nem é tentado.

Testado com o servidor derrubado: o app abriu inteiro do cache, com os 380 filmes e as
1309 sessões.

## Preview browser / celular

No cabeçalho, ao lado das abas, tem um alternador **🖥 Browser · 📱 Celular**.
O 📱 abre a *mesma* página numa janela de 390×844 — assim valem as media queries
de verdade (nada de CSS duplicado simulando celular) e o `localStorage` é o mesmo,
então a agenda acompanha nas duas janelas. Fechar a janelinha volta o botão pro
estado 🖥 sozinho. O alternador some abaixo de 640px (num celular de verdade não
faz sentido) e dentro da própria janela de preview.
