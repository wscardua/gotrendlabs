# Contrato: Ciclo de Vida de Mercado

## Estados canônicos

- `draft`: mercado ainda não publicado
- `scheduled`: publicado com abertura futura
- `open`: recebendo previsões
- `locked`: fechado para novas previsões e aguardando resolução
- `resolved`: resultado definido e efeitos aplicados
- `canceled`: encerrado sem resultado válido

## Regras

- Apenas `open` aceita novas previsões.
- A transição `open -> locked` pode ser manual ou automática via scheduler.
- A transição `locked -> resolved` exige operador ou processo autorizado e evidência.
- `canceled` deve definir política de devolução de stake e comunicação associada.

## Campos mínimos expostos

- `market_id`
- `status`
- `resolution_type`
- `close_at`
- `resolved_at`
- `winning_option_id`
- `resolution_note`
