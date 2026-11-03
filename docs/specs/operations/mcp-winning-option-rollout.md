# Publicação — winning_option_id no get_market

Data: 03/11/2026. FEAT-MCP-001 v1.9 / WFLOW-20261103-MCP-WINNING-OPTION. Estado: preparação local, PR aguardando aprovação do usuário. [Contrato](../contracts/agent-integrations.md), [evidências locais](../testing/mcp-winning-option-results.md).

## Pré-condições e fluxo GitHub

- Preservar branch/worktree local `fix/mcp-get-market-winning-option`.
- Commit e review versionado comparados com origin/main ca67e9f. Apresentar título e descrição da PR em português e obter a aprovação solicitada antes de criá-la.
- Push da branch, criação da PR para main via GitHub MCP, acompanhar checks do último SHA e tratar falhas antes de integrar.
- Merge somente após CI aprovado; acompanhar o workflow de main correspondente ao merge até testes/build/deploy concluídos. ENABLE_PROD_DEPLOY=1 confirmado na preparação; conferir novamente se o job de deploy for omitido.
- O pipeline padrão `.github/workflows/deploy.yml` usa SSM e `ops/deploy/production/deploy.sh`, que recompila a aplicação e o MCP coordenadamente. Não exige migration, nova flag, scope, grant ou novo consentimento para o campo em catalog:read.

## Smoke pós-deploy

1. Confirmar SHA do checkout e dos arquivos de serviço/schema/adapter nas imagens, serviços saudáveis e saúde pública de API/MCP/discovery.
2. Conferir tools/list no runtime: get_market continua read-only/catalog:read; winning_option_id obrigatório e anyOf integer/null. Catálogo mantém 21 ferramentas e nove scopes.
3. Fazer get_market autenticado em mercado existente com resultado, preferencialmente sealed. Comparar winning_option_id com o valor persistido em transação READ ONLY e com options[].id; conferir status e structuredContent. Usar conexão/grant já autorizado sem expor token ou ficha editorial em logs.
4. Se houver mercado visível sem resultado, confirmar a presença de winning_option_id:null. Não criar nem resolver/cancelar/excluir mercados reais para smoke. Se faltar exemplo acessível, registrar o limite e usar a evidência local desse caso.
5. Confirmar que não há nova concessão/permissão nem alteração de hashes/provas pela leitura. Atualizar catálogo/cache do cliente se ainda anunciar schema anterior.

## Recuperação e recibo

Falha de CI impede merge. Falha de deploy exige examinar Actions/SSM e corrigir a causa antes de afirmar disponibilidade; manter API e MCP no mesmo contrato compartilhado. Em caso de necessidade de reversão de código, seguir o fluxo padrão GitHub e registrar reversão lógica; esta alteração não tem transformação de dados para desfazer.

Após sucesso, registrar PR, commits/merge, Actions da PR/main, resultado SSM, schema/payload/valor persistido e limites em recibo produtivo. Reconciliar feature, contrato, README, implementação, changelogs, integration map e workflow. Documento posterior estritamente Markdown deve seguir CI docs-only; preservar branch local.
