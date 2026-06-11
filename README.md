# GoTrendLabs

GoTrendLabs e uma rede social de previsoes com moeda educativa, reputacao publica e resolucao auditavel de mercados. O produto combina uma interface web server-rendered em Django com uma API de dominio em FastAPI e persistencia em PostgreSQL.

## Stack

- Django 4.2 para paginas publicas, areas autenticadas e Admin Ops customizado.
- FastAPI para contratos de dominio, autenticacao, mercados, previsoes, comentarios, filas e operacoes administrativas.
- PostgreSQL 16 para usuarios, sessoes, mercados, opcoes, previsoes, wallet, comentarios e trilha operacional.
- HTMX e JavaScript leve em `apps/web/static/js/gotrendlabs.js` para interacoes parciais e estado local simples.
- CSS proprio em `apps/web/static/css/gotrendlabs.css`, com suporte a dark mode via `localStorage`.

## Estrutura

### Estrutura vigente

- `config/`: settings, URLs e WSGI/ASGI do Django.
- `apps/api/backend_api/`: app FastAPI, schemas Pydantic, seguranca e conexao Postgres.
- `apps/web/django/`: apps Django (`accounts`, `markets`, `core`, `admin_ops`, `wallet`, `profiles`, `agents`, `communications` e `system_logs`) com labels historicos preservados.
- `apps/web/templates/`: templates compartilhados da camada web Django.
- `apps/web/static/`: assets compartilhados da camada web Django.
- `packages/contracts/openapi/gotrendlabs-api.json`: snapshot OpenAPI versionado da FastAPI.
- `docs/specs/`: fonte principal de arquitetura, features, fluxos e criterios de aceite.
- `tools/skills/gotrendlabs/`: skills locais usadas para orientar implementacao por camada.

### Estrutura alvo do monorepo

A reorganizacao esta sendo feita em etapas para reduzir risco. FastAPI, operacao, apps Django, templates e assets web ja vivem nos caminhos novos; os labels Django historicos continuam preservados para nao renomear tabelas nem quebrar migrations.

- `apps/api/`: casa da FastAPI e da autoridade de dominio do produto.
- `apps/web/`: casa da web Django, incluindo apps em `apps/web/django/`, templates compartilhados e assets.
- `apps/mobile/`: reserva para o futuro frontend mobile; nenhum projeto Flutter ou spec tecnica mobile e criado nesta fase.
- `packages/contracts/`: snapshot OpenAPI versionado e futura casa de clientes gerados quando houver consumidor real.
- `ops/`: deploy de producao, scripts operacionais e estado Docker local ignorado pelo Git.
- `docs/audits/`: relatorios de auditoria e seguranca.
- `tools/`: ferramentas de desenvolvimento e skills locais do repositorio inteiro.

Guardrail arquitetural: FastAPI concentra dominio, inteligencia, IA, wallet, reputacao, badges, resolucao, auditoria e integracoes. Django web/Admin Ops e o futuro mobile sao clientes desses contratos e nao devem duplicar regra critica.

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
python -m uvicorn apps.api.backend_api.main:app --reload --port 8001
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
POSTGRES_DB=gotrendlabs
POSTGRES_USER=gotrendlabs
POSTGRES_PASSWORD=gotrendlabs_dev_password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
DJANGO_POSTGRES_DB=gotrendlabs
DJANGO_POSTGRES_USER=gotrendlabs_django
DJANGO_POSTGRES_PASSWORD=gotrendlabs_django_password
DJANGO_POSTGRES_HOST=127.0.0.1
DJANGO_POSTGRES_PORT=5432
FASTAPI_POSTGRES_DB=gotrendlabs
FASTAPI_POSTGRES_USER=gotrendlabs_fastapi
FASTAPI_POSTGRES_PASSWORD=gotrendlabs_fastapi_password
FASTAPI_POSTGRES_HOST=127.0.0.1
FASTAPI_POSTGRES_PORT=5432
BACKEND_API_URL=http://127.0.0.1:8001
GOTRENDLABS_RUNTIME_CONFIG_PATH=.runtime/platform_config.json
GOTRENDLABS_SMTP_PASSWORD=
GOTRENDLABS_SMTP_API_KEY=
GOTRENDLABS_RESEND_API_KEY=
GOTRENDLABS_PUSH_ENABLED=0
GOTRENDLABS_PUSH_PROVIDER=none
GOTRENDLABS_PUSH_DRY_RUN=1
GOTRENDLABS_FCM_CREDENTIALS_JSON=
RECAPTCHA_ENABLED=0
RECAPTCHA_SITE_KEY=
RECAPTCHA_SECRET_KEY=
```

`POSTGRES_*` continua disponivel como fallback local e bootstrap do container. Para runtime, prefira `DJANGO_POSTGRES_*` e `FASTAPI_POSTGRES_*` com usuarios de menor privilegio por aplicacao. O arquivo `.env.example` e apenas modelo versionado; a aplicacao le o `.env` local ou variaveis ja exportadas no ambiente.

O modo manutencao do Admin Ops e salvo em `GOTRENDLABS_RUNTIME_CONFIG_PATH` para continuar funcionando sem conexao com o banco. Configuracoes nao sensiveis de email ficam no banco; senha/API key SMTP devem ficar somente em `GOTRENDLABS_SMTP_PASSWORD` ou `GOTRENDLABS_SMTP_API_KEY`, e a API key Resend deve ficar somente em `GOTRENDLABS_RESEND_API_KEY`. Push mobile nasce desligado com provider `none`/dry-run; credencial FCM futura deve ficar apenas em `GOTRENDLABS_FCM_CREDENTIALS_JSON` ou secret manager, nunca no Git/Admin Ops.

Para ativar o reCAPTCHA v2 checkbox no cadastro e nos envios públicos de sugestão/feedback, preencha `RECAPTCHA_SITE_KEY`, `RECAPTCHA_SECRET_KEY` e use `RECAPTCHA_ENABLED=1`. A site key é pública; a secret key deve ficar apenas no ambiente do servidor.

Para usar SQLite em tarefas rapidas de Django:

```bash
GOTRENDLABS_USE_SQLITE=1 python manage.py migrate
```

## Testes

Rode a suite principal:

```bash
python manage.py test
```

Os testes cobrem contratos de API, renderizacao web, fallback local de desenvolvimento, Admin Ops, wallet, comentarios, previsoes e fluxos autenticados.

Valide o snapshot OpenAPI versionado:

```bash
python packages/contracts/export_openapi.py --check
```

Quando alterar endpoints, payloads ou schemas da FastAPI, regenere o contrato no mesmo PR:

```bash
python packages/contracts/export_openapi.py
```

## Deploy MVP em EC2

O deploy de producao fica em `ops/deploy/production/` e usa Docker Compose na EC2 para subir Caddy, Django, FastAPI e o daemon operacional. O PostgreSQL de producao deve ser gerenciado fora do Compose, por exemplo em Amazon RDS.

A base AWS de producao foi provisionada em `us-east-1` com EC2 ARM gerenciada por SSM, RDS PostgreSQL privado, CloudWatch minimo, Secrets Manager/Parameter Store e role OIDC para GitHub Actions. O deploy automatico ainda depende da criacao segura de `.env.prod` fora do Git na EC2.

Arquivos principais:

- `Dockerfile`: imagem da aplicacao.
- `.env.prod.example`: modelo de variaveis de producao sem segredos reais.
- `ops/deploy/production/docker-compose.yml`: servicos de producao.
- `ops/deploy/production/Caddyfile`: HTTPS automatico e proxy reverso.
- `ops/deploy/production/deploy.sh`: fluxo de deploy na EC2.
- `.github/workflows/deploy.yml`: testes em `main` e deploy futuro via SSM.

Consulte `ops/deploy/production/README.md` para a instalacao inicial e os comandos de deploy.

## Specs e skills

Antes de alterar comportamento, consulte:

- `docs/specs/architecture/frontend-web.md`
- `docs/specs/architecture/backend-api.md`
- `docs/specs/architecture/admin-ops.md`
- `docs/specs/architecture/database.md`
- `docs/specs/features/`
- `docs/specs/testing/`

Skills locais uteis:

- `tools/skills/gotrendlabs/gotrendlabs-architecture-guard/SKILL.md`
- `tools/skills/gotrendlabs/gotrendlabs-django-web/SKILL.md`
- `tools/skills/gotrendlabs/gotrendlabs-fastapi-domain/SKILL.md`
- `tools/skills/gotrendlabs/gotrendlabs-test-strategy/SKILL.md`
- `tools/skills/gotrendlabs/gotrendlabs-postgres-modeling/SKILL.md`
- `tools/skills/gotrendlabs/gotrendlabs-software-architect/SKILL.md`

## Regras atuais importantes

- Handles publicos sao canonicos no formato `@nome`, nascem automaticamente do nome publico e preservam unicidade com sufixo.
- Os cards de destaque do feed priorizam ate dois mercados publicados nao cancelados com mais visualizacoes; empate usa o mercado mais novo.
- Marcacoes editoriais de destaque continuam existindo para curadoria, mas nao superam a ordenacao por visualizacoes no card principal da home.
- Os filtros da home sao ordenacoes/recortes client-side: tendencia, novos, aberto, encerrado, resolvidos, volume, mais curtidas, favoritos pessoais autenticados e minhas previsoes.
- O dashboard do Admin Ops consome o resumo staff da FastAPI (`/admin/dashboard-summary`) e acompanha saúde operacional; criação de mercados fica concentrada na área `Mercados`.
- GTL Credits sao educativos e nao representam dinheiro real.
