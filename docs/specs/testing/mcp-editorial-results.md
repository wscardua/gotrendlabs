# FEAT-MCP-001 — evidências locais e homologação pendente

Estado vigente v1.4: revisão/fechamento universais conforme pedido posterior do usuário; [evidências](universal-editorial-20261007.md) e [fechamento/rollout preparado](mcp-closeout-20261007.md). A matriz abaixo preserva o ensaio inicial; suas menções a ausência de gate universal são históricas. Dot e HTTPS produtivo permanecem pendentes.

Atualização v1.3: [parecer humano em uma ação](mcp-single-review-20261007.md), 47 testes aprovados e UI DEV conferida. Conferência da ficha e decisão são atômicas; não há dois aceites humanos. Fluxo operacional v1.2 abaixo é histórico.

Atualização v1.2: [preparação/reenvio humano](mcp-human-review-20261007.md), 45 testes da suíte MCP e confirmação da UI DEV. Ficha pode ser retomada pelo operador sem executor; parecer e aprovação continuam separados.

Atualização v1.1: [validação de slug/gate/UI](mcp-review-gate-20261007.md), 46 casos distintos aprovados. Mercados de integração exigem aprovação humana atual na FastAPI; editor separa publish/save e Integrações segue Agentes IA. As evidências abaixo preservam o ensaio inicial v1.0; afirmações antigas de ausência de gate universal não dispensam o gate específico v1.1.

Data: 2026-10-07. Branch `feature/mcp-editorial`, worktree `gotrendlabs-mcp`, base remota `9df08bc`. Checkout original, alterações analytics e arquivos mobile preservados. Sem produção, merge ou deploy. Estado da feature: `parcial`, aguardando homologação externa.

## Ambiente e execução

Python 3.11 em `.venv` própria; PostgreSQL loopback isolado `gtl_mcp_pilot`, testes em `test_gtl_mcp_pilot` e `test_gtl_mcp_extra`. Somente credenciais locais de migração, sem provedores externos. FastAPI TestClient e servidores TCP efêmeros, SDK MCP 1.30.0 real e Authlib 1.6.12. Protocolo negociado no teste MCP: `2025-11-25`. Assinatura de publicação usa signer efêmero local, não KMS produtivo.

```sh
.venv/bin/python ops/scripts/test_mcp_local.py --db-admin-env ../gotrendlabs/.env.db-admin.local tests
.venv/bin/python ops/scripts/test_mcp_local.py --db-admin-env ../gotrendlabs/.env.db-admin.local --database gtl_mcp_extra
.venv/bin/python packages/contracts/export_openapi.py --check
```

- Regressão geral: **321 testes passaram** em 581,430 s, exit 0, incluindo os 30 MCP então existentes.
- Suíte MCP final: **33 testes passaram** em 94,928 s, exit 0 e base destruída ao final. São 29 testes de domínio/auth/UI/cliente e 4 do adaptador.
- Complemento final: parecer `rejected` e bloqueio de edição do agente passaram em teste focado (1 teste, 2,851 s, exit 0). Fixtures UI desativadas/revogadas no banco isolado, preservando histórico.
- Django check: sem problemas. `makemigrations --check --dry-run`: sem alterações. Snapshot OpenAPI atualizado; Ruff F, sintaxe JavaScript e `git diff --check` aprovados.
- Imagem Docker reconstruída; smoke sem rede, filesystem read-only, capabilities removidas: sem Django/psycopg ou env de DB/MFA/pepper. Compose mesclado validado sem resolver arquivos secretos. Fragmento Caddy validado dentro de servidor HTTP local com TLS automático desligado apenas para validação de sintaxe, sem iniciar listener. Isso não comprova HTTPS externo.
- Chromium real via Playwright, FastAPI e Django TCP loopback: login/MFA com fator efêmero local, criar/ativar, emitir segredo por AJAX, reload sem reapresentação/reemissão, pausar, desktop 1440 e móvel 390 sem overflow; draft fictício submetido/devolvido com nota humana. Capturas em `.runtime/mcp-ui/`, ignoradas pelo Git, nunca enquanto segredo aparecia. Templates escapam dados e mostram ausência de gate universal.

A primeira regressão detectou defaults SQL ausentes nos campos aditivos de auditoria e filtros vazios novos no mock existente; corrigidos mantendo inserts/consumidores anteriores. Concorrência revelou deadlock de FK com lock da integração: corrigido com `FOR NO KEY UPDATE`, mantendo serialização de revogação/commit. O teste SDK fecha explicitamente a conexão ORM de seu worker para permitir destruir a base isolada. Não interpretar falha de limpeza anterior como falha de produto.

## Resultado por critério

`Local aprovado` significa evidência executada neste checkout, sem alegação de validação Dot ou deploy. Métodos citados pertencem a `tests/test_mcp_editorial.py`; adaptador em `tests/test_mcp_adapter.py`.

| Critério | Resultado | Evidência e limite |
| --- | --- | --- |
| MCP-A01 | Local aprovado | `staff_superuser_mfa_equivalent_and_member_denied`; iguais capacidades, comum/sem MFA negados, CSRF web. |
| MCP-A02 | Local aprovado | `secret_once_rotation_origin_revoke_and_no_log_leak`, Django UI + Chromium; hash/no-store/rotação e GET sem segredo. |
| MCP-A03 | Local aprovado | `oauth_pkce_redirect_single_use_refresh_reuse`, `oauth_invalid_redirect_pkce_and_nonstaff_consent`, SDK OAuth real com discovery/DCR/PKCE/refresh. |
| MCP-A04 | Local aprovado | `credential_invalid_expired_absolute_grant_and_brute_force_limit`, troca de serviço e revogação de origem. |
| MCP-A05 | Local aprovado | `workload_without_delegation_audience_issuer_forgery`, ingestão sem auth/ator extra negada. |
| MCP-A06 | Local aprovado | `pause_resume_terminal_revoke_role_loss_and_transfer`, consentidor demovido após transferência, prazo absoluto e origem expirada. |
| MCP-A07 | Local aprovado | `scopes_ownership_private_record_and_no_admin_authority`, modelos strict e lista de dez ferramentas; nenhum proxy administrativo genérico. |
| MCP-D01 | Local aprovado | `invalid_taxonomy_extras_dates_options_rollback`, criação real, defaults binários e sem taxonomia automática. |
| MCP-D02 | Local aprovado | `create_retry_conflict_and_revoked_retry`; simulação de resposta perdida por replay após commit, mesmo ID/revisão, uma cota/evento. |
| MCP-D03 | Local aprovado | Mesmo teste; conflito de payload e revogação não contornada pelo replay. |
| MCP-D04 | Local aprovado | `human_and_agent_update_same_revision_only_one_wins`, editor antigo exige expected_revision para autoria técnica; nenhuma perda de conteúdo. |
| MCP-D05 | Local aprovado | `publication_and_agent_edit_are_serialized_signed_definition_preserved`, engine compartilhada/assinatura/verificação/checkpoint local. |
| MCP-D06 | Local aprovado | `revocation_wins_lock_before_mutation_and_commit_wins_before_pause`, ordem de lock determinística PostgreSQL. |
| MCP-E01 | Local aprovado | Submissão/parecer/devolução/approval e histórico; Chromium devolveu fixture com nota. Estados approved/rejected não reabrem edição de agente. |
| MCP-E02 | Local aprovado | `old_policy_and_inaccessible_source_preserve_pending`, `pending_evidence_cannot_approve_and_returns_reopen`; política antiga impede submit, relato de fonte inacessível impede aprovação. |
| MCP-E03 | Local aprovado | `submission_return_approval_human_edit_and_stale_versions`; parecer/evidências invalidados e versão incrementada. UI declara ausência de gate universal. |
| MCP-Q01 | Local aprovado | `persistent_quota_concurrent_last_unit_and_expired_lease`, contadores PostgreSQL, um commit, lease vencido recuperado, ativos limitados. Não é teste de carga distribuída. |
| MCP-Q02 | Local aprovado | `sao_paulo_quota_midnight_and_reduced_limit`, tentativas negadas/invalidpayload persistem, redução respeitada, replay sem novo consumo diário. |
| MCP-L01 | Local aprovado | Logs centralizados por estágio/integração/execução/tool/result; MCP real retorna isError mesmo transporte HTTP 200; ingestão correlacionada. |
| MCP-L02 | Local aprovado | `audit_failure_aborts_technical_failure_does_not`; falha técnica tolerada, evento transacional aborta quota/draft. |
| MCP-L03 | Local aprovado | Hash/no-store/redaction de headers/query/erros privados, injeção como dado, GET/HTML posterior sem segredo; spool não contém tokens. |
| MCP-L04 | Local aprovado | Adaptador AST/imagem sem DB; mock offline, spool limitado/durável e replay; `ingest_auth_dedup_identity_and_invalid_uuid`. Saturação/TTL/revogação podem perder log técnico, conforme runbook. |
| MCP-L05 | Local aprovado | Filtros por integração/tool/resultado e purge de SystemLog preservando ficha/revisões. |
| MCP-R01 | Local aprovado | `pagination_metrics_null_filters_and_no_backend_fetch`; cobertura parcial e indisponibilidade null, sem garantia de deduplicação semântica. |
| MCP-S01 | Local aprovado | `injected_text_stored_as_data_not_in_logs_and_no_url_fetch`, UI escape, schema rejeita javascript/credenciais em URL, sem download backend. |
| MCP-O01 | Local parcial | Container/grants/Compose/Caddy local aprovados. HTTPS/discovery no domínio externo ainda pendentes; nenhum deploy executado. |
| MCP-O02 | Regressão local | Suíte geral cobre login/MFA/Admin Ops/mercados/publicação/integridade/bots/daemon e contratos móveis existentes; conferir resultado final acima. Flutter não alterado: campos novos são opcionais e administrativos. |
| MCP-X01 | Local aprovado | Streamable HTTP ClientSession real com OAuth e serviço; discovery/DCR/PKCE/renovação, scopes atuais, schemas/leitura/escrita/erro. |
| MCP-X02 | Pendente externo | Sem conta/sessão Dot disponível nesta execução. Não validado OAuth/escrita/recorrência/renovação/revogação ou logs no Dot real. |

## Próxima etapa

Seguir [runbook do piloto](../../guides/mcp-editorial-pilot.md), usar [prompt de radar](../../guides/dot-editorial-radar.md), configurar domínio HTTPS em ambiente de homologação autorizado, integração pequena com MFA e scopes mínimos. Registrar cliente/conta/horário/IDs sanitizados para MCP-O01/MCP-X02. Manter `GTL_MCP_ENABLED=0` até o piloto autorizado. Rollback desliga API/adapter/handles e preserva dados; não desfaz migrations destrutivamente.

## Refinamento visual posterior

A pedido do usuário, a tela de integrações foi alinhada ao design existente de Config/Admin Ops: navegação única, cabeçalho/ações, seções e campos reutilizados, permissões legíveis, limites agrupados e estados pt-BR. Chrome real no DEV confirmou composição desktop, viewport estreito sem overflow e tema escuro; tema/viewport restaurados. O teste `test_django_ui_csrf_secret_once_review_and_escaped_content` passou novamente (1 teste, 3,206 s, exit 0), com Ruff F, sintaxe JavaScript e diff aprovados. Não houve mudança de domínio/OpenAPI.

### Refinamento de seleção do responsável (2026-10-07)

Três testes focados passaram em PostgreSQL isolado: elegibilidade humana/MFA/projeção mínima/paginação, UI CSRF/seleção/transferência e ciclo de revogação/perda de papel. Chrome DEV confirmou opção por nome selecionável sem salvar; formulário original preenchido preservado. Django check, Ruff, OpenAPI e whitespace aprovados. Sem alteração das pendências Dot/HTTPS.

### Cliente MCP real: todas as ferramentas (2026-10-07)

`test_real_streamable_mcp_client_tools_auth_and_draft` ampliado e executado via `ops/scripts/test_mcp_local.py` com banco PostgreSQL isolado `gtl_mcp_alltools` (base de teste destruída). Passou em 15,236 s; servidores API/MCP TCP efêmeros encerrados. Tokens OAuth e serviço gerados no teste, sem reutilizar segredo do usuário.

| Ferramenta | Serviço | OAuth |
|---|---|---|
| `get_editorial_policy` | passou; hash atual | passou; hash atual |
| `get_taxonomy` | passou | passou |
| `search_markets` | passou; draft encontrado | passou; draft encontrado |
| `get_market` | passou; conteúdo do draft | passou; conteúdo do draft |
| `get_editorial_signals` | passou; disponibilidade explícita | passou; disponibilidade explícita |
| `validate_market_draft` | passou; estruturalmente válido | passou; estruturalmente válido |
| `create_market_draft` | passou; replay sem duplicação | passou; replay sem duplicação |
| `update_market_draft` | passou; revisão incrementada | passou; revisão incrementada |
| `submit_draft_for_review` | passou; estado in_review | passou; estado in_review |
| `get_draft_review` | passou; estado in_review | passou; estado in_review |

26 chamadas `tools/call`: 22 positivas (incluindo replay) e quatro negações esperadas para edição após submissão e mercado inexistente, nos dois modos. Descoberta verifica catálogo exato de dez ferramentas. Dois drafts somente de fixture; nada criado no DEV ou produção. Esta execução valida o servidor com cliente SDK, sem declarar homologação LM Studio/Dot ou validade da credencial colada na conversa.

- Refinamento de descoberta editorial: teste real de todas as ferramentas repetido após mudança de descriptions/instructions, passou em 15,650 s. Confirma manual, checklist e modelo de ficha não vazios e 11 critérios, via get_editorial_policy. Metadata não garante escolha correta pelo LLM; falhas MLX/parser e uso incorreto de ferramentas observados no LM Studio permanecem pendências de homologação do executor.

## Radar agentic com pesquisa externa

[Ensaio de 07/10](mcp-radar-pilot-20261007.md): dez tools/17 chamadas, pesquisa pública real, um draft em revisão no banco isolado. Quatro testes passaram em 29,121 s. Corrigida omissão de campos nullable em detalhe, com regressão de privacidade. Sem homologação Dot/LM Studio ou mercado persistente.

## Radar persistente DEV autorizado

[Ensaio DEV de 07/10](mcp-radar-dev-20261007.md): draft #5 persistente, OAuth local pelo navegador, 21 chamadas/dez tools, três recusas esperadas e 63 logs. Mercados anteriores intactos; UI conferida. Correções de consentimento/título verificadas. Não substitui homologação externa.
