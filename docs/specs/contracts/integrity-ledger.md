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

`GET /markets/{slug}/integrity/verify` retorna, alem dos campos v1 existentes, `definition_matches_current`, `result_matches_current`, `prediction_commitments_valid` e `market_events_valid`. Os campos sao booleanos quando aplicaveis e `null` quando a etapa ainda nao existe. `prediction_commitments_valid` passa a ser aplicavel desde que exista definicao nativa assinada, permitindo auditoria administrativa durante `open`, `locked` e `resolved`, sem expor previsoes ou identidades. Seal, resultado final e Merkle permanecem `null` antes de suas respectivas etapas. `valid` exige simultaneamente as provas aplicaveis do mercado e `ledger_chain_valid=true`: uma cadeia global invalida nunca pode produzir verificacao positiva nem permitir Seal. `errors` contem inconsistencias da prova especifica do mercado; `warnings` pode contextualizar uma falha global sem atribui-la ao mercado, mas essa separacao de apresentacao nao altera o resultado `valid=false`. Indisponibilidade de transporte/KMS e retry de selagem permanecem estados operacionais separados.

Recibos de previsao exigem que o usuario autenticado seja dono da previsao. A prova publica nunca lista previsoes ou identificadores de usuarios.

O endpoint staff reutiliza o mesmo verificador de `GET /markets/{slug}/integrity/verify`, exige operador autenticado e nao passa pelo limite publico compartilhado. Ele nao altera mercado, prova, alerta ou evento ao ser consultado.

O daemon reutiliza a mesma verificacao criptografica autoritativa em modo interno, sem rate limit HTTP, como primeira rotina de cada ciclo e sobre todos os mercados, nao apenas os que ja possuem definicao ou Seal. Mercado em estado publicado (`open`, `locked`, `resolved`, `sealed` ou `canceled`) sem definicao obrigatoria gera `definition_missing`; `draft`/`scheduled` sem definicao permanecem etapas esperadas. Falhas especificas do mercado e falha da cadeia global geram itens `integrity_alert` no contrato staff de filas. Esses itens possuem severidade fixa `high`, status operacional, codigo da divergencia, mercado opcional, primeira/ultima deteccao e numero de ocorrencias. O item e deduplicado enquanto representar o mesmo escopo e tipo de falha.

A verificacao exige cobertura exata entre `gotrendlabs_predictions` e `prediction_commitments`, inclusive para usuarios `is_bot=true`. A unicidade de `prediction_id` impede duplicidade no banco; previsao sem compromisso produz `prediction_commitment_missing`, enquanto compromisso orfao ou divergente produz `prediction_commitment_invalid`. Qualquer caso impede o Seal.

## Erros

- `404`: mercado/prova inexistente
- `403`: recibo nao pertence ao usuario
- `409`: prova Merkle ainda indisponivel antes de `sealed`
- `422`: estado de dominio incompativel
- `503`: signer indisponivel em mutacao; nenhuma mutacao parcial e confirmada
