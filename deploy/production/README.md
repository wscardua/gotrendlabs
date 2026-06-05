# Deploy de producao

Este deploy usa uma EC2 publica com Docker Compose para `proxy`, `django`, `fastapi` e `daemon`, conectando ao PostgreSQL gerenciado no RDS. O Postgres nao roda em container na producao.

## Infra AWS provisionada

A infraestrutura base de producao foi criada em `us-east-1` via MCP AWS em `2026-05-21`, sem deploy da aplicacao ainda.

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
- `deploy/production/docker-compose.yml`: servicos de producao para a EC2.
- `deploy/production/Caddyfile`: HTTPS automatico e proxy reverso para Django.
- `deploy/production/deploy.sh`: fluxo idempotente para primeira instalacao (`git clone`) e deploys seguintes (`git pull`), com build, migrations, static files e restart.
- `.env.prod.example`: modelo de variaveis de producao sem segredos reais.

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
nano .env.prod
```

Configure `.env.prod` com dominio, `DJANGO_SECRET_KEY`, endpoints do RDS, usuarios e senhas. Nao commite `.env.prod`.

Na EC2 provisionada, `Docker Engine`, `Docker Compose plugin`, `git`, `curl`, `ca-certificates`, `unzip`, `AWS CLI v2`, `SSM Agent`, `CloudWatch Agent` e `postgresql-client` ja foram instalados e validados via SSM. Antes do primeiro deploy da aplicacao, crie `/opt/gotrendlabs/.env.prod` fora do Git com os valores reais do Secrets Manager e Parameter Store.

## Primeiro deploy

```bash
APP_DIR=/opt/gotrendlabs BRANCH=main ./deploy/production/deploy.sh
```

## Deploys seguintes

```bash
APP_DIR=/opt/gotrendlabs BRANCH=main ./deploy/production/deploy.sh
```

Para bootstrap remoto via GitHub Actions ou SSM, o script tambem aceita:

```bash
APP_DIR=/opt/gotrendlabs BRANCH=main REPO_URL=https://github.com/OWNER/REPO.git ./deploy/production/deploy.sh
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

## Observacoes operacionais

- Rode apenas um container `daemon` por ambiente.
- O RDS deve aceitar `5432` somente a partir do security group da EC2.
- O acesso administrativo ao banco deve usar tunel SSM pela EC2, nao public access no RDS.
- A role OIDC do GitHub Actions esta restrita ao repositorio `wscardua/gotrendlabs` e ao branch `main`.
- OIDC permanece o mecanismo oficial; nao reintroduza `AWS_ACCESS_KEY_ID` ou `AWS_SECRET_ACCESS_KEY` em GitHub Actions para este deploy.
- Para evoluir para duas VMs, mantenha Django/proxy na EC2 publica e mova FastAPI/daemon para uma EC2 privada.
