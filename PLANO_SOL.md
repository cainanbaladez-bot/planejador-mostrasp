# Plano de execução — Planejador da Mostra

Preparado para o modelo SOL em 17/09/2026.

> **Autoria e estado.** Este plano foi escrito pelo **SOL** (modelo de IA) a partir de uma
> revisão do projeto, e executado por ele no mesmo dia. Foi publicado na versão **v8**
> (sw.js), em 18/09/2026, junto com a medição de eventos. O texto abaixo é o plano
> **original, sem edição**: onde ele diz "ainda não foram implementadas", vale para
> 17/09. O que foi entregue e o que ficou pendente está em
> [Estado da execução](#estado-da-execução-18092026), no fim.

## Pedido e resultado esperado

Implementar as melhorias da revisão do projeto, com prioridade para a confiabilidade do planejamento e para a escolha de critérios **antes de gerar a agenda**. Ao clicar em **Montar minha agenda**, a pessoa deve poder escolher entre ver o máximo de filmes, respeitar suas prioridades, percorrer menor distância e outros objetivos úteis. Exibir uma proposta comparável e editável; somente **Aplicar proposta** modifica a agenda.

Este documento é uma especificação para execução. As funcionalidades descritas ainda não foram implementadas.

## Orientações para quem executar

- Examinar instruções locais e o estado do Git antes de editar. Preservar alterações existentes do usuário.
- Implementar por etapas na ordem abaixo, validando cada entrega. Resolver escolhas rotineiras de implementação com base neste documento.
- Manter a identidade escura e âmbar, o português brasileiro, a ausência de cadastro, o funcionamento offline e a distribuição em HTML único.
- A fonte da interface é `planejador.template.html`. `docs/index.html` e `planejador.html` são saídas do build; não editar manualmente.
- A execução solicitada é local. Não publicar, enviar mensagens ou mudar o modelo de outras tarefas como parte deste plano.
- Não substituir os dados de 2025 por uma suposta programação de 2026. Preservar a faixa de demonstração até existir uma fonte verificada para a nova edição.

## Diagnóstico confirmado

| Local atual | Problema | Consequência |
| --- | --- | --- |
| `montarLink`, `lerLink`, `aplicarLink` | Exportam/importam somente prioridades 1 e 2 | Filmes de prioridade 3 desaparecem ao compartilhar |
| `liberada` | Consulta apenas a faixa de início | Aceita filme que termina em horário bloqueado |
| `conflitos` / `chocaS` | Regras distintas para inclusão manual e automática | A mesma combinação recebe avisos diferentes |
| `encaixar` | Todos os critérios atuais são desempates após prioridades pessoais | Não existe objetivo real de maximizar a quantidade de filmes |
| `pontuar`, critério `desloc` | Minimiza quantidade de cinemas distintos | Não mede distância nem número de deslocamentos |
| Inicialização do estado | `JSON.parse` sem recuperação | Armazenamento inválido interrompe o carregamento |
| Grade de disponibilidade | Interação depende de eventos de ponteiro | Espaço não alterna a célula focada |
| `rodarEncaixe` | Busca síncrona na interface | Pode bloquear interação durante o cálculo |
| Retorno de `encaixar` | Oculta limite de tempo quando todos os filmes cabem | Pode sugerir optimalidade sem ter otimizado os critérios secundários |

Base examinada: 380 filmes e 1.309 sessões; IDs das sessões são únicos e todas referenciam filmes existentes. Os casos de compartilhamento, disponibilidade, regras divergentes e armazenamento inválido foram reproduzidos com o JavaScript atual.

## Etapa 1 — Corrigir a base do planejamento

### Horários e conflitos

1. Criar funções puras compartilhadas para início, término, disponibilidade, deslocamento e compatibilidade.
2. Usar instantes ou minutos absolutos coerentes com `America/Sao_Paulo`, independentes do fuso do aparelho. Adotar intervalos semiabertos: uma sessão que termina exatamente às 19h cabe em disponibilidade até as 19h.
3. Verificar todas as faixas atravessadas pelo filme, incluindo a mudança de dia. Definir explicitamente os limites fora da grade: antes das 10h fica indisponível; após meia-noite exige disponibilidade do dia seguinte, que a grade atual não oferece. Não liberar esses períodos por aproximação silenciosa.
4. Dados sem duração válida precisam de indicação visível e de uma estimativa conservadora explícita. Centralizar a política; não usar um valor oculto diferente por tela.
5. Usar a mesma avaliação no modal, calendário, lista, filtro de disponibilidade e algoritmo. A inclusão manual pode aceitar uma sessão problemática, mas deve mostrar o motivo antes e depois da inclusão.
6. Diferenciar sobreposição, tempo insuficiente de deslocamento, horário indisponível e cinema excluído.
7. Preservar inicialmente as margens atuais: 0 minuto no mesmo cinema e 40 minutos entre cinemas, agora ajustáveis. Uma margem genérica não deve ser apresentada como tempo real de trajeto.

### Compartilhamento e recuperação

1. Versionar o formato do link e incluir edição e os três níveis de prioridade. Oferecer checkbox para incluir disponibilidade, cinemas excluídos e preferências de montagem; deixá-lo desmarcado por padrão.
2. Manter leitura dos links antigos. Sem versão, o parâmetro antigo `s` é ambíguo após a mudança de escala: não adivinhar seu significado; oferecer escolha clara entre “Quero ver” e “Se sobrar tempo” na importação.
3. Validar tipos, prioridades, limites de tamanho e IDs. Para outra edição, explicar a incompatibilidade antes de importar.
4. Atualizar todas as telas após importação, inclusive os cards de filmes; não apenas a agenda e o contador.
5. Encapsular leitura e gravação do armazenamento com validação e tratamento de erro. Preservar o conteúdo inválido para recuperação quando possível; não anunciar que salvou se a gravação falhou.
6. Adicionar exportação/importação de backup JSON com versão e edição. Mostrar resumo antes de substituir dados existentes.
7. Oferecer “Desfazer” para remoções, limpeza e aplicação de proposta, restaurando o estado anterior completo da operação.

## Etapa 2 — Escolher objetivos ao apertar o botão

Trocar o botão **Encaixar** por **Montar minha agenda**. O clique abre um painel acessível, que ocupa a tela no celular, com este fluxo:

1. **O que você quer priorizar?** Opções abaixo, com seleção única e descrição curta. Primeira utilização: “Máximo de filmes”. Nas seguintes, lembrar a escolha.
2. **Ajustes da agenda**, recolhidos inicialmente: manter sessões atuais (ligado), margens, limite diário e horário máximo para terminar.
3. Resumo: quantidade de filmes marcados, dias disponíveis e restrições ativas. Avisar se nenhuma sessão é elegível e oferecer atalhos para ajustar disponibilidade ou marcar filmes.
4. Botão **Gerar proposta**. Durante o cálculo, mostrar andamento e **Cancelar**.
5. Mostrar proposta e controles **Alterar critérios**, **Recalcular**, **Descartar** e **Aplicar proposta**.

### Objetivos e ordem de decisão

Comparar tuplas lexicográficas, em ordem explícita, em vez de misturar unidades em uma soma arbitrária de pesos. Contar filmes distintos, não sessões repetidas.

| Opção na interface | Objetivo e desempates | Texto explicativo |
| --- | --- | --- |
| **Máximo de filmes** | Mais filmes distintos → mais “Quero muito” → mais “Quero ver” → menos deslocamento → menos espera | “Encaixar o maior número possível. Pode trocar um favorito longo por mais filmes.” |
| **Minhas prioridades** | Mais “Quero muito” → mais “Quero ver” → mais “Se sobrar” → menos deslocamento → menos espera | “Proteger seus favoritos, mesmo que caibam menos filmes.” |
| **Menor distância** | Respeitar piso de quantidade → menor distância estimada → mais filmes → prioridades → menos espera | “Reduzir o percurso entre sessões do mesmo dia.” |
| **Menos dias** | Respeitar piso de quantidade → menos dias ocupados → mais filmes → prioridades → menos deslocamento | “Concentrar a programação em menos dias.” |
| **Menos tempo esperando** | Respeitar piso de quantidade → menor espera entre sessões → mais filmes → prioridades → menos deslocamento | “Reduzir os intervalos livres entre filmes.” |
| **Melhores avaliações** | Mais filmes → maior soma de notas disponíveis → maior cobertura de notas → prioridades → menos deslocamento | “Entre agendas com a mesma quantidade, favorecer as notas do Letterboxd disponíveis.” |

Prioridades significa comparar as contagens dos níveis 1, 2 e 3, nessa ordem. Notas ausentes contribuem zero somente para o cálculo, nunca são exibidas como nota zero. Informar cobertura e data disponível das avaliações, sem apresentar dados armazenados como atualizados em tempo real.

### Evitar a solução trivial de poucos filmes

Nos objetivos de distância, dias e espera, minimizar o custo sem um piso levaria a agendas vazias ou quase vazias. Implementar:

- Primeiro obter uma agenda de referência pelo objetivo de máximo de filmes, sob as mesmas restrições.
- Oferecer **“Para melhorar esse critério, aceito abrir mão de…”**: nenhum filme (padrão), até 1 filme ou até 2 filmes.
- Se a referência encontrou `N` filmes e a tolerância é `k`, exigir no mínimo `max(filmes fixos distintos, N-k, N > 0 ? 1 : 0)` filmes. Se existe uma solução com filmes, nunca entregar agenda vazia apenas para reduzir o custo.
- Incluir a própria referência como candidata válida, garantindo uma proposta disponível mesmo quando acabar o tempo da segunda busca.
- Mostrar: “Mantendo os N filmes encontrados” ou “Aceitando até k filmes a menos”. Se a referência não foi provada ótima, chamá-la de “melhor quantidade encontrada”, nunca de máximo garantido.
- Estes modos podem substituir favoritos por filmes de prioridade menor. Explicar isso no painel e destacar no comparativo quais favoritos saíram. Sessões fixas permanecem obrigatórias.
- Não introduzir uma opção “Equilibrado” sem definir uma regra compreensível; os objetivos acima cobrem a primeira entrega.

### Restrições independentes do objetivo

- Selecionar apenas filmes marcados e no máximo uma nova sessão por filme.
- Respeitar toda a disponibilidade e os cinemas habilitados.
- Permitir limite de filmes por dia (sem limite por padrão), horário máximo de término (sem limite adicional por padrão) e margens de troca de sessão/cinema.
- Manter as sessões existentes quando solicitado. Se a base fixa já contém sobreposição, repetição ou viola uma restrição, listar os problemas antes de gerar. Exigir resolução, flexibilização explícita da restrição ou desativação de “Manter”; nunca declarar a proposta inteira válida escondendo conflitos antigos.
- Avaliar estatísticas e trajetos sobre a agenda completa: sessões fixas mais novas.
- Não aplicar resultados de cálculo antigo se os filmes, horários ou preferências mudarem enquanto ele estava em execução.

## Etapa 3 — Medir deslocamento de verdade

1. Adicionar um catálogo de cinemas com ID estável, endereço, latitude, longitude, origem da coordenada e data de verificação. Mapear os nomes atuais para esses IDs.
2. Usar coordenadas verificadas a partir dos endereços, sem inventar localizações pelo bairro. Fazer a preparação dos dados no build ou em script separado, sem exigir localização pessoal, chave paga ou consulta de geocodificação durante o uso do app.
3. Para a primeira versão, calcular distância geográfica entre cinemas de sessões **consecutivas de cada dia**, ordenadas por horário. Somar as distâncias; ida de casa, volta para casa e viradas entre dias ficam fora da medida.
4. Chamar a métrica de **“Distância estimada entre cinemas (linha reta)”**. Não dizer que é trajeto a pé, distância viária ou duração real. O cálculo de viabilidade usa as margens configuradas, não uma velocidade inventada.
5. Cachear a matriz de distâncias por pares de cinemas; operar inteiramente offline depois do build.
6. Coordenada ausente não equivale a distância zero. Se faltarem coordenadas entre os cinemas elegíveis, oferecer **Menos trocas de cinema** como alternativa e explicar a cobertura incompleta. Não comparar agendas com distâncias parcialmente desconhecidas como se fossem completas.
7. A alternativa conta trocas entre sessões consecutivas, não apenas cinemas únicos. `A → B → A` tem duas trocas; `A → A → B` tem uma.
8. Buscar completar a cobertura dos cinemas da edição como parte desta etapa. Se algum endereço permanecer ambíguo, registrar a pendência e entregar o comportamento alternativo funcionando.

## Etapa 4 — Proposta compreensível e cálculo responsivo

### Apresentação

- Exibir quantidade total e novas inclusões; distribuição por prioridade; dias; trocas; distância estimada quando disponível; espera; horas de filme; e quantidade de filmes com nota.
- Mostrar comparação com a agenda atual e, nos modos com tolerância, com a referência de máximo de filmes. Destacar ganhos e perdas em linguagem concreta.
- Exemplo ilustrativo: “12 filmes, 3 dias, 4 trocas. Em comparação com a referência: 1 filme a menos e 2 trocas a menos.” Não usar números de exemplo como resultados reais.
- Para filmes excluídos, distinguir: sem sessões, cinema excluído, duração/horário incompatível, conflito com sessões fixas, conflito na proposta, limite diário e decisão do objetivo.
- Se a busca foi interrompida, usar “Não incluído na melhor combinação encontrada” quando não houver prova de impossibilidade. Não atribuir todo filme excluído a um conflito.
- Manter aviso de resultado aproximado mesmo quando todos os filmes couberem, pois distância, dias e espera podem continuar subótimos.
- Gerar inicialmente apenas o objetivo escolhido. Oferecer comparação com outro objetivo sob demanda; não executar seis buscas longas em toda interação.

### Algoritmo

- Extrair núcleo puro para `src/planner.js` ou estrutura equivalente, com entrada serializável e sem acesso ao DOM/localStorage.
- Separar geração de candidatos, restrições, métricas, comparador e limites otimistas da busca.
- Adaptar as podas para cada objetivo. A poda atual por prioridades não serve para máximo de filmes; custos de distância/espera de uma seleção parcial não são automaticamente limites seguros para agendas completas.
- Semear com soluções gulosas apropriadas e preservar sempre a melhor solução válida já encontrada.
- Usar desempate final estável por IDs de sessões para resultados reproduzíveis.
- Executar em Web Worker; empacotar o código do worker no HTML e criá-lo por Blob para preservar distribuição em arquivo único. Validar também em `file://`; se indisponível, usar execução em lotes que devolvam controle à interface, sem travamento síncrono longo.
- Manter o orçamento inicial próximo de 1,2 s, compartilhado entre referência e otimização, com “Buscar uma combinação melhor” para ampliar o esforço até aproximadamente 5 s. Medir e ajustar com dados reais; retornar metadados de duração, motivo de parada e optimalidade comprovada ou não.
- Cancelamento precisa encerrar o trabalho, e não apenas ocultar o indicador. Ignorar mensagens de requisições obsoletas.
- Métricas: espera é a soma de `max(0, início seguinte - término anterior - margem necessária)` entre sessões consecutivas do mesmo dia. Não incluir períodos antes do primeiro filme ou após o último.

## Etapa 5 — Descoberta, clareza e acessibilidade

- Orientação curta e dispensável: “Marque filmes → Defina disponibilidade → Monte sua agenda”.
- Filtro **Só filmes que cabem na minha disponibilidade**, usando as mesmas regras do planejamento. Mostrar número de sessões elegíveis no card e realçar essas sessões no modal.
- Separar **Limpar filtros**, **Limpar marcações** e **Limpar agenda**.
- Tornar visível o nível de interesse no card e oferecer escolha direta dos níveis, sem exigir percorrer todo o ciclo para corrigir uma escolha.
- Aumentar contraste dos textos secundários e legibilidade de metadados, preservando a identidade visual. Verificar contraste com medição.
- Garantir abertura de cards e acionamento da grade com teclado. Espaço/Enter devem alternar a célula sem alternância dupla após clique ou arraste.
- Modal/painel com nome acessível, foco inicial, foco contido, fechamento por Escape e retorno ao acionador; usar controles semânticos e indicar seleção além da cor.
- Nomear campos e botões de ícone; anunciar salvamento, erros e conclusão com região de status acessível.
- No celular, manter ações essenciais visíveis sem esconder conteúdo e sem rolagem horizontal.

## Etapa 6 — Organização e publicação futura

- Centralizar edição, datas, arquivos de dados, rótulos e versão de esquema em uma configuração consumida pelo build e pelo app.
- Derivar datas do conjunto de sessões e verificar coerência com a configuração. Remover referências fixas à 49ª edição de exportações e legendas, sem apagar o histórico salvo dessa edição.
- Separar incrementalmente planejamento, persistência, compartilhamento e interface em fontes próprias. O build continua produzindo HTML único, com CSS, scripts e dados embutidos e escape seguro.
- Validar IDs, referências, datas e duração na preparação de dados; erros estruturais impedem o build, enquanto ausências esperadas geram relatório explícito.
- Automatizar a versão do cache por conteúdo. Na ativação do service worker, apagar apenas caches deste aplicativo, não todos os caches da origem. Preservar pôsteres quando possível e informar atualização disponível.
- Acrescentar verificações automatizadas ao fluxo do repositório e atualizar o README com os objetivos, suas limitações e os comandos de execução.
- O comando `py -3.10` do README falhou no ambiente examinado por instalação indisponível. Localizar um Python funcional; não concluir que o build está quebrado nem modificar dependências do sistema sem necessidade.

## Validação obrigatória e critérios de aceite

Criar testes de comportamento para o núcleo e testes de integração das jornadas críticas, sem testes que apenas reproduzam a implementação.

| Caso | Resultado esperado |
| --- | --- |
| Link com os três níveis, agenda e restrições opcionais | Exportar e importar preserva exatamente o estado incluído |
| Link antigo ou edição diferente | Tratamento explícito da ambiguidade/incompatibilidade; nenhuma sobrescrita silenciosa |
| Sessão 18h30–20h30 com bloqueio a partir das 19h | Rejeitada pelo encaixe e sinalizada na inclusão manual |
| Sessão termina exatamente no limite da disponibilidade | Aceita |
| Sessão atravessa meia-noite, duração inválida ou aparelho em outro fuso | Política consistente, sem autorização acidental de faixas bloqueadas |
| Troca de cinema com 20 min, margem configurada de 40 min | Mesmo aviso em modal, calendário, lista e planejador |
| Um favorito longo concorre com dois filmes menos prioritários | Máximo de filmes escolhe os dois; Minhas prioridades preserva o favorito |
| Mesmos cinemas distintos, mas ordem A→B→A versus A→A→B | Quantidades de trocas diferentes, medidas corretamente |
| Piso de quantidade e tolerância 0/1/2 | Nenhuma agenda abaixo do piso; nenhuma agenda vazia como atalho para reduzir custo |
| Coordenadas ausentes | Alternativa clara de menos trocas; nenhuma distância falsa |
| Todos os filmes cabem, mas busca esgota tempo | Aviso de aproximação permanece para critérios secundários |
| Agenda fixa contém conflito | Problema destacado antes de gerar; proposta não esconde invalidez |
| Dados locais inválidos ou gravação falha | App abre e informa o problema; sem mensagem falsa de sucesso |
| Aplicar e desfazer; importar e recarregar | Estado restaurado/persistido e telas coerentes |
| Gerar, cancelar, mudar preferência e gerar novamente | Interface responsiva, sem resultado obsoleto aplicado |
| Teclado e leitor de tela | Grade, cards, painel e modal operáveis com foco e nomes corretos |

Para validar a busca, comparar todas as modalidades com enumeração exaustiva em conjuntos pequenos e determinísticos, incluindo casos em que cada objetivo realmente muda a resposta. Para volume real, testar listas de 20, 40 e 80 filmes marcados; medir tempo e responsividade sem exigir prova de ótimo nas instâncias grandes.

Verificar jornadas completas em larguras de 375 px, 390 px e desktop: marcar filmes, ajustar disponibilidade, escolher objetivo, comparar proposta, aplicar, desfazer, compartilhar e restaurar. Verificar versão servida por HTTP, HTML por `file://` e reabertura offline após cache. Build final deve gerar saídas coerentes; registrar quais verificações passaram e qualquer limitação real.

## Ordem de entrega ao usuário

1. Correções de horários, conflitos, compartilhamento e armazenamento; núcleo testável.
2. Painel de objetivos, novas regras de otimização, proposta comparativa e cálculo responsivo.
3. Distância estimada com coordenadas verificadas, alternativa para dados incompletos e novos filtros.
4. Acessibilidade, desfazer/backup completos, configuração de edição, build/cache e documentação.

Ao terminar, relatar o que mudou, os testes executados e eventuais pendências de dados. Entregar os arquivos locais prontos para revisão. Não descrever etapas planejadas como implementadas.

---

## Estado da execução (18/09/2026)

Conferido no código publicado na v8 (`planejador.template.html`). Não é auditoria item a
item de todas as linhas acima, só do que dá pra confirmar direto no código.

**Entregue**
- Etapa 1: link versionado (`v=2`) com edição e os três níveis, com leitura dos links
  antigos; leitura/gravação do `localStorage` com recuperação (`lerLocal`/`gravarLocal`,
  aviso "dados inválidos foram recuperados"); backup e restauração em JSON; **↶ Desfazer**
  nas edições importantes; horários em `America/Sao_Paulo`.
- Etapa 2: botão **⚡ Montar minha agenda** com painel de objetivos (máximo de filmes,
  minhas prioridades, menor deslocamento, menos dias, menos espera, melhores avaliações),
  manter sessões, margem de troca de cinema (20/30/40/60 min), limite por dia, horário
  máximo, tolerância de 0 a 2 filmes com piso de quantidade.
- Etapa 4 (parte): proposta com filmes, dias, trocas, espera e cobertura de notas, motivo
  de cada exclusão, aviso de resultado aproximado; orçamento de 1,2 s com **Buscar
  combinação melhor** até 5 s.
- Etapa 6 (parte): `sw.js` apaga só os caches `planejador-*`; teste automático em
  `tests/planner-smoke.js` (`node tests/planner-smoke.js`, 10 casos).

**Pendente**
- Etapa 3 inteira: não há coordenadas dos cinemas. "Menor deslocamento" conta **trocas de
  cinema** entre sessões seguidas, que é a alternativa que o próprio plano prevê.
- Web Worker: o cálculo roda na página, disparado por `setTimeout`, não em worker.
- Etapa 5 e o resto da Etapa 6 (filtro "só o que cabe", configuração única de edição,
  versão de cache automática) não foram conferidos item a item.

**Acrescentado depois, fora do plano:** eventos de uso no GoatCounter (`medir()`, ver a
seção "Medição de uso" do README).
