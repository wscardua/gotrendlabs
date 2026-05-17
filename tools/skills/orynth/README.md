# Orynth Skills

Fonte canônica das skills do Orynth. Essas skills orientam agentes de IA a trabalhar com specs, arquitetura, testes, memória operacional e implementação por stack.

## Skills de governança

| Skill | Quando usar | Saída esperada |
|---|---|---|
| `orynth-workflow-governor` | processo multi-documento, retomada, bloqueio, conclusão ou reversão lógica | workflow run atualizado e checklist validado |
| `orynth-spec-editor` | criar, traduzir, normalizar ou alterar specs | feature specs, contratos, changelogs e estado coerentes |
| `orynth-spec-orchestrator` | implementar ou retomar feature usando docs | sequência por camada e estado atualizado |
| `orynth-software-architect` | definir arquitetura, segurança e desenho técnico antes de mudanças relevantes | desenho por camada, riscos, ADRs e mitigação |
| `orynth-architecture-guard` | validar fronteiras técnicas | alertas de acoplamento e necessidade de ADR |
| `orynth-test-strategy` | definir aceite, cobertura e regressões | testes esperados e critérios verificáveis |
| `orynth-test-engineer` | implementar, revisar e executar testes concretos | testes executáveis, evidência e lacunas registradas |

## Skills técnicas

| Skill | Quando usar | Saída esperada |
|---|---|---|
| `orynth-django-web` | Django, templates, HTMX, Alpine.js, i18n e admin | UI alinhada aos contratos e sem regra crítica na apresentação |
| `orynth-fastapi-domain` | FastAPI, domínio, autenticação e endpoints | regras centralizadas, payloads claros e erros previsíveis |
| `orynth-postgres-modeling` | PostgreSQL, ledger, integridade e índices | modelagem auditável e aderente ao domínio |
| `orynth-ops-scheduler-communications` | scheduler, eventos, emails e async ops | jobs idempotentes, comunicações rastreáveis e eventos estáveis |

## Ordem recomendada

1. `orynth-workflow-governor`
2. `orynth-spec-editor`
3. `orynth-software-architect`
4. `orynth-architecture-guard`
5. `orynth-test-strategy`
6. skill técnica adequada
7. `orynth-test-engineer`
8. `orynth-spec-orchestrator`

## Regra central

Conhecimento persistente fica em `docs/specs/`. Skills são leves e ensinam o processo.
