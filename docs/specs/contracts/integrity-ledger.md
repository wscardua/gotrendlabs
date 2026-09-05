# Contrato: Ledger de Integridade

O contrato normativo da primeira versao esta em `FEAT-INTEGRITY-001` e usa `protocol_version=gtl-integrity/v1`.

## Resumo de mercado

- `integrity.status`
- `integrity.protocol_version`
- `integrity.definition_registered`
- `integrity.verification_available`
- `integrity.key_fingerprint`
- `published_at`, `seal_due_at`, `sealed_at`

## Endpoints

- `GET /markets/{slug}/integrity`
- `GET /markets/{slug}/integrity/verify`
- `GET /markets/{slug}/integrity/package`
- `GET /markets/{slug}/predictions/{prediction_id}/receipt`
- `GET /markets/{slug}/predictions/{prediction_id}/merkle-proof`
- `GET /integrity/public-key`

Recibos de previsao exigem que o usuario autenticado seja dono da previsao. A prova publica nunca lista previsoes ou identificadores de usuarios.

## Erros

- `404`: mercado/prova inexistente
- `403`: recibo nao pertence ao usuario
- `409`: prova Merkle ainda indisponivel antes de `sealed`
- `422`: estado de dominio incompativel
- `503`: signer indisponivel em mutacao; nenhuma mutacao parcial e confirmada
