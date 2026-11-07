# Aceite local: Desempenho web — 07/11/2026

> Histórico das validações e iterações locais. Para o estado atual de commit, integração e publicação, prevalece o [recibo de fechamento](web-performance-closeout-20261107.md). Contagens e decisões abaixo correspondem à etapa em que foram registradas.

WFLOW-20261107-WEB-PERFORMANCE / FEAT-REP-001 v0.8. Branch `feature/web-performance` baseada em `origin/main` 92f43fd, no worktree `/Users/williamsca/Documents/gotrendlabs-web-performance`. Checkout original e suas alterações preservados. Sem commit, PR, publicação ou deploy nesta execução.

## Implementação e decisões

- Entrada autenticada imediatamente após Perfil e badges; atalho no perfil. Admin Ops preserva exatamente sua condição staff/superuser.
- `/desempenho/` usa cliente Django → `GET /users/me/performance`, token pessoal, cada requisição com `private, no-store`. Nenhum identificador recebido por query seleciona usuário; sem ORM/fallback, novas permissões ou cálculos críticos.
- Seis indicadores do `scorecard`. `ranking_position=0` é Sem posição; categoria vazia é Ainda não definida. Staff/superuser mantêm ocultação administrativa do placar conforme perfil; bot recebe o agregado existente, sem posição pública inventada.
- Histórico exibe as até dez resoluções, escolha/data quando presentes, texto de resultado, delta e label GT₵ educativo do backend, link por slug. Sem imagens por linha ou requisições adicionais, filtros/paginação.
- Total e últimas conquistas vêm de `progression`; imagem de badge extraída em componente compartilhado com perfil, incluindo tema escuro. Links para `/profile/#badges` e ranking. Sem marcos/progresso inventados.
- Vazio orienta participação; erro mantém dados ausentes, retry e status 503; 403 restrito; 401 limpa sessão e redireciona ao login com retorno seguro. Apenas métodos seguros. Renderização completa, sem atualização parcial/loading artificial.
- Tabela desktop adapta linhas a cards no celular, preservando roles explícitos e cabeçalhos para leitores de tela; texto não depende de cor. Tokens, tipografia, foco e temas existentes. Textos novos usam marcadores Django de i18n.

## Evidências

Ambiente reutilizado: `../gotrendlabs-mcp/.venv` (Python 3.11). A `.venv` principal é Python 3.9 e não importa a sintaxe de unions dos contratos atuais; não foi modificada. PostgreSQL 16 efêmero em tmpfs na porta 55439 para a suíte completa, sem tocar no banco/volumes existentes. O Docker não tinha espaço para inicializar outro volume persistente.

- `python manage.py test tests.test_performance_web --noinput`: **12 testes aprovados**, sessão/visitante/401/403/503, dados/vazios, posição no menu, papéis, destinos, ausência de chamadas por linha, escape HTML, GET/HEAD e isolamento por token.
- `python manage.py check`: sem problemas.
- `python packages/contracts/export_openapi.py --check`: snapshot atual e inalterado.
- `python manage.py collectstatic --noinput`: 198 arquivos coletados.
- Quatro scripts JavaScript do CI aprovados: analytics, filtros/feed, convite contextual e preview de previsão.
- `docker build --check .`: sem avisos.
- Build isolado MCP: aprovado.
- Build principal: **não validado**, falhou em `apt-get` com `You don't have enough free space in /var/cache/apt/archives/`. Não houve limpeza de imagens/volumes do usuário.
- Suíte Python completa: `POSTGRES_PORT=55439 python manage.py test --noinput`, **693 testes executados, OK (3 skips), 297,111 s**. O discovery anunciou 696; o runner informa 693 executados no resumo final. Execução iniciada antes de acrescentar duas verificações adicionais à nova classe; a classe final com 12 testes foi reexecutada separadamente e aprovada.

QA reproduzível com `python tests/performance_preview.py` e `NODE_PATH=/Users/williamsca/.npm/_npx/e41f203b7505f1fb/node_modules node tests/test_performance_browser.js`: **30 combinações aprovadas** (1440/1024/768/390/320 px × dados/vazio/erro × claro/escuro), sem overflow horizontal ou erros JS. Verificados empilhamento, dez linhas, imagens por tema, foco visível e Tab. Doze capturas em `.runtime/performance/`; desktop claro e celular escuro inspecionados visualmente. Dados sintéticos existem exclusivamente nos testes, sem persistência ou inclusão no produto.

## MCP, arquitetura e limites

Sem ajustes MCP: ferramentas, schemas, contratos, autenticação, permissões, erros, replays e orientação editorial continuam iguais. É apenas um consumidor web do agregado existente. Ações de Admin Ops não implicam novas permissões MCP. Nenhuma mudança de banco, regras, mobile ou fronteiras; ADR/migration não necessários.

Referência visual anexada não estava disponível na conversa; composição segue descrição e design do projeto. QA em Chrome desktop com viewports móveis e fixtures locais; sem aparelho físico, Safari/Firefox ou sessão produtiva. Catálogos completos de tradução permanecem na iniciativa i18n existente; esta entrega usa seus marcadores. Build principal requer espaço no Docker e nova execução antes de publicação. Nenhum deploy solicitado ou realizado.

## Massa local para avaliação do layout

Em 07/11/2026, a pedido do usuário, criada a conta comum `desempenho.local@example.com` (id 13, Lia • demonstração local), sem privilégios administrativos. Dez mercados exclusivos `local-desempenho-20261107-01` a `-10`, títulos marcados `[Teste local]`, foram criados e passaram pelos serviços backend de publicação, previsão, fechamento e resolução. Fixture editorial explicitamente sintética/local; não representa aprovação editorial produtiva. Nenhum histórico anterior foi alterado. Execução transacional com guarda de banco localhost e supressão de emails somente no processo de fixture.

Contrato real conferido: reputação 120, posição 1 naquele momento, dez resoluções, precisão 70%, sequência 3 e cinco badges (Membro fundador, Primeira resolução, Top 10, 5 acertos, 10 resoluções). Categoria forte vazia preservada conforme backend. Login web real e GET autenticado de `/desempenho/` aprovados, com labels de acerto/erro e no-store. Credenciais e recibo ficam apenas em `.runtime/dev/performance-account.json` com modo 0600; gerador local em `.runtime/dev/seed_performance.py`, ambos ignorados pelo Git. Não foram enviados emails nem alterados MFA/privilégios do admin. Sem alteração de contrato, código de produto ou permissões MCP. Layout permanece aguardando avaliação com dados.

## Refinamento visual após feedback

WFLOW-20261107-WEB-PERFORMANCE-LAYOUT: painel integrado de título/placar, título 32/28 px, sombras removidas da página, espaçamento consistente de 16–24 px, tabela com mercado mais largo e números alinhados à direita. Lateral com imagens de 44 px e descrições compactas, sem repetir Conquistada. Celular usa três colunas de resultados abaixo do mercado. CSS versionado `20261107-layout-2`; serviço web local reiniciado para atualizar o template em cache.

12 testes Django específicos aprovados após alteração; 30 combinações de fixtures (dados/vazio/erro, cinco larguras e dois temas), foco/teclado e imagens temáticas aprovados. Adicionalmente, login web real da conta local e dez combinações de largura/tema, dez resoluções e cinco badges sem overflow. Capturas em `.runtime/performance/live-after-*`; desktop e celular inspecionados. Capturas aguardam a transição de tema existente para evitar cores intermediárias. Sem testes de domínio adicionais por não alterar lógica/API. MCP sem impacto em ferramentas, schemas, permissões, erros ou replays. Pendência de espaço para build principal permanece no workflow original; nenhum deploy.

## Imagens das conquistas locais

A pedido do usuário, vinculadas as artes existentes de `founding_member`, `first_resolution`, `top_ten`, `five_hits` e `ten_resolutions` aos campos `image_url`/`image_dark_url` do catálogo local. Esses campos estavam vazios, causando o check de ausência de imagem no componente compartilhado. Nenhuma arte foi inventada e nenhuma conquista, regra ou métrica alterada. Dez arquivos clara/escura responderam HTTP 200; agregado autenticado retornou as cinco imagens corretas; QA local em dez combinações de largura/tema passou sem overflow. Backup dos vínculos anteriores em `.runtime/dev/performance-badge-images-before.json`. Sem alteração de código/contrato/MCP ou produção.

## Carregar mais no recorte recente

A pedido posterior do usuário, cinco linhas visíveis inicialmente e botão nativo para revelar mais cinco já retornadas pela API. Contador acessível anuncia 5 de 10 e 10 de 10; controle desaparece no fim e foco vai ao primeiro novo link. Zero chamadas de rede para revelar linhas, sem contrato de paginação. Sem JS, todas as dez linhas acessíveis. Estado vazio e listas de até cinco itens não apresentam o controle.

13 testes Django aprovados, 30 combinações de tema/estado/largura aprovadas, teste de Enter/foco/contador/ausência de rede/sem JS aprovado. CSS/JS versionados e serviço web reiniciado. Somente apresentação; MCP/domínio/API preservados. WFLOW-20261107-WEB-PERFORMANCE-LOAD-MORE.

## Atalhos do cabeçalho

Incluídos Explorar mercados (home, primário) e Ver ranking (rankings, secundário), à direita do título no desktop e abaixo do subtítulo em telas pequenas. Mudança visual reversível sem nova regra/contrato/MCP; sem testes novos que espelhem marcação. Django check, diff check e QA autenticado em cinco larguras/dois temas, com dados locais, utilizados na validação. CSS `20261107-heading-actions`; web local reiniciado.

## Reversão dos atalhos do cabeçalho

Usuário rejeitou a composição; os dois atalhos foram removidos e título/subtítulo voltaram à disposição anterior. Histórico de avaliação acima preservado. Placar, badges com imagens e Carregar mais intactos. CSS versionado para invalidar cache; sem impacto MCP ou domínio.

## Identidade no cabeçalho

Proposta aceita pelo usuário: avatar de iniciais, nome e @handle do contexto autenticado existente, à direita do título e abaixo do subtítulo no celular. Não há foto disponível no contrato atual; reutilizado o avatar da navegação. Sem novos dados/chamadas, informações privadas ou impacto MCP. CSS `20261107-profile-identity`; web local reiniciado. Check Django/diff e QA com a conta local nos dois temas e cinco larguras.

## Reversão da identidade

Usuário rejeitou o bloco de avatar/nome/@handle; removido e restaurado cabeçalho anterior. CSS versionado e web local reiniciado. Gráfico ainda não implementado; sugestão usa deltas individuais reais, sem inferir evolução acumulada. Demais funcionalidades preservadas, sem impacto MCP.

## Prévia do gráfico de impactos

Após a reversão da identidade, implementado o gráfico solicitado pelo usuário: até dez impactos reputacionais individuais da API, em ordem cronológica, barras positivas/negativas, valor exato e link acessível ao mercado. Escala em pixels é apresentação, sem cálculo de reputação acumulada. Zero tem marca neutra; vazio/erro/admin não mostram gráfico.

15 testes aprovados, incluindo ordem, deltas preservados, escala, zero e ocultação por papel/vazio. QA autenticado em cinco larguras e dois temas com dez barras e três negativas; sem overflow. CSS `20261107-impact-chart`, serviço local reiniciado. Nenhuma alteração de API/MCP ou deploy. Essa entrada substitui a indicação anterior de gráfico somente sugerido.

### Ajuste de encaixe do gráfico

A pedido do usuário, retorno/eyebrow integram a mesma coluna esquerda de título/subtítulo. Gráfico da direita usa legenda compacta e área de barras de 88 px, preservando proporções/valores e links; distância até placar reduzida. Check Django e diff, QA com conta local em cinco larguras/dois temas, sem overflow. Nenhuma regra/contrato/API/MCP mudou; CSS versionado e web reiniciado.

## Tipografia comparada à Carteira

Inspeção de computed styles confirmou a mesma família IBM Plex Sans, mas overrides de Desempenho faziam título 32 px (Carteira 54 px em 1440), métricas 28 px (22), labels 13 px (12), texto de tabela 14 px (16) e seções 20 px (18). Ajustados para o padrão da Carteira, incluindo título compartilhado responsivo, cabeçalho de tabela uppercase/700/0.08em e métricas com -0.04em. Anotações do gráfico e metadados permanecem compactos por função. CSS versionado `20261107-wallet-type`; web local reiniciado. Check Django/diff e QA autenticado em cinco larguras/dois temas; sem impacto MCP/API.
