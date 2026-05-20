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
- `FEAT-NOTIFY-001` depende de eventos do domínio, preferências de idioma, configuração SMTP em `orynth_site_config` e segredo de envio em ambiente/secret manager
- `FEAT-I18N-001` é transversal às demais features
- `FEAT-OPSLOG-001` depende de `FEAT-AUTH-001` para autorização staff dos contratos administrativos

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
- `FEAT-OPSLOG-001` registra requests Django/FastAPI e logs Python em `orynth_system_logs`; Admin Ops consome `/admin/system-logs` para troubleshooting sem alterar domínio.
- Admin Ops consome `GET /admin/dashboard-summary` via FastAPI para consolidar métricas operacionais de mercados, filas, usuários, engajamento, wallet, badges, logs, manutenção, SMTP e reCAPTCHA.
- Config operacional usa duas fontes por fronteira: modo manutenção em JSON runtime para sobreviver sem banco/API e parâmetros SMTP não sensíveis em `orynth_site_config`.
- Recarga educativa de wallet usa `orynth_site_config.wallet_recharge_min_balance_oc` como piso operacional configurado no Admin Ops; Django e FastAPI bloqueiam solicitação quando `available_oc` está acima desse valor.
- Status do daemon no Dashboard usa `orynth_site_config.daemon_stale_after_minutes` e `orynth_site_config.daemon_missing_after_minutes` como limites operacionais configurados no Admin Ops.
- Ranking web consome `GET /rankings` como fonte autoritativa e usa `Carregar mais` em blocos cumulativos de 10 linhas sem recalcular reputação no Django.

## Skills técnicas por stack

- `orynth-django-web`: páginas, templates, HTMX, Alpine.js, i18n de interface e admin Django
- `orynth-fastapi-domain`: domínio, contratos, autenticação, endpoints e regras centrais
- `orynth-postgres-modeling`: modelagem relacional, ledger, integridade, índices e rastreabilidade
- `orynth-ops-scheduler-communications`: jobs temporizados, eventos, emails, observabilidade operacional e fluxos assíncronos

## Skills de produto e curadoria

- `orynth-prediction-markets`: sugere mercados de previsão binários ou múltiplos usando dados internos da Orynth, trends sociais, links exatos de verificação, diversidade editorial e checagem anti-repetição

## Skill de governança de processo

- `orynth-workflow-governor`: abre, acompanha, retoma, bloqueia, conclui, cancela ou substitui workflows que tocam múltiplos documentos
- `orynth-software-architect`: define arquitetura, segurança, módulos, riscos, ADRs e desenho técnico para mudanças relevantes
- `orynth-test-engineer`: implementa, revisa e executa testes concretos de backend, frontend, contratos, integração e fluxos

## Documentos de workflow

- `docs/specs/workflows/`: templates canônicos de processo
- `docs/specs/state/workflow-runs.md`: memória operacional de execuções
- `docs/specs/state/workflow-checklists.md`: checklists de conclusão e qualidade
