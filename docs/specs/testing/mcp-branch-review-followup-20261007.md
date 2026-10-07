# Correções do review da branch MCP — 2026-10-07

Workflow: WFLOW-20261007-BRANCH-REVIEW-FOLLOWUP-001. Recomendações 1/2 aprovadas pelo usuário. Branch feature/mcp-editorial, base origin/main 9df08bc. Sem commit, merge ou deploy; banco DEV preservado.

## Conjunto versionado

Módulos FastAPI/MCP, app Django/editorial, templates, navegação, migrations, grants, contratos, documentação, exemplos de ambiente sem segredos, configuração de deploy e testes da feature adicionados ao índice Git. Arquivos de ambiente real, runtime, backup, media, ambiente virtual e mudanças mobile do checkout original não incluídos.

Snapshot do índice exportado com git archive para diretório temporário sem .env ou arquivos runtime. Criado ambiente virtual Python 3.11 independente e instalado requirements.txt do snapshot, sem reutilizar site-packages local. Instalação e pip check aprovados. Django check e OpenAPI --check aprovados nesse ambiente. Autodetecção de migrations com SQLite somente em memória: No changes detected; execução efetiva das migrations e teste de grants são feitos na suíte PostgreSQL isolada.

## Teste do Admin Ops

Asserção deixou de exigir versão literal do asset; verifica script js/gotrendlabs.js, query de cache opcional e atributo defer na resposta HTML. Percurso existente test_admin_ops_requires_staff_and_renders_api_data passou completo no ambiente original (1 teste, 3,709 s), incluindo as etapas posteriores ao ponto onde falhava.

## Validação do snapshot

Suíte final: **74 testes, 172,744 s, OK**, cobrindo MCP domínio/auth, adaptador/SDK real, consentimento, publicação/fuso, navegação, validade de credencial e quatro regressões API/Admin Ops. Migrations aplicadas ao PostgreSQL vazio do runner, incluindo grants e auditoria; teste de permissões das roles executado sem skip. Banco PostgreSQL isolado test_gtl_mcp_clean_followup destruído ao final; sem alterações ao gotrendlabs DEV. Ruff F do teste alterado, sintaxe JavaScript e diff do índice aprovados.

## Limites

Dot/HTTPS externo e deploy permanecem pendentes; FEAT-MCP-001 parcial. Item 3 do review (ValueError em editorial_revision inválida no POST web) permanece identificado, fora das recomendações 1/2 selecionadas nesta execução. Os arquivos estão preparados no índice Git, sem criar commit.
