# ADR-0008: Argon2id com pepper para senhas locais

- Data: `2026-09-27`
- Status: `aceita`

## Contexto

FastAPI autenticava senhas PBKDF2-HMAC-SHA256 de 720000 iteracoes na tabela compartilhada `gotrendlabs_users`; Django criava usuarios na mesma tabela com seu hasher padrao. A mudanca foi solicitada antes do lancamento publico de contas e nao precisa preservar hashes anteriores.

## Decisao

- Senhas locais passam por HMAC-SHA256 com pepper secreto de 32 bytes e depois por Argon2id com salt aleatorio de 16 bytes por senha.
- O formato `argon2id_pepper_v1$<hash PHC Argon2id>` identifica o esquema. Parametros iniciais: `m=19456 KiB`, `t=2`, `p=1`, minimo recomendado pela OWASP; apenas duas operacoes pesadas concorrem por processo. O host produtivo documentado e pequeno e exige medicao antes de elevar o custo.
- `packages/security/passwords.py` contem a primitiva usada pela FastAPI para criar e verificar senhas. Django usa um hasher que recusa senhas utilizaveis em runtime; o adaptador Argon2id permanece apenas no processo isolado de testes.
- `GOTRENDLABS_PASSWORD_PEPPER` e Base64 de 32 bytes aleatorios, distinto de outras chaves e entregue pelo ambiente/gerenciador de segredos. Nunca e salvo no banco, no Git, nos logs ou nos contratos.
- O processo FastAPI e o preflight do deploy falham se o segredo estiver ausente ou invalido. O segredo fica em arquivo de ambiente exclusivo da FastAPI (`.env.api.local` no desenvolvimento, `.env.auth.prod` no Compose). Hashes PBKDF2 existentes nao sao aceitos; contas anteriores ao lancamento devem ser recriadas ou ter a senha redefinida.
- O importador de bootstrap nao define mais uma senha; o operador usa `python -m apps.api.backend_api.bootstrap_admin_password --username <usuario>` no contexto da FastAPI. O comando revoga sessoes e audita a acao.
- `gotrendlabs_users` e a funcao de guard pertencem a `gotrendlabs_auth_owner` sem login. A role Django recebe UPDATE apenas das colunas nao sensiveis; trigger sob owner separado impede INSERT com senha utilizavel. `ops/scripts/auth_db_boundary.py` aplica/verifica essa fronteira apos migrations com credencial operacional isolada.
- A troca do pepper v1 exige suporte versionado ou reset de senhas; nao ha rotacao automatica nesta entrega.

## Consequencias

- Sem mudanca OpenAPI ou de schema de produto; web e Flutter continuam usando os endpoints FastAPI existentes.
- O custo de memoria por hash exige medicao de latencia e concorrencia no host de deploy. Rate limits de login continuam necessarios.
- A configuracao produtiva do pepper e da credencial migradora precisa preceder qualquer merge que acione deploy automatico; sem os segredos ou sem a fronteira de banco, o deploy falha antes do restart.
