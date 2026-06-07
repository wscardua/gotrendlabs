# GoTrendLabs Skills

Fonte canônica das skills do GoTrendLabs. Essas skills orientam agentes de IA a trabalhar com specs, arquitetura, testes, memória operacional e implementação por stack.

## Organização do repo

- A FastAPI vive em `apps/api/backend_api/`; apps Django, templates e assets web vivem em `apps/web/`; deploy, scripts operacionais e Docker local vivem em `ops/`.
- A estrutura alvo é documentada em `apps/api/`, `apps/web/`, `apps/mobile/`, `ops/` e `packages/contracts/`.
- `apps/mobile/` é apenas reserva nesta fase; não há spec Flutter nem projeto mobile ainda.
- `packages/contracts/openapi/gotrendlabs-api.json` é o snapshot OpenAPI versionado da FastAPI; regenere com `python packages/contracts/export_openapi.py` ao mudar endpoints, payloads ou schemas.
- `tools/skills/gotrendlabs/` permanece na raiz como ferramenta de desenvolvimento e governança do monorepo inteiro.
- Guardrail central: Django web/Admin Ops e futuro mobile são clientes; FastAPI concentra domínio, inteligência, IA, wallet, reputação, badges, resolução, auditoria e integrações.
- Apps Django em `apps/web/django/` devem preservar `AppConfig.label` historico e migrations estaveis.

## Skills de governança

| Skill | Quando usar | Saída esperada |
|---|---|---|
| `gotrendlabs-workflow-governor` | processo multi-documento, retomada, bloqueio, conclusão ou reversão lógica | workflow run atualizado e checklist validado |
| `gotrendlabs-spec-editor` | criar, traduzir, normalizar ou alterar specs | feature specs, contratos, changelogs e estado coerentes |
| `gotrendlabs-spec-orchestrator` | implementar ou retomar feature usando docs | sequência por camada e estado atualizado |
| `gotrendlabs-software-architect` | definir arquitetura, segurança e desenho técnico antes de mudanças relevantes | desenho por camada, riscos, ADRs e mitigação |
| `gotrendlabs-architecture-guard` | validar fronteiras técnicas | alertas de acoplamento e necessidade de ADR |
| `gotrendlabs-test-strategy` | definir aceite, cobertura e regressões | testes esperados e critérios verificáveis |
| `gotrendlabs-test-engineer` | implementar, revisar e executar testes concretos | testes executáveis, evidência e lacunas registradas |

## Skills técnicas

| Skill | Quando usar | Saída esperada |
|---|---|---|
| `gotrendlabs-django-web` | Django, templates, HTMX, Alpine.js, i18n e admin | UI alinhada aos contratos e sem regra crítica na apresentação |
| `gotrendlabs-fastapi-domain` | FastAPI, domínio, autenticação e endpoints | regras centralizadas, payloads claros e erros previsíveis |
| `gotrendlabs-postgres-modeling` | PostgreSQL, ledger, integridade e índices | modelagem auditável e aderente ao domínio |
| `gotrendlabs-ops-scheduler-communications` | scheduler, eventos, emails e async ops | jobs idempotentes, comunicações rastreáveis e eventos estáveis |

## Skills de produto e curadoria

| Skill | Quando usar | Saída esperada |
|---|---|---|
| `gotrendlabs-prediction-markets` | sugerir mercados de previsão com dados internos, trends sociais/cripto, diversidade e links exatos de verificação | mercados binários/múltiplos com prazo, fonte, critério objetivo, aviso de risco para cripto e anti-repetição |

## Ordem recomendada

1. `gotrendlabs-workflow-governor`
2. `gotrendlabs-spec-editor`
3. `gotrendlabs-software-architect`
4. `gotrendlabs-architecture-guard`
5. `gotrendlabs-test-strategy`
6. skill técnica adequada
7. `gotrendlabs-test-engineer`
8. `gotrendlabs-spec-orchestrator`

## Regra central

Conhecimento persistente fica em `docs/specs/`. Skills são leves e ensinam o processo.
