# Recibo produtivo — resiliência de conexões

05/11/2026. WFLOW-20261105-PRD-DB-RESILIENCE, vinculado à investigação WFLOW-20261105-PRD-ERROR-INVESTIGATION. O smoke abaixo foi somente leitura; não houve teste de carga, mutação de dados, alteração manual de configuração nem rollback em PRD.

## Integração e implantação

- [PR #188](https://github.com/wscardua/gotrendlabs/pull/188) integrada em `main` pelo merge `595a8ac9eee1d3ea601ee0d3ddab4bfd32b9cc88`. A branch local `fix/prd-db-resilience-20261105` foi preservada.
- A primeira CI da PR, [42077291104](https://github.com/wscardua/gotrendlabs/actions/runs/42077291104), falhou ao destruir o banco de testes depois das asserções. O runner passou a drenar logs e fechar pools antes do teardown final. A [CI corrigida da PR 42080024568](https://github.com/wscardua/gotrendlabs/actions/runs/42080024568) aprovou build de produção/MCP, OpenAPI, Node e suíte Python com teardown limpo.
- [Actions de `main` 42082043411](https://github.com/wscardua/gotrendlabs/actions/runs/42082043411): build, OpenAPI, testes e deploy por SSM aprovados. Não houve migration, novo grant ou variável produtiva necessária para esta fatia.
- SSM somente leitura `f412afb7-b628-4023-965b-98834a2ed229`: checkout no host em `595a8ac`; daemon, Django, FastAPI, MCP, proxy e thumbnail worker em execução; MCP `healthy`.

## Smoke e capacidade observada

- `GET /api/health`: 200, `api=ok`, `database=ok`, manutenção web/mobile desativada. `GET /`, `GET /api/markets`, detalhe API de mercado público e página web de integridade: 200. Mercado web inexistente: 404 preservado. O detalhe web público real não foi solicitado porque sua entrega registra visualização; não executar teste mutável em PRD.
- SSM somente leitura `e9d5f808-800f-47f6-97c7-a47f8f3daaf9`: cinco sessões em `pg_stat_activity` no banco no instante da consulta. O `max_connections` produtivo observado antes do deploy era 79; o teto **estimado de configuração** da aplicação com sobreposição de gerações é 59, conforme [ADR-0020](../decisions/ADR-0020-database-capacity.md). A leitura pontual não comprova capacidade sob rajada real.
- CloudWatch RDS, amostras de cinco minutos: `FreeableMemory` média cerca de 139 MB antes do deploy e 131 MB na janela de 18:24 UTC, mínimo 122 MB nessa janela; CPU média cerca de 4%. `DatabaseConnections` teve zeros nas janelas anteriores e 0–4 na última, divergindo da leitura SQL; usar SQL e séries posteriores para avaliar conexões. Memória livre continua apertada e exige observação.
- SSM somente leitura `15a15088-6cc7-4c2c-98c8-02492dfcc5c1`: nos cinco minutos consultados, 34 linhas de logs de FastAPI, Django e proxy, sem linha `ERROR`, traceback ou HTTP 500/503. Isto é observação curta, não garantia de ausência futura de erros.

## Contratos e pendências

A API/web com controle de admissão, pool por PID/role, 503 seguro, ausência de fallback ORM no detalhe/integridade e logger técnico limitado estão ativos no runtime. MCP permanece no mesmo catálogo, schemas, scopes, auditoria e replays; sua saúde foi confirmada, mas não houve mutação MCP produtiva para testar resultado indeterminado. O código Flutter foi validado localmente, porém o workflow GitHub não distribui APK/IPA: usuários com app instalado ainda dependem de release mobile própria para a nova mensagem e retry explícito. O tratamento prévio do app continua consumindo o contrato HTTP sem logout automático, conforme aceite local.

Permanecem fora desta fatia: teste de rajada equivalente à topologia e latência de PRD, acompanhamento de memória/conexões/5xx em janela maior, retenção técnica de um dia, TLS produtivo, alertas/pipeline externo, eventual ajuste de capacidade RDS e atribuição da rajada original. O timeout de leitura direta da API quando uma conexão já estabelecida deixa de responder continua possível; escrita com resposta perdida permanece indeterminada e não recebe retry automático. A projeção pessoal terminal no detalhe web ainda usa ORM após resposta API bem-sucedida, protegida de erro de banco; migração dessa projeção é trabalho separado.

Rollout padrão concluído pelo Actions; rollback não executado. Se a saúde degradar, seguir o [runbook](../operations/db-resilience-rollout.md) e reavaliar orçamento de conexões antes de alterar workers ou réplicas.
