# Integration Map

## Dependências principais

- `FEAT-AUTH-001` suporta as demais features autenticadas
- `FEAT-MARKET-001` depende de `FEAT-AUTH-001` para visão autenticada e personalização
- `FEAT-MARKET-002` depende de `FEAT-MARKET-001`
- `FEAT-PRED-001` depende de `FEAT-MARKET-002`, `FEAT-WALLET-001` e `FEAT-AUTH-001`
- `FEAT-RES-001` depende de `FEAT-PRED-001`, `FEAT-WALLET-001`, `FEAT-REP-001` e `admin-ops`
- `FEAT-REP-001` depende de `FEAT-RES-001`
- `FEAT-COMMENT-001` depende de `FEAT-MARKET-002` e `FEAT-AUTH-001`
- `FEAT-SUGGEST-001` depende de `FEAT-AUTH-001` e `admin-ops`
- `FEAT-NOTIFY-001` depende de eventos do domínio e preferências de idioma
- `FEAT-I18N-001` é transversal às demais features

## Contratos com maior reutilização

- `market-lifecycle.md`
- `prediction-payloads.md`
- `wallet-ledger.md`
- `reputation-ranking.md`
- `i18n-content.md`
- `domain-events.md`

## Integrações já materializadas

- `FEAT-COMMENT-001` usa `FEAT-AUTH-001` para autor/reação autenticada e staff em moderação.
- `FEAT-COMMENT-001` usa `FEAT-MARKET-002` para vínculo com mercado e exposição em `MarketResponse.comments`.
- Admin Ops consome comentários via FastAPI e pode degradar para Postgres local em desenvolvimento quando a API estiver desatualizada.
- `FEAT-AUTH-001` e `FEAT-SUGGEST-001` compartilham validação reCAPTCHA server-side configurável por ambiente.
- Django renderiza o widget v2 e encaminha `recaptcha_token`; FastAPI é a autoridade de validação para cadastro e envios guest.

## Skills técnicas por stack

- `orynth-django-web`: páginas, templates, HTMX, Alpine.js, i18n de interface e admin Django
- `orynth-fastapi-domain`: domínio, contratos, autenticação, endpoints e regras centrais
- `orynth-postgres-modeling`: modelagem relacional, ledger, integridade, índices e rastreabilidade
- `orynth-ops-scheduler-communications`: jobs temporizados, eventos, emails, observabilidade operacional e fluxos assíncronos

## Skill de governança de processo

- `orynth-workflow-governor`: abre, acompanha, retoma, bloqueia, conclui, cancela ou substitui workflows que tocam múltiplos documentos
- `orynth-software-architect`: define arquitetura, segurança, módulos, riscos, ADRs e desenho técnico para mudanças relevantes
- `orynth-test-engineer`: implementa, revisa e executa testes concretos de backend, frontend, contratos, integração e fluxos

## Documentos de workflow

- `docs/specs/workflows/`: templates canônicos de processo
- `docs/specs/state/workflow-runs.md`: memória operacional de execuções
- `docs/specs/state/workflow-checklists.md`: checklists de conclusão e qualidade
