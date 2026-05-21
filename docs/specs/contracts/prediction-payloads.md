# Contrato: Prediction Payloads

## Criar previsão

Entrada mínima:

- `market_id` ou `market_slug` conforme rota pública consumida
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
- `potential_payout`

## Prévia de previsão

`POST /markets/{slug}/prediction-preview`

Entrada mínima:

- `option_id`
- `stake_amount`
- `client_locale`

Saída mínima:

- `market_id`
- `option_id`
- `stake_amount`
- `probability_exact`
- `estimated_return`

A prévia não cria previsão, não altera wallet/ledger e não persiste alteração de probabilidade.

## Mercado com visualização de consenso

Campos derivados esperados nas respostas de mercado usadas pelo frontend:

- `options[].id`
- `options[].probability`
- `options[].probability_exact`
- `options[].sparkline_path`
- `primary_probability`
- `primary_probability_exact`
- `secondary_probability`
- `secondary_probability_exact`
- `resolved_at`
- `resolved_at_label`
- `resolution_timezone`
- `winning_option_id`
- `resolution_note`
- `viewer_has_prediction`
- `viewer_has_favorite`
- `viewer_has_like`
- `sparkline_series`
- `sparkline_path`
- `sparkline_area_path`

## Regras

- O `stake_amount` deve respeitar saldo disponível e limites definidos.
- O contrato deve devolver erros claros para saldo insuficiente, mercado fechado, opção inválida, sessão inválida e previsão duplicada no mesmo mercado.
- O frontend não deve enviar previsão sem `option_id`; a UI deve iniciar sem seleção padrão e usar validação nativa obrigatória para escolha explícita.
- O snapshot retornado precisa ser compatível com o frontend, mas a fonte de verdade permanece no backend.
- A prévia de retorno deve vir do `backend-api`; cálculos no navegador são apenas estado visual temporário e não autoritativo.
- `probability` é inteiro de display; cálculos, barras e gráficos devem usar `probability_exact`.
- Em múltipla escolha, a soma dos inteiros exibidos pode ser menor que `100` quando a divisão exata não é inteira.
- `potential_payout` é informativo até a resolução aplicar payout real.
- Séries visuais devem ser derivadas das previsões persistidas e podem ser recalculadas sob demanda enquanto não houver tabela materializada de snapshots.
- Séries visuais devem considerar previsões `open` e `resolved`; previsões `canceled` não participam do histórico visual.
- `resolved_at_label` é campo de apresentação derivado de `resolved_at` + `resolution_timezone`; cálculos e ordenação devem usar `resolved_at`.
