# Aceite FEAT-THUMB-001

Data: 2026-10-09. Banco PostgreSQL isolado, provider simulado, nenhuma chamada paga.

| Grupo | Evidência executável |
|---|---|
| Staff/MFA/draft/acesso indevido | ThumbnailIntegrationTests.test_staff_mfa_and_direct_draft_guards |
| Contexto atual sem salvar/privacidade/campos necessários | current_context_and_private_data_guard_no_autosave; disabled_and_required_fields_only |
| Idempotência/cotas/claims simultâneos | idempotency_and_active_limit; limits_reserved_and_no_poll_generation; concurrent_requests_and_worker_claim; global_capacity_is_reserved_between_markets |
| Timeout/recusa/indisponibilidade/acesso/resposta inválida | ThumbnailProviderTests; unknown_result_never_repeats_and_queue_recovers |
| Reinício/abandono/fencing/sem replay pago | abandoned_and_fenced_late_result; unknown_result_never_repeats_and_queue_recovers |
| Armazenamento/arquivo inválido/revogação | storage_invalid_and_revoked_authorization |
| Preview protegido e URL derivada | preview_protected_and_confirm_derives_url |
| Outra candidata/incompleta/expirada/conflito de imagem/status | invalid_other_expired_or_incomplete_candidate; confirmation_concurrent_image_and_publication_conflicts; confirmation_waits_for_publication_lock_and_storage_failure_is_safe |
| Falha após promoção/rollback de mercado/image_url público | atomic_market_patch_preserves_url_on_failure |
| Limpeza preserva vinculados/ativos e remove órfãos | prune_preserves_linked_and_running_and_removes_orphans |
| Upload antigo não sobrescreve/compensação/CSRF/resultado publicação | ThumbnailWebTests |
| UI conteúdo sem salvar/loading/sucesso/erro/regeneração/undo/File/escolha manual tardia/alteração de texto/submit continuar ou aguardar | tests/thumbnail_browser.py, template/JS/CSS reais em Chrome headless, sem pageerrors |
| Recorte central/card pequeno desktop/mobile | fixtures games/technology/sports em .runtime/thumbnail-browser/card*.png; conferência visual |
| Upload/fallback público/agentes/gate editorial | suíte Django completa isolada; testes existentes não mudados |

Homologação de modelos/imagens reais permanece pendente. Confirmar modelos com acesso da conta e autorização de consumo, avaliar identificação imediata, relação específica com pergunta, impacto sem texto, centro seguro, neutralidade e alternativas perceptíveis. Não extrapolar fixture para qualidade real ou engajamento.

Resultados finais e comandos ficam no workflow WFLOW-20261009-AI-THUMBNAILS-001. CI/deploy/mounts produtivos não executados.

Resultados: 389 testes de regressão/OK (715.312s), 23 focados finais/OK (29.649s), duas corridas adicionais/OK e repetição direcionada de falha de armazenamento/compensação negada/OK. Browser incluiu também formulário separado de publicação, bloqueio de seleção não revisada e texto alterado durante geração. Django check, makemigrations --check, OpenAPI --check, sintaxe JS, lint F, Compose config --no-env-resolution e diff whitespace aprovados. Logs locais em .runtime/thumbnail-validation; screenshots em .runtime/thumbnail-browser.

## Revisão Bedrock e Configurações do Sistema (v1.1)

- 37 testes/OK em PostgreSQL isolado (52.845s): 29 da feature revisada e 8 regressões de configuração geral/mobile/email/agentes Bedrock. Logs: `.runtime/thumbnail-validation/thumbnail-bedrock-regression.log`.
- 5 testes complementares/OK (2.144s): adapters dos três modelos, HTTP 424/timeout/recusa/resposta inválida, whitelist de dados, uma invocação, sem fallback/retry, job legado sem chamada e lease derivado do timeout congelado. Log `thumbnail-bedrock-adapter.log`.
- 4 testes após schema PUT completo/OK (2.874s): autorização/auditoria/snapshot, formulário independente, erro preservando escolha e CSRF. Log `thumbnail-bedrock-settings.log`.
- Browser Chrome/template/CSS/JS reais, HTTP simulado: modelo selecionável, botão independente sem submeter parâmetros de agentes/email, teclado, desktop/mobile; fluxo completo anterior de editor e três recortes aprovado, sem chamadas pagas. Log `thumbnail-bedrock-browser.log`; screenshots `config-thumbnails*.png` e cards em `.runtime/thumbnail-browser` inspecionados.
- Migration 0023 aplicada somente no DB local; modelo Core/defaults consultados, privilégios FastAPI de configuração/fila confirmados. Live OpenAPI contém GET/PUT settings e 10 parâmetros obrigatórios no PUT, acesso anônimo 401; site local HTTP 200. Worker local atualizado com kill switch 0.
- Checks Django, migration drift, OpenAPI snapshot, Node, Ruff F, Compose config e diff whitespace aprovados. Homologação paga de credencial/modelos/qualidade, produção/IAM/assinatura/mounts continua pendente; não confundir metadata de disponibilidade ou fixtures com inferência validada.

## Ajuste do editor completo (2026-10-09)

Sete testes existentes ThumbnailWebTests/ThumbnailSettingsWebTests passaram (0.154s); Django check/diff whitespace passaram. Browser com template/CSS/JS reais e respostas simuladas manteve todos os fluxos anteriores; editor em 1440/1100/390 px sem overflow horizontal, temas claro/escuro e ajuda recolhível, screenshots inspecionadas. Tabela de participantes usa rolagem interna focável. Evidência `.runtime/thumbnail-validation/thumbnail-editor-layout.log` e screenshots `editor-*.png`. Sem chamadas ao provedor nesta revisão.


## Correções após review de branch (2026-10-09)

- 33 testes da feature aprovados em PostgreSQL isolado, 36.607s (`thumbnail-review-fixes-tests.log`): novos casos de upload confirmado no backend com resposta perdida, reconciliação indisponível/HTTP sem status/408/499/5xx, rejeição 422 com compensação e erro local anterior ao envio. Nenhuma repetição automática nem ação de publicar após reconciliação.
- Browser Chrome/template/CSS/JS com provedor simulado aprovado (`thumbnail-review-fixes-browser.log`): validação nativa habilitada em dois casos novos; campo obrigatório esvaziado durante decisão mantém polling/seleção após sucesso e permite salvar; corrigir enquanto geração ainda ativa permite continuar uma vez. Fluxos anteriores preservados, sem consumo.
- Dockerfile check sem warnings, Django/OpenAPI/Node/Ruff F/diff/YAML e Compose config aprovados. Check Dockerfile incluído no CI; CI remoto não executado.
- Build completo falhou por falta de espaço do Docker Desktop no apt, após superar o parser. Ensaio adicional de volumes isolados usando imagem não root já existente também encontrou ENOSPC na escrita; seus dois volumes próprios foram removidos, sem remover recursos preexistentes. Logs `thumbnail-review-build.log` e `thumbnail-review-mounts.log`. Build/UIDs/mounts atuais continuam pendentes em ambiente com espaço; não marcar esses ensaios como aprovados.

## Fechamento — estado atual (2026-10-09)

Consulta somente leitura ao banco DEV confirmou duas solicitações Bedrock/Core em succeeded, última conclusão 13:42:28 UTC. Logs existentes do executor confirmam HTTP 200 no Runtime Oregon. Consumo local foi autorizado anteriormente; nenhuma inferência adicional foi iniciada nesta etapa. Isso comprova acesso/invocação local, sem validar qualidade visual, modelos alternativos ou acesso produtivo. Os registros acima descrevem suas etapas históricas e não revogam essa evidência posterior.

Rollout agora inclui bootstrap conservador do subdiretório de mídia e o executor nos ciclos de build/parada/migration/restart quando `.env.thumbnails.prod` estiver instalado, inclusive se o recurso estiver pausado. Testes de deploy simulados verificam falha de migration sem restart, profile opcional e ordem de preparação do mount; não operam Docker/AWS reais. CI executará build completo antes do merge.

Checks finais: 43 testes/40.812s aprovados em PostgreSQL isolado (33 thumbnails e 10 deploy), browser aprovado com todos os cenários existentes e validação nativa real. Django check, migration drift, OpenAPI snapshot, Node, Dockerfile check sem warnings, shell syntax e diff whitespace aprovados. Logs `thumbnail-close-tests.log` e `thumbnail-close-browser.log`. Build completo local anterior bloqueado por espaço; build remoto e mounts produtivos não executados nesta preparação. Não somar execuções repetidas como quantidade de testes distintos.

## Correção de CI da PR #143

Primeiro CI: build completo aprovado, 408 testes executados com 2 erros/1 skip. Inserções SQL históricas de SiteConfig omitiam colunas novas não nulas, pois defaults Django não ficam no PostgreSQL. Migration 0024_thumbnail_runtime_defaults fornece defaults SQL conservadores, mantendo inicialização existente e recurso off. Ambos os testes que falharam passaram localmente (2/5.798s, DB isolado). Repetir CI completo antes de merge.

## 2026-10-09 — Fechamento técnico e rollout de thumbnails

PR #143 integrada, merge 15b980585982cfa6706a38d57016614a41ba956d. CI final 408 testes aprovados/1 skip por roles CI, build completo aprovado. Actions 37963430113 e 37964971891 Success (PR e main/produção), SSM deploy Success. Migrations 0022–0024 aplicadas; defaults SQL preservam inicialização existente. Executor dedicado/grants/mounts/UIDs verificados: worker privado RW, API privado RO/subpath público RW, sem candidatas no proxy/Django. Arquivo efêmero próprio removido.

Habilitação produtiva de thumbnails autorizada e concluída: banco e GTL_THUMB_ENABLED=1 na API/worker, Core/Oregon/3:2/180s, limites 10/5/50 por 24h e retenção 24h. Configuração preservada, alteração auditada como operação de sistema; backups de envs 0600 no host. Fila vazia antes/depois, nenhuma chamada paga iniciada, nenhum mercado editado pelo assistente. Site/API HTTP 200 e configurações anônimas 401. Branch local preservada.

Fechamento técnico concluído; homologação de fluxo autenticado/MFA, consumo produtivo e qualidade visual real permanece pendente. Não afirmar inferência real validada em produção. Fonte externa atual: [PR #143](https://github.com/wscardua/gotrendlabs/pull/143) e [Actions](https://github.com/wscardua/gotrendlabs/actions/runs/37964971891). Registros anteriores descrevem etapas históricas, substituídos por esta atualização para estado operacional atual. Evidência documental pós-rollout preparada localmente para versionamento na próxima PR aprovada.


2026-10-09 — Feedback de espera em badges e thumbnails: botão Gerando… desabilitado, painel inline destacado com spinner e aviso Aguarde/alguns minutos/edição dos demais campos. Indicador permanece até prévias carregadas, não desaparece por upload manual e encerra em sucesso/erro; preserva imagem anterior e decisões continuar/aguardar. Anúncio role=status/aria-live e reduced-motion. Browser Chrome real com respostas simuladas aprovado para ambos (badge-loading-browser.log, thumbnail-loading-browser.log), screenshot de loading inspecionado; Django check/Node/diff aprovados, assets locais verificados via HTTP e cache versionado. Sem chamada paga ou implantação dessa alteração.


## 2026-10-09 — Correções de review de imagens administrativas

Correções implementadas e verificadas localmente: salvamento pendente cancelado ao mudar seleção durante decode, instrução para novo Salvar e nenhuma submissão herdada pela próxima geração; identidade estável por badge/sessão, cache limitado com fallback determinístico para badge salva, criação rotacionada apenas após sucesso. 77 testes/83.891s aprovados em PostgreSQL isolado; 3 cenários de identidade/recarga rechecados após fallback determinístico (2.267s). Browser de mercados aprovou reprodução com decode suspenso, manual/Aguardar/gerar outra/Salvar; browser de badges aprovou o mesmo cenário e recarga/polling sem POST extra. Regeneração no teste aguarda a nova candidate_id, evitando corrida entre casos. Django/migrations/OpenAPI/Node/diff aprovados; assets DEV conferidos por HTTP. Sem nova inferência paga, alteração produtiva, commit ou PR; fonte técnica atual nos contratos/features/runbook e estado operacional. Homologação real de pares e PR/deploy próprios permanecem pendentes.


## 2026-10-09 — Estado produtivo atual de imagens administrativas

PR #144 integrada em main edac7c7; CI PR e main/build/deploy Success, 442 testes em ambos com um skip por roles CI ausentes (cenário aprovado localmente). Migration0025/grants/constraints/mounts/executor conferidos; habilitação auditada de badges concluída, política de thumbnails preservada. Stable Image Core/Oregon, badges1:1, timeout180s, limites10 imagens/operador e50 globais por24h,5 solicitações/item, retenção24h. Fila vazia, sem inferência paga ou alteração de mercados/concessões reais. Branch local preservada. Manutenção pública ativa preservada; Admin Ops exige login. Homologação humana/MFA e coerência visual real permanecem pendentes. [Evidência produtiva](../testing/ai-badge-images-production-20261009.md). Registros anteriores são histórico das etapas.


## 2026-10-09 — Incidente: auditoria do worker de imagens

Incidente WFLOW-20261009-IMAGE-WORKER-AUDIT-FIX-001: primeira solicitação produtiva informada permanece queued, sem started_at/provider_id/arquivo. Worker falha na auditoria porque thumbnail_service.event importava main, ativando exigência de pepper/TOTP exclusivos da API. Diagnóstico por SSM/read-only e probes com rollback, sem inferência ou mutação em mercados. Correção local usa diretamente admin_events, sem distribuir segredos HTTP ao executor. Teste em subprocesso com ambiente production, segredos HTTP vazios e provedor simulado cobre claim, sucesso e eventos persistidos. Rollout corretivo e conclusão da solicitação real ainda pendentes; não afirmar latência do provedor, acesso efetivo ou qualidade real por esse incidente.

Validação local: 68 testes aprovados em 105.804s, PostgreSQL isolado/provedor simulado; regressão isolada do worker production sem pepper/TOTP também aprovada (1 teste/2.480s). Django check, OpenAPI atual e diff aprovados. Nenhuma chamada paga ou mudança produtiva; publicação/CI/deploy corretivos aguardam aprovação da descrição. Logs worker-audit-* em .runtime/badge-validation.


2026-10-09 — Rechecagem após isolar GTL_BADGE_PUBLIC_ROOT nos testes de thumbnails: 2 testes (limpeza e worker production) aprovados em 4.743s. Dois arquivos locais removidos pelo teste de limpeza antes da correção foram restaurados byte a byte das candidatas privadas originais; mídias preservadas e nenhum efeito em produção. Esse ajuste é somente do ambiente de testes.


## 2026-10-09 — Recuperação produtiva do executor

Incidente resolvido pela PR #146/main b033afe4, CI PR37981039913 e main37981803447/build/deploy Success (443 testes, um skip de roles CI). SSM deploy3e165a28 e verificação0d584e9f Success: auditoria do worker sem main, serviços ativos. Pedido original cdbe1f42-d75b-44ec-8f0c-11ece3d6952e succeeded em 6.451679s de processamento, arquivo privado presente e ID de provedor registrado; sem nova solicitação/replay pelo assistente ou salvamento/publicação do mercado. Primeira execução Core produtiva iniciada pelo operador confirma acesso efetivo do token/modelo, mas não avaliação visual ou custo faturado. [Evidência externa](https://github.com/wscardua/gotrendlabs/pull/146). Recibo atualizado localmente para próximo versionamento autorizado.


## Relevância visual / WFLOW-20261009-THUMBNAIL-RELEVANCE-001

Inspeção em navegador autenticado de candidatas existentes: FURIA/CS2 c96cea44 gerou homem em fumaça; Corinthians feminino 33b275ca gerou rosto/lápis. Leitura SSM c9905c63 confirmou contexto completo e modelo Ultra/v2. Nenhuma nova inferência. V3 deve manter assunto/resumo antes do estilo, pistas de futebol feminino/CS2, campos permitidos, recorte central e neutralidade; v2 deve manter montagem histórica. Homologação visual real v3 pendente e não comprovada por mocks.

Validação local v3: 70 testes aprovados em 96.136s, PostgreSQL isolado/provedor simulado (thumbnails e badges). Django check, compilação Python e git diff --check aprovados. Ruff não disponível no ambiente virtual; nenhuma instalação realizada. Nenhuma nova chamada paga, alteração de produção ou PR nesta etapa. Homologação visual v3 pendente. Log local ignorado: `.runtime/badge-validation/thumbnail-relevance-tests.log`. Inspeção de candidatas existentes em navegador não iniciou geração nem confirmou/salvou mercados.


2026-10-09 — Pedido do usuário para reproduzir PRD em DEV: criadas via primitive de domínio _insert_market_draft três fixtures locais #9/#10/#11 (prefixo dev-thumb-) com perguntas, resumos, taxonomia, opções, fontes/critérios e prazos equivalentes aos mercados Fluminense×Palmeiras, Corinthians feminino e FURIA/CS2. Exportação PRD somente leitura SSM8c362d7a, sem admin_notes/PII/credenciais/imagens. Drafts sem image_url, sem destaque e auto_close_enabled=false; mercados DEV preexistentes #6/#7/#8 preservados. Contexto/opções conferidos contra exportação; editorial/auditoria inicializados pelo backend. Executor DEV reiniciado com fila vazia (PID75405), código market-thumbnail-bedrock-v3; API health200 e editor protegido302 para login. DEV mantém configuração Core existente; candidatas PRD inspecionadas usavam Ultra. Nenhuma solicitação de geração criada, inferência paga, publicação ou mutação PRD. Recibos ignorados em .runtime/badge-validation/prod-market-context-dev.json e dev-market-copies-receipt.json. Operador realizará avaliação visual local; PR/deploy continuam aguardando aprovação.


2026-10-09 — Usuário ampliou pedido para todos os mercados PRD no DEV. Inventário produtivo integral, sem filtro de slug/status, SSM353ba4f8 Success: exatamente três mercados (#35/#36/#37), todos draft. Conferência local comprova cobertura 3/3 pelas fixtures existentes #9/#10/#11; nenhuma nova cópia criada, evitando duplicação ou sobrescrita das edições locais. Mercados preexistentes #6/#7/#8 preservados. Consulta somente leitura em PRD; sem geração paga. Recibo do catálogo integral em .runtime/badge-validation/all-prod-markets-index.json.


2026-10-09 — Etapa histórica v4, substituída pela v5: prompt market-thumbnail-bedrock-v4 sem temas, entidades, cenas ou condicionais fixos por categoria. Pergunta/resumo/classificação atuais determinam o assunto; regras fixas somente de composição, qualidade, neutralidade e segurança. Substitui a proposta local v3 de âncoras temáticas, rejeitada pelo usuário. Executor DEV reiniciado com fila vazia, PID82614; imagens/estados v3 existentes preservados, sem reinterpretar/repetir solicitações. V3 queued não chama provedor (unsupported_instructions); v2 histórico preservado. Produção e modelos não alterados; sem nova inferência paga. Validação v4: 70 testes de thumbnails/badges aprovados em 102.686s com PostgreSQL isolado/provedor simulado; rechecagem dos 6 testes do provedor aprovada em 0.053s, incluindo invariância do template entre temas, contexto completo e rejeição de v3 sem invocação. Django check, compilação Python e diff aprovados. Nenhuma inferência paga iniciada; qualidade real permanece pendente de avaliação pelo operador. Log thumbnail-dynamic-tests.log e thumbnail-dynamic-provider-tests.log em .runtime/badge-validation.


2026-10-09 — Direção vigente v5: interpretação semântica em modelo textual Bedrock seguida da imagem configurada. Sem templates/presets de assunto ou composição por categoria. Configuração textual própria GTL_THUMB_PLANNER_* congelada no job; default openai.gpt-oss-20b/Mantle us-east-1, timeout45s, saída2048tokens (allowlist20b/120b; timeout10–120s/tokens512–4096). Uma chamada textual e uma imagem por reserva, sem retry/fallback; checkpoints planner/image sob fencing/elegibilidade, lease soma timeouts e brief final privado persistido para auditoria/regeneração. Falha textual impede imagem. V2 histórico preservado; v3/v4 não reinterpretados. Substitui as soluções v3/v4; badges/comentários/interface não mudam. ADR-0014 formaliza a mudança justificada pelos exemplos reais irrelevantes e exigência do usuário. Validação v5: 75 testes aprovados em 103.334s, PostgreSQL isolado/provedor simulado, cobrindo planejamento→imagem, falhas/recusa/timeout sem imagem, checkpoints/fencing, preservação de uso após erro desconhecido e ausência de replay, snapshot/lease, regeneração e badges. Dois testes adicionais dos agentes textuais aprovados (3.271s e1.718s), sem alteração de seu comportamento. Django check, OpenAPI --check, compilação Python e diff aprovados. Executor DEV reiniciado sem geração ativa, PID93387; v5 posteriormente homologado informalmente pelo operador no DEV, conforme recibo abaixo. Nenhuma inferência paga pelo assistente ou mudança produtiva; commit local preparado no fechamento, PR/deploy aguardam aprovação. Credencial/acesso e avaliação visual informal do novo fluxo confirmados no DEV; homologação PRD permanece pendente. Logs thumbnail-semantic-*.log em .runtime/badge-validation.


## Homologação DEV e preparação de PRD v5

2026-10-09 — Homologação DEV v5: operador informou “em dev local parece estar legal” e autorizou preparar PRD. Consulta local somente leitura confirmou três jobs v5 succeeded (34ccb8f0, bcc57be2, 5cb97131), iniciados pelo operador, com planner openai.gpt-oss-20b/Mantle us-east-1 e imagem Core/us-west-2. Tempos de processamento: 17.804s, 9.663s e 15.883s; uso textual retornado registrado, sem afirmar custo faturado. Acesso efetivo e aprovação visual informal do fluxo DEV confirmados; não substituem matriz visual sistemática, medição de engajamento ou homologação do token/modelo em PRD. Nenhuma inferência paga iniciada pelo assistente. Próxima etapa: aprovação da descrição atualizada da PR, CI completo, merge/deploy e verificação produtiva; preservar modelo de imagem e políticas atuais de PRD.


Fechamento local em 2026-10-09: suíte completa de 450 testes aprovada em 862.190s, sem skips, com PostgreSQL isolado e provedores simulados; credenciais de inferência vazias e geração desabilitada no processo de testes. Banco de testes destruído ao concluir. Log ignorado: .runtime/badge-validation/thumbnail-semantic-close-full-tests.log. Django check, snapshot OpenAPI, compilação Python e diff aprovados; checklist de alteração de feature/arquitetura/contratos/ADR/testes/memória conferido. Commit local autorizado preparado somente com 22 arquivos de código/configuração de exemplo/docs/testes; mídia DEV, credenciais e mudanças das outras iniciativas excluídas e preservadas. Submissão da PR com descrição em português, merge e rollout aguardam a aprovação solicitada pelo usuário.
