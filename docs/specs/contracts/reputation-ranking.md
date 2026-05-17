# Contrato: Reputação e Ranking

## Objetivo

Padronizar a forma como o sistema expõe reputação acumulada e ranking social sem acoplar a UX a uma fórmula fixa antes da implementação.

## Campos mínimos

- `user_id`
- `reputation_score`
- `ranking_position`
- `resolved_predictions_count`
- `accuracy_indicator`
- `last_updated_at`

## Regras

- A fórmula pode evoluir, mas as mudanças precisam ser registradas em decisão técnica.
- O ranking deve ser explicável o suficiente para suporte e operação.
- O histórico público não pode depender apenas de posição agregada; deve haver lastro em previsões resolvidas.
