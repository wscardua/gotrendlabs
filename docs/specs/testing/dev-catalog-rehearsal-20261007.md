# Ensaio do catálogo DEV — criação humana e MCP

Data: 2026-10-07. Workflow: WFLOW-20261007-DEV-CATALOG-REHEARSAL-001, vinculado à revisão editorial universal e WFLOW-20261007-MCP-EDITORIAL-SPEC. Branch `feature/mcp-editorial`, worktree `gotrendlabs-mcp`. Sem produção, merge ou deploy.

## Preparação e preservação

Pedido explícito do operador: remover mercados DEV e recriar por preenchimento humano e agente MCP. Banco usado nos percursos: PostgreSQL **gotrendlabs local**, não um banco temporário. Suítes automatizadas destrutivas continuam usando PostgreSQL isolado.

Backup integral custom PostgreSQL antes da limpeza: `.runtime/dev-rehearsal/before-reset.dump`, 947622 bytes, permissão 0600, ignorado pelo Git; SHA256 `ea33c69e379753b568f7d07c83afb12a5a7b291eeec2eac679d90b245c884ed1`. TOC verificado por pg_restore; restauração integral não foi ensaiada. Contém dados privados e deve permanecer local.

Removidos mercados 1, 2, 3 e 5, nove opções, três previsões e dependências de ensaio, incluindo provas antigas e efeitos associados em wallet/reputação. Projeções dos dois usuários afetados recalculadas. Contas, taxonomia, configurações, integração e chaves de assinatura preservadas por comparação antes/depois; logs técnicos e administrativos mantidos. Limpeza transacional específica DEV; sete guards de integridade restaurados na transação. Evento `dev.catalog.reset` registra a operação. Não é um procedimento autorizado para produção.

## Percursos reais no DEV

| Percurso | Evidência final |
|---|---|
| Humano, mercado **6** | Formulário Chrome → salvar draft → parecer humano na UI → publicar versão aprovada → fechamento manual → resolução SIM pela UI. Estado **resolved**, parecer aprovado revisão 4. |
| Agente, mercado **7** | Cliente MCP SDK Streamable HTTP → consultar política/taxonomia/catálogo/sinais → validar proposta → criar → editar → submeter → parecer humano na UI → publicar. Estado **locked**, parecer aprovado revisão 5. |
| Fechamento humano | Prazo persistido 09/10/2026 18:00 UTC; fechamento manual antecipado com justificativa do ensaio. Resolução persistida 07/10/2026 20:23 UTC, igual ao campo escolhido. Sem participantes. |
| Fechamento automático | Prazo 07/10/2026 **20:24:42 UTC**; produção do serviço `close_due_auto_markets` executada no relógio real. Fechou uma vez; repetição retornou vazia. Uma previsão humana de **1 crédito educativo** permitiu percorrer fechamento, pois mercado sem humano é cancelado pela regra existente. |
| Integridade | `audit_integrity_records`: available=true, ledger_status=verified, markets_scanned=2, issues_detected=0, alerts_created=0, scan_failures=0. Ambos endpoints: overall_valid=true, verification_status=verified, errors=[]. Compromisso da previsão também válido. |
| Interface | Catálogo contém só os dois novos cenários; ambos mostram parecer e link direto; apenas #7 mostra origem agente MCP. Fila de resolução mostra #6 resolvido e #7 fechado, com ação Resolver. Nova criação oferece Salvar rascunho. |

Os títulos começam por `[DEV]`. São casos **sintéticos de validação do software**, não sugestões de mercados reais nem pesquisa econômica. A evidência editorial documenta explicitamente o ensaio; não demonstra qualidade de pesquisa de um LLM nem aprovação editorial real de evento externo. O parecer humano foi simulado pelo operador automatizado através da UI, sem gravar aprovação diretamente no banco.

## MCP, autenticação e casos negativos

OAuth local com DCR, authorization code + PKCE S256, consentimento autenticado staff/MFA via endpoints e token com audience MCP. Cliente MCP SDK real executou todas as dez tools: `get_editorial_policy`, `get_taxonomy`, `search_markets`, `get_editorial_signals`, `get_market`, `validate_market_draft`, `create_market_draft`, `update_market_draft`, `submit_draft_for_review`, `get_draft_review`. Grant temporário revogado ao terminar. Não foi uma homologação Dot nem uma interação OAuth do usuário no navegador.

Credencial temporária emitida pela FastAPI para integração existente; client_credentials e cliente MCP real listaram dez tools e consultaram parecer aprovado. Credencial revogada; nova emissão de token retornou 401. Segredos somente em memória; credencial original do operador preservada.

- Replay da criação retornou o mesmo mercado; chave reutilizada com payload diferente recusada.
- Revisão antiga recusada; edição após submissão recusada; ficha privada do mercado humano inacessível ao agente.
- Publicação antes de aprovação retornou **409** para ambos os mercados.
- Aprovação sem atestação dos critérios/fontes retornou **422**, sem alterar revisão.
- Tests isolados complementam concorrência, cotas persistentes, roles/grants, audiência/delegação, OAuth/revogação e invariantes. Não esgotamos artificialmente as cotas DEV da integração.

## Desvios reproduzidos e corrigidos

1. Data/hora de fechamento era interpretada no fuso padrão Django, mesmo com UTC selecionado (18:00 virava 21:00 UTC). Campos de fechamento e resolução agora interpretam a hora no fuso escolhido. Horários inexistentes/ambíguos por DST são recusados explicitamente. Formulário e payload testados com UTC, São Paulo, Nova York e Londres.
2. Editor truncava segundos ao abrir um prazo vindo do MCP. Inicialização preserva segundos/microssegundos e input permite essa precisão, evitando mudança silenciosa de definição.
3. Notas internas persistidas não voltavam na projeção administrativa. FastAPI agora devolve `admin_notes` no contexto administrativo; resposta pública contém string vazia e MCP não expõe o campo. OpenAPI atualizado.
4. Criação oferecia publicação antes de existir parecer. Nova UI salva draft; POST legado de criar/publicar salva uma única vez e redireciona à revisão, sem tentar publicar e induzir repetição do cadastro.
5. Mercado já fechado mostrava botão desabilitado “Fechar após publicar”. Placeholder restrito ao draft; estados finais não recebem essa instrução.

## Testes e evidências

- Suíte ampla: **64 testes, 182,560 s, OK**: test_mcp_publication_ui, test_mcp_editorial, test_mcp_adapter, test_mcp_consent_query e dois percursos de API administrativa em test_web_smoke.
- Após ajustes finais de fuso/resolução/precisão: **17 testes, 4,677 s, OK**, test_mcp_publication_ui + test_admin_market_edit_preserves_collected_resolution_and_graph_data. Conjunto sobreposto à suíte ampla; não somar como testes únicos.
- PostgreSQL de cada suíte destruído pelo runner. DEV permaneceu com os dois cenários.
- OpenAPI `--check`, Django check, Ruff F nos arquivos focais e `git diff --check` aprovados.
- Logs persistidos na janela do ensaio: 17 started, 26 completed, 8 failed, todos com request_id. API e adaptador registram etapas distintas; falhas incluem as recusas intencionais, não são oito incidentes independentes. Eventos administrativos registram criar/editar/submeter, aprovação de ambos, publicar/fechar/resolver e emissão/revogação da credencial.
- Chrome confirmou log #9462 (`get_draft_review`, stage=mcp) com integration_id, credential_id, execution_id e request_id. Filtro de integração funciona no painel `/admin-ops/logs/`.
- Evidências locais ignoradas: `.runtime/dev-rehearsal/` contém relatórios JSON de limpeza, tools, gates, autenticação, fechamento real, auditoria e screenshots `catalog.png`, `resolution.png`, `log.png`. Não copiar backup/sessões/segredos para Git.

## Estado para continuação e limites

- Catálogo: http://localhost:8000/admin-ops/markets/
- Ficha humana: http://localhost:8000/admin-ops/agent-reviews/6/
- Ficha MCP: http://localhost:8000/admin-ops/agent-reviews/7/
- Resolver cenário MCP: http://localhost:8000/admin-ops/resolution/dev-o-ensaio-mcp-concluira-o-fechamento-automatico-com-integridade-valida/resolve/

Uma unidade educativa permanece comprometida no #7 até resolução/cancelamento. #6 aguarda janela normal de selagem; relógio não foi adiantado para forçar selo. Fechamento/auditoria usaram os serviços reais do daemon, sem disparar o ciclo inteiro de emails/push/LLM; instalação persistente e operação por 24 horas não são comprovadas por este ensaio. OAuth em Dot, HTTPS externo, recorrência do executor e deploy continuam pendentes. FEAT-MCP-001 permanece parcial.
