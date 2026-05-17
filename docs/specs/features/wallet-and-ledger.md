---
id: FEAT-WALLET-001
titulo: "Wallet e extrato"
versao: 0.1
status_spec: draft
status_impl: nao_iniciada
ultima_atualizacao: 2026-05-17
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - wallet-ledger.md
dependencias:
  - FEAT-AUTH-001
impacta:
  - frontend-web
  - backend-api
  - database
  - admin-ops
aprovacao: pendente
---

# Wallet e extrato

## Objetivo

Exibir saldo, histórico de movimentações e rastreabilidade da moeda interna do usuário.

## Escopo incluído

- saldo atual
- extrato
- referências às causas de cada lançamento

## Escopo excluído

- saque, depósito real ou blockchain

## Fluxo do usuário

Usuário consulta wallet para entender saldo disponível, stakes aplicados, retornos e recompensas.

## Comportamento esperado

- saldo e extrato são consistentes
- usuário consegue entender a origem de cada lançamento

## Regras de domínio

- saldo deve derivar do ledger
- lançamentos manuais exigem justificativa

## Responsabilidades por camada

- `frontend-web`: visão de saldo e extrato
- `backend-api`: leitura consolidada e regras de consistência
- `database`: ledger e referências
- `admin-ops`: ajustes manuais permitidos e auditados

## Dados e persistência

- ledger de wallet
- saldo derivado
- referências a previsões, payouts e ajustes

## Contratos afetados

- `wallet-ledger.md`

## I18n e conteúdo

- valores e descrições localizados

## Observabilidade e operação

- relatórios de inconsistência entre saldo derivado e projeção

## Testes esperados

- unitários para agregação do ledger
- integração para previsão, refund e payout
- fluxo de visualização do extrato

## Critérios de aceite

- saldo exibido bate com o extrato
- toda movimentação possui causa rastreável

## Impacto de mudança

Mudanças afetam previsão, resolução, recompensas e suporte operacional.
