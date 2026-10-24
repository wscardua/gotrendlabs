# Fechamento técnico produtivo — histórico analítico MCP (24/10/2026)

## Publicação e proteção

- [PR #175](https://github.com/wscardua/gotrendlabs/pull/175), merge `06c1ef09a86d6491670dd347e9498c52ef384e0e`. A branch local `feature/mcp-analytics-history` foi preservada.
- [CI da PR](https://github.com/wscardua/gotrendlabs/actions/runs/40134603844): 587 testes, 2 skips, OpenAPI e builds aprovados. A primeira execução falhou por fixture de consentimento sem campos obrigatórios; o commit `6231b00` alinhou o teste ao contrato, sem fallback de aplicação. [CI, build e deploy da main](https://github.com/wscardua/gotrendlabs/actions/runs/40135480756): sucesso.
- A chave estável de presença analítica foi criada na EC2 em `.env.prod` com modo `0600`, sem registrar seu valor. Snapshot criptografado do volume `snap-065ca39c378db3cb0` e snapshot RDS `gotrendlabs-pre-mcp-analytics-20261024` ficaram disponíveis antes do merge. A role de migração possuía `CREATE` no banco e `pgcrypto` estava disponível.
- SSM `c8cbfb58-80e0-4839-a6b9-9158f3643c15` confirmou SHA implantada, `admin_ops.0027_analytics_history`, `pgcrypto` e `daemon`, `django`, `fastapi`, `mcp`, `proxy` e `thumbnail-worker` em execução.

## Dados e consultas

- Os checkpoints cobrem 17 dias consecutivos, de 29/09 a 15/10/2026, com 1.802 eventos de origem e zero divergências entre `source_events` e eventos brutos ainda presentes (SSM `bb10fb89-6301-4a74-8d26-334b332ebb34`). Nenhum dia foi expurgado nesta data. O daemon já havia consolidado os dias maduros; o backfill explícito idempotente retornou `days=0`, `events=0`, `remaining_days=0` (SSM `33303c9e-d7e0-4704-bff7-09c6545947db`).
- Consulta real da FastAPI no banco produtivo (SSM `a0290a6b-8f12-4672-a3d5-9a0c9478f9f7`): contrato `analytics-mcp.v1`; primeiro evento observável 29/09, último 24/10, consolidado até 15/10. `all_history=true` solicitou 15/06–25/10 por incluir cadastros de domínio; eventos observados cobriram 29/09–25/10. Consultas de um e dez anos responderam com `before_instrumentation=true`; série anual de dez anos retornou 11 buckets e `has_more=false`. Nenhum evento anterior à coleta foi reconstruído. `prediction_preview_viewed` e `share_started` permanecem `no_observations`, não zero observado.
- `EXPLAIN ANALYZE` na role FastAPI (SSM `fcc516cf-de4e-4e3d-bae3-b8c0b1ce4136`): agregação de contagens em 0,189 ms e distintos de presença em 0,314 ms, com 197 linhas de presença. Esta amostra é pequena e não valida escala futura.

## MCP e limite da homologação

- A chamada autenticada à integração MCP conectada `get_editorial_signals` retornou `analytics.availability=available` e resumo observado. Sem credencial, `/mcp` respondeu 401; metadados OAuth de servidor e recurso responderam 200 e anunciaram `analytics:read`. O adaptador produtivo registrou 18 ferramentas, incluindo as oito analíticas (SSM `d3aa85bd-d2e6-4e3c-8fca-31c59da690a9`).
- A única integração produtiva ativa, `MyGoTrendLabsIntegrations`, tinha inicialmente apenas os cinco escopos anteriores. O operador concedeu `analytics:read` depois da implantação, confirmado por leitura do backend; nenhuma permissão foi inferida do acesso humano ou alterada diretamente no banco. A reconexão do ChatGPT às 22:10 UTC criou um grant novo **sem** `analytics:read`; os tokens ativos também conservaram os escopos antigos. O catálogo disponível ao agente conectado ainda mostrou dez ferramentas, enquanto o adaptador produtivo registrou 18. Portanto, as oito ferramentas estão registradas e autorizáveis, mas o app cliente precisa solicitar o novo escopo, atualizar ferramentas e passar por novo consentimento antes do smoke autenticado de `tools/list`, cobertura, janela longa, paginação e revogação.
- A exclusão operacional de visitante, carga em volume representativo, experiência Dot/LM Studio produtiva e correções após expurgo não foram ensaiadas aqui. O contrato e o [runbook](../../guides/mcp-analytics-history.md) conservam esses limites.

WFLOW-20261024-MCP-ANALYTICS-HISTORY: implantação técnica concluída e escopo concedido pelo operador; ativação da conexão externa depende de configurar os escopos solicitados no app cliente, novo OAuth e smoke posterior. A reconexão com escopos antigos não valida as oito ferramentas.
