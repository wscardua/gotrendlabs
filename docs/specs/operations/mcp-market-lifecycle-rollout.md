# Rollout — lifecycle e exclusão MCP

## Estado e escopo

Implantação concluída em 02/11/2026, branch feature/mcp-resolve-cancel-markets. Base origin/main b6a0649. WFLOW-20261102-MCP-LIFECYCLE-CLOSEOUT. Implementação no commit local c778b88, revisão versionada sem findings identificáveis e suíte completa aprovada. A descrição foi aprovada pelo usuário antes da PR #182; publicação, merge, Actions e smoke foram concluídos. Preservar a branch/worktree local após merge.

Três novas tools: resolve_market, cancel_market e delete_market_draft. Novos scopes markets:resolve, markets:cancel e drafts:delete. Catálogo 21; metadata nove scopes. Recuperação de sessão web revogada no consentimento preserva OAuth e exige login/MFA novamente. Sem release mobile, nova variável, segredo ou flag. Não distribuir a senha temporária DEV nem transportar sua alteração para produção.

## Fechamento produtivo verificado

PR #182 integrada; Actions main 41464155882 e SSM deploy/smoke Success/0. Runtime 0ffa4a0 com código/hashes e catálogo 21/nove scopes conferidos. Migration 0007 e ACL mínima corretas. Não houve concessão automática, mutação privilegiada de mercado, nova flag/segredo ou release Flutter. [Recibo vigente](../testing/mcp-market-lifecycle-production-closeout-20261102.md). As instruções abaixo registram o roteiro executado e servem a futuras operações; não representam etapas de deploy ainda pendentes desta fatia.

## Antes do merge

1. Incluir módulos, migration e testes novos no commit; conferir diff versionado contra origin/main e atualizar OpenAPI/estado. Não incluir .env, .venv, .runtime, segredos, dumps ou artefatos de teste.
2. Executar checks locais e suíte isolada. CI deve testar Python 3.12/PostgreSQL 16, imagem principal, imagem MCP, OpenAPI e testes JS/Python. Build local de imagem não substitui CI.
3. Mostrar título/descrição em português e obter aprovação. Após aprovação, enviar branch, criar PR pelo GitHub MCP e acompanhar checks do último SHA. Corrigir falhas antes de merge; não usar bypass.
4. Fazer merge pelo GitHub MCP, mantendo a branch local. Acompanhar GoTrendLabs CI and Deploy do merge e os jobs de build/test/deploy, não apenas o check da PR. O MCP GitHub não expõe todas as operações de Actions; CLI/API de GitHub pode complementar monitoramento.

## Deploy e pré-requisitos

ENABLE_PROD_DEPLOY=1 e configuração AWS/SSM existentes devem estar válidos. O deploy padrão já usa compose principal + MCP, faz build, para writers, aplica boundary/migrations, confere credenciais, coleta estáticos e inicia serviços. Não criar um caminho paralelo de deploy. A migration editorial_integrations.0007 depende de markets.0038 (já implantada na base) e cria recibos MCP, unique/check e trigger append-only.

A nova tabela gotrendlabs_agent_market_requests deve permitir FastAPI SELECT/INSERT e sequência USAGE/SELECT; sem UPDATE/DELETE/UPDATE da sequência. Django recebe somente SELECT, sem acesso à sequência. Conferir roles efetivas/padrão e default ACL, não somente proprietário da migration. Provas, ledger e recibos históricos permanecem intactos. Se a migration falhar, diagnosticar antes de reiniciar writers; não apagar recibos ou remover guards para liberar deploy.

## Smoke pós-deploy

- Registrar PR, SHA de merge, URL/status do Actions e identificador/resultado do SSM. Confirmar o SHA no servidor/imagens e que proxy/Django/FastAPI/daemon/MCP estão saudáveis.
- Conferir migration 0007, tabela/constraints/trigger e ACLs efetivas, incluindo a função de exclusão prepublication (FastAPI EXECUTE, Django negado, sem DELETE geral em revisões).
- Consultar HTTP público: home/health API, discovery OAuth e metadata MCP. Metadata deve anunciar os nove scopes. Inspecionar o runtime MCP para 21 ferramentas e schemas compartilhados e a FastAPI para as três rotas; publicar a ferramenta não concede acesso à integração.
- Conferir que pedidos de mutação sem delegação são recusados. Usar payloads válidos de smoke com IDs inexistentes e sem autenticação, nunca resolver/cancelar/excluir mercado produtivo para testar.
- Não emitir novos grants, tokens privilegiados ou conceder scopes por inferência. As integrações existentes conservam permissões. Se for necessária concessão operacional, identificar a integração e obter instrução explícita para os scopes desejados, ou usar a UI staff/MFA e novo consentimento do operador. O código fica ativo após o deploy, com capacidades por grant.
- Verificação ponta a ponta de liquidação/refund/delete/conflitos permanece no PostgreSQL isolado. Um teste com efeitos reais em produção exige mercado controlado e autorização específica.
- Conferir login/consentimento sem bypass de MFA. Smoke técnico de sessão inválida não homologa o navegador/LM Studio do usuário. Preservar esse limite na entrega.

## Encerramento e recuperação

Após implantação real, registrar recibo em testing e atualizar workflow, implementation-status, changelogs, known-gaps, integration-map, spec e README. Evidência que só existe após deploy pode ser publicada por PR documental posterior; o workflow de docs-only evita novo deploy desnecessário. Não marcar homologação produtiva concluída antes dos checks/smoke reais.

Para bloquear novas operações, remover scopes ou pausar/revogar a integração pelos mecanismos existentes; efeitos confirmados não são desfeitos. Nunca executar down migration destrutiva dos recibos ou restaurar provas assinadas por edição. Rollback de runtime deve preservar schema/recibos e não autoriza undo/cancel automático. Nenhuma ação deve remover a branch local.
