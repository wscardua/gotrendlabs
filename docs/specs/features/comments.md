---
id: FEAT-COMMENT-001
titulo: "Comentários"
versao: 0.1
status_spec: draft
status_impl: nao_iniciada
ultima_atualizacao: 2026-05-17
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

## Escopo excluído

- chat em tempo real
- threads complexas
- seguidores

## Fluxo do usuário

Usuário autenticado comenta em um mercado e visualiza a discussão associada.

## Comportamento esperado

- comentários seguem moderação mínima
- mercado resolvido continua exibindo discussão histórica

## Regras de domínio

- comentário precisa estar vinculado a mercado e autor
- conteúdos moderados precisam preservar trilha operacional

## Responsabilidades por camada

- `frontend-web`: UI de leitura e envio
- `backend-api`: criação, listagem e moderação lógica
- `database`: persistência e estado de moderação
- `admin-ops`: revisão e ação administrativa

## Dados e persistência

- comentário
- autor
- mercado
- estado de moderação

## Contratos afetados

- `domain-events.md`
- `i18n-content.md`

## I18n e conteúdo

- mensagens de moderação e limites de UI localizados

## Observabilidade e operação

- métricas de volume e fila de moderação

## Testes esperados

- integração de criação e listagem
- fluxo de moderação simples

## Critérios de aceite

- usuários autenticados conseguem comentar
- moderação consegue ocultar conteúdo com rastreabilidade

## Impacto de mudança

Mudanças tendem a afetar moderação e carga operacional mais do que contratos financeiros.
