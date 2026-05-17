---
id: FEAT-REP-001
titulo: "Reputação e ranking"
versao: 0.1
status_spec: draft
status_impl: nao_iniciada
ultima_atualizacao: 2026-05-17
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - reputation-ranking.md
dependencias:
  - FEAT-RES-001
impacta:
  - frontend-web
  - backend-api
  - database
aprovacao: pendente
---

# Reputação e ranking

## Objetivo

Exibir desempenho acumulado do usuário e ranking social de forma compreensível e comparável.

## Escopo incluído

- score de reputação
- posição no ranking
- histórico resumido de desempenho

## Escopo excluído

- ligas complexas
- temporadas e resets avançados

## Fluxo do usuário

Usuário acompanha sua evolução e compara desempenho com outros participantes após mercados resolvidos.

## Comportamento esperado

- ranking reflete previsões resolvidas
- perfil e tela de ranking usam o mesmo contrato base

## Regras de domínio

- reputação depende de resultados resolvidos
- mudanças de fórmula exigem decisão técnica registrada

## Responsabilidades por camada

- `frontend-web`: ranking, perfil e explicação superficial
- `backend-api`: cálculo e exposição do score
- `database`: materialização ou persistência auxiliar quando necessário

## Dados e persistência

- score atual
- posição
- contadores derivados

## Contratos afetados

- `reputation-ranking.md`

## I18n e conteúdo

- textos explicativos devem evitar linguagem financeira ou de aposta real

## Observabilidade e operação

- medir distribuição de score e estabilidade da fórmula

## Testes esperados

- unitários para agregação e ordenação
- integração para atualização após resolução

## Critérios de aceite

- usuário consegue ver posição e evolução coerente com resultados resolvidos

## Impacto de mudança

Mudanças nesta feature podem reclassificar histórico e exigem cuidado com comunicação ao usuário.
