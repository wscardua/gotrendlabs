---
id: FEAT-PRED-001
titulo: "Previsão e stake"
versao: 0.1
status_spec: draft
status_impl: nao_iniciada
ultima_atualizacao: 2026-05-17
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - prediction-payloads.md
  - wallet-ledger.md
  - market-lifecycle.md
dependencias:
  - FEAT-AUTH-001
  - FEAT-MARKET-002
  - FEAT-WALLET-001
impacta:
  - frontend-web
  - backend-api
  - database
  - communications
aprovacao: pendente
---

# Previsão e stake

## Objetivo

Permitir que o usuário escolha uma opção em um mercado aberto e aplique stake usando moeda interna.

## Escopo incluído

- seleção de opção
- entrada de stake
- validação de saldo
- confirmação da previsão
- atualização do snapshot de probabilidade

## Escopo excluído

- trading em tempo real
- revenda de posição

## Fluxo do usuário

Usuário autenticado acessa um mercado aberto, escolhe uma opção, informa stake, confirma a ação e recebe retorno com saldo e snapshot atualizados.

## Comportamento esperado

- mercado fechado bloqueia a ação
- saldo insuficiente retorna erro claro
- confirmação registra a previsão e o impacto financeiro correspondente

## Regras de domínio

- stake só pode usar saldo disponível
- cada previsão deve ficar vinculada a mercado, opção e usuário
- a mutação financeira deve ser refletida no ledger

## Responsabilidades por camada

- `frontend-web`: formulário, confirmação e feedback
- `backend-api`: validação, registro de previsão, atualização de snapshot e ledger
- `database`: previsões, lançamentos de wallet, histórico
- `communications`: confirmação de previsão quando definido

## Dados e persistência

- previsão
- stake aplicado
- snapshot de resultado
- entrada de ledger associada

## Contratos afetados

- `prediction-payloads.md`
- `wallet-ledger.md`
- `market-lifecycle.md`

## I18n e conteúdo

- mensagens de validação e confirmação precisam ser localizadas

## Observabilidade e operação

- registrar taxa de erro por saldo e mercado fechado

## Testes esperados

- unitários para validação de stake
- integração de previsão com ledger
- fluxo completo de confirmação

## Critérios de aceite

- previsão válida gera registro e efeito financeiro coerente
- previsões inválidas retornam erro previsível

## Impacto de mudança

Mudanças nesta feature impactam wallet, probabilidades, comunicações e, em certos casos, reputação futura.
