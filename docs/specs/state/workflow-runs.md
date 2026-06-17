# Workflow Runs

Use este arquivo como memória operacional de processos em andamento, concluídos, bloqueados, cancelados ou substituídos.

## WFLOW-20260617-AI-COMMENT-MARKET-LIMIT-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AIAGENT-001`
- Objetivo: tornar administrável o limite total de comentários IA oficiais visíveis por mercado, adicionar override opcional por agente `analyst`, manter `ai_commenting_enabled` como kill switch e preservar cooldown/limites por dia/ciclo como proteções adicionais.
- Etapa atual: concluído; PR #93 mergeada em `main`, hotfix OpenAPI #94 mergeado, deploy de produção concluído pelo workflow `GoTrendLabs CI and Deploy` run `27690438066`, e duplicados históricos de comentários IA visíveis ocultados operacionalmente em produção.
- Artefatos afetados:
  - `apps/api/backend_api/agent_services.py`
  - `apps/api/backend_api/main.py`
  - `apps/api/backend_api/schemas.py`
  - `apps/web/django/agents/`
  - `apps/web/django/admin_ops/`
  - `docs/specs/features/official-ai-agents.md`
  - `docs/specs/state/`
  - `tests/test_web_smoke.py`
- Bloqueios: nenhum conhecido.
- Iniciado em: 2026-06-17
- Atualizado em: 2026-06-17
- Encerrado em: 2026-06-17
- Evidências de validação local: `.venv/bin/python manage.py check` sem issues; `.venv/bin/python manage.py makemigrations --check --dry-run` sem mudanças pendentes; recorte focado de 8 testes IA/Admin Ops OK; `.venv/bin/python manage.py test tests.test_web_smoke --keepdb` com 198 testes OK; `git diff --check` limpo; migration `agents.0005_aiagent_max_comments_per_market_override` aplicada no banco local.
- Evidências de publicação: PR #93 (`Controla comentários IA por mercado no Admin Ops`) mergeada com squash `e309c6b`; PR #94 (`Atualiza snapshot OpenAPI dos agentes IA`) mergeada com squash `41e7925`; workflow `GoTrendLabs CI and Deploy` run `27690438066` concluiu `test` em 4m14s e `deploy` em 49s, com deploy SSM `9e71e997-865c-4597-b927-6282466bc928`; produção respondeu `GET /api/health` com `status=ok`.
- Evidências de produção: consulta read-only SSM `e60dff52-0fa8-4711-9b4a-87460dead67f` encontrou 10 mercados com duplicados visíveis de IA e 22 comentários extras; limpeza SSM `8825bf8e-6a6a-4782-8fe8-986212cc4159` ocultou os 22 extras preservando o comentário IA visível mais antigo por mercado; verificação SSM `69d5f9b6-a430-4aca-afc9-eea633c7f3e8` confirmou `duplicate_markets=0`, `extra_visible_comments=0`, `ai_max_comments_per_market=1`, `ai_commenting_enabled=true` e `GoTrendLabs AI Analyst` sem override.
- Reversão lógica: remover os campos `ai_max_comments_per_market` e `max_comments_per_market_override` e suas migrations, retirar o bloqueio `market_ai_comment_limit` da seleção de candidatos do agente `analyst` e restaurar a documentação para limites baseados apenas em cooldown/dia/ciclo.

## WFLOW-20260616-MOBILE-RANKING-LIVE-REFRESH-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `FEAT-REP-001`
- Objetivo: incluir Ranking no contrato mobile de refresh em tempo de consulta, reconsultando `GET /rankings` ao abrir a tela ativa, voltar do background, tocar na aba, trocar filtros e usar pull-to-refresh, sem polling continuo, sem regra local de reputacao e sem consulta antecipada/duplicada quando a tela esta apenas montada fora da aba ativa.
- Etapa atual: concluido; PR #91 mergeada em `main`, deploy de producao concluido e APK Android beta `1.0.7 (8)` publicada no canal direto do site.
- Artefatos afetados:
  - `apps/mobile/lib/src/features/live_refresh.dart`
  - `apps/mobile/lib/src/features/ranking/`
  - `apps/mobile/lib/src/features/shell/`
  - `apps/mobile/test/`
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/`
- Bloqueios: nenhum conhecido.
- Iniciado em: 2026-06-16
- Atualizado em: 2026-06-16
- Retomada: acompanhar feedback de Ranking no Android beta `1.0.7 (8)`; se a proxima fatia mobile exigir nova publicacao, incrementar `version` em `apps/mobile/pubspec.yaml`, gerar APK release assinada com bases de producao e publicar pelo canal direto.
- Evidências de validação local: `cd apps/mobile && flutter test test/ranking_screen_test.dart test/shell_screen_test.dart` com 8 testes OK; `cd apps/mobile && flutter analyze` sem issues; `cd apps/mobile && flutter test` com 78 testes OK; `git diff --check` limpo.
- Evidências de publicação: PR #91 (`Atualiza Ranking mobile com dados quentes`) mergeada em `main` por squash commit `585733fa69bdccdd4b6d8a90280c9afbcc25e3b2`; GitHub Actions `GoTrendLabs CI and Deploy` run `27658699222` concluiu jobs `test` e `deploy` com sucesso; producao respondeu `https://gotrendlabs.com.br/api/health` com `status=ok`, `maintenance.web_enabled=false`, `maintenance.mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; homepage retornou `HTTP/2 200`; APK release `1.0.7 (8)` gerada com `GTL_API_BASE_URL=https://gotrendlabs.com.br/api` e `GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br`, SHA-256 `54822fc7aa84ebad2e923c0af75076ba43f7d73433c918f1a365bcd2d4ffe5ae` e tamanho `57636557` bytes; APK publicada em producao via SSM `1d347ac1-7a64-496f-b6d4-578926566bc3` com limpeza temporaria posterior via SSM `5c26639f-2a22-4352-a855-56ffd44135e8`; bucket S3 temporario de transporte foi removido; `https://gotrendlabs.com.br/app/android/latest.json` retornou `version_name=1.0.7`, `version_code=8`, `file_size=57636557` e o mesmo SHA-256; download publico da APK retornou `HTTP/2 200`, `content-type: application/vnd.android.package-archive`, `content-length=57636557` e hash recalculado identico.
- Reversao lógica: remover invalidacao/refresh de ranking do helper central, shell e `RankingScreen`, mantendo `GET /rankings` e filtros existentes inalterados.

## WFLOW-20260616-MOBILE-LIVE-REFRESH-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `FEAT-WALLET-001`, `FEAT-NOTIFY-001`
- Objetivo: corrigir refresh em tempo de consulta no app mobile para que mercados/status, detalhe, wallet, ledger, recargas e alertas sejam reconsultados ao abrir telas criticas, voltar do background, trocar para abas dependentes de mercado e usar pull-to-refresh, sem mudar contratos backend.
- Etapa atual: concluído; PR #89 mergeada em `main`, deploy de produção concluído e APK Android beta `1.0.6 (7)` publicado no canal direto do site.
- Artefatos afetados:
  - `apps/mobile/lib/src/features/live_refresh.dart`
  - `apps/mobile/lib/src/features/shell/`
  - `apps/mobile/lib/src/features/markets/`
  - `apps/mobile/lib/src/features/wallet/`
  - `apps/mobile/test/`
  - `apps/mobile/pubspec.yaml`
  - `apps/mobile/README.md`
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
- Bloqueios: nenhum conhecido.
- Iniciado em: 2026-06-16
- Atualizado em: 2026-06-16
- Encerrado em: 2026-06-16
- Retomada: acompanhar feedback físico do app Android publicado; se o usuário ainda perceber dados desatualizados, validar evento específico contra logs/API de produção antes de adicionar polling contínuo.
- Reversão lógica: remover invalidações/refetches centralizados do Flutter, voltar `RefreshIndicator` aos callbacks anteriores e manter a versão Android ativa anterior `1.0.5 (6)` no Admin Ops.
- Evidências de validação local: `cd apps/mobile && flutter test test/markets_screen_test.dart`; `cd apps/mobile && flutter pub get`; `cd apps/mobile && flutter analyze`; `cd apps/mobile && flutter test`; `git diff --check`; `cd apps/mobile && flutter build apk --release --dart-define=GTL_API_BASE_URL=https://gotrendlabs.com.br/api --dart-define=GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br` gerou APK assinado `1.0.6 (7)` com SHA-256 `ce4ea6e23305474b2ec1e5d73708b680ec12a9c4018bd845d77c076e369c2288` e tamanho `57636557` bytes; APK debug com API de produção instalado no Galaxy S20 `192.168.18.148:43831`, sem `adb reverse`, com `GTL_API_BASE_URL=https://gotrendlabs.com.br/api`, Activity `br.com.gotrendlabs.gotrendlabs_mobile/.MainActivity` focada e SHA-256 `48011f20ada65846c0f823d784d11449057ffe116bb61c6029ddcf51f520f756`.
- Evidências de publicação: PR #89 (`Corrige refresh vivo no mobile`) mergeada em `main` por squash commit `db0f9757fbc75df172563af0e03e7561cd1154a8`; GitHub Actions `GoTrendLabs CI and Deploy` run `27656995985` concluiu jobs `test` e `deploy` com sucesso; produção respondeu `https://gotrendlabs.com.br/api/health` com `status=ok`, `maintenance.web_enabled=false`, `maintenance.mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; homepage retornou `HTTP/2 200`; APK release `1.0.6 (7)` publicada em produção via SSM `096bb6c7-e31f-4101-81b0-30d01c370fc9`, com limpeza temporária posterior via SSM `b48ae9f8-9234-4f13-94c6-4ec996d19d96`; bucket S3 temporário de transporte foi removido; `https://gotrendlabs.com.br/app/android/latest.json` retornou `version_name=1.0.6`, `version_code=7`, `file_size=57636557` e SHA-256 `ce4ea6e23305474b2ec1e5d73708b680ec12a9c4018bd845d77c076e369c2288`; download público da APK retornou `HTTP/2 200`, `content-type: application/vnd.android.package-archive`, `content-length=57636557` e hash recalculado idêntico.

## WFLOW-20260616-MOBILE-MARKET-WALLET-UX-FIXES-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `FEAT-PRED-001`, `FEAT-WALLET-001`, `FEAT-NOTIFY-001`, `FastAPI public contract`, `frontend-web`
- Objetivo: corrigir UX mobile de mercado, comentários, alertas e wallet, remover `Insights` enquanto não houver contrato recorrente e alinhar mercados `open` com `auto_close_enabled=true` e `close_at` vencido como efetivamente `locked`.
- Etapa atual: publicado em `main` pela PR #87, deploy de produção concluído e smokes públicos confirmaram API/site saudáveis e Royal Ascot 2026 como `locked`/`Fechado` no contrato público.
- Artefatos afetados:
  - `apps/api/backend_api/main.py`
  - `apps/web/django/core/domain_client.py`
  - `apps/web/django/communications/push_services.py`
  - `apps/mobile/lib/src/`
  - `apps/mobile/test/`
  - `tests/test_web_smoke.py`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/features/mobile-mvp.md`
  - `docs/specs/features/mobile-ux.md`
  - `docs/specs/features/market-detail.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
- Bloqueios: nenhum conhecido; publicação de nova APK beta fica fora desta entrega.
- Iniciado em: 2026-06-16
- Atualizado em: 2026-06-16
- Encerrado em: 2026-06-16
- Retomada: acompanhar feedback mobile de mercado, comunidade, alertas e wallet; se a próxima publicação Android exigir essas telas no canal beta, gerar nova APK em follow-up próprio.
- Reversão lógica: remover overlay de status efetivo em FastAPI/fallback web, restaurar `Insights` no shell mobile, voltar wallet/ticket/alertas/cards ao comportamento anterior e retirar as notas documentais desta fatia.
- Evidências de validação local: `.venv/bin/python manage.py check`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `.venv/bin/python manage.py test tests.test_web_smoke.BackendAuthAPITests.test_market_api_seed_filters_and_detail_contract --keepdb`; `.venv/bin/python manage.py test tests.test_web_smoke.BackendAuthAPITests.test_market_api_treats_expired_auto_close_market_as_locked tests.test_web_smoke.BackendAuthAPITests.test_expired_auto_close_market_blocks_prediction_and_position_actions --keepdb`; `.venv/bin/python manage.py test tests.test_web_smoke.WebSmokeTests.test_main_pages_render --keepdb`; `.venv/bin/python manage.py test tests.test_web_smoke.WebSmokeTests.test_market_pages_consume_api_and_fallback_to_fixture tests.test_web_smoke.WebSmokeTests.test_market_and_result_share_pages_expose_social_cards tests.test_web_smoke.WebSmokeTests.test_home_stays_market_focused_for_guest_and_user tests.test_web_smoke.WebSmokeTests.test_home_stats_show_real_total_predictions tests.test_web_smoke.WebSmokeTests.test_site_local_fallback_treats_expired_auto_close_market_as_locked --keepdb`; `.venv/bin/python manage.py test tests.test_web_smoke.BackendAuthAPITests.test_push_outbox_uses_user_notification_policy_and_safe_payload --keepdb`; `.venv/bin/python -m py_compile apps/web/django/communications/push_services.py tests/test_web_smoke.py`; `cd apps/mobile && flutter pub get`; `cd apps/mobile && flutter analyze`; `cd apps/mobile && flutter test`; `cd apps/mobile && flutter test test/alerts_screen_test.dart test/market_detail_screen_test.dart`; `git diff --check`.
- Evidências de publicação: PR #87 (`Ajusta UX mobile de mercados, alertas e wallet`) mergeada em `main` por squash commit `9f724c989b7d054356fed83130415b14b518dd08`; GitHub Actions `GoTrendLabs CI and Deploy` run `27654353053` concluiu jobs `test` e `deploy` com sucesso; produção respondeu `https://gotrendlabs.com.br/api/health` com `status=ok`, `maintenance.web_enabled=false`, `maintenance.mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; homepage retornou `HTTP/2 200`; `/api/markets` retornou 19 mercados; `/api/markets/rei-rainha-royal-ascot-2026` retornou `status=locked`, `status_label=Fechado`, `auto_close_enabled=true`, `close_at=2026-06-16T15:55:00+00:00` e `comment_count=6`; o mesmo slug ficou ausente de `/api/markets?status=open` e presente em `/api/markets?status=locked`; a página web `/markets/rei-rainha-royal-ascot-2026/` retornou `HTTP 200`, exibiu `Mercado fechado` e manteve o trilho de ciclo sem reabrir o ticket.

## WFLOW-20260616-CADDY-PROBE-BLOCK-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-OPSLOG-001`, infra de produção
- Objetivo: bloquear no Caddy probes comuns de WordPress, PHP, `.env`, `.git` e `vendor` antes que cheguem ao Django, reduzindo ruído em `gotrendlabs_system_logs`
- Etapa atual: publicado em `main` pelas PRs #84 e #85, deploy de produção concluído, proxy recriado e probes validados sem persistência em logs Django
- Artefatos afetados:
  - `ops/deploy/production/Caddyfile`
  - `ops/deploy/production/README.md`
  - `docs/specs/state/feature-changelog.md`
- Bloqueios: nenhum
- Iniciado em: 2026-06-16
- Atualizado em: 2026-06-16
- Encerrado em: 2026-06-16
- Retomada: acompanhar logs técnicos; se surgirem novos padrões de probe recorrentes, adicioná-los ao matcher Caddy em novo follow-up pequeno
- Reversão lógica: remover o matcher `@blocked_probe` e o `handle` correspondente do `Caddyfile`, mantendo as notas documentais como histórico ou revertendo-as em PR separado
- Evidências de validação local: `docker run --rm -v "$PWD/ops/deploy/production/Caddyfile:/etc/caddy/Caddyfile:ro" caddy:2 caddy validate --config /etc/caddy/Caddyfile` com `Valid configuration`; `docker run --rm -v "$PWD/ops/deploy/production/Caddyfile:/etc/caddy/Caddyfile:ro" caddy:2 caddy adapt --config /etc/caddy/Caddyfile --pretty` confirmou `@blocked_probe` antes dos handlers de `/static`, `/media`, `/api` e do proxy Django; após smoke da PR #84 mostrar `/admin/phpinfo.php` ainda chegando ao Django, o matcher foi convertido para `path_regexp` e revalidado com `caddy validate`/`caddy adapt`; `git diff --check`; `docker compose -f ops/deploy/production/docker-compose.yml config` ficou bloqueado localmente pela ausência intencional de `.env.prod`
- Evidências de publicação: PR #84 mergeada em `main` com merge commit `71dbb9f567b671cbebe74aaf3c06b9e357a4a271` e GitHub Actions `GoTrendLabs CI and Deploy` run `27651554576` com jobs `test` e `deploy` em sucesso; PR #85 mergeada em `main` com merge commit `499782e8e6376078d571efec55cacf29b33a5afa` e run `27652030681` com jobs `test` e `deploy` em sucesso; proxy de produção recriado por SSM e validado com `caddy validate` mostrando `path_regexp blocked_probe`; smokes públicos confirmaram `404` direto do Caddy para `/admin/phpinfo.php?codex=final-regexp` e `/admin/.env?codex=final-regexp`, `200` saudável para `/api/health` e home; consulta read-only em `gotrendlabs_system_logs` nos 15 minutos finais retornou `probe_log_count=0`, `recent_error_count=0` e `recent_5xx_count=0`

## WFLOW-20260614-MOBILE-ANTI-ABUSE-CONTRIBUTIONS-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `FEAT-AUTH-001`, `FEAT-SUGGEST-001`
- Objetivo: manter cadastro, feedback e sugestao de mercado de visitantes dentro do app mobile com desafio anti-abuso validado pela FastAPI, corrigindo envio de feedback guest e tornando `Sugerir mercado` visivel no menu principal
- Etapa atual: publicado em `main` pela PR #82, deploy de produção concluído e endpoint anti-abuso mobile validado por smoke
- Artefatos afetados:
  - `apps/api/backend_api/`
  - `apps/mobile/`
  - `packages/contracts/openapi/gotrendlabs-api.json`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/features/mobile-mvp.md`
  - `docs/specs/features/mobile-ux.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/`
- Bloqueios: nenhum conhecido; publicação de APK release/beta permanece fora deste follow-up
- Iniciado em: 2026-06-14
- Atualizado em: 2026-06-15
- Retomada: acompanhar feedback de cadastro, feedback e sugestão no app; para QA física, usar build mobile apontando para `https://gotrendlabs.com.br/api`
- Reversão lógica: remover `GET /anti-abuse/challenge`, remover campos `anti_abuse_token`/`anti_abuse_answer` dos payloads, voltar cadastro/feedback/sugestão mobile ao comportamento anterior e retirar `Sugerir mercado` do menu principal
- Evidências de validação local: `.venv/bin/python -m py_compile apps/api/backend_api/main.py apps/api/backend_api/schemas.py`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `.venv/bin/python manage.py check`; `.venv/bin/python manage.py test tests.test_web_smoke.BackendAuthAPITests.test_recaptcha_blocks_register_and_guest_queue_when_required tests.test_web_smoke.BackendAuthAPITests.test_mobile_anti_abuse_challenge_allows_register_and_guest_queue tests.test_web_smoke.BackendAuthAPITests.test_mobile_anti_abuse_challenge_rejects_wrong_answer tests.test_web_smoke.BackendAuthAPITests.test_recaptcha_not_required_for_authenticated_queue_items --keepdb`; `cd apps/mobile && flutter analyze`; `cd apps/mobile && flutter test test/anti_abuse_repository_test.dart test/support_repository_test.dart test/auth_biometric_test.dart test/shell_screen_test.dart`; `cd apps/mobile && flutter test` com 57 testes OK; `git diff --check`; `cd apps/mobile && flutter build apk --debug --dart-define=GTL_API_BASE_URL=http://127.0.0.1:8001 --dart-define=GTL_PUBLIC_WEB_BASE_URL=http://127.0.0.1:8000`; APK debug instalada no Galaxy S20 via `adb install -r`, com `adb reverse tcp:8001 tcp:8001` e `tcp:8000 tcp:8000`; QA visual física ficou pendente porque o aparelho estava no lockscreen/Bouncer, embora a Activity do app tenha ficado focada atrás do bloqueio
- Evidências de publicação: PR #82 (`Implementa posição mobile e desafio anti-abuso`) mergeada em `main` com merge commit `88b80fe0bd1065e07e75b942716823503c8ba0aa`; GitHub Actions `GoTrendLabs CI and Deploy` run `27542726255` concluiu jobs `test` e `deploy` com sucesso; produção respondeu `https://gotrendlabs.com.br/api/health` com `status=ok`, `web_enabled=false`, `mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; `/api/anti-abuse/challenge` respondeu com `prompt`, `token` e `expires_at`; `/api/openapi.json` expôs `/anti-abuse/challenge` e os campos `anti_abuse_token`/`anti_abuse_answer` em `RegisterPayload`; `/api/markets` retornou 19 mercados

## WFLOW-20260614-MOBILE-POSITION-REVISION-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `FEAT-PRED-001`, `FEAT-WALLET-001`
- Objetivo: implementar no Flutter/mobile a experiência de reforço e revisão de posição já exposta pela FastAPI, preservando backend como autoridade de domínio
- Etapa atual: publicado em `main` pela PR #82, deploy de produção concluído e contratos de posição mobile validados por smoke
- Artefatos afetados:
  - `apps/mobile/`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/features/mobile-ux.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/`
- Bloqueios: nenhum conhecido; QA autenticado de reforço/revisão em dispositivo físico ainda depende de usuário real com posição ativa
- Iniciado em: 2026-06-14
- Atualizado em: 2026-06-15
- Retomada: acompanhar feedback de uso mobile em mercados com posição ativa; QA visual autenticado de reforço/revisão em dispositivo físico deve usar usuário real com posição ativa
- Reversão lógica: remover parsing de `viewer_position` e métodos `position-preview`/`position-actions` no mobile, voltar `PredictionTicket` ao fluxo exclusivo de primeira previsão e restaurar docs/state para reforço/revisão mobile pendente
- Evidências de validação local: `cd apps/mobile && flutter test test/markets_repository_test.dart`; `cd apps/mobile && flutter test test/prediction_ticket_test.dart`; `cd apps/mobile && flutter analyze`; `cd apps/mobile && flutter test` com 55 testes OK; `.venv/bin/python packages/contracts/export_openapi.py --check`; `.venv/bin/python manage.py check`; `git diff --check`; `cd apps/mobile && flutter build apk --debug` gerando `build/app/outputs/flutter-apk/app-debug.apk` com aviso não bloqueante já conhecido de Kotlin Gradle Plugin transitivo em `package_info_plus`/`share_plus`
- Evidências UX incrementais: linguagem mobile simplificada em 2026-06-15 para expor `Aumentar posição` e `Trocar escolha`, mantendo contratos `reinforcement`/`revision`; validação com `dart format lib/src/features/markets/prediction_ticket.dart test/prediction_ticket_test.dart`, `flutter test test/prediction_ticket_test.dart`, `flutter analyze`, `flutter test` com 57 testes OK e `git diff --check`
- Evidências UX incrementais: ações de posição convertidas em frames sempre fechados em 2026-06-15, inclusive quando apenas uma ação estiver disponível, e preview de posição sem `allowed` agora bloqueia confirmação por padrão; validação com `dart format lib/src/features/markets/market_models.dart test/markets_repository_test.dart`, `flutter test test/markets_repository_test.dart test/prediction_ticket_test.dart`, `flutter analyze`, `flutter test` com 59 testes OK, `git diff --check` e APK debug instalada no Galaxy S20 apontando para `https://gotrendlabs.com.br/api` / `https://gotrendlabs.com.br`
- Evidências de publicação: PR #82 (`Implementa posição mobile e desafio anti-abuso`) mergeada em `main` com merge commit `88b80fe0bd1065e07e75b942716823503c8ba0aa`; GitHub Actions `GoTrendLabs CI and Deploy` run `27542726255` concluiu jobs `test` e `deploy` com sucesso; produção respondeu `https://gotrendlabs.com.br/api/health` com `status=ok`, `web_enabled=false`, `mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; `/api/openapi.json` expôs `/markets/{slug}/position-preview` e `/markets/{slug}/position-actions`; `/api/markets` retornou 19 mercados

## WFLOW-20260614-POSITION-REVISION-WEB-FIRST-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-PRED-001`, `FEAT-WALLET-001`, `Admin Ops`, `FastAPI public contract`, `frontend-web`
- Objetivo: implementar reforço e revisão auditável de posições primeiro no backend/site, preservando FastAPI como autoridade e deixando mobile para fase posterior
- Etapa atual: publicado em `main` pela PR #80, deploy de produção concluído e contrato novo validado por smoke
- Artefatos afetados:
  - `apps/api/backend_api/`
  - `apps/web/django/markets/`
  - `apps/web/django/admin_ops/`
  - `apps/web/static/js/gotrendlabs.js`
  - `packages/contracts/openapi/gotrendlabs-api.json`
  - `docs/specs/`
- Bloqueios: nenhum; mobile permanece como fase posterior documentada em `known-gaps.md`
- Iniciado em: 2026-06-14
- Atualizado em: 2026-06-14
- Retomada: acompanhar feedback de uso web e planejar a fase mobile sem mover regra de domínio para o app
- Reversão lógica: remover endpoints `position-preview`/`position-actions`, restaurar unicidade `uniq_prediction_user_market`, remover campos de posição/config, voltar UI para estado somente leitura após primeira previsão e retirar `prediction_revision_penalty`
- Evidências de validação local: `.venv/bin/python manage.py check`; `.venv/bin/python manage.py makemigrations --check --dry-run`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `git diff --check origin/main`; suíte completa `.venv/bin/python manage.py test --keepdb` com 186 testes OK; testes focados de reforço/revisão, bloqueios por cutoff/config, lock transacional de previsão inicial, auditoria de resolução com posições revisadas, Admin Ops Config e regressões de dashboard/AI/resolução/web também executados durante o ciclo de correção
- Evidências incrementais: limite máximo de reforços, grupos de configuração por reforço/revisão e resumo de entradas abertas validados com `.venv/bin/python manage.py test tests.test_web_smoke.BackendAuthAPITests.test_position_reinforcement_and_revision_are_auditable_wallet_mutations tests.test_web_smoke.BackendAuthAPITests.test_position_reinforcement_respects_admin_limit tests.test_web_smoke.BackendAuthAPITests.test_position_revision_respects_admin_config_and_cutoff_window tests.test_web_smoke.WebSmokeTests.test_admin_config_persists_maintenance_json_and_smtp_database_config --keepdb`; `.venv/bin/python manage.py check`; `.venv/bin/python manage.py makemigrations --check --dry-run`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `git diff --check`
- Evidências UX: detalhe web reorganizado para resumo compacto, entradas abertas recolhíveis e abas `Reforçar`/`Revisar`, validado com `.venv/bin/python manage.py test tests.test_web_smoke.WebSmokeTests.test_market_detail_position_actions_use_compact_tabs tests.test_web_smoke.BackendAuthAPITests.test_position_reinforcement_and_revision_are_auditable_wallet_mutations tests.test_web_smoke.BackendAuthAPITests.test_position_reinforcement_respects_admin_limit --keepdb`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `git diff --check`
- Evidências UX incrementais: confirmação de revisão passou a exibir entradas encerradas, total ativo, custo em GT₵/percentual e nova posição estimada vindos da FastAPI, validado com `.venv/bin/python manage.py test tests.test_web_smoke.WebSmokeTests.test_market_detail_position_actions_use_compact_tabs tests.test_web_smoke.BackendAuthAPITests.test_position_reinforcement_and_revision_are_auditable_wallet_mutations tests.test_web_smoke.BackendAuthAPITests.test_position_reinforcement_respects_admin_limit --keepdb`; `.venv/bin/python manage.py check`; `.venv/bin/python manage.py makemigrations --check --dry-run`
- Evidências de publicação: PR #80 (`Reforço e revisão de posição web-first`) mergeada em `main` com merge commit `dc785eac6e0a7c996f0bc312d4c91f90606407fb`; GitHub Actions `GoTrendLabs CI and Deploy` run `27507258490` concluiu jobs `test` e `deploy` com sucesso; produção respondeu `https://gotrendlabs.com.br/` com HTTP 200, `https://gotrendlabs.com.br/api/health` com `status=ok`, `web_enabled=false`, `mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; `/api/markets` retornou o campo `viewer_position`; `/api/openapi.json` expôs `/markets/{slug}/position-preview` e `/markets/{slug}/position-actions`.

## WFLOW-20260613-BADGE-HISTORICAL-OWNERSHIP-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-REP-001`, `Admin Ops`, `FastAPI public contract`
- Objetivo: separar exibição pública/histórica de badges da concessão automática, garantindo que badges pausadas continuem no catálogo visível para todos, sem novas concessões, e que conquistas persistidas continuem compartilháveis e presentes no ranking enquanto a badge estiver visível
- Etapa atual: publicado em `main` e validado em produção
- Artefatos afetados:
  - `apps/api/backend_api/`
  - `apps/web/django/admin_ops/`
  - `apps/web/static/js/gotrendlabs.js`
  - `tests/test_web_smoke.py`
  - `packages/contracts/openapi/gotrendlabs-api.json`
  - `docs/specs/contracts/reputation-ranking.md`
  - `docs/specs/features/reputation-and-ranking.md`
  - `docs/specs/spec_prediction_social_market_pt.md`
  - `docs/specs/state/change-log-specs.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
- Bloqueios: nenhum
- Iniciado em: 2026-06-13
- Atualizado em: 2026-06-13
- Encerrado em: 2026-06-13
- Retomada: evolução futura pode adicionar filtros administrativos por estado de catálogo/concessão ou ações dedicadas de reexibição, preservando a separação `is_active`/`rule_active`
- Reversão lógica: voltar `POST /admin/badges/{code}/deactivate` a ocultar definição e regra, remover `rule_active` do payload administrativo e restaurar filtros públicos para exigir badge ativa e regra ativa no catálogo
- Evidencias de validacao local: testes focados de badges/ranking/compartilhamento e catálogo pausado visível com `.venv/bin/python manage.py test --keepdb tests.test_web_smoke.BackendAuthAPITests.test_badge_catalog_public_personalized_and_admin_contracts tests.test_web_smoke.BackendAuthAPITests.test_badge_awards_are_idempotent_for_automatic_rules tests.test_web_smoke.BackendAuthAPITests.test_rankings_include_recent_active_badges tests.test_web_smoke.WebSmokeTests.test_public_badges_page_renders_for_guest_and_authenticated_user tests.test_web_smoke.WebSmokeTests.test_public_badge_share_link_is_unique_to_awarded_user`; regressao do checkbox Admin Ops com `.venv/bin/python manage.py test --keepdb tests.test_web_smoke.WebSmokeTests.test_admin_badge_form_sends_unchecked_rule_active_false`; `.venv/bin/python manage.py check`; `.venv/bin/python manage.py makemigrations --check --dry-run`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `.venv/bin/python manage.py test --keepdb tests.test_web_smoke` com 180 testes OK
- Evidencias de publicacao: PR #78 mergeada em `main` por squash (`65f8d3d6bdbaa414c73e616015347576a21adc7a`); GitHub Actions `GoTrendLabs CI and Deploy` run `27478757690` concluiu com jobs `test` e `deploy` em sucesso; smoke PRD confirmou `https://gotrendlabs.com.br/`, `/badges/`, `/api/health` e `/api/badges` com HTTP 200, `health.status=ok`, `checks.api=ok`, `checks.database=ok` e payload público de badges contendo `rule_active`.

## WFLOW-20260613-MOBILE-MAINTENANCE-GATE-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `Admin Ops`, `FastAPI public contract`
- Objetivo: implementar manutencao mobile independente da web, controlada pelo Admin Ops, com `GET /health` enriquecido e bloqueio autoritativo da FastAPI para clientes mobile sem excecao por papel no app
- Etapa atual: concluido; PR #75 publicada e mergeada em `main`, GitHub Actions `GoTrendLabs CI and Deploy` verde, producao respondendo com o contrato `/api/health` enriquecido e APK Android beta `1.0.5 (6)` publicada no canal direto
- Artefatos afetados:
  - `apps/api/backend_api/main.py`
  - `apps/web/django/admin_ops/`
  - `apps/web/django/core/platform_config.py`
  - `apps/mobile/`
  - `tests/test_web_smoke.py`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/integration-map.md`
  - `apps/mobile/README.md`
- Bloqueios: nenhum para publicacao; validacao funcional do toggle mobile em sessao Admin Ops autenticada de producao segue como QA operacional recomendado
- Iniciado em: 2026-06-13
- Atualizado em: 2026-06-13
- Encerrado em: 2026-06-13
- Retomada: validar o toggle `Manutenção do app` em sessao Admin Ops autenticada de producao quando houver janela operacional; acompanhar feedback da APK Android beta `1.0.5 (6)` para estados de backend indisponivel/degradado
- Reversao logica: remover `mobile_maintenance_enabled`/mensagem do runtime JSON/Admin Ops, retirar middleware mobile por `X-GoTrendLabs-Client`, voltar `/health` ao contrato simples e remover o gate Flutter `features/maintenance`
- Evidencias de validacao local: `dart format`; `.venv/bin/python manage.py test tests.test_web_smoke.MobileMaintenanceGateTests --keepdb` com 5 testes OK; `cd apps/mobile && flutter test test/maintenance_gate_test.dart` com 4 testes OK; `.venv/bin/python manage.py check`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `cd apps/mobile && flutter analyze`; `cd apps/mobile && flutter test` com 50 testes OK; `git diff --check`; FastAPI e Django locais reiniciados com `.venv/bin/python`; `/health` local retornou `checks.api=ok` e `checks.database=ok`; APK debug Android atualizado foi instalado e aberto no emulador `gotrendlabs_pixel` apos wipe do AVD travado em `RUNNING_LOCKED`
- Evidencias de producao: PR #75 mergeada como `8fe120b6816e08ed86519834b8916fc852e482d9`; GitHub Actions `GoTrendLabs CI and Deploy` run `27473013601` concluiu jobs `test` e `deploy` com sucesso; `https://gotrendlabs.com.br/api/health` retornou `status=ok`, `maintenance.web_enabled=false`, `maintenance.mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; homepage retornou `HTTP/2 200`; `https://gotrendlabs.com.br/admin-ops/config/` redirecionou para login com `HTTP/2 302`, confirmando a rota protegida em producao; `flutter build apk --release --dart-define=GTL_API_BASE_URL=https://gotrendlabs.com.br/api --dart-define=GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br` gerou APK assinada `1.0.5 (6)` com SHA-256 `c061681f2495759cca2d2eaf38282541d4a82fd1309fefb4037f9f4ac0b2109b` e tamanho `57292289` bytes; APK publicada via SSM `e8a5e7b6-4123-4a34-a547-bf136b99e665` com registro ativo em `gotrendlabs_mobile_app_releases`; limpeza de temporario no container concluida via SSM `bc234076-9b0c-41ae-aac9-a18db56b6e63`; `https://gotrendlabs.com.br/app/android/latest.json` retornou `version_name=1.0.5`, `version_code=6`, `file_size=57292289` e o mesmo SHA-256; download publico da APK retornou `HTTP/2 200`, `content-type: application/vnd.android.package-archive`, `content-length=57292289` e hash recalculado identico; bucket S3 temporario de transporte foi removido

## WFLOW-20260613-MOBILE-BIOMETRIC-AUTH-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `FEAT-AUTH-001`, `future-mobile`
- Objetivo: implementar desbloqueio biométrico/local para sessão mobile lembrada no Android e iOS, sem criar endpoint novo e mantendo a FastAPI como autoridade de sessão
- Etapa atual: concluído; PR #73 publicada e mergeada em `main`, GitHub Actions `GoTrendLabs CI and Deploy` verde, produção fora de maintenance mode e APK Android beta `1.0.4 (5)` publicada no canal direto
- Artefatos afetados:
  - `apps/mobile/`
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/feature-changelog.md`
  - `apps/mobile/README.md`
- Bloqueios: nenhum para publicação; smoke real de prompt biométrico em dispositivo físico de usuário segue como QA operacional recomendado
- Iniciado em: 2026-06-13
- Atualizado em: 2026-06-13
- Encerrado em: 2026-06-13
- Retomada: acompanhar feedback da APK Android beta `1.0.4 (5)` e validar em dispositivo físico real com biometria/senha local quando disponível
- Reversão lógica: remover `local_auth`, preferência biométrica, estado `Sessão protegida`, ajustes nativos Android/iOS e restaurar docs/state para a sessão lembrada simples
- Evidências de validação local: `flutter pub get`; `dart format`; `flutter test test/auth_biometric_test.dart` cobrindo login, cadastro, sessão protegida, preferência desligada sem botão `Entrar com biometria` e desbloqueio sem backfill de preferência; `flutter analyze`; `flutter test` com 46 testes OK; `git diff --check`; `flutter build apk --debug` gerou `build/app/outputs/flutter-apk/app-debug.apk` com aviso não bloqueante já conhecido de Kotlin Gradle Plugin transitivo em `package_info_plus`/`share_plus`; APK debug reinstalado no `emulator-5554`; emulador confirmado com PIN ativo (`1234`) e app debug instalado; `plutil -lint apps/mobile/ios/Runner/Info.plist`; `flutter build ios --simulator --debug` passou após alinhar `IPHONEOS_DEPLOYMENT_TARGET=15.0` às dependências Firebase mobile; iOS Simulator `iPhone 17 Pro` com iOS 26.5 carregou dados locais usando `GTL_API_BASE_URL=http://127.0.0.1:8001`; `flutter build apk --release --dart-define=GTL_API_BASE_URL=https://gotrendlabs.com.br/api --dart-define=GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br` gerou APK assinada `1.0.4 (5)` com SHA-256 `43f8c1184ce7c913070d9bc2c09344a70f2ed8f4c14a12749d8e688d831bc81c` e tamanho `57292069` bytes
- Evidências de produção: PR #73 mergeada como `88808880e9f18b4b9c4dd33a5c45be774819541a`; GitHub Actions `GoTrendLabs CI and Deploy` run `27468406864` concluiu `test` e `deploy` com sucesso; APK release assinada `1.0.4 (5)` foi publicada via SSM `f0f9e3de-7c60-40cd-bdc9-40329db9f1cd`; SSM `727013d0-b5ea-48b4-a72c-63fae0f3b09c` desligou maintenance mode; `https://gotrendlabs.com.br/app/android/latest.json` retornou `version_name=1.0.4`, `version_code=5`, `file_size=57292069` e SHA-256 `43f8c1184ce7c913070d9bc2c09344a70f2ed8f4c14a12749d8e688d831bc81c`; download público da APK retornou `HTTP/2 200`, `content-type: application/vnd.android.package-archive` e hash recalculado idêntico; `https://gotrendlabs.com.br/api/health` retornou `{"status":"ok"}`; homepage retornou `HTTP/2 200`; bucket S3 temporário de transporte foi removido

## WFLOW-20260612-MOBILE-FIREBASE-PUSH-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-NOTIFY-001`, `FEAT-MOBILE-001`, `communications`, `future-mobile`
- Objetivo: implementar push mobile FCM real para Android, preservando defaults seguros, credenciais fora do Git/Admin Ops e o app como cliente da FastAPI
- Etapa atual: concluído; PR #71 publicada e mergeada em `main`, GitHub Actions `GoTrendLabs CI and Deploy` verde, PRD com FCM real habilitado fora do Git/Admin Ops e APK Android beta `1.0.3 (4)` publicada com Firebase ativo
- Artefatos afetados:
  - `apps/mobile/`
  - `apps/web/django/communications/`
  - `apps/web/django/admin_ops/`
  - `config/urls.py`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
  - `.env.example`
  - `requirements.txt`
- Bloqueios: nenhum para a ativação operacional; teste ponta a ponta de recebimento ainda depende de usuário autenticado/dispositivo Android com APK `1.0.3 (4)` instalado e permissão de notificação aceita
- Iniciado em: 2026-06-12
- Atualizado em: 2026-06-12
- Encerrado em: 2026-06-12
- Retomada: validar recebimento real no Android com usuário autenticado, acompanhar novos devices em Admin Ops e publicar nova APK apenas quando houver incremento de versão/canal
- Reversão lógica: voltar Flutter para provider noop/fake-token, remover dependências Firebase mobile, canal Android, sender Firebase Admin SDK e restaurar docs/state para fase dry-run/noop mantendo outbox `PushDelivery` intacta
- Evidências de validação local: `dart format lib test`; `git diff --check`; `flutter analyze`; `flutter test`; `flutter test test/push_controller_test.dart test/push_repository_test.dart test/about_screen_test.dart`; `flutter build apk --debug`; `.venv/bin/python manage.py check`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `RECAPTCHA_ENABLED=0 .venv/bin/python manage.py test --keepdb` com os testes focados `BackendAuthAPITests.test_fcm_provider_marks_successful_delivery_as_sent`, `test_fcm_provider_retries_transient_send_errors`, `test_push_outbox_uses_user_notification_policy_and_safe_payload`, `test_push_preferences_block_outbox_and_provider_invalidates_bad_tokens`, `WebSmokeTests.test_admin_push_devices_tab_lists_devices_without_raw_tokens` e `WebSmokeTests.test_admin_ops_requires_staff_and_renders_api_data`; teste local com service account Firebase carregada confirmou `provider=fcm`, `dry_run=False`, `fcm_secret_configured=True` sem imprimir segredo
- Evidências de produção: PR #71 mergeada como `e51465e8f5894521edbaf716d0e35750dc386fe9`; GitHub Actions `GoTrendLabs CI and Deploy` run `27445681561` concluiu `test` e `deploy` com sucesso; SSM `5582a581-d8ee-4a8e-9034-b6251797c7d6` atualizou `/opt/gotrendlabs/.env.prod`, recriou `django`, `fastapi` e `daemon`, `manage.py check` passou e `push_runtime_config` retornou `enabled=True`, `provider=fcm`, `dry_run=False`, `fcm_secret_configured=True`; APK release assinada `1.0.3 (4)` com SHA-256 `88e5620dd7d6989e01b785f9c2ebee94cce11817fd4b0687681ea286da133713` foi publicada via SSM `2f08493a-2337-4507-be4c-20972982b75c`; `https://gotrendlabs.com.br/app/android/latest.json` retornou `version_name=1.0.3`, `version_code=4`, `file_size=56555211` e o mesmo SHA-256; download público da APK retornou `HTTP/2 200` e hash recalculado idêntico; `https://gotrendlabs.com.br/api/health` retornou `{"status":"ok"}`; maintenance permaneceu desligado; bucket S3 temporário de transporte foi removido

## WFLOW-20260611-MOBILE-UX-FEED-RANKING-SESSION-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`
- Objetivo: implementar melhorias de feed mobile, ranking, confirmação de previsão, consenso multi-série, push informativo em `Sobre`, tracking de view/share, sessão com `Lembrar login` e APK Android beta `1.0.2+3`
- Etapa atual: concluído; branch `feature/mobile-ux-feed-ranking-session` publicada, PR #70 criada, `main` atualizada para `0577280`, deploy de produção executado via SSM e APK Android beta `1.0.2 (3)` publicada em produção
- Artefatos afetados:
  - `apps/mobile/`
  - `apps/mobile/test/`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/features/mobile-mvp.md`
  - `docs/specs/features/mobile-ux.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/integration-map.md`
  - `docs/specs/state/known-gaps.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `apps/mobile/README.md`
- Bloqueios: GitHub API/Actions ficou indisponível por timeout durante o fechamento; merge foi aplicado por fast-forward via `git push` para `main` e deploy foi executado diretamente por SSM
- Iniciado em: 2026-06-11
- Atualizado em: 2026-06-12
- Encerrado em: 2026-06-12
- Retomada: acompanhar feedback de usuários no Android beta `1.0.2 (3)`; se precisar publicar nova APK, incrementar `version` em `apps/mobile/pubspec.yaml`, gerar release assinada com os defines de produção e publicar pelo Admin Ops/canal direto
- Reversão lógica: reverter ajustes Flutter de feed/ranking/sessão/consenso/push informativo/tracking, restaurar splash/header anterior e voltar README/specs/state para o comportamento mobile anterior
- Evidências de validação local: `git diff --check`; `flutter pub get`; `flutter analyze` sem issues; `flutter test` com 35 testes OK; `flutter build apk --release --dart-define=GTL_API_BASE_URL=https://gotrendlabs.com.br/api --dart-define=GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br --dart-define=GTL_PUSH_FIREBASE_ENABLED=false` gerou APK assinada com SHA-256 `ae52faaf0525cd22dd45da3ced89ba6f7f208864da3c7c26384e9a0b0c3337bb`; QA local em Android Emulator e iPhone Simulator durante a implementação; revisão documental contra `gotrendlabs-mobile-docs-governor`
- Evidências de produção: deploy SSM `43bc0576-7521-4c1d-be4e-ccb107be40cf` concluiu `Success`, sem migrations pendentes e com containers `django`, `fastapi`, `daemon` e `proxy` recriados; release Android publicada por SSM `8bc28e39-0fd1-4306-a807-9598b5256c8f`, `https://gotrendlabs.com.br/app/android/latest.json` retornou `version_name=1.0.2`, `version_code=3`, `file_size=55753713` e SHA-256 `ae52faaf0525cd22dd45da3ced89ba6f7f208864da3c7c26384e9a0b0c3337bb`; download público de `https://gotrendlabs.com.br/media/app_releases/android/gotrendlabs-android-1.0.2-3.apk` retornou `HTTP/2 200`, `content-type: application/vnd.android.package-archive`, `content-length: 55753713` e hash recalculado idêntico; `https://gotrendlabs.com.br/api/health` retornou `{"status":"ok"}`

## WFLOW-20260611-SOCIAL-AUTH-IMMEDIATE-EMAIL-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`, `FEAT-NOTIFY-001`
- Objetivo: implementar login social real para Google/Facebook/X, envio imediato filtrado para emails críticos de autenticação e rodapé institucional automático em emails transacionais
- Etapa atual: concluído; branch `feature/social-login-immediate-email` criada a partir de `origin/main`, login social real, dreno imediato filtrado de emails críticos e rodapé transacional automático implementados
- Artefatos afetados:
  - `apps/api/backend_api/`
  - `apps/web/django/accounts/`
  - `apps/web/django/communications/`
  - `docs/specs/`
  - `packages/contracts/openapi/gotrendlabs-api.json`
  - `tests/test_web_smoke.py`
- Bloqueios: credenciais OAuth informadas em chat/notes devem ser rotacionadas antes de produção e instaladas apenas via ambiente
- Iniciado em: 2026-06-11
- Atualizado em: 2026-06-11
- Encerrado em: 2026-06-11
- Retomada: instalar credenciais OAuth rotacionadas em PRD, configurar callbacks dos provedores, recriar `django`, `fastapi` e `daemon`, validar `/api/health`, login social com conta teste, cadastro/reset imediato e rodapé em novo email
- Reversão lógica: voltar botões sociais para placeholder, remover variáveis OAuth do ambiente, manter outbox/daemon como caminho único e remover rodapé automático do renderizador
- Evidências de validação local: `python manage.py check`; `python manage.py makemigrations --check --dry-run`; `python manage.py test --keepdb tests.test_web_smoke` com 167 testes OK; `python packages/contracts/export_openapi.py --check`; `git diff --check`

## WFLOW-20260609-RESEND-TRANSACTIONAL-EMAIL-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-NOTIFY-001`, `communications`
- Objetivo: adicionar Resend como provider de email transacional via API HTTPS, preservando outbox, templates, retries, logs e SMTP genérico como fallback
- Etapa atual: concluído; branch `feature/resend-transactional-email` criada a partir de `origin/main`, provider Resend implementado, integração antiga de email removida do app/docs, resíduos de banco/env limpos, reset de senha com envio imediato e links absolutos
- Artefatos afetados:
  - `apps/web/django/communications/`
  - `apps/web/django/admin_ops/`
  - `apps/api/backend_api/main.py`
  - `config/settings.py`
  - `.env.example`
  - `.env.prod.example`
  - `docs/specs/`
  - `tests/test_web_smoke.py`
- Bloqueios: ativação real em produção depende de instalação de `GOTRENDLABS_RESEND_API_KEY`, DNS Resend verificado e rotação da key compartilhada no chat
- Iniciado em: 2026-06-09
- Atualizado em: 2026-06-09
- Encerrado em: 2026-06-09
- Retomada: após deploy, definir provider `resend` no Admin Ops, preencher `no-reply@gotrendlabs.com.br`, instalar `GOTRENDLABS_RESEND_API_KEY` fora do Git, recriar containers e validar com `send_resend_test_email`
- Reversão lógica: voltar `email_provider` para `smtp`, remover `GOTRENDLABS_RESEND_API_KEY` do ambiente e manter outbox/templates/SMTP existentes intactos
- Evidências de validação local: `manage.py makemigrations --check --dry-run`; `manage.py check`; suíte completa `manage.py test --keepdb` com 163 testes OK; `git diff --check`; busca local confirmou ausência da key real Resend nos arquivos alterados

## WFLOW-20260608-MOBILE-LAUNCHER-BRANDING-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`
- Objetivo: alinhar a identidade nativa do app ao site, usando nome exibido `GoTrendLabs`, icone de launcher derivado do logo de constelacao e splash Android escuro
- Etapa atual: concluido; nome iOS, icones iOS/Android, variantes iOS `dark`/`tinted` e launch theme Android moderno com lockup/branding da marca atualizados e validados localmente em 2026-06-08
- Artefatos afetados:
  - `apps/mobile/ios/Runner/Info.plist`
  - `apps/mobile/ios/Runner/Assets.xcassets/AppIcon.appiconset/`
  - `apps/mobile/android/app/src/main/res/mipmap-*/ic_launcher.png`
  - `apps/mobile/android/app/src/main/res/drawable*/launch_background.xml`
  - `apps/mobile/android/app/src/main/res/drawable-nodpi/launch_*.png`
  - `apps/mobile/android/app/src/main/res/values*/`
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/state/feature-changelog.md`
- Bloqueios: nenhum local
- Iniciado em: 2026-06-08
- Atualizado em: 2026-06-08
- Encerrado em: 2026-06-08
- Retomada: se o visual do launcher/splash for refinado novamente, gerar novas variantes `Any`, `Dark` e `Tinted` a partir da mesma marca do site e validar no iOS/Android Simulator
- Reversao logica: restaurar `CFBundleDisplayName` anterior, icones de launcher anteriores em iOS/Android e launch theme Android padrao do Flutter
- Evidencias de validacao local: `plutil -lint apps/mobile/ios/Runner/Info.plist`; `flutter analyze`; `flutter build apk --debug`; `flutter build ios --simulator --debug`; `assetutil --info build/ios/iphonesimulator/Runner.app/Assets.car` confirmou `UIAppearanceDark` e `Tinted`; `xcrun simctl listapps` confirmou `CFBundleDisplayName = GoTrendLabs`; app relancado no `GTL iPhone 16` com `GTL_API_BASE_URL=http://127.0.0.1:8001` e `GTL_PUBLIC_WEB_BASE_URL=http://127.0.0.1:8000`; APK debug reinstalado no `emulator-5554`, label `GoTrendLabs` confirmado via `aapt dump badging`, gaveta Android validada visualmente, launch theme escuro validado ao abrir `br.com.gotrendlabs.gotrendlabs_mobile/.MainActivity` e frames capturados confirmaram splash moderno com badge, wordmark, tagline e fundo escuro

## WFLOW-20260608-ANDROID-DIRECT-DOWNLOAD-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`
- Objetivo: distribuir beta Android publico pelo site oficial com APK release assinado, Admin Ops de upload, CTA discreto no rodape/login/cadastro/compartilhamento, checksum publico e API mobile em `/api/*`
- Etapa atual: concluido; APK Android `1.0.1 (2)` assinado com a identidade nativa atual foi publicado em producao e o link HTTPS direto foi validado em 2026-06-08
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
- Bloqueios: nenhum para o canal direto
- Observacao operacional: a release anterior `1.0.0 (1)` foi assinada com certificado SHA-256 `5a5bf9444b9ac753a59af2514e84897179de4b3d311f42844b7eae856d89afe4`, diferente da nova chave estavel local `3b549cb758247332d5ec1cdd5522d35fb15360d240bd3974e4c4ac1d4e2be05f`; quem instalou a APK anterior pode precisar desinstalar e reinstalar uma vez
- Iniciado em: 2026-06-08
- Atualizado em: 2026-06-08
- Encerrado em: 2026-06-08
- Retomada: quando o canal for revisado, conferir `/app/android/latest.json`, rodape/login/cadastro/compartilhamento com link direto, download HTTPS, SHA-256 e smokes de API publica em `/api/health` e `/api/markets`
- Reversao logica: remover CTA Android do rodape/login/cadastro/compartilhamento, modelo `MobileAppRelease`, tela Admin Ops e rota Caddy `/api/*`, mantendo o app mobile local intacto
- Evidencias de validacao local: `manage.py check`; `manage.py makemigrations --check --dry-run`; testes focados de pagina Android/Admin Ops/Caddy; suite Django completa `manage.py test --keepdb` com 160 testes OK; `flutter analyze`; `flutter test`; `flutter build apk --debug`; `flutter build apk --release` falhando sem signing conforme esperado; `flutter build apk --release` com keystore temporaria local e defines de producao gerando APK assinado; segredo/keystore temporarios removidos apos validacao
- Evidencias de validacao de producao: release ativa `1.0.1 (2)` criada em `gotrendlabs_mobile_app_releases` com arquivo `app_releases/android/gotrendlabs-android-1.0.1-2.apk`, SHA-256 `065c352e10d942d86c8665745fe91d374bd168db81377fd666c858fedbf8d186` e `file_size=55458673`; `curl -I -L https://gotrendlabs.com.br/media/app_releases/android/gotrendlabs-android-1.0.1-2.apk` retornou `HTTP/2 200`, `content-type: application/vnd.android.package-archive` e `content-length: 55458673`; download HTTPS recalculado com `shasum -a 256` retornou o mesmo SHA-256; apos recriar o container `proxy` para aplicar o `Caddyfile` versionado, `https://gotrendlabs.com.br/api/health` retornou `HTTP/2 200` com `{"status":"ok"}`, `https://gotrendlabs.com.br/api/markets` retornou JSON de mercados e `/app/android/latest.json` retornou a release ativa `1.0.1 (2)`.

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
- Reversão lógica: selecionar provider `smtp` ou desabilitar `email_enabled`, mantendo outbox para auditoria.
- Evidências de validação: `manage.py check`, `manage.py makemigrations --check --dry-run`, suite `manage.py test --keepdb`, `git diff --check`, `send_resend_test_email --dry-run` e teste real retornando erro Resend de domínio não verificado.

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
