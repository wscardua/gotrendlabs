# Web

Diretorio da camada web Django do GoTrendLabs.

Estrutura vigente:

- `apps/web/django/`: apps Django do produto (`accounts`, `core`, `markets`, `admin_ops`, `wallet`, `profiles`, `agents`, `communications` e `system_logs`).
- `apps/web/templates/`
- `apps/web/static/`

`config/` permanece na raiz como entrada Django para settings, URLs e WSGI/ASGI.

Os apps em `apps/web/django/` preservam `AppConfig.label` historico para manter migrations e nomes de tabela estaveis.

Guardrail: Django renderiza web/Admin Ops e consome contratos; regra critica de dominio continua na FastAPI.
