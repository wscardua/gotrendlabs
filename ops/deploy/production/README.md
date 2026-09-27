# Deploy de producao

Este deploy usa uma EC2 publica com Docker Compose para `proxy`, `django`, `fastapi` e `daemon`, conectando ao PostgreSQL gerenciado no RDS. O Postgres nao roda em container na producao.

## Infra AWS provisionada

A infraestrutura base de produção foi criada em `us-east-1` via MCP AWS em `2026-05-21`; a aplicação está implantada e recebe atualizações da `main` pelo GitHub Actions/SSM.

- EC2: `i-0fc304f1acb85daea` (`gotrendlabs-prod-host`, `t4g.micro`, Ubuntu ARM64)
- IP publico/Elastic IP: `32.199.120.235`
- RDS: `gotrendlabs-prod-db` (`db.t4g.micro`, PostgreSQL 16)
- Endpoint RDS: `gotrendlabs-prod-db.cinqq6ymy9in.us-east-1.rds.amazonaws.com`
- VPC dedicada: `vpc-0b6ce8dcda5f5500f` (`10.40.0.0/16`)
- Segredo consolidado: `gotrendlabs/prod/app-secrets`
- Parametros: `/gotrendlabs/prod/*`
- Role GitHub Actions: `arn:aws:iam::204620194924:role/gotrendlabs-prod-github-actions-deploy-role`

O RDS permanece privado (`PubliclyAccessible=false`) e aceita `5432` apenas a partir do security group da EC2. A EC2 expoe publicamente apenas `80` e `443`; SSH fica fechado e o acesso operacional padrao e via SSM.

Por restricao do plano AWS `FREE`, o backup retention do RDS ficou em `1` dia. Ao migrar a conta para plano pago, revisar para `7` dias conforme a decisao original do MVP.

## Acesso operacional

Abra shell na EC2 via SSM:

```bash
aws ssm start-session \
  --target i-0fc304f1acb85daea \
  --region us-east-1
```

Para acessar o RDS em um DB viewer local, mantenha um terminal aberto com tunel SSM:

```bash
aws ssm start-session \
  --target i-0fc304f1acb85daea \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters '{"host":["gotrendlabs-prod-db.cinqq6ymy9in.us-east-1.rds.amazonaws.com"],"portNumber":["5432"],"localPortNumber":["15432"]}' \
  --region us-east-1
```

No DB viewer use `localhost:15432`, database `gotrendlabs`, usuario `gotrendlabsadmin`, SSL `require` e a senha armazenada no Secrets Manager em `gotrendlabs/prod/app-secrets`. Nao exponha o RDS publicamente para acesso administrativo.

Para validar por `psql` via tunel SSM local:

```bash
psql "host=localhost port=15432 dbname=gotrendlabs user=gotrendlabsadmin sslmode=require"
```

Para conexao direta a partir da EC2, use o endpoint final:

```bash
psql "host=gotrendlabs-prod-db.cinqq6ymy9in.us-east-1.rds.amazonaws.com port=5432 dbname=gotrendlabs user=gotrendlabsadmin sslmode=verify-full sslrootcert=./global-bundle.pem"
```

## Arquivos

- `Dockerfile`: receita da imagem da aplicacao, mantida na raiz do repo.
- `ops/deploy/production/docker-compose.yml`: servicos de producao para a EC2.
- `ops/deploy/production/Caddyfile`: HTTPS automatico e proxy reverso para Django.
- `ops/deploy/production/deploy.sh`: fluxo idempotente para primeira instalacao (`git clone`) e deploys seguintes (`git pull`), com build, migrations, static files e restart.
- `.env.prod.example`: modelo de variaveis de producao sem segredos reais.
- `.env.auth.prod.example`: modelo separado do pepper, entregue apenas ao container FastAPI.
- `.env.fastapi-db.prod.example`: credencial PostgreSQL com escrita de senha, entregue apenas ao container FastAPI.
- `.env.migrate.prod.example`: credenciais de banco usadas somente pelo servico operacional de migrations.

## Primeira instalacao na EC2

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl ca-certificates
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
```

Se esse bootstrap for feito manualmente em uma sessao interativa, saia e entre novamente para aplicar o grupo `docker`.

```bash
sudo mkdir -p /opt/gotrendlabs
sudo chown ubuntu:ubuntu /opt/gotrendlabs
git clone URL_DO_REPO /opt/gotrendlabs
cd /opt/gotrendlabs
cp .env.prod.example .env.prod
cp .env.auth.prod.example .env.auth.prod
cp .env.fastapi-db.prod.example .env.fastapi-db.prod
cp .env.migrate.prod.example .env.migrate.prod
nano .env.prod
```

Configure `.env.prod` com dominio, `DJANGO_SECRET_KEY` e apenas a credencial PostgreSQL da role Django. Configure `.env.fastapi-db.prod` com `FASTAPI_POSTGRES_*` e restrinja-o com `chmod 600`; somente o container FastAPI o recebe. O daemon usa a role Django, sem permissao de atualizar senhas. Nao deixe `POSTGRES_USER/PASSWORD` nem `FASTAPI_POSTGRES_*` no arquivo compartilhado. Mantenha `GOTRENDLABS_RATE_LIMITS_ENABLED=1` em producao; a aplicacao tambem liga o rate limit por padrao fora dos testes, mas a chave explicita evita ambiguidade operacional. Nao commite arquivos de ambiente.

Antes de publicar a mudanca de hash de senha, configure `GOTRENDLABS_PASSWORD_PEPPER` somente em `.env.auth.prod` com Base64 de 32 bytes aleatorios (`python -c 'import base64,secrets; print(base64.b64encode(secrets.token_bytes(32)).decode())'`). Use um segredo exclusivo, entregue pelo mecanismo de segredos operacional; nao reutilize `DJANGO_SECRET_KEY`. Restrinja o arquivo a conta operacional (`chmod 600 .env.auth.prod`). O deploy valida o valor no container FastAPI antes de iniciar os servicos. O esquema novo nao verifica hashes PBKDF2 antigos; contas de teste anteriores precisam de reset/recriacao. Guarde copia recuperavel do segredo fora da EC2, pois sua perda impede autenticar as senhas v1.

Depois de importar os dados de bootstrap, defina a senha de um administrador existente pelo contexto FastAPI: `docker compose -f ops/deploy/production/docker-compose.yml run --rm -it fastapi python -m apps.api.backend_api.bootstrap_admin_password --username @admin`. A senha e digitada sem aparecer no historico do shell. O importador nao altera senhas existentes.

No corte de 2026-09-27, o superusuario produtivo e `@admin`. Sua credencial bootstrap gerada esta na chave `GOTRENDLABS_ADMIN_BOOTSTRAP_PASSWORD` de `gotrendlabs/prod/app-secrets` no Secrets Manager; consulte-a por canal seguro e nao a copie para Git, logs ou comandos de shell. O pepper esta na chave `GOTRENDLABS_PASSWORD_PEPPER` do mesmo segredo e so e injetado no arquivo da FastAPI. Duas contas anteriores ficaram com senha inutilizavel e exigem reset caso sejam reutilizadas.

Configure `.env.migrate.prod` com uma credencial operacional que tenha `CREATEROLE`, `CREATE` no schema e possa alterar as tabelas Django existentes. Essa credencial nao entra nos containers de runtime. O deploy executa migrations pelo servico `migrate`, aplica `ops/sql/auth_password_boundary.sql` antes/depois delas e falha antes do restart caso Django exponha outra credencial de banco, a role Django possa alterar `gotrendlabs_users.password` ou a FastAPI nao use a role autorizada. O novo proprietario `gotrendlabs_auth_owner` nao tem login; o trigger protege insercoes com senha utilizavel e as permissoes de coluna protegem updates. O ensaio em infraestrutura separada foi dispensado nesta fase; valide as permissoes da credencial migradora por preflight no RDS antes de integrar a branch.

Para auditar o corte sem revelar dados pessoais, execute `docker compose -f ops/deploy/production/docker-compose.yml run --rm fastapi python -m ops.scripts.auth_db_boundary inventory`. Contas PBKDF2 exigem reset/recriacao antes de depender do login novo. Para medir o custo do hash em um host de ensaio equivalente, use `docker compose -f ops/deploy/production/docker-compose.yml run --rm fastapi python -m ops.scripts.benchmark_password_hash --workers 1,2,5,10 --operations 8`; compare com memoria livre, swap, creditos de CPU e latencia HTTP do stack, sem usar este benchmark isolado como garantia de capacidade.

## Corte inicial sem ensaio isolado

O usuario dispensou o ambiente de ensaio separado nesta fase. Antes de integrar a branch a `main`, deixe revisaveis os tres arquivos de ambiente segregados, confirme que o usuario migrador consegue aplicar `ops/sql/auth_password_boundary.sql` no RDS e registre um snapshot recuperavel do banco e uma copia segura do pepper fora da EC2. Execute o inventario de hashes sem PII e defina reset/recriacao para contas PBKDF2 antes de depender do login novo. Nao exponha os valores dos segredos no log de preflight.

Como o merge dispara o deploy automatico, mantenha a branch fora de `main` ate esses preparativos estarem prontos. Apos o primeiro deploy, confira `GET /api/health`, cadastro/login/logout/recuperacao pela API e site, login/logout no app, roles com `auth_db_boundary check` e `check-api`, e saldo/ledger de um cancelamento de teste. Registre memoria e swap da EC2, creditos de CPU, latencia de auth e erros `5xx` durante o smoke e nas primeiras horas. Falha de autenticacao, erro de privilegio, OOM ou degradacao persistente interrompe a liberacao; preserve o pepper e o snapshot para diagnostico e correcao. O rollback de codigo isolado nao torna hashes v1 novamente verificaveis por PBKDF2.

Antes do corte, obtenha snapshot recuperavel do banco e copia segura do pepper fora da EC2. Se o preflight de pepper, migrations ou grants falhar, o script encerra antes de reiniciar os servicos; migrations eventualmente aplicadas ainda exigem avaliacao de compatibilidade com os processos antigos. Corrija a credencial/permissao e repita ou restaure o snapshot conforme o caso. `ops/sql/auth_password_boundary_rollback.sql` e uma reversao manual anterior ao lancamento e recusa executar se houver qualquer hash Argon2id v1. Um rollback de codigo nao transforma hashes Argon2id novamente em PBKDF2: apos existir hash v1, preserve o segredo e planeje reset de senha ou correcao para a frente, sem devolver ownership da tabela ao runtime Django.

Na EC2 provisionada, `Docker Engine`, `Docker Compose plugin`, `git`, `curl`, `ca-certificates`, `unzip`, `AWS CLI v2`, `SSM Agent`, `CloudWatch Agent` e `postgresql-client` ja foram instalados e validados via SSM. Antes do primeiro deploy da aplicacao, crie `/opt/gotrendlabs/.env.prod` fora do Git com os valores reais do Secrets Manager e Parameter Store.

## Primeiro deploy

```bash
APP_DIR=/opt/gotrendlabs BRANCH=main ./ops/deploy/production/deploy.sh
```

## Deploys seguintes

```bash
APP_DIR=/opt/gotrendlabs BRANCH=main ./ops/deploy/production/deploy.sh
```

Para bootstrap remoto via GitHub Actions ou SSM, o script tambem aceita:

```bash
APP_DIR=/opt/gotrendlabs BRANCH=main REPO_URL=https://github.com/OWNER/REPO.git ./ops/deploy/production/deploy.sh
```

## GitHub Actions

O repositório inclui o workflow `.github/workflows/deploy.yml` para:

- rodar `python manage.py test` em todo `push` na `main`;
- assumir uma role AWS via OIDC;
- disparar o deploy na EC2 com `AWS Systems Manager`;
- executar o mesmo `deploy.sh` usado manualmente.

Configure estes valores no GitHub antes de habilitar o deploy automatico:

- variable obrigatoria `ENABLE_PROD_DEPLOY`: use `1` apenas depois que `.env.prod` existir na EC2 e os valores abaixo estiverem configurados
- variable obrigatoria `AWS_GITHUB_ACTIONS_ROLE_ARN`: `arn:aws:iam::204620194924:role/gotrendlabs-prod-github-actions-deploy-role`
- variable recomendada `AWS_EC2_INSTANCE_ID`: `i-0fc304f1acb85daea`
- variable `AWS_REGION` opcional, default `us-east-1`
- variable `APP_DIR` opcional, default `/opt/gotrendlabs`
- variable `DEPLOY_BRANCH` opcional, default `main`
- variable `REPO_URL` opcional, default `https://github.com/<owner>/<repo>.git`
- secret legado opcional `AWS_GITHUB_ACTIONS_ROLE_ARN`: fallback temporario enquanto a configuracao antiga ainda existir
- secret legado opcional `AWS_EC2_INSTANCE_ID`: fallback temporario enquanto a configuracao antiga ainda existir

Checklist exato para o workflow:

1. `main` deve ser o branch que dispara o deploy de producao.
2. `ENABLE_PROD_DEPLOY` deve ser `1`.
3. `AWS_GITHUB_ACTIONS_ROLE_ARN` deve apontar para a conta `204620194924`.
4. `AWS_EC2_INSTANCE_ID` deve apontar para a EC2 gerenciada por SSM.
5. `.env.prod` deve existir em `/opt/gotrendlabs/.env.prod` antes do primeiro deploy automatico.
6. O job deve passar pela etapa `Verify assumed AWS identity` com `aws sts get-caller-identity` retornando a conta `204620194924` antes do `send-command`.

O workflow agora faz um preflight explicito da configuracao e falha cedo quando `AWS_GITHUB_ACTIONS_ROLE_ARN`, `AWS_EC2_INSTANCE_ID` ou `AWS_REGION` estiverem ausentes/inconsistentes. O deploy automatico continua nao substituindo a criacao segura de `.env.prod` na EC2.

## DNS e HTTPS

O Caddy emite e renova certificados publicos automaticamente para:

- `gotrendlabs.com.br`
- `www.gotrendlabs.com.br`
- `gotrendlabs.com`
- `www.gotrendlabs.com`

Para o certificado ser aceito em producao:

- os registros DNS desses hosts apontam para o IP publico da EC2;
- portas `80` e `443` estao liberadas no security group;
- nenhum outro processo esta usando `80` ou `443` na EC2.
- no Cloudflare, use SSL/TLS `Full (strict)` depois que o Caddy emitir o certificado.

O deploy nao gera certificado autoassinado por IP. Acesso por IP direto e apenas
diagnostico temporario; o caminho oficial e sempre pelos dominios.

## Resend transacional

O provider preferencial para email transacional pode ser Resend via API HTTPS. A configuracao operacional segue duas fronteiras:

- Dominio remetente verificado no dashboard Resend, por padrao `gotrendlabs.com.br`, com SPF/DKIM publicados no DNS; DMARC e recomendado.
- Parametros nao sensiveis no Admin Ops; API key somente em `GOTRENDLABS_RESEND_API_KEY` ou secret manager.

Configuracao padrao do Admin Ops depois da verificacao DNS:

- provider: `resend`
- remetente padrao: `no-reply@gotrendlabs.com.br`
- reply-to: mailbox operacional real, quando existir

Fluxo seguro:

1. Adicionar `gotrendlabs.com.br` no Resend e publicar os registros SPF/DKIM exibidos pelo dashboard.
2. Aguardar o dominio ficar verificado e criar uma API key restrita ao projeto/dominio quando possivel.
3. Atualizar `/opt/gotrendlabs/.env.prod` com `GOTRENDLABS_RESEND_API_KEY` fora do Git e reiniciar os containers.
4. Selecionar `Resend` no Admin Ops, preencher remetente/reply-to e validar com:

```bash
docker compose -f ops/deploy/production/docker-compose.yml run --rm django \
  python manage.py send_resend_test_email --to wsca@icloud.com
```

Depois da verificacao do dominio, o Resend permite enviar de qualquer endereco desse dominio; nao e necessario criar previamente `no-reply@...` no dashboard. Bounce/complaint webhooks ficam para uma etapa posterior.

## Push mobile

Push mobile usa Firebase Cloud Messaging como arquitetura alvo para Android e iOS, mas a primeira fase de produção deve permanecer desligada/noop:

- `GOTRENDLABS_PUSH_ENABLED=0` mantém a outbox sem enfileirar novas entregas.
- `GOTRENDLABS_PUSH_PROVIDER=none` evita chamadas externas.
- `GOTRENDLABS_PUSH_DRY_RUN=1` permite validar daemon/outbox quando a flag geral for ligada em ambiente controlado.
- `GOTRENDLABS_FCM_CREDENTIALS_JSON` fica reservado para credencial futura em ambiente/secret manager; nunca salve esse valor no banco, Admin Ops ou Git.

Ao ativar FCM real no futuro, atualize `/opt/gotrendlabs/.env.prod`, recrie `django`, `fastapi` e `daemon`, e valide com um dispositivo operacional antes de liberar eventos para usuários.

## API publica e APK beta Android

O Caddy publica a FastAPI sob o mesmo dominio oficial:

- `https://gotrendlabs.com.br/api/*` roteia para `fastapi:8001` usando `handle_path`, removendo o prefixo `/api`.
- Probes comuns contra WordPress, PHP, `.env`, `.git` e `vendor` sao respondidos com `404` diretamente no Caddy antes de chegar ao Django. A regra nao bloqueia `/admin/*` genericamente; apenas padroes suspeitos como `/admin/.env` e `/admin/phpinfo.php` entram no bloqueio.
- Smokes esperados apos deploy: `/api/health`, `/api/markets`, login/auth e endpoints mobile existentes.
- Quando o `Caddyfile` mudar, recrie ou recarregue o servico `proxy` e confirme que o container em execucao contem o bloco novo. O arquivo no disco pode estar atualizado enquanto o Caddy ainda roda com configuracao antiga:

```bash
docker compose -f ops/deploy/production/docker-compose.yml up -d --force-recreate --no-deps proxy
docker compose -f ops/deploy/production/docker-compose.yml exec -T proxy caddy validate --config /etc/caddy/Caddyfile
docker compose -f ops/deploy/production/docker-compose.yml exec -T proxy sh -c 'grep -n "handle_path /api" -A2 /etc/caddy/Caddyfile'
```

O beta Android fora da Google Play e distribuido por Django/Admin Ops:

1. Gerar APK release assinado localmente, sem commitar APK, keystore, senha ou `apps/mobile/android/key.properties`.
2. Fazer upload em `/admin-ops/mobile-releases/`.
3. Conferir o CTA Android no rodape/login/cadastro/compartilhamento e o JSON `/app/android/latest.json`.
4. Baixar o APK pelo link HTTPS publico e conferir o SHA-256 com o valor exibido na pagina.

Os arquivos ficam no volume de media em `MEDIA_ROOT/app_releases/android/` e sao servidos por `/media/app_releases/android/...`. Apenas uma release Android ativa deve existir por vez. Google Play e atualizacao automatica dentro do app continuam fora desta etapa.

## Google Play closed testing

O canal Google Play Closed testing usa Android App Bundle assinado localmente e e independente do APK beta direto publicado pelo Admin Ops. Preparar um AAB para Play Console nao altera `/app/android/latest.json` nem substitui o APK ativo do site.

Build padrao do AAB:

```bash
cd apps/mobile
flutter build appbundle --release \
  --dart-define=GTL_API_BASE_URL=https://gotrendlabs.com.br/api \
  --dart-define=GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br
```

Para a primeira release de teste fechado, use:

- Versao: `1.0.8+9`
- Release name: `1.0.8+9 - Closed testing Android`
- Release notes:

```text
<pt-BR>
Primeira versão de teste fechado do app GoTrendLabs no Google Play. Inclui feed e detalhe de mercados, previsões com GT₵ educativo, carteira, ranking, alertas, perfil, suporte, proteção local da sessão, manutenção mobile e push Android via FCM quando autorizado.
</pt-BR>
```

O AAB, APKs, keystores, `apps/mobile/android/key.properties` e `apps/mobile/android/app/google-services.json` nao devem ser commitados. Registre SHA-256 e tamanho do AAB no workflow de release antes do upload manual no Play Console.

## Observacoes operacionais

- Rode apenas um container `daemon` por ambiente.
- O container Django executa dois workers Uvicorn. Na EC2 `t4g.micro`, mantenha 1 GiB de swap com `vm.swappiness=10` e monitore memória; reduzir temporariamente para um worker é o rollback operacional caso haja pressão sustentada.
- O container `daemon` roda `run_gotrendlabs_daemon` a cada 300 segundos; mantenha os limites do Dashboard Admin Ops com folga operacional, por padrão 7 minutos para `Atrasado` e 21 minutos para `Sem sinal`.
- O RDS deve aceitar `5432` somente a partir do security group da EC2.
- O acesso administrativo ao banco deve usar tunel SSM pela EC2, nao public access no RDS.
- A role OIDC do GitHub Actions esta restrita ao repositorio `wscardua/gotrendlabs` e ao branch `main`.
- OIDC permanece o mecanismo oficial; nao reintroduza `AWS_ACCESS_KEY_ID` ou `AWS_SECRET_ACCESS_KEY` em GitHub Actions para este deploy.
- Para evoluir para duas VMs, mantenha Django/proxy na EC2 publica e mova FastAPI/daemon para uma EC2 privada.

## Ledger de integridade em produção

O rollout do ledger segue obrigatoriamente `docs/specs/operations/market-integrity-deploy.md`. A chave privada Ed25519 permanece no KMS sob `alias/gotrendlabs-integrity-signing`; a role da EC2 recebe somente assinatura/leitura da chave pública no ARN específico. O segredo de pseudonimização e o identificador KMS ficam no Secrets Manager e são sincronizados para `.env.prod` sem aparecer em logs.

Como o produto ainda não foi lançado, o primeiro rollout cria snapshot do RDS e remove todos os mercados pré-existentes sem definição assinada. Não há migração retroativa, modo legado ou alegação de que registros anteriores possuíam prova original.
