---
id: FEAT-SUGGEST-001
titulo: "Sugestões de mercado"
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
impacta:
  - frontend-web
  - backend-api
  - database
  - admin-ops
  - communications
aprovacao: pendente
---

# Sugestões de mercado

## Objetivo

Permitir que usuários enviem sugestões de perguntas para futura curadoria administrativa.

## Escopo incluído

- envio de sugestão
- confirmação de recebimento
- fila administrativa

## Escopo excluído

- publicação automática
- marketplace aberto de criação

## Fluxo do usuário

Usuário autenticado preenche proposta de mercado, envia e recebe confirmação; a sugestão entra em fluxo administrativo.

## Comportamento esperado

- sugestões ficam pendentes até revisão
- admin consegue classificar e reaproveitar conteúdo

## Regras de domínio

- usuário comum não publica mercado diretamente
- histórico de sugestão precisa ser rastreável

## Responsabilidades por camada

- `frontend-web`: formulário e confirmação
- `backend-api`: validação e persistência
- `database`: sugestão e status
- `admin-ops`: revisão, descarte ou promoção a rascunho
- `communications`: confirmação eventual

## Dados e persistência

- sugestão
- autor
- status de revisão
- feedback administrativo

## Contratos afetados

- `domain-events.md`
- `i18n-content.md`

## I18n e conteúdo

- campos textuais devem prever tradução assistida futura quando aplicável

## Observabilidade e operação

- medir volume, taxa de aproveitamento e backlog

## Testes esperados

- integração de submissão
- fluxo administrativo básico

## Critérios de aceite

- usuário consegue enviar sugestão
- operação consegue rastrear e revisar a fila

## Impacto de mudança

Mudanças aqui afetam principalmente admin, comunicações e possíveis pipelines de conteúdo.
