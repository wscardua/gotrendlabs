# Review de impacto — winning_option_id no get_market

Data: 03/11/2026. Skill gotrendlabs-review-branch-impact. Revisão somente de leitura do commit de implementação; registro produzido depois de concluir a revisão.

## Resumo

- Base preferencial e merge-base: origin/main ca67e9f00e29b154573afcb35a8e8f6e6014547c.
- Intervalo: ca67e9f...e01c9ac (commit de implementação e preparação local).
- Escopo: diff completo dos 19 arquivos listados abaixo, seguindo projeção, rota FastAPI, adapter/schema e consumidores diretos. Sem auditoria geral ou código fora do escopo.
- Superfícies: backend/API editorial, MCP, schema/OpenAPI, testes, documentação e memória operacional. Sem banco/migration, alteração web/Admin Ops, Flutter, infraestrutura ou jobs.
- Mobile não impactado: MarketsRepository consulta `/markets/{slug}` e endpoints públicos de previsões/integridade; não consome `/integrations/editorial/markets/{market_id}` ou MarketProjection. MarketResponse público não mudou.
- Risco geral: baixo. Valor já persistido, projetado sob o lock existente, schema obrigatório nullable e adapter sem SQL.

Arquivos revisados:

- README.md
- apps/api/backend_api/editorial_schemas.py
- apps/api/backend_api/editorial_service.py
- apps/mcp/README.md
- apps/mcp/server.py
- docs/specs/architecture/backend-api.md
- docs/specs/contracts/agent-integrations.md
- docs/specs/features/mcp-editorial-agents.md
- docs/specs/operations/mcp-winning-option-rollout.md
- docs/specs/state/change-log-specs.md
- docs/specs/state/feature-changelog.md
- docs/specs/state/implementation-status.md
- docs/specs/state/integration-map.md
- docs/specs/state/workflow-runs.md
- docs/specs/testing/mcp-editorial-acceptance.md
- docs/specs/testing/mcp-winning-option-results.md
- packages/contracts/openapi/gotrendlabs-api.json
- tests/test_mcp_editorial.py
- tests/test_mcp_market_actions.py

## Findings

Nenhum problema identificável no diff.

A projeção sempre insere winning_option_id, inclusive None, e o schema sem default exige o campo; exclude_unset não o elimina. Campo operacional é acrescentado somente em market_projection, mantendo get_market interno e snapshots editoriais intactos. Consulta usa parâmetros, lock compartilhado e transação existentes. Rota preserva catalog:read, identidade da integração e omissão da ficha alheia. Não há nova entrada, mutação, permissão ou alteração de recibo/replay. OpenAPI corresponde ao schema compartilhado, coberto no SDK real.

## Pontos a validar

- Imagem API e MCP no mesmo SHA após Actions/deploy, schema anunciado em tools/list e payload autenticado do servidor implantado: evidência atual é local; conferir conforme roteiro de rollout.
- Cache do cliente conectado: atualizar catálogo apenas se ainda anunciar contrato anterior após verificar servidor.

## Riscos residuais e cobertura

Testes locais da implementação: 142 cenários na regressão, 140 aprovados/um skip/uma expectativa de contagem de fixtures corrigida; reexecução do cenário SDK aprovada. Resultado combinado 141 aprovados/um skip. A role dedicada ausente no cluster impede somente o check de grants nomeados; ACL com roles temporárias passou. Cobertura inclui null/campo ausente, resolved/sealed por lifecycle, correspondência às opções, SDK serviço/OAuth, scopes, ficha alheia e snapshots. [Evidências completas](mcp-winning-option-results.md).

Nesta revisão: diff completo, consumidores e diff --check conferidos; na preparação também OpenAPI --check e Ruff F aprovados. Não houve mudança de código após os testes e nenhuma repetição ampla foi necessária. CI completo da PR/main e smoke produtivo ainda pendentes; sem lacuna funcional específica identificada. Não houve teste de carga ou injeção de falha em produção para este campo de leitura.
