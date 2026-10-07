# Fechamento local e preparação de rollout — FEAT-MCP-001

Data: 2026-10-07. Workflow `WFLOW-20261007-MCP-CLOSEOUT-001`, vinculado ao workflow documental `WFLOW-20261007-MCP-EDITORIAL-SPEC`. Branch `feature/mcp-editorial`, base remota revalidada `9df08bc220c343e6ffefbed0ed3c2d80e072fd3e`. Checkout original, analytics e itens mobile preservados.

## Alterações finais

- FastAPI/Admin Ops/MCP, migrations/grants, OpenAPI, UI e ensaios da feature compõem uma entrega única. OAuth interativo e serviço continuam disponíveis; pesquisa/agenda ficam no executor externo.
- POST web com revisão editorial inválida retorna erro legível e conserva o formulário, sem chamar a mutação da API. Regressão cobre texto, zero e negativo.
- Metadados novos de parecer declaram corretamente o gate universal. Dados históricos de decisões não são reescritos; o enforcement vigente continua na FastAPI e considera versão/hash/política.
- Fontes documentais corrigidas: frontmatter de auth/logs, estado da arquitetura/ADR e runbook; aprovação humana universal substitui a decisão inicial de não criar gate global, conforme pedido posterior explícito do usuário.
- Deploy usa o override MCP, bloqueia rotas internas no proxy, valida/recarrega Caddy e aguarda saúde dos serviços. Após build/preflights, estabelece janela sem writers durante migrations/backfill; falha mantém writers parados para recuperação explícita. Configurador gera/preserva workload em dois arquivos locais 0600, sem herdar DB/pepper/TOTP no adaptador; primeira instalação desligada. Ativação/rollback explícitos preservam dados e segredo. Nenhuma integração, credencial de agente ou mercado é criada pelo bootstrap.
- CI passa a executar regressão em PR para `main`; deploy continua exclusivo da `main` após testes, com OIDC/SSM existentes. Mudança docs-only mantém o fluxo leve existente.

## Validação

**Regressão completa final: 367 testes/879,395 s/OK** em PostgreSQL isolado, após as correções, exit 0. Bases do fechamento e repetição focal destruídas, conferidas no catálogo PostgreSQL; DEV preservado. Dois cenários adicionais de janela/falha foram executados no pacote de sete testes de rollout (369 casos distintos ao todo; cinco testes de configuração se sobrepõem à suíte completa). A primeira execução (367 testes/873,059 s) encontrou expectativa obsoleta de sintaxe Caddy e fixture incompleta do novo teste de revisão inválida (três subcasos). Ambos corrigidos, sem retirar/quarentenar testes. Repetição focal: **19 testes/6,268 s/OK**, incluindo formulário/revisão inválida, proxy e metadados de aprovação universal; base PostgreSQL isolada destruída.

- **Sete testes de configuração/rollout passaram em 2,146 s** (cinco sobrepostos à regressão geral, dois adicionais de janela). Mocks de Docker/Git executam o script real: writers param durante migrations, reiniciam após sucesso e ficam parados em falha de migration. Não acessam Docker/produção/banco. Cinco testes do configurador cobrem: defaults/permissões/isolamento, habilitação e rollback sem rotação, divergência recusada sem sobrescrita, origem HTTPS/symlink, saída sem segredo.
- Imagem MCP Python 3.12 construída e executada sem rede, com usuário não privilegiado, filesystem somente leitura, tmpfs e capabilities removidas. Saúde desligada retornou OK; Django/psycopg/segredos humanos e credenciais de DB ausentes.
- Compose mesclado conferido sem resolver arquivos secretos. Caddy `adapt --validate` aprovado; ordem real das rotas bloqueia acesso interno antes da API pública. Bash, JavaScript, Ruff F, Django, OpenAPI, dependências e whitespace aprovados. YAML do workflow parseado, PR/main conferidos; execução real Actions depende de submissão.
- UI DEV previamente conferida com Chrome e cliente SDK real para todas as dez ferramentas, OAuth/serviço e logs persistidos. Ver [ensaio atual](dev-catalog-rehearsal-20261007.md), [regressão em instalação limpa](mcp-branch-review-followup-20261007.md) e [revisão universal](universal-editorial-20261007.md).

## Pré-checagem produtiva somente leitura

- Actions está configurado para deploy automático; EC2 em execução, Compose 5.1.4, serviços web/API/daemon/proxy ativos. Commit produtivo é a base desta branch; arquivos MCP ainda ausentes.
- RDS disponível e retenção de backup automático de um dia. Snapshot manual antes do merge ainda **não executado**; será criado e aguardado após autorização.
- Inventário produtivo: zero mercados/opções/previsões/definições/selos. Contas e demais dados devem ser preservados. Contagens/hashes sanitizados guardados fora do Git para comparação pós-deploy; nenhum conteúdo pessoal/segredo foi exportado.
- Nenhum deploy, alteração de configuração ou mutação de domínio em produção realizado neste fechamento local. Backups operacionais preexistentes não foram removidos.

## Resultado de aceite e limites

A matriz [por critério](mcp-editorial-results.md) continua aplicável com as extensões posteriores da [aceitação](mcp-editorial-acceptance.md). OAuth/serviço, permissões, drafts, parecer, gate universal/fechamento, cotas, idempotência, concorrência, logs e cliente MCP têm evidência local. MCP-O01 tem pacote operacional validado localmente, mas HTTPS/deploy público ainda pendentes. MCP-X02 (Dot real) permanece pendente: não comprovar conta, consentimento, escrita, recorrência, renovação ou revogação sem execução externa real. Configuração local e SDK não substituem essa homologação.

FEAT-MCP-001 permanece `parcial` até reunir evidências necessárias; o pedido de fechar a entrega não transforma pendência externa em validação. Sem testes que criem mercados reais em produção.

## Próxima ação

Apresentar título/descrição da PR ao usuário antes de submetê-la. Após autorização: enviar branch, abrir PR, aguardar CI, criar snapshot RDS, merge sem remover branch local, acompanhar Actions e ativar/smoke HTTPS conforme [runbook](../../guides/mcp-editorial-pilot.md). Registrar evidências produtivas e a homologação Dot quando efetivamente realizadas.
