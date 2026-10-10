# Parecer humano em documento único — rollout produtivo de 2026-10-10

Workflow `WFLOW-20261010-EDITORIAL-DOCUMENT-001`, FEAT-EDITORIAL-001 / FEAT-MCP-001. O fechamento técnico da revisão 1.5 foi autorizado pelo operador; a homologação externa do Dot continua separada.

## GitHub e proteção dos dados

- [PR #148](https://github.com/wscardua/gotrendlabs/pull/148) integrada em `main` no merge `df3a691fa2ddf9bc098b9538d80fc3243c85547d`. [CI da PR](https://github.com/wscardua/gotrendlabs/actions/runs/38059400936) e [CI/build/deploy da main](https://github.com/wscardua/gotrendlabs/actions/runs/38060102537) concluídos com sucesso: 454 testes em cada execução, um skip de roles do ambiente CI. A branch local `feature/editorial-single-document-review` foi preservada.
- Snapshot manual RDS `gotrendlabs-pre-editorial-document-20261010` criado antes do merge e conferido `available`/100%. Nenhum restore ou exclusão foi executado.
- Inventário pré-merge somente leitura via SSM `0f00a32e-1295-40ea-afe3-3325ad8e87cb`: quatro mercados `draft`, oito opções, zero previsões, quatro fichas em `preparation`, 19 revisões. Tamanhos das fichas existentes: 7.067–10.832 caracteres, abaixo do limite de 60.000 do novo documento. Hashes de mercados, opções e previsões foram registrados para comparação, sem exportar conteúdo ou credenciais.

## Migração e verificação produtiva

- Actions/SSM concluiu o deploy; SSM `b47b7fce-0092-4cdd-aa4f-62509dc3446a` confirmou o host no SHA `df3a691`, migrations `editorial_integrations.0004_single_editorial_document` e `.0005_restore_published_editorial_decisions` aplicadas e serviços daemon, Django, FastAPI, MCP, proxy e thumbnail-worker em execução.
- Quatro fichas foram convertidas uma vez em documentos de 12.573–14.474 caracteres, cada um com apenas `policy_version`, `policy_hash` e `document` e as seções editoriais previstas. As 27 URLs das fontes estruturadas anteriores aparecem nos textos convertidos; nenhuma ficou ausente. As revisões passaram de 19 para 23, preservando snapshots anteriores. Os quatro mercados continuam `draft` e as quatro fichas continuam em `preparation`, exigindo novo parecer antes de publicar.
- Mercados (4), opções (8) e previsões (0) mantiveram contagens e SHA-256 idênticos aos do inventário anterior. Nenhum mercado foi criado, publicado, cancelado ou reaberto pelo rollout.
- Smoke HTTPS: `/api/health` e discovery MCP retornaram `200`; chamada MCP sem credencial retornou `401`; revisão Admin Ops sem sessão redirecionou para login (`302`) e API administrativa sem autenticação retornou `401`. O OpenAPI produtivo expõe `POST /admin/agent-editorial-reviews/{market_id}/assessment`, com `EditorialRecord` de três campos e `HumanEditorialAssessment` com `confirmed`; `/record` e `/decision` não aparecem.

## Limite do aceite

O teste autenticado de um parecer novo no Admin Ops produtivo não foi executado: exigiria sessão humana staff/MFA e mutação de um draft real. O fluxo de escrita, rollback e gate tem cobertura local/CI, e a conversão/schema/serviços foram conferidos em produção. Não há mercado publicado/terminal no inventário produtivo para observar a restauração histórica da migration 0005; esse caso foi coberto em DEV/testes. Dot e o piloto autenticado real permanecem pendentes; não inferir sua homologação a partir da disponibilidade MCP.
