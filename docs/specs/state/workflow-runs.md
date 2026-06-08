# Workflow Runs

Use este arquivo como memória operacional de processos em andamento, concluídos, bloqueados, cancelados ou substituídos.

## WFLOW-20260608-ANDROID-DIRECT-DOWNLOAD-001

- Tipo: `new-feature`
- Status: `em_validacao`
- Feature alvo: `FEAT-MOBILE-001`
- Objetivo: distribuir beta Android publico pelo site oficial com APK release assinado, Admin Ops de upload, CTA discreto no rodape/login/cadastro/compartilhamento, checksum publico e API mobile em `/api/*`
- Etapa atual: implementacao local validada; smoke de producao pos-deploy e upload de APK assinado real ainda pendentes
- Artefatos afetados:
  - `apps/mobile/android/`
  - `apps/mobile/README.md`
  - `apps/web/django/admin_ops/`
  - `apps/web/django/core/`
  - `apps/web/templates/`
  - `apps/web/static/css/gotrendlabs.css`
  - `ops/deploy/production/Caddyfile`
  - `docs/specs/`
  - `tests/test_web_smoke.py`
- Bloqueios: smoke de producao depende de deploy em `main` e upload de APK assinado real pelo Admin Ops
- Iniciado em: 2026-06-08
- Atualizado em: 2026-06-08
- Retomada: gerar APK release com keystore real, publicar em `/admin-ops/mobile-releases/`, validar `/api/health`, rodape/login/cadastro/compartilhamento com link direto, download HTTPS e SHA-256
- Reversao logica: remover CTA Android do rodape/login/cadastro/compartilhamento, modelo `MobileAppRelease`, tela Admin Ops e rota Caddy `/api/*`, mantendo o app mobile local intacto
- Evidencias de validacao local: `manage.py check`; `manage.py makemigrations --check --dry-run`; testes focados de pagina Android/Admin Ops/Caddy; suite Django completa `manage.py test --keepdb` com 160 testes OK; `flutter analyze`; `flutter test`; `flutter build apk --debug`; `flutter build apk --release` falhando sem signing conforme esperado; `flutter build apk --release` com keystore temporaria local e defines de producao gerando APK assinado; segredo/keystore temporarios removidos apos validacao

## WFLOW-20260608-MOBILE-PUSH-NOTIFICATIONS-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-NOTIFY-001`, `FEAT-MOBILE-001`, `communications`, `future-mobile`
- Objetivo: iniciar push notifications mobile com FCM como arquitetura alvo, começando por provider `none`/dry-run/noop desligado por padrão
- Etapa atual: concluído; PR #63 mergeada em `main`, `GoTrendLabs CI and Deploy` run `27162536605` passou testes e deploy em 2026-06-08
- Artefatos afetados:
  - `apps/web/django/communications/`
  - `apps/api/backend_api/`
  - `apps/web/django/admin_ops/`
  - `apps/mobile/lib/src/features/push/`
  - `packages/contracts/openapi/gotrendlabs-api.json`
  - `docs/specs/`
- Bloqueios: envio FCM real depende de projeto Firebase, credencial fora do Git/Admin Ops, dependências Flutter Firebase e aprovação operacional explícita
- Iniciado em: 2026-06-08
- Atualizado em: 2026-06-08
- Encerrado em: 2026-06-08
- Retomada: evoluir para FCM real somente com projeto Firebase, credenciais em ambiente/secret manager, dependências Flutter Firebase e aprovação operacional explícita
- Reversão lógica: remover modelos/migration/serviços/endpoints/admin/templates push, retirar Flutter `features/push`, restaurar OpenAPI/specs/state e manter `gotrendlabs_user_notifications`/email intactos
- Evidências de validação local/remota: `manage.py check`; `manage.py makemigrations --check --dry-run`; `packages/contracts/export_openapi.py --check`; suíte Django completa `manage.py test --keepdb` com 155 testes OK; `flutter analyze`; `flutter test`; testes focados de push/Admin Ops/dashboard; `git diff --check`; FastAPI/Django locais reiniciados e `/admin-ops/` renderizou `Push mobile` em Saúde técnica; emulador Android `emulator-5554` executou o app com `GTL_PUSH_FAKE_TOKEN` e registrou `PushDevice` local em `gotrendlabs_push_devices`; GitHub Actions `GoTrendLabs CI and Deploy` run `27162536605` concluiu `test` e `deploy` com sucesso

## WFLOW-20260608-MOBILE-IOS-SIMULATOR-001

- Tipo: `change-feature`
- Status: `em_publicacao`
- Feature alvo: `FEAT-MOBILE-001`, `future-mobile`
- Objetivo: preparar o app Flutter mobile para iOS Simulator sem alterar contratos FastAPI nem regras de domínio
- Etapa atual: estrutura iOS gerada em `apps/mobile/ios`, Xcode/CocoaPods validados localmente, app executado no iPhone Simulator com bases locais via `127.0.0.1` e aguardando aprovação do usuário para abrir PR em português, mergear em `main` e acompanhar `GoTrendLabs CI and Deploy` quando disparado
- Artefatos afetados:
  - `apps/mobile/ios/`
  - `apps/mobile/.metadata`
  - `apps/mobile/README.md`
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/change-log-specs.md`
  - `docs/specs/state/integration-map.md`
  - `docs/specs/state/known-gaps.md`
- Bloqueios: nenhum local; PR, merge e monitoramento de produção dependem de aprovação explícita do usuário
- Iniciado em: 2026-06-08
- Atualizado em: 2026-06-08
- Encerrado em: pendente
- Retomada: após aprovação, stage/commit, push da branch `codex/mobile-ios-simulator-support`, abrir PR em português, mergear em `main`, acompanhar `GoTrendLabs CI and Deploy` se disparado e atualizar este registro para `concluido` ou `bloqueado`
- Reversão lógica: remover `apps/mobile/ios/`, retirar a plataforma iOS de `.metadata`, restaurar README/specs/state para escopo Android-only e manter contratos FastAPI inalterados
- Evidências de validação local: `flutter doctor -v` sem issues com Xcode 26.5 e CocoaPods 1.16.2; `flutter analyze` sem issues; `flutter test` com 16 testes OK; `flutter run -d 53BDA0A2-23E9-4F01-A468-593A2AF0C8A8 --dart-define=GTL_API_BASE_URL=http://127.0.0.1:8001 --dart-define=GTL_PUBLIC_WEB_BASE_URL=http://127.0.0.1:8000` abriu o app no iPhone 17 Simulator; `flutter run -d 207EDA52-ED42-4CCB-AD4E-35F0CAE5A29C` abriu o app no iPhone 17 Pro Max Simulator; screenshots confirmaram a tela mobile carregando dados locais da API

## WFLOW-20260607-MOBILE-ANDROID-MVP-001

- Tipo: `new-feature`
- Status: `em_publicacao`
- Feature alvo: `FEAT-MOBILE-001`, `future-mobile`
- Objetivo: implementar e polir o app Flutter Android do GoTrendLabs como cliente da FastAPI, com design dark-first editorial, feed, detalhe, auth, previsão, comentários, wallet, perfil, ranking, badges, alertas, busca, áreas pessoais e tela `Sobre`
- Etapa atual: implementação local validada; docs/specs reconciliados; aguardando aprovação do usuário para abrir PR em português, mergear em `main` e acompanhar o workflow de produção quando disparado
- Artefatos afetados:
  - `apps/mobile/`
  - `apps/mobile/lib/src/ui/`
  - `apps/mobile/lib/src/features/info/about_screen.dart`
  - `apps/mobile/test/about_screen_test.dart`
  - `apps/mobile/test/markets_screen_test.dart`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/integration-map.md`
  - `docs/specs/state/known-gaps.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `apps/mobile/README.md`
- Bloqueios: nenhum local; PR, merge e monitoramento de produção dependem de aprovação explícita do usuário
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Encerrado em: pendente
- Retomada: após aprovação, stage/commit, push da branch `feature/mobile-android-design-refresh`, abrir PR em português, mergear em `main`, acompanhar `GoTrendLabs CI and Deploy` e atualizar este registro para `concluido` ou `bloqueado`
- Reversão lógica: reverter o refresh visual em `apps/mobile`, remover a tela `Sobre`, filtros pessoais e componentes compartilhados novos, restaurar README/status/changelog/acceptance/integration map/workflow desta fatia e manter os contratos FastAPI sem alteração
- Evidências de validação local: `flutter pub get`; `flutter analyze` sem issues; `flutter test` com 16 testes OK; `flutter build apk --debug` gerou APK debug com aviso não bloqueante do Kotlin Gradle Plugin transitivo em `package_info_plus`/`share_plus`; APK instalado no `emulator-5554`; smoke visual em emulador para `Hoje`, `Mercados`, detalhe, alertas e `Sobre`; `Sobre` exibe apenas saúde da API, versão/build, pacote/plataforma e dados seguros da conta, sem endereço de API/web, token, segredo ou ID interno; contratos OpenAPI e regras de domínio permanecem inalterados

## WFLOW-20260607-MOBILE-SPECS-SKILLS-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `future-mobile`
- Objetivo: criar specs e skills locais para iniciar o app Flutter Android do GoTrendLabs com design mobile inspirado nas referências fornecidas pelo usuário e governança docs/memória
- Etapa atual: concluido; specs mobile criadas, skills mobile adicionadas, README mobile atualizado, estado/changelog/integration map/known gaps alinhados e projeto Flutter mantido como próxima etapa
- Artefatos afetados:
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/features/mobile-mvp.md`
  - `docs/specs/features/mobile-ux.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/change-log-specs.md`
  - `docs/specs/state/integration-map.md`
  - `docs/specs/state/known-gaps.md`
  - `apps/mobile/README.md`
  - `tools/skills/gotrendlabs/`
- Bloqueios: nenhum para specs; antes de login persistente falta decisão técnica de autenticação mobile segura
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Encerrado em: 2026-06-07
- Retomada: revisar specs com o usuário e criar o projeto Flutter em `apps/mobile` quando aprovado
- Reversão lógica: remover as specs/skills mobile criadas nesta fatia e restaurar `apps/mobile/README.md` como reserva sem spec Flutter
- Evidências de validação: revisão documental contra skills mobile, arquitetura existente e referências visuais fornecidas; sem testes executáveis porque não houve código Flutter

## WFLOW-20260607-ADMIN-CONTRACTS-TIMELINE-001

- Tipo: `change-feature`
- Status: `em_validacao`
- Feature alvo: `FEAT-MARKET-001`, `admin-ops`
- Objetivo: adicionar painel administrativo read-only para organização operacional de contratos/mercados ativos e pendentes
- Etapa atual: implementação local concluída; aguardando publicação via PR e validação do workflow de produção
- Artefatos afetados:
  - `apps/web/django/admin_ops/views.py`
  - `apps/web/django/admin_ops/templates/admin_ops/contracts.html`
  - `apps/web/django/admin_ops/templates/admin_ops/markets.html`
  - `apps/web/static/css/gotrendlabs.css`
  - `config/urls.py`
  - `tests/test_web_smoke.py`
  - `docs/specs/architecture/admin-ops.md`
  - `docs/specs/architecture/backend-api.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
- Bloqueios: nenhum
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Retomada: após aprovação, abrir PR em português, mergear em `main`, acompanhar `GoTrendLabs CI and Deploy` e atualizar este registro para `concluido` ou `bloqueado`
- Reversão lógica: remover rota `/admin-ops/contracts/`, botão no browse de mercados, helper de timeline no Django, template/CSS do painel e teste focado
- Evidências de validação local: `manage.py check`, `makemigrations --check --dry-run`, teste focado `tests.test_web_smoke.WebSmokeTests.test_admin_contracts_timeline_uses_active_market_contract_dates`, render manual com API mockada e `git diff --check`

## WFLOW-20260607-WEB-ASSETS-LAYOUT-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `frontend-web`, `repo-layout`
- Objetivo: mover templates e assets compartilhados da web para `apps/web/` sem mover apps Django
- Etapa atual: concluido; `templates/` movido para `apps/web/templates/`, `static/` movido para `apps/web/static/`, settings/docs/skills atualizados e apps Django preservados nos caminhos historicos
- Artefatos afetados:
  - `apps/web/templates/`
  - `apps/web/static/`
  - `config/settings.py`
  - `README.md`
  - `docs/specs/architecture/frontend-web.md`
  - `docs/specs/state/feature-changelog.md`
  - `tools/skills/gotrendlabs/`
- Bloqueios: nenhum
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Encerrado em: 2026-06-07
- Retomada: próxima reorganização web deve avaliar se vale mover apps Django para `apps/web/django/`, preservando `AppConfig.label`, migrations e imports
- Reversão lógica: mover `apps/web/templates/` de volta para `templates/`, `apps/web/static/` de volta para `static/` e restaurar `TEMPLATES["DIRS"]`/`STATICFILES_DIRS`
- Evidências de validação: `manage.py check`, `manage.py findstatic css/gotrendlabs.css js/gotrendlabs.js brand/gtl-logo.svg`, suite `manage.py test --keepdb` com 150 testes OK e `manage.py collectstatic --noinput`

## WFLOW-20260607-OPS-LAYOUT-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `infra-deploy-mvp`, `repo-layout`
- Objetivo: mover deploy, scripts e Docker local para `ops/` como terceira etapa da reorganização do monorepo
- Etapa atual: concluido; deploy de produção movido para `ops/deploy/production/`, scripts operacionais movidos para `ops/scripts/`, Compose local atualizado para `ops/docker/postgres/data/`, README/specs/skills/testes alinhados e workflow SSM ajustado para atualizar o checkout remoto antes de chamar o script movido
- Artefatos afetados:
  - `ops/deploy/production/`
  - `ops/scripts/`
  - `ops/docker/README.md`
  - `docker-compose.yml`
  - `.github/workflows/deploy.yml`
  - `tests/test_web_smoke.py`
  - `docs/specs/state/feature-changelog.md`
  - `tools/skills/gotrendlabs/`
- Bloqueios: nenhum
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Encerrado em: 2026-06-07
- Retomada: próxima reorganização deve preparar a camada web Django com cuidado para preservar labels, migrations, templates e static
- Reversão lógica: restaurar `deploy/production/`, `scripts/ops/` e `docker/postgres/data/` como caminhos oficiais e reverter referências em workflow, Compose, docs e testes
- Evidências de validação: `manage.py check`, `docker compose config --quiet`, `docker compose -f ops/deploy/production/docker-compose.yml config --quiet --no-env-resolution`, suite `manage.py test --keepdb` com 150 testes OK e correção pós-merge para o checkout SSM antigo que ainda não continha `ops/deploy/production/deploy.sh`

## WFLOW-20260607-FASTAPI-LAYOUT-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `backend-api`, `repo-layout`
- Objetivo: mover fisicamente o runtime FastAPI para `apps/api/backend_api/` como segunda etapa da reorganização do monorepo
- Etapa atual: concluido; pacote FastAPI movido, imports e patches atualizados para `apps.api.backend_api`, comando `uvicorn` local/producao alinhado, specs/skills/docs atualizados e validação local concluida
- Artefatos afetados:
  - `apps/api/backend_api/`
  - `ops/deploy/production/docker-compose.yml`
  - `tests/test_web_smoke.py`
  - `docs/specs/architecture/backend-api.md`
  - `docs/specs/state/feature-changelog.md`
  - `tools/skills/gotrendlabs/`
- Bloqueios: nenhum
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Encerrado em: 2026-06-07
- Retomada: próxima reorganização deve mover `ops/` ou iniciar a preparação da camada web, sem misturar com mudanças funcionais
- Reversão lógica: restaurar o pacote para `backend_api/`, reverter imports para `backend_api.*` e voltar o comando de produção para `uvicorn backend_api.main:app`
- Evidências de validação: `manage.py check`, import direto `from apps.api.backend_api.main import app`, suite `manage.py test --keepdb` com 150 testes OK, `python -m uvicorn apps.api.backend_api.main:app --port 8011`, `GET /health` OK e `/docs` 200

## WFLOW-20260605-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-NOTIFY-001`
- Objetivo: configurar infraestrutura AWS SES SMTP para envio transacional sandbox da GoTrendLabs
- Etapa atual: concluído; identidades SES `gotrendlabs.com.br`/`.com` verificadas, segredo SMTP instalado na produção, teste sandbox validado, production access solicitado e negado no caso `178067031900201`, recurso manual enviado pelo console AWS, comando de teste SMTP, runbook e specs atualizados em 2026-06-05
- Artefatos afetados:
  - `admin_ops/management/commands/send_smtp_test_email.py`
  - `ops/deploy/production/README.md`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: production access do SES foi negado, reenvio imediato por CLI retornou `ConflictException`, a conta sem Premium Support não permite acompanhar/responder ao caso via Support API e o recurso manual enviado pelo console AWS aguarda nova resposta
- Iniciado em: 2026-06-05
- Atualizado em: 2026-06-05
- Encerrado em: 2026-06-05
- Retomada: acompanhar o caso SES `178067031900201`, publicar a branch para disponibilizar `send_smtp_test_email` no deploy e então implementar envio real em `communications`
- Reversão lógica: desativar `email_enabled`, remover segredo do ambiente e revogar usuário IAM SMTP se a integração SES for abandonada

## WFLOW-20260605-002

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-NOTIFY-001`, `FEAT-AUTH-001`
- Objetivo: implementar emails transacionais com SES em hold, outbox + daemon, templates editáveis e confirmação de email com login limitado
- Etapa atual: concluído; `communications` criado com templates/outbox/tokens, FastAPI enfileira emails v1, Django/Admin Ops expõe confirmação/reenvio/templates/teste SMTP, daemon processa entregas com retry e guarda sandbox, specs e testes atualizados
- Artefatos afetados:
  - `communications/`
  - `backend_api/main.py`
  - `backend_api/email_outbox.py`
  - `backend_api/market_lifecycle_engine.py`
  - `backend_api/daemon_services.py`
  - `accounts/`
  - `admin_ops/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: production access do SES segue em hold/negado no caso `178067031900201`; daemon suprime destinatários comuns enquanto `GOTRENDLABS_SES_PRODUCTION_ACCESS` não estiver ativo
- Iniciado em: 2026-06-05
- Atualizado em: 2026-06-05
- Encerrado em: 2026-06-05
- Retomada: quando production access for aprovado, ativar `GOTRENDLABS_SES_PRODUCTION_ACCESS=1`, revisar allowlist e validar envio real para destinatário operacional
- Reversão lógica: desativar `email_enabled`, parar o daemon de envio ou marcar templates inativos, preservando outbox para auditoria

## WFLOW-20260606-SECURITY-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`, `FEAT-OPSLOG-001`, `FEAT-MARKET-001`, `infra-deploy-mvp`
- Objetivo: executar auditoria local de seguranca e endurecer endpoints publicos, redirects, uploads Admin Ops, headers de media e defaults de producao sem alterar regras funcionais de dominio
- Etapa atual: concluido; auditoria local registrada em `docs/audits/security-audit-2026-06-06.md`, hardening aplicado, specs/state alinhados e `.env.prod.example` explicita `GOTRENDLABS_RATE_LIMITS_ENABLED=1`
- Artefatos afetados:
  - `backend_api/main.py`
  - `config/settings.py`
  - `accounts/`, `core/views.py`, `markets/views.py`
  - `admin_ops/views.py`
  - `ops/deploy/production/Caddyfile`, `.env.prod.example`, `ops/deploy/production/README.md`
  - `tests/test_web_smoke.py`
  - `docs/audits/security-audit-2026-06-06.md`
  - `docs/specs/state/`
- Bloqueios: atualizacao de dependencias vulneraveis segue pendente porque o indice local de pacotes ainda nao disponibiliza versoes corrigidas de Pillow/Starlette/python-dotenv
- Iniciado em: 2026-06-06
- Atualizado em: 2026-06-06
- Encerrado em: 2026-06-06
- Retomada: substituir rate limit em memoria por store distribuido quando houver multiplas instancias, atualizar dependencias assim que o indice permitir e acompanhar alertas de scanner no CI
- Reversão lógica: desligar temporariamente `GOTRENDLABS_RATE_LIMITS_ENABLED=0` apenas em contingencia, manter `DJANGO_DEBUG=0` e reverter validacao de upload/redirects somente por PR corretiva com teste
- Evidências de validação: `manage.py check`, `check --deploy` com variaveis de producao, `tests.test_web_smoke.SecurityHardeningTests` com 7 testes OK, suite `tests.test_web_smoke --keepdb` com 150 testes OK, Bandit sem achados High e `pip-audit` registrando pendencias de pacote sem versao corrigida disponivel no indice local

## Modelo

```md
## WFLOW-YYYYMMDD-001

- Tipo: `change-feature`
- Status: `aberto`
- Feature alvo: `FEAT-XXX`
- Objetivo: descrição curta
- Etapa atual: etapa do workflow canônico
- Artefatos afetados:
  - `docs/specs/features/example.md`
- Bloqueios: nenhum
- Iniciado em: YYYY-MM-DD
- Atualizado em: YYYY-MM-DD
- Encerrado em: pendente
- Retomada: próxima ação objetiva
- Reversão lógica: como cancelar ou substituir sem apagar histórico
```

## WFLOW-20260604-GOTRENDLABS-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-I18N-001`, `FEAT-WALLET-001`, `FEAT-AUTH-001`, `FEAT-OPSLOG-001`
- Objetivo: substituir profundamente a identidade da plataforma por GoTrendLabs, com moeda GTL Credits/GT₵ e contratos técnicos `_gtl`
- Etapa atual: concluído; rebrand de código, docs, deploy, migrations de schema/domínio controlado, assets GTL, favicon de navegador, correções de mídia pública, topo Admin Ops e validação local/cloud finalizados em 2026-06-05
- Artefatos afetados:
  - `backend_api/`, `accounts/`, `markets/`, `admin_ops/`, `agents/`, `system_logs/`
  - `templates/`, `static/css/gotrendlabs.css`, `static/js/gotrendlabs.js`, `static/brand/`
  - `ops/deploy/production/`, `.github/workflows/deploy.yml`, `.env.example`, `.env.prod.example`
  - `docs/specs/`, `tools/skills/gotrendlabs/`
- Bloqueios: nenhum
- Iniciado em: 2026-06-04
- Atualizado em: 2026-06-05
- Encerrado em: 2026-06-05
- Retomada: evoluir i18n por catálogos em workflow futuro
- Reversão lógica: restaurar backup `git-all-refs.bundle` e dump local criado antes da mudança; em produção, reverter por snapshot RDS e app dir anterior se o deploy for iniciado
- Evidências de validação: `manage.py check`, `makemigrations --check --dry-run`, suíte completa `129/129` com `--keepdb`, scans de resíduos em código/schema local e cloud, `docker compose config`, containers `gotrendlabs-*` em execução, `maintenance_enabled=False`, `market_thumbnails=39`, `badge_images=30`, domínios `gotrendlabs.com.br`, `www.gotrendlabs.com.br`, `gotrendlabs.com` e `www.gotrendlabs.com` com HTTP 200 e SSL válido; PR #43 publicou favicon SVG nos templates base, GitHub Actions `GoTrendLabs CI and Deploy` concluiu `test` e `deploy` com sucesso e produção respondeu os assets `gtl-constellation-mark-*.svg` como `image/svg+xml`.

## WFLOW-20260528-PUBLIC-COPY-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`, `FEAT-AUTH-001`, `FEAT-REP-001`, `FEAT-SUGGEST-001`
- Objetivo: simplificar a home pública e alinhar a linguagem de produto para tom claro, social e confiável
- Etapa atual: concluído
- Artefatos afetados:
  - `accounts/templates/accounts/`
  - `core/templates/core/`
  - `markets/templates/markets/detail.html`
  - `templates/components/market_card.html`
  - `static/css/gotrendlabs.css`
  - `static/js/gotrendlabs.js`
  - `docs/specs/`
  - `PRODUCT.md`
  - `DESIGN.md`
- Bloqueios: nenhum
- Iniciado em: 2026-05-28
- Atualizado em: 2026-05-28
- Encerrado em: 2026-05-28
- Retomada: extrair strings públicas para `FEAT-I18N-001` quando a internacionalização for priorizada
- Reversão lógica: reintroduzir blocos da home e labels anteriores por nova mudança de UI, preservando specs desta decisão como histórico

## WFLOW-20260524-RETENTION-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-OPSLOG-001`, `FEAT-AIAGENT-001`
- Objetivo: tornar configurável no Admin Ops a retenção de logs técnicos e auditoria de agentes IA
- Etapa atual: concluído
- Artefatos afetados:
  - `admin_ops/`
  - `backend_api/daemon_services.py`
  - `system_logs/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-24
- Atualizado em: 2026-05-24
- Encerrado em: 2026-05-24
- Retomada: acompanhar em produção o primeiro ciclo do daemon após deploy para validar contadores de prune
- Reversão lógica: ocultar campos de retenção no Admin Ops e voltar defaults de 90 dias, preservando colunas em `gotrendlabs_site_config` para compatibilidade

## WFLOW-20260517-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `sistema-documental`
- Objetivo: criar base canônica de specs, contratos, arquitetura, testes, estado e skills
- Etapa atual: concluído
- Artefatos afetados:
  - `docs/specs/`
  - `tools/skills/gotrendlabs/`
  - `docs/guides/ia-spec-workflow.md`
- Bloqueios: nenhum
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: usar novos workflows para mudanças futuras
- Reversão lógica: substituir por novo workflow que revise a estrutura documental

## WFLOW-20260520-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-OPSLOG-001`
- Objetivo: implementar daemon operacional com regras temporizadas centralizadas no backend
- Etapa atual: concluído
- Artefatos afetados:
  - `backend_api/`
  - `system_logs/management/commands/`
  - `admin_ops/templates/admin_ops/dashboard.html`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: daemon ja possui container de producao no deploy EC2; proxima evolucao e alertas externos/observabilidade
- Reversão lógica: desativar execução do comando `run_gotrendlabs_daemon` preservando serviços backend e eventos já registrados

## WFLOW-20260520-018

- Tipo: `change-infra`
- Status: `concluido`
- Feature alvo: `infra-deploy-mvp`, `FEAT-OPSLOG-001`
- Objetivo: preparar deploy MVP em AWS EC2 com Docker Compose, RDS gerenciado, Caddy HTTPS e daemon em container dedicado
- Etapa atual: concluído
- Artefatos afetados:
  - `Dockerfile`
  - `.dockerignore`
  - `.env.prod.example`
  - `ops/deploy/production/`
  - `config/settings.py`
  - `README.md`
  - `docs/specs/spec_prediction_social_market_pt.md`
  - `docs/specs/decisions/ADR-0003-ec2-compose-rds-mvp.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: configurar EC2/RDS reais, preencher `.env.prod` fora do Git, apontar DNS e executar `ops/deploy/production/deploy.sh`
- Reversão lógica: remover artefatos de deploy de producao e voltar settings para defaults locais, preservando specs/ADR como decisão substituída

## WFLOW-20260521-001

- Tipo: `change-infra`
- Status: `concluido`
- Feature alvo: `infra-deploy-mvp`, `FEAT-OPSLOG-001`
- Objetivo: provisionar a base AWS real do MVP com EC2 ARM, RDS PostgreSQL privado, SSM, CloudWatch minimo, segredos/configuracao e role OIDC para GitHub Actions
- Etapa atual: concluido
- Artefatos afetados:
  - `ops/deploy/production/README.md`
  - `ops/deploy/production/deploy.sh`
  - `.github/workflows/deploy.yml`
  - `docs/specs/decisions/ADR-0003-ec2-compose-rds-mvp.md`
  - `docs/specs/state/`
- Bloqueios: nenhum para a infra base; deploy da aplicacao depende de `.env.prod` criado fora do Git na EC2
- Iniciado em: 2026-05-21
- Atualizado em: 2026-05-21
- Encerrado em: 2026-05-21
- Retomada: criar `.env.prod` na EC2, configurar secrets/variables do GitHub, executar primeiro deploy e apontar DNS quando houver dominio
- Reversão lógica: remover recursos AWS provisionados em `us-east-1` usando tags `Project=gotrendlabs`, `Environment=prod`, `ManagedBy=codex-mcp`, preservando ADR como decisão substituída se a estratégia mudar

## WFLOW-20260521-002

- Tipo: `change-infra`
- Status: `concluido`
- Feature alvo: `infra-deploy-mvp`, `FEAT-OPSLOG-001`
- Objetivo: endurecer a autenticacao OIDC do GitHub Actions para o deploy via SSM, adicionando preflight de configuracao e prova explicita da identidade AWS assumida
- Etapa atual: concluido
- Artefatos afetados:
  - `.github/workflows/deploy.yml`
  - `ops/deploy/production/README.md`
  - `docs/specs/state/workflow-runs.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/integration-map.md`
  - `docs/specs/state/known-gaps.md`
- Bloqueios: o deploy automatico ainda depende de `.env.prod` existente na EC2 e do repositório GitHub possuir as variables esperadas
- Iniciado em: 2026-05-21
- Atualizado em: 2026-05-21
- Encerrado em: 2026-05-21
- Retomada: executar o workflow na `main` com `ENABLE_PROD_DEPLOY=1` e validar a etapa `Verify assumed AWS identity` antes do primeiro deploy automatico real
- Reversão lógica: voltar o workflow para a leitura exclusiva de secrets e remover o preflight, preservando esta entrada como histórico de endurecimento operacional

## WFLOW-20260522-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AIAGENT-001`
- Objetivo: implementar agentes IA oficiais para comentários, previsão bot controlada, Admin Ops, saúde técnica e auditoria
- Etapa atual: concluído; app `agents`, ciclo IA, Admin Ops, auditoria, saúde técnica, métricas humano/bot, exclusão de bots, simulações Bedrock e ajustes UX finais validados localmente em 2026-05-23
- Artefatos afetados:
  - `agents/`
  - `backend_api/`
  - `admin_ops/`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-23
- Encerrado em: 2026-05-23
- Retomada: acompanhar deploy em `main`, validar migrations em produção e observar primeiro ciclo daemon com IA desligada por padrão
- Reversão lógica: desativar `ai_agents_enabled` em `gotrendlabs_site_config`, manter auditoria histórica e remover integração do ciclo IA por workflow substituto

## WFLOW-20260520-002

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-WALLET-001`, `FEAT-AUTH-001`
- Objetivo: padronizar símbolo público `GT₵`, expor métricas educativas na home e reorganizar rodapé/Admin Ops
- Etapa atual: concluído
- Artefatos afetados:
  - `backend_api/main.py`
  - `core/domain_client.py`
  - `accounts/api_client.py`
  - `core/templates/core/home.html`
  - `templates/base.html`
  - `templates/components/footer.html`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: evoluir um formatador central de moeda/i18n quando `FEAT-I18N-001` avançar
- Reversão lógica: restaurar labels visíveis antigos, remover métricas públicas da home e voltar Admin Ops para a navegação anterior preservando contratos internos `_gtl`

## WFLOW-20260517-002

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `sistema-documental`
- Objetivo: adicionar changelog por feature e skills técnicas por stack
- Etapa atual: concluído
- Artefatos afetados:
  - `docs/specs/state/feature-changelog.md`
  - `tools/skills/gotrendlabs/gotrendlabs-django-web/`
  - `tools/skills/gotrendlabs/gotrendlabs-fastapi-domain/`
  - `tools/skills/gotrendlabs/gotrendlabs-postgres-modeling/`
  - `tools/skills/gotrendlabs/gotrendlabs-ops-scheduler-communications/`
  - `docs/guides/ia-spec-workflow.md`
- Bloqueios: nenhum
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: usar skills técnicas junto do orquestrador
- Reversão lógica: substituir por novo workflow que altere ou remova skills específicas

## WFLOW-20260517-003

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `sistema-documental`
- Objetivo: adicionar governança de workflows, reforçar testes no guia e revisar eficácia das skills
- Etapa atual: concluído
- Artefatos afetados:
  - `docs/specs/workflows/`
  - `docs/specs/state/workflow-runs.md`
  - `docs/specs/state/workflow-checklists.md`
  - `docs/specs/state/governance-review.md`
  - `tools/skills/gotrendlabs/gotrendlabs-workflow-governor/`
  - `tools/skills/gotrendlabs/README.md`
  - `docs/guides/ia-spec-workflow.md`
  - `tools/skills/gotrendlabs/*/SKILL.md`
- Bloqueios: nenhum
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: abrir novo workflow para qualquer mudança multi-documento
- Reversão lógica: criar workflow substituto que altere o processo canônico

## WFLOW-20260517-004

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `sistema-documental`
- Objetivo: adicionar skills de arquiteto de software/segurança e engenheiro de testes, atualizando fluxos obrigatórios
- Etapa atual: concluído
- Artefatos afetados:
  - `tools/skills/gotrendlabs/gotrendlabs-software-architect/`
  - `tools/skills/gotrendlabs/gotrendlabs-test-engineer/`
  - `tools/skills/gotrendlabs/README.md`
  - `docs/specs/workflows/`
  - `docs/specs/state/workflow-checklists.md`
  - `docs/specs/state/integration-map.md`
  - `docs/guides/ia-spec-workflow.md`
- Bloqueios: nenhum
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: usar `gotrendlabs-software-architect` antes de mudanças relevantes e `gotrendlabs-test-engineer` para testes executáveis
- Reversão lógica: criar workflow substituto que ajuste obrigatoriedade ou escopo das skills

## WFLOW-20260517-005

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`
- Objetivo: mover autenticação/cadastro/sessão para `backend-api` FastAPI e manter Django como web layer consumidor
- Etapa atual: concluído
- Artefatos afetados:
  - `backend_api/`
  - `accounts/`
  - `config/settings.py`
  - `tests/test_web_smoke.py`
  - `requirements.txt`
  - `docs/specs/features/auth-and-session.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/known-gaps.md`
- Bloqueios: login social real depende de credenciais OAuth e decisão de provedor/configuração
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: implementar OAuth Google/Facebook real e endurecer cookies/tokens para ambiente não local
- Reversão lógica: substituir por workflow que troque o contrato de auth/session mantendo a migração de dados explícita

## WFLOW-20260517-006

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-WALLET-001`, `FEAT-REP-001`
- Objetivo: implementar núcleo completo do usuário com perfil, wallet, ledger inicial, reputação base, badges e ranking via FastAPI
- Etapa atual: concluído
- Artefatos afetados:
  - `backend_api/`
  - `accounts/`
  - `profiles/`
  - `wallet/`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/wallet-and-ledger.md`
  - `docs/specs/features/reputation-and-ranking.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/known-gaps.md`
- Bloqueios: fórmula avançada de reputação depende de previsões e resolução de mercados
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: implementar previsão/stake usando o saldo derivado do ledger e depois resolução/payout/reputação avançada
- Reversão lógica: criar workflow substituto que migre ou remova tabelas de núcleo do usuário mantendo trilha de ledger

## WFLOW-20260517-007

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-WALLET-001`
- Objetivo: adicionar projeção `gotrendlabs_wallet_balances` para leitura rápida de saldo mantendo ledger como fonte auditável
- Etapa atual: concluído
- Artefatos afetados:
  - `accounts/`
  - `backend_api/`
  - `tests/test_web_smoke.py`
  - `docs/specs/contracts/wallet-ledger.md`
  - `docs/specs/features/wallet-and-ledger.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: usar helper ledger + balance ao implementar stake, refund, payout e ajustes manuais
- Reversão lógica: reconstruir a projeção a partir do ledger ou substituir por nova projeção versionada

## WFLOW-20260517-008

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`
- Objetivo: adicionar aceite obrigatório de política de uso, edição de perfil e exclusão lógica de conta
- Etapa atual: concluído
- Artefatos afetados:
  - `accounts/`
  - `backend_api/`
  - `profiles/`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/auth-and-session.md`
  - `docs/specs/state/`
- Bloqueios: confirmação de email em alteração de endereço fica para communications
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: implementar confirmação de email, política versionada administrável e OAuth real
- Reversão lógica: criar workflow substituto que reative contas ou migre estados sem apagar histórico

## WFLOW-20260517-009

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`
- Objetivo: mover feed e detalhe de mercado para FastAPI/Postgres mantendo fixture apenas como fallback
- Etapa atual: concluído
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `core/`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/market-feed.md`
  - `docs/specs/features/market-detail.md`
  - `docs/specs/state/`
- Bloqueios: admin CRUD, cálculo real de probabilidades e comentários reais ficam para features futuras
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: implementar FEAT-PRED-001 usando os mercados persistidos como base
- Reversão lógica: fixture permanece disponível como fallback; uma reversão pode desativar consumo da API no Django sem apagar tabelas

## WFLOW-20260518-001

- Tipo: `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-SUGGEST-001`
- Objetivo: implementar primeira fatia real de filas operacionais para sugestões e feedback recompensável
- Etapa atual: concluído; `.venv/bin/python manage.py test` executado com sucesso em 2026-05-18
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `core/`
  - `admin_ops/`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/market-suggestions.md`
  - `docs/specs/features/wallet-and-ledger.md`
  - `docs/specs/contracts/wallet-ledger.md`
  - `docs/specs/contracts/domain-events.md`
  - `docs/specs/architecture/admin-ops.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: próxima fatia pode adicionar event bus assíncrono, histórico público de feedback, comunicações transacionais e moderação de comentários
- Reversão lógica: substituir por workflow que desative endpoints e mantenha dados históricos de filas preservados

## WFLOW-20260518-010

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`, `admin-ops`
- Objetivo: implementar admin real de mercados e taxonomia com FastAPI/Postgres como autoridade e Django como camada web
- Etapa atual: concluído
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `admin_ops/`
  - `accounts/api_client.py`
  - `accounts/session.py`
  - `tests/test_web_smoke.py`
  - `docs/specs/architecture/admin-ops.md`
  - `docs/specs/contracts/market-lifecycle.md`
  - `docs/specs/state/`
- Bloqueios: resolução real, payout, sugestões, feedback, moderação avançada, scheduler e gestão de operadores ficam para features próprias
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: implementar FEAT-PRED-001 ou FEAT-RES-001 usando mercados persistidos e auditados
- Reversão lógica: manter tabelas e eventos; desativar rotas admin ou ocultar ações no Django se for preciso suspender operação

## WFLOW-20260518-011

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`, `admin-ops`
- Objetivo: corrigir regras de opções por tipo de mercado e filtros do browse administrativo
- Etapa atual: concluído
- Artefatos afetados:
  - `backend_api/`
  - `admin_ops/`
  - `accounts/api_client.py`
  - `static/`
  - `tests/test_web_smoke.py`
  - `docs/specs/architecture/admin-ops.md`
  - `docs/specs/contracts/market-lifecycle.md`
  - `docs/specs/state/`
- Bloqueios: probabilidades reais continuam dependentes de FEAT-PRED-001
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: evoluir cálculo real de probabilidade e stake em FEAT-PRED-001
- Reversão lógica: voltar o Admin Ops para options fixas antigas e remover o filtro por status da query administrativa

## WFLOW-20260518-012

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`, `admin-ops`
- Objetivo: corrigir UX e validação do editor administrativo de mercado
- Etapa atual: concluído
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `admin_ops/`
  - `static/`
  - `templates/`
  - `config/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: histórico superado; daemon operacional implementado em `WFLOW-20260520-001`
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: histórico superado; evoluir supervisor/deploy do daemon se necessário
- Reversão lógica: manter campos no banco e ocultar controles avançados no editor se necessário

## WFLOW-20260518-013

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`, `admin-ops`
- Objetivo: melhorar objetividade do formulário administrativo, feedback de sucesso e regra de fechamento manual
- Etapa atual: concluído
- Artefatos afetados:
  - `backend_api/`
  - `admin_ops/`
  - `accounts/api_client.py`
  - `static/`
  - `templates/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: histórico superado; daemon operacional implementado em `WFLOW-20260520-001`
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: histórico superado; evoluir supervisor/deploy do daemon se necessário
- Reversão lógica: ocultar botão de fechamento manual e desabilitar endpoint `/admin/markets/{slug}/lock` se necessário

## WFLOW-20260518-014

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `admin-ops`
- Objetivo: redesenhar Admin Ops de taxonomia e substituir exclusão física por bloqueio lógico de categorias/subcategorias
- Etapa atual: concluído
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `admin_ops/`
  - `accounts/api_client.py`
  - `static/`
  - `templates/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: evoluir ordenação, tradução e políticas de publicação da taxonomia quando houver i18n operacional
- Reversão lógica: manter campos de bloqueio e ocultar ações de bloqueio/desbloqueio no Admin Ops se a operação precisar ser suspensa

## WFLOW-20260518-015

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `admin-ops`
- Objetivo: vincular seleção de categoria/subcategoria do mercado à taxonomia persistida e refinar dark mode do editor
- Etapa atual: concluído
- Artefatos afetados:
  - `admin_ops/`
  - `static/`
  - `templates/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: evoluir busca/combobox de taxonomia se o volume de categorias crescer
- Reversão lógica: voltar campos de categoria/subcategoria para texto livre apenas no Django, mantendo validação FastAPI de bloqueio

## WFLOW-20260518-016

- Tipo: `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-PRED-001`
- Objetivo: implementar primeira fatia real de previsão e stake com uma previsão por usuário/mercado
- Etapa atual: concluído; `.venv/bin/python manage.py test` executado com sucesso em 2026-05-18
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `accounts/api_client.py`
  - `config/urls.py`
  - `static/js/gotrendlabs.js`
  - `tests/test_web_smoke.py`
  - `docs/specs/state/`
- Bloqueios: resolução, payout real, reputação avançada, comunicações e refund/cancelamento ficam fora desta entrega
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: implementar FEAT-RES-001 usando `gotrendlabs_predictions`, `prediction_stake_lock` e snapshots de entrada como base
- Reversão lógica: desativar rota de confirmação no Django e endpoint FastAPI, preservando `gotrendlabs_predictions` e ledger para auditoria/migração

## WFLOW-20260518-017

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-PRED-001`, `FEAT-MARKET-001`, `FEAT-MARKET-002`
- Objetivo: alinhar gráficos de consenso, UX de previsão bloqueada/visitante e fallback local em Postgres
- Etapa atual: concluído; `.venv/bin/python manage.py test` executado com sucesso em 2026-05-18
- Artefatos afetados:
  - `backend_api/`
  - `core/`
  - `markets/`
  - `templates/components/market_card.html`
  - `static/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: histórico materializado de snapshots, realtime/websocket e analytics avançado ficam fora desta entrega
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: criar tabela de snapshots se o volume de previsões tornar caro recalcular séries a partir de `gotrendlabs_predictions`
- Reversão lógica: ocultar sparklines nos templates preservando snapshots atuais de opção e registros de previsão

## WFLOW-20260518-018

- Tipo: `bugfix`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`, `FEAT-PRED-001`
- Objetivo: corrigir edição administrativa de mercado quando opções já possuem previsões vinculadas
- Etapa atual: concluído; `.venv/bin/python manage.py test` executado com sucesso em 2026-05-18
- Artefatos afetados:
  - `backend_api/`
  - `accounts/api_client.py`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: criar operação explícita de desativação/arquivamento de opção quando a UX administrativa exigir retirar opções já usadas
- Reversão lógica: bloquear edição de opções em mercados com previsões, preservando edição dos demais campos

## WFLOW-20260518-019

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-PRED-001`, `FEAT-MARKET-001`, `FEAT-MARKET-002`
- Objetivo: usar probabilidade decimal exata como fonte de verdade e truncar apenas a apresentação inteira
- Etapa atual: concluído; colunas inteiras redundantes removidas; `.venv/bin/python manage.py test` executado com sucesso em 2026-05-18
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `core/`
  - `admin_ops/`
  - `templates/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: histórico materializado de snapshots segue fora desta entrega
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: criar tabela de snapshots caso a evolução visual precise consultar histórico já materializado
- Reversão lógica: continuar serializando `probability_exact`, mas voltar templates a usar os inteiros se houver problema visual temporário

## WFLOW-20260518-020

- Tipo: `bugfix`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `admin-ops`
- Objetivo: recuperar tela administrativa de mercados após remoção de colunas inteiras e documentar fallback operacional
- Etapa atual: concluído; `.venv/bin/python manage.py test` executado com sucesso em 2026-05-18
- Artefatos afetados:
  - `admin_ops/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: observar logs da FastAPI depois de futuras migrations destrutivas e considerar healthcheck/versionamento de schema
- Reversão lógica: remover fallback local do browse administrativo se a operação passar a exigir falha explícita quando a API estiver fora

## WFLOW-20260518-021

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `admin-ops`
- Objetivo: simplificar ações da listagem administrativa removendo CTA público da tabela
- Etapa atual: concluído; teste de renderização do Admin Ops atualizado em 2026-05-18
- Artefatos afetados:
  - `admin_ops/templates/admin_ops/markets.html`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: se operadores precisarem abrir público diretamente da lista, reavaliar como ação contextual por status
- Reversão lógica: reintroduzir CTA público na tabela sem alterar contratos de domínio

## WFLOW-20260518-022

- Tipo: `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-COMMENT-001`
- Objetivo: implementar comentários reais em mercados com reações e moderação básica auditável
- Etapa atual: concluído; `.venv/bin/python manage.py test` executado com sucesso em 2026-05-18
- Artefatos afetados:
  - `docs/specs/features/comments.md`
  - `markets/`
  - `backend_api/`
  - `accounts/api_client.py`
  - `admin_ops/`
  - `tests/test_web_smoke.py`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: evoluir denúncias por usuários, paginação, edição/exclusão pelo autor ou respostas/thread quando forem priorizados
- Reversão lógica: ocultar formulários e ações de comentário mantendo tabelas históricas preservadas para auditoria/migração

## WFLOW-20260518-023

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`
- Objetivo: registrar filtros rápidos funcionais, curtidas nos cards e regra de destaque/fallback do feed
- Etapa atual: concluído; specs e estado documental atualizados em 2026-05-18
- Artefatos afetados:
  - `docs/specs/features/market-feed.md`
  - `docs/specs/architecture/frontend-web.md`
  - `docs/specs/spec_prediction_social_market_pt.md`
  - `docs/specs/state/`
  - `README.md`
- Bloqueios: nenhum
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: se favoritos por usuário forem priorizados, criar nova feature/contrato em vez de reaproveitar `is_featured`
- Reversão lógica: manter `GET /markets` estável e remover apenas ordenações client-side/chips visuais se houver regressão de UX

## WFLOW-20260519-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`, `FEAT-SUGGEST-001`
- Objetivo: adicionar reCAPTCHA v2 checkbox ao cadastro e aos envios guest de sugestão/feedback
- Etapa atual: concluído; testes automatizados executados em 2026-05-19
- Artefatos afetados:
  - `backend_api/`
  - `accounts/`
  - `core/`
  - `templates/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-19
- Atualizado em: 2026-05-19
- Encerrado em: 2026-05-19
- Retomada: configurar `RECAPTCHA_SITE_KEY` e `RECAPTCHA_SECRET_KEY` por ambiente e ativar `RECAPTCHA_ENABLED=1`
- Reversão lógica: desativar `RECAPTCHA_ENABLED` sem remover contratos ou campos opcionais

## WFLOW-20260519-002

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-REP-001`
- Objetivo: implementar badges administráveis com catálogo público e concessão automática por regras controladas
- Etapa atual: concluído; `python manage.py test` executado com sucesso em 2026-05-19
- Artefatos afetados:
  - `docs/specs/features/reputation-and-ranking.md`
  - `docs/specs/contracts/reputation-ranking.md`
  - `docs/specs/architecture/`
  - `accounts/`
  - `backend_api/`
  - `admin_ops/`
  - `core/`
  - `profiles/`
  - `tests/test_web_smoke.py`
- Bloqueios: nenhum
- Iniciado em: 2026-05-19
- Atualizado em: 2026-05-19
- Encerrado em: 2026-05-19
- Retomada: evoluir raridade, temporadas, compartilhamento completo de badge ou reprocessamento administrativo em lote quando priorizado
- Reversão lógica: ocultar rotas/telas de badges administráveis e manter tabelas novas preservadas para migração futura

## WFLOW-20260519-003

- Tipo: `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`
- Objetivo: implementar métricas operacionais de visualizações e compartilhamentos por mercado
- Etapa atual: concluído; `.venv/bin/python manage.py test` e testes focados do Admin Ops executados com sucesso em 2026-05-19
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `core/`
  - `accounts/api_client.py`
  - `admin_ops/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-19
- Atualizado em: 2026-05-19
- Encerrado em: 2026-05-19
- Retomada: evoluir para deduplicação ou analytics por origem quando priorizado
- Reversão lógica: remover exibição/admin e descontinuar incrementos mantendo colunas zeráveis para migração futura

## WFLOW-20260519-004

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`, `FEAT-WALLET-001`
- Objetivo: implementar gestão administrativa de usuários cadastrados no Admin Ops
- Etapa atual: concluído; suíte `.venv/bin/python manage.py test` executada com sucesso em 2026-05-19 após refinamentos de layout/menu, badges adquiridas e ajuste manual sem direção pré-selecionada
- Artefatos afetados:
  - `backend_api/`
  - `accounts/api_client.py`
  - `admin_ops/`
  - `config/urls.py`
  - `templates/admin_base.html`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-19
- Atualizado em: 2026-05-19
- Encerrado em: 2026-05-19
- Retomada: evoluir gestão de operadores, mascaramento seletivo de dados sensíveis ou ajuste de reputação apenas com nova decisão técnica
- Reversão lógica: ocultar rotas/telas de usuários no Admin Ops e manter eventos/ledger preservados para auditoria

## WFLOW-20260520-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-OPSLOG-001`
- Objetivo: implementar logs técnicos persistidos para troubleshooting em Django, FastAPI, logging Python e Admin Ops
- Etapa atual: concluído; `.venv/bin/python manage.py test`, checks de migration e testes focados de Admin Ops/logs executados com sucesso em 2026-05-20
- Artefatos afetados:
  - `system_logs/`
  - `backend_api/`
  - `admin_ops/`
  - `accounts/api_client.py`
  - `config/`
  - `templates/admin_base.html`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: evoluir alertas, paginação avançada e integração externa de observabilidade quando priorizado
- Reversão lógica: ocultar telas/rotas de logs no Admin Ops e manter tabela para auditoria técnica temporária até expiração

## WFLOW-20260520-002

- Tipo: `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-NOTIFY-001`, `FEAT-OPSLOG-001`
- Objetivo: implementar Config operacional, modo manutenção, separação de credenciais PostgreSQL por serviço, SMTP não sensível persistido e Dashboard Admin Ops ampliado com saúde operacional
- Etapa atual: concluído; `.venv/bin/python manage.py check`, `.venv/bin/python manage.py makemigrations --check --dry-run`, `.venv/bin/python manage.py test` e `git diff --check` executados com sucesso em 2026-05-20
- Artefatos afetados:
  - `backend_api/`
  - `accounts/api_client.py`
  - `admin_ops/`
  - `core/`
  - `config/`
  - `templates/`
  - `static/css/gotrendlabs.css`
  - `.env.example`
  - `README.md`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: evoluir envio real em `communications`, criação operacional de roles PostgreSQL de menor privilégio e gráficos/históricos do dashboard quando priorizado
- Reversão lógica: ocultar Config/Dashboard ampliado no Admin Ops, manter `gotrendlabs_site_config` preservada e desativar middleware de manutenção se necessário

## WFLOW-20260520-003

- Tipo: `refactor-feature`
- Status: `concluido`
- Feature alvo: `FEAT-RES-001`
- Objetivo: centralizar ciclo de vida de mercado em engine backend, adicionar auditoria read-only de resolução no Admin Ops e validar fluxo hard com 100 usuários simulados
- Etapa atual: concluído; `.venv/bin/python manage.py test tests`, testes focados de Admin Ops/resolução e `git diff --check` executados com sucesso em 2026-05-20
- Artefatos afetados:
  - `backend_api/market_lifecycle_engine.py`
  - `backend_api/main.py`
  - `backend_api/schemas.py`
  - `accounts/api_client.py`
  - `admin_ops/`
  - `markets/management/commands/reconcile_canceled_market_refunds.py`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/research/qa-simulacao-hard-100-usuarios-20260520.md`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: evoluir auditorias públicas/usuário final, snapshots históricos materializados e exportação operacional quando priorizado
- Reversão lógica: remover ação/tela/contrato de auditoria, manter `MarketLifecycleEngine` se o refactor permanecer desejável; se necessário, mover chamadas de lifecycle de volta para handlers preservando testes de ledger/reputação

## WFLOW-20260520-004

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-WALLET-001`, `FEAT-REP-001`
- Objetivo: implementar recarga educativa por fila Admin Ops com piso configurável, histórico/extrato paginados e ranking web paginado
- Etapa atual: concluído; `.venv/bin/python manage.py check`, `.venv/bin/python manage.py makemigrations --check --dry-run`, `.venv/bin/python manage.py test tests.test_web_smoke`, `git diff --check` e migração local executados com sucesso em 2026-05-20
- Artefatos afetados:
  - `accounts/`
  - `backend_api/`
  - `admin_ops/`
  - `wallet/`
  - `profiles/`
  - `config/urls.py`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: evoluir cadência/janela automática de recargas, materialização futura do ranking ou controles operacionais mais granulares quando priorizado
- Reversão lógica: ocultar botões/rotas de recarga e filtro `wallet_recharge`, manter ledger/solicitações preservados para auditoria; remover paginação web apenas na camada Django se houver regressão de UX

## WFLOW-20260520-005

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`
- Objetivo: restaurar rodapé público nas telas standalone de autenticação e alinhar a regra documental de apresentação pública
- Etapa atual: concluído; testes focados de auth web, verificação HTTP local de `/login/` e `git diff --check` executados com sucesso em 2026-05-20
- Artefatos afetados:
  - `accounts/templates/accounts/`
  - `templates/base.html`
  - `templates/components/footer.html`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/auth-and-session.md`
  - `docs/specs/architecture/frontend-web.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: manter novos layouts públicos usando o partial de rodapé compartilhado para evitar divergência visual
- Reversão lógica: remover o include do rodapé nas telas standalone de auth e ajustar a spec para voltar a exigir apenas navegação pública

## WFLOW-20260520-006

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`
- Objetivo: padronizar botões sociais iconizados em login/cadastro, incluir X no placeholder social e corrigir espaçamento vertical das telas de auth
- Etapa atual: concluído; `.venv/bin/python manage.py test tests.test_web_smoke.BackendAuthAPITests.test_social_auth_placeholder_supports_initial_providers`, `.venv/bin/python manage.py test tests.test_web_smoke.WebSmokeTests.test_login_page_has_focused_auth_layout`, `.venv/bin/python manage.py test tests.test_web_smoke`, `git diff --check` e screenshots locais via Chrome/Playwright executados com sucesso em 2026-05-20
- Artefatos afetados:
  - `accounts/templates/accounts/login.html`
  - `accounts/templates/accounts/register.html`
  - `backend_api/main.py`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/auth-and-session.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: implementar OAuth real para `google`, `facebook` e `x` quando credenciais/callbacks forem priorizados
- Reversão lógica: restaurar botões textuais antigos e remover `x` do placeholder FastAPI, mantendo o ajuste de altura natural de auth se a correção visual permanecer desejável

## WFLOW-20260520-007

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`
- Objetivo: reduzir atrito de navegação tornando o título do card de mercado clicável para o detalhe
- Etapa atual: concluído; `.venv/bin/python manage.py test tests.test_web_smoke.WebSmokeTests.test_market_card_title_links_to_market_detail`, suíte `.venv/bin/python manage.py test tests.test_web_smoke` e `git diff --check` executados com sucesso em 2026-05-20
- Artefatos afetados:
  - `templates/components/market_card.html`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/market-feed.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: avaliar métricas de CTR do título versus CTA quando a instrumentação de eventos do feed for priorizada
- Reversão lógica: remover o link do título e manter apenas os CTAs explícitos `Prever`/`Ver resolução`

## WFLOW-20260520-008

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-REP-001`, `FEAT-WALLET-001`, `FEAT-OPSLOG-001`, `admin-ops`
- Objetivo: padronizar listas web e browses principais do Admin Ops com `Carregar mais` em blocos cumulativos de 10 itens
- Etapa atual: concluído; `.venv/bin/python -m py_compile admin_ops/views.py profiles/views.py wallet/views.py`, testes focados de Admin Ops e `.venv/bin/python manage.py test tests.test_web_smoke` executados com sucesso em 2026-05-20
- Artefatos afetados:
  - `profiles/`
  - `wallet/`
  - `admin_ops/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: aplicar o mesmo padrão a novos browses web simples, mantendo paginação por offset apenas em auditorias ou telas que precisem de posição explícita
- Reversão lógica: restaurar os controles de página/offset nas views/templates afetados, preservando contratos backend e documentação histórica

## WFLOW-20260520-009

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-I18N-001`, `sistema-documental`
- Objetivo: renomear a marca pública da plataforma para `GoTrendLabs` preservando identificadores técnicos e `GTL Credits`
- Etapa atual: concluído; testes e busca final registrados na implementação desta branch
- Artefatos afetados:
  - `templates/`
  - `accounts/templates/accounts/`
  - `core/`
  - `backend_api/main.py`
  - `static/js/gotrendlabs.js`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: extrair strings de marca para catálogos quando `FEAT-I18N-001` avançar
- Reversão lógica: restaurar textos públicos para `GoTrendLabs`, mantendo `GTL Credits` e identificadores técnicos inalterados

## WFLOW-20260520-010

- Tipo: `docs-tooling`
- Status: `concluido`
- Feature alvo: `sistema-documental`, `curadoria-de-mercados`
- Objetivo: criar skill local para sugerir mercados de previsão com dados internos da GoTrendLabs, trends sociais, links exatos de verificação, diversidade editorial e anti-repetição
- Etapa atual: concluído; `python3 /Users/williamsca/.codex/skills/.system/skill-creator/scripts/quick_validate.py tools/skills/gotrendlabs/gotrendlabs-prediction-markets` executado com sucesso em 2026-05-20
- Artefatos afetados:
  - `tools/skills/gotrendlabs/gotrendlabs-prediction-markets/`
  - `tools/skills/gotrendlabs/README.md`
  - `docs/guides/gotrendlabs-prediction-markets-skill.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: configurar tokens opcionais de redes sociais quando a operação quiser consultar APIs externas diretamente
- Reversão lógica: remover a skill e o guia, mantendo apenas o histórico documental desta decisão

## WFLOW-20260521-001

- Tipo: `docs-tooling`
- Status: `concluido`
- Feature alvo: `sistema-documental`, `curadoria-de-mercados`
- Objetivo: reforçar a skill `gotrendlabs-prediction-markets` para validar que a fonte de resolução consegue fundamentar e certificar o resultado antes de sugerir mercados
- Etapa atual: concluído; `python3 /Users/williamsca/.codex/skills/.system/skill-creator/scripts/quick_validate.py tools/skills/gotrendlabs/gotrendlabs-prediction-markets` e `git diff --check` executados com sucesso em 2026-05-21
- Artefatos afetados:
  - `tools/skills/gotrendlabs/gotrendlabs-prediction-markets/SKILL.md`
  - `tools/skills/gotrendlabs/gotrendlabs-prediction-markets/references/fontes-sociais-e-verificacao.md`
  - `tools/skills/gotrendlabs/gotrendlabs-prediction-markets/references/framework-de-mercados.md`
  - `docs/guides/gotrendlabs-prediction-markets-skill.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-21
- Atualizado em: 2026-05-21
- Encerrado em: 2026-05-21
- Retomada: integrar checagens automatizadas por API/navegador quando credenciais sociais oficiais estiverem configuradas
- Reversão lógica: remover a etapa obrigatória de validação da fonte e voltar ao requisito anterior de link exato com fallback

## WFLOW-20260521-002

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`, `FEAT-MARKET-001`, `FEAT-MARKET-002`, `FEAT-PRED-001`, `FEAT-WALLET-001`
- Objetivo: corrigir perfil autenticado com dados reais do banco, adicionar marcação administrativa de bots, remover indução de escolha no ticket, ajustar métricas públicas de wallet, melhorar share de mercado e estados de saldo
- Etapa atual: concluído; `.venv/bin/python manage.py check`, testes focados de perfil/ticket/share/admin e `.venv/bin/python manage.py test` executados com sucesso durante a implementação em 2026-05-21
- Artefatos afetados:
  - `accounts/`
  - `admin_ops/`
  - `backend_api/`
  - `core/`
  - `markets/templates/markets/detail.html`
  - `profiles/views.py`
  - `static/css/gotrendlabs.css`
  - `static/js/gotrendlabs.js`
  - `templates/`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/`
  - `docs/specs/contracts/`
  - `docs/specs/architecture/`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-21
- Atualizado em: 2026-05-21
- Encerrado em: 2026-05-21
- Retomada: avaliar cache-busting centralizado para assets estáticos e teste visual automatizado quando o navegador MCP estiver disponível
- Reversão lógica: remover `is_bot`, restaurar ticket com botão desabilitado até escolha, voltar métrica `distributed_gtl` para todos os créditos e retirar opções/CTA do share de mercado

## WFLOW-20260521-003

- Tipo: `infra-data`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`
- Objetivo: impedir que mercados fixture sejam semeados em produção e limpar os fixtures criados no primeiro deploy
- Etapa atual: concluído; migration inicial de mercados sem `RunPython` de seed, seed explícito restrito ao harness de testes e RDS de produção validado com `gotrendlabs_markets = 0`
- Artefatos afetados:
  - `markets/migrations/0001_initial.py`
  - `tests/test_web_smoke.py`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-21
- Atualizado em: 2026-05-21
- Encerrado em: 2026-05-21
- Retomada: criar mercados reais via Admin Ops/curadoria antes de liberar tráfego editorial de produção
- Reversão lógica: reintroduzir seed apenas em ambiente não-produtivo, nunca via migration aplicada em PRD

## WFLOW-20260521-004

- Tipo: `infra-data`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-AUTH-001`, `FEAT-WALLET-001`
- Objetivo: criar fluxo one-off idempotente para popular PRD com dados editoriais bons de DEV, admin inicial, wallet conciliada, badges com mídia e site config
- Etapa atual: concluído; PRD populado com `@admin`, wallet conciliada, 10 badges com mídia, site config, 27 mercados editoriais, 65 opções e 47 arquivos de mídia; snapshot RDS pré-import `gotrendlabs-prod-before-bootstrap-20260521215807`; senha de `admin@gotrendlabs.com.br` resetada e validada, parâmetros temporários de senha removidos do SSM
- Artefatos afetados:
  - `ops/scripts/export_dev_bootstrap.py`
  - `ops/scripts/import_prod_bootstrap.py`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-21
- Atualizado em: 2026-05-21
- Encerrado em: 2026-05-21
- Retomada: seguir criando novos conteúdos diretamente em PRD; se novo reset administrativo for necessário, usar `SecureString` temporário e removê-lo após validação
- Reversão lógica: restaurar snapshot RDS pré-import e remover mídia copiada do volume `mediafiles`

## WFLOW-20260522-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`
- Objetivo: tornar a ação de favorito visível para visitantes na home e no detalhe, em estado readonly com aviso de login, mantendo mutação e recorte `Favoritos` autenticados
- Etapa atual: concluído; `.venv/bin/python manage.py test tests.test_web_smoke`, `.venv/bin/python manage.py check`, `git diff --check` e validação local da home/detalhe no `runserver` executados com sucesso em 2026-05-22
- Artefatos afetados:
  - `templates/components/market_card.html`
  - `markets/templates/markets/detail.html`
  - `static/js/gotrendlabs.js`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/`
  - `docs/specs/architecture/frontend-web.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: avaliar CTA direto para login caso métricas mostrem muitos cliques de visitante sem conversão
- Reversão lógica: ocultar novamente affordance de favorito para visitantes e remover handler `data-guest-favorite-button`

## WFLOW-20260522-002

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-SUGGEST-001`, `FEAT-OPSLOG-001`
- Objetivo: expor `Sugerir mercado` no topo público e incluir indicador `Backend API` no Dashboard Admin Ops consultando `GET /health`
- Etapa atual: concluído; testes de navegação pública, health online/offline do dashboard, `manage.py check` e `git diff --check` executados em 2026-05-22
- Artefatos afetados:
  - `templates/base.html`
  - `admin_ops/`
  - `accounts/api_client.py`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/`
  - `docs/specs/architecture/`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: avaliar se o healthcheck deve expor versão/build quando houver necessidade operacional
- Reversão lógica: remover o link público de sugestão no topo e ocultar o card `Backend API`, mantendo `/health` disponível para infraestrutura

## WFLOW-20260522-003

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`
- Objetivo: ampliar a curadoria assistida para mercados cripto com fontes objetivas, aviso de risco e seed DEV inicial com thumbnails autorais
- Etapa atual: concluído; skill `gotrendlabs-prediction-markets` atualizada para cripto, 3 mercados DEV criados como `draft`, thumbs 512x512 geradas em `media/market_thumbnails/`, `quick_validate.py` e `git diff --check` executados com sucesso em 2026-05-22
- Artefatos afetados:
  - `tools/skills/gotrendlabs/gotrendlabs-prediction-markets/`
  - `tools/skills/gotrendlabs/README.md`
  - `docs/guides/gotrendlabs-prediction-markets-skill.md`
  - `docs/specs/state/`
  - `media/market_thumbnails/generated-bitcoin-acima-80000-30-junho-2026.png`
  - `media/market_thumbnails/generated-solana-acima-bsc-tvl-31-maio-2026.png`
  - `media/market_thumbnails/generated-pepe-acima-shiba-meme-coins-15-junho-2026.png`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: revisar odds/fontes no Admin Ops antes de publicar os mercados cripto; em PRD, aplicar via fluxo operacional controlado, não por migration automática
- Reversão lógica: remover/arquivar os mercados cripto em DEV/PRD e retirar `cripto` da skill se a categoria for descontinuada

## WFLOW-20260522-004

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`, `FEAT-REP-001`
- Objetivo: implementar `evento` como terceira camada da taxonomia de mercado e aplicar o recorte em mercado público/Admin Ops/badges
- Etapa atual: concluído; migrations, contratos FastAPI, Admin Ops, renderização pública e testes focados de evento executados em 2026-05-22; suíte smoke completa fica registrada na validação da branch
- Artefatos afetados:
  - `markets/`
  - `accounts/`
  - `backend_api/`
  - `admin_ops/`
  - `templates/components/market_card.html`
  - `markets/templates/markets/detail.html`
  - `static/js/gotrendlabs.js`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: decidir se ranking público e sugestão de mercado também passam a capturar/filtrar evento em uma próxima fatia
- Reversão lógica: ocultar seleção/exibição de evento na UI e tratar regras de badge com `event` preenchido como inativas, preservando tabelas para nova migração corretiva

## WFLOW-20260522-005

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`
- Objetivo: redesenhar Admin Ops Taxonomia em master-detail e adicionar aviso opcional por evento para mercados sensíveis
- Etapa atual: concluído; migration `MarketEvent.notice`, contratos FastAPI/Django, UI pública de detalhe/ticket, Admin Ops master-detail, testes e specs atualizados em 2026-05-22
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `core/`
  - `admin_ops/`
  - `markets/templates/markets/detail.html`
  - `static/js/gotrendlabs.js`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: avaliar templates de aviso pré-cadastrados por categoria sensível se operadores repetirem o mesmo texto
- Reversão lógica: manter `notice` vazio e ocultar o alerta público, preservando o layout master-detail e a coluna para compatibilidade

## WFLOW-20260522-006

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`
- Objetivo: adicionar avisos opcionais em categoria/subcategoria e corrigir a operação visual da tela Admin Ops Taxonomia
- Etapa atual: concluído; migration para `MarketCategory.notice` e `MarketSubcategory.notice`, contratos FastAPI/Django, Admin Ops, detalhe/ticket público, testes e specs atualizados em 2026-05-22
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `core/`
  - `admin_ops/`
  - `markets/templates/markets/detail.html`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: avaliar previews consolidados de avisos quando categoria/subcategoria/evento possuírem textos longos simultaneamente
- Reversão lógica: manter avisos de categoria/subcategoria vazios e ocultar seus campos na UI, preservando colunas para compatibilidade

## WFLOW-20260522-007

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`, `FEAT-REP-001`
- Objetivo: reposicionar avisos no detalhe de mercado, permitir exclusão segura de eventos sem mercado e exibir miniatura no browse Admin Ops de badges
- Etapa atual: concluído; template público, API FastAPI, proxy Django, Admin Ops, testes e specs atualizados em 2026-05-22
- Artefatos afetados:
  - `backend_api/`
  - `accounts/`
  - `admin_ops/`
  - `markets/templates/markets/detail.html`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: avaliar se categorias/subcategorias sem mercados também devem ter limpeza controlada ou seguir somente bloqueio lógico
- Reversão lógica: ocultar ação `delete_event`, manter validação 422 para eventos vinculados e voltar avisos para posição anterior se a UI de negociação pedir destaque maior

## WFLOW-20260522-008

- Tipo: `change-ui`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`
- Objetivo: substituir o indicador circular dos cards por indicador horizontal de prazo tecnicamente baseado em tempo restante e exibir thumbnail no detalhe de negociação
- Etapa atual: concluído; card, detalhe de mercado, CSS, JS de hidratação, testes e specs atualizados em 2026-05-22
- Artefatos afetados:
  - `templates/components/market_card.html`
  - `markets/templates/markets/detail.html`
  - `static/css/gotrendlabs.css`
  - `static/js/gotrendlabs.js`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: validar visualmente em browser se a rail horizontal economiza espaço nos cards de 3 colunas sem perder legibilidade
- Reversão lógica: restaurar o indicador circular textual mantendo a regra de não usar probabilidade como progresso de tempo

## WFLOW-20260522-009

- Tipo: `change-content`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`
- Objetivo: aplicar lote cripto mainstream com taxonomia `Mercado > Cripto > moeda`, aviso de subcategoria e thumbnails autorais
- Etapa atual: concluído; comando idempotente `seed_crypto_markets_20260522`, memória editorial, changelogs e 3 thumbs 512x512 adicionados; lote aplicado em PRD via SSM/container Django em 2026-05-22, com 3 mercados `open`, aviso de subcategoria e imagens no volume `production_mediafiles`
- Artefatos afetados:
  - `markets/management/commands/seed_crypto_markets_20260522.py`
  - `media/market_thumbnails/generated-ethereum-acima-3000-30-junho-2026.png`
  - `media/market_thumbnails/generated-dogecoin-top10-30-junho-2026.png`
  - `media/market_thumbnails/generated-solana-acima-xrp-ranking-30-junho-2026.png`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: revisar odds/fechamento no Admin Ops e publicar ajustes editoriais caso a curadoria queira destacar algum card no feed
- Reversão lógica: cancelar/arquivar os três mercados e limpar ou alterar o aviso da subcategoria `Cripto` se a taxonomia for revista

## WFLOW-20260524-002

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-REP-001`
- Objetivo: exibir badges conquistadas no ranking e ampliar filtros públicos para evento
- Etapa atual: concluído; FastAPI, Django, CSS/JS, testes e specs atualizados em 2026-05-24
- Artefatos afetados:
  - `backend_api/`
  - `profiles/`
  - `static/css/gotrendlabs.css`
  - `static/js/gotrendlabs.js`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-24
- Atualizado em: 2026-05-24
- Encerrado em: 2026-05-24
- Retomada: avaliar visualmente em produção se o limite `3 +N` preserva legibilidade em usuários com muitos reconhecimentos
- Reversão lógica: ocultar badges no template do ranking e ignorar `event` no filtro web, mantendo campos adicionais do contrato como compatibilidade não disruptiva

## WFLOW-20260524-003

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`
- Objetivo: exibir progressão neutra para operadores autenticados e permitir geração administrativa auditada de link de reset de senha
- Etapa atual: concluído; FastAPI, Django Admin Ops, home autenticada, testes e specs atualizados em 2026-05-24
- Artefatos afetados:
  - `backend_api/`
  - `accounts/`
  - `admin_ops/`
  - `core/templates/core/home.html`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-24
- Atualizado em: 2026-05-24
- Encerrado em: 2026-05-24
- Retomada: se reset por email real for priorizado, integrar communications/SMTP em vez de expor apenas link operacional
- Reversão lógica: ocultar a ação `password_reset` no detalhe de usuário e voltar o filtro da home para não carregar `user_summary` de operadores

## WFLOW-20260607-DJANGO-APPS-LAYOUT-001

- Tipo: `architecture-change`
- Status: `concluido`
- Feature alvo: reorganizacao do monorepo GoTrendLabs
- Objetivo: mover apps Django para `apps/web/django/`, preservando `AppConfig.label`, migrations e comandos locais
- Etapa atual: concluido; codigo, docs, skills, checks, collectstatic e suite Django validados em 2026-06-07
- Artefatos afetados:
  - `apps/web/django/`
  - `config/`
  - `apps/api/backend_api/`
  - `ops/scripts/`
  - `tests/test_web_smoke.py`
  - `README.md`
  - `docs/specs/architecture/`
  - `tools/skills/gotrendlabs/`
- Bloqueios: nenhum
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Retomada: abrir PR, acompanhar CI/deploy e fazer smoke pos-merge
- Reversão lógica: restaurar apps Django para a raiz mantendo os imports novos fora do merge, se alguma incompatibilidade de import path for encontrada

## WFLOW-20260607-OPENAPI-CONTRACTS-001

- Tipo: `architecture-change`
- Status: `concluido`
- Feature alvo: contratos OpenAPI versionados para web/mobile futuro
- Objetivo: versionar o snapshot OpenAPI da FastAPI e validar sincronismo em CI antes de novos clientes
- Etapa atual: concluido; snapshot, exportador, docs, skills, CI, checks e suite Django validados em 2026-06-07
- Artefatos afetados:
  - `packages/contracts/`
  - `apps/api/backend_api/main.py`
  - `.github/workflows/deploy.yml`
  - `README.md`
  - `docs/specs/architecture/`
  - `tools/skills/gotrendlabs/`
- Bloqueios: nenhum
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Retomada: abrir PR, acompanhar CI/deploy e fazer smoke pos-merge
- Reversão lógica: remover snapshot/versionador e voltar `packages/contracts/` para estado reservado, mantendo a documentação viva da FastAPI em `/docs`

## WFLOW-20260607-MOBILE-ANDROID-MVP-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`
- Objetivo: implementar o MVP Android Flutter consumindo a FastAPI como fonte da verdade
- Etapa atual: concluido; app Flutter, ajustes de contrato, docs, testes, build Android debug e smoke em emulador validados em 2026-06-07
- Artefatos afetados:
  - `apps/mobile/`
  - `apps/api/backend_api/`
  - `packages/contracts/openapi/gotrendlabs-api.json`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/`
  - `tests/test_web_smoke.py`
- Bloqueios: nenhum para o MVP Android local
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Encerrado em: 2026-06-07
- Retomada: ampliar QA autenticado real em emulador, avaliar refresh token/offline/push/iOS e consolidar cliente gerado quando contratos estabilizarem
- Reversão lógica: ocultar entrada mobile/reverter `apps/mobile`, manter contratos backend compatíveis de recarga como extensao segura, e preservar docs para retomada futura
