# Orynth Trends

Orynth Trends e uma rede social de previsoes com moeda educativa, reputacao publica e resolucao auditavel de mercados. O produto combina uma interface web server-rendered em Django com uma API de dominio em FastAPI e persistencia em PostgreSQL.

## Stack

- Django 4.2 para paginas publicas, areas autenticadas e Admin Ops customizado.
- FastAPI para contratos de dominio, autenticacao, mercados, previsoes, comentarios, filas e operacoes administrativas.
- PostgreSQL 16 para usuarios, sessoes, mercados, opcoes, previsoes, wallet, comentarios e trilha operacional.
- HTMX e JavaScript leve em `static/js/orynth.js` para interacoes parciais e estado local simples.
- CSS proprio em `static/css/orynth.css`, com suporte a dark mode via `localStorage`.

## Estrutura

- `config/`: settings, URLs e WSGI/ASGI do Django.
- `backend_api/`: app FastAPI, schemas Pydantic, seguranca e conexao Postgres.
- `accounts/`: usuario customizado, formularios, sessao Django e telas de login/cadastro.
- `markets/`: modelos de mercado, opcoes, previsoes, comentarios e servicos locais.
- `core/`: feed, paginas publicas, fallback de dominio e context processors.
- `admin_ops/`: painel operacional customizado para mercados, taxonomia, filas e moderacao.
- `docs/specs/`: fonte principal de arquitetura, features, fluxos e criterios de aceite.
- `tools/skills/orynth/`: skills locais usadas para orientar implementacao por camada.

## Setup local

Crie e ative um ambiente Python:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Suba o Postgres:

```bash
docker compose up -d postgres
```

Execute as migrations:

```bash
python manage.py migrate
```

Em dois terminais, rode a API e o Django:

```bash
uvicorn backend_api.main:app --reload --port 8001
python manage.py runserver 127.0.0.1:8000
```

Acesse:

- App web: `http://127.0.0.1:8000/`
- Login: `http://127.0.0.1:8000/login/`
- Admin Ops: `http://127.0.0.1:8000/admin-ops/`
- FastAPI: `http://127.0.0.1:8001/docs`

## Configuracao

Variaveis relevantes:

```bash
POSTGRES_DB=orynth
POSTGRES_USER=orynth
POSTGRES_PASSWORD=orynth_dev_password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
DJANGO_POSTGRES_DB=orynth
DJANGO_POSTGRES_USER=orynth_django
DJANGO_POSTGRES_PASSWORD=orynth_django_password
DJANGO_POSTGRES_HOST=127.0.0.1
DJANGO_POSTGRES_PORT=5432
FASTAPI_POSTGRES_DB=orynth
FASTAPI_POSTGRES_USER=orynth_fastapi
FASTAPI_POSTGRES_PASSWORD=orynth_fastapi_password
FASTAPI_POSTGRES_HOST=127.0.0.1
FASTAPI_POSTGRES_PORT=5432
BACKEND_API_URL=http://127.0.0.1:8001
ORYNTH_RUNTIME_CONFIG_PATH=.runtime/platform_config.json
ORYNTH_SMTP_PASSWORD=
ORYNTH_SMTP_API_KEY=
RECAPTCHA_ENABLED=0
RECAPTCHA_SITE_KEY=
RECAPTCHA_SECRET_KEY=
```

`POSTGRES_*` continua disponivel como fallback local e bootstrap do container. Para runtime, prefira `DJANGO_POSTGRES_*` e `FASTAPI_POSTGRES_*` com usuarios de menor privilegio por aplicacao. O arquivo `.env.example` e apenas modelo versionado; a aplicacao le o `.env` local ou variaveis ja exportadas no ambiente.

O modo manutencao do Admin Ops e salvo em `ORYNTH_RUNTIME_CONFIG_PATH` para continuar funcionando sem conexao com o banco. Configuracoes SMTP nao sensiveis ficam no banco; senha/API key devem ficar somente em `ORYNTH_SMTP_PASSWORD` ou `ORYNTH_SMTP_API_KEY`.

Para ativar o reCAPTCHA v2 checkbox no cadastro e nos envios públicos de sugestão/feedback, preencha `RECAPTCHA_SITE_KEY`, `RECAPTCHA_SECRET_KEY` e use `RECAPTCHA_ENABLED=1`. A site key é pública; a secret key deve ficar apenas no ambiente do servidor.

Para usar SQLite em tarefas rapidas de Django:

```bash
ORYNTH_USE_SQLITE=1 python manage.py migrate
```

## Testes

Rode a suite principal:

```bash
python manage.py test
```

Os testes cobrem contratos de API, renderizacao web, fallback local de desenvolvimento, Admin Ops, wallet, comentarios, previsoes e fluxos autenticados.

## Deploy MVP em EC2

O deploy de producao fica em `deploy/production/` e usa Docker Compose na EC2 para subir Caddy, Django, FastAPI e o daemon operacional. O PostgreSQL de producao deve ser gerenciado fora do Compose, por exemplo em Amazon RDS.

A base AWS de producao foi provisionada em `us-east-1` com EC2 ARM gerenciada por SSM, RDS PostgreSQL privado, CloudWatch minimo, Secrets Manager/Parameter Store e role OIDC para GitHub Actions. O deploy automatico ainda depende da criacao segura de `.env.prod` fora do Git na EC2.

Arquivos principais:

- `Dockerfile`: imagem da aplicacao.
- `.env.prod.example`: modelo de variaveis de producao sem segredos reais.
- `deploy/production/docker-compose.yml`: servicos de producao.
- `deploy/production/Caddyfile`: HTTPS automatico e proxy reverso.
- `deploy/production/deploy.sh`: fluxo de deploy na EC2.
- `.github/workflows/deploy.yml`: testes em `main` e deploy futuro via SSM.

Consulte `deploy/production/README.md` para a instalacao inicial e os comandos de deploy.

## Specs e skills

Antes de alterar comportamento, consulte:

- `docs/specs/architecture/frontend-web.md`
- `docs/specs/architecture/backend-api.md`
- `docs/specs/architecture/admin-ops.md`
- `docs/specs/architecture/database.md`
- `docs/specs/features/`
- `docs/specs/testing/`

Skills locais uteis:

- `tools/skills/orynth/orynth-django-web/SKILL.md`
- `tools/skills/orynth/orynth-test-strategy/SKILL.md`
- `tools/skills/orynth/orynth-postgres-modeling/SKILL.md`
- `tools/skills/orynth/orynth-software-architect/SKILL.md`

## Regras atuais importantes

- Handles publicos sao canonicos no formato `@nome`, nascem automaticamente do nome publico e preservam unicidade com sufixo.
- Os cards de destaque do feed priorizam ate dois mercados publicados nao cancelados com mais visualizacoes; empate usa o mercado mais novo.
- Marcacoes editoriais de destaque continuam existindo para curadoria, mas nao superam a ordenacao por visualizacoes no card principal da home.
- Os filtros da home sao ordenacoes/recortes client-side: tendencia, novos, aberto, encerrado, resolvidos, volume, mais curtidas, favoritos pessoais autenticados e minhas previsoes.
- O dashboard do Admin Ops consome o resumo staff da FastAPI (`/admin/dashboard-summary`) e acompanha saúde operacional; criação de mercados fica concentrada na área `Mercados`.
- Orynth Coins sao educativos e nao representam dinheiro real.
