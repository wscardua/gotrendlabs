# Contrato: Wallet e Ledger

## Modelo

- `gotrendlabs_wallet_ledger` é a fonte auditável das mutações da wallet.
- `gotrendlabs_wallet_balances` é a projeção operacional para leitura rápida do saldo atual.
- A wallet exibida ao usuário deve ser reconciliável com a razão de transações.
- Cada mutação relevante gera uma entrada de ledger.
- Cada mutação relevante atualiza ledger e projeção de saldo na mesma transação.

## Tipos iniciais de lançamento

- `grant_initial`
- `prediction_stake_lock`
- `prediction_refund`
- `prediction_payout`
- `prediction_loss`
- `prediction_revision_penalty`
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
- `entry_type_label`
- `amount`
- `direction`
- `direction_label`
- `reference_type`
- `reference_id`
- `created_at`
- `created_by`

### Balance

- `user_id`
- `available_gtl`
- `locked_gtl`
- `total_earned_gtl`
- `updated_at`

## Regras

- O saldo exibido deve ser conciliável com o ledger.
- Contratos de leitura para usuário final devem expor `entry_type_label` e `direction_label` em linguagem clara, preservando `entry_type` e `direction` para rastreabilidade técnica.
- Leituras frequentes de saldo devem usar `gotrendlabs_wallet_balances`.
- Em caso de divergência, `gotrendlabs_wallet_ledger` vence e a projeção deve ser reconstruída.
- Ajustes manuais exigem operador e justificativa.
- Ajustes manuais administrativos usam `entry_type="manual_adjustment"`, `reference_type="admin_user_adjustment"` e `reference_id` com o id do usuário afetado.
- Ajustes manuais aceitam apenas `direction="credit"` ou `direction="debit"` sobre saldo disponível; débito maior que `available_gtl` deve ser rejeitado.
- Ajustes manuais administrativos devem registrar `user.wallet_adjust` em `gotrendlabs_admin_events` e preencher `created_by`.
- Ajustes manuais administrativos podem ter `created_by` igual ao usuário afetado quando o operador é `staff`/`superuser`; a auditoria continua obrigatória.
- Toda referência deve apontar para o objeto causal quando houver.
- `prediction_stake_lock` deve reduzir `available_gtl`, aumentar `locked_gtl` e apontar para `reference_type="prediction"`.
- `prediction_refund` deve usar `direction="release"` e devolver stake bloqueado para saldo disponível.
- Refund de cancelamento deve ser idempotente por previsão enquanto não houver novo `lock`/`prediction_resolution_relock` posterior; isso evita duplicidade em reconciliações e preserva o caso de resolução desfeita seguida de cancelamento final.
- `prediction_payout` deve usar `direction="credit"` e representar ganho líquido acima do stake liberado.
- `prediction_payout_reversal` deve usar `direction="debit"` para estornar ganho líquido quando uma resolução for desfeita.
- `prediction_resolution_relock` deve usar `direction="lock"` para rebloquear stake quando uma resolução for desfeita.
- `prediction_loss` deve usar `direction="settle"` e baixar stake bloqueado sem alterar saldo disponível.
- `prediction_revision_penalty` deve usar `direction="debit"` e registrar o custo educativo de revisão sobre o valor ativo abandonado.
- Revisão de posição deve liberar as posições ativas antigas, debitar a penalidade quando configurada e bloquear a nova posição restante na mesma transação.
- `reward_feedback` deve ser `credit`, usar `reference_type="feedback"` e apontar para o feedback revisado.
- `reward_suggestion` deve ser `credit`, usar `reference_type="suggestion"` e apontar para a sugestão revisada.
- `educational_recharge` deve ser `credit`, usar `reference_type="wallet_recharge_request"` e apontar para a solicitação aprovada.
- Recompensas operacionais exigem usuário cadastrado e valor inteiro positivo.
- Uma recompensa operacional não pode ser registrada mais de uma vez para o mesmo `entry_type`, `reference_type` e `reference_id`.
- Recompensas por feedback ou sugestão não geram reputação.
- Recarga educativa aprovada não gera reputação nem incrementa `total_earned_gtl`.
- Solicitação de recarga educativa deve ser bloqueada quando `available_gtl` for maior que `gotrendlabs_site_config.wallet_recharge_min_balance_gtl`.
- Usuário pode manter no máximo uma solicitação de recarga educativa `pending`; novas solicitações ficam bloqueadas até aprovação ou rejeição administrativa.
- O agregado público `distributed_gtl` usado pela home soma apenas lançamentos `direction="credit"` do ledger de usuários comuns, excluindo usuários `staff` e `superuser`, incluindo `grant_initial`, recompensas operacionais, recargas educativas aprovadas, ajustes manuais de crédito e payouts líquidos desses usuários.
- Agregados públicos derivados do ledger não expõem usuário, saldo individual nem extrato, e não substituem a projeção `gotrendlabs_wallet_balances`.
