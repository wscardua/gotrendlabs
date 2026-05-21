---
id: FEAT-MARKET-001
titulo: "Feed de mercados"
versao: 0.9
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-05-21
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - market-lifecycle.md
  - i18n-content.md
  - wallet-ledger.md
dependencias:
  - FEAT-AUTH-001
impacta:
  - frontend-web
  - backend-api
  - database
aprovacao: pendente
---

# Feed de mercados

## Objetivo

Exibir mercados relevantes com filtros e informações suficientes para descoberta e retorno recorrente.

## Escopo incluído

- listagem de mercados
- filtros públicos por status/categoria via API
- recorte autenticado de mercados nos quais o usuário já fez previsão
- recorte autenticado de mercados favoritados pelo usuário
- curtida autenticada de mercado limitada a uma por usuário
- ordenações rápidas no feed web por tendência, abertura, fechamento, volume, curtidas, novidade e recorte de resolvidos
- carregamento incremental client-side dos cards renderizados em blocos de 18 itens
- destaque de probabilidade agregada
- mini gráfico de evolução do consenso por opção
- contador compacto de curtidas no card do mercado
- navegação para detalhe
- métricas públicas de economia educativa na home

## Escopo excluído

- streaming em tempo real

## Fluxo do usuário

Usuário acessa o feed, filtra mercados, identifica oportunidades de previsão e entra no detalhe da pergunta escolhida.

## Comportamento esperado

- feed exibe mercados coerentes com o status
- mercados fechados ou resolvidos permanecem legíveis
- mercados cancelados não aparecem na página inicial nem no feed público padrão
- categorias ajudam recorrência e descoberta
- cards exibem CTA `Prever` para mercados abertos, incluindo múltipla escolha
- títulos dos cards de mercado também navegam para o detalhe, reduzindo atrito além do CTA principal
- cards exibem curtidas reais do mercado como sinal social discreto
- usuário autenticado pode curtir/descurtir cada mercado uma única vez; a ação atualiza o contador sem recarregar a página
- visitante vê o contador de curtidas no mesmo slot visual, mas ao tentar curtir recebe aviso de que a ação exige login
- mini gráficos refletem histórico real de previsões persistidas, sem SVG estático de tendência
- mini gráficos devem continuar refletindo histórico após resolução; previsões `resolved` permanecem na série visual e previsões `canceled` ficam fora
- labels mostram percentuais inteiros, enquanto barras e mini gráficos usam `probability_exact`
- botão `Trending` ordena por mercados mais visualizados, com mercado mais recente como desempate
- botões `Novos`, `Aberto`, `Encerrado`, `Mais volume` e `Mais curtidas` reordenam ou filtram a lista no frontend sem recarregar a página
- botão `Aberto` mostra apenas cards com `status=open`, usando os cards já renderizados e sem recarregar a página
- botão `Encerrado` mostra apenas cards com `status=locked`, usando os cards já renderizados e sem recarregar a página
- botão `Resolvidos` no feed público mostra apenas cards com `status=resolved`, usando os cards já renderizados e sem recarregar a página
- feed mostra inicialmente até 18 cards por recorte e revela mais 18 a cada acionamento de `Carregar mais`
- `Favoritos` é um recorte pessoal autenticado de mercados salvos pelo usuário
- usuário autenticado pode acionar `Minhas previsões` para ver apenas cards de mercados onde já registrou previsão
- usuário autenticado pode favoritar/desfavoritar mercados públicos diretamente no card
- visitante não vê o filtro `Favoritos` nem ação de favoritar
- visitante não vê o filtro `Minhas previsões`
- o card principal do feed exibe os dois mercados publicados não cancelados mais visualizados por `view_count`, excluindo `draft` e `canceled`, com mercado mais novo como desempate
- a hero do feed exibe métricas compactas, incluindo total real de previsões persistidas, total de `O₵` distribuídas e total de `O₵` movimentadas em previsões, sem filtrar por mês
- a métrica `O₵ distribuídas` exclui créditos destinados a `staff` e `superuser`, evitando inflar economia pública com saldos operacionais internos
- métricas públicas de moeda devem usar o símbolo de apresentação `O₵`; campos e identificadores técnicos permanecem com sufixo `_oc`
- o texto da home deve preservar o contexto educativo e evitar termos que sugiram dinheiro real, trading ou saque
- prévias públicas fora do feed, como o ticket de onboarding no cadastro, podem reutilizar mercados serializados pelo domínio como sinal social; para cadastro, usa maior `view_count` entre publicados não cancelados, exclui `draft` e `canceled`, e usa o mais recente por `created_at` como desempate/fallback

## Regras de domínio

- o feed deve refletir estados vindos do domínio
- probabilidades exibidas são informativas, não editáveis pela UI
- mercados `canceled` não aparecem no feed público padrão
- mercados `draft` e `canceled` não entram no card principal; mercados `resolved` podem entrar se liderarem por `view_count`, com CTA de visualização
- mercados cancelados não podem permanecer marcados como destaque editorial
- no máximo dois mercados podem ficar marcados como destaque editorial ao mesmo tempo
- mercados de múltipla escolha iniciam com probabilidades decimais iguais para todas as opções, sem vantagem artificial por sobra de arredondamento
- categorias e subcategorias não possuem exclusão física operacional; itens retirados do uso devem ser bloqueados logicamente
- categorias/subcategorias bloqueadas permanecem preservadas para histórico, mas não podem ser usadas em novos mercados ou reclassificações administrativas

## Responsabilidades por camada

- `frontend-web`: listagem, ordenações rápidas, cards, destaque principal e carregamento incremental/interações parciais
- `backend-api`: busca, filtros públicos, favoritos pessoais, curtidas de mercado, estatísticas públicas e serialização
- `database`: índices por status, categoria, datas relevantes, favoritos por usuário e curtidas por usuário

## Implementação atual

- mercados públicos persistidos em PostgreSQL como fonte principal
- seed inicial baseado no fixture de domínio
- `GET /markets` expõe feed público com filtros por status, categoria e subcategoria; sem filtro explícito, exclui `draft` e `canceled`
- `GET /markets` marca `viewer_has_prediction=true` quando recebe sessão válida e o usuário possui previsão no mercado
- `GET /markets` marca `viewer_has_favorite=true` quando recebe sessão válida e o usuário favoritou o mercado
- `GET /markets` marca `viewer_has_like=true` quando recebe sessão válida e o usuário curtiu o mercado
- `POST /markets/{slug}/favorite` e `DELETE /markets/{slug}/favorite` permitem favoritar/desfavoritar de forma idempotente
- `POST /markets/{slug}/like` e `DELETE /markets/{slug}/like` permitem curtir/descurtir de forma idempotente
- `MarketResponse` expõe `is_featured`, `market_like_count`, `view_count`, `created_at` e `close_at` para seleção visual, destaque e ordenação client-side
- `MarketResponse` expõe `view_count` e `share_count` como métricas de popularidade usadas no Admin Ops e na seleção pública de destaques/onboarding
- `GET /admin/markets` aceita ordenação operacional por `order=views_desc` e `order=shares_desc` para apoiar curadoria por popularidade
- Django renderiza atributos `data-*` nos cards para ordenar e filtrar sem reload: destaque, favoritos pessoais, curtidas, visualizações, volume, datas e status
- cards consomem `sparkline_series` quando disponível e hidratam pelo Postgres local quando a API entrega payload antigo
- cadastro renderiza um ticket de onboarding com o mercado publicado não cancelado mais visualizado, excluindo `draft` e `canceled`, incluindo mini gráfico por `sparkline_series`, opções e retorno estimado meramente ilustrativo
- filtros rápidos do feed são implementados em JavaScript leve sobre a lista já renderizada; o modo `Resolvidos` oculta temporariamente cards que não estejam resolvidos
- o modo `Mais curtidas` ordena por `market_like_count`, com mercado mais recente como desempate
- o modo `Favoritos` usa `viewer_has_favorite` já serializado, sem nova mutação nem recálculo de domínio no navegador
- o modo `Minhas previsões` usa `viewer_has_prediction` já serializado, sem nova mutação nem recálculo de domínio no navegador
- controle `Carregar mais` do feed atua sobre a lista filtrada/ordenada no cliente, sem chamada adicional ao backend
- `GET /stats` expõe métricas públicas da home: `open_markets`, `total_predictions`, `distributed_oc`, `moved_oc`, `resolution_sla` e `real_money`
- a métrica pública `previsões totais` é calculada a partir de `orynth_predictions` persistidas, sem janela mensal
- a métrica pública `O₵ distribuídas` soma créditos positivos registrados no ledger de wallet de usuários comuns, excluindo operadores (`staff`/`superuser`), e é enviada como label pronto para apresentação
- a métrica pública `O₵ movimentadas` soma stakes de previsões registradas e é enviada como label pronto para apresentação
- browse administrativo de mercados usa fallback local em Postgres quando a API administrativa falha, mantendo a visualização de ativos/rascunhos disponível em desenvolvimento
- browse administrativo de mercados exibe popularidade em indicadores compactos e permite alternar entre ordem padrão, mais visualizados e mais compartilhados
- Admin Ops gerencia categorias/subcategorias em tela de browse operacional com criação, edição, bloqueio/desbloqueio e indicação visual de estado
- bloqueio de taxonomia é persistido em PostgreSQL e validado pela FastAPI antes de criar/editar mercados
- Django consome a FastAPI e usa Postgres local como fallback de desenvolvimento para mercado, opções, consenso, wallet e ranking

## Dados e persistência

- mercado
- categoria com estado de bloqueio lógico
- subcategoria com estado de bloqueio lógico
- snapshot resumido de probabilidade
- `is_featured` no mercado para curadoria editorial do feed
- `orynth_market_favorites` guarda favoritos pessoais com unicidade por usuário e mercado
- `orynth_market_likes` guarda curtidas reais do mercado com unicidade por usuário e mercado
- `market_like_count` derivado de curtidas reais em `orynth_market_likes`; likes em comentários não alimentam esse contador
- `created_at` e `close_at` para ordenações rápidas
- `view_count` e `share_count` para ordenações operacionais no Admin Ops
- série visual derivada de previsões para mini gráfico do card
- `viewer_has_prediction` derivado da sessão autenticada para personalização de leitura do feed
- `viewer_has_favorite` derivado da sessão autenticada para personalização de leitura do feed
- `viewer_has_like` derivado da sessão autenticada para personalização da ação de curtida do card

## Contratos afetados

- `market-lifecycle.md`
- `i18n-content.md`
- `wallet-ledger.md`

## I18n e conteúdo

- títulos e rótulos de filtros devem ser localizáveis

## Observabilidade e operação

- medir uso de filtros e CTR do feed para detalhe
- medir visualizações de detalhe e ações de compartilhamento por mercado para apoio operacional/admin

## Testes esperados

- integração para filtros por status/categoria
- renderização dos modos de ordenação rápida e do recorte `Resolvidos` no feed web
- regressão para o modo `Mais curtidas` ordenando por curtidas reais do mercado
- regressão para métrica de previsões totais baseada em previsões persistidas reais
- regressão para métricas públicas de `O₵ distribuídas` e `O₵ movimentadas` na home e no contrato `/stats`, garantindo exclusão de créditos de operadores na distribuição
- renderização de `data-*` de ordenação e contador de curtidas no card
- regressão para título do card como link para o detalhe do mercado
- regressão para contadores operacionais de visualizações/compartilhamentos expostos no contrato e ocultos do feed público
- regressão para ordenação administrativa por mercados mais visualizados e mais compartilhados
- seleção do card principal por `view_count`, excluindo `draft` e `canceled`, com desempate por mercado mais recente
- seleção do ticket de onboarding do cadastro por `view_count`, excluindo `draft` e `canceled`, com desempate por mercado mais recente
- regressão para cancelados fora da lista padrão do feed e fora do card principal
- regressão para `viewer_has_prediction` autenticado no contrato de listagem
- regressão para favoritos pessoais autenticados no contrato de listagem e endpoints idempotentes
- regressão para curtidas reais autenticadas no contrato de listagem e endpoints idempotentes, garantindo uma curtida por usuário/mercado
- renderização do filtro `Favoritos` apenas para usuário logado, com estado vazio quando não houver favoritos
- renderização do filtro `Minhas previsões` apenas para usuário logado, com estado vazio quando não houver cards previstos
- regressão para carregamento incremental do feed em blocos de 18 cards e reset do recorte ao trocar filtros
- integração para bloqueio/desbloqueio de categoria e subcategoria
- criação/edição administrativa de mercado deve rejeitar taxonomia bloqueada
- fluxo de navegação feed -> detalhe
- regressão para cards com payload antigo sem sparkline

## Critérios de aceite

- usuário encontra mercados por categoria e status
- usuário consegue reordenar a lista por tendência baseada em visualizações, volume, curtidas e novidade sem recarregar
- usuário consegue alternar para o recorte de mercados abertos sem recarregar
- usuário consegue alternar para o recorte de mercados encerrados (`locked`) sem recarregar
- usuário consegue alternar para o recorte de mercados resolvidos sem recarregar
- usuário autenticado consegue alternar para o recorte `Minhas previsões` sem recarregar
- usuário autenticado consegue favoritar mercados e alternar para o recorte `Favoritos` sem recarregar
- usuário autenticado consegue curtir/descurtir cada mercado uma vez, sem recarregar
- usuário carrega mais mercados em blocos de 18 cards sem recarregar
- cards exibem informações mínimas coerentes
- título e CTA principal levam ao detalhe do mercado
- cards exibem curtidas em singular/plural correto e com contraste em light/dark mode
- destaque principal exibe até dois mercados publicados não cancelados mais visualizados, excluindo `draft` e `canceled`, incluindo resolvidos quando liderarem por popularidade
- home exibe métricas públicas de economia educativa com `O₵ distribuídas` e `O₵ movimentadas em previsões`, sem sugerir dinheiro real
- créditos de `staff`/`superuser` não entram no número público de `O₵ distribuídas`

## Impacto de mudança

Mudanças aqui podem afetar descoberta, categorias e contratos de listagem consumidos também pelo admin.
