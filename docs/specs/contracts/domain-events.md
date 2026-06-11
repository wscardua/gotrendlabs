# Contrato: Eventos de Domínio

## Objetivo

Definir eventos produzidos pelo domínio e consumidos por subsistemas como comunicações, scheduler e observabilidade.

## Eventos iniciais

- `user.registered`
- `user.email_confirmation`
- `account.password_reset`
- `prediction.created`
- `market.locked`
- `market.resolved`
- `market.canceled`
- `market.resolution_undone`
- `feedback.submitted`
- `suggestion.submitted`
- `wallet.credited`
- `badge.awarded`
- `notification.created`
- `email.delivery_queued`
- `push.delivery_queued`

## Eventos administrativos persistidos

- `comment.hide`
- `comment.restore`
- `market.resolve`
- `market.cancel`
- `market.cancel_reconcile`
- `market.resolution_undo`

Esses eventos são registrados em `gotrendlabs_admin_events` nas primeiras fatias de comentários e resolução. Eles preservam operador, entidade, justificativa e momento, mas ainda não representam emissão assíncrona no envelope de eventos de domínio.

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
- A primeira fatia de comentários persiste moderação administrativa; ações sociais persistem notificações in-app em `gotrendlabs_user_notifications`, mas `comment.created`, `comment.reacted` e eventos assíncronos equivalentes seguem pendentes até existir event bus dedicado.
- `user.welcome`, `user.email_confirmation`, `account.password_reset`, `market.locked`, `market.resolved` e `wallet.credited` podem criar entregas transacionais idempotentes em `communications_emaildelivery` antes do event bus dedicado.
- `market.locked`, `market.resolved`, `wallet.credited` e `badge.awarded` podem persistir notificações in-app para destinatários humanos diretamente afetados antes do event bus dedicado.
- `notification.created` representa persistência de inbox in-app e usa `source_key` idempotente por destinatário, sem envio externo obrigatório.
- `email.delivery_queued` representa persistência da outbox transacional e usa `idempotency_key` única; eventos críticos de identidade/acesso podem tentar envio imediato filtrado após commit, enquanto eventos de produto continuam dependentes do daemon.
- `push.delivery_queued` representa persistência da outbox mobile por `UserNotification` e dispositivo, sem garantir envio FCM imediato.
- Push mobile só pode ser derivado de `notification.created`; política por evento decide se a notificação persistida vira push imediato, digest futuro ou nenhum envio.
