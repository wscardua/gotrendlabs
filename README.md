# Orynth

Orynth e uma rede social de previsoes com moeda educativa, reputacao publica e resolucao auditavel de mercados. O produto combina uma interface web server-rendered em Django com uma API de dominio em FastAPI e persistencia em PostgreSQL.

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
BACKEND_API_URL=http://127.0.0.1:8001
RECAPTCHA_ENABLED=0
RECAPTCHA_SITE_KEY=
RECAPTCHA_SECRET_KEY=
```

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
- Os cards de destaque do feed sao configurados no Admin Ops por mercado e ate dois mercados podem ficar em destaque por vez.
- Se o feed tiver menos de dois destaques editoriais elegiveis, a home completa com mercados mais curtidos; empate usa o mercado mais novo.
- Os filtros da home sao ordenacoes client-side: tendencia, encerramento, volume, novos e favoritos editoriais.
- O dashboard do Admin Ops e uma tela de acompanhamento; criacao de mercados fica concentrada na area `Mercados`.
- Orynth Coins sao educativos e nao representam dinheiro real.
