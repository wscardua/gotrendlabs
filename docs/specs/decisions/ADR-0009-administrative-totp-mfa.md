# ADR-0009 — TOTP obrigatório para contas administrativas

## Decisão

Contas `is_staff` ou `is_superuser` usam TOTP RFC 6238 (30 segundos, SHA-1, seis dígitos), compatível com Google Authenticator, após a primeira credencial. A FastAPI cria e verifica desafios e emite a sessão; Django só apresenta o fluxo. O Django Admin nativo foi removido das rotas para não criar bypass da sessão FastAPI.

## Segurança

O segredo é cifrado por Fernet com `GOTRENDLABS_TOTP_ENCRYPTION_KEY`, disponível somente na FastAPI. Desafios e recovery codes são hashados e de uso único. O limite de tentativas MFA fica no PostgreSQL para ser compartilhado por workers. Uma sessão administrativa exige `mfa_verified_at` e `mfa_method`.

## Consequências

O rollout revoga sessões administrativas existentes. Operadores sem fator configurado passam por enrollment e não recebem sessão antes da confirmação. Reset de senha não afeta MFA; recuperação exige superuser já autenticado por MFA e deve ser completada em evolução posterior com endpoint administrativo auditado.
