---
id: FEAT-MARKET-002
titulo: "Detalhe do mercado"
versao: 0.1
status_spec: draft
status_impl: nao_iniciada
ultima_atualizacao: 2026-05-17
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - market-lifecycle.md
  - prediction-payloads.md
  - i18n-content.md
dependencias:
  - FEAT-MARKET-001
impacta:
  - frontend-web
  - backend-api
  - database
aprovacao: pendente
---

# Detalhe do mercado

## Objetivo

Exibir a pergunta do mercado, opções disponíveis, contexto, probabilidade agregada, comentários e ações de previsão.

## Escopo incluído

- visão detalhada do mercado
- alternativas de resposta
- estado atual do mercado
- entrada para comentários e previsão

## Escopo excluído

- gráficos financeiros avançados
- live updates complexos

## Fluxo do usuário

Usuário entra no mercado, entende o contexto, avalia opções, acompanha comentários e decide prever.

## Comportamento esperado

- opções disponíveis variam conforme o tipo do mercado
- estado do mercado governa disponibilidade de ação
- resolução final fica visível quando existir

## Regras de domínio

- o contrato do detalhe deve expor apenas dados consistentes com o estado
- mercado `locked` não aceita novas previsões

## Responsabilidades por camada

- `frontend-web`: layout do detalhe, interação parcial e mensagens
- `backend-api`: resposta detalhada do mercado e validação de estados
- `database`: mercado, opções, comentários agregados e resolução

## Dados e persistência

- mercado
- opções
- resultado/resolução
- comentários vinculados

## Contratos afetados

- `market-lifecycle.md`
- `prediction-payloads.md`
- `i18n-content.md`

## I18n e conteúdo

- conteúdo textual do mercado deve permitir localização futura

## Observabilidade e operação

- medir visão de detalhe, taxa de previsão e leitura de resolução

## Testes esperados

- integração do detalhe por tipo de mercado
- fluxo de detalhe com mercado aberto, locked e resolved

## Critérios de aceite

- usuário entende estado, opções e ação disponível sem ambiguidade

## Impacto de mudança

Mudanças neste contrato impactam previsão, comentários e compartilhamento.
