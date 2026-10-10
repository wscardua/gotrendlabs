# Change Log de Specs

## 2026-10-10 — FEAT-MCP-001 v1.5

Contrato editorial passa a aceitar documento consolidado, com projeção de fichas E01–E11 antigas e um único aceite humano para aprovação. E01–E11 permanecem orientação; confirmação global não inventa verificação independente. FEAT-MCP-001, contrato agent-integrations, ficha/checklist e estratégia de teste sincronizados.


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

## 2026-10-07 — evidência de radar MCP

- Workflow WFLOW-20261007-MCP-RADAR-PILOT-001 concluído localmente; [ensaio](../testing/mcp-radar-pilot-20261007.md), fixtures públicas e harness opt-in registrados. Contrato nullable revalidado, sem alteração de schema. Feature permanece parcial; sem homologação externa ou publicação.

## 2026-10-07 — FEAT-MCP-001 implementação local

- OAuth/Authlib e serviço, identidade técnica/delegação, MCP SDK Streamable HTTP com dez ferramentas restritas, gestão/consentimento/revisão Admin Ops. Staff/superuser com MFA equivalentes.
- Migrations aditivas/grants, serviços compartilhados, drafts/ficha/snapshots, idempotência, cotas persistentes São Paulo, locks humanos/publicação/revogação e correlação nos logs/eventos existentes.
- OpenAPI atualizado, testes PostgreSQL/cliente MCP real, UI desktop/mobile, imagem sem DB e configuração/runbook/rollback/prompt preparados. [Evidências](../testing/mcp-editorial-results.md). Sem merge/deploy; Dot e HTTPS externo pendentes.


## 2026-09-29 — FEAT-ANALYTICS-001 conclusão v0.4

- Status de implementação promovido para `implementada_validada` após PR `#133`, CI/deploy e GeoLite/proxy produtivos. Memória registra a ausência de tráfego real durante a manutenção e a necessidade de novo binário Flutter para usuários mobile existentes.

## 2026-10-07 — FEAT-MCP-001 v1.0

- Consolidada spec MCP editorial com contrato de ferramentas/API, ADR-0011, matriz de aceite e prompt para implementação em contexto limpo.
- Regra final do usuário: staff e superusers têm gestão equivalente; divisão por papel/responsável apenas futura. OAuth e serviço no escopo, Dot como primeiro executor-alvo sujeito a homologação.
- Reutilização de logs e eventos existentes, ficha persistida, quotas/idempotência/concorrência, fronteira sem DB no MCP. Entrega documental; runtime não alterado.

## 2026-09-29 — FEAT-ANALYTICS-001 v0.4

- Define retenção de produto D1/D7/D30 por coorte, diferença entre visitante e conta, coortes maduras e cobertura inicial parcial.
- Substitui o mapa de blocos por SVG das malhas simplificadas oficiais do IBGE, mantendo a FastAPI como fonte das contagens.
- Fecha o escopo implementável da v0.4 localmente; publicação, configuração GeoLite/proxy e smoke produtivo permanecem etapas operacionais antes de `implementada_validada`. Melhorias futuras são listadas separadamente em `known-gaps.md`.

## 2026-09-29 — FEAT-ANALYTICS-001 v0.3

- Contrato staff passa a expor última remessa de eventos, volume humano de 24 horas, última execução de atualização GeoLite e estado/metadados do arquivo ativo.
- Importador backend registra sucesso ou falha da atualização GeoLite; o painel não confunde a presença do arquivo com execução comprovada.

## 2026-09-29 — FEAT-ANALYTICS-001 v0.2

- Resumo staff passa a oferecer rankings de UFs/cidades brasileiras, cobertura e atividade geográfica diária, além de funil observacional de desistência por sessão/mercado após 30 minutos de inatividade.
- Flutter registra escolha de opção no ticket inicial. Confirmação persistida segue separada do clique observado.

## 2026-09-29 — FEAT-ANALYTICS-001

- Criada spec de analytics proprio e ADR-0010 para fronteiras FastAPI/Django/Flutter, identidade por evento, geografia aproximada e limites de atribuicao.
- O dashboard distingue coleta observada de totais persistidos no dominio; fluxo de sessoes vai ate o clique de confirmacao, com indicador separado de primeira previsao persistida por conta/mercado em sete dias.

## 2026-09-28 — MFA administrativo TOTP

- `FEAT-AUTH-001` passa a incluir TOTP obrigatório para staff/superuser, sessões com evidência MFA, desafios curtos, recovery codes hashados e revogação de sessões administrativas no rollout.
- ADR-0009 registra autoridade FastAPI, proteção Fernet do segredo e remoção da rota Django Admin como prevenção de bypass.
- A versão `0.7` explicita persistência, critérios de aceite, testes de regressão, segregação operacional da chave Fernet e a incompatibilidade intencional do cliente mobile até haver superfície administrativa própria.

## 2026-09-27 — Identidades bot e credencial de teste apos o corte

- `FEAT-AIAGENT-001` v0.4 explicita que os agentes oficiais sao vinculados por `user_id`/`is_bot` e nao autenticam com senha para executar o daemon; senhas inutilizaveis nas contas bot sao esperadas.
- Memoria de autenticacao registra a restauracao operacional de `@test` com Argon2id e a conta staff que ainda requer reset, sem alterar contrato HTTP, schema ou codigo do app.

## 2026-09-27 — Validacao produtiva do corte de senha

- A fatia Argon2id/pepper e autoridade da FastAPI foi implantada pela PR `#126`, com CI/deploy e smokes web/API/mobile-header produtivos aprovados. Fronteira de roles e segregacao de segredo foram conferidas em runtime; 0 hashes PBKDF2 restam.
- Estado da feature ampla continua `draft/parcial`, porque refresh/revogacao avancada, rate limit distribuido e politica administravel seguem fora desta entrega. Ensaio isolado foi dispensado; capacidade sob carga real continua em observacao.

## 2026-09-27 — Fechamento documental do corte de senha

- A melhoria Argon2id/pepper e autoridade exclusiva da FastAPI esta validada localmente; `FEAT-AUTH-001` permanece `draft/parcial` porque abrange outras evolucoes de autenticacao. O usuario dispensou ensaio externo isolado nesta fase, nao o preflight do host, o inventario de hashes e o smoke/monitoramento do primeiro deploy.
- Contratos HTTP/OpenAPI e schema funcional permanecem inalterados. A memoria operacional registra que PR, merge, deploy e validacao produtiva ainda dependem de aprovacao e execucao.

## 2026-09-27 — Correcoes da revisao de autenticacao e refund

- Arquitetura de banco, ADR-0008 e contrato de wallet explicitam owner sem login, migrator separado, grants por coluna, preflight e falha transacional quando refund nao tem saldo bloqueado suficiente.
- Contratos HTTP/OpenAPI e Flutter permanecem inalterados; pendencias de segredo/capacidade/corte produtivo seguem registradas.

## 2026-09-27 — FEAT-AUTH-001 senha Argon2id com pepper

- Versao `0.5` define hash Argon2id com sal individual e pepper exclusivo da FastAPI, fora do banco; Django web nao recebe o segredo nem cria/verifica senhas em runtime. Sem compatibilidade PBKDF2 no corte pre-lancamento; contratos HTTP e schema de produto preservados.
- Arquitetura, testes, integracao operacional e ADR-0008 registram configuracao produtiva, custo de memoria, perda/rotacao do segredo e validacao antes do deploy.

## 2026-09-26 — Validação produtiva do editorial

- `FEAT-EDITORIAL-001` promovida a `implementada_validada` após PR `#124`, CI/deploy `36275879637` e smoke produtivo de acesso e renderização dos três documentos para staff. Workflow de fechamento concluído; limites de IA e visibilidade dos arquivos no repositório público preservados.

## 2026-09-26 — Fechamento do escopo editorial

- FEAT-EDITORIAL-001 passa a `implementada_aguardando_deploy`: conteúdo aprovado, consulta staff e critérios versionados implementados com testes locais e validação visual. Avaliação IA e parecer persistido são evolução separada; produção será marcada validada apenas depois de CI/deploy/smoke.

## 2026-09-26 — Consulta editorial local

- FEAT-EDITORIAL-001 passa a `parcial`: Admin Ops exibe os documentos aprovados e o JSON dos critérios prepara integração futura. Arquitetura, integration map, aceite e testes atualizados; conteúdo editorial v1.2 permanece aprovado.

## 2026-09-26 — Aprovação do editorial

- Promovida a spec editorial v1.2 por aprovação explícita do usuário; conteúdo e contratos preservados. A proposta de integração administrativa/IA não altera o estado da entrega documental.

## 2026-09-26 — Editorial v1.2

- Atualizadas origem funcional e spec editorial: mercados de previsão são o núcleo; categorias orientam catálogo. Manual, ficha e checklist independente sincronizados; percentuais de diversidade da v1.1 substituídos por planejamento sem cotas de aprovação. Sem alterações de código, contratos ou mercados.

## 2026-09-26 — Editorial v1.1

- Separadas orientações operacionais e referências técnicas. Manual/ficha passam a usar exemplos didáticos, mantendo E01–E11; removidas duração, cadência e distribuição temática do piloto. Acompanhamento editorial permanece sem telemetria nova.

## 2026-09-26 — Editorial

- Criada `FEAT-EDITORIAL-001` com escopo documental, contratos revisados sem alteração, fronteiras e critérios de aceite.
- Manual e ficha definem seleção, redação, validação de fonte, horários, exceções, parecer e tratamento pós-publicação.
- Atualizadas origem funcional, descoberta no README, arquitetura Admin Ops, integration map e status; preservada distinção entre processo humano e gate automatizado futuro.

## 2026-09-26

- evoluídas arquitetura e feature mobile para incluir AAB assinado no Google Play Closed testing, mantendo publicação pública/open testing fora do escopo e o canal APK direto independente;
- registrados build `1.2.0+14`, assinatura, hash, tamanho, ABIs, bases produtivas e publicação concluída no Closed testing com notas `pt-BR`;
- explicitado em UX e aceite mobile que `birth_date` permanece obrigatória também na edição do perfil, sem ação de limpeza, com entrada `DD/MM/AAAA` normalizada para o contrato `YYYY-MM-DD`;
- mantida a FastAPI como autoridade exclusiva da maioridade; a validação Flutter continua limitada a presença e formato para UX;
- encerrado o workflow de maioridade após revisão de branch, 106 testes Flutter, QA físico no Galaxy S20, PR `#121`, CI/deploy `36246617456`, migration e smokes produtivos de API, web, política pública e contrato mobile.

## 2026-09-19

- evoluída `FEAT-AUTH-001` para exigir data de nascimento privada e restringir contas humanas a pessoas com 18 anos completos, com FastAPI como autoridade nos cadastros por senha/social e na edição de perfil;
- definido corte pré-produção simples: perfis legados sem nascimento recebem `1990-01-01`, sem fluxo de regularização, e web/mobile apenas coletam e apresentam a decisão do backend;
- aprovada e marcada como `implementada_validada` a `FEAT-OPSLOG-001`; o daemon contínuo revalida conexões Django nos limites de cada ciclo para impedir falhas recorrentes das outboxes após conexão PostgreSQL encerrada;
- registrado o critério de aceite e a regressão automatizada para os limites de conexão do ciclo, sem alterar contratos, schema, eventos de domínio ou consumidores web/mobile.
- migradas as skills versionadas do GoTrendLabs de `tools/skills/gotrendlabs/` para `.agents/skills/`, o caminho de descoberta automática do Codex para o repositório;
- atualizados o índice, README, guia de workflow, arquitetura geral e arquitetura mobile; registros históricos continuam preservando o caminho usado no momento de cada execução.

## 2026-09-07

- registrado `WFLOW-20260907-PRODUCTION-AUDIT-FOLLOWUPS-023` para consolidar os achados produtivos como evolucoes planejadas, sem alterar o estado validado de `FEAT-INTEGRITY-001`;
- priorizada a separacao de owner/migrator das roles runtime do ledger e a ativacao/teste dos destinos de alarmes, incluindo correcao das dimensoes do disco;
- documentados capacidade/HA, retencao operacional, identidade por workload, rotacao versionada do commitment secret, headers FastAPI, tratamento de push terminal e validacao continuada como proximos ciclos;
- encerrado `WFLOW-20260907-INTEGRITY-CLOSEOUT-022` e promovida `FEAT-INTEGRITY-001` para `implementada_validada` após PRs, CI/deploy, rollout AWS, corte idempotente e smoke produtivo;
- registrada a regressão operacional que remove `PushDelivery` somente quando vinculada às notificações dos mercados eliminados, preservando históricos não relacionados;
- promovida `FEAT-INTEGRITY-001` para `aprovada` na versão `1.2`, por autorização explícita do usuário, mantendo implementação aguardando deploy até validação produtiva;
- definido corte sem legado para remover todos os mercados pré-lançamento sem definição, inclusive `draft`/`scheduled`, após snapshot validado;
- atualizado runbook AWS com KMS/IAM/Secrets Manager, swap/monitoramento e segundo worker Django;
- endurecida a selagem para exigir auditoria global integral fresca sob lock, sem confiar apenas em checkpoint historico;
- removidas da prova publica referencias/eventos individuais de previsao, substituidos por agregado de compromissos;
- ampliada a verificacao de metadados persistidos de definicao, compromisso, Seal e folhas, e definido backoff de uma hora para divergencia global identica;
- definido que cadeia global em `failed` suprime a fila de selagem antes da iteração dos mercados, sem interromper as demais tarefas do daemon;
- registradas como evolucao futura a rotacao versionada do segredo de pseudonimizacao e a materializacao de resumo autoritativo por mercado;
- aprovada `ADR-0007` para checkpoints assinados, auditoria incremental por ciclo, auditoria integral no primeiro ciclo apos 24 horas e leitura publica sem full scan;
- substituido o booleano ambiguo `valid` pelos estados `verification_status` e resultados nullable separados para mercado, cadeia e conjunto;
- adicionado `GET /integrity/status`, metadados de checkpoint no contrato de verificacao e build Flutter `1.2.0+13` sem compatibilidade pre-producao;
- endurecida a semantica de verificacao para que cadeia global invalida torne `valid=false` e qualquer falha aplicavel bloqueie Seal;
- definido que alertas pendentes prevalecem nos selos visuais e que auditoria cobre mercado publicado sem definicao;
- ampliada a cobertura assinada/conferida dos metadados persistidos do ledger e restringida a causalidade do purge de badges;
- registrado o risco de desempenho linear da verificacao global, separado da cobertura adequada dos indices de lookup existentes;
- substituida a convivencia com mercados pre-producao sem prova por corte destrutivo controlado, com inventario, backup, `dry-run` e recusa de registros criptograficos protegidos;
- previsoes humanas e de agentes IA passam a compartilhar persistencia inicial atomica e cobertura obrigatoria um-para-um por compromisso;
- IDs taxonomicos tornam a associacao parte da prova enquanto nomes permanecem snapshot editorial renomeavel;
- falha da auditoria deixa de derrubar o daemon, adia apenas selagem e preserva tarefas independentes;
- removida a necessidade de compatibilidade com builds Flutter anteriores, ainda nao publicados; o build desta fatia passa a `1.2.0+13`.

## 2026-09-06

- ampliada a auditoria de integridade do Admin Ops para qualquer estado do mercado, com diagnóstico separado por camada e compromissos verificáveis antes da selagem;
- esclarecido que a auditoria criptografica e a primeira rotina de todo ciclo do daemon, cobre mercados em qualquer estado e nao depende da janela de selagem;
- ampliada `FEAT-INTEGRITY-001` para manter comprovantes do usuario em todos os estados posteriores, ajustar os CTAs dos cards e criar auditoria criptografica recorrente pelo daemon com fila operacional de severidade alta;
- comprovantes individuais de previsao passam a abrir em modal web responsivo e o detalhe lista separadamente os recibos de entrada inicial, reforcos e revisoes, preservando a rota completa como fallback;
- refinada a experiencia web de `FEAT-INTEGRITY-001`: o modal compacto deixa de destacar uma secao negativa de limitacoes ou alertas globais que nao invalidam o mercado, o CTA de mercados finalizados volta a `Ver resolução` e a confirmacao de previsao explicita o comprovante assinado emitido pela FastAPI;
- refinada `FEAT-INTEGRITY-001` para separar retry operacional (`seal_retry_pending`) de diferenca criptografica (`verification_failed`) e representar cancelamento preservado sem etapas eternamente pendentes;
- a verificacao passa a comparar definicao e resultado operacionais com os snapshots assinados e a validar os compromissos incluidos no Merkle;
- web e mobile passam a usar verde somente para verificacao aprovada, azul para processo ativo, amarelo para prazo/retry, cinza para nao aplicavel/legado e vermelho para inconsistencia comprovada.

## 2026-09-05

- criada `FEAT-INTEGRITY-001` e o contrato `integrity-ledger.md` para canonicalização, assinaturas, Merkle, visibilidade e migração de legado;
- ciclo de mercado, previsões, eventos, notificações, backend, banco, daemon, web, mobile e testes foram atualizados para `sealed` e provas verificáveis;
- aprovadas ADR-0004, ADR-0005 e ADR-0006 para ledger interno, AWS KMS Ed25519 e correções append-only;
- comunicação institucional passou a distinguir claramente ledger interno de blockchain pública/descentralizada.

## 2026-08-29

- atualizada a especificação de `FEAT-MARKET-001` e a arquitetura web para definir cards compactos: classificação e prazo relativo permanecem no feed, enquanto volume reservado, participantes, `close_label` e fonte ficam fora dessa superfície.
- atualizado o estado de implementação e a regressão esperada, incluindo o rótulo visual `Consenso final` em cards resolvidos, sem mudança de contratos FastAPI/OpenAPI ou impacto no app mobile.

## 2026-06-17

- registrado que `primary_probability*` e `secondary_probability*` em `MarketResponse` são atalhos de leitura derivados da opção líder por `gotrendlabs_market_options.probability_exact`, sem snapshot duplicado em `gotrendlabs_markets`.
- registrada evolução de `FEAT-REP-001` para requisitos adicionais configuráveis em regras de badge, persistidos em `BadgeRuleRequirement` e avaliados com lógica AND pela `BadgeAwardEngine`.
- atualizado contrato administrativo de badges para incluir `requirements`, mantendo contratos públicos/mobile sem expor a estrutura interna de requisitos.
- registrada configuração da badge `Top 10` como `ranking_position <= 10` com requisito adicional `resolved_predictions_count >= 3`.
- registrada evolução de `FEAT-AIAGENT-001` para limite administrável de comentários IA visíveis por mercado em `gotrendlabs_site_config.ai_max_comments_per_market`, com default `1`.
- registrado que o daemon pula mercados que já atingiram esse limite e audita o motivo `market_ai_comment_limit`; comentários ocultos/moderados não contam para o total visível.
- registrado override opcional por agente em `gotrendlabs_ai_agents.max_comments_per_market_override`; quando preenchido, o limite é contado sobre comentários visíveis do próprio bot do agente, e a auditoria de limite é agregada quando todos os candidatos avaliados são bloqueados.

## 2026-06-13

- registrada evolução de `FEAT-REP-001` para tratar badges conquistadas como propriedade histórica: `BadgeDefinition.is_active` controla exibição pública/histórica e `BadgeRule.is_active` controla novas concessões.
- atualizado contrato de reputação/ranking para manter badges pausadas visíveis no catálogo público/autenticado para todos, sem novas concessões, e preservar ranking e compartilhamento público por token para quem já conquistou.
- registrada evolucao de `FEAT-MOBILE-001` para manutencao mobile independente da web, controlada pelo Admin Ops em runtime JSON e aplicada de forma autoritativa pela FastAPI para clientes com `X-GoTrendLabs-Client: mobile`.
- atualizado contrato mobile de `GET /health` para expor `maintenance.web_enabled`, `maintenance.mobile_enabled`, `maintenance.mobile_message`, `checks.api` e `checks.database`, com status degradado quando o backend nao estiver saudavel.
- registrado que a manutencao mobile nao possui entrada operacional visivel nem excecao por papel no app; usuarios publicos, staff e superusers permanecem bloqueados no shell mobile durante a janela.

## 2026-06-12

- registrada evolução de `FEAT-NOTIFY-001`/`FEAT-MOBILE-001` para push FCM real em Android com Firebase local, sender backend via Firebase Admin SDK, channel Android `gtl_default`, payloads seguros e defaults operacionais `none`/dry-run preservados.
- registrada aba Admin Ops `Dispositivos` em Push mobile para observabilidade de `PushDevice` sem expor token bruto.

## 2026-06-11

- registrada evolução de `FEAT-AUTH-001` para OAuth real em Google, Facebook e X, com vínculo seguro por identidade externa ou email verificado pelo provedor.
- registrada política de envio imediato para emails críticos de identidade/acesso já existentes, mantendo eventos de produto e volume no daemon.
- registrada exigência de rodapé institucional automático e customizável por template nos emails transacionais renderizados por `communications`.

## 2026-06-08

- registrada evolução de `FEAT-NOTIFY-001` para push mobile com provider `none`/dry-run, policies/templates/preferências, outbox `PushDelivery`, endpoints FastAPI e Flutter noop.
- atualizada arquitetura mobile para refletir estrutura iOS gerada em `apps/mobile/ios`, mantendo Android como MVP já validado e iOS Simulator como preparação local.
- atualizados contratos de base URL mobile para separar Android emulator (`10.0.2.2`), iOS Simulator/Chrome local (`127.0.0.1`) e aparelho físico (`<ip-do-mac>`).
- atualizados critérios de aceite mobile para simulação iOS local com Xcode completo, CocoaPods, device iOS listado por `flutter devices` e bases locais via `127.0.0.1`.
- atualizado estado operacional de FEAT-MOBILE-001 para remover iOS Simulator dos gaps e manter TestFlight/App Store, push, offline e QA visual amplo como pendências futuras.

## 2026-06-07

- criadas specs iniciais de mobile Flutter: `mobile-flutter.md`, `mobile-api-contracts.md`, `mobile-mvp.md`, `mobile-ux.md` e `mobile-acceptance.md`.
- registrada direção visual mobile dark-first inspirada nas imagens fornecidas pelo usuário, com cards fortes de mercado, detalhe com hero, abas `Visao geral`/`Comunidade`, bottom navigation e bottom sheets, sem copiar identidade de terceiros.
- adicionadas skills mobile locais para arquitetura, UX, contratos API, testes, implementação Flutter e governança docs/memória.
- atualizado status operacional, integration map, known gaps e README mobile para refletir que as specs existem, mas o projeto Flutter ainda não foi criado.

## 2026-06-06

- registrada evolução de `FEAT-OPSLOG-001` para daemon de produção com intervalo de 300 segundos e defaults de saúde 7/21 minutos no Dashboard Admin Ops.
- registrada evolução de `FEAT-SUGGEST-001` para categoria de sugestão baseada na taxonomia ativa administrada, endpoint público `GET /taxonomy` e validação backend contra categoria inexistente/bloqueada.
- registrada evolução de `FEAT-AUTH-001` e `FEAT-WALLET-001` para indicação bonificada com código opcional no cadastro, ledger `reward_referral`, configuração `referral_bonus_gtl` no Admin Ops e UI contextual em carteira/perfil.
- registrada evolução de `FEAT-AUTH-001` para prefixo `@` fixo no identificador editável e retorno contextual `← Voltar` com fallback seguro.
- registrada evolução de `FEAT-AIAGENT-001` para auditoria administrativa com rótulos e explicações de tipo, status e motivo, preservando códigos técnicos.
- atualizado `frontend-web.md` para fechamento legível em cards de mercado e remoção de ISO cru em labels públicos.

## 2026-06-05

- registrada evolução de `FEAT-NOTIFY-001` para emails transacionais com `EmailTemplate`, `EmailDelivery`, `EmailConfirmationToken`, templates editáveis no Admin Ops, daemon de outbox e retries por provider.
- registrada decisão operacional de agrupar templates e logs de entrega em `Politica de Emails`, mantendo edição PT-BR com variáveis documentadas, preview local de HTML e listagem de outbox sem expor links sensíveis.
- registrada evolução de `FEAT-AUTH-001` para confirmação de email por token expirável, login limitado até confirmação, reenvio limitado e recuperação de senha sem exposição pública do `reset_url`.
- atualizado contrato de eventos para refletir outbox transacional antes do event bus dedicado.
- registrado que o remetente operacional padrão é `no-reply@gotrendlabs.com.br` e que host, porta, TLS/SSL e usuário SMTP são parâmetros não sensíveis administráveis quando o fallback SMTP for usado.

## 2026-06-09

- registrada evolução de `FEAT-NOTIFY-001` para provider Resend via API HTTPS, mantendo outbox/templates/retries/logs existentes e segredo somente em `GOTRENDLABS_RESEND_API_KEY`.
- atualizado Admin Ops/Dashboard para configuração e saúde de email provider-aware, com SMTP genérico como fallback e Resend como opção transacional.
- registrado requisito de recuperação de senha com tentativa de envio imediato após commit e links absolutos nos templates transacionais.

## 2026-05-24

- registrada evolução de `FEAT-AUTH-001` para reset administrativo auditado por Admin Ops e exibição de `Sua progressão` para operadores sem participação no ranking público
- atualizado contrato `backend-api.md` com `POST /admin/users/{user_id}/password-reset`, nota obrigatória, bloqueios de autoação/conta desativada e permissão restrita para alvos administrativos
- registrada evolução de `FEAT-REP-001` para expor badges conquistadas resumidas no ranking e filtro público por evento
- atualizado contrato `reputation-ranking.md` para aceitar `event`, retornar `selected_event` e serializar eventos na taxonomia de filtros
- registrada decisão de UI de manter o handle como identificação principal da linha e renderizar badges após o nome/handle, com excedentes resumidos como `+N`
- registrada evolução de `FEAT-AIAGENT-001` para cobertura maior do ciclo de comentários IA, com candidatos configuráveis, tentativas LLM limitadas e fallback em respostas não publicáveis/validação segura
- registrado que erro real de provedor LLM interrompe tentativas do ciclo para evitar cascata de custo durante instabilidade
- registrada atualização de `scheduler-jobs.md` para explicitar avaliação local de múltiplos mercados e limite de chamadas LLM por ciclo
- registrada regra de cautela factual do prompt IA para evitar afirmações técnicas específicas, eventos, números, anúncios ou fontes ausentes do contexto do mercado
- registrada evolução de `FEAT-OPSLOG-001` e `FEAT-AIAGENT-001` para retenção configurável separada de logs técnicos e auditoria IA no Admin Ops
- registrado que o purge operacional passa a usar `created_at` e o prazo atual de `gotrendlabs_site_config`, afetando também registros antigos

## 2026-05-17

- criada a estrutura canônica de specs técnicas, contratos, decisões, testes e memória operacional
- adicionadas 11 feature specs iniciais derivadas da spec funcional principal
- adicionadas 4 skills canônicas no repositório para edição de specs, orquestração, guarda arquitetural e estratégia de testes
- adicionado `feature-changelog.md` para histórico granular por feature
- adicionadas 4 skills técnicas por stack para Django, FastAPI, Postgres e operações assíncronas/comunicações
- adicionada governança de workflows para mudanças multi-documento, retomada e reversão lógica
- reforçada a presença de testes no guia rápido e nas regras de conclusão
- adicionado índice de skills em `tools/skills/gotrendlabs/README.md`
- adicionada revisão de governança em `governance-review.md`
- adicionadas skills `gotrendlabs-software-architect` e `gotrendlabs-test-engineer`
- workflows e guia atualizados para incluir arquitetura/segurança e testes executáveis
- registrada implementação parcial de `FEAT-AUTH-001` com backend FastAPI como autoridade de autenticação/sessão e Django como consumidor web
- registrada evolução de `FEAT-AUTH-001` com aceite obrigatório de política, edição de perfil e exclusão lógica de conta
- registrada implementação parcial de `FEAT-WALLET-001` e `FEAT-REP-001` com núcleo de usuário persistido em PostgreSQL e exposto pela FastAPI
- registrada projeção `gotrendlabs_wallet_balances` para leitura rápida de saldo sem substituir o ledger auditável
- registrada implementação parcial de `FEAT-MARKET-001` e `FEAT-MARKET-002` com mercados públicos persistidos em PostgreSQL, expostos pela FastAPI e consumidos pelo Django

## 2026-05-18

- registrada primeira fatia real do Admin Ops para mercados e taxonomia
- formalizada proteção por usuário `is_staff=true` nas rotas administrativas
- documentado cancelamento lógico de mercado e auditoria simples em `gotrendlabs_admin_events`
- atualizados gaps restantes de admin para separar CRUD básico real de fluxos operacionais ainda pendentes
- registrada regra de opções por tipo: `binary` fixo `SIM`/`NAO` em `50%`/`50%` e `multiple` com duas ou mais opções distribuídas automaticamente
- registrado filtro real por status no browse administrativo de mercados
- registrada persistência de `close_at`, `close_timezone`, `auto_close_enabled` e thumbnail de card para mercados administrativos
- registrada regra de não salvar mercado administrativo com campos operacionais mínimos ausentes
- registrado `closes_in` como rótulo automático derivado de `close_at`, removendo entrada manual do admin
- registrado fechamento manual para mercados sem daemon automático, com transição para `locked` e evento `market.lock`
- registrada resolução manual com `resolved_at`, `resolution_timezone`, payout/reputação, undo operacional e refund total de cancelamento
- registrada preservação de gráficos de consenso após resolução usando previsões `open` e `resolved`
- registrado que `close_label` é mensagem pública opcional e que percentuais ficam em `gotrendlabs_market_options.probability_exact`
- registrado vínculo obrigatório entre categoria/subcategoria da taxonomia persistida no editor administrativo de mercado
- registrada primeira fatia real de filas operacionais para sugestão de mercado e feedback
- registrado envio autenticado ou guest com nome/email para feedback e sugestão
- registrado browse administrativo de filas com data de criação, tipo do item e ordenação por data
- registrada regra de ação específica por fila: conversão em rascunho apenas para sugestão de mercado e crédito operacional para itens com usuário cadastrado
- registrado bloqueio de crédito duplicado por item de fila e inclusão de `reward_suggestion` no contrato de wallet
- registrada regra de integridade para opções de mercado: opções com previsões vinculadas não podem ser removidas/recriadas silenciosamente durante edição administrativa
- registrada primeira fatia real de comentários em mercados com criação autenticada, like/dislike, ocultação/restauração administrativa e trilha via eventos administrativos
- registrados detalhes de contrato/arquitetura da FEAT-COMMENT-001: endpoints públicos/admin, tabelas de comentário/reação, handles `@`, ações iconizadas e fallback local de desenvolvimento
- registrada atualização da FEAT-MARKET-001 para filtros rápidos funcionais no feed, destaque principal por visualizações excluindo `draft`/`canceled` e contador de curtidas nos cards

## 2026-05-19

- registrada reconciliação operacional idempotente para mercados `canceled` com previsões `open`, incluindo `dry-run`, evento `market.cancel_reconcile` e preservação de reputação
- registrado que o cancelamento administrativo deve validar ausência de previsões abertas após refund antes de concluir a transição para `canceled`
- registrada evolução de FEAT-REP-001 para badges administráveis com catálogo público, imagem, regras controladas e concessão automática idempotente
- adicionados contratos públicos e administrativos de badges em `reputation-ranking.md`
- registradas responsabilidades de `backend-api`, `frontend-web` e `admin-ops` para impedir cálculo de elegibilidade fora do domínio
- registrado que regras temáticas de badge usam categoria/subcategoria da taxonomia dinâmica cadastrada no Admin Ops
- explicitado no contrato administrativo de badges quais campos são obrigatórios e quais permanecem opcionais no formulário
- registrado que o browse administrativo de badges expõe categoria/subcategoria da regra para auditoria operacional rápida
- registrado que o formulário administrativo de badges exibe prévia do card público antes de salvar
- registrado que badges possuem imagem padrão/tema claro e imagem opcional para tema escuro, com troca visual por tema e fallback
- registrada `BadgeAwardEngine` como fonte única de avaliação e persistência de conquistas de badge por eventos de domínio
- registrado compartilhamento MVP de badge conquistada via rota web autenticada, ação nativa do navegador e fallback de cópia de link/texto
- ajustado gap restante de badges naquele momento para separar compartilhamento básico de card social completo; gap posteriormente reduzido pela evolução de compartilhamento social com Open Graph/Twitter
- registrada evolução do compartilhamento social para pergunta, resultado e badge com links por rede, metadados Open Graph/Twitter e imagem social dinâmica
- registrado uso de origem pública configurável para crawlers sociais e aviso quando o host local não for rastreável
- registrado token opaco em link público de badge conquistada para evitar exposição de identificador direto de usuário
- registrado fallback visual de thumbnail para mercado sem imagem/thumb, aplicado ao feed e às imagens sociais
- registrada política pública de uso com leitura em modal no cadastro, mantendo aceite obrigatório versionado
- registrado que login/cadastro mantêm navegação pública compacta e retorno `← Feed` no primeiro painel de conteúdo
- registrado ticket de onboarding do cadastro selecionado por maior `view_count` entre mercados publicados não cancelados, excluindo `draft` e `canceled`, com fallback para mercado mais recente em empate/ausência de visualizações

## 2026-05-20

- registrado que telas públicas de autenticação mantêm rodapé público compartilhado além de navegação, tema e retorno `← Feed`
- registrado que login/cadastro expõem provedores sociais iniciais Google, Facebook e X como affordances iconizadas, mantendo OAuth real como gap
- registrado que títulos de cards de mercado navegam para o detalhe como redução de atrito no feed público
- registrada área Config no Admin Ops para modo manutenção em runtime JSON e parâmetros SMTP não sensíveis em banco
- registrado que segredo SMTP permanece fora do banco/interface, via ambiente ou secret manager
- registrada separação operacional de credenciais PostgreSQL por serviço Django/FastAPI com fallback local `POSTGRES_*`
- registrado `GET /admin/dashboard-summary` como contrato staff agregado para Dashboard Admin Ops
- registrado que o Dashboard Admin Ops usa métricas de saúde operacional sem consultas locais espalhadas no Django

## 2026-05-23

- registrada implementação parcial de `FEAT-NOTIFY-001` com inbox in-app persistida, sino no topo, contador de não lidas, dropdown e marcação de leitura
- registrado `comment_count` público em `MarketResponse`, cards da home/feed e detalhe do mercado, derivado apenas de comentários `visible`
- registrada regra de notificações sociais para mercados participados por previsão: nova previsão, curtida de mercado, comentário e curtida em comentário
- registrada regra de notificações sistêmicas para crédito recebido, mercado participado fechado/resolvido e badge recebida
- registrado roteamento contextual do dropdown: badges para `/badges/`, créditos para `/wallet/`, eventos de mercado para o detalhe do mercado e comentários para `#comments`
- atualizado mapa de integração para refletir JSON runtime de manutenção, `gotrendlabs_site_config`, SMTP via ambiente e resumo operacional centralizado na FastAPI
- registrada `MarketLifecycleEngine` como ponto central do ciclo operacional de mercado no backend
- registrado `GET /admin/markets/{slug}/resolution-audit` como contrato staff read-only para auditoria de resolução
- registrado que Admin Ops mostra ação “Auditoria” em mercados resolvidos, com paginação de 10 participantes e legenda de ledger
- registrada rodada QA hard com 100 usuários simulados em `docs/research/qa-simulacao-hard-100-usuarios-20260520.md`
- adicionada skill `gotrendlabs-prediction-markets` para curadoria assistida de mercados de previsão com dados internos, trends sociais, diversidade, links exatos de verificação e anti-repetição
- adicionado guia `docs/guides/gotrendlabs-prediction-markets-skill.md` para uso da skill de curadoria de mercados

## 2026-05-21

- reforçada a skill `gotrendlabs-prediction-markets` para exigir validação da fonte de resolução antes de aceitar mercados sugeridos
- documentado que a validação pode usar navegador local, browser automation, APIs, web search, ORM, banco ou APIs internas quando necessário
- adicionado `Status de validacao da fonte` ao formato esperado de mercados sugeridos
- registrado que operadores (`staff`/`superuser`) não recebem bootstrap público de reputação, wallet inicial, badges ou atividade social
- registrado que thumbnails de mercado com `image_url` devem ser imagens puras do evento, sem título/texto embutido, mantendo HTML/API como fonte de verdade de metadados
- documentado o lote editorial seed de 27 mercados em `docs/specs/state/editorial-seed-markets-20260521.md`
- registrado que `/profile/` usa dados reais de `gotrendlabs_user_profiles`, com `display_name` como fonte principal do nome editável
- registrado marcador administrativo `is_bot` restrito a Admin Ops, com filtro, badge, edição auditada e sem exposição pública
- registrado que ajuste manual de wallet da própria conta é permitido para operadores, mantendo auditoria, enquanto outras autoações sensíveis seguem bloqueadas
- registrado que `GT₵ distribuídas` exclui créditos de `staff` e `superuser`
- registrado que ticket de previsão não pré-seleciona opção, orienta escolha explícita, usa radio obrigatório e apresenta estado sem saldo disponível
- registrado que card social de mercado exibe opções/probabilidades e CTA editorial para o detalhe do mercado

## 2026-05-22

- ampliada a skill `gotrendlabs-prediction-markets` para suportar categoria `cripto`, fontes cripto/on-chain e aviso obrigatório de que mercados cripto não caracterizam recomendação de investimento
- documentado seed DEV de 3 mercados cripto em `docs/specs/state/editorial-seed-markets-20260521.md`, mantendo status `draft`, taxonomia idempotente e thumbs locais autorais
- documentado lote aprovado `Mercado > Cripto` com aviso no nível da subcategoria, eventos por moeda e comando idempotente `seed_crypto_markets_20260522`

## 2026-10-09 — thumbnails IA no Admin Ops

Feature FEAT-THUMB-001 e contrato admin-thumbnails formalizados antes de codificar, com critérios do prompt autorizado. ADR-0012 registra fila PostgreSQL/worker dedicado, uncertain sem retries pagos, volume privado/promoção, gpt-5.4-mini + gpt-image-1.5 e gate editorial vigente. OpenAPI, migration/grants, env sem segredos, runbook, matriz de testes e estados sincronizados. Homologação real/produção pendentes.

- 2026-10-09 — FEAT-THUMB-001 v1.1: OpenAI substituído por Bedrock Runtime/Core com adapters SD3.5/Ultra selecionáveis em Configurações do Sistema; modelo/região/proporção/timeout/cotas/retenção, API staff/MFA e auditoria, migration 0023/grants, snapshot por job e bloqueio explícito de legados. Sem consumo pago/deploy; 37 testes e 9 verificações complementares aprovados, browser/checks aprovados; migration/grants e runtime local verificados.

## 2026-10-09 — Composição do editor de mercados

Editor Admin Ops com cabeçalho unificado, formulário/prévia alinhados, grupos separados de resolução/card/notas, textos mais compactos, upload/geração lado a lado e ajuda recolhível. Rolagem da tabela contida e cache CSS renovado. Feature/aceite/workflow atualizados; contratos e revisão humana preservados. Browser responsivo e sete testes Web aprovados, sem consumo ou deploy nesta etapa.

## 2026-10-09 — Correções dos findings de thumbnails

Dockerfile corrigido e check incluído no CI. Compensação de upload diferencia rejeição/resultado desconhecido e reconcilia pela API; publicação não é repetida. Decisão inline preserva polling quando validação nativa impede envio; versão JS administrativa atualizada. Novos testes de resposta perdida/erro local/reconciliação e browser nativo aprovados. Build/mounts locais pendentes por falta de espaço Docker, sem consumir IA ou modificar produção.

## 2026-10-09 — Preparação do fechamento FEAT-THUMB-001

Fonte da verdade reconciliada com autorizações e duas solicitações Core concluídas no DEV, sem nova inferência no fechamento. Deploy prepara subdiretório de mídia e acompanha executor quando seu segredo estiver instalado, inclusive pausado; CI inclui build completo. PR/CI/merge/implantação dependem de aprovação da descrição; branch local preservada. Qualidade visual sistemática e acesso produtivo não declarados validados. WFLOW-20261009-THUMBNAIL-CLOSE-001.

## 2026-10-09 — Imagens IA de badges

FEAT-BADGE-IMAGE-001, admin-badge-images, ADR-0013 e aceite/runbook formalizados. Fronteiras, fila tipada, orçamento global por contagem, ownership/editor e política universal light/dark definidos antes do código. OpenAPI/migration/grants, arquitetura e memória atualizados; não confundir evidência local com homologação produtiva.

## 2026-10-09 — Fechamento técnico e rollout de thumbnails

PR #143 integrada, merge 15b980585982cfa6706a38d57016614a41ba956d. CI final 408 testes aprovados/1 skip por roles CI, build completo aprovado. Actions 37963430113 e 37964971891 Success (PR e main/produção), SSM deploy Success. Migrations 0022–0024 aplicadas; defaults SQL preservam inicialização existente. Executor dedicado/grants/mounts/UIDs verificados: worker privado RW, API privado RO/subpath público RW, sem candidatas no proxy/Django. Arquivo efêmero próprio removido.

Habilitação produtiva de thumbnails autorizada e concluída: banco e GTL_THUMB_ENABLED=1 na API/worker, Core/Oregon/3:2/180s, limites 10/5/50 por 24h e retenção 24h. Configuração preservada, alteração auditada como operação de sistema; backups de envs 0600 no host. Fila vazia antes/depois, nenhuma chamada paga iniciada, nenhum mercado editado pelo assistente. Site/API HTTP 200 e configurações anônimas 401. Branch local preservada.

Fechamento técnico concluído; homologação de fluxo autenticado/MFA, consumo produtivo e qualidade visual real permanece pendente. Não afirmar inferência real validada em produção. Fonte externa atual: [PR #143](https://github.com/wscardua/gotrendlabs/pull/143) e [Actions](https://github.com/wscardua/gotrendlabs/actions/runs/37964971891). Registros anteriores descrevem etapas históricas, substituídos por esta atualização para estado operacional atual. Evidência documental pós-rollout preparada localmente para versionamento na próxima PR aprovada.


## 2026-10-09 — Correção: par de imagens de badges

Correção clara/escura concluída: 78 testes aprovados (73 geração/regressões/deploy em 96.927s + 5 reinício/concessões/catálogo/formulário em 10.185s), PostgreSQL isolado e provedor simulado. Browsers badge e thumbnail aprovados; prévias distintas, troca de tema, ausência da variante escura preserva o par anterior, undo/uploads/late response/submit. Django check, migration drift, OpenAPI, Node e diff aprovados. Executor DEV reiniciado sem job em execução (PID 95376), chave/flag mantidas ativas, API health 200. Nenhuma inferência paga iniciada pela correção; dois jobs DEV anteriores de versão universal permanecem preservados. Suíte completa de 431 testes é evidência da versão anterior, não foi repetida nesta alteração. Homologação real da coerência entre variantes e PR/deploy próprios seguem pendentes.


## 2026-10-09 — Correções de review de imagens administrativas

Correções implementadas e verificadas localmente: salvamento pendente cancelado ao mudar seleção durante decode, instrução para novo Salvar e nenhuma submissão herdada pela próxima geração; identidade estável por badge/sessão, cache limitado com fallback determinístico para badge salva, criação rotacionada apenas após sucesso. 77 testes/83.891s aprovados em PostgreSQL isolado; 3 cenários de identidade/recarga rechecados após fallback determinístico (2.267s). Browser de mercados aprovou reprodução com decode suspenso, manual/Aguardar/gerar outra/Salvar; browser de badges aprovou o mesmo cenário e recarga/polling sem POST extra. Regeneração no teste aguarda a nova candidate_id, evitando corrida entre casos. Django/migrations/OpenAPI/Node/diff aprovados; assets DEV conferidos por HTTP. Sem nova inferência paga, alteração produtiva, commit ou PR; fonte técnica atual nos contratos/features/runbook e estado operacional. Homologação real de pares e PR/deploy próprios permanecem pendentes.


## 2026-10-09 — Fechamento técnico local / WFLOW-20261009-BADGE-CLOSE-001

Validação final do fechamento: 442 testes aprovados em 776.623s, PostgreSQL isolado e provedor simulado, log local badge-close-full-tests.log. Browsers de badges e mercados aprovados, incluindo recarga sem geração extra e escolha manual durante decode sem submit herdado; Django, migration drift, OpenAPI, Node, shell, Compose, diff e Dockerfile check aprovados (sem avisos). Build completo remoto, PR/merge/deploy e habilitação produtiva de badges aguardam aprovação da descrição. Nenhuma inferência paga nesta validação. Homologação humana/MFA e coerência visual real permanecem pendentes; thumbnails produtivas PR #143 preservadas.


## 2026-10-09 — Estado produtivo atual de imagens administrativas

PR #144 integrada em main edac7c7; CI PR e main/build/deploy Success, 442 testes em ambos com um skip por roles CI ausentes (cenário aprovado localmente). Migration0025/grants/constraints/mounts/executor conferidos; habilitação auditada de badges concluída, política de thumbnails preservada. Stable Image Core/Oregon, badges1:1, timeout180s, limites10 imagens/operador e50 globais por24h,5 solicitações/item, retenção24h. Fila vazia, sem inferência paga ou alteração de mercados/concessões reais. Branch local preservada. Manutenção pública ativa preservada; Admin Ops exige login. Homologação humana/MFA e coerência visual real permanecem pendentes. [Evidência produtiva](../testing/ai-badge-images-production-20261009.md). Registros anteriores são histórico das etapas.


## 2026-10-09 — Incidente: auditoria do worker de imagens

Incidente WFLOW-20261009-IMAGE-WORKER-AUDIT-FIX-001: primeira solicitação produtiva informada permanece queued, sem started_at/provider_id/arquivo. Worker falha na auditoria porque thumbnail_service.event importava main, ativando exigência de pepper/TOTP exclusivos da API. Diagnóstico por SSM/read-only e probes com rollback, sem inferência ou mutação em mercados. Correção local usa diretamente admin_events, sem distribuir segredos HTTP ao executor. Teste em subprocesso com ambiente production, segredos HTTP vazios e provedor simulado cobre claim, sucesso e eventos persistidos. Rollout corretivo e conclusão da solicitação real ainda pendentes; não afirmar latência do provedor, acesso efetivo ou qualidade real por esse incidente.
