# Revisão de UX editorial — 2026-10-07

Workflow: WFLOW-20261007-MCP-REVIEW-UX-002; FEAT-MCP-001 permanece parcial por homologação externa.

## Diagnóstico e solução

Draft DEV #5 em revisão 9 conserva lacunas E07/E09/E10/E11. Marcar todos os critérios não resolve automaticamente essas lacunas; nenhuma aprovação foi feita pelo agente. Mensagem traduz motivos, campo orienta documentar resolução antes de limpar, decisão/marcações/texto são preservados em erro.

Fontes sugeridas no texto editável de evidência, sem seletores repetidos. Conversão exata de URLs cadastradas mantém os índices estruturados. Remover citação obrigatória é recusado; verificação humana não é inferida. Sugestões grandes permanecem como ajuda junto da evidência, sem exceder o limite de 2000 caracteres.

Mercados acompanha Admin Ops: título 34px, cabeçalho externo ao painel, tabela de seis colunas, destaque junto do título e tipo junto da categoria, métricas legíveis e scroll contido. Origem/estado/revisão MCP preservados.

## Validação

Oito testes passaram em 12,393 s: aprovação única, falha/rollback por lacunas mesmo com todas as marcações, remoção de fonte obrigatória, CSRF, conflitos e três decisões, retomada humana compatível, cinco estados/mercados legados/links, mapeamento exato de URLs e publicação/fuso. PostgreSQL temporário destruído; nenhum write/parecer/publicação em DEV.

Após ajustes finais, seis casos relevantes passaram novamente em 3,413 s. Ruff, Django check e diff check passaram. Chrome DEV conferido visualmente, ficha #5 revisão 9 observada; screenshots locais em .runtime/mcp-review-ux002. Desktop somente; homologação Dot/LM Studio e deploy pendentes. Sem mudança de schema/OpenAPI/migrations.

## Continuação — WFLOW-20261007-MCP-GAPS-RESOLUTION-001

Confirmação explícita de lacunas resolvidas no mesmo formulário: não exige apagar texto manualmente. Sem confirmação, o erro permanece; com confirmação e evidências válidas, gaps é registrado vazio via assessment. Fontes ausentes ainda bloqueiam e rollback preserva a ficha. Texto/checkbox/decisão mantidos após erro. Sete testes em 8,925 s passaram; Chrome DEV conferido no draft #5 revisão 9, sem alterar/aprovar/publicar. Screenshot .runtime/mcp-gaps-resolution/review.jpg. Sem mudança OpenAPI/migration; feature permanece parcial por homologação externa.

Caso ampliado confirma snapshot revisão 1 com lacunas originais após resolução e aprovação; passou em 3,492 s. Ruff/Django/diff aprovados.
