# Contrato: integrações de agentes — FEAT-MCP-001

Versão 1.5 — 2026-10-10. Implementado localmente; Dot/deploy pendentes. Autoridade: [feature](../features/mcp-editorial-agents.md) e [ADR-0011](../decisions/ADR-0011-mcp-editorial-integrations.md). Rotas abaixo estão na implementação FastAPI e no snapshot OpenAPI; sua disponibilidade externa depende do rollout autorizado.

## Revisão 1.5 — documento único (2026-10-10)

`editorial_record` contém somente `policy_version`, `policy_hash` e `document` (texto não vazio, máximo 60.000 caracteres). O documento cobre contexto/duplicidade, pergunta/regras/prazos, fontes com URL e data, contingências/responsável e pendências/conclusão. Campos estruturados anteriores recebem `422`. `GET /admin/agent-editorial-reviews/{id}` fornece o documento persistido e a política atual; a migração 0004 converte registros anteriores sem alterar snapshots históricos. Drafts/agendados exigem nova revisão humana; a 0005 preserva a decisão histórica de mercados já publicados.

`POST /admin/agent-editorial-reviews/{id}/assessment` recebe `editorial_record` com documento, `expected_revision`, `snapshot_hash`, `decision` e `confirmed` booleano. `confirmed=true` é obrigatório para `approved`; devolução/rejeição o dispensam. O endpoint mantém locks, transação, auditoria, snapshot e versionamento. As antigas rotas `/record` e `/decision` deixam de existir. O MCP usa o mesmo schema de draft, mas não possui ferramenta para enviar `confirmed` ou decisão humana. O gate de publicação exige confirmação na decisão documental, além de revisão/hash/política/conteúdo atuais. As descrições anteriores abaixo são apenas históricas.

Na aprovação, o texto deve conter a seção `PENDÊNCIAS E CONCLUSÃO` com `Pendências para aprovação: nenhuma` como primeira linha de conteúdo e sem duplicá-la; a ausência, outro valor ou simples acréscimo após pendências já listadas aparece como `unresolved_editorial_gaps` em `pending` e devolve `422` ao tentar aprovar. A linha opcional `Anúncio esperado: <datetime ISO 8601 com offset>` é validada contra `close_at` pela FastAPI; formato inválido ou duplicado devolve `invalid_editorial_announcement` e fechamento igual/posterior devolve `close_after_editorial_announcement`, ambos `422`. `Anúncio esperado: não informado` documenta ausência de horário conhecido. Esta regra mantém um só campo editável, sem interpretar a suficiência factual do restante do texto.

## Princípios

Resposta de registro OAuth/DCR omite metadados opcionais ausentes: `scope`, quando presente, é string, nunca `null` (RFC 7591). Registro técnico não concede acesso; consentimento staff/MFA, PKCE S256, redirect exato, resource e scopes continuam obrigatórios.

REST interno de domínio e ferramentas MCP possuem schemas versionados e mapeamento explícito. FastAPI autentica e autoriza toda chamada. Erros são tipados, sem traceback/segredos. Identidades, audience e scopes nunca vêm de argumentos confiados ao modelo.

## Catálogo MCP v1

| Ferramenta | Escopo | Comportamento |
| --- | --- | --- |
| `get_editorial_policy` | `editorial:read` | Manual, ficha, E01–E11, versão, hash e data; somente versão aprovada |
| `get_taxonomy` | `catalog:read` | IDs e hierarquia disponível; bloqueados não podem ser usados |
| `search_markets` | `catalog:read` | Busca paginada por texto/estado/evento/período; projeção mínima para duplicidade |
| `get_market` | `catalog:read` | Conteúdo editorial mínimo; ficha privada somente para integração proprietária |
| `get_editorial_signals` | `metrics:read` | Agregados, período, atualização, humano/bot e disponibilidade |
| `validate_market_draft` | `drafts:write` | Validação sem gravação de mercado; erros estruturais, pendências e semelhantes |
| `create_market_draft` | `drafts:write` | Cria draft e ficha, com idempotência; retorna ID, revisão e URL administrativa |
| `update_market_draft` | `drafts:write` | Somente draft próprio editável; exige revisão esperada e idempotência |
| `submit_draft_for_review` | `drafts:submit` | Snapshot e estado editorial em revisão; nunca publica |
| `get_draft_review` | `editorial:read` | Retorna parecer/pedidos de ajustes do próprio draft |

`tools/list` e `tools/call` respeitam grants; ocultar ferramenta não substitui check de execução. Rotular leituras e escritas corretamente. Não expor método para simular clique staff ou chamar rota arbitrária. Documentos editoriais podem ser resources adicionais; manter ferramenta equivalente para clientes que não usam resources.

## API de gestão humana

- `GET /admin/agent-integration-responsibles?after={id}`: opções humanas elegíveis (conta ativa, staff OU superuser, não bot), com `items` contendo apenas `id`, `display_name`, `username`; paginação por ID em lotes de 100, `has_more` e `next_cursor`. Exige a mesma sessão administrativa MFA; não exposto por ferramentas MCP.
- `GET/POST /admin/agent-integrations`: listar/criar.
- `GET/PATCH /admin/agent-integrations/{id}`: detalhe/configuração com versão esperada.
- `POST .../{id}/activate`, `/pause`, `/revoke`: transições auditadas.
- `POST .../{id}/credentials`: emissão única; `POST .../{id}/credentials/{credential_id}/revoke`: revogação.
- `GET .../{id}/connections` e `POST .../{id}/connections/{grant_id}/revoke`: grants OAuth.
- `POST .../{id}/transfer-responsibility`: transferência explícita auditada.
- `GET /admin/agent-editorial-reviews`: fila paginada.
- `GET /admin/agent-editorial-reviews/{market_id}` e `POST .../{market_id}/decision`: parecer humano (`approved`, `returned`, `rejected`) com revisão/hash esperado e nota.

Todas exigem conta ativa staff OU superuser + MFA. Ambos administram todas as integrações igualmente. CSRF no frontend, verificações também na API. IDs relacionados devem pertencer à integração indicada.

## API de domínio para agentes proposta

Prefixo `/integrations/editorial`: `/policy`, `/taxonomy`, `/markets`, `/markets/{id}`, `/signals`, `/drafts/validate`, `/drafts`, `/drafts/{id}`, `/drafts/{id}/submit`, `/drafts/{id}/review`. POST/PATCH conforme ferramentas. Rotas nunca usam `_current_staff_user` com conta administrativa compartilhada para representar o agente.

Prefixo `/internal/agent-integrations`: validação/troca de delegação e ingestão limitada de eventos técnicos. Exige workload MCP e contexto verificável. Rotas internas não devem ser publicadas indiscriminadamente pelo proxy; rede privada é defesa adicional, não substitui autenticação. Definir endpoints OAuth/token/discovery na implementação conforme biblioteca e versão protocolar adotadas; todos documentados e testados.

## Payload de draft

Campos permitidos: `title`, `summary`, `kind` (`binary`/`multiple`), `category_id`, `subcategory_id`, `event_id`, `options` (label/hint), `source`, `resolution_criteria`, `close_at`, `close_timezone`, `editorial_record`. Schema proíbe extras. Limites finitos para textos/listas/evidências definidos em Pydantic e MCP de forma consistente. Binário segue normalização autoritativa existente; múltiplo tem pelo menos duas opções distintas. Backend fornece defaults visuais seguros.

`editorial_record`: `policy_version`, `policy_hash`, justificativa, sinais, cobertura de busca, semelhantes, fontes e evidências por criterion_id. Cada fonte tem URL, finalidade, verificação relatada, momento e extrato. Critério usa `satisfied`/`pending`/`not_verified`; não permite ao agente preencher decisão humana. Campo `expected_revision` é obrigatório na edição/submissão; `idempotency_key` obrigatório em mutações, repassado ao backend como chave validada.

Resposta de mutação: `market_id`, `slug`, `market_status`, `editorial_status`, `revision`, `policy_version`, `admin_url`, `request_id`, `replayed`. Nunca retornar segredo ou notas de outros recursos. Autor/responsável/integração vêm da autenticação.

## Leituras e erros

Paginação: `items`, `next_cursor`, `has_more`, `as_of`, `coverage`; limite default 20, máximo 100. Busca truncada informa limite e não comprova deduplicação completa. Métricas incluem unidade, período, timezone e `availability`; `null` representa ausência, não zero.

Erros estáveis: `unauthenticated` (401), `forbidden_scope`/`integration_inactive`/`resource_forbidden` (403 ou 404 para recurso não visível), `not_found` (404), `version_conflict`/`idempotency_conflict`/`draft_not_editable` (409), `validation_failed` (422), `quota_exceeded` (429 com retry quando aplicável), `dependency_unavailable` (503). OAuth usa erros padronizados próprios. No MCP mapear erros de ferramenta/protocolo corretamente e registrar resultado de negócio mesmo com HTTP 200.

## Modelagem lógica mínima

Entidades de integração, credencial, grant/token, idempotência/cotas e ficha/revisão são novos dados de domínio; não são novos logs paralelos. Aplicação Django responsável pelas migrations é escolhida pelo implementador preservando labels históricos; runtime de escrita permanece FastAPI.

Relações: integração → responsável; credencial/grant → integração; grant OAuth → usuário consentidor; token → origem revogável; draft → integração criadora; revisão/ficha → mercado + versão; eventos administrativos → integração/executor + humano responsável + request/execução. Restrições únicas para chaves idempotentes e versões. Índices para estado, expiração, quota e consultas administrativas. Revogar não apaga autoria. Separar grants para novos modelos nas roles migrator/runtime.

Schemas HTTP entram no OpenAPI durante implementação, não nesta entrega documental. Ferramentas MCP possuem teste de paridade com schemas de domínio e versão de contrato.

## Evidência e operação

[Resultados locais por critério](../testing/mcp-editorial-results.md), [runbook OAuth/serviço](../../guides/mcp-editorial-pilot.md). Campos opcionais `editorial_revision`/`editorial_status` em MarketResponse e `expected_revision` na edição administrativa preservam consumidores web/mobile existentes. Somente o editor administrativo de draft com autoria técnica precisa enviar revisão esperada. Migrations mantêm defaults SQL vazios nos campos aditivos de correlação para inserts anteriores.

## Revisão 1.1 — aprovação para publicação de mercados de integração

Slug é derivado do título no backend, colisões recebem sufixo numérico; não muda na edição MCP e não identifica replay. MarketLifecycleEngine exige parecer humano aprovado/currente para todos os mercados, sob locks mercado/ficha. Sem ficha, publicação bloqueia. Retorna 409 com código `editorial_approval_required` e mensagem operacional quando decisão/revisão/hash/política/conteúdo não forem atuais. Publicar versão aprovada não salva campos do editor. Revisão detalhada informa `publication_gate_enforced=true` e `publication_gate_scope=all_markets`; gate universal.

A projeção administrativa MarketResponse acrescenta `editorial_market_id` opcional para link da ficha, junto de editorial_revision/status. Projeções públicas não fornecem dados da ficha. Listagem web em `/admin-ops/integrations/`, criação em `/admin-ops/integrations/new/`; gestão existente preservada.

## Preparação humana da ficha — revisão 1.2

`PATCH /admin/agent-editorial-reviews/{market_id}/record`: staff/superuser com MFA, payload estrito `expected_revision`, `editorial_record` (mesmo contrato validado), `submit_for_review` boolean default false e `note` humana obrigatória. Mercados draft/scheduled/open/locked; lock mercado/ficha, conflito 409 para revisão antiga, cria snapshot e incrementa revisão, limpa parecer anterior. Estado preparation ou in_review conforme ação. Evento `agent.record.human_update` com integração/ator humano. Não altera mercado, cota de agente ou permissões MCP. Reenvio sem mudanças após sucesso exige revisão atual; PRG impede repetição acidental no navegador.

A UI permite atualizar evidências/status/fontes/lacunas e salvar ou salvar/enviar para revisão. Nenhum status é satisfeito automaticamente. Aprovação continua separada: todos os critérios/fontes exigidos verificados independentemente, sem lacunas e política atual. Devolução/rejeição continuam possíveis com pendências. Erros preservam contexto da ficha.

Detalhe administrativo da revisão também expõe `criteria` da política atual para rotular a preparação; erros de aprovação preservam `validation_failed` e apresentam orientação humana, com lista `pending` quando aplicável.

## Parecer humano em uma ação — revisão 1.3

`POST /admin/agent-editorial-reviews/{market_id}/assessment`: payload ReviewDecision (`expected_revision`, `snapshot_hash` atual, `decision`, `note`, `verified_criteria`, `verified_source_indexes`) + `editorial_record`. Staff/superuser MFA; mercados draft/scheduled/open/locked, versão/hash atuais. Salva ficha/snapshot e decisão na mesma transação com locks existentes; erro reverte ficha, revisão, estado e eventos. Suporta preparação/revisão/devolvido e nova avaliação de versões de draft. Sem submissão humana prévia. Relato do agente não pré-seleciona atestação humana. UI verifica cada critério/fonte uma vez e registra parecer; publicar continua separado. Contratos /record e /decision preservados para compatibilidade.

### Projeção humana das evidências

A UI pode apresentar URLs sugeridas no texto editável de evidência e converter citações explícitas às fontes cadastradas em source_indexes, eliminando seleções redundantes. O contrato JSON estruturado e a verificação independente verified_source_indexes permanecem iguais. Alterar/remover a citação atualiza o vínculo; fonte obrigatória ausente ou não verificada impede aprovação. Não inferir verificação humana das sugestões. Erros pending são apresentados com motivos legíveis, incluindo declared_gaps.

A confirmação web gaps_resolved é intenção explícita do operador para registrar editorial_record.gaps vazio no assessment existente. Não cria permissão/contrato MCP nem aprovação automática. Lacunas originais permanecem nos snapshots anteriores; erros preservam o texto submetido e a confirmação para correção, sem persistência parcial.

## Revisão universal 1.4 — 2026-10-07

Criação administrativa e conversão de sugestões inicializam ficha pendente com integration_id nulo; MCP mantém autoria técnica. Migração aditiva 0003 preenche legados sem alterar estado/provas nem inventar aprovação. Listagem e detalhe staff incluem origem, revisão e link para todos os mercados. MarketResponse administrativo acrescenta editorial_origin (human/mcp/null) e closure_configuration_errors; projeções públicas mantêm null/[] sem divulgar ficha.

Parecer/preparo em mercados open/locked altera apenas ficha/histórico; terminais resolved/sealed/canceled são somente leitura. Permissões MCP não se ampliam. O snapshot cobre também auto_close_enabled e campos do card, impedindo publicação de configuração diferente da versão aprovada. Gate central valida fechamento antes da assinatura: close_at futuro com timezone, close_timezone IANA válido e modo boolean explícito, em modo automático e manual.

A UI admite adicionar fonte e citar sua URL na evidência; apenas confirmação explícita atribui verificação humana. Lacunas e critérios continuam dependentes de atestação independente.

### Notas administrativas e precisão de prazo

`MarketResponse.admin_notes` é preenchido apenas no contexto administrativo; público recebe vazio e a projeção MCP não inclui o campo. O editor humano preserva segundos/microssegundos de `close_at` fornecidos pelo MCP, sem alterar o instante ao abrir e reenviar o formulário.

## Compatibilidade de registro OAuth — correção Codex

POST `/oauth/register` ignora metadados não reconhecidos (RFC 7591 seção 2), incluindo `application_type: native` enviado pelo Codex. Extras não são persistidos, refletidos na resposta nem usados para permissões. Campos reconhecidos continuam validados: redirect HTTPS/loopback sem fragmento, grants code/refresh, response code e autenticação pública none. Schemas de domínio/admin continuam proibindo extras.

O metadata público do adaptador preserva exatamente o issuer configurado e usado pela FastAPI/RFC 9207, sem adicionar barra por normalização de URL; anuncia os cinco scopes. Registro não autentica nem concede integração: consentimento humano/MFA, PKCE, resource e autorização por scope continuam obrigatórios.
