---
id: FEAT-MARKET-001
titulo: "Feed de mercados"
versao: 0.1
status_spec: draft
status_impl: nao_iniciada
ultima_atualizacao: 2026-05-17
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
- filtros por status e categoria
- destaque de probabilidade agregada
- navegação para detalhe

## Escopo excluído

- ordenação avançada por trading
- streaming em tempo real

## Fluxo do usuário

Usuário acessa o feed, filtra mercados, identifica oportunidades de previsão e entra no detalhe da pergunta escolhida.

## Comportamento esperado

- feed exibe mercados coerentes com o status
- mercados fechados ou resolvidos permanecem legíveis
- categorias ajudam recorrência e descoberta

## Regras de domínio

- o feed deve refletir estados vindos do domínio
- probabilidades exibidas são informativas, não editáveis pela UI

## Responsabilidades por camada

- `frontend-web`: listagem, filtros e paginação/interações parciais
- `backend-api`: busca, filtros, ordenação e serialização
- `database`: índices por status, categoria e datas relevantes

## Dados e persistência

- mercado
- categoria
- snapshot resumido de probabilidade

## Contratos afetados

- `market-lifecycle.md`
- `i18n-content.md`

## I18n e conteúdo

- títulos e rótulos de filtros devem ser localizáveis

## Observabilidade e operação

- medir uso de filtros e CTR do feed para detalhe

## Testes esperados

- integração para filtros por status/categoria
- fluxo de navegação feed -> detalhe

## Critérios de aceite

- usuário encontra mercados por categoria e status
- cards exibem informações mínimas coerentes

## Impacto de mudança

Mudanças aqui podem afetar descoberta, categorias e contratos de listagem consumidos também pelo admin.
