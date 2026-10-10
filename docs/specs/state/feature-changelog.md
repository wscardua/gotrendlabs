# Feature Changelog

## 2026-10-10 — bloqueios objetivos do documento editorial

FEAT-MCP-001/FEAT-EDITORIAL-001: aprovação documental exige declaração explícita de ausência de pendências; horário de anúncio conhecido é comparado ao fechamento pela FastAPI. Migration 0005 restaura o parecer histórico de mercados publicados/terminais convertidos, enquanto drafts e agendados aguardam novo parecer. Mantidos um textarea e um check no Admin Ops.

## 2026-10-10 — documento único no parecer editorial

FEAT-MCP-001 v1.5: preparação e parecer usam exclusivamente documento textual versionado. Admin Ops apresenta um campo de texto, uma confirmação humana para aprovar e decisão; MCP/FastAPI rejeitam campos estruturados anteriores e as rotas separadas `/record` e `/decision` foram removidas. A migration 0004 converte registros existentes uma vez e exige nova revisão, preservando histórico. Gate universal de publicação permanece vinculado à aprovação humana da versão atual.


- 2026-10-07: resposta DCR omite metadados opcionais ausentes; teste com callback HTTPS ChatGPT e `ui_locales`. PR #140 implantada/Actions 37710313470 Success; 51 testes locais e CI PR/main 372 testes/OK (um skip por roles CI ausentes), smoke HTTPS DCR aprovado. Homologação ChatGPT pendente; WFLOW-20261007-MCP-CHATGPT-DCR-001.

- 2026-10-07: WFLOW-20261007-MCP-CODEX-OAUTH-001 corrige DCR Codex (extra application_type) e issuer exato no discovery MCP; 50 testes locais/OK e CI PR/main 371 testes/OK (um skip por roles CI ausentes); implantada pela PR #138/Actions 37699380266, registro CLI real conferido em produção. Sem migrations/permissões novas; homologação humana permanece pendente.

## 2026-10-07 — MCP editorial implantado e habilitado em produção

- PR #136/merge b36ea44; CI PR e main passaram com 369 testes cada, OpenAPI e deploy Actions 37692274600 aprovados. Snapshot RDS disponível antes do merge; branch local preservada.
- MCP habilitado explicitamente; migrations/grants/append-only/isolamento/0600 e HTTPS/discovery/auth/internal conferidos, inventários de domínio idênticos e zero mercados produtivos de teste.
- [Evidências produtivas](../testing/mcp-production-rollout-20261007.md). Entrega técnica/rollout concluídos; FEAT-MCP-001 permanece parcial por homologação Dot/piloto autenticado.

## 2026-10-07 — fechamento local MCP e rollout preparado

- Fonte de verdade alinhada: revisão universal, arquitetura/ADR, frontmatter auth/logs, operação e pendências externas. Revisão inválida no POST recebe erro controlado sem mutação; parecer novo informa gate universal.
- Deploy integra serviço/proxy MCP, arquivos privados 0600 e ativação/rollback explícitos, desligado na primeira instalação. CI de PR adicionada, deploy restrito à main. Pré-checagem produtiva somente leitura; snapshot/merge/deploy aguardam autorização da descrição da PR.
- 367 testes/879,395 s/OK; 19 focais/6,268 s e sete de rollout/2,146 s aprovados, com sobreposições documentadas. Docker/Compose/Caddy/Django/OpenAPI/Ruff/JS/dependências/diff aprovados. Evidências e checklist: [fechamento](../testing/mcp-closeout-20261007.md). FEAT-MCP-001 permanece parcial por rollout/HTTPS/Dot; branch local deve ser preservada.

## 2026-10-07 — recomendações 1/2 do review MCP

- Dependências, templates, migrations/grants, deploy/runbook e testes da feature adicionados ao índice Git. Snapshot limpo sem env/runtime validado com venv nova e instalação independente de requirements.
- Teste de asset verifica script/defer sem versão literal. 74 testes/172,744 s/OK em PostgreSQL isolado; Django/OpenAPI/pip/migrations/diff aprovados. [Relatório](../testing/mcp-branch-review-followup-20261007.md). Sem commit/merge/deploy ou mutação DEV; item 3 não selecionado, homologação externa ainda pendente.

## 2026-10-07 — ensaio integral do catálogo DEV humano e MCP

- Catálogo DEV reiniciado mediante pedido explícito e backup integral local; contas, configuração, taxonomia, integração e logs preservados. Mercados antigos 1/2/3/5 substituídos por cenários sintéticos #6 humano (resolvido) e #7 MCP (fechado/aguardando resolução).
- Corrigidos fuso escolhido no fechamento/resolução, precisão do prazo MCP, retorno privado de notas administrativas, criação sem publicação prematura e ação inadequada no mercado fechado. OpenAPI atualizado.
- 64 testes amplos e 17 focais (sobrepostos) passaram; UI Chrome, dez tools MCP/OAuth/serviço, gates, logs e integridade reais DEV conferidos. Fechamento automático em relógio real; cadeia e dois mercados verificados, zero issues. [Relatório](../testing/dev-catalog-rehearsal-20261007.md). Dot/deploy permanecem pendentes.

## 2026-10-07 — feedback de fechamento legado publicado

- Diagnóstico DEV: salvamento rejeitado por definição assinada; valores preenchidos não persistidos. Mensagem backend específica e aviso web distinguem registro salvo/formulário, sem liberar alteração de prazo/fuso/modo publicado.
- 12 testes passaram (4,794 s); PostgreSQL isolado destruído, checks e Chrome aprovados. Sem mutação DEV/migration/deploy. Retificação assinada permanece evolução separada. [Relatório](../testing/legacy-closure-feedback-20261007.md).


## 2026-10-07 — revisão editorial universal e fechamento completo

- Ficha/parecer para origem humana, sugestão convertida e MCP; gate FastAPI exige aprovação atual e configuração de fechamento em ambos os modos. Edição invalida; ficha em publicado não altera lifecycle.
- Migration 0003 integration nullable/backfill pendente aplicada DEV; mercados/opções/previsões/provas e aprovação Tesla preservados. UI universal com fontes atestadas, links e alertas; OpenAPI/ADR/specs/runbook atualizados.
- 68 testes passaram (195,984 s), PostgreSQL isolado destruído; checks estáticos/contratos e Chrome DEV aprovados. [Relatório](../testing/universal-editorial-20261007.md). Sem deploy, homologação externa pendente.

## 2026-10-07 — estado publicado no editor de todos os mercados

- Estado publicado/cancelado aparece também em mercados sem MCP; estado atual usa label FastAPI. Link/parecer/bloqueio continuam específicos à ficha de integração.
- Oito testes UI passaram (0,021 s), Chrome DEV confirma EV publicado/Aberto sem ficha MCP. Sem alteração de dados/regras/contratos/OpenAPI.

## 2026-10-07 — mensagem editorial após publicação

- Editor diferencia lifecycle: bloqueio apenas em draft/scheduled sem aprovação, mensagem de publicação já realizada nos estados publicados e cancelamento em canceled. Parecer traduzido e aviso pré-publicação restrito aos estados adequados.
- Sete testes passaram (0,021 s); Chrome DEV confirma Tesla publicado/aprovado revisão 11. Sem alterações no backend, contratos/OpenAPI, dados ou publicação pelo agente.

## 2026-10-07 — confirmação humana de lacunas resolvidas

- Parecer permite confirmar resolução documentada das lacunas sem apagar texto manualmente. A ação humana atualiza a ficha via assessment existente; snapshots anteriores preservados.
- Sem resolução inferida de critérios, aprovação automática ou redução das validações de fontes/versão/MFA. Texto/confirmação preservados em erro; sete testes passaram (8,925 s). DEV #5 permanece em revisão, sem publicação/deploy.

## 2026-10-07 — revisão MCP e design de mercados

- Mercados adota cabeçalho compacto e painel/tabela Admin Ops, agrupa destaque e tipo, preserva origem/estado/link MCP.
- Fontes sugeridas integram a evidência editável; removidos seletores repetidos por critério. Vínculo estruturado deriva de URLs explícitas ao catálogo; conferência humana independente mantida.
- Bloqueio de lacunas explica motivo e preserva decisão/marcações; oito testes locais em PostgreSQL isolado passaram (12,393 s), UI Chrome DEV conferida sem escrita no draft. Contrato/OpenAPI compatíveis, sem migrations/deploy.

## 2026-10-07 — origem MCP e revisão na lista de mercados

- Admin Ops mostra identificação de agente IA via MCP, estado editorial distinto do status do mercado e link direto ao parecer humano. Reutiliza metadados administrativos existentes; sem contrato/migration/regra nova.
- Quatro testes UI passaram; conferência Chrome DEV somente leitura. Indicador mantém legibilidade e versão de CSS atualizada; nenhuma alteração nos dados DEV.


## 2026-10-07 — parecer humano MCP em uma ação

- Formulário único para conferir/ajustar ficha e registrar aprovar/devolver/rejeitar. Sem etapa humana obrigatória de reenvio e sem status/atestação duplicados; contexto opcional recolhível.
- FastAPI assessment compõe snapshot e decisão atomicamente; falha reverte inclusive eventos e revisões. MFA/versão/hash/locks, gate de publicação e contratos anteriores preservados; sem migrations, publicação DEV ou deploy.

## 2026-10-07 — retomada da revisão humana MCP

- Admin Ops permite atualizar ficha e enviar para revisão sem depender do executor. FastAPI valida registro/revisão/estado/MFA, cria snapshot e evento humano e invalida parecer antigo.
- Aprovação permanece separada e recusa pendências; erros mantêm o contexto e CSRF/PRG protegem submissão. OpenAPI/runbook/contratos e testes sincronizados; sem migration ou publicação DEV.

## 2026-10-07 — MCP revisão 1.1: slug, aprovação obrigatória e estrutura de gestão

- Slug gerado do título com colisões/replay protegidos. Gate específico no lifecycle exige aprovação humana vigente para mercados de integração; versão/hash/política/conteúdo revalidados antes de assinar/abrir.
- Editor separa publicar de salvar; preserva fuso e seleção de evento homônimo. Integrações segue Agentes IA: indicadores, tabela, criação separada, auditoria recente centralizada. OpenAPI aditivo sincronizado.
- Draft DEV #5 corrigido sem publicação; revisão 4/preparation, prazo e mercados 1–3 preservados. [Evidências](../testing/mcp-review-gate-20261007.md). Feature permanece parcial por homologação externa/deploy.

## 2026-10-07 — radar MCP persistente no DEV

- Execução autorizada no PostgreSQL DEV: draft #5 em revisão, dez tools/21 chamadas, replay/conflitos e preservação dos mercados prévios verificados. OAuth local real e UI conferidos.
- Corrigidos parâmetros escalares do consentimento Django e título na ficha de revisão. Teste sem banco, Ruff/OpenAPI aprovados. [Evidências](../testing/mcp-radar-dev-20261007.md). Sem publicação ou homologação externa.

## 2026-10-07 — FEAT-MCP-001 radar real em ambiente isolado

- Pesquisa externa + cliente MCP real: dez tools, 17 chamadas, um draft/ficha submetido sem parecer humano fictício; replay/cota e recusa de edição confirmados.
- Corrigida serialização de campos nullable em detalhe de mercado, preservando privacidade de ficha. Quatro testes passaram (29,121 s), incluindo OAuth/serviço. [Relatório](../testing/mcp-radar-pilot-20261007.md).

## 2026-10-07 — FEAT-MCP-001 descoberta editorial explícita

- Instructions e descrições diferenciam política/manual editorial (`get_editorial_policy`), catálogo (`search_markets`), taxonomia e detalhe de mercado. Sem alteração de nomes, schemas, rotas ou acesso.
- Cliente real com dez ferramentas em ambos os modos passou novamente (15,650 s), incluindo conteúdo completo do manual/checklist/ficha e 11 critérios. Runbook orienta Refresh tools/conversa nova e registra limitações do parser/modelo do LM Studio.

## 2026-10-07 — FEAT-MCP-001 exercício de todas as ferramentas

- Teste de cliente MCP real ampliado para as dez ferramentas com OAuth e serviço: catálogo exato, leituras, validação, criação/replay, edição, submissão e consulta do parecer. Edição em revisão e ID inexistente negados como esperado.
- Execução TCP/PostgreSQL isolada passou em 15,236 s, sem mercados no DEV/produção ou uso do segredo compartilhado. Base destruída e servidores temporários encerrados; 22 chamadas positivas e quatro negações esperadas. Homologação LM Studio/Dot continua independente.

## 2026-10-07 — FEAT-MCP-001 seletor de validade

- Campo de validade usa calendário/horário nativos (`datetime-local`), com fuso São Paulo explícito e precisão de minutos. Data UTC existente é convertida para apresentação local; escolha é enviada à API com offset pelo Django, independentemente do fuso ativo/browser.
- Quatro testes passaram (conversão com troca de dia, fuso alternativo, data inválida e regressão UI/CSRF), checks aprovados e componente conferido no Chrome DEV. Sem salvar integração, alterar contratos ou recarregar formulário preenchido do usuário.

## 2026-10-07 — FEAT-MCP-001 responsável por seleção de nome

- Criação e transferência exibem nomes/@usuários elegíveis no lugar de campo numérico; nomes também aparecem no resumo/listagem. API administrativa MFA oferece projeção mínima paginada de humanos ativos staff/superuser, sem emails ou dados pessoais adicionais. Django valida a opção e FastAPI revalida elegibilidade na mutação.
- OpenAPI/contrato atualizados. Três testes isolados passaram (MFA, elegibilidade, paginação, seleção, transferência e regressões), checks estáticos aprovados e Chrome DEV conferido. Formulário aberto do usuário preservado; nenhuma integração criada no DEV.

## 2026-10-07 — FEAT-MCP-001 parecer humano alinhado ao Admin Ops

- Fila e detalhe de parecer reutilizam cabeçalho, ações, estados e seções de configuração. Ficha/contexto, critérios, fontes, decisão e histórico têm hierarquia própria; labels explícitos e conteúdo longo responsivo.
- Mantidos CSRF, revisão/hash esperados, verificação independente, escape de conteúdo e aviso sobre publicação humana. Dois testes direcionados passaram em PostgreSQL isolado, incluindo renderização de draft em revisão com evidência maliciosa; Chrome DEV conferido em desktop/390 px. Sem criação de mercado no DEV ou alteração de regras de domínio.

## 2026-10-07 — navegação compartilhada Admin Ops

- Menu lateral por áreas, busca com suporte a acentos e indicação da seção ativa em telas aninhadas. Drawer móvel com navegação por teclado, Escape e retorno de foco; fallback visível sem JavaScript.
- Mantidos os tokens do design system e removida navegação duplicada da revisão editorial. Cache de CSS/JS atualizado.
- Quatro testes direcionados passaram, incluindo proteção/renderização Admin Ops e CSRF/segredo único/escape MCP, com PostgreSQL isolado. Chrome DEV conferido em desktop e viewport estreito, busca vazia/acentos/sem resultados e abertura/fechamento do menu. Sem alteração de domínio, contratos ou publicação.

## 2026-10-07 — FEAT-MCP-001 alinhamento visual Admin Ops

- Integrações reutiliza cabeçalho, campos e seções da página de Config; retirada navegação duplicada. Formulário organizado em identificação, permissões legíveis e limites agrupados. Estados traduzidos e revogação definitiva separada das ações usuais.
- CSS/JS do Admin recebem versão nova para invalidar cache. Layout conferido no Chrome DEV em desktop/tela estreita/tema escuro; preferência original restaurada. Teste existente de CSRF/exibição única/escape passou. Sem alteração de contratos ou regras de domínio.


## 2026-10-07 — FEAT-MCP-001 implementação local

- OAuth/Authlib e serviço, identidade técnica/delegação, MCP SDK Streamable HTTP com dez ferramentas restritas, gestão/consentimento/revisão Admin Ops. Staff/superuser com MFA equivalentes.
- Migrations aditivas/grants, serviços compartilhados, drafts/ficha/snapshots, idempotência, cotas persistentes São Paulo, locks humanos/publicação/revogação e correlação nos logs/eventos existentes.
- OpenAPI atualizado, testes PostgreSQL/cliente MCP real, UI desktop/mobile, imagem sem DB e configuração/runbook/rollback/prompt preparados. [Evidências](../testing/mcp-editorial-results.md). Sem merge/deploy; Dot e HTTPS externo pendentes.


## 2026-09-29 — FEAT-ANALYTICS-001 validação produtiva v0.4

- PR `#133` integrada por squash (`61bc109`); CI e deploy produtivo do workflow `36583348331` concluídos com sucesso.
- GeoLite City instalada no volume persistente e carga registrada como `success`, após corrigir a posse do diretório runtime. Segredo compartilhado e rede confiável do proxy configurados; saúde da API/banco, rotas OpenAPI e proteção do Analytics administrativo verificados.
- Site em manutenção e sem eventos humanos recentes durante o smoke; distribuição de novo binário Flutter e observação da primeira coleta real continuam como acompanhamento operacional, fora do fechamento do backend/web v0.4.

## 2026-10-07 — FEAT-MCP-001 especificada

- Feature aprovada para implementação: MCP editorial, gestão de integrações, dois modos de autenticação, drafts/ficha/revisão e auditoria existente.
- Contratos e critérios de aceite definidos; nenhum endpoint, migration ou tela implementado nesta entrega. Prompt de retomada em `docs/guides/implementar-mcp-editorial-prompt.md`.

## 2026-09-29 — FEAT-ANALYTICS-001 retenção e mapa real

- FastAPI calcula coortes D1/D7/D30 separadas para visitantes anônimos e contas cadastradas, com elegibilidade por dia completo, base numérica e semanas de entrada.
- Admin Ops reorganizado em retenção, jornada, geografia, tráfego e operação. O mapa esquemático foi substituído por SVG local com as 27 malhas simplificadas do IBGE e contorno visível sem JavaScript.
- Revisão para publicação: a chave de tela web é normalizada para o catálogo fechado e o limite da coleta usa IP de origem validado, não `visitor_id` controlado pelo cliente.

## 2026-09-29 — FEAT-ANALYTICS-001 estado das cargas

- Última remessa de eventos e volume recebido em 24 horas aparecem no Admin Ops, calculados e registrados pela FastAPI.
- Atualizador GeoLite local valida checksum/base, substitui arquivo atomicamente e grava resultado; painel exibe última execução e arquivo ativo separadamente.

## 2026-09-29 — FEAT-ANALYTICS-001 geografia e desistência

- FastAPI passa a agregar UFs/cidades do Brasil, cobertura geografica diaria, atividade diaria da UF e funil observacional de ticket por sessao/mercado apos 30 minutos sem atividade.
- Admin Ops apresenta mapa esquematico das UFs, rankings filtraveis, evolucao e pontos de parada; o app Flutter emite selecao de opcao no ticket inicial.
- Cliques e abandono nao sao tratados como confirmacao de dominio nem motivo comprovado da saida.

## 2026-09-29 — FEAT-ANALYTICS-001 primeira fatia

- Branch `feature/first-party-analytics` criada de `origin/main` cf0f33b apos snapshot integral anterior ao trabalho.
- Novo contrato de eventos e tabelas de visitante, sessao, visualizacao e evento; coleta web/mobile, geografia opcional local, resumo FastAPI staff/MFA e pagina Analytics no Admin Ops.
- Totais de dominio sao lidos de usuarios/previsoes reais sem atribuir indevidamente origem/regiao. Cobertura restante documentada em `known-gaps.md`.

## 2026-09-28 — FEAT-AUTH-001 MFA administrativo implantado

- TOTP RFC 6238 compatível com Google Authenticator foi implementado para staff/superuser: FastAPI controla desafio de cinco minutos, fator Fernet, rate limit, recovery codes hashados/uso único e sessão administrativa com evidência MFA; Django apenas apresenta os fluxos PT-BR/EN e Django Admin não é exposto.
- Migrations `accounts 0023/0024`, snapshot OpenAPI, ADR-0009, documentação operacional e regressões unitárias/web/integração foram concluídos. A chave Fernet de produção foi provisionada no Secret Manager e sincronizada exclusivamente para o ambiente FastAPI, sem valor em Git ou logs.
- PR `#130` integrou a implementação e PR `#131` tornou a migration de grants compatível com o banco efêmero do CI. O workflow `36425169684` concluiu a suíte e o deploy; produção respondeu API e site saudáveis, com migrations `0023/0024` aplicadas e a chave Fernet restrita ao ambiente FastAPI.
- A fatia MFA está implantada e validada; `FEAT-AUTH-001` ampla permanece `draft/parcial` pelas evoluções de autenticação ainda registradas, e o app mobile não recebe MFA administrativo enquanto não tiver superfície de operações.

## 2026-09-27 — FEAT-AUTH-001 / FEAT-AIAGENT-001 contas produtivas apos Argon2id

- `@test` manteve sua identidade e recebeu nova senha Argon2id via FastAPI; hash, login mobile-header e login web foram validados. Senha armazenada fora do Git no Secrets Manager. `@karlascardua` permanece sem senha utilizavel e requer reset antes de novo acesso.
- Os dois agentes oficiais mantem senhas inutilizaveis intencionalmente. O daemon usa `user_id`/`is_bot` e continuou executando ciclos para ambos; 26 ciclos recentes por agente foram pulados por `no_eligible_market`, sem falha de autenticacao. Sem mudanca de codigo, contratos, migrations ou app mobile.

## 2026-09-27 — FEAT-AUTH-001 melhoria de senha implantada

- PR `#126` integrada a `main`; CI e deploy `36330226816` passaram. Fronteira PostgreSQL e segredos segregados ativos na EC2/RDS, com `auth_db_boundary check` e `check-api` aprovados nas roles reais. Site, API e login/sessao/logout com headers mobile validados em producao.
- Corte pre-lancamento encerrou 3 hashes PBKDF2: superusuario `@admin` recebeu novo hash Argon2id pela FastAPI; duas contas tiveram senha antiga inutilizada e sessoes revogadas. Inventario final: 1 Argon2id, 0 PBKDF2 e 4 senhas inutilizaveis. Credencial bootstrap e pepper estao fora do Git no Secrets Manager; snapshot RDS anterior ao corte disponivel. `FEAT-AUTH-001` ampla permanece `draft/parcial`.
- O redeploy documental `#127` passou em CI/deploy. Um `401` do `@admin` apos esse deploy exigiu redefinir novamente a senha; depois disso, login web/mobile e verificacao do hash permaneceram corretos apos reinicio, recriacao e reaplicacao dos grants/migrations. Causa inicial nao reproduzida, registrada em `known-gaps.md` para acompanhamento.

## 2026-09-27 — FEAT-AUTH-001 fechamento local da melhoria de senha

- A fatia Argon2id/pepper e autoridade da FastAPI esta pronta para publicacao, com suite Django/API de 267 testes, 107 testes Flutter, `flutter analyze`, OpenAPI e smoke local web/API/Android aprovados. O ensaio isolado foi dispensado pelo usuario; preflight de segredos, grants, inventario de PBKDF2, CI/deploy e smoke produtivo continuam obrigatorios para fechar esta entrega.
- A feature ampla de autenticacao segue `draft/parcial`; nenhuma alteracao de contrato HTTP, OpenAPI ou app mobile foi necessaria.

## 2026-09-27 — FEAT-AUTH-001 e FEAT-RES-001 correcoes do review local

- `gotrendlabs_users` e o guard de senha passaram a pertencer a role sem login; migrations usam credencial separada, grants por coluna preservam edicao nao sensivel pelo Django e preflight bloqueia deploy inseguro. Revisao posterior separou tambem `FASTAPI_POSTGRES_*` do ambiente compartilhado: so FastAPI recebe a credencial com escrita de senha; Django e daemon usam a role Django. Aplicado e verificado apenas no PostgreSQL local.
- Reconciliação de refund agora recusa saldo bloqueado insuficiente antes de gravar ledger/credito. Teste cobre rollback, caso normal e reexecucao idempotente.
- Inventario de hashes sem PII e benchmark isolado foram adicionados para preparar corte de contas e capacidade; host produtivo nao foi alterado.

## 2026-09-27 — FEAT-AUTH-001 Argon2id com pepper

- Senhas locais passam a usar Argon2id com sal individual e pepper exclusivo de 32 bytes fora do banco/Git; FastAPI detem o segredo e cria/verifica senhas em runtime. Django recusa criacao/verificacao local de senhas utilizaveis e os clientes web/mobile preservam os contratos da API. Hashes PBKDF2 anteriores sao rejeitados conforme corte pre-lancamento aprovado pelo usuario.
- Sem mudanca de schema de produto/OpenAPI. Cadastro, login, login social e reset preservam seus contratos. Segredo ausente/invalido bloqueia a FastAPI; `.env.api.local` e `.env.auth.prod` segregam o segredo, e o banco local bloqueia a escrita de senha pela role Django via trigger. Ownership de banco e configuracao do host antecedem qualquer deploy.
- Testes de interoperabilidade, sal, segredo ausente/incorreto, hash antigo/malformado, inicializacao e fluxos de auth adicionados/revisados; a suite final de 267 testes locais passou, alem dos checks de Django, migrations e OpenAPI. Custo inicial `m=19456 KiB,t=2,p=1` com duas operacoes concorrentes por processo por limite do host atual; medicao produtiva pendente.

## 2026-09-26 — FEAT-EDITORIAL-001 implantada e validada

- PR `#124` integrada à `main`; GitHub Action `36275879637` concluiu testes e deploy com sucesso. Rota produtiva redireciona visitantes ao login; manual, checklist e ficha renderizam `200` para sessão staff no container. Estado promovido a `implementada_validada`; IA e parecer estruturado seguem como evolução futura.

## 2026-09-26 — FEAT-EDITORIAL-001 fechamento do escopo local

- Manual/ficha/checklist v1.2 aprovados; consulta staff no Admin Ops e critérios JSON E01–E11 implementados e validados localmente. Revisão visual do usuário concluída; documentação, testes e memória alinhados. Estado `implementada_aguardando_deploy` até CI/deploy/smoke produtivo. Avaliação por IA e parecer estruturado ficam para evolução futura separada.

## 2026-09-26 — FEAT-EDITORIAL-001 consulta Admin Ops local

- Criada página staff de consulta ao manual, checklist e ficha, com atalhos na lista e no editor de mercados. Critérios E01–E11 versionados em JSON e confrontados com documentos por testes. Conteúdo read-only; sem execução de IA, parecer persistido ou gate novo.

## 2026-09-26 — FEAT-EDITORIAL-001 versão 1.2 aprovada

- Usuário aprovou o editorial v1.2. Status documental promovido a `aprovada`, mantendo implementação `documentada`. Consulta administrativa e futura avaliação por IA são evolução separada, ainda não implementada.

## 2026-09-26 — FEAT-EDITORIAL-001 mercados de previsão (v1.2)

- Reorganizado manual a partir de incerteza, pergunta, opções/regras, apuração, revisão e resolução. Incluída introdução sobre mercados de previsão e opções de resposta. Checklist E01–E11 separado e ficha alinhada; removidas cotas de categorias como requisito de publicação, preservando anti-repetição. Indicadores agrupados em participação/acompanhamento e qualidade das perguntas/resolução.

## 2026-09-26 — FEAT-EDITORIAL-001 revisão de clareza (v1.1)

- Manual e ficha reescritos para staff sem conhecimento técnico, com exemplos de diversidade, perguntas, fontes, prazos e comunicação de percentuais. Removido o piloto; acompanhamento dos indicadores explica leitura, limitações e ações. Regras de domínio preservadas.

## 2026-09-26 — FEAT-EDITORIAL-001 governança documental

- Criados manual editorial e ficha reutilizável para pauta, fonte, critérios, prazos, exceções, revisão E01–E11 e acompanhamento.
- Registrados pareceres operacionais, rechecagem da versão antes de publicar, responsabilidade humana e compatibilidade com definição assinada/selagem.
- Integradas spec funcional, arquitetura Admin Ops, README e memória operacional; sem alteração de runtime, contratos ou mercados reais.
- Piloto temático e cadência permanecem hipóteses; aprovação estruturada e bloqueio automático não foram implementados.

## 2026-09-26 — FEAT-MOBILE-001 AAB Google Play Closed testing

- Versão mobile avançada para `1.2.0+14`, preservando o APK público direto `1.0.7 (8)` e a política produtiva de compatibilidade.
- AAB assinado gerado com bases de produção, `targetSdk=36`, três ABIs, SHA-256 `0f87b9634be842f69c0c257b6a41c35313a29750c13ae3cba9cd25068b172a16` e tamanho `57524579` bytes.
- Specs passam a distinguir Closed testing suportado de publicação pública ainda fora do escopo; a release usa o nome automático `14 (1.2.0)` e notas gerais em `pt-BR`.
- Bundle 14 publicado no track `Closed testing - Alpha`, ativo e `Available to testers on Google Play`, com rollout de 100% para o grupo configurado e disponibilidade em 177 países/regiões; notas `pt-BR` confirmadas no Console.

## 2026-09-26 — FEAT-AUTH-001 maioridade publicada

- PR `#121` integrada em `main`; CI, suíte completa, migration `accounts 0022` e deploy produtivo concluídos com sucesso no workflow `36246617456`.
- Smokes produtivos confirmaram `birth_date` obrigatória nos contratos, rejeição de ausência, menoridade e data futura, além da aceitação do limite exato de 18 anos antes das demais regras do cadastro, sem criar conta de teste.
- Após autorização do proprietário, a manutenção web foi desativada; home, cadastro e política pública responderam normalmente e exibiram a restrição a pessoas com 18 anos completos.

## 2026-09-19 — FEAT-AUTH-001 maioridade obrigatória

- Cadastro humano por senha e por provedor social passa a exigir `birth_date` privada e aceita somente pessoas com 18 anos completos, com decisão autoritativa na FastAPI.
- Django web e Flutter coletam a data, exibem a política etária e preservam mensagens seguras do backend; perfil não permite remover a data nem alterá-la para uma condição de menoridade.
- Migration pré-produção preenche perfis legados sem nascimento com `1990-01-01` antes de tornar a coluna obrigatória; a versão fixa da política passa a `2026-09-19`.
- No Flutter, cadastro e perfil reutilizam o formatador `DD/MM/AAAA`, enviam `YYYY-MM-DD` à FastAPI e bloqueiam data vazia ou inválida antes do envio sem duplicar a decisão autoritativa de maioridade.

## 2026-09-19 — FEAT-OPSLOG-001 conexão do daemon entre ciclos

- O comando contínuo `run_gotrendlabs_daemon` passa a revalidar conexões Django antes e depois de cada ciclo, evitando que as outboxes de email e push reutilizem uma conexão PostgreSQL encerrada durante o intervalo de 300 segundos.
- A correção preserva o isolamento de falhas, a idempotência e os contratos das outboxes; não altera schema, eventos de domínio ou regras de retry.
- A regressão cobre os dois limites de conexão de um ciclo `--once`.

## 2026-09-07 — FEAT-INTEGRITY-001 evolucoes pos-auditoria

- O smoke criptografico permanece valido; foram registrados, sem mudanca de runtime, hardenings P1 para ownership/grants append-only e entrega efetiva dos alarmes.
- Capacidade/HA, retencao operacional, identidade IAM por workload, rotacao versionada do commitment secret, headers publicos da FastAPI e ensaio de carga/observacao por 24 horas ficam como P2 antes do lancamento irrestrito.
- FEAT-NOTIFY-001 passa a prever tratamento administrativo auditado e idempotente de entregas push terminais; as quatro falhas antigas foram limpas preservando as notificacoes de origem, mas o mecanismo permanente continua planejado.

## 2026-09-07 — FEAT-INTEGRITY-001 encerramento produtivo

- PRs `#114` e `#115` integradas por merge commit; workflows de CI/deploy `34157223820` e `34158379066` concluídos com sucesso.
- AWS KMS Ed25519, alias, IAM mínimo, segredo de commitment, snapshot RDS, alarme de volume de assinatura e 1 GiB de swap foram configurados em produção.
- O corte idempotente removeu todos os 30 mercados pré-lançamento sem definição assinada e efeitos estritamente relacionados; a primeira tentativa foi revertida integralmente por FK de push e originou regressão específica antes da execução final.
- Smoke produtivo confirmou assinatura/verificação KMS real, chave pública/fingerprint coerentes, checkpoint integral, cadeia global válida sem pendências, FastAPI/banco saudáveis, dois workers Django e um daemon.
- A implementação passa para `implementada_validada`; carga representativa, observação da auditoria por 24 horas, identidade IAM por workload e rotação versionada do segredo permanecem evoluções documentadas.

## 2026-09-07 — FEAT-INTEGRITY-001 aprovação e preparação de produção

- A spec funcional/técnica foi aprovada pelo usuário na versão `1.2`; a implementação permanece `implementada_aguardando_deploy` até CI, rollout AWS e smoke produtivo.
- O corte inicial passa a remover todos os mercados pré-lançamento sem definição assinada, inclusive rascunhos e agendados, sempre após snapshot do RDS e sem assinatura retroativa ou modo legado.
- O Compose de produção passa o frontend Django de um para dois workers Uvicorn; o runbook exige 1 GiB de swap, monitoramento de memória e rollback operacional para um worker.
- O runbook consolida criação da chave/alias KMS Ed25519, IAM mínimo no ARN específico, segredo de pseudonimização no Secrets Manager, sincronização segura do runtime e smokes de assinatura/auditoria.

## 2026-09-07 — FEAT-INTEGRITY-001 endurecimento de selagem e prova pública

- A selagem passa a executar auditoria integral fresca da cadeia global sob o mesmo lock transacional; checkpoint anterior continua acelerando consultas públicas, mas não autoriza uma transição irreversível.
- A prova pública deixa de expor eventos e referências de compromissos individuais; web e mobile recebem somente o total agregado, a raiz final e os eventos de ciclo do mercado.
- O verificador confronta o envelope criptográfico e os metadados persistidos de definição, compromissos, Seal e folhas Merkle, incluindo relações, timestamps, protocolo, algoritmo e fingerprint.
- Divergência global idêntica, sem mudança no head, respeita backoff de uma hora no daemon para evitar repetição de varredura e assinatura a cada ciclo; a falha continua visível e suprime as selagens antes da iteração dos mercados vencidos.
- Rotação versionada do segredo de pseudonimização e resumo materializado por mercado ficam registrados para evolução da plataforma.

## 2026-09-07 — FEAT-INTEGRITY-001 checkpoints assinados

- O daemon passa a criar checkpoints globais canonicos, assinados, encadeados e append-only, com auditoria incremental em cada ciclo e integral no bootstrap/primeiro ciclo apos 24 horas.
- A verificacao publica deixa de percorrer todos os eventos e passa a validar checkpoint, head e limite por consultas indexadas; novo `GET /integrity/status` expoe a situacao global sem dados de mercado.
- O contrato substitui `valid` por `verification_status`, `market_valid`, `ledger_chain_valid` e `overall_valid`, distinguindo atraso normal (`pending`) de divergencia (`failed`) e indisponibilidade.
- Selagem permanece fail-closed sob advisory lock; a otimização incremental serve às auditorias recorrentes e às leituras públicas, sem substituir a auditoria integral exigida pelo Seal.
- Django/Admin Ops e Flutter apresentam sequencia auditada, head, pendencias e horario da ultima auditoria sem disparar full scan; Flutter avanca para `1.2.0+13` sem camada legada.
- Migration `0031_integrity_ledger_checkpoints` adiciona indices, assinatura historica, trigger contra mutacao/truncate e privilegios minimos.
- O corte pre-producao remove alertas operacionais mutaveis dos mercados candidatos antes da FK `PROTECT`, sem tocar provas append-only.

## 2026-09-07 — FEAT-INTEGRITY-001 fechamento dos achados de revisao

- A selagem passa a exigir a verificacao integral aprovada, incluindo definicao/resultado atuais, compromissos, eventos do mercado e cadeia global; qualquer divergencia mantem o mercado em `resolved` para retry seguro.
- `valid=false` passa a ser obrigatorio quando a cadeia global falha, ainda que `ledger_chain_valid` e `warnings` preservem o diagnostico de escopo.
- Alertas pendentes prevalecem no resumo de integridade, impedindo cards web/mobile de exibirem selo positivo para mercado com falha conhecida.
- O verificador da cadeia vincula protocolo, entidade, mercado, timestamp, correlacao/causalidade, algoritmo, fingerprint e `created_at` aos dados assinados ou a metadados criptograficamente conferidos.
- A auditoria passa a varrer tambem mercados sem definicao e cria `definition_missing` de severidade alta quando a prova e obrigatoria.
- O purge pre-producao remove somente badges causalmente ligados aos mercados eliminados e preserva concessoes/notificacoes independentes.
- O risco de escala da verificacao global integral foi encaminhado para checkpoints assinados; medicao com volume representativo continua pendente em staging.

## 2026-09-07 — FEAT-INTEGRITY-001 endurecimento de cobertura e corte pre-producao

- Mercados publicados sem definicao assinada deixam de ser mantidos como legado ativo; comando `purge_unsigned_markets` inventaria em `dry-run`, exige backup confirmado, recusa provas protegidas, remove dependencias operacionais e reconcilia wallet/reputacao/badges.
- Previsoes iniciais humanas e de agentes IA compartilham escritor transacional com wallet, compromisso e evento; falha do signer no agente reverte o savepoint antes da auditoria da falha.
- Verificacao compara previsoes com compromissos em cobertura exata e valida opcao, stake, tipo, sequencia, timestamp, pseudonimo e definicao; ausencia ou adulteracao impede Seal.
- Definicoes novas protegem IDs taxonomicos e preservam nomes como snapshot, permitindo renomeacao editorial sem esconder troca de associacao.
- Auditoria indisponivel adia apenas a selagem do ciclo; fechamento, retencao, email, push e processo daemon continuam isolados.
- Flutter avanca para `1.1.0+12`; como ainda nao esta em producao, nao foi criada camada de compatibilidade com builds anteriores.

## 2026-09-06 — FEAT-MOBILE-UX-001 detalhe e painéis compactos

- O critério de resolução passa a anteceder previsão/posição e resultado pessoal no detalhe mobile.
- `Sua mesa` reduz cada atalho a duas linhas visuais; o painel de seis métricas passa a duas fileiras compactas em celular padrão.
- Comprovantes assinados iniciam recolhidos e a verificação do mercado ganha detalhes técnicos completos e progressivos, em paridade com o comprovante individual.

## 2026-09-06 — FEAT-INTEGRITY-001 posição coerente no detalhe web

- `Sua posição` passa a ocupar uma posição fixa entre o estado/resultado oficial e as ações, usando o mesmo componente em mercados abertos, em apuração, resolvidos, selados e cancelados.
- Resultado pessoal, confirmação de previsão/reforço/revisão e comprovantes assinados ficam reunidos no bloco pessoal; o resultado oficial permanece independente.

## 2026-09-06 — FEAT-INTEGRITY-001 copy coerente do ciclo web

- O detalhe web passa a identificar o bloco como `Ciclo do mercado` e usa mensagens próprias para agendamento, apuração, resultado publicado, conclusão e cancelamento.
- Rótulos e métricas deixam de mostrar `Fecha em` ou contagem regressiva depois que as previsões foram encerradas.
- A finalização pendente diferencia prazo normal, retry operacional e mercado legado; a etapa final selada aparece concluída.

## 2026-09-06 — FEAT-INTEGRITY-001 conclusão clara no detalhe web

- O detalhe de mercado selado passa a comunicar primeiro `Mercado concluído`, deixando explícito que o ciclo de previsões, apuração e resultado terminou.
- A integridade aparece como complemento `Concluído e verificável`, com explicação curta sobre resultado publicado e registro finalizado; o escudo permanece como único acesso à verificação.

## 2026-09-06 — FEAT-INTEGRITY-001 hierarquia da integridade no detalhe mobile

- A secao mobile passa a se chamar `Integridade do mercado`; no estado registrado, informa que a definicao publicada foi registrada e pode ser conferida.
- O bloco deixa de interromper o fluxo principal e aparece depois de previsao/posicao, comprovantes e criterio/resultado, mantendo `Verificar integridade` como acao secundaria.

## 2026-09-06 — FEAT-INTEGRITY-001 selo compacto nos cards mobile

- Os cards Flutter deixam de exibir o pill textual `Definicao registrada`/`Historico verificavel` e passam a usar somente um escudo circular no canto superior direito da imagem, em paridade visual com o site.
- Thumbnail e informacoes editoriais permanecem intactas; tooltip e semantics mantem a descricao completa para acessibilidade, e cores/icones continuam distinguindo registro, finalizacao, retry, divergencia e Seal.

## 2026-09-06 — FEAT-INTEGRITY-001 comprovantes assinados no mobile

- O detalhe mobile autenticado passa a listar separadamente o comprovante da previsao inicial, de cada reforco e de cada revisao, inclusive depois que a posicao deixa de estar ativa.
- Cada item abre um modal rolavel com resumo da acao, explicacao leiga de hash/assinatura/encadeamento, detalhes tecnicos, estado da prova individual, copia e retry.
- A confirmacao imediata de uma mutacao oferece acesso ao recibo completo; Flutter continua consumindo a FastAPI sem recalcular ou assinar dados no aparelho.

## 2026-09-06 — FEAT-INTEGRITY-001 auditoria administrativa por camada

- `Auditar integridade` passa a estar disponível no browse administrativo para qualquer estado e na fila de resolução para todos os itens exibidos.
- A visão operacional separa definição, compromissos, resultado, Seal, Merkle, eventos do mercado e cadeia global, sem rotular etapas futuras ou mercados legados como adulteração.
- Compromissos assinados passam a reportar validade desde a publicação, antes do Seal, sem expor previsões ou usuários.
- A consulta administrativa usa endpoint staff read-only dedicado e o mesmo verificador autoritativo da FastAPI, sem consumir o rate limit público compartilhado.

## 2026-09-06 — FEAT-INTEGRITY-001 auditoria antecipada em todos os estados

- A auditoria de integridade passa a abrir cada ciclo do daemon e varre todos os mercados com definição nativa assinada, inclusive abertos, fechados, resolvidos, selados e cancelados.
- O alerta entra na fila na primeira passagem posterior à divergência, sem depender de `seal_due_at` ou da execução de uma selagem.

## 2026-09-06 — FEAT-INTEGRITY-001 comprovantes persistentes e auditoria pelo daemon

- Comprovantes do titular permanecem acessiveis no detalhe durante `open`, `locked`, `resolved`, `sealed` e `canceled`; o Seal adiciona a prova Merkle sem esconder recibos anteriores.
- Cards finalizados usam o CTA `Resultado` e apresentam compartilhamento como icone secundario acessivel.
- O daemon audita definicao, resultado, compromissos, Merkle, Seal e cadeia global, criando alertas operacionais `high` deduplicados na fila `Integridade` sem alterar o ledger.

## 2026-09-06 — FEAT-INTEGRITY-001 comprovantes em modal por ação

- O comprovante assinado abre em modal compacto no detalhe do mercado, com a página completa preservada para navegação sem JavaScript.
- Entrada inicial, reforços e revisões ficam listados como comprovantes independentes, identificados por tipo e sequência, sem substituir assinaturas anteriores.

## 2026-09-06 — FEAT-INTEGRITY-001 confirmação de assinatura e copy compacta

- O modal de verificação remove a ressalva destacada e mantém o foco em como hash, assinatura e histórico conectado detectam alterações.
- Alertas da cadeia global que não invalidam as provas específicas do mercado ficam no contrato e na auditoria operacional, sem parecer falha do mercado nas experiências públicas web/mobile.
- Cards resolvidos e selados voltam a usar o CTA familiar `Ver resolução`.
- A confirmação de previsão, reforço ou revisão passa a informar que o comprovante foi assinado e oferece acesso ao recibo individual emitido pela FastAPI.

## 2026-09-06 — FEAT-INTEGRITY-001 semântica e verificação reforçadas

- Estados visuais agora distinguem registro em curso, prazo/retry operacional, etapa não aplicável e diferença criptográfica, com cores coerentes em web, Admin Ops e mobile.
- A verificação compara definição e resultado atuais aos snapshots assinados e valida compromissos, folhas/provas Merkle, Seal, eventos do mercado e cadeia global.
- Chaves públicas históricas passam a ser preservadas em registro append-only, mantendo a verificação após rotação ou reinício local sem armazenar chave privada.

## 2026-09-06 — FEAT-INTEGRITY-001 método criptográfico compacto

- A primeira leitura passou a resumir hash, assinatura criptográfica e encadeamento sem expandir a página com nova seção longa.
- A comunicação diferencia detecção de manipulação de impedimento absoluto e informa que a chave privada permanece protegida.
- O botão textual redundante foi removido do detalhe; o escudo sobre a thumbnail permanece como acionador acessível da verificação.

## 2026-09-06 — FEAT-INTEGRITY-001 clareza da verificação pública

- O modal de integridade passou a responder primeiro se alguma alteração indevida foi detectada e para que a conferência existe.
- Publicação, previsões, resultado e finalização passaram a formar uma linha do tempo em linguagem comum, com estado coerente para mercado registrado, resultado pendente e histórico selado.
- A experiência agora explica o efeito de uma alteração, os limites da prova e a analogia de impressão digital antes de apresentar hashes, chave e protocolo.

## 2026-09-05 — FEAT-INTEGRITY-001 Ledger Criptográfico de Integridade

- A sinalização web foi refinada para preservar a thumbnail e usar um selo iconizado sobreposto no canto superior direito, disponível também no detalhe do mercado.
- A verificação web passou a abrir em modal compartilhado, responsivo e acessível, com conteúdo leigo antes dos detalhes técnicos e rota completa mantida como fallback.
- Publicação passa a registrar definição canônica assinada; previsão inicial, reforço e revisão geram comprovantes pseudonimizados na mesma transação.
- Ciclo de mercado ganhou `seal_due_at` e estado terminal `sealed`, com reversão auditável antes do prazo e selagem idempotente pelo daemon usando Merkle Tree.
- Ledger global encadeado e assinado ganhou proteção append-only no PostgreSQL; correções pós-selagem são novos eventos e nunca reescrevem a prova anterior.
- FastAPI/OpenAPI expõem resumo, verificação, chave pública, pacote e comprovante individual; Django e Flutter apenas consomem e apresentam esses contratos.
- Cards web/mobile distinguem “Definição registrada” de “Histórico verificável”; páginas institucionais explicam limites sem alegar blockchain pública, descentralização ou imutabilidade absoluta.
- Produção exige AWS KMS Ed25519 e segredo de pseudonimização; signer efêmero permanece restrito a desenvolvimento/testes.

## 2026-08-29 — FEAT-MARKET-001 compactação dos cards do feed web

- Cards do feed/home mantêm a classificação por categoria, subcategoria, evento e status em uma faixa própria abaixo do cabeçalho de título/miniatura, aproveitando a largura disponível do card.
- A leitura compacta remove volume reservado, participantes, `close_label`, fonte e a mensagem redundante `Crédito distribuído` de cards resolvidos; o prazo relativo `closes_in`, o indicador visual, consenso, opções, CTAs e ações sociais permanecem. Cards resolvidos exibem `Consenso final` como rótulo discreto do gráfico/opções, sem antecipar o resultado vencedor.
- Não houve alteração em FastAPI, OpenAPI, persistência ou app mobile; a mudança é somente de apresentação web e é coberta por regressão de renderização.

## 2026-06-20 — FEAT-MOBILE-001 novo AAB Google Play Closed testing

- Versão mobile avançada para `1.0.10+11` para nova rodada de Google Play Closed testing, sem mudança funcional e preservando o APK público direto `1.0.7 (8)`; `versionCode 10` foi descartado porque o Play Console informou que já tinha sido usado.
- AAB assinado gerado com bases de produção, SHA-256 `6592ccd9e65d323127bbbf2050866f58f050d85bbe9303280182237570e0d476` e tamanho `57383320` bytes.
- Release name definido como `1.0.10+11 - Closed testing Android` e release notes `pt-BR` prontas para Play Console.

## 2026-06-20 — FEAT-MOBILE-001 compatibilidade mobile por build

- FastAPI passou a enriquecer `GET /health` com bloco `mobile`, incluindo build/versão instalados por headers, release Android ativa, build mínimo/recomendado, flags de atualização e URL de download.
- Clientes mobile passam a enviar `X-GoTrendLabs-App-Version` e `X-GoTrendLabs-App-Build` em todas as chamadas, mantendo `versionCode`/build number como autoridade de compatibilidade.
- Middleware FastAPI bloqueia clientes mobile abaixo de `min_supported_android_build` com `426 code=app_update_required`, preservando `/health` isento e mantendo manutenção mobile como `503 code=mobile_maintenance`.
- Migration de compatibilidade concede leitura runtime para a FastAPI em `gotrendlabs_site_config` e `gotrendlabs_mobile_app_releases`, evitando falha aberta quando a política buscar a release Android ativa em produção.
- Admin Ops Config ganhou seção `Compatibilidade mobile` com build mínimo, build recomendado e mensagem obrigatória, validação contra a release Android ativa, alteração restrita a superuser e auditoria `mobile.compatibility_update`.
- Flutter ampliou o gate inicial para mostrar tela obrigatória de atualização quando `mobile.update_required=true` e o `ApiClient` promove qualquer `426 code=app_update_required` para o estado global de atualização obrigatória; update opcional não bloqueia o shell.
- O projeto continua com API atual única, sem `/api/v1` ou `/api/v2`; campos novos opcionais e mudanças backend/web/admin-only não forçam atualização mobile.

## 2026-06-18 — FEAT-MOBILE-001 preparação Google Play Closed testing

- Versão mobile avançada para `1.0.8+9` para o primeiro AAB de Google Play Closed testing, preservando o APK público direto `1.0.7 (8)` até uma publicação própria desse canal.
- Documentado o build `flutter build appbundle --release` com bases de produção, signing local e artefato esperado `build/app/outputs/bundle/release/app-release.aab`.
- Release name definido como `1.0.8+9 - Closed testing Android` e release notes `pt-BR` prontas para Play Console.
- Critérios de aceite mobile passaram a cobrir AAB de Closed testing, hash/tamanho registrados e separação entre canal Google Play e canal APK direto.

## 2026-06-18 — FEAT-MOBILE-001 desempenho autenticado

- FastAPI ganhou `GET /users/me/performance`, contrato autenticado agregado para placar, historico de resolucoes e progressao do usuario logado.
- O app mobile ganhou tela `Desempenho`, acessivel pelo menu e pelo Perfil, sem virar nova aba da bottom navigation.
- A tela usa linguagem de evolucao preditiva, reputacao, resolucao auditavel e GT₵ educativo, sem calcular reputacao, resultado, ranking ou badges no Flutter.
- Copy final da tela remove termos tecnicos para usuario final e usa labels simples de resolucao, como `Acertou` e `Não acertou`.
- Desempenho passou a reconsultar a FastAPI ao abrir a tela, voltar do background, usar pull-to-refresh e apos confirmacoes de previsao/posicao.

## 2026-06-18 — FEAT-MOBILE-001 ajustes de perfil e mesa autenticada

- Campo mobile `Data de nascimento` no perfil passou a aceitar digitacao apenas de numeros com barras automaticas em `DD/MM/AAAA`, preservando envio `YYYY-MM-DD` para a FastAPI.
- Recorte `Posições` em `Mercados` passou a usar `viewer_position.has_position` como fonte de verdade de posicao ativa, sem listar mercados onde o usuario tem apenas participacao historica.
- Atalho `Sua mesa` em `Hoje` passou a contar posicoes ativas por `viewer_position.has_position` e substituiu o contador ambiguo `Encerram` por `Abertas`, restrito a posicoes ativas em mercados abertos.
- Testes Flutter cobrem o formatter de data, payload normalizado de perfil e a regressao de mesa em que `viewer_has_prediction=true` sem posicao ativa nao deve entrar em `Posições`.

## 2026-06-18 — FEAT-MOBILE-001 limpeza de perfil, contribuição e wallet

- Perfil mobile autenticado passou a exibir email, data de nascimento e bio em uma seção privada, com edição em bottom sheet e data em formato `DD/MM/AAAA`.
- Usuário em login limitado pode corrigir somente o email pelo app e receber nova confirmação; data de nascimento e bio continuam bloqueadas até a confirmação do endereço.
- Feedback e sugestão de mercado no app movem o desafio anti-abuso para depois de `Descrição`/`Contexto`, mantendo token e resposta assinados pela FastAPI.
- Bottom sheets de contribuição deixam de expor termos técnicos como `FastAPI/Admin Ops` para usuários finais.
- Wallet mobile remove a etiqueta `Fila Admin Ops` e os quadros explicativos `Solicitação`, `Revisão` e `Crédito` da recarga controlada, preservando elegibilidade, pendência, histórico e criação via API.

## 2026-06-18 — FEAT-MARKET-001 probabilidade derivada das opções

- `gotrendlabs_markets` deixou de persistir `primary_probability_exact` e `secondary_probability_exact`; a fonte única de consenso passa a ser `gotrendlabs_market_options.probability_exact`.
- `MarketResponse` preserva `primary_probability*` e `secondary_probability*` como campos derivados para compatibilidade com web/mobile; em múltipla escolha, o atalho público usa a opção líder por `probability_exact`, sem alterar a ordem editorial de `options[]`.
- Admin Ops, bootstrap e seeds deixam de enviar/gravar probabilidade agregada separada, evitando cards com percentual diferente do ticket de previsão.

## 2026-06-17 — FEAT-REP-001 requisitos configuráveis de badges

- Badges administráveis passaram a aceitar requisitos adicionais configuráveis por regra, avaliados pela `BadgeAwardEngine` com lógica AND depois da regra principal.
- Requisitos adicionais reutilizam os mesmos tipos de métrica controlados pelo backend, com recorte opcional por categoria/subcategoria/evento e flag `is_active` para não bloquear concessões quando desativados.
- Admin Ops passou a listar, criar, editar e remover requisitos adicionais no formulário de badges, mantendo `Conceder para novas conquistas` como controle da regra principal.
- A badge `Top 10` permanece configurada por `ranking_position <= 10`, mas ganhou requisito adicional `resolved_predictions_count >= 3` e descrição pública alinhada.
- Contratos públicos/mobile de badges não expõem a estrutura de requisitos; a mudança afeta a concessão autoritativa no backend e o contrato administrativo de badges.

## 2026-06-17 — FEAT-AIAGENT-001 limite administrável de comentários IA

- Admin Ops Config ganhou `Comentários IA por mercado`, persistido em `gotrendlabs_site_config.ai_max_comments_per_market`, com default `1`.
- Admin Ops de agentes ganhou override opcional `Comentários IA/mercado do agente`, persistido em `gotrendlabs_ai_agents.max_comments_per_market_override`, para o `analyst` herdar o global quando vazio ou usar limite próprio entre `1..10`.
- O ciclo do agente `analyst` passou a contar comentários visíveis de autores `is_bot=true` antes de chamar a LLM; mercados no limite configurado são pulados e auditados com `market_ai_comment_limit`.
- A auditoria `market_ai_comment_limit` passou a ser agregada quando todos os candidatos avaliados foram bloqueados pelo limite, evitando inflar o painel por mercado a cada ciclo do daemon.
- Cooldown, limites por dia/ciclo e tentativas LLM seguem como proteções adicionais; comentários ocultos/moderados não contam para o limite total por mercado.
- Em produção, duplicados históricos visíveis de IA foram tratados operacionalmente ocultando os comentários extras e preservando o comentário IA visível mais antigo por mercado.

## 2026-06-16 — FEAT-MOBILE-001 ajustes de mercado, alertas e wallet

- FastAPI passou a expor mercado com fechamento automático vencido como efetivamente `locked`/`Fechado` nos contratos públicos e a bloquear preview/criação/reforço/revisão nesses casos, sem exigir regra local no Flutter.
- Mobile passou a abrir a aba `Comunidade` por `/markets/:slug?tab=community` a partir de contadores de comentários e alertas de comentário.
- Mobile passou a invalidar e reconsultar mercados, detalhe, wallet, ledger, recargas e alertas em eventos de consulta reais: entrada em telas críticas, retorno do background, troca para abas dependentes de mercados e pull-to-refresh.
- Ranking mobile passou a invalidar e reconsultar `GET /rankings` ao abrir a tela ativa, voltar do background, tocar na aba, trocar filtros e usar pull-to-refresh, evitando consulta antecipada/duplicada enquanto a tela está apenas montada fora da aba ativa.
- APK Android beta `1.0.7 (8)` publicada em produção no canal direto, com `/app/android/latest.json` apontando para o arquivo ativo e SHA-256 `54822fc7aa84ebad2e923c0af75076ba43f7d73433c918f1a365bcd2d4ffe5ae`.
- Detalhe mobile passou a exibir pergunta/contexto completo fora do hero truncado.
- Ticket de previsão passou a mostrar `Disponível` e `Bloqueado` vindos da wallet da API.
- Wallet mobile passou a priorizar `Disponível` e `Bloqueado`, rebaixando recarga educativa para seção secundária.
- Tela/menu `Insights` foi removido do app enquanto não houver contrato recorrente de backend para essa superfície.

## 2026-06-16 — FEAT-OPSLOG-001 hardening de probes no Caddy

- Caddy de produção passou a responder `404` diretamente para probes comuns de WordPress, PHP, `.env`, `.git` e `vendor` antes que as requests cheguem ao Django.
- O bloqueio preserva `/admin/*` como rota real, cobrindo apenas padrões suspeitos como `/admin/.env` e `/admin/phpinfo.php`.
- A mudança reduz ruído em `gotrendlabs_system_logs` sem alterar Django, FastAPI, banco, Cloudflare ou contratos públicos.

## 2026-06-15 — Publicação mobile de posição e anti-abuso

- PR #82 publicou em `main` a fase mobile de reforço/revisão de posição e o desafio anti-abuso para cadastro, feedback e sugestão de visitantes.
- GitHub Actions `GoTrendLabs CI and Deploy` run `27542726255` concluiu `test` e `deploy` com sucesso.
- Produção respondeu `/api/health` saudável, `/api/anti-abuse/challenge` com `prompt`/`token`/`expires_at`, `/api/openapi.json` com `/anti-abuse/challenge`, `/position-preview` e `/position-actions`, e `/api/markets` com dados públicos.

## 2026-06-14 — FEAT-MOBILE-001 desafio anti-abuso e contribuição mobile

- FastAPI ganhou `GET /anti-abuse/challenge`, retornando desafio simples com token assinado e expiração curta para clientes mobile.
- Payloads de cadastro, sugestão de mercado e feedback passaram a aceitar `anti_abuse_token` e `anti_abuse_answer`, mantendo reCAPTCHA v2 como mecanismo web e validando o desafio mobile apenas no backend.
- App Flutter passou a exibir o desafio dentro do cadastro, feedback e sugestão de mercado para visitantes, sem enviar o usuário para fora do app.
- Feedback e sugestão por visitante agora validam nome/email e mantêm erros visíveis no bottom sheet; usuários autenticados continuam enviando sem desafio.
- `Sugerir mercado` passou a aparecer no menu principal do app, além do Perfil, usando categorias ativas de `GET /taxonomy`.

## 2026-06-14 — FEAT-MOBILE-001 reforço e revisão de posição mobile

- App Flutter passou a interpretar `viewer_position` de `GET /markets/{slug}` e trocar o ticket de previsão inicial por uma mesa de posição quando o usuário já possui posição ativa.
- Mobile passou a consumir `POST /markets/{slug}/position-preview` e `POST /markets/{slug}/position-actions` para reforço/revisão, mantendo `/predict` reservado à primeira previsão.
- Mesa de posição exibe opção ativa, entradas abertas, total ativo, crédito possível agregado, histórico resumido, reforços/revisões restantes e motivos de bloqueio retornados pela FastAPI.
- Reforço mobile mantém a mesma opção ativa, exige preview válido e mostra novo total ativo, reforços restantes e crédito possível calculados pela API.
- Revisão mobile permite apenas opção diferente, exige preview válido e mostra entradas encerradas, penalidade, nova posição estimada, revisões restantes e crédito possível calculados pela API.
- UX mobile passou a apresentar reforço como `Aumentar posição` e revisão como `Trocar escolha`, reduzindo jargão sem alterar os contratos FastAPI `reinforcement`/`revision`.
- Ações de posição no mobile passaram a aparecer como frames fechados por padrão, com resumo e contador/bloqueio no cabeçalho, abrindo somente a ação escolhida pelo usuário.
- Prévia de reforço/revisão com campo `allowed` ausente passou a ser tratada como bloqueada pelo app, exigindo confirmação explícita da FastAPI antes de liberar ação.
- Testes Flutter de repository e widget cobrem chamadas de posição, reforço, revisão com penalidade e bloqueios de backend.

## 2026-06-14 — FEAT-PRED-001 reforço e revisão de posição web-first

- FastAPI ganhou contratos autenticados para prévia e criação de reforço/revisão de posição, mantendo `/predict` reservado à primeira previsão.
- `gotrendlabs_predictions` passou a suportar múltiplas posições auditáveis por usuário/mercado, com `action_type`, sequência e supersedência para posições revisadas.
- Revisão preserva histórico, libera posições antigas, aplica `prediction_revision_penalty` e bloqueia nova posição com o valor restante.
- Mutações de previsão/posição passaram a usar lock transacional por usuário/mercado para impedir concorrência entre primeira previsão, reforços e revisões.
- Auditoria de resolução considera apenas posições `resolved`; posições `revised` permanecem auditáveis no histórico/sparkline sem inflar liquidação.
- Admin Ops Config ganhou seção `Previsões e posições` para ajustar grupos de reforço e revisão, incluindo limite máximo de reforços, limite de revisões, janela de corte, penalidade e mínimos de GT₵ sem deploy.
- Detalhe web de mercado passou a mostrar reforço/revisão para usuários com posição ativa, incluindo resumo das entradas abertas, total afetado pela revisão e custo percentual; mobile passou a consumir os mesmos contratos FastAPI em fase publicada posteriormente pela PR #82.

## 2026-06-13 — FEAT-REP-001 badges conquistadas como propriedade histórica

- Admin Ops separou exibição histórica (`is_active`) de novas concessões (`rule_active`) para badges.
- A ação de pausa de badge agora interrompe somente novas concessões, preservando conquistas já registradas.
- Catálogo público/autenticado continua exibindo badges pausadas para todos, com estado de concessão pausada quando aplicável.
- Ranking e compartilhamento público por token continuam exibindo badges pausadas para quem já conquistou.
- Ocultar a badge com `is_active=false` remove do catálogo, ranking e compartilhamento público sem apagar conquistas persistidas.

## 2026-06-13 — FEAT-MOBILE-001 manutenção mobile independente

- Admin Ops Config ganhou controle separado de `Manutenção do app`, salvo no runtime JSON com mensagem propria, sem acoplar ao modo manutencao web.
- FastAPI passou a enriquecer `GET /health` com `maintenance.mobile_enabled`, `maintenance.mobile_message`, `checks.api` e `checks.database`, mantendo `status: ok` quando saudavel e retornando degradado quando o banco falha.
- O app Flutter envia `X-GoTrendLabs-Client: mobile`, checa `/health` no boot e mostra tela dark-first de manutencao quando a API falha, fica degradada ou o modo mobile esta ativo.
- Durante manutencao mobile, FastAPI bloqueia chamadas mobile nao isentas com `503`/`code=mobile_maintenance`; nao ha excecao por staff ou superuser no app.
- `AuthResponse` e `/auth/session` permanecem sem expor `is_superuser` no contrato publico; o gate mobile usa `GET /health` e a regra autoritativa da API.
- APK Android beta `1.0.5 (6)` publicada em produção no canal direto, com `/app/android/latest.json` apontando para o arquivo ativo e SHA-256 `c061681f2495759cca2d2eaf38282541d4a82fd1309fefb4037f9f4ac0b2109b`.

## 2026-06-13 — FEAT-MOBILE-001 autenticação biométrica local

- App mobile ganhou proteção local para sessões lembradas: com `Lembrar login` ligado e suporte do aparelho, a biometria vem ligada por padrão no login e a reabertura exige biometria ou senha do aparelho antes de ativar o Bearer token persistido.
- O token salvo agora pode ser lido sem ser instalado em memória; cancelamento ou falha do desbloqueio mantém a sessão em estado `Sessão protegida`, sem chamada autenticada e sem apagar o token persistido.
- Login sheet passou a oferecer `Proteger sessão com biometria` ligada por padrão no login e cadastro quando o aparelho suporta autenticação local; quando há sessão lembrada protegida, a tela de entrada mostra `Entrar com biometria`; Perfil ganhou o controle `Proteção local` para ativar/desativar a preferência neste dispositivo.
- Android passou a declarar `USE_BIOMETRIC`, usar `FlutterFragmentActivity`, `minSdk >= 24` e tema AppCompat para o diálogo biométrico; iOS ganhou `NSFaceIDUsageDescription`.
- A mudança não cria endpoint, não altera OpenAPI e não envia dados biométricos ao backend; `/auth/session` continua validando a sessão restaurada.
- APK Android beta `1.0.4 (5)` publicada em produção no canal direto, com `/app/android/latest.json` apontando para o arquivo ativo e SHA-256 `43f8c1184ce7c913070d9bc2c09344a70f2ed8f4c14a12749d8e688d831bc81c`.

## 2026-06-12 — FEAT-NOTIFY-001 / FEAT-MOBILE-001 push FCM real Android

- Admin Ops Push mobile ganhou aba `Dispositivos` para listar devices registrados, status, plataforma, versão/build, hash parcial do token e agregados de entrega, sem expor token bruto.
- App Android passou a inicializar Firebase opcionalmente, aplicar `google-services` apenas quando `google-services.json` local existir e manter o arquivo fora do Git.
- Flutter passou a coletar token FCM somente após autenticação, registrar `PushDevice` pela FastAPI, manter `GTL_PUSH_FAKE_TOKEN` para QA sem entrega real e mostrar estado seguro em `Sobre` sem expor token.
- Android ganhou permissão `POST_NOTIFICATIONS`, canal nativo `gtl_default` e metadado default de FCM para exibir notificações em Android 8+.
- Payloads FCM seguros agora abrem rotas permitidas (`/markets/:slug`, `/wallet`, `/badges`, `/alerts`) e o app busca o estado real na FastAPI ao abrir.
- Daemon de `communications` passou a enviar FCM real via Firebase Admin SDK quando `GOTRENDLABS_PUSH_ENABLED=1`, provider `fcm`, dry-run desligado e `GOTRENDLABS_FCM_CREDENTIALS_JSON` estiver configurado fora do Git/Admin Ops.
- Sender FCM grava `provider_message_id` em sucesso, agenda retry em falhas transitórias e invalida `PushDevice` quando o provedor rejeita token.
- Processamento de `PushDelivery` passou por revisão de segurança operacional: claim em transação curta, envio FCM fora de lock longo e recuperação de entregas antigas em `sending`.
- Contadores/filtros da aba `Dispositivos` em Admin Ops passaram a seguir status mutuamente exclusivo, alinhado ao rótulo renderizado na tabela.
- Defaults seguros continuam `GOTRENDLABS_PUSH_ENABLED=0`, `GOTRENDLABS_PUSH_PROVIDER=none` e `GOTRENDLABS_PUSH_DRY_RUN=1`.

## 2026-06-11 — FEAT-MOBILE-001 feed, ranking e sessão mobile

- Tela `Hoje` passou a destacar apenas mercados abertos e ordenar destaque/tendências por engajamento visual usando campos já retornados por `GET /markets`, sem criar regra de domínio local.
- Cards mobile passaram a exibir prazo restante compacto em barra de regressão/urgência na linha inferior do card, ao lado dos comentários, com cor que evolui conforme o fechamento se aproxima; o detalhe passou a usar hero não navegável, evitando empilhar a mesma rota ao tocar na imagem do mercado.
- Confirmação de previsão passou a usar bottom sheet com `SafeArea` e área rolável para evitar overflow em aparelho físico, viewport compacto ou fonte ampliada.
- Gráfico de consenso mobile passou a renderizar uma linha por opção usando `sparkline_series` da FastAPI.
- Ranking mobile passou a identificar participantes por `@handle` e exibir badges compactas com overflow `+N`, reutilizando `badges` e `badges_total` de `/rankings`.
- Ranking passou a ocupar a segunda aba da bottom navigation no lugar de `Insights`; naquela fatia, `Insights` foi movido para o menu superior.
- Menu superior passou a seguir a ordem Wallet, Badges, Insights, Suporte, Política e segurança, Sobre e Sair; em 2026-06-16, `Insights` foi removido novamente enquanto nao houver contrato recorrente backend.
- Estado de push mobile saiu de `Perfil` e `Alertas` e passou para `Sobre` como item informativo de saúde/configuração do build; push real/FCM continua fora do escopo.
- Mobile passou a incrementar `view_count` ao abrir o detalhe do mercado, alinhando a semântica do web; `share_count` permanece incrementado na ação real de compartilhamento.
- Login mobile ganhou `Lembrar login` ligado por padrão; quando desligado, o token Bearer fica apenas em memória e não é persistido no secure storage.
- Splash Android e header do shell mobile foram refinados para manter `Preveja antes do consenso.` alinhado logo abaixo de `GoTrendLabs`.
- Versão mobile desta fatia definida como `1.0.2+3` para publicação Android beta após merge.
- APK Android beta `1.0.2 (3)` publicada em produção no canal direto, com `/app/android/latest.json` apontando para o arquivo ativo e SHA-256 `ae52faaf0525cd22dd45da3ced89ba6f7f208864da3c7c26384e9a0b0c3337bb`.

## 2026-06-11 — FEAT-AUTH-001 / FEAT-NOTIFY-001 login social e emails críticos

- Login social deixou de ser placeholder e passou a usar OAuth real para Google, Facebook e X, com Django cuidando de start/callback e FastAPI criando/vinculando usuário, sessão e auditoria.
- Vínculo social passou a exigir identidade externa existente ou email verificado pelo provedor para conta já existente, evitando duplicidade silenciosa e vínculo por email não confiável.
- X OAuth2 passou a aceitar conclusão de cadastro com email informado pelo usuário quando o provedor não retorna email, exigindo token pendente assinado pela FastAPI, criando conta limitada e disparando confirmação imediata; identidades X já vinculadas entram direto mesmo sem email no retorno do provedor.
- Emails críticos de autenticação (`user.welcome` em conta nova, `user.email_confirmation` em cadastro/reenvio/mudança de email e `account.password_reset`) passaram a tentar envio imediato após commit, mantendo fallback para outbox/daemon.
- Emails transacionais passaram a receber rodapé institucional automático no renderizador central; o conteúdo do rodapé agora é customizável pelo template especial `system.transactional_footer`, com fallback seguro no código.
- Eventos de produto, como mercado fechado/resolvido e crédito recebido, continuam sendo drenados pelo daemon.

## 2026-06-08 — FEAT-MOBILE-001 identidade nativa do app

- Nome exibido do app iOS ajustado para `GoTrendLabs`, removendo o sufixo técnico `Mobile` do launcher.
- Ícones de launcher iOS e Android foram regenerados a partir do símbolo de constelação do logo do site, mantendo a marca visual alinhada ao web; no iOS, o asset catalog inclui variantes `dark` e `tinted` para evitar adaptação automática ruim do sistema.
- Splash/launch theme Android foi alinhado ao app dark-first, substituindo a tela intermediária branca por uma abertura em fundo escuro com lockup da marca, badge de constelação, tagline e configuração Android 12+ com ícone/branding dedicados.
- A mudança é apenas de branding nativo: contratos FastAPI, OpenAPI, autenticação, regras de domínio e distribuição beta permanecem inalterados.

## 2026-06-08 — FEAT-MOBILE-001 beta Android pelo site

- Adicionado canal publico discreto para download de APK Android beta fora da Google Play, com CTA direto no rodape, nas telas de acesso e nas paginas de compartilhamento quando houver release ativa, e estado "Android em breve" quando nao houver release.
- Adicionado estado `iOS em breve` ao lado do CTA Android, sem link de download nesta etapa.
- Adicionado `/app/android/latest.json` com metadados da release Android ativa para uso futuro pelo app.
- Admin Ops ganhou `/admin-ops/mobile-releases/` para upload de APK, calculo servidor-side de SHA-256/tamanho e ativacao de uma unica release Android por vez.
- APKs ficam em `MEDIA_ROOT/app_releases/android/` e sao servidos por `/media/app_releases/android/...`; APK, keystore, senhas e `android/key.properties` permanecem fora do Git.
- Build Android release passou a exigir signing local via `apps/mobile/android/key.properties`; o exemplo versionado fica em `key.properties.example`.
- Caddy de producao passou a rotear `/api/*` para `fastapi:8001` removendo o prefixo `/api`.
- Build beta documentado com `GTL_API_BASE_URL=https://gotrendlabs.com.br/api`, `GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br` e `GTL_PUSH_FIREBASE_ENABLED=false`.
- Google Play, auto-update no app e envio FCM real seguem fora desta etapa.

## 2026-06-08 — FEAT-NOTIFY-001 / FEAT-MOBILE-001 push mobile noop

- Adicionada fundação de push mobile com `PushDevice`, `PushEventPolicy`, `PushTemplate`, `PushDelivery` e `PushPreference`, mantendo toda push derivada de `gotrendlabs_user_notifications`.
- FastAPI passou a expor endpoints autenticados para registrar/listar/revogar dispositivos e consultar/alterar preferências de push.
- Daemon operacional passou a drenar `PushDelivery` com provider `none`/dry-run, supressão quando desligado e invalidação automática de token rejeitado.
- Admin Ops ganhou `Política de Push` com templates/event policies por evento, fallback visível, preview seguro, logs filtráveis, teste manual por `PushDevice` e saúde de push no Dashboard sem expor token, payload sensível ou segredo FCM.
- A saúde de push no Dashboard foi ajustada para funcionar também no processo FastAPI standalone, inicializando o contexto Django antes de consultar modelos de `communications`.
- Flutter ganhou `features/push` com repository/controller, `NoopPushTokenProvider` e `FakePushTokenProvider` controlado por `GTL_PUSH_FAKE_TOKEN` para QA local; Firebase/dependências reais seguem fora desta fase.
- Defaults seguros: `GOTRENDLABS_PUSH_ENABLED=0`, `GOTRENDLABS_PUSH_PROVIDER=none`, `GOTRENDLABS_PUSH_DRY_RUN=1`.
- OpenAPI, specs mobile/communications, README e critérios de aceite foram atualizados para a fase noop/dry-run.

## 2026-06-08 — FEAT-MOBILE-001 suporte iOS Simulator

- Gerada estrutura iOS Flutter em `apps/mobile/ios`, mantendo o app como cliente da FastAPI e sem alterar contratos, OpenAPI ou regras críticas de domínio.
- `.metadata` passou a registrar Android e iOS como plataformas do projeto mobile.
- README e specs mobile passaram a documentar que o iOS Simulator usa `127.0.0.1` para acessar FastAPI/Django locais, enquanto o emulador Android continua usando `10.0.2.2`.
- Critérios de aceite passaram a separar Android MVP de simulação iOS local, exigindo Xcode completo, CocoaPods e device iOS listado por `flutter devices`.
- Validação local confirmou `flutter doctor -v` sem issues, app abrindo no iPhone 17 e iPhone 17 Pro Max Simulator e telas carregando dados da API local.
- Homologação iOS ampla, TestFlight, App Store, push nativo e QA visual completo seguem fora desta entrega.

## 2026-06-07 — FEAT-MOBILE-001 refresh visual Android

- App Flutter Android recebeu refresh visual dark-first/editorial no tema, shell, cards de mercado, detalhe, ticket de previsão, comunidade, wallet, ranking, alertas, busca, perfil, badges, confiança e bottom sheets.
- Adicionada camada compartilhada de componentes visuais mobile para headers editoriais, superfícies, métricas, pills, skeletons e estados vazios/erro.
- Tela `Mercados` passou a ter recortes `Todos`, `Favoritos` e `Posições`, filtrando pelos flags autenticados `viewer_has_favorite` e `viewer_has_prediction` retornados pela FastAPI.
- Tela `Hoje` passou a exibir `Sua mesa` para usuários autenticados com atalhos para posições, favoritos e mercados com posição em fechamento, sem criar regra de domínio local.
- Cards de mercado passaram a sinalizar quando o usuário já possui posição ou favorito naquele mercado.
- Adicionada tela mobile `Sobre`, acessível pelo menu e pelo perfil, com versão/build, saúde da API, dados mínimos da sessão e cópia de diagnóstico sem token, segredo ou endereço de API.
- A mudança é somente UX/UI: contratos FastAPI, OpenAPI, autenticação e regras críticas de domínio permanecem inalterados e autoritativos no backend.
- Critérios de QA visual mobile foram atualizados para exigir consistência do design system nas telas principais e secundárias.
- Status de implementação: `parcial`.

## 2026-06-07 — FEAT-MOBILE-001 MVP Flutter Android

- Criado projeto Flutter em `apps/mobile` para Android, com tema dark-first GoTrendLabs e bottom navigation inicial `Hoje`, `Insights`, `Mercados`, `Alertas`, `Busca`; em 2026-06-16, `Insights` deixou de ser superficie ativa.
- Feed, browse, busca e detalhe de mercado consomem a FastAPI local; o emulador usa `http://10.0.2.2:8001`.
- Auth mobile v1 usa Bearer simples retornado pela FastAPI e armazenado em secure storage, sem refresh token nesta fatia.
- Favoritos, curtidas, comentários, preview e criação de previsão chamam apenas endpoints backend; o app não calcula saldo, probabilidade, payout, reputação, badges ou resolução como fonte de verdade.
- Wallet, perfil, ranking, badges e alertas foram implementados como leitura da API.
- Perfil mobile passou a expor catalogo de badges, imagens de badges via `/media`, convite por referral, atalhos com icones para wallet/ranking/sair e forms de suporte/sugestao alinhados a web.
- Sugestao de mercado mobile passou a carregar categorias ativas de `GET /taxonomy`; feedback mobile passou a usar as opcoes publicas da web sem seletor de prioridade.
- Cards de mercado mobile passaram a resolver midia pelo web base, sem gerar iniciais locais de categoria nem sobrepor `thumb` quando `image_url` existir; fallback visual permanece apenas de apresentacao.
- Ticket de previsao mobile passou a espelhar o preview web com `Opcao escolhida`, `Credito possivel se acertar` e `Credito reservado`, atualizando o retorno via `/prediction-preview` com debounce ao selecionar opcao ou mover o controle.
- Wallet mobile ganhou recarga controlada com elegibilidade, pendencia, historico e solicitacao por `/users/me/wallet/recharge-requests`; o contrato passou a expor `available_gtl`, `min_balance_gtl` e `eligible`, mantendo o `POST` como autoridade de dominio.
- Ranking mobile passou a carregar filtros de categoria, subcategoria e evento a partir de `/rankings`, como na web.
- Mobile passou a expor `Politica de uso`, `Conceitos` e `Seguranca` em tela publica de confianca, acessivel pelo menu e perfil.
- Mensagens de erro mobile passaram a traduzir validacoes FastAPI comuns para copy final, evitando payload tecnico na UI.
- Validações locais: `flutter analyze`, `flutter test`, `flutter doctor -v`, `flutter build apk --debug`, `python manage.py check`, teste backend focado e `packages/contracts/export_openapi.py --check`.

## 2026-06-07 — FEAT-MOBILE-001 specs e skills mobile

- Criadas specs iniciais do app Flutter Android: arquitetura, contratos FastAPI, MVP, UX dark-first e critérios de aceite.
- A UX mobile incorpora as imagens de inspiração fornecidas pelo usuário como direção de padrões, sem copiar marca, naming, textos ou layout literal.
- Criadas skills locais para governança mobile: arquitetura, UX, contratos API, testes, implementação Flutter e docs/memória.
- `apps/mobile/README.md`, `tools/skills/gotrendlabs/README.md`, status, integration map, known gaps e workflow foram alinhados.
- Status de implementação: `nao_iniciada`; o ambiente Flutter/Android está preparado, mas o projeto Flutter ainda não foi criado.

## 2026-06-07 — Dashboard administrativo de contratos

- Admin Ops ganhou tela `Contratos` em `/admin-ops/contracts/`, com linha do tempo read-only para organizar mercados ativos e pendentes.
- A timeline usa `created_at` como início, `close_at` como fechamento previsto, `resolved_at` quando existir e linha pontilhada para o dia atual.
- A leitura operacional foi refinada para painel de fases (`Criação`, `Operação`, `Fechamento`, `Resolução`) com legenda no topo, marcos de trilho diferenciando passado/hoje/futuro, alerta visual para fechamento próximo/atrasado e carregamento em blocos de 10.
- A tela reutiliza `GET /admin/markets`, sem novo endpoint FastAPI, migration ou entidade de domínio.
- Specs de Admin Ops e Backend API foram alinhadas para documentar o uso operacional do contrato administrativo existente.

## 2026-06-07 — Organização de templates e assets web em `apps/web`

- Templates compartilhados foram movidos de `templates/` para `apps/web/templates/`.
- Assets compartilhados foram movidos de `static/` para `apps/web/static/`.
- `TEMPLATES["DIRS"]` e `STATICFILES_DIRS` passaram a apontar para os novos caminhos.
- Apps Django permanecem nos caminhos históricos nesta fatia para preservar labels, imports e migrations.

## 2026-06-07 — Organização operacional em `ops/`

- Deploy de produção foi movido de `deploy/production/` para `ops/deploy/production/`, mantendo Compose, Caddyfile, runbook e `deploy.sh` juntos.
- Scripts operacionais foram movidos de `scripts/ops/` para `ops/scripts/`.
- Compose local passou a reservar estado Postgres em `ops/docker/postgres/data/`, mantendo o diretório ignorado pelo Git e preservando dados locais antigos fora da migração.
- Workflow GitHub Actions, README, specs, skills e testes passaram a apontar para os novos caminhos operacionais.
- GitHub Actions passou a atualizar o checkout remoto na EC2 antes de chamar o script em `ops/deploy/production/`, cobrindo a transição em que o checkout existente ainda não tinha o caminho novo.

## 2026-06-07 — Organização da FastAPI em `apps/api`

- Pacote FastAPI movido de `backend_api/` para `apps/api/backend_api/`, preservando a autoridade de domínio e sem alterar contratos funcionais.
- Imports internos, comandos de daemon/suporte, testes e patches passaram a usar o namespace `apps.api.backend_api`.
- Comando local passou a usar `python -m uvicorn apps.api.backend_api.main:app`; Compose de produção aponta para `uvicorn apps.api.backend_api.main:app`.
- README, specs de arquitetura, integração e skills locais foram alinhados ao novo caminho.

## 2026-06-06 — Auditoria de seguranca local

- Autenticacao/sessao passaram a ter hardening automatico em modo producao, redirects `next` validados como locais e rate limit in-memory nos endpoints publicos sensiveis.
- Admin Ops passou a validar uploads de imagem por conteudo real, limitar tamanho e regravar PNG antes de persistir em `media`.
- Caddy passou a servir `/media/*` com `nosniff`, CSP restritiva e cache curto; relatório `docs/audits/security-audit-2026-06-06.md` registra achados, evidencias e pendencias.

## 2026-06-06 — FEAT-OPSLOG-001 cadência do daemon em produção

- Docker Compose de produção passou a executar `run_gotrendlabs_daemon` com intervalo de 300 segundos.
- Defaults de saúde do daemon passaram para 7 minutos até `Atrasado` e 21 minutos até `Sem sinal`, mantendo folga para ciclos de 5 minutos com IA, prune, emails e fechamento de mercados.
- Specs de scheduler/deploy passaram a documentar a cadência operacional e os limites padrão do Dashboard Admin Ops.

## 2026-06-06 — Polimento de experiência e auditoria

- Perfil autenticado passou a renderizar `@` como prefixo fixo do identificador, aceitando edição apenas do nome do handle e preservando normalização backend.
- Retorno contextual público passou de `← Feed` para `← Voltar`, usando origem local confiável quando disponível e fallback para o feed.
- Política de uso removeu a seção pública “O MVP ainda está evoluindo.”, mantendo a versão vigente.
- Cards de mercado passaram a expor fechamento em formato legível e a normalizar labels ISO vindos da API/fallback local.
- Auditoria IA no Admin Ops passou a explicar tipo, status e motivo no browse e detalhe, preservando códigos técnicos no detalhe operacional.

## 2026-06-06 — FEAT-AUTH-001 / FEAT-WALLET-001 indicação bonificada

- Cadastro FastAPI passou a aceitar `referral_code` opcional e creditar `reward_referral` ao indicador comum ativo quando a conta convidada é criada por código válido.
- Criadas tabelas `gotrendlabs_referral_codes` e `gotrendlabs_referral_rewards` para código estável, recompensa idempotente por convidado e vínculo com ledger.
- Admin Ops Config ganhou `referral_bonus_gtl`, com default `200 GT₵` e valor `0` como bônus desativado.
- Carteira e perfil autenticado passaram a renderizar card contextual de indicação com link copiável/compartilhável; compartilhamentos de mercado/resultado por usuário logado podem carregar `ref`.
- Django captura `?ref=` em sessão e preserva o código até o cadastro, sem criar página isolada de convite.

## 2026-06-06 — FEAT-SUGGEST-001 taxonomia na sugestão

- Tela pública/autenticada de sugerir mercado passou a carregar categorias ativas da taxonomia administrada em Admin Ops, com fallback local de desenvolvimento.
- FastAPI passou a expor `GET /taxonomy` sem exigir staff, retornando apenas taxonomia ativa para formulários públicos.
- `POST /suggestions` passou a validar a categoria contra categorias ativas cadastradas e preservar o nome canônico no item da fila editorial.

## 2026-06-05 — FEAT-AUTH-001 navegação administrativa

- Entrada administrativa no chip do usuário passou de `Admin` para `Painel Administrativo`, aparece como primeira ação para staff/superusers e recebe sinalização visual própria de acesso restrito.

## 2026-06-05 — FEAT-NOTIFY-001 emails transacionais

- Adicionado app `communications` com `EmailTemplate`, `EmailDelivery` e `EmailConfirmationToken`.
- Templates transacionais por chave/idioma passaram a ser editáveis no Admin Ops, com seeds para confirmação de email, recuperação de senha, mercado fechado/resolvido e crédito concedido.
- Cadastro e alteração de email passam a emitir link expirável de confirmação; contas não confirmadas entram em login limitado até confirmar o endereço.
- Recuperação de senha pública passou a enfileirar email transacional e não expõe mais `reset_url` na resposta pública.
- Fechamento/resolução de mercado para participantes humanos e créditos concedidos passam a criar entregas idempotentes na outbox.
- Daemon operacional passou a processar `EmailDelivery` com retries, status `queued`/`sending`/`sent`/`failed`/`suppressed` e registro de falhas de provider.
- Admin Ops passou a expor `Politica de Emails`, agrupando templates PT-BR, variáveis disponíveis, preview local do email HTML e logs filtráveis de entrega da outbox sem renderizar links sensíveis.
- Status de implementação: `parcial`; event bus dedicado, preferências/cadência avançadas e webhooks de bounce/complaint seguem fora desta fatia.

## 2026-06-09 — FEAT-NOTIFY-001 Resend transacional

- `SiteConfig` passou a registrar `email_provider`, mantendo SMTP genérico como fallback e adicionando Resend como provider de email transacional.
- `communications` passou a enviar emails via Resend API HTTPS quando selecionado, preservando outbox, templates, retries, snapshots renderizados, `provider_message_id` e `Idempotency-Key`.
- Admin Ops passou a exibir segredo Resend separado, seletor de provedor e teste operacional `send_resend_test_email`, sem persistir ou expor `GOTRENDLABS_RESEND_API_KEY`.
- Dashboard/Admin Summary passaram a reportar saúde de email de forma provider-aware.
- Recuperação de senha passou a tentar envio imediato após o commit e a renderizar links absolutos no email, mantendo o daemon como fallback de retry.
- Resend exige domínio remetente verificado no dashboard com SPF/DKIM; DMARC é recomendado. Bounce/complaint webhooks seguem fora desta fatia.

## 2026-06-05 — GoTrendLabs validação final e ajustes de produção

- Rebrand GoTrendLabs validado localmente e em produção com `manage.py check`, `makemigrations --check --dry-run`, suíte completa `129/129`, scans de resíduos em código/schema e checks HTTP/SSL dos domínios públicos.
- FastAPI passou a filtrar URLs locais de thumbnail inexistentes em payloads públicos, preservando a URL crua nos contratos Admin Ops; templates públicos possuem fallback textual quando a imagem falha no navegador.
- Docker Compose de produção passou a montar `mediafiles` também no serviço FastAPI, permitindo que a API valide existência de `/media/...`; volume `gotrendlabs_mediafiles` foi restaurado com thumbnails/badges.
- Topo do Admin Ops ganhou layout próprio com navegação rolável/empilhável em larguras intermediárias, evitando sobreposição de `Logs` com alternância de tema e `Ver site público`.
- Templates base público e Admin Ops passaram a declarar favicon SVG da marca GoTrendLabs, com variantes por preferência de tema do navegador e `theme-color` alinhado ao shell visual.
- Produção verificada fora de modo manutenção, com EC2 no commit validado, containers `gotrendlabs-*` em execução, schema ativo sem resíduos antigos e domínios `gotrendlabs.com.br`/`.com` servindo 200 com SSL válido.
- Status de implementação: `parcial`, com rebrand profundo concluído nesta fatia; internacionalização completa por catálogo permanece fora do escopo.

## 2026-06-04 — GoTrendLabs deep rebrand

- Plataforma renomeada para `GoTrendLabs` em produto, código, docs, deploy, templates, comandos e skills locais.
- Moeda educativa passou a usar `GTL Credits` e símbolo `GT₵`.
- Contratos técnicos de moeda passaram para o sufixo `_gtl`, substituindo o padrão técnico anterior.
- Tabelas ativas passam a usar prefixo `gotrendlabs_*`, com migrations de rename para preservar dados.
- Variáveis operacionais da marca passaram para `GOTRENDLABS_*` e domínio padrão `gotrendlabs.com.br`.
- Status de implementação: `parcial` até conclusão de testes e mutações externas GitHub/AWS.

## 2026-05-28 — FEAT-MARKET-001 linguagem pública e home simplificada

- Home pública passou a priorizar o grid de mercados, removendo hero narrativo, blocos laterais e progressão da primeira dobra.
- Copy pública foi alinhada para tom claro, social e confiável, incluindo `Prever`, `Em apuração`, `carteira educativa`, `crédito reservado`, `GT₵ reservadas` e microcopy de segurança sem dinheiro real.
- Cards do feed passaram a preservar ações na mesma linha em mobile, usar `NÃO` na camada pública e diferenciar `Prever`, `Em apuração` e `Ver resolução` por status.
- Páginas públicas de login, cadastro, badges, compartilhamento, sugestões, feedback, conceitos, segurança e detalhe receberam ajustes de linguagem sem alterar models, migrations, seeds ou schema.
- Status de implementação: `parcial`.

## 2026-05-24 — FEAT-OPSLOG-001 / FEAT-AIAGENT-001 retenção configurável

- Admin Ops Config passou a persistir retenção separada para logs técnicos e auditoria IA em `gotrendlabs_site_config`.
- Prune do daemon passou a aplicar o prazo atual por `created_at` para `gotrendlabs_system_logs` e `gotrendlabs_ai_agent_actions`, afetando também registros antigos.
- Comando operacional de prune passou a reportar logs técnicos e ações de auditoria IA removidos.
- Status de implementação: `parcial`.

## 2026-05-24 — FEAT-AUTH-001 progressão de operadores e reset administrativo

- Home autenticada passou a exibir `Sua progressão` também para `staff`/`superuser`, preservando exclusão do ranking público e exibindo estado neutro quando `ranking_position=0`.
- FastAPI passou a expor `POST /admin/users/{user_id}/password-reset`, gerando link de recuperação para conta ativa com nota operacional, auth event e auditoria `user.password_reset_request`.
- Reset administrativo bloqueia autoação, permite `staff` apenas para usuários comuns e exige `superuser` para alvos `staff`/`superuser`.
- Admin Ops passou a renderizar ação de geração de link no detalhe do usuário e exibir o link como campo read-only para envio ao usuário, evitando clique do operador logado.
- Testes cobrem contrato backend, permissões, auditoria, sessão preservada até confirmação, renderização Admin Ops e progressão de operador na home.
- Status de implementação: `parcial`.

## 2026-05-24 — FEAT-REP-001 badges no ranking e filtro por evento

- `GET /rankings` passou a retornar resumo público de badges ativas conquistadas por usuário ranqueado, limitado a 3 itens visíveis e `badges_total` para overflow visual.
- Ranking web passou a renderizar badges após o handle do usuário, preservando o handle como identificação principal da linha e resumindo excedentes como `+N`.
- Ranking público passou a aceitar filtro `event` quando `category` e `subcategory` estão selecionados; taxonomia do ranking agora inclui eventos por subcategoria.
- Django continua consumindo `GET /rankings` como fonte autoritativa e apenas normaliza dados de apresentação, sem calcular reputação ou elegibilidade de badges.
- Testes cobrem ranking global/temático/evento, badges ativas/inativas, payload legado sem badges, renderização web e preservação de filtros no `Carregar mais`.
- Status de implementação: `parcial`.

## 2026-05-24 — FEAT-AIAGENT-001 cobertura do ciclo IA

- Ciclo de comentários IA passou a avaliar lista configurável de mercados candidatos por ciclo, com default de 200 candidatos.
- Admin Ops passou a expor limite de tentativas LLM por ciclo de comentário, default 3, separado do número máximo de comentários publicados.
- Fallback de comentário tenta próximo mercado quando a LLM retorna `should_publish=false` ou texto inválido, mas para em erro real de provedor para controlar custo.
- Saúde IA passou a considerar recuperação após ciclo bem-sucedido, sem manter status visual de erro por falhas históricas já superadas.
- Prompt de comentário IA foi versionado para `gotrendlabs-ai-agent-v4` e passou a exigir cautela factual: sem upgrades, eventos, números, anúncios ou fontes específicas fora do contexto do mercado, usando linguagem condicional para inferências.

## 2026-05-23 — FEAT-AIAGENT-001 agentes IA oficiais

- Criado app `agents` com agentes oficiais vinculados a usuários `is_bot=true` e auditoria de ações IA.
- Configuração operacional de IA foi adicionada a `gotrendlabs_site_config`, mantendo o segredo do provedor LLM fora do banco (`OPENAI_API_KEY` ou `AWS_BEARER_TOKEN_BEDROCK`).
- Daemon passou a executar ciclo IA isolado e a registrar resumo de comentários, previsões, skips e erros.
- Comentários de bot expõem selo `IA oficial`; rankings, badges e reputação pública excluem bots.
- Mercado sem participação humana passa a ser cancelado no fechamento automático, com refund de previsões abertas.
- Admin Ops passou a oferecer gestão visual de agentes, edição de parâmetros IA, saúde técnica, auditoria paginada com filtro por motivo e detalhe operacional das ações.
- Browse administrativo de mercados passou a permitir busca textual, exibir participantes e o editor passou a mostrar participantes humanos/bots/total operacional em seção própria.

Use este arquivo para registrar mudanças relevantes por feature, com foco em impacto técnico e rastreabilidade para a IA.

## Modelo de entrada

```md
## FEAT-XXX

### YYYY-MM-DD - vX.Y
- mudança principal
- contratos afetados
- status de implementação resultante
```

## FEAT-NOTIFY-001

### 2026-05-23 - v0.2
- `gotrendlabs_user_notifications` passou a persistir inbox in-app com idempotência por destinatário e `source_key`
- FastAPI passou a expor `GET /users/me/notifications` e `POST /users/me/notifications/read-all`
- ações sociais notificam participantes humanos de mercados em que fizeram previsão: nova previsão, curtida de mercado, comentário em mercado e curtida em comentário próprio
- eventos sistêmicos notificam o beneficiário direto: crédito recebido, mercado participado fechado/resolvido e badge recebida
- home/feed e detalhe do mercado passaram a exibir `comment_count` público de comentários `visible`
- Django renderiza sino com contador/dropdown, botão desabilitado para visitantes, fallback local read-only em desenvolvimento e links contextuais para mercado, comentários, wallet e badges
- status de implementação: `parcial`

## FEAT-OPSLOG-001

### 2026-05-22 - v0.9
- Dashboard Admin Ops passou a exibir o indicador `Backend API` em Saúde técnica, validado por chamada read-only ao `GET /health`
- o healthcheck é consultado independentemente de `/admin/dashboard-summary`, preservando renderização do resumo quando apenas o health falha
- status de implementação: `parcial`

### 2026-05-21 - v0.8
- workflow `.github/workflows/deploy.yml` passou a validar `ENABLE_PROD_DEPLOY`, `AWS_GITHUB_ACTIONS_ROLE_ARN`, `AWS_EC2_INSTANCE_ID` e `AWS_REGION` antes de tentar assumir a role AWS
- deploy GitHub Actions passou a priorizar repository variables para ARN da role e instance id, mantendo fallback temporario para secrets legados
- etapa `Verify assumed AWS identity` passou a executar `aws sts get-caller-identity` antes do `ssm send-command`, endurecendo o diagnostico de OIDC no branch `main`
- status de implementação: `parcial`

### 2026-05-21 - v0.7
- infra AWS base passou a ter EC2 ARM gerenciada por SSM, CloudWatch Agent para métricas/logs mínimos de host e alarmes mínimos de EC2/RDS
- RDS PostgreSQL 16 foi provisionado privado, com acesso administrativo via túnel SSM e sem exposição pública de `5432`
- GitHub Actions OIDC foi preparado para deploy via SSM no branch `main`, mantendo `.env.prod` e segredos fora do Git
- status de implementação: `parcial`

### 2026-05-20 - v0.6
- daemon operacional passou a ter empacotamento de produção como serviço dedicado no Docker Compose da EC2
- deploy MVP documenta que apenas um container `daemon` deve rodar por ambiente
- status de implementação: `parcial`

### 2026-05-20 - v0.5
- Admin Ops Config passou a persistir limites de heartbeat do daemon em `gotrendlabs_site_config`
- Dashboard Summary passou a calcular `Ativo`, `Atrasado` e `Sem sinal` com base em `daemon_stale_after_minutes` e `daemon_missing_after_minutes`
- validação administrativa impede limite de `Sem sinal` menor ou igual ao limite de `Atrasado`
- status de implementação: `parcial`

### 2026-05-20 - v0.4
- rotinas de prune de logs e status do daemon passaram a viver em serviço backend reutilizável
- comando `prune_system_logs` deixou de conter regra própria e passou a chamar o backend
- daemon operacional passou a registrar heartbeat, início, falhas, fechamentos e prune em `gotrendlabs_system_logs`
- Dashboard Admin Ops passou a exibir status do daemon a partir do heartbeat calculado pela FastAPI
- status de implementação: `parcial`

### 2026-05-20 - v0.3
- FastAPI passou a expor `GET /admin/dashboard-summary` como contrato staff agregado para saúde operacional da plataforma
- Dashboard Admin Ops passou a renderizar KPIs, ação necessária, saúde técnica, top mercados e eventos administrativos recentes a partir desse contrato
- métricas recentes usam janela de 7 dias e preservam agregações operacionais sem recalcular regras de domínio
- status de implementação: `parcial`

### 2026-05-20 - v0.2
- Admin Ops passou a paginar o browse de logs e preservar filtros entre páginas
- filtro de usuário passou a usar identificador pesquisável por `@handle`, nome, email ou ID, carregando usuários comuns, staff e superusers
- contratos administrativos de logs passaram a expor `user_identifier` para exibição operacional amigável
- detalhe do log remove duplicações visuais de mensagem/request e mantém usuário apenas no card principal
- spec passou a explicitar cobertura de logs técnicos de segurança e fronteira com `gotrendlabs_auth_events`
- status de implementação: `parcial`

### 2026-05-20 - v0.1
- criada spec inicial para logs técnicos de troubleshooting
- adicionada persistência em `gotrendlabs_system_logs` com retenção, redaction e contexto JSON
- FastAPI passou a expor contratos staff para listagem e detalhe de logs
- Django Admin Ops passou a consultar logs técnicos com filtros e tela de detalhe
- status de implementação: `parcial`

## FEAT-AUTH-001

### 2026-05-21 - v0.14
- perfil autenticado passou a priorizar `gotrendlabs_user_profiles.display_name` como fonte real do nome editável, preservando `gotrendlabs_users.first_name` como compatibilidade
- Admin Ops passou a marcar contas controladas por robôs internos via `is_bot`, com filtro, badge e auditoria `user.bot_update`, sem exposição em contratos públicos/autenticados comuns
- ajuste manual de wallet da própria conta passou a ser permitido para `staff`/`superuser`, mantendo nota, ledger e auditoria, enquanto demais autoações sensíveis continuam bloqueadas
- status de implementação: `parcial`

### 2026-05-21 - v0.13
- bootstrap de núcleo de usuário passou a diferenciar usuário comum de operador: contas `staff`/`superuser` não recebem `grant_initial`, reputação pública, badges nem atividade social
- contexto web deixou de exibir reputação/acerto de operadores no chip, perfil, carteira e resumo da home
- testes cobrem que usuário comum mantém bootstrap completo e idempotente, enquanto operador permanece fora de métricas públicas
- status de implementação: `parcial`

### 2026-05-20 - v0.12
- rodapé público passou a ser organizado em quatro colunas: Institucional, Produto, Confiança e Suporte
- links de conta, mercados recorrentes e operações administrativas foram removidos do rodapé público
- Admin Ops passou a aparecer no chip do usuário apenas para contexto autenticado `is_staff` ou `is_superuser`
- status de implementação: `parcial`

### 2026-05-20 - v0.11
- login e cadastro passaram a renderizar botões sociais iconizados para Google, Facebook e X, preservando rótulos acessíveis
- placeholder FastAPI de login social passou a reconhecer `x` junto de `google` e `facebook`, ainda retornando `501` até existir OAuth real
- layout das páginas standalone de auth passou a usar altura natural para evitar espaçamento vertical divergente entre login, cadastro e rodapé
- status de implementação: `parcial`

### 2026-05-20 - v0.10
- telas standalone de autenticação passaram a renderizar o rodapé público compartilhado via partial reutilizável
- `base.html` passou a usar o mesmo componente de rodapé, reduzindo divergência entre páginas públicas comuns e fluxos de auth
- smoke tests passam a validar rodapé em login e cadastro
- status de implementação: `parcial`

### 2026-05-20 - v0.9
- recuperação de senha passou a usar tokens de uso único emitidos pela FastAPI, com confirmação por contrato e revogação de sessões antigas
- telas de recuperação de senha passaram a preservar navegação pública, retorno `← Feed` e alternância de tema
- Admin Ops passou a permitir gestão controlada de `is_staff`/`is_superuser` por superuser, com nota operacional e auditoria `user.roles_update`
- status de implementação: parcial

### 2026-05-19 - v0.8
- detalhe administrativo de usuário passou a exibir badges adquiridas sem recalcular elegibilidade na UI
- formulário de ajuste manual de wallet passou a exigir seleção explícita de direção, sem opção pré-selecionada
- navegação administrativa foi ordenada como Dashboard, Usuários, Categorias, Badge, Mercado, Resolução e Filas
- status de implementação: `parcial`

### 2026-05-19 - v0.7
- Admin Ops passou a ter gestão de usuários com listagem, busca, filtros por status/papel e detalhe operacional amplo
- FastAPI passou a expor contratos staff para detalhe de usuário, desativação/reativação, revogação de sessões e ajuste manual de wallet
- ações administrativas de usuário registram eventos `user.*` em `gotrendlabs_admin_events` e bloqueiam operações perigosas sobre a própria conta do operador
- status de implementação: `parcial`

### 2026-05-19 - v0.6
- login e cadastro passaram a exibir navegação pública compacta para mercados, badges e ranking
- login e cadastro passaram a exibir retorno compacto `← Feed` no primeiro painel de conteúdo, seguindo o padrão das páginas públicas fora da home
- cadastro passou a expor política de uso em modal, mantendo link para página pública completa `/use-policy/`
- painel de cadastro passou a apresentar prévia de onboarding com ticket de mercado, badges bloqueadas e confiança/GT₵ sem dinheiro real
- status de implementação: `parcial`

### 2026-05-19 - v0.5
- perfil autenticado passou a persistir e editar `birth_date` e `sex` opcionais em `gotrendlabs_user_profiles`
- `GET/PATCH /users/me` expõe e atualiza dados privados do perfil; perfil público não expõe email, data de nascimento, sexo nem metadados privados
- Django mantém edição básica inline na própria tela `/profile/`, com reputação em cards e exclusão lógica no painel lateral
- status de implementação: `parcial`

### 2026-05-19 - v0.4
- cadastro passou a aceitar `recaptcha_token` e validar reCAPTCHA v2 no servidor quando configurado
- Django renderiza widget v2 no formulário de cadastro usando `RECAPTCHA_SITE_KEY`
- configuração por ambiente adicionada via `RECAPTCHA_ENABLED`, `RECAPTCHA_SITE_KEY` e `RECAPTCHA_SECRET_KEY`
- status de implementação: `parcial`

### 2026-05-17 - v0.3
- cadastro exige aceite da política de uso e persiste versão/data do aceite
- perfil autenticado permite alterar nome, email, idioma, bio e categoria forte via FastAPI
- adicionada exclusão lógica de conta com `account_status`, `is_active=false`, revogação de sessões e preservação física dos dados
- respostas autenticadas expõem data de criação, último login e status da conta
- status de implementação: `parcial`

### 2026-05-17 - v0.2
- criada camada `backend-api` FastAPI para `POST /auth/register`, `POST /auth/login`, `GET /auth/session`, `POST /auth/logout` e placeholder de login social
- persistência em PostgreSQL com `gotrendlabs_users`, `gotrendlabs_auth_sessions`, `gotrendlabs_external_identities` e `gotrendlabs_auth_events`
- Django deixou de criar/login usuário diretamente e passou a consumir o contrato da API, mantendo apenas token/contexto na sessão web
- testes adicionados para contrato FastAPI de sessão e para fluxo web Django via API
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `i18n-content.md`, `domain-events.md`
- status de implementação: `nao_iniciada`

## FEAT-MARKET-001

### 2026-05-22 - v0.31
- adicionado comando idempotente `seed_crypto_markets_20260522` para aplicar o lote aprovado `Mercado > Cripto` com aviso de subcategoria e eventos Ethereum, Dogecoin e Solana
- adicionadas 3 thumbnails autorais 512x512 para o lote mainstream cripto, mantendo imagens sem texto/logos embutidos
- contratos relacionados: `market-feed.md`
- status de implementação: `parcial`

### 2026-05-22 - v0.30
- cards da home/feed trocaram o indicador circular por uma barra horizontal compacta de prazo, calculada com `created_at` e `close_at`
- detalhe do mercado passou a exibir a thumbnail/ícone encaixada à esquerda do título, preservando os metadados textuais em HTML
- a probabilidade deixou de alimentar visualmente o indicador de tempo; ela permanece nos textos e gráficos próprios de consenso
- contratos relacionados: `market-feed.md`, `frontend-web.md`
- status de implementação: `parcial`

### 2026-05-22 - v0.29
- eventos sem mercados vinculados podem ser excluídos pelo Admin Ops e por `DELETE /admin/categories/{category_slug}/subcategories/{subcategory_slug}/events/{event_slug}`; eventos vinculados continuam protegidos e devem ser bloqueados para preservar histórico
- contratos relacionados: `database.md`, `backend-api.md`, `admin-ops.md`
- status de implementação: `parcial`

### 2026-05-22 - v0.28
- categorias e subcategorias passaram a aceitar `notice` opcional de até 500 caracteres no Admin Ops e em `/admin/taxonomy`
- layout master-detail da taxonomia foi ajustado para abrir formulários como painéis contextuais estáticos, evitando sobreposição visual na gestão
- contratos relacionados: `market-feed.md`, `database.md`, `backend-api.md`, `admin-ops.md`, `frontend-web.md`
- status de implementação: `parcial`

### 2026-05-22 - v0.27
- Admin Ops de taxonomia passou para layout master-detail com categorias na lateral e subcategorias/eventos agrupados no painel principal
- eventos passaram a aceitar `notice` opcional de até 500 caracteres, retornado por `/admin/taxonomy`
- contratos relacionados: `market-feed.md`, `database.md`, `backend-api.md`, `admin-ops.md`, `frontend-web.md`
- status de implementação: `parcial`

### 2026-05-22 - v0.26
- taxonomia de mercado passou a ter terceira camada `evento`, vinculada à subcategoria e gerenciada no Admin Ops
- criação/edição administrativa de mercado seleciona evento ativo da subcategoria; mercados existentes são migrados para evento `Geral`
- `MarketResponse` e cards da home/feed passam a exibir categoria, subcategoria e evento
- contratos relacionados: `market-feed.md`, `market-lifecycle.md`, `database.md`, `backend-api.md`, `admin-ops.md`, `frontend-web.md`
- status de implementação: `parcial`

### 2026-05-22 - v0.25
- skill `gotrendlabs-prediction-markets` passou a aceitar categoria `cripto`, fontes cripto/on-chain e aviso obrigatório `Não caracteriza recomendação de investimento`
- DEV recebeu 3 mercados cripto em `draft` com taxonomia `Cripto`, subcategorias `Preço`, `DeFi / On-chain` e `Meme coins`
- adicionadas 3 thumbnails autorais para os mercados cripto, mantendo imagens sem texto/logos embutidos
- status de implementação: `parcial`

### 2026-05-22 - v0.24
- visitantes passaram a ver a affordance de favorito nos cards da home em estado apagado/readonly
- filtro `Favoritos` e mutação de favoritar/desfavoritar permanecem exclusivos para usuários autenticados
- clique de visitante na affordance mostra aviso de login, sem enviar formulário de mutação
- status de implementação: `parcial`

### 2026-05-21 - v0.23
- migration inicial de mercados deixou de executar seed automático a partir de `data/fixtures/domain.json`
- produção foi alinhada para não manter mercados fixture criados pelo primeiro deploy
- status de implementação: `parcial`

### 2026-05-21 - v0.22
- métrica pública `GT₵ distribuídas` passou a excluir créditos de `staff` e `superuser` no contrato `/stats` e no fallback local da home
- espaçamento visual do bloco `AO VIVO`/destaques da home foi ajustado para reduzir colisão entre rótulo e título
- status de implementação: `parcial`

### 2026-05-21 - v0.21
- adicionadas 27 thumbnails autorais de mercado como imagens puras, quadradas e específicas por evento, usadas via `image_url`
- documentado lote editorial seed de 27 mercados/categorias/subcategorias para retomada operacional e auditoria da fonte de verdade
- guia da skill `gotrendlabs-prediction-markets` passou a registrar que inclusão aprovada cria taxonomia idempotente e mantém mercados em `draft`
- status de implementação: `parcial`

### 2026-05-20 - v0.20
- home passou a exibir métricas públicas de economia educativa com `GT₵ distribuídas` e `GT₵ movimentadas em previsões`
- FastAPI passou a expor `GET /stats` com `open_markets`, `total_predictions`, `distributed_gtl`, `moved_gtl`, `resolution_sla` e `real_money`
- fallback local Django passou a calcular `distributed_gtl` a partir de créditos do ledger e `moved_gtl` a partir de stakes de previsões
- textos visíveis de moeda foram padronizados para `GT₵`, preservando campos e identificadores técnicos `_gtl`
- status de implementação: `parcial`

### 2026-05-20 - v0.19
- título dos cards de mercado passou a ser link para o detalhe, reduzindo atrito de navegação no feed/home e listas que reutilizam o card
- smoke test passa a proteger o link do título para o detalhe do mercado
- status de implementação: `parcial`

### 2026-05-20 - v0.18
- fechamento automático de mercados vencidos com `auto_close_enabled=true` foi centralizado em serviço backend e em entrada própria da `MarketLifecycleEngine`
- comando `run_gotrendlabs_daemon` foi adicionado como processo operacional fino, sem duplicar regra de domínio
- fechamentos automáticos registram `market.lock` com ator sistema/nulo e nota operacional padronizada
- status de implementação: `parcial`

### 2026-05-19 - v0.17
- mercados passaram a persistir `view_count` e `share_count` como contadores operacionais de popularidade sem deduplicação
- contrato público/admin expõe os contadores, e `view_count` passa a guiar a seleção pública de destaque da home e do ticket de cadastro
- Admin Ops lista popularidade por mercado em `Mercados ativos e rascunhos`, com indicadores compactos e ordenação por mais visualizados ou mais compartilhados
- status de implementação: `parcial`

### 2026-05-19 - v0.16
- ticket de onboarding do cadastro passou a usar o mercado publicado não cancelado com maior `view_count`, excluindo `draft` e `canceled`
- quando houver empate ou ausência de visualizações, o ticket de onboarding usa o mercado mais recente por `created_at`
- prévia reutiliza `sparkline_series`, opções e dados serializados do domínio, com fallback local quando a API está indisponível
- status de implementação: `parcial`

### 2026-05-19 - v0.15
- feed público passou a expor recorte rápido `Resolvidos`, filtrando client-side cards já renderizados com `status=resolved`
- hero do feed passou a mostrar `previsões totais` calculadas a partir de previsões persistidas reais, sem janela mensal
- páginas públicas fora da home passaram a usar retorno compacto `← Feed` dentro do primeiro painel, alinhado ao rótulo inicial da tela
- Admin Ops passou a usar apenas a navegação principal no topo, com link de Resolução incluído e sem menu secundário duplicado
- status de implementação: `parcial`

### 2026-05-19 - v0.14
- cards de mercado passaram a usar fallback visual de thumbnail quando `image_url` e `thumb` estão vazios, derivando iniciais de categoria/subcategoria/título
- fallback de thumbnail também é aplicado aos cards de compartilhamento social e imagens Open Graph de mercado/resultado
- curtidas do card foram separadas de reações em comentários; `market_like_count` passa a representar curtidas reais do mercado
- status de implementação: `parcial`

### 2026-05-18 - v0.13
- feed público passou a ter ordenações rápidas client-side por tendência, encerramento, volume, novidade e favoritos editoriais
- cards de mercado passaram a exibir contador compacto de curtidas
- contrato/renderização do feed usa `is_featured`, `market_like_count`, `view_count`, `created_at` e `close_at` para destaque e ordenação visual
- destaque principal do feed prioriza os mercados não cancelados mais visualizados, incluindo resolvidos quando liderarem por popularidade, com mercado mais novo como desempate
- status de implementação: `parcial`

### 2026-05-18 - v0.12
- listagem administrativa "Mercados ativos e rascunhos" removeu o CTA `Ver público`, mantendo apenas `Editar/visualizar`
- acesso à página pública permanece disponível dentro do editor de mercado
- status de implementação: `parcial`

### 2026-05-18 - v0.11
- página inicial/feed público padrão deixou de renderizar mercados cancelados
- endpoint público `GET /markets` sem filtro explícito passou a excluir `draft` e `canceled`
- status de implementação: `parcial`

### 2026-05-18 - v0.10
- browse administrativo de mercados passou a usar fallback local em Postgres quando a FastAPI administrativa retorna erro transitório
- documentado que mudanças de schema com SQL direto exigem reinício do processo FastAPI em ambientes long-running
- status de implementação: `parcial`

### 2026-05-18 - v0.9
- edição administrativa de mercado passou a sincronizar opções sem apagar/recriar opções que já possuem previsões vinculadas
- tentativa de remover opção com previsão vinculada retorna erro de domínio em vez de erro interno
- cliente Django passou a exibir erro de API genérico como falha de requisição, não como falha de autenticação
- status de implementação: `parcial`

### 2026-05-18 - v0.8
- cards do feed passaram a exibir mini gráficos de evolução do consenso com uma linha por opção
- CTA de mercados abertos passou a ser `Prever` também para múltipla escolha
- fallback do Django para feed/categorias passou a hidratar séries visuais e IDs de opção a partir do Postgres local quando a API entrega payload antigo
- status de implementação: `parcial`

### 2026-05-18 - v0.7
- Admin Ops de taxonomia passou a operar em formato de browse objetivo, com filtros por uso/bloqueio e política lateral
- categorias e subcategorias ganharam bloqueio lógico persistido (`is_blocked`, `blocked_at`, `blocked_reason`) em vez de exclusão física
- FastAPI expõe ações staff para bloquear/desbloquear categoria e subcategoria, registrando eventos administrativos
- criação/edição administrativa de mercado rejeita categoria ou subcategoria bloqueada
- status de implementação: `parcial`

### 2026-05-18 - v0.6
- Admin Ops passou a marcar campos obrigatórios e exibir feedback de sucesso ao salvar/publicar/cancelar/fechar mercado
- adicionada ação manual de fechamento para mercados `open`/`scheduled` com `auto_close_enabled=false`
- fechamento manual muda status para `locked` e registra evento `market.lock`
- editor administrativo passou a carregar categoria/subcategoria da taxonomia persistida, mantendo subcategoria vinculada à categoria selecionada
- categoria/subcategoria agora iniciam com opção “Selecione”, sem pré-seleção automática em novo mercado
- ajustado contraste de dark mode no editor de opções e no controle de fechamento automático
- status de implementação: `parcial`

### 2026-05-18 - v0.5
- editor administrativo passou a exigir campos operacionais mínimos antes de salvar mercado
- adicionados `close_at`, `close_timezone`, `auto_close_enabled` e `image_url` ao contrato persistido de mercado
- prévia do card no Admin Ops passou a atualizar conforme preenchimento e upload de thumbnail
- status canônico de mercado passou a ser exibido sem usar rótulos editoriais como status
- rótulo curto de prazo passou a ser derivado automaticamente de `close_at`
- status de implementação: `parcial`

### 2026-05-18 - v0.4
- browse administrativo de mercados passou a filtrar por status via `GET /admin/markets?status=...`
- chips do Django Admin Ops agora refletem filtro ativo e contadores globais por status
- status de implementação: `parcial`

### 2026-05-18 - v0.3
- adicionada primeira fatia real do Admin Ops para mercados e taxonomia
- FastAPI expõe endpoints staff para listar, criar, editar, publicar e cancelar mercados
- Django Admin Ops passou a consumir a API administrativa com bloqueio para guest e usuário comum
- criada auditoria simples em `gotrendlabs_admin_events`
- status de implementação: `parcial`

### 2026-05-17 - v0.2
- criadas tabelas PostgreSQL para categorias, subcategorias, mercados e opções
- adicionado seed inicial idempotente a partir de `data/fixtures/domain.json`
- FastAPI passou a expor `GET /markets` com filtros públicos básicos
- Django passou a consumir a FastAPI para o feed, preservando fixture como fallback
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `market-lifecycle.md`, `i18n-content.md`
- status de implementação: `nao_iniciada`

## FEAT-MARKET-002

### 2026-05-22 - v0.14
- avisos de categoria/subcategoria/evento continuam agrupados em alerta informativo, mas passam a renderizar abaixo de `Critério de resolução` no detalhe/ticket do mercado
- contratos relacionados: `market-feed.md`, `frontend-web.md`
- status de implementação: `parcial`

### 2026-05-22 - v0.13
- `MarketResponse` passou a expor `category_notice` e `subcategory_notice`
- detalhe público e ticket de previsão renderizam avisos informativos de categoria/subcategoria/evento quando preenchidos, sem exibir avisos nos cards da home/feed
- status de implementação: `parcial`

### 2026-05-22 - v0.12
- `MarketResponse` passou a expor `event_notice`
- detalhe público e ticket de previsão renderizam aviso informativo do evento quando preenchido, sem exibir aviso nos cards da home/feed
- status de implementação: `parcial`

### 2026-05-22 - v0.11
- detalhe/previsão pública do mercado passou a exibir o evento junto de categoria e subcategoria
- compartilhamento social/fallback visual passa a considerar o evento quando disponível
- status de implementação: `parcial`

### 2026-05-22 - v0.10
- detalhe de mercado passou a exibir favorito readonly para visitantes e favorito funcional para autenticados
- estado visitante usa o mesmo aviso de login da affordance pública da home, sem formulário de mutação
- status de implementação: `parcial`

### 2026-05-21 - v0.9
- card social de mercado passou a exibir opções/probabilidades com barras discretas de consenso
- CTA editorial `Dispute previsões, construa reputação e ganhe destaque.` passou a direcionar para o detalhe do mercado
- imagem social dinâmica de mercado passou a incluir resumo das opções principais
- status de implementação: `parcial`

### 2026-05-19 - v0.8
- abertura do detalhe público incrementa `view_count` do mercado com fallback local quando a API está indisponível
- controles de compartilhamento de pergunta/resultado incrementam `share_count` via rota leve de tracking, sem bloquear navegação/cópia
- editor administrativo exibe visualizações e compartilhamentos como campos read-only de popularidade operacional
- status de implementação: `parcial`

### 2026-05-19 - v0.7
- rotas web de compartilhamento de pergunta e resultado passaram a expor links por rede, metadados Open Graph/Twitter e imagem social dinâmica
- card social de mercado inclui contexto curto da plataforma e CTA de aquisição: "Dispute previsões, construa reputação e ganhe destaque."
- card social de resultado prioriza pergunta e exibe o resultado imediatamente abaixo como desfecho
- origem pública de compartilhamento pode ser configurada para crawlers sociais; host local exibe aviso de preview não rastreável
- status de implementação: `parcial`

### 2026-05-18 - v0.6
- detalhe do mercado passou a exibir gráfico de evolução do consenso com uma linha por opção
- gráfico de evolução passou a preservar histórico após resolução, considerando previsões `open` e `resolved` e excluindo `canceled`
- mercado resolvido passou a exibir data/hora/timezone da resolução e mensagem personalizada no ticket para usuário que acertou ou errou
- visitantes veem opções e consenso sem controle de stake; usuários com previsão existente veem aviso destacado e controles desabilitados
- fallback local do Django hidrata `option.id`, `sparkline_path` e `sparkline_series` quando a FastAPI está indisponível ou desatualizada
- status de implementação: `parcial`

### 2026-05-18 - v0.5
- documentado que percentuais iniciais das opções ficam persistidos em `gotrendlabs_market_options.probability_exact`
- status de implementação: `parcial`

### 2026-05-18 - v0.4
- formalizada regra de opções por tipo de mercado no admin
- `binary` persiste opções canônicas `SIM`/`NAO` com `50%`/`50%`
- `multiple` aceita duas ou mais opções sem limite máximo fixo e distribui percentuais automaticamente para somar `100%`
- status de implementação: `parcial`

### 2026-05-18 - v0.3
- dados-base do detalhe podem ser mantidos pelo Admin Ops real
- publicação administrativa preserva contrato público de detalhe em `GET /markets/{slug}`
- cancelamento administrativo preserva histórico sem exclusão física
- status de implementação: `parcial`

### 2026-05-17 - v0.2
- detalhe de mercado passou a ser persistido e serializado pela FastAPI em `GET /markets/{slug}`
- contrato mantém opções, probabilidade snapshot, categoria, subcategoria e critérios de resolução compatíveis com os templates
- Django passou a consumir a FastAPI no detalhe e nas páginas de compartilhamento, preservando fallback fixture
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `market-lifecycle.md`, `prediction-payloads.md`, `i18n-content.md`
- status de implementação: `nao_iniciada`

## FEAT-PRED-001

### 2026-05-21 - v0.6
- ticket de previsão em mercado aberto passou a iniciar sem opção pré-selecionada e usa radio obrigatório nativo para evitar confirmação ambígua
- UI do ticket passou a orientar seleção explícita com chamada visual discreta antes das opções
- usuário autenticado sem saldo disponível vê estado somente leitura com indicação de saldo indisponível e CTA para wallet
- status de implementação: `parcial`

### 2026-05-19 - v0.5
- prévia de retorno da previsão passou a ter contrato FastAPI sem efeito colateral
- fallback local mutável de criação de previsão no Django foi removido; falha da API não cria previsão nem altera wallet/ledger
- status de implementação: `parcial`

### 2026-05-18 - v0.4
- adicionados campos decimais para probabilidade real em mercado, opções e probabilidade de entrada da previsão
- colunas inteiras redundantes foram removidas; `probability` permanece apenas como campo derivado no contrato de leitura
- mercados de múltipla escolha distribuem `100 / quantidade_de_opções` igualmente, sem sobra artificial para a primeira opção
- `potential_payout` passa a usar a probabilidade decimal vigente antes da previsão
- status de implementação: `parcial`

### 2026-05-18 - v0.3
- séries visuais de consenso passaram a ser derivadas de `gotrendlabs_predictions` ordenadas por criação
- mercados binários e múltipla escolha expõem evolução por opção para cards e detalhe
- adicionado fallback local de confirmação/persistência quando a FastAPI separada está indisponível no ambiente de desenvolvimento
- testes cobrem confirmação local, payload antigo sem IDs/séries e hidratação visual dos cards
- status de implementação: `parcial`

### 2026-05-18 - v0.2
- adicionada primeira mutação real de previsão em `POST /markets/{slug}/predict`
- decisão de MVP: permitir apenas uma previsão por usuário em cada mercado
- stake positivo sem teto fixo é limitado pelo saldo disponível e gera `prediction_stake_lock`
- probabilidades do mercado são recalculadas com peso sintético base e peso `reputacao * stake`
- Django passou a confirmar previsão via FastAPI e exibir sucesso/erros de domínio
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `prediction-payloads.md`, `wallet-ledger.md`, `market-lifecycle.md`
- status de implementação: `nao_iniciada`

## FEAT-RES-001

### 2026-05-20 - v0.4
- ciclo operacional de mercado foi centralizado na `MarketLifecycleEngine`, mantendo handlers HTTP apenas com autenticação, transação, chamada da engine e serialização
- FastAPI passou a expor `GET /admin/markets/{slug}/resolution-audit` como contrato staff read-only para mercados resolvidos
- auditoria agrega participantes, winners/losers, stakes, refunds, payouts, losses e badges concedidas na resolução a partir de SQL no backend
- Admin Ops passou a mostrar ação “Auditoria” para mercados resolvidos, com tela própria, paginação de 10 participantes e legenda de ledger
- Dashboard Admin Ops recebeu ajustes de contraste em modo escuro para KPIs, métricas, saúde técnica, tabelas e alertas
- QA hard com 100 usuários simulados foi registrada em `docs/research/qa-simulacao-hard-100-usuarios-20260520.md`
- contratos relacionados: `market-lifecycle.md`, `wallet-ledger.md`, `reputation-ranking.md`, `domain-events.md`
- status de implementação: `parcial`

### 2026-05-19 - v0.3
- cancelamento administrativo passou a validar que não restam previsões `open` após aplicar refund total
- adicionada reconciliação operacional idempotente para mercados já `canceled` que ainda possuam previsões `open`
- reconciliação registra `market.cancel_reconcile` e preserva reputação
- adicionada regressão para estado órfão `canceled` + previsão `open`, cobrindo dry-run, refund, saldo e idempotência
- contratos relacionados: `market-lifecycle.md`, `wallet-ledger.md`, `domain-events.md`
- status de implementação: `parcial`

### 2026-05-18 - v0.2
- adicionada resolução manual por `POST /admin/markets/{slug}/resolve`
- resolução registra opção vencedora, evidência, operador, payout, perda e delta de reputação pela fórmula MVP
- resolução passou a registrar data/hora efetiva (`resolved_at`) e timezone controlado (`resolution_timezone`), com campos editáveis no Admin Ops
- cancelamento administrativo passou a aplicar refund total dos stakes bloqueados
- mercados resolvidos passaram a permanecer no browse de resolução com ação excepcional de desfazer resolução
- browse de resolução passou a exibir data/hora/timezone e ordenar por resolução recente, antiga ou pendências
- desfazer resolução retorna o mercado para `locked`, estorna payout líquido, rebloqueia stakes e recalcula reputação
- mercado resolvido passou a ficar somente leitura no editor administrativo
- Admin Ops passou a listar mercados `locked` e publicar resolução real
- contratos relacionados: `market-lifecycle.md`, `wallet-ledger.md`, `reputation-ranking.md`, `domain-events.md`
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `market-lifecycle.md`, `wallet-ledger.md`, `reputation-ranking.md`, `domain-events.md`
- status de implementação: `nao_iniciada`

## FEAT-REP-001

### 2026-05-22 - v1.2
- browse Admin Ops de badges passou a exibir miniatura da imagem cadastrada, com fallback textual compacto para badges sem imagem
- contratos relacionados: `admin-ops.md`, `frontend-web.md`
- status de implementação: `parcial`

### 2026-05-22 - v1.1
- regras administrativas de badge passaram a aceitar recorte opcional por evento, depois de categoria/subcategoria
- `BadgeAwardEngine` passou a aplicar `category/subcategory/event` para previsões resolvidas e comentários
- regras por evento não contam sugestões aprovadas antigas enquanto sugestão ainda não captura evento
- browse/formulário de badges exibem e validam o recorte de evento usando a taxonomia dinâmica
- contratos relacionados: `reputation-ranking.md`, `reputation-and-ranking.md`, `backend-api.md`, `admin-ops.md`
- status de implementação: `parcial`

### 2026-05-20 - v1.0
- padrão web de listas simples passou a usar `Carregar mais` em blocos cumulativos de 10 itens
- tela pública de ranking trocou navegação `Anterior`/`Próxima` por `Carregar mais`, preservando filtros de categoria/subcategoria
- browses principais do Admin Ops de usuários, mercados, resolução, filas e logs passaram a usar o mesmo padrão em blocos de 10
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `parcial`

### 2026-05-20 - v0.9
- tela pública de ranking passou a paginar a lista em 10 linhas por página
- paginação preserva filtros de categoria/subcategoria aplicados
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `parcial`

### 2026-05-19 - v0.8
- ranking web passou a consumir `GET /rankings` como fonte única
- fallback local de cálculo de ranking/reputação no Django foi removido; falha da API exibe erro/estado vazio
- status de implementação: `parcial`

### 2026-05-19 - v0.7
- compartilhamento de badge passou a gerar card social com metadados Open Graph/Twitter e imagem dinâmica
- link público de conquista usa token opaco para permitir preview social sem expor id, email ou handle na URL
- botão de cópia copia apenas o link canônico; links por rede mantêm texto contextual quando suportado
- cards de badge no perfil passaram a usar o mesmo padrão visual do catálogo e apontar para `share-badge`
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `parcial`

### 2026-05-19 - v0.6
- catálogo público de badges passou a exibir ação de compartilhar apenas para usuários autenticados em badges já conquistadas
- adicionada rota web autenticada `/share/badge/{code}/`, validando a conquista antes de renderizar a página de compartilhamento
- compartilhamento MVP usa ação nativa do navegador quando disponível e fallback de cópia de link/texto
- reforçado que compartilhar badge não altera reputação, ranking, ledger, wallet nem concessão de badges
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `parcial`

### 2026-05-19 - v0.5
- badges passaram de registros hardcoded por usuário para catálogo administrável com definição, regra e conquista separadas
- adicionados contratos públicos `GET /badges` e `GET /users/me/badges` com estado pessoal quando autenticado
- adicionados contratos staff para listar, criar, editar e desativar badges no Admin Ops
- concessão automática usa `rule_type` controlado no backend e é idempotente por usuário/badge
- regras temáticas de badge passaram a selecionar categoria/subcategoria da taxonomia dinâmica e aplicar recorte em previsões, acertos, comentários e sugestões aprovadas
- contrato administrativo de badges passou a distinguir campos obrigatórios de opcionais e exigir marcação visual no formulário
- browse administrativo de badges passou a exibir categoria/subcategoria da regra, usando `Todas / Todas` para regras globais
- formulário administrativo de badges passou a exibir prévia do card público, incluindo imagem local antes de salvar
- badges passaram a aceitar imagem padrão/tema claro e imagem opcional para tema escuro, com fallback para a imagem padrão quando a escura não existir
- concessão de badges passou a ser centralizada na `BadgeAwardEngine`, com eventos de domínio para cadastro, comentário, sugestão, feedback e resolução de mercado
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `parcial`

### 2026-05-19 - v0.4
- ranking público passou a aceitar filtros de categoria/subcategoria e expor metadados de taxonomia
- ranking temático é recalculado em leitura com previsões resolvidas do recorte usando a fórmula MVP
- tela de ranking passou a identificar usuários por handle e remover filtros decorativos sem contrato
- quadro "Seu recorte" passou a depender de sessão/dados reais, sem percentuais fictícios para visitantes
- usuários `is_staff` e `is_superuser` foram excluídos do ranking público na API e no fallback Django
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `parcial`

### 2026-05-18 - v0.3
- resolução de mercado passou a atualizar reputação com `K=10` usando `probability_at_entry`
- `accuracy_indicator`, `resolved_predictions_count` e `streak` passam a refletir previsões resolvidas
- cancelamento/refund não altera reputação
- status de implementação: `parcial`

### 2026-05-17 - v0.2
- criada reputação base provisória por usuário com score inicial `100`
- criado ranking público simples ordenado por reputação e data de criação
- criadas badges estruturadas com `founding_member` concedida no cadastro e demais badges bloqueadas
- Django passou a renderizar perfil/ranking a partir da FastAPI quando disponível
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `nao_iniciada`

## FEAT-WALLET-001

### 2026-05-21 - v1.2
- agregado público `GT₵ distribuídas` passou a considerar apenas créditos de usuários comuns, excluindo operadores `staff` e `superuser`
- ajuste manual de wallet permite autoajuste por operador com nota e auditoria, preservando bloqueio das demais autoações sensíveis
- status de implementação: `parcial`

### 2026-05-20 - v1.1
- ledger passou a alimentar o agregado público `GT₵ distribuídas` usado nas métricas da home
- agregado público considera apenas lançamentos `direction="credit"` e não expõe recorte individual de wallet ou extrato
- movimentação pública em previsões é exibida como soma de stakes registrados, mantendo o contexto educativo de `GT₵`
- status de implementação: `parcial`

### 2026-05-20 - v1.0
- extrato da wallet trocou navegação `Anterior`/`Próxima` por `Carregar mais` em blocos cumulativos de 10 lançamentos
- histórico de recargas permanece limitado às últimas 3 solicitações
- status de implementação: `parcial`

### 2026-05-20 - v0.9
- Admin Ops Config ganhou parâmetro `wallet_recharge_min_balance_gtl` para definir o saldo máximo elegível à solicitação de recarga educativa
- backend e wallet web bloqueiam nova solicitação quando `available_gtl` está acima do piso configurado
- histórico de recargas na wallet mostra apenas os 3 itens mais recentes e o extrato pagina 10 lançamentos por vez
- status de implementação: `parcial`

### 2026-05-20 - v0.8
- wallet passou a permitir solicitação autenticada de recarga educativa com uma pendência por usuário
- Admin Ops passou a listar `wallet_recharge` nas filas e aprovar ou rejeitar solicitações com auditoria
- aprovação cria ledger `educational_recharge`, atualiza `gotrendlabs_wallet_balances` e não altera reputação nem `total_earned_gtl`
- status de implementação: `parcial`

### 2026-05-19 - v0.7
- ajuste manual de wallet por staff passou a usar `manual_adjustment`, `admin_user_adjustment`, operador e nota obrigatória
- direção do ajuste manual deve ser escolhida explicitamente no Admin Ops, sem seleção padrão
- débito manual acima do saldo disponível é rejeitado pelo backend
- status de implementação: `parcial`

### 2026-05-19 - v0.6
- refund de cancelamento passou a ser idempotente por previsão enquanto não houver novo lock/relock posterior
- reconciliação operacional de mercado cancelado cria `prediction_refund` ausente e atualiza `gotrendlabs_wallet_balances` na mesma transação
- preservado caso de resolução desfeita seguida de cancelamento final, criando novo release após `prediction_resolution_relock`
- status de implementação: `parcial`

### 2026-05-18 - v0.5
- resolução vencedora libera stake por `prediction_refund` e credita ganho líquido por `prediction_payout`
- resolução perdedora baixa stake bloqueado por `prediction_loss` com `direction="settle"`
- cancelamento com previsão aberta devolve 100% do stake bloqueado por `prediction_refund`
- status de implementação: `parcial`

### 2026-05-18 - v0.4
- ledger passou a reconhecer recompensas operacionais de feedback e sugestão de mercado
- `reward_feedback` e `reward_suggestion` atualizam extrato e projeção `gotrendlabs_wallet_balances`
- aprovações de crédito em filas operacionais bloqueiam duplicidade por item
- recompensas operacionais não concedem reputação
- status de implementação: `parcial`

### 2026-05-17 - v0.3
- adicionada projeção operacional `gotrendlabs_wallet_balances` para leitura rápida de saldo
- mantido `gotrendlabs_wallet_ledger` como fonte auditável e regra de reconciliação
- FastAPI passou a ler saldo pela projeção e a centralizar mutações no helper ledger + balance
- migration inclui backfill de saldos existentes a partir do ledger
- status de implementação: `parcial`

### 2026-05-17 - v0.2
- criado ledger PostgreSQL `gotrendlabs_wallet_ledger` como fonte do saldo do usuário
- cadastro passou a registrar `grant_initial` de `2000 GT₵` na mesma transação do usuário
- adicionados endpoints FastAPI de wallet e extrato autenticado
- Django passou a renderizar carteira e extrato a partir da FastAPI
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `wallet-ledger.md`
- status de implementação: `nao_iniciada`

## FEAT-COMMENT-001

### 2026-05-18 - v0.3
- UI pública de comentários passou a identificar autores por `@handle`
- ações de `like` e `dislike` passaram a usar botões iconizados com estado ativo
- convite de login para visitante no bloco de comentários foi redesenhado como callout
- documentação de arquitetura/contratos passou a registrar endpoints, tabelas, moderação e fallback local
- status de implementação: `parcial`

### 2026-05-18 - v0.2
- adicionada persistência de comentários e reações em mercados
- FastAPI passou a expor criação/listagem pública, `like`/`dislike` autenticado e moderação staff por `visible`/`hidden`
- Django passou a renderizar formulário, lista e ações de reação no detalhe do mercado
- Admin Ops passou a listar e moderar comentários com evento `comment.hide`/`comment.restore`
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `domain-events.md`, `i18n-content.md`
- status de implementação: `nao_iniciada`

## FEAT-SUGGEST-001

### 2026-05-22 - v0.6
- navegação pública principal passou a exibir `Sugerir mercado` para visitantes e usuários autenticados
- o link usa o fluxo de sugestão existente, preservando envio guest e atalho autenticado no menu do usuário
- status de implementação: `parcial`

### 2026-05-19 - v0.5
- Admin Ops deixou de executar fallbacks locais mutáveis para filas, comentários, conversão de sugestão e créditos operacionais
- indisponibilidade da FastAPI passa a ser exibida como erro operacional sem alterar domínio diretamente pelo Django
- status de implementação: `parcial`

### 2026-05-19 - v0.4
- sugestões de mercado e feedback passaram a aceitar `recaptcha_token`
- FastAPI exige reCAPTCHA válido para envios de visitantes quando configurado
- Django renderiza widget v2 apenas para visitantes e preserva bypass para usuários autenticados
- fallback local de desenvolvimento valida reCAPTCHA antes de persistir envio guest
- status de implementação: `parcial`

### 2026-05-18 - v0.3
- formulários públicos passaram a aceitar envio autenticado ou visitante identificado por nome e email
- confirmação de envio passou a usar popup na home após redirecionamento
- fila operacional passou a exibir Mercado e Feedback com data de criação, tipo do item e ordenação por data
- removidas colunas operacionais não usadas nesta fatia, como aging e responsável
- tela de revisão passou a exibir status persistido, recompensa, contexto completo e ações específicas por tipo
- conversão em rascunho ficou restrita a sugestão de mercado e bloqueada após conversão
- créditos podem ser aprovados para feedback ou sugestão apenas quando houver usuário cadastrado, com bloqueio de reenvio
- status de implementação: `parcial`

### 2026-05-18 - v0.2
- adicionada persistência para sugestões de mercado e feedbacks operacionais
- FastAPI passou a expor submissão pública/autenticada e fila administrativa staff
- Admin Ops passou a listar itens reais, revisar, converter sugestão em rascunho e recompensar feedback via ledger
- feedback recompensável entra como fatia operacional mínima; event bus assíncrono segue pendente
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `domain-events.md`, `i18n-content.md`
- status de implementação: `nao_iniciada`

## FEAT-NOTIFY-001

### 2026-05-20 - v0.2
- Admin Ops passou a persistir configuração SMTP não sensível em `gotrendlabs_site_config`
- senha/API key SMTP permanecem fora do banco, via `GOTRENDLABS_SMTP_PASSWORD` ou `GOTRENDLABS_SMTP_API_KEY`
- TLS e SSL são mutuamente exclusivos na configuração operacional
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `domain-events.md`, `i18n-content.md`
- status de implementação: `nao_iniciada`

## FEAT-I18N-001

### 2026-05-20 - v0.2
- marca pública da plataforma alterada para `GoTrendLabs` em templates, compartilhamento social, API title/health, README e specs ativas
- nomes técnicos, identificadores `gotrendlabs_*`, arquivos, comandos, env vars e `GTL Credits` foram preservados
- extração completa de strings para catálogos `pt-BR`/`en` segue fora desta fatia
- status de implementação: `nao_iniciada`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `i18n-content.md`
- status de implementação: `nao_iniciada`

## Sistema documental e skills

### 2026-06-07 - v0.8
- adicionado snapshot OpenAPI versionado em `packages/contracts/openapi/gotrendlabs-api.json`
- adicionado exportador/verificador `packages/contracts/export_openapi.py`
- CI passou a validar o snapshot com `python packages/contracts/export_openapi.py --check` antes da suite
- README, specs de arquitetura e skills locais atualizados para a política de contratos
- status de implementação: `concluida`

### 2026-06-07 - v0.7
- apps Django movidos para `apps/web/django/`, preservando `AppConfig.label` historico e migrations existentes
- README, arquitetura web/admin/system overview e skills locais atualizados para a nova estrutura vigente
- status de implementação: `concluida`

### 2026-05-17 - v0.3
- adicionada skill `gotrendlabs-workflow-governor`
- adicionados templates em `docs/specs/workflows/`
- adicionados `workflow-runs.md` e `workflow-checklists.md`
- guia atualizado com fluxo de testes e governança de processo

### 2026-05-17 - v0.4
- adicionada skill `gotrendlabs-software-architect` para arquitetura, segurança e desenho técnico
- adicionada skill `gotrendlabs-test-engineer` para testes concretos de backend, frontend, integração e regressão
- workflows atualizados para exigir arquitetura/segurança em mudanças relevantes e testes executáveis quando houver código

## 2026-10-09 — FEAT-THUMB-001 v1.0, local

Um clique gera, outro regenera, seleção automática e desfazer preservam uploads/edições. Execução persistente dedicada, staff/MFA/draft, limites reservados PostgreSQL, privacidade de candidatas, confirmação por ID no PATCH, URL pública compatível e limpeza conservadora. Gate editorial da versão salva preservado. Upload só grava após validação e compensa falha; publicação após salvamento reporta resultado real. Testes isolados/browser e documentação entregues; sem consumo pago/deploy. WFLOW-20261009-AI-THUMBNAILS-001.

- 2026-10-09 — FEAT-THUMB-001 v1.1: OpenAI substituído por Bedrock Runtime/Core com adapters SD3.5/Ultra selecionáveis em Configurações do Sistema; modelo/região/proporção/timeout/cotas/retenção, API staff/MFA e auditoria, migration 0023/grants, snapshot por job e bloqueio explícito de legados. Sem consumo pago/deploy; 37 testes e 9 verificações complementares aprovados, browser/checks aprovados; migration/grants e runtime local verificados.

## 2026-10-09 — Preparação do fechamento FEAT-THUMB-001

Fonte da verdade reconciliada com autorizações e duas solicitações Core concluídas no DEV, sem nova inferência no fechamento. Deploy prepara subdiretório de mídia e acompanha executor quando seu segredo estiver instalado, inclusive pausado; CI inclui build completo. PR/CI/merge/implantação dependem de aprovação da descrição; branch local preservada. Qualidade visual sistemática e acesso produtivo não declarados validados. WFLOW-20261009-THUMBNAIL-CLOSE-001.

## 2026-10-09 — Imagens IA de badges

FEAT-BADGE-IMAGE-001 local: gerar/regenerar/desfazer na criação e edição, contexto atual e par de imagens, uma para cada tema; confirmação atômica por ID e versão; fila/provedor/executor/cotas compartilhados, habilitação independente. Upload após validação e compensação conservadora, APIs públicas/concessões preservadas. 70 testes e browsers aprovados; PR/produção pendentes.

## 2026-10-09 — Fechamento técnico e rollout de thumbnails

PR #143 integrada, merge 15b980585982cfa6706a38d57016614a41ba956d. CI final 408 testes aprovados/1 skip por roles CI, build completo aprovado. Actions 37963430113 e 37964971891 Success (PR e main/produção), SSM deploy Success. Migrations 0022–0024 aplicadas; defaults SQL preservam inicialização existente. Executor dedicado/grants/mounts/UIDs verificados: worker privado RW, API privado RO/subpath público RW, sem candidatas no proxy/Django. Arquivo efêmero próprio removido.

Habilitação produtiva de thumbnails autorizada e concluída: banco e GTL_THUMB_ENABLED=1 na API/worker, Core/Oregon/3:2/180s, limites 10/5/50 por 24h e retenção 24h. Configuração preservada, alteração auditada como operação de sistema; backups de envs 0600 no host. Fila vazia antes/depois, nenhuma chamada paga iniciada, nenhum mercado editado pelo assistente. Site/API HTTP 200 e configurações anônimas 401. Branch local preservada.

Fechamento técnico concluído; homologação de fluxo autenticado/MFA, consumo produtivo e qualidade visual real permanece pendente. Não afirmar inferência real validada em produção. Fonte externa atual: [PR #143](https://github.com/wscardua/gotrendlabs/pull/143) e [Actions](https://github.com/wscardua/gotrendlabs/actions/runs/37964971891). Registros anteriores descrevem etapas históricas, substituídos por esta atualização para estado operacional atual. Evidência documental pós-rollout preparada localmente para versionamento na próxima PR aprovada.


## 2026-10-09 — Correção: par de imagens de badges

Correção clara/escura concluída: 78 testes aprovados (73 geração/regressões/deploy em 96.927s + 5 reinício/concessões/catálogo/formulário em 10.185s), PostgreSQL isolado e provedor simulado. Browsers badge e thumbnail aprovados; prévias distintas, troca de tema, ausência da variante escura preserva o par anterior, undo/uploads/late response/submit. Django check, migration drift, OpenAPI, Node e diff aprovados. Executor DEV reiniciado sem job em execução (PID 95376), chave/flag mantidas ativas, API health 200. Nenhuma inferência paga iniciada pela correção; dois jobs DEV anteriores de versão universal permanecem preservados. Suíte completa de 431 testes é evidência da versão anterior, não foi repetida nesta alteração. Homologação real da coerência entre variantes e PR/deploy próprios seguem pendentes.


2026-10-09 — Feedback de espera em badges e thumbnails: botão Gerando… desabilitado, painel inline destacado com spinner e aviso Aguarde/alguns minutos/edição dos demais campos. Indicador permanece até prévias carregadas, não desaparece por upload manual e encerra em sucesso/erro; preserva imagem anterior e decisões continuar/aguardar. Anúncio role=status/aria-live e reduced-motion. Browser Chrome real com respostas simuladas aprovado para ambos (badge-loading-browser.log, thumbnail-loading-browser.log), screenshot de loading inspecionado; Django check/Node/diff aprovados, assets locais verificados via HTTP e cache versionado. Sem chamada paga ou implantação dessa alteração.


## 2026-10-09 — Correções de review de imagens administrativas

Correções implementadas e verificadas localmente: salvamento pendente cancelado ao mudar seleção durante decode, instrução para novo Salvar e nenhuma submissão herdada pela próxima geração; identidade estável por badge/sessão, cache limitado com fallback determinístico para badge salva, criação rotacionada apenas após sucesso. 77 testes/83.891s aprovados em PostgreSQL isolado; 3 cenários de identidade/recarga rechecados após fallback determinístico (2.267s). Browser de mercados aprovou reprodução com decode suspenso, manual/Aguardar/gerar outra/Salvar; browser de badges aprovou o mesmo cenário e recarga/polling sem POST extra. Regeneração no teste aguarda a nova candidate_id, evitando corrida entre casos. Django/migrations/OpenAPI/Node/diff aprovados; assets DEV conferidos por HTTP. Sem nova inferência paga, alteração produtiva, commit ou PR; fonte técnica atual nos contratos/features/runbook e estado operacional. Homologação real de pares e PR/deploy próprios permanecem pendentes.


## 2026-10-09 — Fechamento técnico local / WFLOW-20261009-BADGE-CLOSE-001

Validação final do fechamento: 442 testes aprovados em 776.623s, PostgreSQL isolado e provedor simulado, log local badge-close-full-tests.log. Browsers de badges e mercados aprovados, incluindo recarga sem geração extra e escolha manual durante decode sem submit herdado; Django, migration drift, OpenAPI, Node, shell, Compose, diff e Dockerfile check aprovados (sem avisos). Build completo remoto, PR/merge/deploy e habilitação produtiva de badges aguardam aprovação da descrição. Nenhuma inferência paga nesta validação. Homologação humana/MFA e coerência visual real permanecem pendentes; thumbnails produtivas PR #143 preservadas.


## 2026-10-09 — Estado produtivo atual de imagens administrativas

PR #144 integrada em main edac7c7; CI PR e main/build/deploy Success, 442 testes em ambos com um skip por roles CI ausentes (cenário aprovado localmente). Migration0025/grants/constraints/mounts/executor conferidos; habilitação auditada de badges concluída, política de thumbnails preservada. Stable Image Core/Oregon, badges1:1, timeout180s, limites10 imagens/operador e50 globais por24h,5 solicitações/item, retenção24h. Fila vazia, sem inferência paga ou alteração de mercados/concessões reais. Branch local preservada. Manutenção pública ativa preservada; Admin Ops exige login. Homologação humana/MFA e coerência visual real permanecem pendentes. [Evidência produtiva](../testing/ai-badge-images-production-20261009.md). Registros anteriores são histórico das etapas.


## 2026-10-09 — Incidente: auditoria do worker de imagens

Incidente WFLOW-20261009-IMAGE-WORKER-AUDIT-FIX-001: primeira solicitação produtiva informada permanece queued, sem started_at/provider_id/arquivo. Worker falha na auditoria porque thumbnail_service.event importava main, ativando exigência de pepper/TOTP exclusivos da API. Diagnóstico por SSM/read-only e probes com rollback, sem inferência ou mutação em mercados. Correção local usa diretamente admin_events, sem distribuir segredos HTTP ao executor. Teste em subprocesso com ambiente production, segredos HTTP vazios e provedor simulado cobre claim, sucesso e eventos persistidos. Rollout corretivo e conclusão da solicitação real ainda pendentes; não afirmar latência do provedor, acesso efetivo ou qualidade real por esse incidente.


## 2026-10-09 — Recuperação produtiva do executor

Incidente resolvido pela PR #146/main b033afe4, CI PR37981039913 e main37981803447/build/deploy Success (443 testes, um skip de roles CI). SSM deploy3e165a28 e verificação0d584e9f Success: auditoria do worker sem main, serviços ativos. Pedido original cdbe1f42-d75b-44ec-8f0c-11ece3d6952e succeeded em 6.451679s de processamento, arquivo privado presente e ID de provedor registrado; sem nova solicitação/replay pelo assistente ou salvamento/publicação do mercado. Primeira execução Core produtiva iniciada pelo operador confirma acesso efetivo do token/modelo, mas não avaliação visual ou custo faturado. [Evidência externa](https://github.com/wscardua/gotrendlabs/pull/146). Recibo atualizado localmente para próximo versionamento autorizado.


FEAT-THUMB-001: correção local de relevância visual, assunto antes do estilo e pistas explícitas de futebol feminino e CS2; preservação de prompt v2 para jobs históricos. Duas imagens Ultra produtivas inspecionadas não representam o mercado; nenhuma inferência nova. Qualidade v3 e rollout pendentes.

Evidência WFLOW-20261009-THUMBNAIL-RELEVANCE-001: 70 testes aprovados em 96.136s, PostgreSQL isolado/provedor simulado (thumbnails e badges). Django check, compilação Python e git diff --check aprovados. Ruff não disponível no ambiente virtual; nenhuma instalação realizada. Nenhuma nova chamada paga, alteração de produção ou PR nesta etapa. Homologação visual v3 pendente.


2026-10-09 — Etapa histórica v4, substituída pela v5: prompt market-thumbnail-bedrock-v4 sem temas, entidades, cenas ou condicionais fixos por categoria. Pergunta/resumo/classificação atuais determinam o assunto; regras fixas somente de composição, qualidade, neutralidade e segurança. Substitui a proposta local v3 de âncoras temáticas, rejeitada pelo usuário. Executor DEV reiniciado com fila vazia, PID82614; imagens/estados v3 existentes preservados, sem reinterpretar/repetir solicitações. V3 queued não chama provedor (unsupported_instructions); v2 histórico preservado. Produção e modelos não alterados; sem nova inferência paga. Validação v4: 70 testes de thumbnails/badges aprovados em 102.686s com PostgreSQL isolado/provedor simulado; rechecagem dos 6 testes do provedor aprovada em 0.053s, incluindo invariância do template entre temas, contexto completo e rejeição de v3 sem invocação. Django check, compilação Python e diff aprovados. Nenhuma inferência paga iniciada; qualidade real permanece pendente de avaliação pelo operador. Log thumbnail-dynamic-tests.log e thumbnail-dynamic-provider-tests.log em .runtime/badge-validation.


2026-10-09 — Direção vigente v5: interpretação semântica em modelo textual Bedrock seguida da imagem configurada. Sem templates/presets de assunto ou composição por categoria. Configuração textual própria GTL_THUMB_PLANNER_* congelada no job; default openai.gpt-oss-20b/Mantle us-east-1, timeout45s, saída2048tokens (allowlist20b/120b; timeout10–120s/tokens512–4096). Uma chamada textual e uma imagem por reserva, sem retry/fallback; checkpoints planner/image sob fencing/elegibilidade, lease soma timeouts e brief final privado persistido para auditoria/regeneração. Falha textual impede imagem. V2 histórico preservado; v3/v4 não reinterpretados. Substitui as soluções v3/v4; badges/comentários/interface não mudam. ADR-0014 formaliza a mudança justificada pelos exemplos reais irrelevantes e exigência do usuário. Validação v5: 75 testes aprovados em 103.334s, PostgreSQL isolado/provedor simulado, cobrindo planejamento→imagem, falhas/recusa/timeout sem imagem, checkpoints/fencing, preservação de uso após erro desconhecido e ausência de replay, snapshot/lease, regeneração e badges. Dois testes adicionais dos agentes textuais aprovados (3.271s e1.718s), sem alteração de seu comportamento. Django check, OpenAPI --check, compilação Python e diff aprovados. Executor DEV reiniciado sem geração ativa, PID93387; v5 posteriormente homologado informalmente pelo operador no DEV, conforme recibo abaixo. Nenhuma inferência paga pelo assistente ou mudança produtiva; commit local preparado no fechamento, PR/deploy aguardam aprovação. Credencial/acesso e avaliação visual informal do novo fluxo confirmados no DEV; homologação PRD permanece pendente. Logs thumbnail-semantic-*.log em .runtime/badge-validation.


## Homologação DEV e preparação de PRD v5

2026-10-09 — Homologação DEV v5: operador informou “em dev local parece estar legal” e autorizou preparar PRD. Consulta local somente leitura confirmou três jobs v5 succeeded (34ccb8f0, bcc57be2, 5cb97131), iniciados pelo operador, com planner openai.gpt-oss-20b/Mantle us-east-1 e imagem Core/us-west-2. Tempos de processamento: 17.804s, 9.663s e 15.883s; uso textual retornado registrado, sem afirmar custo faturado. Acesso efetivo e aprovação visual informal do fluxo DEV confirmados; não substituem matriz visual sistemática, medição de engajamento ou homologação do token/modelo em PRD. Nenhuma inferência paga iniciada pelo assistente. Próxima etapa: aprovação da descrição atualizada da PR, CI completo, merge/deploy e verificação produtiva; preservar modelo de imagem e políticas atuais de PRD.


Fechamento local em 2026-10-09: suíte completa de 450 testes aprovada em 862.190s, sem skips, com PostgreSQL isolado e provedores simulados; credenciais de inferência vazias e geração desabilitada no processo de testes. Banco de testes destruído ao concluir. Log ignorado: .runtime/badge-validation/thumbnail-semantic-close-full-tests.log. Django check, snapshot OpenAPI, compilação Python e diff aprovados; checklist de alteração de feature/arquitetura/contratos/ADR/testes/memória conferido. Commit local autorizado preparado somente com 22 arquivos de código/configuração de exemplo/docs/testes; mídia DEV, credenciais e mudanças das outras iniciativas excluídas e preservadas. Submissão da PR com descrição em português, merge e rollout aguardam a aprovação solicitada pelo usuário.
