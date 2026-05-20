---
id: FEAT-COMMENT-001
titulo: "Comentários"
versao: 0.1
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-05-18
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - domain-events.md
  - i18n-content.md
dependencias:
  - FEAT-AUTH-001
  - FEAT-MARKET-002
impacta:
  - frontend-web
  - backend-api
  - database
  - admin-ops
aprovacao: pendente
---

# Comentários

## Objetivo

Adicionar camada social simples aos mercados por meio de comentários vinculados à pergunta.

## Escopo incluído

- criar comentário
- listar comentários
- moderação básica
- curtir e descurtir comentários

## Escopo excluído

- chat em tempo real
- respostas/thread de comentários no MVP
- seguidores
- denúncias por usuários

## Fluxo do usuário

Usuário autenticado comenta em um mercado e visualiza a discussão associada.

## Comportamento esperado

- comentários seguem moderação mínima
- mercado resolvido continua exibindo discussão histórica
- comentários ocultos por moderação deixam de aparecer publicamente, mas permanecem preservados para operação
- cada usuário autenticado pode manter no máximo uma reação ativa por comentário: `like` ou `dislike`
- a UI pública identifica o autor pelo handle iniciado com `@`
- visitantes veem um convite de login para comentar, sem formulário mutável

## Regras de domínio

- comentário precisa estar vinculado a mercado e autor
- conteúdos moderados precisam preservar trilha operacional
- comentários novos entram como `visible`
- moderação administrativa alterna entre `visible` e `hidden` com nota operacional
- `draft` e `canceled` não aceitam novos comentários
- mercados `open`, `locked` e `resolved` aceitam comentários
- likes e dislikes são reações mutuamente exclusivas por usuário e comentário
- Django/Admin Ops não devem criar, reagir ou moderar comentário localmente quando a FastAPI estiver indisponível.

## Responsabilidades por camada

- `frontend-web`: UI de leitura, envio, CTA de login para visitante e ações iconizadas de reação
- `backend-api`: criação, listagem, reação e moderação lógica
- `database`: persistência de comentários, reações e estado de moderação
- `admin-ops`: listagem em fila operacional, ocultação/restauração e registro administrativo

## Dados e persistência

- comentário
- autor
- mercado
- estado de moderação
- nota de moderação, moderador e timestamps
- reação por usuário e comentário
- constraint única para uma reação por usuário em cada comentário

## Contratos afetados

- `domain-events.md`
- `i18n-content.md`

## API e interface pública

- `GET /markets/{slug}/comments`
- `POST /markets/{slug}/comments`
- `POST /comments/{id}/like`
- `DELETE /comments/{id}/like`
- `POST /comments/{id}/dislike`
- `DELETE /comments/{id}/dislike`
- `GET /admin/comments`
- `PATCH /admin/comments/{id}/moderation`
- `MarketResponse.comments` retorna comentários visíveis com contagem de `like`/`dislike` e reação do usuário autenticado quando houver sessão.
- Likes/dislikes de comentários são reações internas dos comentários e não alimentam `market_like_count` do mercado.

## I18n e conteúdo

- mensagens de moderação e limites de UI localizados

## Observabilidade e operação

- métricas de volume e fila de moderação

## Testes esperados

- integração de criação e listagem
- fluxo de moderação simples
- bloqueio de comentário anônimo e em mercado inválido
- alternância de `like`/`dislike` sem duplicidade
- renderização web pública e ação administrativa

## Critérios de aceite

- usuários autenticados conseguem comentar
- moderação consegue ocultar conteúdo com rastreabilidade
- comentários ocultos não aparecem no detalhe público
- comentários visíveis aparecem em mercados abertos, fechados e resolvidos
- usuários autenticados conseguem alternar uma reação por comentário

## Impacto de mudança

Mudanças tendem a afetar moderação e carga operacional mais do que contratos financeiros.
