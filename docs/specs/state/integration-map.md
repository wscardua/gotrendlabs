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
- `FEAT-NOTIFY-001` depende de eventos do domínio, preferências de idioma, configuração SMTP em `gotrendlabs_site_config` e segredo de envio em ambiente/secret manager
- `FEAT-I18N-001` é transversal às demais features
- `FEAT-OPSLOG-001` depende de `FEAT-AUTH-001` para autorização staff dos contratos administrativos
- `FEAT-MOBILE-001` depende de `FEAT-AUTH-001`, `FEAT-MARKET-001`, `FEAT-MARKET-002`, `FEAT-PRED-001`, `FEAT-WALLET-001`, `FEAT-COMMENT-001`, `FEAT-REP-001` e contratos FastAPI/OpenAPI para operar como cliente mobile sem regra crítica local

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
- `FEAT-MARKET-001` fornece taxonomia `categoria -> subcategoria -> evento` para criação/edição de mercados, cards públicos e filtros administrativos; avisos opcionais de categoria/subcategoria/evento alimentam somente detalhe/ticket público abaixo do critério de resolução, e eventos sem mercados vinculados podem ser excluídos no Admin Ops.
- `FEAT-REP-001` consome a mesma taxonomia para recorte opcional de badges por categoria/subcategoria/evento; regras por evento só contam dados de domínio que carregam evento persistido.
- Admin Ops consome comentários via FastAPI e pode degradar para Postgres local em desenvolvimento quando a API estiver desatualizada.
- `FEAT-AUTH-001` e `FEAT-SUGGEST-001` compartilham validação reCAPTCHA server-side configurável por ambiente.
- Django renderiza o widget v2 e encaminha `recaptcha_token`; FastAPI é a autoridade de validação para cadastro e envios guest.
- `FEAT-OPSLOG-001` registra requests Django/FastAPI e logs Python em `gotrendlabs_system_logs`; Admin Ops consome `/admin/system-logs` para troubleshooting sem alterar domínio e configura `system_log_retention_days`.
- Admin Ops consome `GET /admin/dashboard-summary` via FastAPI para consolidar métricas operacionais de mercados, filas, usuários, engajamento, wallet, badges, logs, manutenção, email e reCAPTCHA.
- Config operacional usa duas fontes por fronteira: modo manutenção web/mobile em JSON runtime para sobreviver sem banco/API e parâmetros não sensíveis de email em `gotrendlabs_site_config`.
- Resend usa API HTTPS com domínio remetente verificado; SMTP permanece como fallback genérico configurável. O app usa apenas parâmetros não sensíveis em `gotrendlabs_site_config` e segredo em ambiente/secret manager.
- `communications` integra `FEAT-AUTH-001`, `FEAT-RES-001`, `FEAT-WALLET-001` e o daemon por meio de `EmailDelivery`: boas-vindas, confirmação de email, reset de senha, mercado fechado/resolvido e crédito concedido são enfileirados com idempotência e enviados conforme provider SMTP/Resend.
- Admin Ops expõe `Politica de Emails`, consumindo `EmailTemplate` para edição simples de assunto/corpos por chave/idioma, incluindo o rodapé transacional especial `system.transactional_footer`, e `EmailDelivery` para logs filtráveis de outbox, sem expor senha/API key de email nem contexto/corpo com links sensíveis.
- `communications` integra push mobile por meio de `PushDelivery`: toda entrega deriva de `gotrendlabs_user_notifications`, aplica `PushEventPolicy`/`PushPreference`, usa provider `none`/dry-run por padrão e envia FCM real apenas quando `GOTRENDLABS_PUSH_ENABLED=1`, provider `fcm`, dry-run desligado e credencial Firebase vier do ambiente/secret manager.
- Admin Ops expõe `Política de Push`, consumindo `PushTemplate`, `PushEventPolicy` e `PushDelivery` para edição operacional e logs sem expor token de dispositivo, payload sensível ou credencial Firebase.
- Recarga educativa de wallet usa `gotrendlabs_site_config.wallet_recharge_min_balance_gtl` como piso operacional configurado no Admin Ops; Django e FastAPI bloqueiam solicitação quando `available_gtl` está acima desse valor.
- Reforço/revisão de posição usa `gotrendlabs_site_config` para flags, limite de reforços, limite de revisões, cutoff, penalidade e mínimos; FastAPI valida e executa as mutações de previsão/wallet com lock transacional por usuário/mercado, Django web apenas consome preview/ação e o mobile deve reutilizar os mesmos contratos em fase posterior.
- Status do daemon no Dashboard usa `gotrendlabs_site_config.daemon_stale_after_minutes` e `gotrendlabs_site_config.daemon_missing_after_minutes` como limites operacionais configurados no Admin Ops.
- Ranking web consome `GET /rankings` como fonte autoritativa, filtra por categoria/subcategoria/evento, exibe badges conquistadas resumidas após o handle e usa `Carregar mais` em blocos cumulativos de 10 linhas sem recalcular reputação ou elegibilidade de badges no Django.
- Deploy MVP usa EC2 com Docker Compose para `proxy`, `django`, `fastapi` e `daemon`; PostgreSQL de producao fica em RDS/servico gerenciado fora do Compose.
- O volume Docker `gotrendlabs_mediafiles` é compartilhado por Caddy/Django e montado read-only no FastAPI para que mídia `/media/...` seja servida pelo proxy e validada pela API antes de aparecer em payloads públicos.
- Infra AWS base de producao foi provisionada em `us-east-1` com EC2 `t4g.micro`, RDS PostgreSQL 16 `db.t4g.micro`, VPC dedicada, SSM, CloudWatch minimo, Parameter Store, Secrets Manager e role OIDC restrita para GitHub Actions no branch `main`; o workflow de deploy agora faz preflight de variables/secrets e valida `aws sts get-caller-identity` antes do `ssm send-command`.
- Acesso administrativo ao RDS usa tunel SSM pela EC2; o RDS permanece privado e aceita `5432` somente do security group da EC2.
- Workflow `.github/workflows/deploy.yml` roda testes em `main` e esta preparado para disparar `ops/deploy/production/deploy.sh` via SSM quando os secrets/variables do GitHub e `.env.prod` da EC2 estiverem configurados.
- `FEAT-AIAGENT-001` integra `apps/api/backend_api/agent_services.py` ao daemon operacional, usa `gotrendlabs_site_config` para flags/limites/retenção de auditoria, `gotrendlabs_ai_agents` para personas oficiais, `gotrendlabs_ai_agent_actions` para auditoria e exclui bots de ranking/badges/reputação pública.
- Admin Ops consome contratos staff de mercado para busca textual no browse e detalhe de participantes por mercado, mantendo Django como camada de exibição e FastAPI/backend como fonte das métricas humano/bot/total.
- `FEAT-MOBILE-001` integra o app Flutter em `apps/mobile` à FastAPI como cliente JSON, reutilizando `GET /markets`, `GET /markets/{slug}`, `POST /markets/{slug}/view`, `POST /markets/{slug}/share`, `GET /taxonomy`, `GET /stats`, `GET /health`, contratos autenticados de sessão/usuário, favoritos, curtidas, comentários, preview/criação de previsão inicial, wallet/recarga, ranking, badges e alertas; flags autenticados como `viewer_has_favorite` e `viewer_has_prediction` alimentam recortes pessoais no app sem recalcular domínio no cliente. Reforço/revisão de posição fica pendente no app até implementação mobile dedicada.
- `FEAT-MOBILE-001` usa `GET /health` enriquecido para o boot gate de manutencao mobile; Admin Ops controla `mobile_maintenance_enabled` em runtime JSON separado do modo web, FastAPI bloqueia chamadas mobile por `X-GoTrendLabs-Client: mobile`, e nao ha excecao por papel no app.
- `FEAT-MOBILE-001` consome os contratos autenticados de push (`/users/me/push-devices` e `/users/me/push-preferences`) por repository/controller; QA local pode registrar um device fake autenticado com `GTL_PUSH_FAKE_TOKEN`, e Android com `google-services.json` local coleta token FCM apenas após autenticação.
- A tela mobile `Sobre` pode consultar a saúde da API e dados seguros da sessão, mas não deve expor endereços de API/web, tokens, segredos ou ID interno do usuário na UI nem no diagnóstico copiado.
- `FEAT-MOBILE-001` publica o beta Android pelo site: Django expõe CTA direto no rodape, nas telas de acesso e nas paginas de compartilhamento, expõe `/app/android/latest.json`, Admin Ops gerencia `MobileAppRelease`, arquivos ficam em media e Caddy serve `/media/app_releases/android/...` por HTTPS.
- Produção expõe a FastAPI para o app mobile em `https://gotrendlabs.com.br/api/*`, com Caddy removendo o prefixo `/api` antes de encaminhar para `fastapi:8001`; mudanças no `Caddyfile` precisam recriar/recarregar o container `proxy` para que o roteamento em execucao acompanhe o arquivo versionado.
- No emulador Android, o mobile consome a API local por `http://10.0.2.2:8001`; `127.0.0.1` dentro do emulador aponta para o próprio dispositivo emulado.
- No iOS Simulator, o mobile consome a API/web local do Mac por `http://127.0.0.1:8001` e `http://127.0.0.1:8000`, mantendo o mesmo contrato FastAPI e apenas trocando a base local por plataforma.
- A estratégia v1 de autenticação persistente mobile usa Bearer em secure storage quando `Lembrar login` está ligado e token apenas em memória quando desligado; refresh token, renovação automática e revogação avançada continuam como evolução futura.

## Skills técnicas por stack

- `gotrendlabs-django-web`: páginas, templates, HTMX, Alpine.js, i18n de interface e admin Django
- `gotrendlabs-fastapi-domain`: domínio, contratos, autenticação, endpoints e regras centrais
- `gotrendlabs-postgres-modeling`: modelagem relacional, ledger, integridade, índices e rastreabilidade
- `gotrendlabs-ops-scheduler-communications`: jobs temporizados, eventos, emails, observabilidade operacional e fluxos assíncronos
- `gotrendlabs-mobile-architect`: arquitetura Flutter, navegação, estado, ambiente Android e fronteiras mobile/FastAPI
- `gotrendlabs-mobile-api-contract-guard`: contratos FastAPI, OpenAPI, auth, payloads e erros consumidos pelo app mobile
- `gotrendlabs-mobile-flutter-implementer`: implementação Flutter em `apps/mobile` guiada por specs
- `gotrendlabs-mobile-test-strategy`: testes unitários, widget, repository, integration, smoke Android e QA visual mobile
- `gotrendlabs-mobile-ux-designer`: UX/UI dark-first, componentes, telas e aderência às referências visuais fornecidas sem cópia literal

## Skills de produto e curadoria

- `gotrendlabs-prediction-markets`: sugere mercados de previsão binários ou múltiplos usando dados internos da GoTrendLabs, trends sociais/cripto, links exatos de verificação, diversidade editorial, aviso de risco para cripto e checagem anti-repetição

## Skill de governança de processo

- `gotrendlabs-workflow-governor`: abre, acompanha, retoma, bloqueia, conclui, cancela ou substitui workflows que tocam múltiplos documentos
- `gotrendlabs-software-architect`: define arquitetura, segurança, módulos, riscos, ADRs e desenho técnico para mudanças relevantes
- `gotrendlabs-test-engineer`: implementa, revisa e executa testes concretos de backend, frontend, contratos, integração e fluxos
- `gotrendlabs-mobile-docs-governor`: mantém docs, status, changelog, workflow, integration map, README e memória sincronizados para mobile

## Documentos de workflow

- `docs/specs/workflows/`: templates canônicos de processo
- `docs/specs/state/workflow-runs.md`: memória operacional de execuções
- `docs/specs/state/workflow-checklists.md`: checklists de conclusão e qualidade
