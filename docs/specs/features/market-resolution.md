---
id: FEAT-RES-001
titulo: "Resolução de mercado"
versao: 0.1
status_spec: draft
status_impl: nao_iniciada
ultima_atualizacao: 2026-05-17
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

## Escopo excluído

- resolução totalmente descentralizada
- arbitragem pública complexa

## Fluxo do usuário

Mercado é fechado na data prevista, operador revisa e define a opção vencedora, o sistema aplica payouts, atualiza reputação e comunica o resultado.

## Comportamento esperado

- só mercados elegíveis podem ser resolvidos
- resolução gera trilha auditável
- resultado fica visível no detalhe do mercado

## Regras de domínio

- resolução exige estado compatível
- payout e ajustes dependem da política de produto
- cancelamento precisa de política explícita de refund

## Responsabilidades por camada

- `backend-api`: regras de transição e aplicação de efeitos
- `database`: estado final, evidência, operador, lançamentos e histórico
- `scheduler-jobs`: lock automático
- `communications`: notificação de resultado
- `admin-ops`: revisão e resolução operacional

## Dados e persistência

- resolução
- evidência
- estado do mercado
- efeitos financeiros
- efeitos reputacionais

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

## Testes esperados

- unitários para transições de estado
- integração de resolução com wallet e reputação
- fluxo de lock automático + resolução administrativa

## Critérios de aceite

- mercado resolvido reflete corretamente opção vencedora e efeitos associados

## Impacto de mudança

Alta sensibilidade; mudanças afetam contratos centrais e múltiplas features dependentes.
