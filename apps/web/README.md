# Web

Diretorio reservado para a futura organizacao da camada web Django do GoTrendLabs.

Nesta fase de fundacao, Django, templates e assets continuam nos caminhos atuais:

- `config/`
- apps Django no topo do repo, como `accounts/`, `core/`, `markets/`, `admin_ops/`, `wallet/`, `profiles/`, `agents/`, `communications/` e `system_logs/`
- `templates/`
- `static/`

Quando a migracao fisica acontecer, templates e static poderao ser movidos para `apps/web/` e os apps Django so devem ser movidos com preservacao explicita de `AppConfig.label` e migrations.

Guardrail: Django renderiza web/Admin Ops e consome contratos; regra critica de dominio continua na FastAPI.
