# Contrato: Ledger de Integridade

O contrato normativo da primeira versao esta em `FEAT-INTEGRITY-001` e usa `protocol_version=gtl-integrity/v1`.

## Resumo de mercado

- `integrity.status`
- `integrity.protocol_version`
- `integrity.definition_registered`
- `integrity.verification_available`
- `integrity.key_fingerprint`
- `published_at`, `seal_due_at`, `sealed_at`

O registro append-only `integrity_signing_keys` preserva somente a chave publica, algoritmo e fingerprint de cada `key_id`; chave privada nunca e persistida pelo produto.

`integrity.status` usa `seal_retry_pending` para indisponibilidade operacional de selagem e reserva `verification_failed` para diferenca criptografica detectada. `canceled_preserved` evita apresentar mercados cancelados como eternamente pendentes.

Mercado ativo sem `market_integrity_definitions` e inconsistencia operacional: nao aceita previsao nem selagem e deve ser removido pelo corte controlado do ambiente pre-producao. `legacy_unregistered` nao faz parte do catalogo normal apos esse corte.

## Endpoints

- `GET /markets/{slug}/integrity`
- `GET /markets/{slug}/integrity/verify`
- `GET /admin/markets/{slug}/integrity/verify` (staff, auditoria operacional read-only)
- `GET /markets/{slug}/integrity/package`
- `GET /markets/{slug}/predictions/{prediction_id}/receipt`
- `GET /markets/{slug}/predictions/{prediction_id}/merkle-proof`
- `GET /integrity/public-key`
- `GET /integrity/status`

`GET /markets/{slug}/integrity/verify` retorna `verification_status`, `market_valid`, `ledger_chain_valid`, `overall_valid`, `definition_matches_current`, `result_matches_current`, `prediction_commitments_valid`, `market_events_valid`, sequencias global verificada/atual, eventos pendentes, horario e tipo da auditoria. Booleanos sao `null` quando ainda nao existe evidencia suficiente. `verified` exige mercado e cadeia validos ate o head atual; `pending` significa eventos posteriores ao checkpoint e usa `ledger_chain_valid=null`/`overall_valid=null`; `failed` representa divergencia confirmada e `unavailable` ausencia/falha operacional do checkpoint. Nenhuma consulta publica executa full scan do ledger.

`GET /integrity/status` expoe o mesmo resumo global sem dados de mercado. A resposta valida o checkpoint assinado antes de usa-lo.

Recibos de previsao exigem que o usuario autenticado seja dono da previsao. A prova publica nunca lista previsoes, eventos `prediction_committed`, IDs/referencias/timestamps individuais nem identificadores de usuarios. `prediction_commitments` expoe somente `count`, `included_in_seal` e `predictions_root` agregado quando o Seal existir.

O endpoint staff reutiliza o mesmo verificador de `GET /markets/{slug}/integrity/verify`, exige operador autenticado e nao passa pelo limite publico compartilhado. Ele nao altera mercado, prova, alerta ou evento ao ser consultado.

O daemon reutiliza o verificador autoritativo como primeira rotina de cada ciclo: valida o checkpoint, processa o delta e cria nova atestacao assinada; no bootstrap ou a cada 24 horas executa auditoria integral. Seal sempre exige nova auditoria integral sob lock, independentemente da idade do checkpoint. Divergencia global identica no mesmo head usa backoff de uma hora sem novo checkpoint/assinatura a cada ciclo, mas continua atualizando o alerta operacional deduplicado. Mercado em estado publicado (`open`, `locked`, `resolved`, `sealed` ou `canceled`) sem definicao obrigatoria gera `definition_missing`; `draft`/`scheduled` sem definicao permanecem etapas esperadas.

A verificacao exige cobertura exata entre `gotrendlabs_predictions` e `prediction_commitments`, inclusive para usuarios `is_bot=true`. A unicidade de `prediction_id` impede duplicidade no banco; previsao sem compromisso produz `prediction_commitment_missing`, enquanto compromisso orfao ou divergente produz `prediction_commitment_invalid`. Qualquer caso impede o Seal.

## Erros

- `404`: mercado/prova inexistente
- `403`: recibo nao pertence ao usuario
- `409`: prova Merkle ainda indisponivel antes de `sealed`
- `422`: estado de dominio incompativel
- `503`: signer indisponivel em mutacao; nenhuma mutacao parcial e confirmada
