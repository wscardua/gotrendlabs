# Contrato: Wallet e Ledger

## Modelo

- A wallet do usuário é derivada de uma razão de transações.
- Cada mutação relevante gera uma entrada de ledger.

## Tipos iniciais de lançamento

- `grant_initial`
- `prediction_stake_lock`
- `prediction_refund`
- `prediction_payout`
- `manual_adjustment`
- `reward_feedback`

## Campos mínimos

- `entry_id`
- `user_id`
- `entry_type`
- `amount`
- `direction`
- `reference_type`
- `reference_id`
- `created_at`
- `created_by`

## Regras

- O saldo exibido deve ser conciliável com o ledger.
- Ajustes manuais exigem operador e justificativa.
- Toda referência deve apontar para o objeto causal quando houver.
