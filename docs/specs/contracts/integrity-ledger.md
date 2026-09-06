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

## Endpoints

- `GET /markets/{slug}/integrity`
- `GET /markets/{slug}/integrity/verify`
- `GET /markets/{slug}/integrity/package`
- `GET /markets/{slug}/predictions/{prediction_id}/receipt`
- `GET /markets/{slug}/predictions/{prediction_id}/merkle-proof`
- `GET /integrity/public-key`

`GET /markets/{slug}/integrity/verify` retorna, alem dos campos v1 existentes, `definition_matches_current`, `result_matches_current`, `prediction_commitments_valid` e `market_events_valid`. Os campos sao booleanos quando aplicaveis e `null` quando a etapa ainda nao existe. `valid` resume as provas do mercado; `ledger_chain_valid` informa separadamente a cadeia global para que falha historica externa ao mercado nao seja atribuida silenciosamente a ele. `errors` contem somente inconsistencias que invalidam a prova especifica do mercado; observacoes globais que nao mudam `valid` ficam em `warnings`. Indisponibilidade de transporte/KMS e retry de selagem permanecem estados operacionais separados.

Recibos de previsao exigem que o usuario autenticado seja dono da previsao. A prova publica nunca lista previsoes ou identificadores de usuarios.

O daemon reutiliza a mesma verificacao criptografica autoritativa em modo interno, sem rate limit HTTP, como primeira rotina de cada ciclo e sobre todos os mercados nativos, nao apenas mercados selados. Falhas especificas do mercado e falha da cadeia global geram itens `integrity_alert` no contrato staff de filas. Esses itens possuem severidade fixa `high`, status operacional, codigo da divergencia, mercado opcional, primeira/ultima deteccao e numero de ocorrencias. O item e deduplicado enquanto representar o mesmo escopo e tipo de falha.

## Erros

- `404`: mercado/prova inexistente
- `403`: recibo nao pertence ao usuario
- `409`: prova Merkle ainda indisponivel antes de `sealed`
- `422`: estado de dominio incompativel
- `503`: signer indisponivel em mutacao; nenhuma mutacao parcial e confirmada
