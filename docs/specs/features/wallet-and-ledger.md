---
id: FEAT-WALLET-001
titulo: "Wallet e extrato"
versao: 0.5
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-05-21
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
- solicitação de recarga educativa com aprovação ou rejeição administrativa
- ajuste manual auditado por staff no detalhe administrativo de usuário
- agregado público de `GT₵` distribuídas para métricas educativas da home

## Escopo excluído

- saque, depósito real ou blockchain
- recompensa para visitante sem conta cadastrada

## Fluxo do usuário

Usuário consulta wallet para entender saldo disponível, stakes aplicados, retornos e recompensas.

## Comportamento esperado

- saldo e extrato são consistentes
- saldo é exibido por projeção operacional reconciliável com ledger
- usuário consegue entender a origem de cada lançamento
- extrato autenticado exibe rótulos humanos para tipo e direção, sem mostrar códigos técnicos como `prediction_payout` ou `reward_referral` na carteira educativa
- extrato usa `Carregar mais` em lotes cumulativos de 10 lançamentos

## Regras de domínio

- ledger é a fonte auditável da wallet
- saldo exibido deve vir de projeção de leitura rápida reconciliável com ledger
- toda mutação de wallet deve atualizar ledger e projeção na mesma transação
- lançamentos manuais exigem justificativa
- ajuste manual administrativo exige escolha explícita de direção (`credit` ou `debit`), sem seleção padrão no formulário
- ajuste manual administrativo deve usar `manual_adjustment`, `created_by`, `reference_type="admin_user_adjustment"` e registrar evento `user.wallet_adjust`
- staff/superuser pode executar ajuste manual sobre a própria wallet, mantendo nota operacional, ledger e auditoria; isso não libera autoações sensíveis de sessão/status/papel
- débito manual não pode exceder saldo disponível
- recompensa operacional exige usuário cadastrado, valor inteiro positivo e referência ao item revisado
- a mesma fila operacional não pode gerar crédito mais de uma vez para o mesmo item
- recompensa por feedback ou sugestão não altera reputação
- solicitação de recarga educativa só pode ser criada quando o saldo disponível do usuário estiver menor ou igual ao piso `wallet_recharge_min_balance_gtl` configurado em Admin Ops
- usuário pode ter no máximo uma solicitação de recarga educativa `pending`
- recarga educativa aprovada pelo Admin Ops exige valor inteiro positivo, operador e referência à solicitação
- recarga educativa usa `educational_recharge`, `direction="credit"` e `reference_type="wallet_recharge_request"`
- recarga educativa não altera reputação nem `total_earned_gtl`
- o agregado público `GT₵ distribuídas` deve contar lançamentos de ledger com `direction="credit"` apenas de usuários comuns, excluindo `staff` e `superuser`, incluindo grant inicial, recompensas, recargas aprovadas, ajustes manuais de crédito e payouts líquidos desses usuários comuns
- o agregado público de distribuição não expõe recortes por usuário nem substitui saldo, extrato ou projeção de wallet
- cancelamento de mercado com previsão aberta gera refund total por `prediction_refund`
- resolução vencedora libera stake e credita apenas o ganho líquido por `prediction_payout`
- resolução perdedora baixa o stake bloqueado por `prediction_loss` sem devolver saldo disponível
- revisão de posição libera stakes ativos antigos, debita `prediction_revision_penalty` quando configurado e bloqueia o stake restante da nova posição
- desfazer resolução estorna payout líquido por `prediction_payout_reversal` e rebloqueia stake por `prediction_resolution_relock`

## Responsabilidades por camada

- `frontend-web`: visão de saldo, extrato e apresentação de agregados públicos já calculados
- `backend-api`: leitura consolidada, estatísticas públicas e regras de consistência
- `database`: ledger e referências
- `admin-ops`: ajustes manuais permitidos e auditados
- `queues`: aprovações operacionais que disparam crédito rastreável

## Dados e persistência

- ledger de wallet
- projeção de saldo atual
- referências a previsões, payouts, reversões, ajustes e recompensas operacionais
- solicitações de recarga educativa com status, valor aprovado, nota e revisor
- parâmetro operacional `wallet_recharge_min_balance_gtl` em `gotrendlabs_site_config`

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
- integração para solicitação, bloqueio de duplicidade pendente, aprovação e rejeição de recarga educativa
- regressão para agregado público de `GT₵ distribuídas` baseado apenas em créditos do ledger de usuários não operadores
- regressão para ajuste manual da própria wallet por operador com auditoria
- fluxo de visualização do extrato
- bloqueio de recompensa operacional duplicada

## Critérios de aceite

- saldo exibido bate com o extrato
- toda movimentação possui causa rastreável
- crédito operacional aprovado aparece no extrato e atualiza saldo disponível
- recarga educativa aprovada aparece no extrato e atualiza saldo disponível sem alterar ganhos por acerto
- ajuste manual administrativo aparece no ledger, atualiza a projeção e preserva operador/justificativa
- home consegue exibir total público de `GT₵ distribuídas` sem revelar dados privados de wallet
- métricas públicas de distribuição não contam créditos internos de operadores

## Impacto de mudança

Mudanças afetam previsão, resolução, recompensas e suporte operacional.
