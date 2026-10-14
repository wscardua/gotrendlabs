## Atualização de publicação — 2026-10-12

PR #166 integrada; CI completo da PR e main aprovado com 515 testes/2 skips por execução, incluindo migrations em PostgreSQL limpo. Deploy e smoke técnico produtivo aprovados; [evidências e limites](analytics-production-20261012.md). Os registros locais abaixo são históricos; suas ressalvas não significam que o gate de CI permaneça pendente.

# Aceite local — comparação de acessos por plataforma

- Data: 2026-10-12; FEAT-ANALYTICS-001 v0.6.
- Branch: `feature/analytics-platform-comparison`, criada após fetch de `origin/main` cea46e2 em worktree isolado. Alterações anteriores da pasta original preservadas.
- Runtime usado: ambiente existente `gotrendlabs-ai-thumbnails/.venv`, Python 3.11. O `.venv` original usa Python 3.9 e não importa anotações preexistentes da main.

## Resultado

FastAPI retorna `platforms` e `platform_daily`. Sessões, visitantes e contas são distintos no período; visualizações contam páginas/telas; participação usa sessões do recorte. Todos os filtros são aplicados. O Admin Ops mostra cards Web/App mobile, gráfico responsivo e tabela diária acessível sem JavaScript. Web inclui navegador no celular. Não houve mudança no Flutter, na coleta, nas tabelas ou nas permissões.

## Evidências

- `manage.py test tests.test_analytics_contract tests.test_analytics_web.AnalyticsPlatformPresentationTests --noinput`: 8 testes/OK, incluindo origem única e participação ausente sem sessões.
- `AnalyticsIntegrationTests.test_platform_comparison_counts_distincts_and_respects_filters`: OK, executado isoladamente em schema vazio `gtl_analytics_platform_qa` no banco de testes existente `gtl_mcp_pilot`, com estruturas copiadas e search_path restrito. Schema removido ao final; nenhum dado público do banco alterado. Valida ingestão FastAPI, deduplicação, IDs distintos por período, conta compartilhada entre plataformas, exclusão staff/bot, filtro móvel de período, público, cidade/UF, plataforma única e dias UTC sem eventos. Estruturas copiadas com LIKE não replicam triggers/FKs; esta evidência valida agregações e ingestão, não substitui uma suíte normal com todas as migrations.
- `python tests/analytics_platforms_browser.py`: OK no Chrome headless com template e assets reais e dados sintéticos. Viewports 1280px e 390px, ambas/única/vazia, gráfico sem NaN/Infinity, ausência de overflow horizontal/erros JS, tabela sem JS e abertura por Enter. Capturas em `.runtime/analytics-platform-browser/`; desktop e mobile inspecionados visualmente.
- `manage.py check`, `manage.py makemigrations --check --dry-run`, `node --check apps/web/static/js/analytics-platforms.js` e `git diff --check`: OK.
- Exportação OpenAPI e `packages/contracts/export_openapi.py --check`: OK. Snapshot permanece idêntico; a rota existente tem resposta sem response_model. Shape dos novos campos documentado em `contracts/analytics-events.md`.

## Limites e retomada

A suíte direcionada normal de 16 testes não iniciou: PostgreSQL local ficou travado nas operações de remoção de `test_gotrendlabs` e criação de `test_gtl_analytics_platform_comparison`, apesar dos pedidos de cancelamento e terminação das conexões. Os runners foram interrompidos. Não houve remoção comprovada de `test_gotrendlabs` nem criação comprovada do novo banco. Um contêiner temporário ficou no estado Created e foi removido sem iniciar. Não houve reinício dos serviços compartilhados. SQLite não executa SQL de migrations preexistentes; não foi usado para declarar aprovação de integração.

Após resolver o ambiente local, repetir no banco isolado:

```sh
DJANGO_POSTGRES_DB=gtl_analytics_platform_comparison BACKEND_API_URL=http://127.0.0.1:9 /caminho/do/venv/bin/python manage.py test tests.test_analytics_integration tests.test_analytics_contract tests.test_analytics_web --noinput
```

A v0.6 está implementada e validada nos cenários acima localmente. Sem commit, PR, publicação ou deploy. Smoke produtivo permanece para publicação.

## Impacto MCP

Sem ajuste necessário: o MCP não consome o resumo administrativo e o contexto editorial continua expondo analytics como indisponível. A melhoria não altera ferramentas, schemas MCP, permissões, erros, replays ou orientação editorial; não amplia acesso de agentes a partir do acesso staff humano.

## Ativação do DEV local

Web/API reiniciados a partir da worktree de comparação, com configuração e ambiente virtual existentes. Proxy em http://localhost:8000, banco, media e MCP preservados. Health e assets novos retornaram HTTP 200; agregação usando a role FastAPI DEV e template completo com dados locais passaram. No recorte de 7 dias, Web retornou 3 sessões e App mobile 0; não foram criados eventos fictícios. A rota administrativa mantém exigência de sessão e redireciona para login sem autenticação. Acesso: http://localhost:8000/admin-ops/analytics/.

## Correção do finding de concorrência

`AnalyticsIntegrationTests.test_platform_comparison_is_consistent_during_concurrent_ingestion` executa uma nova ingestão mobile em outra conexão após a execução do primeiro SELECT do resumo. Antes da correção, o teste falhou com soma das sessões por plataforma 2 e total 1. Após usar GROUPING SETS para obter os dois níveis de agregação na mesma instrução/snapshot, passou: o resumo inicial tem Web 1/100%, mobile 0/0%; uma nova leitura vê Web 1/50%, mobile 1/50%. Os IDs globais continuam distintos entre plataformas, sem somar contas como pessoas.

Executados novamente o cenário original de filtros/zeros em PostgreSQL e os oito testes de contrato/apresentação: OK. Ambos os cenários PostgreSQL usaram schema isolado com estruturas copiadas, removido ao final; a limitação de migrations/triggers/FKs e da suíte normal acima permanece. Nenhuma operação foi feita nos dados DEV para esse teste. OpenAPI --check e diff --check passaram; DEV recarregou o backend, health HTTP 200 e resumo com a role DEV mantiveram números consistentes. Contrato JSON, autenticação/MFA, Flutter, MCP e escrita/replays não mudam.
