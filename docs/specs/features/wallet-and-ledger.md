---
id: FEAT-WALLET-001
titulo: "Wallet e extrato"
versao: 0.2
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-05-19
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
- recompensas operacionais aprovadas para feedback e sugestão de mercado
- ajuste manual auditado por staff no detalhe administrativo de usuário

## Escopo excluído

- saque, depósito real ou blockchain
- recompensa para visitante sem conta cadastrada

## Fluxo do usuário

Usuário consulta wallet para entender saldo disponível, stakes aplicados, retornos e recompensas.

## Comportamento esperado

- saldo e extrato são consistentes
- saldo é exibido por projeção operacional reconciliável com ledger
- usuário consegue entender a origem de cada lançamento

## Regras de domínio

- ledger é a fonte auditável da wallet
- saldo exibido deve vir de projeção de leitura rápida reconciliável com ledger
- toda mutação de wallet deve atualizar ledger e projeção na mesma transação
- lançamentos manuais exigem justificativa
- ajuste manual administrativo exige escolha explícita de direção (`credit` ou `debit`), sem seleção padrão no formulário
- ajuste manual administrativo deve usar `manual_adjustment`, `created_by`, `reference_type="admin_user_adjustment"` e registrar evento `user.wallet_adjust`
- débito manual não pode exceder saldo disponível
- recompensa operacional exige usuário cadastrado, valor inteiro positivo e referência ao item revisado
- a mesma fila operacional não pode gerar crédito mais de uma vez para o mesmo item
- recompensa por feedback ou sugestão não altera reputação
- cancelamento de mercado com previsão aberta gera refund total por `prediction_refund`
- resolução vencedora libera stake e credita apenas o ganho líquido por `prediction_payout`
- resolução perdedora baixa o stake bloqueado por `prediction_loss` sem devolver saldo disponível
- desfazer resolução estorna payout líquido por `prediction_payout_reversal` e rebloqueia stake por `prediction_resolution_relock`

## Responsabilidades por camada

- `frontend-web`: visão de saldo e extrato
- `backend-api`: leitura consolidada e regras de consistência
- `database`: ledger e referências
- `admin-ops`: ajustes manuais permitidos e auditados
- `queues`: aprovações operacionais que disparam crédito rastreável

## Dados e persistência

- ledger de wallet
- projeção de saldo atual
- referências a previsões, payouts, reversões, ajustes e recompensas operacionais

## Contratos afetados

- `wallet-ledger.md`

## I18n e conteúdo

- valores e descrições localizados

## Observabilidade e operação

- relatórios de inconsistência entre saldo derivado e projeção

## Testes esperados

- unitários para agregação do ledger
- integração para previsão, refund e payout
- integração para `reward_feedback` e `reward_suggestion`
- integração para ajuste manual administrativo com crédito, débito, nota obrigatória, bloqueio de saldo insuficiente e auditoria
- fluxo de visualização do extrato
- bloqueio de recompensa operacional duplicada

## Critérios de aceite

- saldo exibido bate com o extrato
- toda movimentação possui causa rastreável
- crédito operacional aprovado aparece no extrato e atualiza saldo disponível
- ajuste manual administrativo aparece no ledger, atualiza a projeção e preserva operador/justificativa

## Impacto de mudança

Mudanças afetam previsão, resolução, recompensas e suporte operacional.
