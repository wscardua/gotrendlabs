# Contrato: Eventos de Domínio

## Objetivo

Definir eventos produzidos pelo domínio e consumidos por subsistemas como comunicações, scheduler e observabilidade.

## Eventos iniciais

- `user.registered`
- `prediction.created`
- `market.locked`
- `market.resolved`
- `market.canceled`
- `feedback.submitted`
- `suggestion.submitted`

## Campos mínimos do envelope

- `event_id`
- `event_type`
- `occurred_at`
- `actor_type`
- `actor_id`
- `subject_type`
- `subject_id`
- `payload_version`

## Regras

- Eventos devem ser estáveis o suficiente para consumo assíncrono.
- Mudanças de shape exigem versionamento do payload ou compatibilidade explícita.
