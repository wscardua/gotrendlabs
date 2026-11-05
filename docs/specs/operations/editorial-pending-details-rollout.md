# Publicação — detalhes de pendências editoriais

Data: 05/11/2026. FEAT-MCP-001 revisão 1.10 / WFLOW-20261105-EDITORIAL-PENDING-DETAILS. Estado: implantada e verificada em produção pela PR #186; os passos abaixo registram o roteiro executado. [Contrato](../contracts/agent-integrations.md#diagnóstico-de-pendências--05112026), [aceites](../testing/editorial-pending-details.md), [recibo produtivo](../testing/editorial-pending-production-closeout-20261105.md).

## Pré-flight e GitHub

- Preservar a branch/worktree local `fix/editorial-pending-details-20261105`; não modificar o mercado 62 nem outros mercados produtivos.
- Base `origin/main` bf11a0c. Preparar commit de fechamento documental, push da branch e apresentar ao usuário título/descrição da PR antes de criá-la, conforme solicitação explícita.
- Após aprovação, criar PR em português para main via GitHub MCP. Acompanhar checks do SHA final; corrigir falhas antes do merge. Não excluir a branch local.
- `ENABLE_PROD_DEPLOY=1`, `DEPLOY_BRANCH=main` e `AWS_REGION=us-east-1` confirmados por leitura de variáveis do repositório em 05/11. Alterações incluem `apps/` e `packages/`, portanto o workflow `.github/workflows/deploy.yml` executará CI completo e, após merge em main, o job de deploy por SSM. Confirmar novamente se o job for omitido.
- Pré-flight AWS em 05/11: instância produtiva `i-0fc304f1acb85daea` em estado `running` e agente SSM `Online` (DescribeInstances/DescribeInstanceInformation). Disponibilidade no momento do merge ainda deve ser confirmada pelo job de deploy.
- O deploy padrão recompila API e MCP com o schema compartilhado; nenhuma migration, flag, grant, novo scope, consentimento ou ajuste de dados é exigido por esta correção.

## Smoke pós-deploy

1. Confirmar SHA do checkout em produção, imagens API/MCP com `editorial_pending.py`, `editorial_schemas.py` e `server.py` da revisão integrada, serviços saudáveis, `/api/health` e metadata MCP 200.
2. Conferir `tools/list` autenticado: mesma ferramenta `validate_market_draft`, scope `drafts:write` e schema de saída contendo `pending`, `pending_details`, `assessment_scope` e `impact.approval=human_attestation_required`.
3. Consultar `get_editorial_policy` e confirmar versão/hash vigentes antes do smoke. Montar somente payloads sintéticos de validação, com taxonomia atual obtida por `get_taxonomy`, prazo futuro, agenda completa e `Anúncio esperado: não informado`; identificar explicitamente como teste estrutural, sem alegar pesquisa ou evidência editorial.
4. Chamar apenas `validate_market_draft`, que não cria nem modifica mercado: (a) documento com `## PENDÊNCIAS E CONCLUSÃO`, `Pendências para aprovação: nenhuma` e lista informativa deve retornar `pending=[]` quando não houver outro alerta; (b) documento com `Pendências humanas: ... (E10)` deve manter `unresolved_editorial_gaps`, detalhe E10, `approval=human_attestation_required`, criação/submissão permitidas pelo aviso; (c) documento com rótulo `Pendências:` e lista deve detalhar itens; evitar entrada grande em produção.
5. Confirmar que nenhuma mutação de mercado, aprovação ou publicação foi feita. Se o cliente apresentar schema em cache, atualizar catálogo e repetir apenas a validação de leitura.

## Falha e fechamento

Falha de CI impede merge. Falha do deploy ou smoke exige investigar Actions/SSM e API/MCP juntos antes de declarar a funcionalidade ativa; sem rollback de dados, pois não há migration. Se for necessária reversão de código, seguir PR auditável e registrar resultado.

Após o smoke, registrar PR, SHA de merge, Actions PR/main, SSM e resultados reais em recibo produtivo. Atualizar feature, contrato, README MCP, workflow, status, changelogs, integration map e known-gaps para distinguir conclusão desta revisão do status global parcial de FEAT-MCP-001. O recibo posterior pode ser docs-only com CI leve; preservar a branch local.
