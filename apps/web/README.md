# Web

Diretorio da camada web Django do GoTrendLabs.

Nesta fase da reorganizacao, templates compartilhados e assets estaticos ja vivem aqui:

- `apps/web/templates/`
- `apps/web/static/`

Os apps Django continuam nos caminhos historicos por enquanto:

- `config/`
- apps Django no topo do repo, como `accounts/`, `core/`, `markets/`, `admin_ops/`, `wallet/`, `profiles/`, `agents/`, `communications/` e `system_logs/`

Uma migracao futura dos apps Django para `apps/web/django/` so deve acontecer com preservacao explicita de `AppConfig.label`, imports e migrations.

Guardrail: Django renderiza web/Admin Ops e consome contratos; regra critica de dominio continua na FastAPI.
