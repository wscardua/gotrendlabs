# Fechamento legado publicado — diagnóstico e feedback

WFLOW-20261007-LEGACY-CLOSURE-FEEDBACK-001. Chrome DEV confirmou POST rejeitado no mercado lider-vendas-ev-4t26: formulário contém data e fuso, mas FastAPI retorna definição registrada protegida. Há uma previsão e definição assinada. Não é falha de parser/data picker; dados persistidos permanecem sem close_at/fuso.

Backend agora explica especificamente bloqueio de data/fuso/modo quando um campo protegido mudou. Admin Ops distingue configuração do registro salvo e formulário ainda não persistido, preserva preenchimento e explica condição de legado assinado. Gate de novas publicações e proteções de definição não foram removidos. Nenhum prazo/mercado/previsão/prova DEV alterado e nenhum cancelamento executado.

Testes: UI verifica aviso sem instrução enganosa e POST rejeitado preservando valor; PostgreSQL isolado verifica tentativas de mudar prazo/fuso/modo em publicado com previsões, sem mutação de configuração/revisão e com mensagem específica; mantém cenário resolução e preservação de dados/gráficos. Fixtures incompletas do novo teste web foram ajustadas (sessão/contexto/identificadores), sem mudanças de domínio para atender testes.

Execução: .venv/bin/python ops/scripts/test_mcp_local.py --db-admin-env ../gotrendlabs/.env.db-admin.local --database gtl_mcp_closure_feedback_pass tests.test_mcp_publication_ui tests.test_web_smoke.BackendAuthAPITests.test_admin_market_edit_preserves_collected_resolution_and_graph_data. Resultado: **12 testes / 4,794 s / OK**, banco isolado destruído. Django check, OpenAPI --check, Ruff F nos testes/F821-F823 no main e git diff --check aprovados.

Chrome confirmou aviso atualizado; screenshot local .runtime/universal-editorial/legacy-closure-feedback.png. Formulário do operador não foi recarregado; nova aba somente leitura para QA. Sem migrations, deploy ou merge.

Limitação: retificação assinada de prazo/fuso não existe no contrato atual. Cancelamento/refund e nova proposta revisada são alternativas operacionais existentes, dependentes de decisão humana. Esta entrega corrige diagnóstico/apresentação, não permite salvar nova configuração do legado publicado.
