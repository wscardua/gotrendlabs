# Contrato: Eventos de Domínio

## Objetivo

Definir eventos produzidos pelo domínio e consumidos por subsistemas como comunicações, scheduler e observabilidade.

## Eventos iniciais

- `user.registered`
- `prediction.created`
- `market.locked`
- `market.resolved`
- `market.canceled`
- `market.resolution_undone`
- `feedback.submitted`
- `suggestion.submitted`

## Eventos administrativos persistidos

- `comment.hide`
- `comment.restore`
- `market.resolve`
- `market.cancel`
- `market.cancel_reconcile`
- `market.resolution_undo`

Esses eventos são registrados em `orynth_admin_events` nas primeiras fatias de comentários e resolução. Eles preservam operador, entidade, justificativa e momento, mas ainda não representam emissão assíncrona no envelope de eventos de domínio.

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
- A primeira fatia de filas operacionais persiste sugestões e feedbacks, mas a emissão assíncrona dedicada destes eventos ainda é pendente.
- A primeira fatia de comentários persiste moderação administrativa, mas `comment.created`, `comment.reacted` e eventos assíncronos equivalentes seguem pendentes até existir event bus dedicado.
