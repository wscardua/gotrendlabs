# ADR-0005: AWS KMS com Ed25519

- Data: `2026-09-05`
- Status: `aceita`

## Decisao

Produção usa chave assimetrica AWS KMS `ECC_NIST_EDWARDS25519`, `SIGN_VERIFY`, com `kms:Sign` restrito ao runtime/adaptador de integridade. A chave privada nunca e exportada ou persistida. `key_id` e fingerprint publico acompanham provas para rotacao e verificacao historica.

Verificacao usa a chave publica fora do KMS quando possivel. Desenvolvimento/testes podem usar chave efemera em memoria, identificada explicitamente e proibida quando `GOTRENDLABS_ENV=production`.

## Consequencias

Falha KMS aborta publicacao/previsao/selagem. Deploy requer IAM, chave, alarmes e teste de assinatura. A aplicacao adiciona dependencia AWS oficial e timeout/retry limitado.
