# Revisão editorial universal — evidências locais 2026-10-07

Workflow: WFLOW-20261007-UNIVERSAL-EDITORIAL-001, vinculado ao WFLOW-20261007-MCP-EDITORIAL-SPEC. FEAT-EDITORIAL-001 v1.3 e FEAT-MCP-001 v1.4. Solicitação explícita substitui exceção anterior do gate apenas MCP. Branch feature/mcp-editorial, worktree gotrendlabs-mcp; analytics/mobile preservados. Sem merge/deploy/produção.

## Resultado por aceite

| Critério | Resultado |
| --- | --- |
| Todo mercado possui ficha | Criação humana, conversão de sugestões e MCP cobertas; migration 0003 backfill idempotente, origem humana integration nullable |
| Aprovação exigida na publicação | FastAPI/lifecycle bloqueia ausência, preparo, devolução, rejeição, revisão/hash/política/conteúdo divergentes antes de assinatura; edição invalida |
| Fechamento completo | Ambos os modos exigem prazo futuro aware, fuso IANA válido e modo explícito; ausência/passado/fuso inválido bloqueados com 422 closure_configuration_invalid |
| Publicação válida | Parecer atual + configuração válida publicam; fechamento manual testado via lock; regras existentes de opções/texto/taxonomia preservadas |
| Histórico legado | Migration não altera estados/dados/provas nem aprova legados; parecer em open/locked só altera ficha; terminais somente leitura |
| Admin Ops | Menu Revisão editorial, origem humana sem selo IA, link de ficha universal, alertas de fechamento, fonte adicional com atestação explícita; erro mantém preenchimento |
| Auth/isolamento/logs/cotas/concorrência | Suite MCP com SDK real OAuth e serviço, revogação/audience/roles/idempotência/leases/quota e corridas; MCP sem ORM, regras na API |
| Regressões | Ranking temático, publicação, previsão, payout/perda/reputação, distribuição, undo/refund, cancelamento e órfãos, preservação de dados/provas, conversão de sugestão |

## Execução final

`.venv/bin/python ops/scripts/test_mcp_local.py --db-admin-env ../gotrendlabs/.env.db-admin.local --database gtl_mcp_universal_regression` com labels:

- tests.test_mcp_editorial
- tests.test_mcp_publication_ui
- tests.test_mcp_adapter
- tests.test_mcp_consent_query
- tests.test_admin_navigation
- tests.test_web_smoke.BackendAuthAPITests.test_rankings_filter_category_subcategory_recalculates_theme
- tests.test_web_smoke.BackendAuthAPITests.test_admin_resolve_market_applies_payout_loss_and_reputation_formula
- tests.test_web_smoke.BackendAuthAPITests.test_market_resolution_distribution_math_undo_and_refund_audit
- tests.test_web_smoke.BackendAuthAPITests.test_admin_cancel_market_refunds_open_predictions_without_reputation_change
- tests.test_web_smoke.BackendAuthAPITests.test_reconcile_canceled_market_refunds_open_prediction_orphans
- tests.test_web_smoke.BackendAuthAPITests.test_admin_market_edit_preserves_collected_resolution_and_graph_data
- tests.test_web_smoke.BackendAuthAPITests.test_admin_market_api_requires_staff_and_manages_markets_taxonomy
- tests.test_web_smoke.BackendAuthAPITests.test_operational_queues_submit_review_convert_and_reward

**68 testes / 195,984 s / OK**. PostgreSQL descartável test_gtl_mcp_universal_regression destruído; sem publicação de mercado DEV. Log local /tmp/gtl-universal-regression.log. Rodadas anteriores identificaram expectativas de revisão publicada e fixtures PATCH sem expected_revision; corrigidas antes da execução final. Aprovações criadas só em fixtures isoladas, sem autoaprovação no produto.

OpenAPI --check, makemigrations --check --dry-run, manage.py check, Ruff F nos módulos novos/alterados e F821/F822/F823 nos arquivos legados, git diff --check aprovados. Lint global de main.py contém imports/redefinições preexistentes; não feito cleanup incidental.

## DEV e conferência visual

Aplicada editorial_integrations.0003_universal_editorial com role de migrations local, sem mudança de grants runtime. Comparação SHA-256 antes/depois: 4 mercados, 9 opções, 3 previsões, 4 definições de integridade, 2 selos e ficha MCP preexistente preservados. Novas fichas #1/#2/#3 preparação/revisão1/origem humana; #5 Tesla aprovado/revisão11 preservado. Prova local ignorada: .runtime/universal-editorial/dev-migration.json.

Chrome localhost:8000: editor EV mostra aviso de close_at/fuso ausentes e link Conferir ficha editorial; revisão #3 mostra E01–E11 pendentes, fontes e formulário humano, sem alterar lifecycle. Menu renomeado. Screenshots .runtime/universal-editorial/editor.png e review.png. Conferência desktop, sem alegar teste mobile.

## Limites e operação

EV já estava aberto sem prazo/fuso; permanece aberto, nenhuma data foi inventada e nenhuma previsão/definição assinada foi reescrita. Operador deve tratar configuração histórica com as regras de integridade existentes. Gate protege novas publicações e não garante uptime do daemon ou verdade da atestação humana. Deploy/rollback preparado no runbook; produção não tocada. Dot/HTTPS/renovação externa seguem pendentes e FEAT-MCP-001 permanece parcial. Manual editorial/criteria continua v1.2 aprovado, diversidade sem cotas obrigatórias.
