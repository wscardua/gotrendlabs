# Contrato: Wallet e Ledger

## Modelo

- `orynth_wallet_ledger` é a fonte auditável das mutações da wallet.
- `orynth_wallet_balances` é a projeção operacional para leitura rápida do saldo atual.
- A wallet exibida ao usuário deve ser reconciliável com a razão de transações.
- Cada mutação relevante gera uma entrada de ledger.
- Cada mutação relevante atualiza ledger e projeção de saldo na mesma transação.

## Tipos iniciais de lançamento

- `grant_initial`
- `prediction_stake_lock`
- `prediction_refund`
- `prediction_payout`
- `prediction_loss`
- `prediction_payout_reversal`
- `prediction_resolution_relock`
- `manual_adjustment`
- `reward_feedback`
- `reward_suggestion`
- `educational_recharge`

## Campos mínimos

### Ledger

- `entry_id`
- `user_id`
- `entry_type`
- `amount`
- `direction`
- `reference_type`
- `reference_id`
- `created_at`
- `created_by`

### Balance

- `user_id`
- `available_oc`
- `locked_oc`
- `total_earned_oc`
- `updated_at`

## Regras

- O saldo exibido deve ser conciliável com o ledger.
- Leituras frequentes de saldo devem usar `orynth_wallet_balances`.
- Em caso de divergência, `orynth_wallet_ledger` vence e a projeção deve ser reconstruída.
- Ajustes manuais exigem operador e justificativa.
- Ajustes manuais administrativos usam `entry_type="manual_adjustment"`, `reference_type="admin_user_adjustment"` e `reference_id` com o id do usuário afetado.
- Ajustes manuais aceitam apenas `direction="credit"` ou `direction="debit"` sobre saldo disponível; débito maior que `available_oc` deve ser rejeitado.
- Ajustes manuais administrativos devem registrar `user.wallet_adjust` em `orynth_admin_events` e preencher `created_by`.
- Toda referência deve apontar para o objeto causal quando houver.
- `prediction_stake_lock` deve reduzir `available_oc`, aumentar `locked_oc` e apontar para `reference_type="prediction"`.
- `prediction_refund` deve usar `direction="release"` e devolver stake bloqueado para saldo disponível.
- Refund de cancelamento deve ser idempotente por previsão enquanto não houver novo `lock`/`prediction_resolution_relock` posterior; isso evita duplicidade em reconciliações e preserva o caso de resolução desfeita seguida de cancelamento final.
- `prediction_payout` deve usar `direction="credit"` e representar ganho líquido acima do stake liberado.
- `prediction_payout_reversal` deve usar `direction="debit"` para estornar ganho líquido quando uma resolução for desfeita.
- `prediction_resolution_relock` deve usar `direction="lock"` para rebloquear stake quando uma resolução for desfeita.
- `prediction_loss` deve usar `direction="settle"` e baixar stake bloqueado sem alterar saldo disponível.
- `reward_feedback` deve ser `credit`, usar `reference_type="feedback"` e apontar para o feedback revisado.
- `reward_suggestion` deve ser `credit`, usar `reference_type="suggestion"` e apontar para a sugestão revisada.
- `educational_recharge` deve ser `credit`, usar `reference_type="wallet_recharge_request"` e apontar para a solicitação aprovada.
- Recompensas operacionais exigem usuário cadastrado e valor inteiro positivo.
- Uma recompensa operacional não pode ser registrada mais de uma vez para o mesmo `entry_type`, `reference_type` e `reference_id`.
- Recompensas por feedback ou sugestão não geram reputação.
- Recarga educativa aprovada não gera reputação nem incrementa `total_earned_oc`.
- Solicitação de recarga educativa deve ser bloqueada quando `available_oc` for maior que `orynth_site_config.wallet_recharge_min_balance_oc`.
- Usuário pode manter no máximo uma solicitação de recarga educativa `pending`; novas solicitações ficam bloqueadas até aprovação ou rejeição administrativa.
