---
id: FEAT-MARKET-001
titulo: "Feed de mercados"
versao: 0.5
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-05-20
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - market-lifecycle.md
  - i18n-content.md
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
- ordenações rápidas no feed web por tendência, fechamento, volume, novidade, favoritos editoriais e recorte de resolvidos
- destaque de probabilidade agregada
- mini gráfico de evolução do consenso por opção
- contador compacto de curtidas no card do mercado
- navegação para detalhe

## Escopo excluído

- filtros personalizados por usuário autenticado
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
- cards exibem curtidas agregadas do mercado como sinal social discreto
- mini gráficos refletem histórico real de previsões persistidas, sem SVG estático de tendência
- mini gráficos devem continuar refletindo histórico após resolução; previsões `resolved` permanecem na série visual e previsões `canceled` ficam fora
- labels mostram percentuais inteiros, enquanto barras e mini gráficos usam `probability_exact`
- botões `Trending`, `Encerrando`, `Mais volume`, `Novos` e `Favoritos` reordenam a lista no frontend sem recarregar a página
- botão `Resolvidos` no feed público mostra apenas cards com `status=resolved`, usando os cards já renderizados e sem recarregar a página
- `Favoritos` no feed público significa mercados destacados pela curadoria, não favoritos salvos por usuário
- o card principal do feed exibe os dois mercados publicados não cancelados mais visualizados por `view_count`, excluindo `draft` e `canceled`, com mercado mais novo como desempate
- a hero do feed exibe métricas compactas, incluindo total real de previsões persistidas, sem filtrar por mês
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

- `frontend-web`: listagem, ordenações rápidas, cards, destaque principal e paginação/interações parciais
- `backend-api`: busca, filtros públicos, contagem agregada de curtidas e serialização
- `database`: índices por status, categoria e datas relevantes

## Implementação atual

- mercados públicos persistidos em PostgreSQL como fonte principal
- seed inicial baseado no fixture de domínio
- `GET /markets` expõe feed público com filtros por status, categoria e subcategoria; sem filtro explícito, exclui `draft` e `canceled`
- `MarketResponse` expõe `is_featured`, `market_like_count`, `view_count`, `created_at` e `close_at` para seleção visual, destaque e ordenação client-side
- `MarketResponse` expõe `view_count` e `share_count` como métricas de popularidade usadas no Admin Ops e na seleção pública de destaques/onboarding
- `GET /admin/markets` aceita ordenação operacional por `order=views_desc` e `order=shares_desc` para apoiar curadoria por popularidade
- Django renderiza atributos `data-*` nos cards para ordenar e filtrar sem reload: destaque, curtidas, volume, datas e status
- cards consomem `sparkline_series` quando disponível e hidratam pelo Postgres local quando a API entrega payload antigo
- cadastro renderiza um ticket de onboarding com o mercado publicado não cancelado mais visualizado, excluindo `draft` e `canceled`, incluindo mini gráfico por `sparkline_series`, opções e retorno estimado meramente ilustrativo
- filtros rápidos do feed são implementados em JavaScript leve sobre a lista já renderizada; o modo `Resolvidos` oculta temporariamente cards que não estejam resolvidos
- a métrica pública `previsões totais` é calculada a partir de `orynth_predictions` persistidas, sem janela mensal
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
- `market_like_count` derivado de reações `like` em comentários visíveis
- `created_at` e `close_at` para ordenações rápidas
- `view_count` e `share_count` para ordenações operacionais no Admin Ops
- série visual derivada de previsões para mini gráfico do card

## Contratos afetados

- `market-lifecycle.md`
- `i18n-content.md`

## I18n e conteúdo

- títulos e rótulos de filtros devem ser localizáveis

## Observabilidade e operação

- medir uso de filtros e CTR do feed para detalhe
- medir visualizações de detalhe e ações de compartilhamento por mercado para apoio operacional/admin

## Testes esperados

- integração para filtros por status/categoria
- renderização dos modos de ordenação rápida e do recorte `Resolvidos` no feed web
- regressão para métrica de previsões totais baseada em previsões persistidas reais
- renderização de `data-*` de ordenação e contador de curtidas no card
- regressão para título do card como link para o detalhe do mercado
- regressão para contadores operacionais de visualizações/compartilhamentos expostos no contrato e ocultos do feed público
- regressão para ordenação administrativa por mercados mais visualizados e mais compartilhados
- seleção do card principal por `view_count`, excluindo `draft` e `canceled`, com desempate por mercado mais recente
- seleção do ticket de onboarding do cadastro por `view_count`, excluindo `draft` e `canceled`, com desempate por mercado mais recente
- regressão para cancelados fora da lista padrão do feed e fora do card principal
- integração para bloqueio/desbloqueio de categoria e subcategoria
- criação/edição administrativa de mercado deve rejeitar taxonomia bloqueada
- fluxo de navegação feed -> detalhe
- regressão para cards com payload antigo sem sparkline

## Critérios de aceite

- usuário encontra mercados por categoria e status
- usuário consegue reordenar a lista por tendência, encerramento, volume, novidade e favoritos editoriais sem recarregar
- usuário consegue alternar para o recorte de mercados resolvidos sem recarregar
- cards exibem informações mínimas coerentes
- título e CTA principal levam ao detalhe do mercado
- cards exibem curtidas em singular/plural correto e com contraste em light/dark mode
- destaque principal exibe até dois mercados publicados não cancelados mais visualizados, excluindo `draft` e `canceled`, incluindo resolvidos quando liderarem por popularidade

## Impacto de mudança

Mudanças aqui podem afetar descoberta, categorias e contratos de listagem consumidos também pelo admin.
