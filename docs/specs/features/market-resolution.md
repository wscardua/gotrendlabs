---
id: FEAT-RES-001
titulo: "Resolução de mercado"
versao: 0.1
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-05-18
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - market-lifecycle.md
  - wallet-ledger.md
  - reputation-ranking.md
  - domain-events.md
dependencias:
  - FEAT-PRED-001
  - FEAT-WALLET-001
  - FEAT-REP-001
impacta:
  - backend-api
  - database
  - scheduler-jobs
  - communications
  - admin-ops
aprovacao: pendente
---

# Resolução de mercado

## Objetivo

Permitir fechamento e definição do resultado de um mercado, com aplicação consistente de efeitos financeiros, reputacionais e de comunicação.

## Escopo incluído

- travar mercado
- resolver manualmente
- registrar evidência e operador
- aplicar efeitos em wallet e reputação
- desfazer resolução operacionalmente quando necessário, retornando o mercado para fechado

## Escopo excluído

- resolução totalmente descentralizada
- arbitragem pública complexa

## Fluxo do usuário

Mercado é fechado na data prevista, operador revisa e define a opção vencedora, o sistema aplica payouts, atualiza reputação e comunica o resultado.

## Comportamento esperado

- só mercados elegíveis podem ser resolvidos
- resolução gera trilha auditável
- resultado fica visível no detalhe do mercado
- operador informa opção vencedora, fonte pública, justificativa, data/hora efetiva e timezone controlado no Admin Ops
- browse de resolução lista mercados `locked` e `resolved`, mostra data/hora/timezone quando houver resolução e permite ordenar por resolução recente, resolução antiga ou pendências

## Regras de domínio

- resolução exige estado compatível
- resolução manual exige evidência pública e justificativa operacional na UI administrativa; a API aceita pelo menos um dos dois para compatibilidade operacional
- `resolved_at` representa o momento efetivo da decisão e deve ser armazenado com timezone normalizado; `resolution_timezone` preserva o timezone selecionado para exibição/auditoria
- timezone de resolução deve vir de lista controlada no Admin Ops; texto livre não deve ser usado para evitar registros inválidos
- payout usa `reward_bruto = stake * (1 / p)`, onde `p` é `probability_at_entry` como fração decimal
- reputação usa `K=10`: acerto aplica `delta_R = K * (1 - p)`; erro aplica `delta_R = -K * p`
- reputação mínima é `0` e só muda em resolução, nunca em cancelamento
- cancelamento aplica refund total dos stakes bloqueados e não gera payout nem alteração de reputação
- cancelamento administrativo deve falhar como inconsistência operacional se, após o refund, ainda houver previsão `open` no mercado
- reconciliação de mercado cancelado é operação excepcional para dados já inconsistentes; ela cancela previsões órfãs `open`, cria refunds ausentes de forma idempotente e registra `market.cancel_reconcile`
- desfazer resolução retorna o mercado para `locked`, estorna payout líquido, rebloqueia stakes e recalcula reputação

## Responsabilidades por camada

- `backend-api`: regras de transição e aplicação de efeitos
- `database`: estado final, evidência, operador, lançamentos e histórico
- `scheduler-jobs`: lock automático
- `communications`: notificação de resultado
- `admin-ops`: revisão e resolução operacional

## Dados e persistência

- resolução
- evidência
- `resolved_at`
- `resolution_timezone`
- estado do mercado
- efeitos financeiros
- efeitos reputacionais
- `prediction_refund` para devolução/liberação de stake
- `prediction_payout` para crédito líquido de acerto
- `prediction_loss` para baixa auditável de stake perdido
- `prediction_payout_reversal` para estornar ganho líquido ao desfazer resolução
- `prediction_resolution_relock` para rebloquear stake ao desfazer resolução

## Contratos afetados

- `market-lifecycle.md`
- `wallet-ledger.md`
- `reputation-ranking.md`
- `domain-events.md`

## I18n e conteúdo

- resolução pública deve ser compatível com múltiplos idiomas

## Observabilidade e operação

- trilha administrativa obrigatória
- métricas de tempo até resolução
- comando operacional de reconciliação deve oferecer modo `dry-run` antes de aplicar correção em mercado cancelado com previsões abertas

## Testes esperados

- unitários para transições de estado
- integração de resolução com wallet e reputação
- fluxo de lock automático + resolução administrativa
- regressão para mercado `canceled` com previsão `open` órfã, validando refund, saldo, reputação inalterada e idempotência

## Critérios de aceite

- mercado resolvido reflete corretamente opção vencedora e efeitos associados
- mercado cancelado devolve 100% dos stakes bloqueados e preserva reputação
- mercado resolvido com resolução desfeita retorna para `locked` e fica pronto para nova decisão

## Impacto de mudança

Alta sensibilidade; mudanças afetam contratos centrais e múltiplas features dependentes.
