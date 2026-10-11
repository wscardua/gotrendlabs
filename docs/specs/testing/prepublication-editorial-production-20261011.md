# Recibo produtivo: exclusão pré-publicação e parecer humano

Data: 2026-10-11. WFLOW-20261011-CLOSE-PREPUBLICATION-EDITORIAL. Entrega técnica concluída; homologação humana final do painel autenticado permanece com o operador.

## GitHub e implantação

- [PR #156](https://github.com/wscardua/gotrendlabs/pull/156), merge `32a45131920af6f1427f484531b26b249cb5ef76`, conferido no host de PRD.
- [CI final da PR](https://github.com/wscardua/gotrendlabs/actions/runs/38149320217): build/OpenAPI aprovados, 495 testes/2 skips em 483.943s.
- [Main e deploy](https://github.com/wscardua/gotrendlabs/actions/runs/38150080993): build/OpenAPI aprovados, 495 testes/2 skips em 476.876s; test/deploy Success.
- Primeiro CI 38148616230 identificou uma expectativa antiga do mock de publicação, sem `expected_market_id`. Fixture/asserção corrigidas no commit `9458a72`; os 16 testes de interface passaram localmente e o CI completo foi repetido com sucesso.
- SSM do Actions `c7d84727-16a3-4495-8056-5d20048b350d`: Success. API, Django, MCP, daemon e thumbnail-worker recriados; proxy validado/recarregado, MCP healthy.
- Snapshot RDS `gotrendlabs-before-pr156-20261011` confirmado `available` antes do merge/migrations. Configurações/mídia existentes preservadas; sem flag nova para ativação.

## Banco e permissões reais

`editorial_integrations.0006_prepublication_deletion` e `admin_ops.0026_deleted_market_thumbnail_receipts` aplicadas.

Função `public.delete_prepublication_editorial(bigint,integer)`: owner `gotrendlabsadmin`, SECURITY DEFINER, `search_path=pg_catalog`. EXECUTE FastAPI permitido; Django/PUBLIC negados. FastAPI não recebeu DELETE geral sobre revisões editoriais. Além do catálogo, execução efetiva no container Django recebeu `42501` como esperado.

SSM `a6fe7bdf-7f1e-4389-a847-7db587f546ca`: smoke com credencial real `gotrendlabs_fastapi`, fixtures exclusivas, na mesma transação revertida. Confirmou exclusão em preparation/in_review, remoção de revisões, auditoria, rejeição de ID antigo (409), aprovação humana com documento sem formato obrigatório/política antiga/anúncio inválido e gate de publicação atual. Rollback verificado: nenhuma fixture persistiu. Não foram usados mercados reais para exclusão ou aprovação. Os IDs de sequência consumidos pelas fixtures não são revertidos, conforme PostgreSQL.

SSM `d747e999-b9f2-434f-adfd-bcd557302b22`: negação efetiva da função para role `gotrendlabs_django`, Success/42501.

## HTTP e MCP

- Site `/`, `/api/health` e discovery `/.well-known/oauth-protected-resource/mcp`: HTTP200.
- GET `/api/admin/markets` e DELETE administrativo sem autenticação: HTTP401.
- JS público contém envio do ID original do mercado e foi servido com a versão nova.
- Chamada real `get_editorial_policy` via MCP produtivo confirma política v1.2/hash preservada, checklist v1.3 e modelo v1.6 com hashes abaixo. Nenhuma ferramenta de exclusão ou aprovação adicionada; preparação de agentes conserva validadores. Replays/recursos removidos cobertos nas suítes locais/CI; não foram feitas escritas MCP reais como smoke.

| Artefato | SHA-256 |
| --- | --- |
| Política aprovada | `9d9b13bf75268cb236120e9aa3f3b46f512fd7b20f965514654d947cd2f40fa1` |
| Checklist | `b34fd86b508853136699933da2de19633d96888209b71adc060206082579a22c` |
| Modelo | `7067cb731d53a61c1d89259949bfb7c52c79ff8e103714679575564c6d711f7d` |

Mobile não consome as rotas administrativas alteradas. Não houve inferência paga iniciada nesta validação. Branch local/remota `feature/delete-draft-review-markets` preservada.

## Limite da verificação

Smoke de domínio com role real e rollback não substitui o teste humano do formulário com sessão staff/MFA. Esse teste final permanece com o operador. A entrega técnica deste escopo está concluída; futuras evoluções das features amplas não são declaradas concluídas por este recibo. [Runbook](../../guides/prepublication-editorial-rollout.md).
