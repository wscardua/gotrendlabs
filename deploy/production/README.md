# Deploy de producao

Este deploy usa uma EC2 publica com Docker Compose para `proxy`, `django`, `fastapi` e `daemon`, conectando ao PostgreSQL gerenciado no RDS. O Postgres nao roda em container na producao.

## Arquivos

- `Dockerfile`: receita da imagem da aplicacao, mantida na raiz do repo.
- `deploy/production/docker-compose.yml`: servicos de producao para a EC2.
- `deploy/production/Caddyfile`: HTTPS automatico e proxy reverso para Django.
- `deploy/production/deploy.sh`: fluxo de `git pull`, build, migrations, static files e restart.
- `.env.prod.example`: modelo de variaveis de producao sem segredos reais.

## Primeira instalacao na EC2

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl ca-certificates
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
```

Saia do SSH e entre novamente para aplicar o grupo `docker`.

```bash
sudo mkdir -p /opt/orynth
sudo chown ubuntu:ubuntu /opt/orynth
cd /opt/orynth
git clone URL_DO_REPO .
cp .env.prod.example .env.prod
nano .env.prod
```

Configure `.env.prod` com dominio, `DJANGO_SECRET_KEY`, endpoints do RDS, usuarios e senhas. Nao commite `.env.prod`.

## Primeiro deploy

```bash
docker compose -f deploy/production/docker-compose.yml build
docker compose -f deploy/production/docker-compose.yml run --rm django python manage.py migrate
docker compose -f deploy/production/docker-compose.yml run --rm django python manage.py collectstatic --noinput
docker compose -f deploy/production/docker-compose.yml up -d
docker compose -f deploy/production/docker-compose.yml ps
```

## Deploys seguintes

```bash
APP_DIR=/opt/orynth BRANCH=main ./deploy/production/deploy.sh
```

## DNS e HTTPS

O Caddy emite e renova o certificado automaticamente quando:

- `ORYNTH_DOMAIN` aponta para o IP publico da EC2;
- portas `80` e `443` estao liberadas no security group;
- nenhum outro processo esta usando `80` ou `443` na EC2.

## Observacoes operacionais

- Rode apenas um container `daemon` por ambiente.
- O RDS deve aceitar `5432` somente a partir do security group da EC2.
- Para evoluir para duas VMs, mantenha Django/proxy na EC2 publica e mova FastAPI/daemon para uma EC2 privada.
