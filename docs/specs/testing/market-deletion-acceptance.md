# Aceite: exclusão física de mercado pré-publicação

WFLOW-20261011-PHYSICAL-MARKET-DELETION, 2026-10-11. Substitui a abordagem lógica local anterior.

- Staff/MFA exclui draft preparation/in_review; GET é somente confirmação, POST exige CSRF/confirmação e ID/revisão exibidos.
- Remover fisicamente mercado, opções, ficha/parecer, todas as revisões e dependências de apresentação. Desvincular sugestões sem modificar status/crédito; conservar auditoria administrativa.
- Impedir exclusão de qualquer outro estado, publicado, previsão ou prova criptográfica; função SQL revalida restrições e grants não liberam DELETE geral em revisões.
- Falha de auditoria causa rollback integral, incluindo histórico, opções e vínculos.
- Confirmação antiga não exclui um novo mercado no mesmo slug. Publicação que aguardava lock recebe 404 se o mercado foi removido.
- MCP não lista/consulta/revisa/edita/submete mercado removido, inclusive em replays. Chaves/hash idempotentes preservam apenas marcador de exclusão. Nova criação com chave nova recebe outro ID e pode reutilizar slug.
- Aba antiga não gera thumbnail de mercado recriado no mesmo slug: ID original ou pedido legado sem ID retorna 409 antes de reservar job/cota. ID atual permite geração; ID inválido retorna 422; snapshot/hash não incluem ID.
- Thumbnail job perde vínculo, snapshot e usage, torna-se expired/market_deleted e segue contando nas cotas. Provider atrasado não grava candidata nem restaura job. Prune limpa mídia gerada órfã; arquivos manuais/compartilhados não são apagados indiscriminadamente.
- Desktop/celular, sem JavaScript, confirmação e voltar acessíveis, campos ID/revisão/CSRF presentes, sem overflow horizontal.

## Execução

Validação com venv existente gotrendlabs-ai-thumbnails/.venv (Python 3.11), bancos PostgreSQL isolados test_gtl_physical_delete_checks/test_gtl_delete_final_checks e providers simulados.

- 24 testes focados aprovados em 45.809s: exclusão, MCP e workers atrasados/cotas.
- Após restringir também a limpeza dos alertas na função SQL, 21 testes de exclusão aprovados em 58.995s, incluindo dependências e rollback.
- Confirmação real renderizada em Chrome, 1440×900 e 390×900, JavaScript desabilitado: aprovada e screenshots inspecionadas. Campos ID/revisão/CSRF, ações e ausência de overflow conferidos. Artefatos locais em .runtime/market-deletion-browser.
- Django check, makemigrations --check --dry-run, OpenAPI --check e git diff --check aprovados.
- Grants verificados no catálogo PostgreSQL: EXECUTE FastAPI permitido/Django negado e DELETE geral das revisões negado. Execução dos testes utiliza o proprietário do banco isolado; smoke autenticado com as roles produtivas deve acompanhar o rollout.
- Regressão compartilhada: 204 testes aprovados em 531.145s (exclusão, MCP/editorial/publicação, thumbnails, badges, taxonomia e ledger). A suíte iniciou antes do ajuste final da função SQL para alertas; os 21 testes específicos foram repetidos e aprovados após esse ajuste. Logs locais: /tmp/physical-deletion-focused.log, /tmp/physical-deletion-final.log e /tmp/physical-deletion-regression.log.

## Rollout

Aplicar editorial_integrations.0006 e admin_ops.0026 antes do runtime. Sem migration deleted_at. Não reverter a constraint de thumbnails para a versão anterior enquanto existirem recibos técnicos desvinculados; em rollback de código, manter as migrations aditivas. Remoções físicas não são reversíveis sem backup. Após pedido explícito de reinício, as duas migrations foram aplicadas no DEV local e PostgreSQL/proxy/API/web/MCP/executor reiniciados na worktree da feature. Seis mercados e mídia preservados, fila de geração vazia antes da parada; health/web/discovery HTTP200 e privilégio EXECUTE da role FastAPI conferidos. Não houve exclusão real, migration em PRD, inferência iniciada pela verificação ou deploy produtivo.

## Ajuste visual no DEV

Confirmação agrupada em painel Admin Ops com cabeçalho alinhado, status/slug legíveis, aviso de exclusão e rodapé de ações. Botões empilhados no celular. Seis testes web e aceite Chrome 1440×900/390×900 sem JavaScript aprovados após o ajuste; screenshots inspecionadas. CSS versionado e resposta HTTP200 no DEV conferidos. Nenhuma exclusão real nesta verificação.

Correção da revisão: PATCH e publish/cancel/lock de uma aba antiga, com ID anterior ou sem ID, devem retornar 409 após exclusão/recriação do slug. Mercado novo e revisão permanecem intactos; ID novo permite salvar/cancelar. A UI deve encaminhar o ID original submetido, mesmo quando o GET retorna outro ID. Diretório media versionado intacto e mídia DEV servida via configuração.

Evidência das correções pós-revisão: 88 testes/OK (236.790s), PostgreSQL isolado test_gtl_mcp_delete_fixes; OpenAPI, Django check, compilação e diff aprovados. DEV HTTP200 em API/web/mídia/discovery. Anúncio esperado específico reportado pelo usuário ainda não reproduzido: aguardando linha rejeitada; não houve flexibilização do validador.

## Correção de identidade da geração — 2026-10-11

Protegida geração de thumbnail contra aba antiga após exclusão/recriação do slug: expected_market_id validado sob lock antes de job/cotas; cliente legado sem ID rejeitado após exclusão anterior. Regra compartilhada com as demais mutações administrativas, contexto/hash de geração preservados, badges sem novo campo. Reconciliado texto CRLF com a atestação humana. 70 testes/OK (109.566s), browsers de mercados/badges aprovados com HTTP/provedores simulados; Django/Node/compilação/OpenAPI/diff aprovados. DEV serve schema e JS atualizados. MCP sem ajuste de ferramentas/schemas/permissões: geração é administrativa, validações automáticas de preparação preservadas e replays testados. Mobile não consome a rota administrativa. Sem migration adicional, geração paga, commit/push ou deploy.

## Estado consolidado para publicação

O diagnóstico editorial antes pendente foi resolvido pela consulta somente leitura do mercado 44 e reprodução CRLF. A aprovação humana posteriormente passou a usar atestação, conforme [aceite vigente](human-editorial-attestation-acceptance.md); relatos anteriores são históricos. Publicação e smoke produtivo seguem o [runbook](../../guides/prepublication-editorial-rollout.md).
