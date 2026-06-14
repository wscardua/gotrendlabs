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

## Reforço e revisão de posição

`POST /markets/{slug}/position-preview`

Entrada mínima:

- `action`: `reinforcement` ou `revision`
- `option_id`
- `stake_amount` para reforço; em revisão v1 o valor é ignorado e a nova posição usa o saldo ativo após penalidade
- `client_locale`

Saída mínima:

- `market_id`
- `option_id`
- `action`
- `stake_amount`
- `active_stake_amount`
- `active_position_count`
- `penalty_amount`
- `revision_penalty_percent`
- `new_position_stake_amount`
- `position_total_after`
- `probability_exact`
- `estimated_return`
- `reinforcement_remaining`
- `revision_remaining`
- `allowed`
- `blocked_reason`

`POST /markets/{slug}/position-actions`

Entrada mínima:

- `action`: `reinforcement` ou `revision`
- `option_id`
- `stake_amount` para reforço; revisão usa o valor ativo agregado menos penalidade
- `client_locale`

Saída mínima:

- `prediction_id`
- `market_id`
- `option_id`
- `action`
- `stake_amount`
- `penalty_amount`
- `accepted_at`
- `wallet_balance_after`
- `market_probability_snapshot`
- `potential_payout`
- `viewer_position`

`POST /markets/{slug}/predict` permanece reservado para a primeira previsão do usuário no mercado. Usuário que já possui histórico nesse mercado deve usar os contratos de reforço/revisão.

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
- `viewer_position`
- `viewer_has_favorite`
- `viewer_has_like`
- `market_like_count`
- `comment_count`
- `sparkline_series`
- `sparkline_path`
- `sparkline_area_path`

## Regras

- O `stake_amount` deve respeitar saldo disponível e limites definidos.
- O contrato deve devolver erros claros para saldo insuficiente, mercado fechado, opção inválida, sessão inválida, tentativa de usar `/predict` após a primeira previsão e ações de posição inelegíveis.
- Reforço mantém a mesma opção ativa, respeita `position_reinforcement_max_count` e cria nova posição `open` sem penalidade.
- Revisão troca para uma opção diferente, supersede posições ativas anteriores, aplica o percentual de custo configurado para troca de posição e cria nova posição `open` com o valor restante.
- `viewer_position` deve expor posição ativa agregada, entradas abertas resumidas, limite/restante de reforços, limite/restante de revisões, percentual de custo de revisão, custo estimado em GT₵ e nova posição estimada para a UI explicar o que será encerrado antes da confirmação.
- Cada entrada, reforço ou revisão gera linha própria em `gotrendlabs_predictions`; posições substituídas ficam como `revised` com `superseded_by` e `superseded_at`.
- Mutações de posição devem ser serializadas por usuário/mercado em lock transacional; a checagem de `/predict` precisa ocorrer depois desse lock para impedir duas previsões iniciais concorrentes quando ainda não existe linha bloqueável.
- O frontend não deve enviar previsão sem `option_id`; a UI deve iniciar sem seleção padrão e usar validação nativa obrigatória para escolha explícita.
- O snapshot retornado precisa ser compatível com o frontend, mas a fonte de verdade permanece no backend.
- A prévia de retorno deve vir do `backend-api`; cálculos no navegador são apenas estado visual temporário e não autoritativo.
- `probability` é inteiro de display; cálculos, barras e gráficos devem usar `probability_exact`.
- Em múltipla escolha, a soma dos inteiros exibidos pode ser menor que `100` quando a divisão exata não é inteira.
- `potential_payout` é informativo até a resolução aplicar payout real.
- Séries visuais devem ser derivadas das previsões persistidas e podem ser recalculadas sob demanda enquanto não houver tabela materializada de snapshots.
- Séries visuais devem considerar previsões `open` e `resolved`; previsões `revised` entram no ponto de criação e saem no ponto `superseded_at`; previsões `canceled` não participam do histórico visual.
- `resolved_at_label` é campo de apresentação derivado de `resolved_at` + `resolution_timezone`; cálculos e ordenação devem usar `resolved_at`.
- Previsões bot oficiais são `Prediction` reais de usuários `is_bot=true`, criadas somente pelo backend/daemon quando flags e limites permitirem.
- Previsão bot é bloqueada quando `human_participants=0` ou abaixo de `ai_min_humans_for_prediction`.
- Respostas de mercado expõem `human_participants`, `bot_participants`, `human_volume_gtl`, `bot_volume_gtl` e `total_volume_gtl`; `participants` e `volume_gtl` legados representam humanos.
