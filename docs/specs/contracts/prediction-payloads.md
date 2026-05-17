# Contrato: Prediction Payloads

## Criar previsão

Entrada mínima:

- `market_id`
- `option_id`
- `stake_amount`
- `client_locale`

Saída mínima:

- `prediction_id`
- `market_id`
- `option_id`
- `stake_amount`
- `accepted_at`
- `wallet_balance_after`
- `market_probability_snapshot`

## Regras

- O `stake_amount` deve respeitar saldo disponível e limites definidos.
- O contrato deve devolver erros claros para saldo insuficiente, mercado fechado, opção inválida e sessão inválida.
- O snapshot retornado precisa ser compatível com o frontend, mas a fonte de verdade permanece no backend.
