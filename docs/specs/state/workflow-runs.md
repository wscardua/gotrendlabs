# Workflow Runs

## WFLOW-20261010-MCP-TOOLS-SCHEMA-001

- Origem: solicitação de alinhar `tools/list` ao documento editorial único, testar validação produtiva sem criação e versionar checklist/modelo sem alterar a política v1.2.
- Diagnóstico: metadados da conexão MCP direta e `apps/mcp/server.py` já apresentam o schema documental; o cadastro `MyGoTrendLabsMCP-v2` do cliente ainda declara `justification`/`search_coverage` obrigatórios e rejeita `document` antes de alcançar o servidor. A validação direta em produção aceitou o documento e retornou `unresolved_editorial_gaps`, `agent_reported`, sem criação/aprovação/publicação. Captura bruta de `tools/list` no endpoint produtivo ainda pendente.
- Escopo local: adicionar `checklist_hash` e `record_template_hash` à resposta de política, contrato OpenAPI, testes de `tools/list` real e documentação. Não alterar mercado, grant/permissão, agenda nem versão/hash da política aprovada.
- Preparação de fechamento: revisão de impacto identificou apenas o recibo de teste fora do índice; ele está incluído no conjunto a versionar. Feature/contrato, testes, OpenAPI, guia, integration map, status, changelogs, lacunas e checklist de fechamento reconciliados. A spec funcional não muda: trata-se de metadados técnicos do MCP, sem regra editorial nova ou fronteira arquitetural nova; ADR adicional não é necessário. Suíte MCP/editorial e adaptador: 56 testes/OK em PostgreSQL isolado; teste integrado repetido após asserções finais: 1/OK; Django check, OpenAPI --check, compilação e diff passaram.
- Estado: teste integrado de `tools/list` e retorno de política passou com serviço e OAuth; OpenAPI atualizado. Commit local e descrição de PR em preparação; PR/CI/merge/deploy aguardam aprovação da descrição pelo usuário. A atualização do cadastro externo do cliente permanece pendente mesmo após o deploy. [Evidência](../testing/mcp-tools-schema-20261010.md). Não marcar a FEAT-MCP-001 ampla como concluída enquanto Dot/piloto autenticado e teste humano produtivo seguirem pendentes.

## WFLOW-20261010-EDITORIAL-DOCUMENT-001

- Tipo: alteração da FEAT-MCP-001 / FEAT-EDITORIAL-001. Usuário autorizou implementar documento único e pediu branch nova após buscar `origin/main`.
- Branch: `feature/editorial-single-document-review`, worktree isolado baseado em `origin/main` 9b798ea; alterações do checkout original preservadas.
- Escopo revisado pelo usuário: contrato JSON exclusivo com documento autoritativo, sem campos estruturados, `/record` ou `/decision` em runtime. Admin Ops mantém um textarea e um check; MCP usa o mesmo schema. Migration 0004 converte registros anteriores uma única vez, preserva snapshots e exige nova revisão humana para drafts/agendados; conversões acima de 60.000 caracteres falham sem truncar.
- Estado anterior à correção: implementação e migration 0004 DEV concluídas; seis fichas convertidas, URLs/evidências preservadas. Backup privado ignorado em `.runtime/dev/editorial-before-single-document.json`. Suíte MCP/editorial: 70 testes aprovados; dois testes regressivos representativos de mercado também aprovados. Dot externo, CI e deploy pendentes.
- Fechamento local da revisão de impacto em 2026-10-10: um único campo de texto e um check preservados. A FastAPI apresenta `unresolved_editorial_gaps` na validação/painel e exige declaração explícita de resolução para aprovar; anúncio esperado conhecido com offset deve ser posterior a `close_at`. Migration 0005 restaura a última decisão histórica apenas dos mercados já publicados/terminais que vieram da ficha estruturada; drafts/agendados continuam exigindo novo parecer. Em DEV, seis documentos persistidos, quatro drafts em preparação e dois mercados publicados (`locked`/`resolved`) com aprovação histórica novamente visível; URLs/evidências preservadas, sem publicação ou reabertura. Suíte MCP/editorial e dois fluxos de mercado: 75 testes aprovados em 191,264 s; quatro testes focais após o ajuste final de `pending` e da regra textual também aprovados em 11,740 s. Django check, migration drift, OpenAPI --check, compilação e diff aprovados; processos DEV em auto-reload e saúde API/web/MCP 200. Checklist de feature, contrato, arquitetura, testes e memória conferido. Dot externo, CI e deploy permanecem pendentes.
- Preparação do fechamento em 2026-10-10: `origin/main` continua em 9b798ea, sem divergência; GitHub MCP autenticado. Contrato, runbook, README, status e lacunas reconciliados para que a revisão 1.5 seja a fonte vigente, mantendo revisões anteriores identificadas como histórico. Status: implementação local concluída, PR/CI/merge/migração e smoke produtivo aguardam apresentação e aprovação da descrição pelo usuário. Preservar a branch local. FEAT-MCP-001 permanece parcial pela homologação externa Dot/piloto autenticado, independente do fechamento desta melhoria.
- Fechamento produtivo em 2026-10-10: usuário aprovou a descrição e continuidade; PR #148 integrada em `main` df3a691. CI PR/main 454 testes/OK (um skip CI); Actions 38060102537 build/deploy Success. Snapshot RDS anterior ao merge disponível. Migrations 0004/0005 aplicadas; quatro documentos convertidos com 27 URLs de fontes preservadas e quatro drafts ainda em preparação. Inventários de mercados/opções/previsões mantidos. API, MCP e controles de acesso responderam conforme contrato. [Recibo produtivo](../testing/editorial-document-production-20261010.md). Status desta melhoria: `concluido` para implementação, publicação e smoke técnico; piloto Dot e avaliação humana autenticada em PRD continuam pendentes, sem fechar a FEAT-MCP-001 ampla. Branch local preservada.


## WFLOW-20261009-THUMBNAIL-RELEVANCE-001

- Fechamento local em 2026-10-09: suíte completa de 450 testes aprovada em 862.190s, sem skips, com PostgreSQL isolado e provedores simulados; credenciais de inferência vazias e geração desabilitada no processo de testes. Banco de testes destruído ao concluir. Log ignorado: .runtime/badge-validation/thumbnail-semantic-close-full-tests.log. Django check, snapshot OpenAPI, compilação Python e diff aprovados; checklist de alteração de feature/arquitetura/contratos/ADR/testes/memória conferido. Commit local autorizado preparado somente com 22 arquivos de código/configuração de exemplo/docs/testes; mídia DEV, credenciais e mudanças das outras iniciativas excluídas e preservadas. Submissão da PR com descrição em português, merge e rollout aguardam a aprovação solicitada pelo usuário.

- 2026-10-09 — Preflight PRD somente leitura: SSM3c6b5fda confirmou SHA b033afe4, seis serviços ativos e credencial Bedrock presente no executor (valor não exposto), switch ambiental 1, defaults textuais 20b/us-east-1. Consulta inicial da política precisou ser corrigida por uso inadequado do context manager; SSM8f95b96a concluiu Success sem stderr: thumbnail_enabled=true, Core/stability.stable-image-core-v1:1, us-west-2, 3:2, timeout180s, limites operador50/mercado50/global50 por24h e retenção24h; nenhum queued/running. Valores atuais substituem o recibo histórico de defaults10/5 no que se refere à configuração efetiva observada, sem alterar os defaults da spec. Preservar essas escolhas no deploy. Nenhuma mutação produtiva ou inferência; preflight não comprova acesso de inferência Mantle do token produtivo.

- 2026-10-09 — Homologação DEV v5: operador informou “em dev local parece estar legal” e autorizou preparar PRD. Consulta local somente leitura confirmou três jobs v5 succeeded (34ccb8f0, bcc57be2, 5cb97131), iniciados pelo operador, com planner openai.gpt-oss-20b/Mantle us-east-1 e imagem Core/us-west-2. Tempos de processamento: 17.804s, 9.663s e 15.883s; uso textual retornado registrado, sem afirmar custo faturado. Acesso efetivo e aprovação visual informal do fluxo DEV confirmados; não substituem matriz visual sistemática, medição de engajamento ou homologação do token/modelo em PRD. Nenhuma inferência paga iniciada pelo assistente. Próxima etapa: aprovação da descrição atualizada da PR, CI completo, merge/deploy e verificação produtiva; preservar modelo de imagem e políticas atuais de PRD.

- Direção vigente: usuário exige interpretação semântica, não template. Implementar v5: planejador textual Bedrock separado dos comentários, conceito específico derivado do contexto, seguido de modelo de imagem configurado. Chamada adicional justificada por falha real v2 e rejeição das soluções v3/v4. ADR-0014 registra etapas/cotas/checkpoints/configurações; Validação v5: 75 testes aprovados em 103.334s, PostgreSQL isolado/provedor simulado, cobrindo planejamento→imagem, falhas/recusa/timeout sem imagem, checkpoints/fencing, preservação de uso após erro desconhecido e ausência de replay, snapshot/lease, regeneração e badges. Dois testes adicionais dos agentes textuais aprovados (3.271s e1.718s), sem alteração de seu comportamento. Django check, OpenAPI --check, compilação Python e diff aprovados. Executor DEV reiniciado sem geração ativa, PID93387; v5 posteriormente homologado informalmente pelo operador no DEV, conforme recibo abaixo. Nenhuma inferência paga pelo assistente ou mudança produtiva; commit local preparado no fechamento, PR/deploy aguardam aprovação. Credencial/acesso e avaliação visual informal do novo fluxo confirmados no DEV; homologação PRD permanece pendente. Logs thumbnail-semantic-*.log em .runtime/badge-validation. Evidências v3/v4 são históricas.

- Etapa histórica v4 (substituída pela v5): usuário rejeitou temas fixos no prompt. Remover condicionais/âncoras por futebol/CS2; instruções v4 inteiramente orientadas pelos campos atuais, com regras fixas somente de composição/qualidade/neutralidade. Diagnóstico DEV: 3 jobs v3 succeeded e 1 failed, nenhum ativo; manter histórico/candidatas sem replay. V3 não será reinterpretada, novos pedidos usam v4. Validação v4: 70 testes de thumbnails/badges aprovados em 102.686s com PostgreSQL isolado/provedor simulado; rechecagem dos 6 testes do provedor aprovada em 0.053s, incluindo invariância do template entre temas, contexto completo e rejeição de v3 sem invocação. Django check, compilação Python e diff aprovados. Nenhuma inferência paga iniciada; qualidade real permanece pendente de avaliação pelo operador. Log thumbnail-dynamic-tests.log e thumbnail-dynamic-provider-tests.log em .runtime/badge-validation. Evidências anteriores da v3 são históricas.

- 2026-10-09 — Usuário ampliou pedido para todos os mercados PRD no DEV. Inventário produtivo integral, sem filtro de slug/status, SSM353ba4f8 Success: exatamente três mercados (#35/#36/#37), todos draft. Conferência local comprova cobertura 3/3 pelas fixtures existentes #9/#10/#11; nenhuma nova cópia criada, evitando duplicação ou sobrescrita das edições locais. Mercados preexistentes #6/#7/#8 preservados. Consulta somente leitura em PRD; sem geração paga. Recibo do catálogo integral em .runtime/badge-validation/all-prod-markets-index.json.

- 2026-10-09 — Pedido do usuário para reproduzir PRD em DEV: criadas via primitive de domínio _insert_market_draft três fixtures locais #9/#10/#11 (prefixo dev-thumb-) com perguntas, resumos, taxonomia, opções, fontes/critérios e prazos equivalentes aos mercados Fluminense×Palmeiras, Corinthians feminino e FURIA/CS2. Exportação PRD somente leitura SSM8c362d7a, sem admin_notes/PII/credenciais/imagens. Drafts sem image_url, sem destaque e auto_close_enabled=false; mercados DEV preexistentes #6/#7/#8 preservados. Contexto/opções conferidos contra exportação; editorial/auditoria inicializados pelo backend. Executor DEV reiniciado com fila vazia (PID75405), código market-thumbnail-bedrock-v3; API health200 e editor protegido302 para login. DEV mantém configuração Core existente; candidatas PRD inspecionadas usavam Ultra. Nenhuma solicitação de geração criada, inferência paga, publicação ou mutação PRD. Recibos ignorados em .runtime/badge-validation/prod-market-context-dev.json e dev-market-copies-receipt.json. Operador realizará avaliação visual local; PR/deploy continuam aguardando aprovação.

- Estado: correção local concluída e validada; aguardando aprovação da descrição para PR/CI/deploy. Branch fix/market-thumbnail-relevance baseada em main b033afe4; mudanças documentais pós-rollout e mídia DEV preservadas.
- Diagnóstico: leitura produtiva SSM c9905c63 e inspeção autenticada das candidatas existentes c96cea44 (FURIA/CS2: homem em fumaça) e 33b275ca (Corinthians feminino: rosto/lápis). Contexto completo e correto; ambas Ultra, instruções v2. Falha de aderência visual confirmada, causa exata do modelo não comprovada. Nenhuma nova inferência ou mutação produtiva.
- Escopo/aceite histórico v3 (substituído pela v5): assunto e resumo antes do estilo, pistas visuais explícitas de futebol feminino e CS2 quando presentes no contexto, preservando entidades, neutralidade, recortes e campos permitidos. Prompt v3; jobs v2 conservam instruções históricas, badges e agentes não mudam. Uma chamada nativa, sem tradutor/segunda chamada ou troca de modelo. Testes simulados de contextos distintos, versão histórica, dados privados, regeneração e contratos.
- Arquitetura histórica v3 (substituída pelo ADR-0014): alteração somente no adaptador de imagem do backend; sem contratos/migration/novas fronteiras ou ADR estrutural. Referência oficial AWS recomenda assunto, meio, composição e iluminação em linguagem descritiva: https://aws.amazon.com/blogs/machine-learning/understanding-prompt-engineering-unlock-the-creative-potential-of-stability-ai-models-on-aws/.
- Validação: 70 testes aprovados em 96.136s, PostgreSQL isolado/provedor simulado (thumbnails e badges). Django check, compilação Python e git diff --check aprovados. Ruff não disponível no ambiente virtual; nenhuma instalação realizada. Nenhuma nova chamada paga, alteração de produção ou PR nesta etapa. Homologação visual v3 pendente.
- Publicação: mostrar descrição e solicitar aprovação antes da nova PR. Homologação real de relevância v3 pendente; mocks não demonstram qualidade.

## WFLOW-20261009-IMAGE-WORKER-AUDIT-FIX-001

- Tipo: correção de incidente de FEAT-THUMB-001/FEAT-BADGE-IMAGE-001. Operador informou geração produtiva demorando; diagnóstico somente leitura e probes com rollback, sem inferência ou mudanças nos mercados. Branch própria fix/admin-image-worker-audit, base main f18647a; branches anteriores e mídia preservadas.
- Evidência: job cdbe1f42-d75b-44ec-8f0c-11ece3d6952e continua queued, sem started_at/provider_id/arquivo; executor em loop de erro. SSM34b3e49a/2d46395d confirmam switches/grants/claim/elegibilidade. SSM6bd632ac reproduz RuntimeError de password pepper no registro de auditoria antes do commit.
- Causa: thumbnail_service.event importa main e aciona validação de segredos HTTP em produção; worker corretamente não recebe pepper/TOTP.
- Correção/aceite: importar o primitive backend admin_events diretamente, preservando payload/auditoria/transação. Worker produtivo sem segredos HTTP processa jobs com provedor simulado; regressões mercados/badges e agentes. Sem fornecer segredos HTTP ao executor, migrations, alterações de modelo/limites ou replay pago.
- Evidências: Validação local: 68 testes aprovados em 105.804s, PostgreSQL isolado/provedor simulado; regressão isolada do worker production sem pepper/TOTP também aprovada (1 teste/2.480s). Django check, OpenAPI atual e diff aprovados. Nenhuma chamada paga ou mudança produtiva; publicação/CI/deploy corretivos aguardam aprovação da descrição. Logs worker-audit-* em .runtime/badge-validation.
- Isolamento de testes: Rechecagem após isolar GTL_BADGE_PUBLIC_ROOT nos testes de thumbnails: 2 testes (limpeza e worker production) aprovados em 4.743s. Dois arquivos locais removidos pelo teste de limpeza antes da correção foram restaurados byte a byte das candidatas privadas originais; mídias preservadas e nenhum efeito em produção. Esse ajuste é somente do ambiente de testes.
- Estado: concluído para correção/CI/rollout/recuperação do pedido. Usuário autorizou reinício com “pode derrubar se quiser”; pausa do worker somente após confirmar zero jobs running, SSM b6c5ee83 Success.
- Resultado: Incidente resolvido pela PR #146/main b033afe4, CI PR37981039913 e main37981803447/build/deploy Success (443 testes, um skip de roles CI). SSM deploy3e165a28 e verificação0d584e9f Success: auditoria do worker sem main, serviços ativos. Pedido original cdbe1f42-d75b-44ec-8f0c-11ece3d6952e succeeded em 6.451679s de processamento, arquivo privado presente e ID de provedor registrado; sem nova solicitação/replay pelo assistente ou salvamento/publicação do mercado. Primeira execução Core produtiva iniciada pelo operador confirma acesso efetivo do token/modelo, mas não avaliação visual ou custo faturado. [Evidência externa](https://github.com/wscardua/gotrendlabs/pull/146). Recibo atualizado localmente para próximo versionamento autorizado.

## WFLOW-20261009-BADGE-ROLLOUT-DOCS-001

- Tipo: publicação documental do recibo pós-rollout de FEAT-BADGE-IMAGE-001; ligado ao fechamento abaixo. Documentos atualizados com resultados observados após o merge, sem mudança de código/configuração produtiva.
- Status: concluído para revisão documental e publicação da [PR #145](https://github.com/wscardua/gotrendlabs/pull/145), com descrição aprovada pelo usuário. Integração e checks finais têm evidência no estado da própria PR. Branch feature/admin-ai-badges preservada, base edac7c7; recibo preparado no commit d59d211.
- Escopo: evidências PR/Actions/SSM, habilitação auditada, specs/status/gaps/changelogs/mapa/aceite/runbook. Sem nova inferência, deploy ou mudança de domínio.
- Validação: diff e referências conferidos, apenas 12 arquivos docs Markdown; CI leve e ausência de deploy devem ser confirmados antes do merge. Publicação documental não altera serviços produtivos.
- Próxima ação externa: homologação humana/MFA e avaliação real do par mediante autorização de consumo; o recibo aponta PR #144/Actions/SSM e separa esses gates da entrega técnica concluída.

## WFLOW-20261009-BADGE-CLOSE-001

- Tipo: fechamento técnico/publicação de FEAT-BADGE-IMAGE-001 e ajustes do componente compartilhado de thumbnails; implementation-cycle. Usuário autorizou preparar documentação, commit/PR/merge/deploy, condicionando submissão da PR à apresentação e aprovação da descrição. Não remover branch local nem mudanças do checkout original.
- Branch: feature/admin-ai-badges, worktree próprio, HEAD/base origin/main 15b980585982cfa6706a38d57016614a41ba956d; fetch confirmou ausência de divergência. Escopo: par claro/escuro, espera visível, seleção/desfazer/confirmar, recuperação de editor, ajustes de consumo/armazenamento e fechamento documental de thumbnails PR #143. Mídia DEV/envs/logs/screenshots fora da publicação.
- Preparação: arquitetura/contrato/ADR-0013/migration0025/grants/runbook/OpenAPI e aceite reconciliados; dois findings do review corrigidos com testes de regressão. GitHub MCP autenticado como wscardua; nenhuma PR aberta dessa branch. Actions deploy main habilitado, último rollout 37964971891 Success para 15b9805.
- Status: concluído para implementação/integração/rollout/habilitação técnica. Usuário aprovou a descrição e o fluxo remoto com “prossiga”. Commit de implementação18d07c6; PR #144 integrada e produção conferida. Homologação real permanece pendente.
- Validação final do fechamento: 442 testes aprovados em 776.623s, PostgreSQL isolado e provedor simulado, log local badge-close-full-tests.log. Browsers de badges e mercados aprovados, incluindo recarga sem geração extra e escolha manual durante decode sem submit herdado; Django, migration drift, OpenAPI, Node, shell, Compose, diff e Dockerfile check aprovados (sem avisos). Na preparação local, build remoto e rollout ainda aguardavam aprovação; foram posteriormente concluídos conforme resultado produtivo abaixo. Nenhuma inferência paga nesta validação. Homologação humana/MFA e coerência visual real permanecem pendentes; thumbnails produtivas PR #143 preservadas.
- Resultado produtivo: PR #144 integrada em main edac7c7; CI PR e main/build/deploy Success, 442 testes em ambos com um skip por roles CI ausentes (cenário aprovado localmente). Migration0025/grants/constraints/mounts/executor conferidos; habilitação auditada de badges concluída, política de thumbnails preservada. Stable Image Core/Oregon, badges1:1, timeout180s, limites10 imagens/operador e50 globais por24h,5 solicitações/item, retenção24h. Fila vazia, sem inferência paga ou alteração de mercados/concessões reais. Branch local preservada. Manutenção pública ativa preservada; Admin Ops exige login. Homologação humana/MFA e coerência visual real permanecem pendentes. [Evidência produtiva](../testing/ai-badge-images-production-20261009.md).
- Próxima ação: operador homologa fluxo MFA e imagens reais mediante autorização de consumo; registro documental pós-rollout preparado em WFLOW-20261009-BADGE-ROLLOUT-DOCS-001.

## WFLOW-20261009-BADGE-REVIEW-FIXES-001

- Status: concluído localmente. Correções implementadas e verificadas localmente: salvamento pendente cancelado ao mudar seleção durante decode, instrução para novo Salvar e nenhuma submissão herdada pela próxima geração; identidade estável por badge/sessão, cache limitado com fallback determinístico para badge salva, criação rotacionada apenas após sucesso. 77 testes/83.891s aprovados em PostgreSQL isolado; 3 cenários de identidade/recarga rechecados após fallback determinístico (2.267s). Browser de mercados aprovou reprodução com decode suspenso, manual/Aguardar/gerar outra/Salvar; browser de badges aprovou o mesmo cenário e recarga/polling sem POST extra. Regeneração no teste aguarda a nova candidate_id, evitando corrida entre casos. Django/migrations/OpenAPI/Node/diff aprovados; assets DEV conferidos por HTTP. Sem nova inferência paga, alteração produtiva, commit ou PR; fonte técnica atual nos contratos/features/runbook e estado operacional. Homologação real de pares e PR/deploy próprios permanecem pendentes.

- Correções dos dois findings autorizadas pelo usuário: cancelar/finalizar explicitamente salvamento pendente quando a seleção manual muda durante carregamento das prévias; nenhuma geração posterior herda submit. Preservar identidade do editor por badge/sessão para recuperar jobs em recarga, sem nova chamada paga ou acesso entre sessões. Especificação ajustada antes do código; testes de browser e sessão/recuperação previstos. Branch própria preservada, PR/deploy seguem aprovação anterior pendente.

## WFLOW-20261009-BADGE-IMAGES-001

- 2026-10-09 — Feedback de espera em badges e thumbnails: botão Gerando… desabilitado, painel inline destacado com spinner e aviso Aguarde/alguns minutos/edição dos demais campos. Indicador permanece até prévias carregadas, não desaparece por upload manual e encerra em sucesso/erro; preserva imagem anterior e decisões continuar/aguardar. Anúncio role=status/aria-live e reduced-motion. Browser Chrome real com respostas simuladas aprovado para ambos (badge-loading-browser.log, thumbnail-loading-browser.log), screenshot de loading inspecionado; Django check/Node/diff aprovados, assets locais verificados via HTTP e cache versionado. Sem chamada paga ou implantação dessa alteração.

- Correção de escopo autorizada pelo usuário: gerar uma imagem clara e outra escura, substituindo a candidata universal. Spec/contrato v1.1 ajustados antes do código; par indivisível na seleção/confirmacão, duas invocações com reserva de duas unidades global/operador, auditoria por tema e falha parcial sem aplicação/retry. Validações anteriores de 431 testes referem-se à versão universal; Correção clara/escura concluída: 78 testes aprovados (73 geração/regressões/deploy em 96.927s + 5 reinício/concessões/catálogo/formulário em 10.185s), PostgreSQL isolado e provedor simulado. Browsers badge e thumbnail aprovados; prévias distintas, troca de tema, ausência da variante escura preserva o par anterior, undo/uploads/late response/submit. Django check, migration drift, OpenAPI, Node e diff aprovados. Executor DEV reiniciado sem job em execução (PID 95376), chave/flag mantidas ativas, API health 200. Nenhuma inferência paga iniciada pela correção; dois jobs DEV anteriores de versão universal permanecem preservados. Suíte completa de 431 testes é evidência da versão anterior, não foi repetida nesta alteração. Homologação real da coerência entre variantes e PR/deploy próprios seguem pendentes.

- Diagnóstico DEV posterior: mensagem de indisponibilidade causada por badge_image_enabled=false, com chave operacional GTL_THUMB_ENABLED=1. Habilitação local aplicada via serviço auditado após confirmar ausência de jobs badge queued/running; enabled=True, API health 200, web/API/executor ativos. Nenhuma chamada paga iniciada pelo diagnóstico; produção de badges permanece pendente da PR própria.

- Tipo: new-feature; FEAT-BADGE-IMAGE-001. Usuário autorizou prosseguir com feature separada após análise; branch feature/admin-ai-badges em worktree próprio preservando thumbnails e checkout original.
- Etapa: spec/contrato/ADR formalizados antes do código; implementação local concluída e validada; aguardando aprovação da descrição da PR própria. Base reconciliada via fast-forward com main/merge 15b9805 da PR #143; alterações de badges preservadas. PR de badges somente após descrição e aprovação próprias. Sem inferência paga adicional.
- Aceite: criação e edição com contexto atual, par de imagens clara/escura 1:1 e seleção/undo, confirmação no salvamento existente, ownership/editor/versão, privacidade/cotas compartilhadas, executor recuperável sem retry pago. Provedor e regras de concessão preservados.
- Artefatos: ai-badge-images.md, admin-badge-images.md, ADR-0013; queue/migration/grants, API/Django/JS/painel, mounts/runbook/OpenAPI e testes isolados/browser.
- Evidências: 70 testes/77.125s aprovados; browsers badges e thumbnails aprovados, campos/temas/arquivos/late response/native validation/continuar/aguardar. Checks Django/migrations/OpenAPI/Node/Ruff F/shell/Compose/diff aprovados. Suíte completa 431 testes/793.744s aprovada; implementação local concluída, próxima ação apresentar descrição da PR própria para aprovação. Runtime local migrou 0024/0025 e serve esta branch; API/web/executor reiniciados com fila vazia, arquivos públicos/privados preservados sem sobrescrever. Badges off por default; não houve nova inferência paga. Thumbnails integradas e habilitadas em produção com Actions/SSM Success; evidência de fechamento técnico registrada abaixo.

## WFLOW-20261009-THUMBNAIL-CLOSE-001

- Tipo: fechamento via ciclo de implementação/publicação; FEAT-THUMB-001, vinculado às execuções de implementação e review.
- Autorização: revisar fonte da verdade, preparar commit/PR em português e rollout; aguardar aprovação explícita da descrição antes de submeter PR. Preservar branch local e trabalho do checkout original. Merge somente após CI aprovado; acompanhar Actions e verificar implantação/habilitação produtiva.
- Etapa atual: PR #143 integrada em main (15b9805), CI/deploy concluídos e thumbnails habilitadas em produção; inferência paga e homologação humana produtiva pendentes. Evidências finais de rollout registradas ao final deste documento. Feature de badges implementada separadamente, aguardando aprovação da própria PR. Aceite adicional: executor incluído nos deploys seguintes quando seu arquivo de segredo estiver instalado; criação segura do subdiretório de mídia antes dos mounts; CI com build completo. Testes de deploy simulados sem AWS/provedor.
- Evidência inicial (anterior à publicação): main remota atualizada e sem divergência da base; MCP GitHub autenticado, nenhuma PR aberta dessa branch. Consulta somente leitura ao banco DEV confirmou duas solicitações Core/Bedrock succeeded, última conclusão 2026-10-09 13:42:28 UTC. Essa evidência valida invocação local, não qualidade visual ou acesso produtivo. Sem nova chamada paga nesta execução.
- Evidências finais locais: 43 testes/40.812s aprovados em PostgreSQL isolado (33 thumbnails e 10 deploy); browser Chrome/template/CSS/JS reais com HTTP simulado aprovado. Django check, migration drift, OpenAPI, Node, Dockerfile check sem warnings, shell syntax e diff whitespace aprovados. Logs thumbnail-close-* em .runtime/thumbnail-validation. Build completo incluído no CI, pendente remoto; limitação de espaço local previamente registrada permanece. Variáveis GitHub conferidas somente leitura: deploy produtivo habilitado e branch alvo main. Mídia DEV não será versionada.
- Pendências atuais: smoke humano autenticado/MFA, autorização específica para inferência paga em produção e avaliação visual real. Commit/PR/CI/merge/deploy, grants, mounts e habilitação técnica foram concluídos conforme evidências finais abaixo.
- Análise solicitada posteriormente: extensão do conceito a imagens de badges. Código confirmado: editor com uploads/prévia light/dark e contratos image_url/image_dark_url; direção visual existente em badges-imagem/prompt-geracao-badge.md. Reaproveitar mecanismos de execução/segurança, com contexto, prompt, associação e política de confirmação próprios. Jobs atuais têm FK de mercado/draft e não servem diretamente a badges. Criação ainda não salva exige candidata privada vinculada a operador/sessão e identidade do editor, confirmada no POST de criação, sem criar/ativar badge pela geração. Análise inicial levou à feature separada, posteriormente autorizada e implementada no workflow WFLOW-20261009-BADGE-IMAGES-001; a PR de thumbnails foi integrada conforme evidências finais.

## WFLOW-20261009-THUMBNAIL-REVIEW-FIXES-001

- Status: implementação concluída e testes locais aprovados; verificação Docker completa parcial por falta de espaço local. Correções dos três findings autorizadas pelo usuário, vinculadas a WFLOW-20261009-AI-THUMBNAILS-001.
- Escopo/aceite: Dockerfile parseável e build local; upload removido apenas antes do envio ou após rejeição confirmada, resultado desconhecido reconciliado por consulta e arquivo preservado quando não confirmável; decisão inline mantém polling/edições se validação nativa impedir submissão. Sem mudança de contratos, inferência paga, commit/push/deploy ou produção.
- Testes previstos: rejeição 422, resposta perdida após commit, reconciliação indisponível, erro local anterior ao envio; browser com validação nativa real e continuação após correção de campo; suíte PostgreSQL isolada, build/Compose local e checks.
- Evidências: 33 testes aprovados/36.607s em PostgreSQL isolado; browser aprovado com dois cenários de validação nativa e fluxos anteriores. Check Dockerfile sem warnings, Compose config/YAML/Django/OpenAPI/Node/Ruff F/diff aprovados; CI agora executa docker build --check. Build completo e escrita em volumes isolados falharam por ENOSPC no Docker Desktop, pendentes em ambiente com espaço. Ensaios sem rede e com imagem não root existente não comprovam imagem nova; volumes próprios removidos, recursos preexistentes intactos. Logs thumbnail-review-* em .runtime/thumbnail-validation. Sem chamadas pagas, commit/push/deploy ou mudanças produtivas.
- Reinício local solicitado pelo operador: PostgreSQL, proxy, API, Django, MCP e executor de thumbnails reiniciados; nenhuma geração ativa antes da parada. Banco, rascunhos e arquivos preservados. PostgreSQL aceitando conexões; API, web, proxy, editor, saúde e discovery MCP responderam HTTP 200. Executor ativo e chave operacional de thumbnails habilitada; nenhuma solicitação de geração iniciada pela verificação.

## WFLOW-20261007-MCP-CHATGPT-DCR-001

- Tipo: `change-feature`; Status: `concluido` para correção técnica/rollout; homologação ChatGPT pendente; FEAT-MCP-001; vinculado a WFLOW-20261007-MCP-CODEX-OAUTH-001.
- Objetivo: corrigir metadado opcional nulo na resposta DCR e investigar rejeição de cadastro ChatGPT, sem ampliar permissões ou enfraquecer OAuth.
- Evidência: formulário real configura OAuth/DCR e endpoints corretos; discovery público 200; logs produtivos mostram registros DCR 201. Resposta do código inclui `scope: null` quando omitido pelo cliente, incompatível com o tipo string da RFC 7591. Não há evidência suficiente para atribuir exclusivamente a esse campo a rejeição genérica do ChatGPT.
- Escopo: omitir campos opcionais ausentes na resposta de registro; teste de contrato e consent-info com callback HTTPS ChatGPT/ui_locales; contrato, runbook e estado. Sem migrations, novos grants, mercados ou edição de configuração produtiva.
- Validação local: 51 testes/156,480 s/OK em PostgreSQL isolado; OpenAPI/Ruff/diff aprovados. [Evidências](../testing/mcp-chatgpt-dcr-20261007.md).
- Etapa: PR #140 integrada (dfc0b95); CI PR/main 372 testes/OK (um skip por roles CI ausentes), deploy Actions 37710313470 Success; ajuste conferido na API em execução e no DCR público 201 sem scope null, /mcp sem token 401. Branch local preservada. Cadastro/consentimento ChatGPT permanece pendente; operador repete OAuth/DCR sem ID/segredo de serviço.


## WFLOW-20261007-MCP-CODEX-OAUTH-001

- Status: `concluido` para correção técnica/rollout; consentimento humano/piloto externo pendente; FEAT-MCP-001; vinculado ao workflow documental e fechamento MCP.
- Falha real: Codex 0.160.1 envia `application_type: native`; POST /oauth/register retorna 422 por extra proibido. Reprodução com CLI real e captura em servidor local, sem tokens.
- Escopo: ignorar metadados DCR não reconhecidos conforme RFC 7591, conservar validação dos campos reconhecidos; preservar issuer textual exato nos metadados públicos do adaptador (SDK acrescentava barra). Nenhuma mudança de permissões, MFA, PKCE, banco ou audience.
- Artefatos: schemas API, metadata MCP, testes de registro/segurança/OAuth e discovery, OpenAPI, contrato, ADR, runbook e estado.
- Validação local: 50 testes/153,516 s/OK em PostgreSQL isolado; CLI real atingiu URL de autorização em mock local, SDK real validou OAuth/serviço/tools/renovação. OpenAPI/Ruff/diff aprovados. [Evidências](../testing/mcp-codex-oauth-20261007.md).
- Usuário aprovou descrição/continuidade; PR #138 integrada, CI PR/main 371 testes/OK (um skip por roles CI ausentes), deploy Actions 37699380266 aprovado. SSM produtivo comprova flags, saúde, grants/isolamento. Codex CLI real registrou cliente e atingiu URL de autorização em produção.
- Próxima ação externa: operador conclui Authenticate/login/MFA/consentimento no Desktop; executar piloto autenticado e homologar Dot. Nenhum token/grant/mercado produtivo emitido pelo ensaio; DCR persistiu somente o cliente técnico.

## WFLOW-20261007-MCP-CLOSEOUT-001

- Status: `concluido` para entrega técnica/GitHub/rollout; homologação externa explicitamente pendente. FEAT-MCP-001 permanece parcial até MCP-X02/piloto autenticado.
- Usuário aprovou descrição e continuidade. PR #136 integrada em main b36ea44; CI PR/main com 369 testes/OK e deploy Actions 37692274600 com sucesso. Snapshot RDS gotrendlabs-pre-mcp-20261007 disponível antes do merge.
- Ativação explícita API/MCP concluída; migrations/grants de onze tabelas, append-only/isolamento, arquivos 0600, saúde e HTTPS/discovery/401/internal404 conferidos. Inventários de domínio antes/depois idênticos, nenhum mercado produtivo de teste.
- Specs/ADR/contratos/OpenAPI/runbook/memória/evidências alinhados. Branch local/checkout original/analytics/mobile preservados. [Relatório local](../testing/mcp-closeout-20261007.md), [rollout produtivo](../testing/mcp-production-rollout-20261007.md).
- Próxima ação externa: operador com MFA cria/ativa integração pequena e executa piloto OAuth/serviço; homologar Dot real, recorrência/renovação/revogação/logs. Não há conexão Dot validada nem enforcement editorial inferido: gate universal é aplicado pela FastAPI.
- Vinculado ao WFLOW-20261007-MCP-EDITORIAL-SPEC e WFLOW-20261007-BRANCH-REVIEW-FOLLOWUP-001.

## WFLOW-20261007-BRANCH-REVIEW-FOLLOWUP-001

- Status: `concluido` localmente; FEAT-MCP-001; recomendações 1/2 do review aprovadas pelo usuário.
- Escopo: adicionar os arquivos da feature ao índice Git; corrigir teste de carregamento do asset sem versão literal; validar snapshot completo em diretório limpo, instalação de dependências, migrations/grants e percursos de API/Admin Ops em PostgreSQL isolado.
- Item 3 (revisão inválida no POST) não incluído nesta autorização específica. Sem commit, merge, deploy ou alterações no DEV.
- Evidências: dependências/migrations no índice; snapshot sem env/runtime, venv nova e instalação requirements aprovados. Django/OpenAPI/pip/autodetecção de migrations/diff aprovados. **74 testes/172,744 s/OK**, PostgreSQL isolado destruído. Teste Admin Ops completo passou. [Relatório](../testing/mcp-branch-review-followup-20261007.md). Sem pendência nos itens 1/2.
- Vinculado: WFLOW-20261007-MCP-EDITORIAL-SPEC e WFLOW-20261007-DEV-CATALOG-REHEARSAL-001.

## WFLOW-20261007-DEV-CATALOG-REHEARSAL-001

- Status: `concluido` localmente; pedido explícito de remover mercados DEV e recriar por UI humana e MCP real. Vinculado ao WFLOW-20261007-MCP-EDITORIAL-SPEC e à revisão universal.
- Backup integral local antes da limpeza, inventário de dependências, preservação de contas/taxonomia/configurações/integrações/logs. Remover efeitos de mercados de ensaio e recalcular projeções afetadas.
- Validar preenchimento/persistência/fuso, ficha/parecer, gate, idempotência/concorrência, publicação, fechamento, logs e integridade. Corrigir desvios reproduzidos e registrar evidência. Sem produção/deploy.
- Evidências: backup integral local; IDs antigos 1/2/3/5 removidos; #6 humano resolvido e #7 MCP fechado. 64 testes amplos + 17 focais sobrepostos aprovados. Dez tools reais, OAuth/serviço, UI, logs e auditoria verified/zero issues. [Relatório](../testing/dev-catalog-rehearsal-20261007.md). Sem pendência local deste ensaio; Dot/HTTPS/deploy seguem externos.

## WFLOW-20261007-LEGACY-CLOSURE-FEEDBACK-001

- Status: `concluido` localmente para diagnóstico/feedback; correção da configuração publicada continua indisponível pelo contrato de integridade.
- Problema confirmado no Chrome DEV: POST do EV conserva campos preenchidos, mas FastAPI rejeita alteração da definição assinada; alerta repete orientação de preenchimento baseada no registro anterior.
- Escopo: distinguir registro salvo/formulário e explicar proteção do fechamento publicado. Preservar definição/provas/previsões; não implementar alteração silenciosa ou cancelamento automático.
- Testes: rejeição de prazo/fuso em publicado sem mutação, mensagem e valores preservados, ausência de instrução enganosa no alerta legado.
- Vinculado: WFLOW-20261007-UNIVERSAL-EDITORIAL-001. Iniciado e encerrado em 2026-10-07.
- Evidências: 12 testes/4,794 s/OK; banco isolado destruído. Django/OpenAPI/Ruff/diff aprovados. Chrome DEV confirma aviso; dados DEV e formulário do operador preservados. [Relatório](../testing/legacy-closure-feedback-20261007.md).

## WFLOW-20261007-UNIVERSAL-EDITORIAL-001

- Status: `concluido` localmente; FEAT-EDITORIAL-001 + FEAT-MCP-001. Revisão explícita pelo usuário do escopo anterior sem gate global.
- Escopo: ficha/parecer para todos os mercados; gate universal na FastAPI; validação de fechamento automático/manual antes de assinatura. Migração aditiva nullable integração e backfill de fichas pendentes, sem aprovação inventada.
- Legado publicado: manter estados, previsões, ledger e provas; permitir conferência humana de abertos/fechados e consulta de terminais. Não fechar, cancelar ou resolver automaticamente.
- Testes: humano/MCP/criação por sugestão, publicação sem revisão/retornada/rejeitada/antiga, fechamento inválido/validado em ambos os modos, concorrência/privacidade/roles/migração e UI DEV.
- Iniciado e encerrado em: 2026-10-07.
- Evidências: 68 testes/195,984 s/OK, PostgreSQL isolado destruído; OpenAPI/migrations/Django/Ruff/diff aprovados. Migration DEV preservou 4 mercados/9 opções/3 previsões/4 definições/2 selos e parecer Tesla revisão11; novas fichas humanas pendentes. Chrome confirma aviso fechamento e revisão #3. [Relatório](../testing/universal-editorial-20261007.md). Sem deploy; homologação externa MCP pendente.
- Vinculado ao WFLOW-20261007-MCP-EDITORIAL-SPEC.

## WFLOW-20261007-MARKET-PUBLISHED-NOTICE-002

- Status: `concluido` localmente; continuação da mensagem pós-publicação.
- Escopo: estado publicado/cancelado também em mercados sem MCP; nenhuma criação de ficha ou gate global. DEV EV somente leitura.
- Iniciado e encerrado em: 2026-10-07.
- Evidências: oito testes UI/0,021 s aprovados; Ruff/Django/diff. Chrome DEV confirma lider-vendas-ev-4t26 publicado/Aberto sem ficha editorial; screenshot .runtime/market-published-notice002/ev.jpg. Sem backend/OpenAPI/migration ou escrita em DEV.

## WFLOW-20261007-MCP-PUBLISHED-NOTICE-001

- Status: `concluido` localmente; FEAT-MCP-001.
- Problema: fallback do editor exibe bloqueio de publicação também para mercado já publicado.
- Escopo: apresentação dependente do lifecycle, sem alterar gate, parecer ou dados DEV. Testar rascunhos/agendados e estados pós-publicação/cancelamento.
- Iniciado e encerrado em: 2026-10-07.
- Evidências: sete testes UI passaram (0,021 s), Ruff/Django/diff aprovados. Chrome DEV confirma revisão 11 aprovada e publicação realizada pelo operador; novo aviso visível. Screenshot .runtime/mcp-published-notice/editor.jpg. Sem backend/OpenAPI/migrations ou escrita em DEV; feature permanece parcial por homologação externa.

## WFLOW-20261007-MCP-GAPS-RESOLUTION-001

- Status: `concluido` localmente; FEAT-MCP-001.
- Pedido: operador marcou critérios mas texto de lacunas continua impedindo aprovação do draft Tesla.
- Solução: confirmação explícita de resolução no mesmo formulário, sem apagar texto manualmente; preservação de histórico e validações backend/CSRF/versão/fonte. Sem parecer ou publicação automática em DEV.
- Iniciado e encerrado em: 2026-10-07.
- Evidências: sete testes passaram (8,925 s), caso ampliado de preservação do histórico passou (3,492 s); PostgreSQL isolado destruído. Ruff/Django/diff aprovados; Chrome DEV confirma novo checkbox, draft #5 revisão 9 intacto. [Relatório](../testing/mcp-review-ux-20261007.md). Contrato/OpenAPI compatíveis, sem migrations/deploy; homologação externa pendente.

## WFLOW-20261007-MCP-REVIEW-UX-002

- Status: `concluido` localmente; FEAT-MCP-001. Continuação da revisão única e lista de mercados.
- Escopo: alinhamento com design Admin Ops; sugestões de fontes na evidência editável, sem seleções repetidas; bloqueios explícitos e preservação da decisão em erro.
- Segurança: atestação humana de fontes permanece independente; FastAPI mantém validação, versionamento e rollback. Sem aprovação/publicação ou escrita em DEV.
- Iniciado e encerrado em: 2026-10-07.
- Evidências: [relatório UX](../testing/mcp-review-ux-20261007.md); oito testes passaram (12,393 s) e seis casos relevantes repetidos após ajustes finais (3,413 s). PostgreSQL isolado destruído; Ruff/Django/diff aprovados. UI desktop Chrome DEV, draft #5 revisão 9 preservado; sem homologação externa, publicação ou deploy.

## WFLOW-20261007-MCP-MARKET-LIST-001

- Status: `concluido` localmente; FEAT-MCP-001, vinculado ao workflow documental WFLOW-20261007-MCP-EDITORIAL-SPEC.
- Escopo: lista administrativa mostra origem MCP, estado editorial e acesso direto ao parecer, reutilizando projeção FastAPI existente. Sem alteração de contratos, migrations ou dados DEV.
- Validação: estados editoriais, ausência de marcação em mercados sem ficha de integração, links por ID e UI DEV somente leitura.
- Iniciado e encerrado em: 2026-10-07.
- Evidências: quatro testes UI passaram (0,031 s), Ruff/Django/diff aprovados; Chrome DEV confirma origem MCP, estado Em revisão e link /admin-ops/agent-reviews/5/. Screenshot local .runtime/mcp-market-list/list.jpg. Contrato/OpenAPI sem mudanças, pois projeção administrativa existente já retorna os campos. Feature permanece parcial por homologação externa; sem publicação/deploy.

## WFLOW-20261007-MCP-SINGLE-REVIEW-001

- Status: `concluido` localmente; FEAT-MCP-001, continuação da retomada humana v1.2.
- Pedido: remover etapas burocráticas entre conferência da ficha e parecer. Uma única ação humana para aprovar/devolver/rejeitar, sem submissão humana prévia.
- Solução: assessment administrativo FastAPI salva ficha/snapshot e parecer atomicamente, com MFA, versão/hash/locks/validação existentes. UI unifica evidências, verificação independente e decisão; publicação separada.
- Preservação: contratos /record e /decision compatíveis; nenhuma aprovação/publicação de draft DEV pelo agente. Sem migrations nem permissões novas ao MCP.
- Testes: decisão direta de preparação, rollback integral de aprovação inválida, conflitos de versão/hash, permissões, UI/CSRF/checks humanos não inferidos de relatos do agente; regressão MCP.
- Iniciado em: 2026-10-07.
- Evidências: [parecer em uma ação](../testing/mcp-single-review-20261007.md), 47 testes em 139,495 s, exit 0; Ruff/Django/OpenAPI/diff aprovados. Chrome DEV confirma formulário/botão únicos, sem escrita no draft #5 (revisão 9 observada).
- Encerrado em: 2026-10-07; contratos/ADR/feature/runbook/estado sincronizados. Feature parcial por homologação externa; sem publicação/deploy.

## WFLOW-20261007-MCP-HUMAN-PREPARE-001

- Status: `concluido` localmente; FEAT-MCP-001, continuação de WFLOW-20261007-MCP-REVIEW-GATE-001.
- Problema: edição humana volta a preparação, mas UI não permite completar ficha/re-submeter sem executor; usuário fica impedido de registrar parecer.
- Escopo: staff/superuser MFA salva ficha estruturada e solicita revisão via FastAPI; snapshot/versionamento/evento humano; aprovação permanece ação separada com validações existentes. Nenhuma aprovação/publicação automática em DEV.
- Artefatos: feature/contrato/serviço/API/UI/OpenAPI/testes/runbook/estado. Sem migration nova ou permissão adicional ao MCP.
- Testes: fluxo preparação → ficha → revisão → parecer → gate; MFA/permissões/revisão antiga/malformada/estado publicado; UI/CSRF/erro com contexto.
- Iniciado em: 2026-10-07.
- Evidências: [retomada humana](../testing/mcp-human-review-20261007.md), 45 testes/130,785 s + repetição de 2 novos/6,320 s, exit 0. MFA/CSRF/estado/versão/pendências e UI DEV conferidos; Ruff/Django/OpenAPI/diff aprovados.
- Encerrado em: 2026-10-07; sem alteração do draft DEV #5 (revisão 6 observada), aprovação, publicação ou deploy. Feature parcial por homologação externa.

## WFLOW-20261007-MCP-REVIEW-GATE-001

- Status: `concluido` localmente; tipo `change-feature` + `implementation-cycle`; FEAT-MCP-001.
- Solicitação: slug legível, publicação dependente de parecer favorável para drafts de agentes, estrutura Integrações como Agentes IA. Revisão explícita do escopo anterior sem gate.
- Arquitetura: FastAPI aplica bloqueio no MarketLifecycleEngine após lock do mercado; ficha/decisão/hash/versionamento reutilizados. Sem regra crítica em Django/MCP, sem gate para mercados humanos legados.
- Testes: slug/replay/colisão, parecer ausente/devolvido/rejeitado/antigo, edição invalida aprovação, publicação aprovada/integridade e concorrência, compatibilidade humana; listagem/formulário e UI real DEV.
- Dados DEV: preservar draft #5 e mercados anteriores; somente correção de slug pelo editor humano, sem publicar.
- Iniciado em: 2026-10-07.

- Evidências: 44 testes em 147,858 s + 1 agendado em 4,403 s + 1 preservação de edição humana em 4,003 s, todos exit 0 (46 casos distintos); Ruff/Django/JS/OpenAPI/diff aprovados. UI desktop real; draft DEV #5 revisão 4/preparation, fechamento e mercados 1–3 preservados, guard recusa publicação.
- Artefatos: [resultados da revisão](../testing/mcp-review-gate-20261007.md); feature/contratos/ADR/runbook/OpenAPI/estado/changelogs sincronizados. Sem migrations novas.
- Encerrado em: 2026-10-07. Dot/HTTPS externo, QA responsivo desta revisão e deploy continuam pendentes; feature parcial.

## WFLOW-20261007-MCP-RADAR-DEV-001

- Status: `concluido` localmente; tipo `test-review-cycle`; FEAT-MCP-001.
- Autorização: usuário solicita repetir radar no banco DEV persistente, substituindo o isolamento anterior para este ensaio.
- Escopo: OAuth local/integração existente, dez tools reais, pesquisa/deduplicação, um draft persistente e testes negativos apenas nesse draft, conferência no painel.
- Preservação: sem publicar/resolver/cancelar, sem reset/migrations/flush, sem alterações em mercados anteriores ou credenciais do usuário.
- Artefatos: [relatório DEV](../testing/mcp-radar-dev-20261007.md), correção de consentimento escalar e título da revisão, teste sem banco.
- Evidências: draft #5 persistente/revisão 3; dez tools/21 chamadas/3 recusas corretas/63 logs correlacionados; mercados anteriores intactos; UI conferida; OAuth temporário revogado; Ruff/OpenAPI/diff e teste de consentimento aprovados.
- Encerrado em: 2026-10-07.
- Retomada: responsável humano revisa E07/E09/E10/E11 e ficha antes de qualquer publicação; Dot/LM Studio externo ainda pendente.
- Iniciado em: 2026-10-07.


## WFLOW-20261007-MCP-RADAR-PILOT-001

- Tipo: `test-review-cycle`; FEAT-MCP-001, vinculado ao WFLOW-20261007-MCP-EDITORIAL-SPEC.
- Status: `concluido` localmente.
- Objetivo: radar com pesquisa externa real, catálogo público DEV somente leitura, cliente MCP real e escritas exclusivamente em PostgreSQL descartável.
- Artefatos: harness opt-in, fixtures públicas, [relatório](../testing/mcp-radar-pilot-20261007.md) e correção de serialização nullable.
- Evidências: 17 chamadas/dez tools; um draft in_review, replay sem duplicação, edição em revisão recusada, 51 logs correlacionados. Quatro testes passaram em 29,121 s; inclui OAuth/serviço e privacidade. Base isolada destruída.
- Encerrado em: 2026-10-07.
- Retomada: repetir pesquisa/deduplicação completa e preencher pendências humanas antes de piloto persistente.
- Limites: sem publicação, parecer humano simulado ou homologação Dot/LM Studio.
- Iniciado em: 2026-10-07.

## WFLOW-20261007-MCP-TOOL-DISCOVERY-001

- Tipo: `change-feature` + `test-review-cycle`; FEAT-MCP-001.
- Status: `concluido` localmente.
- Objetivo: esclarecer a escolha de política editorial versus catálogo/taxonomia pelos executores externos.
- Artefatos: instructions e descrições MCP, teste de resposta da política e runbook.
- Evidências: cliente real TCP repetiu as dez ferramentas com OAuth/serviço, replay e recusas esperadas; passou em 15,650 s. Política contém manual/checklist/ficha não vazios e 11 critérios. Base isolada destruída e servidores temporários encerrados. Ruff/diff aprovados.
- Limite: metadata esclarece propósito; escolha efetiva depende do modelo/executor. Homologação LM Studio não concluída, após erros de parser/MLX observados.
- Próxima ação: Refresh tools/reconexão e conversa nova no LM Studio; confirmar execução de get_editorial_policy com modelo de tool use compatível.
- Iniciado em: 2026-10-07; sem mudança de autenticação, nomes, schemas ou rotas.

## WFLOW-20261007-MCP-ALL-TOOLS-001

- Tipo: `test-review-cycle`; vinculado ao workflow MCP de implementação.
- Status: `concluido` localmente.
- Objetivo: executar cliente MCP Streamable HTTP real com todas as dez ferramentas, OAuth e credencial de serviço, em PostgreSQL isolado.
- Artefatos: teste end-to-end ampliado e evidências por ferramenta.
- Evidências: teste passou em 15,236 s com API/adapter em portas TCP efêmeras e cliente SDK real. Dez tools descobertas e chamadas com sucesso em ambos os modos (22 chamadas positivas incluindo replay, quatro negações esperadas). Dois drafts de fixture, sem duplicação, editados e submetidos; revisão in_review confirmada; edição em revisão e ID inexistente recusados. Base isolada destruída e servidores encerrados.
- Checklist: evidências MCP e changelog sincronizados; Ruff/diff aprovados. Sem mudança de contratos/OpenAPI/domínio. Validação não homologa LM Studio, Dot nem a credencial compartilhada.
- Próxima ação: conectar executor real com OAuth ou nova credencial de serviço e registrar homologação de cliente.
- Limites: credenciais geradas no teste; segredo compartilhado pelo usuário não reutilizado nem copiado. Sem mercados no DEV/produção, sem publicação.
- Iniciado em: 2026-10-07.

## WFLOW-20261007-EXPIRY-PICKER-001

- Tipo: `change-feature` + `implementation-cycle` + `test-review-cycle`; FEAT-MCP-001.
- Status: `concluido` localmente.
- Objetivo: validade selecionável por calendário/horário nativos, com fuso explícito America/Sao_Paulo e conversão no servidor.
- Artefatos: formulário/template Django, testes e documentação; contrato REST com offset permanece.
- Evidências: quatro testes passaram em PostgreSQL isolado, incluindo conversão UTC/local com troca de dia, fuso ativo alternativo, data inválida e regressão de UI/CSRF/parecer/transferência. Base de teste destruída. Chrome DEV apresentou datetime-local e affordance nativa de calendário, valor selecionável válido; sem salvar integração e formulário original preservado.
- Checklist: Django check/Ruff/diff aprovados; feature e changelog atualizados. Sem mudança REST/OpenAPI/migration; backend mantém validação de validade futura. Fuso de apresentação/interpretação São Paulo explícito, precisão de minutos.
- Próxima ação: usar o calendário/horário na criação ou edição local.
- Iniciado em: 2026-10-07; sem publicação ou alteração de banco.

## WFLOW-20261007-RESPONSIBLE-SELECT-001

- Tipo: `change-feature` + `implementation-cycle` + `test-review-cycle`; FEAT-MCP-001.
- Status: `concluido` localmente.
- Objetivo: seleção de responsável por nome no Admin Ops, carregada via API administrativa MFA, sem exigir conhecimento de IDs.
- Artefatos: endpoint/projeção mínima, formulários Django, template, OpenAPI, testes e estados.
- Evidências: três testes passaram em PostgreSQL isolado: MFA/401/403, exclusão de bots/inativos/não administrativos, projeção mínima e paginação de 103 responsáveis; renderização da seleção/valor atual e transferência válida/forjada, CSRF e ciclo de revogação/papéis. Base destruída. Chrome DEV confirmou seleção por nome, sem salvar integração; formulário previamente preenchido pelo usuário preservado em sua aba.
- Checklist: feature/contrato/OpenAPI/changelog/integration map sincronizados; Django check, Ruff, OpenAPI --check e diff aprovados. Nenhuma migration ou alteração de grants necessária; lista usa SELECT já permitido à role API. Estado MCP permanece parcial pela homologação externa.
- Próxima ação: usar seleção na criação/transferência no piloto local.
- Iniciado em: 2026-10-07; sem publicação/deploy.

## WFLOW-20261007-EDITORIAL-UI-001

- Tipo: `change-feature` + `implementation-cycle` + `test-review-cycle`; continuidade visual de FEAT-MCP-001.
- Status: `concluido` localmente.
- Objetivo: alinhar fila e parecer humano ao design system Admin Ops, preservando contratos e controles de revisão.
- Artefatos: template de revisão, partial de estados editoriais, CSS e cache de assets; testes e documentação.
- Evidências: dois testes direcionados passaram em PostgreSQL isolado, incluindo draft realmente submetido à revisão, 11 critérios, fonte, labels, revisão/hash ocultos, escape de evidência maliciosa, CSRF e smoke administrativo. Base de teste destruída. Django check, Ruff, JS e diff aprovados.
- Conferência visual: fila vazia no Chrome DEV desktop e viewport 390 px, sem overflow horizontal; viewport restaurado. Detalhe em revisão conferido por renderização no teste isolado, sem criar mercado no DEV.
- Checklist: contrato/backend/MFA/concorrência inalterados; arquitetura frontend e changelog atualizados. FEAT-MCP-001 permanece parcial pela homologação externa já registrada.
- Próxima ação: acompanhar revisão com conteúdo editorial real durante piloto autorizado.
- Iniciado em: 2026-10-07.
- Limites: sem merge, deploy ou dados de mercados reais para QA.

## WFLOW-20261007-ADMIN-NAV-001

- Tipo: `change-feature` + `implementation-cycle` + `test-review-cycle`; continuidade do refinamento Admin Ops solicitado após `WFLOW-20261007-MCP-EDITORIAL-IMPL`.
- Status: `concluido` localmente.
- Objetivo: melhorar a navegação compartilhada do Admin Ops, mantendo o design system e os controles existentes.
- Artefatos: context processor de navegação, template base/partial, CSS/JS, testes e documentação frontend.
- Implementação: menu lateral agrupado, busca local com normalização de acentos, página ativa nas rotas aninhadas, drawer móvel com foco/Escape e remoção do menu duplicado de revisão editorial.
- Evidências: quatro testes direcionados passaram (rotas aninhadas/public route, CSRF/segredo único/escape e smoke administrativo) em PostgreSQL isolado; base de teste destruída. Chrome DEV desktop/móvel confirmou busca acentuada/sem resultados, indicação ativa, abertura/Escape/foco e ausência de overflow horizontal. Django check, Ruff, sintaxe JS e whitespace aprovados. Expectativa antiga de cache JS do smoke atualizada para a nova versão.
- Documentação: arquitetura frontend, changelog e workflow sincronizados; estado MCP permanece parcial pela homologação externa independente.
- Limites: sem mudança de contratos, permissões, migrations ou navegação pública/mobile Flutter; sem merge/deploy.
- Iniciado em: 2026-10-07.

## WFLOW-20261007-MCP-EDITORIAL-IMPL

- Tipo: `implementation-cycle` + `test-review-cycle`; vinculado a `WFLOW-20261007-MCP-EDITORIAL-SPEC`.
- Status: `bloqueado` somente para homologação externa; implementação/testes locais concluídos. FEAT-MCP-001 permanece `parcial`.
- Objetivo: executar fatias A/B/C, preservando contratos existentes e trabalho analytics/mobile.
- Base: `origin/main` 9df08bc, atualizado com fetch; worktree `gotrendlabs-mcp`, branch `feature/mcp-editorial`. Apenas docs MCP transportados do checkout original; venv original preservado, Python 3.11 separado.
- Arquitetura: FastAPI dona de identidade/OAuth/delegação/persistência/domínio; MCP SDK 1.30.0 Streamable HTTP sem banco; Authlib 1.6.12; Admin Ops via HTTP/MFA/CSRF. `FOR NO KEY UPDATE` na integração, locks no mercado/revisão, publicação serializada com engine/assinatura existentes.
- Artefatos: `apps/api/backend_api/editorial_*.py`, handlers/serviços compartilhados, `apps/mcp`, `editorial_integrations`/migrations, Admin Ops/templates/JS/CSS, OpenAPI, requirements, testes, exemplos env, Compose/Docker/Caddy opcionais, runbook/prompt/ADR/estados.
- Etapa atual: A auth/gestão/leitura/logs, B drafts/ficha/parecer/cotas/idempotência/concorrência e C pacote/operação/cliente real local concluídas. Dot/HTTPS externo pendentes.
- Evidências: 321 testes gerais passaram; suíte final MCP com 33 testes passou e destruiu base isolada. PostgreSQL/grants reais, cliente SDK OAuth/serviço, PKCE/refresh/reuse, locks/revogação/publicação, falhas audit/log, quota/fonte/política. UI Chromium desktop/móvel e devolução humana real com fixture isolada. Django check/migration drift/OpenAPI/Ruff/JS/diff aprovados; imagem MCP sem DB/segredos, Compose e Caddy validados localmente. [Matriz](../testing/mcp-editorial-results.md).
- Checklist: arquitetura/segurança/specs/contratos/testes/ADR/changelogs/status/integration map/known gaps sincronizados. Nenhum gate editorial universal nem promessa de compatibilidade Dot sem evidência.
- Bloqueio externo: conta/sessão Dot e endpoint público HTTPS de homologação não disponíveis nesta execução. A falta não impediu nenhuma etapa local autorizada. Não marcar `implementada_validada`.
- Iniciado/atualizado em: 2026-10-07.
- Próxima ação: seguir [runbook](../../guides/mcp-editorial-pilot.md), autorizar/configurar piloto HTTPS e executar MCP-O01/MCP-X02 com Dot real; registrar recorrência/renovação/revogação e correlação sanitizada.
- Reversão lógica: kill switch API/adapter, retirar handles opcionais e pausar/revogar integração; preservar snapshots/drafts/auditoria e migrations aditivas.
- Publicação: não houve commit/PR/merge/deploy/produção nesta execução; exemplos produtivos desligados por padrão.
- DEV posterior solicitado: PostgreSQL local reiniciado, migrations MCP aplicadas por role migradora e serviços web/API/MCP/proxy iniciados no worktree. Origin `http://127.0.0.1:8000`, MCP habilitado somente neste DEV, discovery/authorize/health/UI guards aprovados. Configuração/segredos/PIDs locais ignorados em `.runtime/dev/`; conta e MFA existentes preservados. Homologação Dot/HTTPS externo permanece pendente.
- Ajuste visual solicitado: tela de integrações alinhada à composição de Config/Admin Ops, sem menu duplicado nem painel/formulário isolado. Seções de identificação/permissões/limites, estados pt-BR, credenciais/atividade e revogação segregadas. Conferência no Chrome real do DEV em desktop, viewport estreito e dark mode (tema/viewport restaurados); teste UI CSRF/segredo/escape passou, Ruff/JS/diff aprovados. Nenhum contrato de domínio alterado.

## WFLOW-20261007-MCP-EDITORIAL-SPEC

- Tipo: `new-feature` + consolidação documental para implementação em contexto limpo.
- Status: `concluido` (somente especificação; implementação não iniciada).
- Feature: `FEAT-MCP-001` v1.0.
- Origem: decisões do usuário entre 2026-10-02 e 2026-10-07 e pedido de fechar spec/prompt para GPT-6.1 Sol.
- Artefatos: `features/mcp-editorial-agents.md`, `contracts/agent-integrations.md`, `decisions/ADR-0011-mcp-editorial-integrations.md`, `testing/mcp-editorial-acceptance.md`, `docs/guides/implementar-mcp-editorial-prompt.md`, estados/changelogs e referências de arquitetura/editorial/logs/auth.
- Decisões: staff/superuser com MFA gerenciam todas as integrações igualmente; OAuth e serviço; adaptador sem banco; FastAPI autoritativa; drafts restritos, ficha versionada, revisão humana; logs existentes; cotas PostgreSQL, idempotência e concorrência; Dot externo com homologação obrigatória.
- Revisão arquitetural: baseada em leitura de handlers de auth/mercados/logs, modelos, daemon, Compose/Caddy e contratos. Identificadas permissões amplas, efeitos de taxonomia/destaque, ausência de identidade técnica estruturada, quota em memória e log técnico não transacional. A spec trata essas lacunas sem alterar o runtime.
- Aceite documental: catálogo de ferramentas/rotas alvo, modelagem lógica, defaults, limites de escopo, matriz de testes e prompt autossuficiente. Links relativos e whitespace verificados. Nenhum teste de código executado porque entrega é docs-only.
- Estado de origem: branch `feature/first-party-analytics`; alterações não rastreadas mobile preexistentes preservadas. Nenhum commit, PR, merge ou deploy realizado por esta entrega.
- Pendências: implementação completa, escolha de biblioteca OAuth/MCP, teste real com cliente e Dot, homologação/produção. Não confundir estas pendências com bloqueio da entrega documental.
- Próxima ação: usar o prompt em `docs/guides/implementar-mcp-editorial-prompt.md`, abrir workflow de implementação vinculado e executar fatias A/B/C. Publicação não autorizada pelo prompt.

## WFLOW-20260929-ANALYTICS-001

- Tipo: `change-feature` + `implementation-cycle` + `test-review-cycle`.
- Status: `concluido` para o escopo v0.4, com deploy e smoke produtivo aprovados.
- Feature alvo: `FEAT-ANALYTICS-001`.
- Objetivo: analytics proprio de navegacao web/mobile, geografia aproximada, funil e insights no Admin Ops com FastAPI autoritativa.
- Base: `origin/main` cf0f33b, branch `feature/first-party-analytics`.
- Restauracao integral anterior: `/Users/williamsca/Documents/gotrendlabs-restore-20260929-before-analytics` (copia da solucao, bundle Git e status original).
- Etapa atual: PR `#133` integrada na `main` (`61bc109`), CI/deploy `36583348331` concluído; branch local `feature/first-party-analytics` preservada.
- Artefatos afetados: spec de analytics, FastAPI/OpenAPI, migracao PostgreSQL, Django web/Admin Ops, Flutter, testes e memoria operacional.
- Validacao: migration `admin_ops.0020` aplicada localmente; 286 testes Django passaram com `BACKEND_API_URL` isolada, 106 testes Flutter passaram, `flutter analyze`, `manage.py check`, `makemigrations --check`, snapshot OpenAPI e sintaxe JavaScript aprovados. Os tres testes de pagina que falharam antes do isolamento consultavam um mercado concluido na API local externa ao banco de teste; repetidos com o isolamento, passaram.
- GeoLite local: arquivo oficial `GeoLite2-City_20260925.tar.gz` baixado da conta MaxMind apos aceite do titular; SHA256 do arquivo compactado conferido com o checksum oficial, `.mmdb` extraido para `.runtime/geolite/GeoLite2-City.mmdb`, biblioteca `geoip2` validou o tipo e uma consulta. Caminho configurado apenas no `.env.api.local` ignorado pelo Git; serviços locais foram reiniciados após a configuração.
- Ampliação v0.2: FastAPI agrega UF/cidade e evolução diária e mede desistência de jornada sessão/mercado após 30 minutos de inatividade; Admin Ops apresenta mapa esquematico e séries, e o Flutter emite escolha de opção. Testes direcionados Django (10), suíte Flutter (106), `flutter analyze`, snapshot OpenAPI, renderização do template, sintaxe do mapa JS e `git diff --check` passaram. A suíte Django completa executou 288 testes: 3 páginas falharam ao consultar a API local externa ao banco de teste; os 3 passaram com `BACKEND_API_URL` isolada. FastAPI local reiniciada e `/health` validado.
- Ampliação v0.3: tabela de status da última remessa e histórico de atualizações GeoLite criados pela migration `admin_ops.0021` e aplicada localmente. O importador validou checksum oficial e reinstalou atomicamente a base GeoLite City de 2026-09-25 (65.345.887 bytes, 6.104.689 nós), registrando sucesso. O relatório agora mostra última remessa, volume humano de 24 h, última atualização GeoLite e estado do arquivo. Onze testes direcionados de analytics, `manage.py check`, `makemigrations --check`, snapshot OpenAPI, renderização do dashboard com dados locais e `git diff --check` passaram. FastAPI local reiniciada após a mudança.
- Ampliação v0.4: retenção observada D1/D7/D30 por coortes semanais para cadastrados e visitantes, apurada pela FastAPI em dias completos de São Paulo, com sessão nova obrigatória para retorno anônimo. O dashboard ganhou hierarquia visual revisada e um mapa SVG real das 27 UFs, gerado de GeoJSON simplificado da API de Malhas do IBGE. Testes direcionados de integração cobriram coortes maduras e retorno anônimo em sessão diferente; `manage.py check`, `makemigrations --check`, snapshot OpenAPI, sintaxe JS e `git diff --check` passaram. Página real, retenção vazia e desenho/acessibilidade do mapa foram conferidos no navegador; FastAPI local reiniciada e `/health` respondeu `ok`. Não há nova migration nesta etapa.
- Fechamento solicitado: escopo da v0.4 concluído localmente. Revisão pré-publicação normalizou chaves de tela web e retirou `visitor_id` controlado pelo cliente da identidade do rate limit; regressão de integração adicionada. A publicação por PR, o CI, a implantação da GeoLite/configuração do proxy na produção e o smoke produtivo ainda precisam ser comprovados antes de marcar a implementação `implementada_validada`. As evoluções fora do escopo permanecem em `known-gaps.md`.
- Validação pré-PR: suíte Django completa isolada da API local passou com 291 testes, após uma primeira execução concorrente que gerou duas falhas de cadastro não reproduzidas isoladamente; Flutter passou 106 testes, `flutter analyze` e build APK debug. Snapshot OpenAPI, `manage.py check`, `makemigrations --check`, sintaxe JavaScript e diff sem whitespace também passaram. A EC2 produtiva está online e os serviços estão ativos; `.env.prod` ainda não contém as três chaves GeoLite/proxy, que serão configuradas antes do merge.
- Publicação produtiva: GeoLite2 City de 2026-09-25 foi transferida por bucket S3 privado temporário, SHA-256 `7f734d177eabd4412436f03fc3ddc01f69f465999c053951faab71f2dd9d3655` conferido, e instalada no volume persistente após migrations `admin_ops.0020/0021`. `.env.prod` recebeu caminho da base, segredo proxy e CIDR Docker `172.19.0.0/16`, com backup operacional e modo `0600`, sem expor segredo. Primeira tentativa do importador registrou falha de permissão porque o diretório criado pelo SSM pertencia a root; ownership ajustado ao usuário runtime `100:101` e segunda execução registrou `success` (65.345.887 bytes, 6.104.689 nós). Arquivo ativo `ready` e amostra de IP brasileiro retornou BR/SP/São Paulo. Arquivo de transferência e bucket temporário foram removidos após sucesso.
- Smoke produtivo: `GET /api/health` informou API/banco `ok`; OpenAPI publicou `/analytics/events` e `/admin/analytics/summary`; `/admin-ops/analytics/` redirecionou visitante para login; consulta do resumo no processo FastAPI retornou retenção e última carga `success`. O site público está em manutenção e a janela de 24 horas tinha zero eventos humanos, portanto não houve comprovação de coleta por navegação real em produção neste corte. O dashboard staff autenticado não foi aberto no smoke; a renderização foi verificada localmente.
- Próxima evolução fora do escopo: distribuir novo binário Flutter, observar coleta real após sair da manutenção, agendar atualização GeoLite e ampliar eventos/funis conforme `known-gaps.md`.
- Reversao logica: desativar coleta nos clientes e ocultar pagina administrativa; preservar backup anterior e retirar tabelas somente mediante migracao posterior explicita.

Use este arquivo como memória operacional de processos em andamento, concluídos, bloqueados, cancelados ou substituídos.

## WFLOW-20260928-ADMIN-TOTP-MFA-036

- Tipo: `change-feature` + `implementation-cycle` + `test-review-cycle`.
- Status: `concluido`.
- Feature alvo: `FEAT-AUTH-001`.
- Objetivo: exigir TOTP para sessões e operações administrativas, mantendo FastAPI como autoridade de autenticação e removendo o Django Admin como rota paralela.
- Artefatos afetados: FastAPI auth/session, PostgreSQL/migration accounts 0023, Django accounts/Admin Ops guard, OpenAPI, ADR-0009, specs e testes.
- Decisões: desafio opaco expira em cinco minutos e é usado uma vez; segredo TOTP é Fernet com chave dedicada exclusiva da FastAPI; recovery codes são hashados; limite MFA é persistido no PostgreSQL; rollout revoga sessões staff/superuser existentes.
- Evidências locais: migration completa aplicada em PostgreSQL isolado `gotrendlabs_mfa_isolated`; `makemigrations --check` sem alterações nessa base; role FastAPI comprovada com INSERT/SELECT rollback em tabelas MFA. Smoke HTTP isolado confirmou login staff sem sessão, enrollment, confirmação TOTP, sessão MFA para `/admin/users`, recuperação por superuser e reenrollment do alvo. Compilação Python, testes de primitivas TOTP, OpenAPI check e `git diff --check` aprovados. `makemigrations --check` permanece bloqueado somente no `db.sqlite3` histórico (`admin.0001_initial` antes de `accounts.0001_initial`), que não foi alterado.
- Recuperação: endpoint e ação Admin Ops `POST /admin/users/{user_id}/mfa/recover` exigem superuser com MFA, nota, revogam fator/códigos/desafios/sessões do alvo e exigem novo enrollment; a ação não permite auto-recuperação.
- Correção pós-review: a resposta única que revela recovery codes agora recebe `Cache-Control: private, no-store`, coberta por regressão de integração. O preflight de deploy exige e valida a chave Fernet apenas no container FastAPI; o helper SSM preserva o arquivo de autenticação, força `0600` e não revela valores.
- Preparação operacional: `GOTRENDLABS_TOTP_ENCRYPTION_KEY` foi criada em `gotrendlabs/prod/app-secrets` e sincronizada para `/opt/gotrendlabs/.env.auth.prod` via SSM em 2026-09-28, com confirmação sem material secreto; a chave é entregue apenas ao container FastAPI.
- Evidência adicional local: 20 testes MFA/web/integração focados passaram, incluindo o cabeçalho da resposta de recovery codes; checks Django, sintaxe dos scripts de deploy e snapshot OpenAPI foram verificados.
- Entrega: PR `#130` integrou a feature; PR `#131` corrigiu a migration de grant para banco efêmero de CI. O workflow `36425169684` concluiu testes e deploy em 2026-09-28. O servidor produtivo confirmou containers ativos, arquivo de autenticação com modo `0600`, migrations `accounts 0023/0024` aplicadas e respostas saudáveis em `/api/health` e `/`.
- Pendência operacional: o primeiro operador deve concluir o enrollment com seu próprio autenticador; isso não é automatizado para não tomar posse de fator ou recovery codes. O app mobile continua fora do fluxo até existir superfície administrativa.
- Iniciado em: 2026-09-28.

## WFLOW-20260927-AUTH-AI-TEST-ACCOUNTS-035

- Tipo: `operational-validation` + `change-feature` documental.
- Status: `concluido` operacionalmente; publicacao documental aguardando PR.
- Features alvo: `FEAT-AUTH-001` e `FEAT-AIAGENT-001`.
- Objetivo: conferir impacto do corte Argon2id nas identidades dos agentes IA e devolver acesso a conta produtiva de teste.
- Inventario produtivo: `@gotrendlabs_ai_analyst` e `@gotrendlabs_ai_liquidity` sao usuarios bot ativos, vinculados a agentes ativos, com senha inutilizavel por desenho; `@test` e usuario humano ativo/email confirmado; `@karlascardua` e conta staff ativa com senha inutilizavel apos o corte; `@admin` tem Argon2id.
- Verificacao de arquitetura: `agent_services._active_agents` seleciona por `gotrendlabs_ai_agents.user_id`, `agent_type`, `is_active` e `users.is_bot/is_active`. Comentarios e previsoes sao gravados pelo backend/daemon como identidade vinculada, sem login ou verificacao de senha bot. Flags produtivas de agentes, comentarios e previsoes estao ligadas. A auditoria registrou 26 ciclos recentes de cada agente apos o deploy, todos `skipped/no_eligible_market`; isso comprova execucao do scheduler sem erro de autenticacao, mas nao exercita criacao real de comentario/previsao nesta janela.
- Acao produtiva: conta `@test` (ID 7) foi preservada para nao alterar referencias; sua senha inutilizavel foi substituida por hash Argon2id pela FastAPI, sessoes antigas revogadas e evento administrativo registrado. Nova credencial recuperavel em `gotrendlabs/prod/app-secrets`, chave `GOTRENDLABS_TEST_ACCOUNT_PASSWORD`, sem valor em Git ou logs.
- Evidencia: hash novo verificado; login/sessao/logout/revogacao com headers mobile retornaram `200/200/204/401`; login/sessao/logout web passaram. Email de acesso: `test@gotrendlabs.com.br`. Nenhum codigo, contrato HTTP, migration ou configuracao dos agentes foi alterado.
- Pendencia: `@karlascardua` continua sem senha utilizavel e precisa de reset se seu acesso staff for necessario. Aguardar mercado elegivel para observar acao IA real apos o corte; manter monitoramento do `401` de `@admin` registrado no workflow anterior.
- Iniciado e concluido operacionalmente em: 2026-09-27.
- Proxima acao: publicar esta conciliacao documental apos aprovacao da descricao da PR; resetar a conta staff apenas por solicitacao do titular/operador autorizado.

## WFLOW-20260927-AUTH-API-AUTHORITY-034

- Tipo: `change-feature` + `implementation-cycle` + `test-review-cycle`.
- Status: `concluido`.
- Feature alvo: `FEAT-AUTH-001`.
- Objetivo: tornar a FastAPI a unica operadora de credenciais em runtime, remover o pepper do Django web/daemon e validar localmente a fronteira consumida por web e Flutter.
- Etapa atual: melhoria implantada e validada em producao pela PR `#126`; ensaio em infraestrutura separada dispensado pelo usuario nesta fase.
- Artefatos afetados: settings/hashers Django, FastAPI/bootstrap operacional, Compose/env, protecao PostgreSQL, testes, specs, ADR e memoria operacional.
- Fronteiras: os fluxos web e mobile continuam chamando FastAPI; importador cria admin com senha inutilizavel, CLI FastAPI define senha, audita e revoga sessoes, Django web recusa hash de senha e nao recebe pepper. `gotrendlabs_users` e o guard pertencem a `gotrendlabs_auth_owner` sem login tambem em producao; a role Django nao pode atualizar a coluna password.
- Escopo: entregar esta melhoria de senha e autoridade da FastAPI sem fechar as demais evolucoes de `FEAT-AUTH-001`; validar localmente, preparar o host, publicar via PR e comprovar o primeiro deploy produtivo.
- Iniciado em: 2026-09-27
- Atualizado em: 2026-09-27
- Evidencia: 228 testes web/API, 6 testes focados de senha/bootstrap, 11 testes Flutter auth, `manage.py check`, migrations --check, OpenAPI --check, `git diff --check` e sintaxe do deploy aprovados. SQL local bloqueou UPDATE(password) com a role Django e permitiu com a role FastAPI em transacoes desfeitas. Segredo local Base64 de 32 bytes em `.env.api.local` ignorado e `0600`.
- Correcao do review: `MarketLifecycleEngine` verifica saldo bloqueado com lock antes de refund; API e comando operacional fazem rollback em insuficiencia, com log tecnico. `gotrendlabs_users`, trigger, funcao e sequence pertencem a `gotrendlabs_auth_owner` sem login; grant por coluna tira UPDATE(password) de Django e preserva edicao de perfil, FastAPI conserva a escrita de credencial. Scripts locais e servico `migrate` separam credencial operacional; deploy repete grants apos migrations e falha no preflight inseguro.
- Evidencia adicional local: script de setup idempotente; Django recebeu SQLSTATE 42501 ao tentar UPDATE(password), FastAPI conseguiu em transacao desfeita, Django atualizou campo nao sensivel e INSERT com senha utilizavel foi bloqueado pelo trigger; preflight recusou GRANT inseguro temporario e o rollback da transacao restaurou a fronteira. Inventario sem PII anterior ao smoke mobile: 3 contas locais, 2 hashes v1, 1 PBKDF2, 1 admin. Benchmark Mac de 8 operacoes por nivel chegou a p95 de ~109 ms com 5 workers e RSS ~54 MiB, sem extrapolacao para EC2; Compose config, migrations --plan e OpenAPI validados. Suite completa: 267 testes passaram com `BACKEND_API_URL=http://127.0.0.1:9`; os tres testes de pagina que falharam sem isolamento consultavam o mercado ja concluido na API local em vez da fixture aberta. Dois cenarios novos de rollback de refund passaram tambem em execucao focada. API e site locais responderam `200` apos reinicio.
- Smoke adicional local: 13 testes focados de senha, cadastro/sessao/logout, reset, administracao, cancelamento, reconciliacao e paginas web passaram; API real retornou `200/200/200/204/401` para health/login/sessao/logout/token revogado; site real aceitou login do administrador e logout. `flutter test` passou com 107 testes e `flutter analyze` sem issues; APK debug compilou, abriu no emulador Android, carregou mercado pela API local, autenticou conta temporaria, exibiu perfil e voltou ao estado visitante apos logout. As duas contas temporarias do smoke foram desativadas pela API administrativa. O email local `admin@localhost` e recusado pela validacao de email do formulario Flutter, entao o login mobile foi validado com email de teste valido; isso nao altera o contrato da API nem prova compatibilidade de credenciais produtivas.
- Revisao pos-smoke de `43ec566` contra `origin/main` (`8e1b733`) identificou credenciais `FASTAPI_POSTGRES_*` no ambiente compartilhado, que permitiam ao processo Django escolher a role FastAPI apesar do grant por coluna. Correcao local: credenciais FastAPI movidas para `.env.api.local`; `.env` deixa de expor essa role e a credencial de bootstrap; Compose produtivo passa a injetar `.env.fastapi-db.prod` somente na FastAPI, mantendo Django/daemon na role Django. `auth_db_boundary check` rejeita credenciais alternativas FastAPI/migracao expostas, `check-api` exige a role FastAPI autorizada, e o inventario usa o ambiente da API; probes, inventario e idempotencia do `apply` passaram. API e web locais reiniciados e responderam `200`; conexoes diretas confirmaram role FastAPI na API e role Django no daemon, e login/sessao/logout reais pela API passaram. Dez testes focados pos-correcao, `manage.py check`, `bash -n` e `git diff --check` passaram. Compose `--profile ops config --quiet` passou com modelos temporarios e a checagem de ambiente resolveu apenas credenciais permitidas por servico. Inventario apos smoke: 5 contas, 4 hashes v1, 1 PBKDF2; as 2 contas criadas no smoke estao desativadas. Nenhum host produtivo foi alterado.
- Infra inicial: EC2 `gotrendlabs-prod-host` `t4g.micro` e RDS `gotrendlabs-prod-db` `db.t4g.micro`, sem host/banco de ensaio separado. Antes do corte, o SQL de grants/ownership passou no RDS dentro de transacao revertida; a capacidade foi observada no primeiro deploy, sem ensaio de carga equivalente.
- Decisao de 2026-09-27: usuario optou por pular o ensaio isolado por indisponibilidade de recursos e por informar que o aplicativo ainda nao esta em uso produtivo. A validacao RDS/EC2 deixa de ser gate pre-merge nesta fase, mas seus riscos permanecem conhecidos e devem ser monitorados no corte inicial; o benchmark Mac nao substitui medicao no host.
- Preparo produtivo: `.env.auth.prod`, `.env.fastapi-db.prod` e `.env.migrate.prod` instalados com modo `0600`; arquivo compartilhado limpo de credenciais FastAPI. Pepper e senha bootstrap do `@admin` guardados em `gotrendlabs/prod/app-secrets`, sem valores em Git/logs; snapshot RDS recuperavel `gotrendlabs-auth-argon2id-20260927` disponivel antes da mudanca. A role migradora recebeu associacao necessaria; SQL de fronteira passou em transacao com rollback. Inventario inicial: 5 contas, 3 PBKDF2 e 2 senhas inutilizaveis.
- Publicacao: PR `#126` mergeada via squash `a41722074088623519e6f8a58dcbe091351c9dee`; CI na branch `36329832007` passou sem deploy, e GitHub Actions `36330226816` passou testes e deploy SSM `227c99a2-428f-42b4-8e1b-a3962d37c945` na `main`.
- Validacao produtiva: `GET /api/health` informou `status=ok` e checks de API/banco `ok`; site respondeu `200`. Senha de `@admin` definida pelo codigo da FastAPI com revogacao de sessoes; dois hashes PBKDF2 remanescentes foram tornados inutilizaveis, com sessoes revogadas e evento administrativo. Inventario final: 1 hash Argon2id, 0 PBKDF2 e 4 senhas inutilizaveis. Login/sessao/logout/revogacao pela API com headers mobile `1.2.0+14` retornaram `200/200/204/401`; login/sessao/logout web passaram. `auth_db_boundary check` e `check-api` passaram com as roles reais; Django/daemon nao recebem pepper nem credenciais FastAPI, e o host executa o commit do merge.
- Capacidade observada: EC2 tinha 301 MiB de memoria disponivel e 370 MiB de swap usado antes do corte; apos deploy/smokes, 366 MiB disponiveis e 355 MiB de swap usado. `CPUCreditBalance` recente: 286,69. Isto comprova apenas o primeiro smoke, nao carga sustentada.
- Acompanhamento apos PR documental `#127`: GitHub Actions `36331039961` concluiu CI e novo deploy com sucesso (`8c1a1562c734d8d19ce4145291205b2b7556aa5c`). O primeiro login `@admin` depois desse deploy retornou `401`; o hash Argon2id existente nao verificava contra a credencial bootstrap guardada, embora o pepper do arquivo coincidisse com o Secrets Manager. A causa da divergencia nao foi estabelecida. A senha foi redefinida novamente pelo codigo da FastAPI, com revogacao de sessoes e verificacao imediata do hash. Smokes independentes de login/sessao/logout/revogacao mobile-header passaram; reinicio e recriacao do container FastAPI, seguidos de reaplicacao dos grants e migrations sem pendencias, preservaram a verificacao e os smokes passaram novamente. Login/sessao/logout web tambem passaram. Inventario final permaneceu 1 Argon2id, 0 PBKDF2, 4 inutilizaveis; ultimo smoke mostrou 309 MiB de memoria disponivel, 353 MiB de swap usado e `CPUCreditBalance` 287,89. Monitorar reincidencia de `401` apos proximos deploys e investigar se ocorrer.
- Conclusao local em: 2026-09-27; entrega publicada e validada em: 2026-09-27.
- Reaberto apos review em: 2026-09-27
- Proxima acao: observar memoria, swap, latencia e creditos de CPU sob uso real; planejar evolucoes restantes de `FEAT-AUTH-001` em outro ciclo. Branch local `feat/argon2id-pepper-passwords` preservada.

## WFLOW-20260927-AUTH-PASSWORD-HASH-033

- Tipo: `change-feature` + `implementation-cycle` + `test-review-cycle`.
- Status: `substituido`.
- Substituido pelo corte de autoridade `WFLOW-20260927-AUTH-API-AUTHORITY-034`.
- Feature alvo: `FEAT-AUTH-001`.
- Objetivo: substituir o hash PBKDF2 de senhas por Argon2id com pepper compartilhado entre FastAPI e Django.
- Etapa atual: implementacao e validacao local concluidas; preparacao operacional produtiva pendente antes de merge/deploy.
- Artefatos afetados: spec de auth, arquitetura, ADR, codigo FastAPI/Django, requisitos, configuracao de ambiente, testes e memoria operacional.
- Decisao de escopo: sem migracao de hashes PBKDF2 nem preservacao de contas de desenvolvimento, conforme orientacao do usuario; sem mudanca de schema ou contrato HTTP.
- Fronteiras: FastAPI continua autoridade de autenticacao; Django usa o mesmo hasher apenas ao criar/verificar usuarios locais; o pepper fica fora do banco e do Git.
- Implementacao: `argon2-cffi` e primitiva compartilhada com HMAC-SHA256/pepper de 32 bytes, Argon2id `m=19456 KiB,t=2,p=1`, salt de 16 bytes e limite de duas operacoes caras por processo; adaptador Django, validacao produtiva fail-closed, env examples e ADR-0008. Pepper local gerado em `.env` ignorado pelo Git.
- Evidencia local: 265 testes passaram na suite completa; quatro testes especificos de senha passaram apos ajuste final do guard de ambiente; tres testes de integracao auth passaram, incluindo cadastro/login, reset e login social; `manage.py check`, `makemigrations --check --dry-run`, OpenAPI `--check` e `git diff --check` passaram. Benchmark local sequencial: hash 81,5 ms e verificacao 40,0 ms de media em cinco operacoes cada, sem inferencia de capacidade da EC2.
- Checklist: feature v0.5, arquitetura, estrategia de teste, integration map, ADR, changelogs, status e known gaps atualizados; schema e OpenAPI sem alteracao; sem arquivos mobile modificados.
- Pendencias operacionais: provisionar `GOTRENDLABS_PASSWORD_PEPPER` no ambiente produtivo antes de merge/deploy automatico, medir memoria/latencia concorrente na EC2 e recriar/resetar contas preexistentes se houver. Nenhuma publicacao feita nesta branch.
- Iniciado em: 2026-09-27
- Atualizado em: 2026-09-27
- Encerrado localmente em: 2026-09-27
- Proxima acao: revisar a branch e configurar o segredo produtivo antes de qualquer integracao/deploy.

## WFLOW-20260926-EDITORIAL-CLOSEOUT-032

- Tipo: `implementation-cycle` + `test-review-cycle` + fechamento de feature.
- Status: `concluido`
- Feature alvo: `FEAT-EDITORIAL-001`.
- Objetivo: fechar o escopo aprovado (manual/ficha/checklist e consulta staff no Admin Ops), publicar via PR e comprovar funcionamento em produção.
- Etapa atual: escopo editorial implantado e validado em produção.
- Artefatos afetados: feature spec, status, arquitetura Admin Ops, changelogs, integration map, known-gaps, README, código Django/CSS, requisitos, testes e workflow.
- Decisão: avaliação por IA, parecer estruturado e gate autoritativo não integram esta feature; serão evolução futura. O usuário aceitou manter o conteúdo editorial no repositório público, com a limitação registrada na spec.
- Fronteiras: Django apresenta material versionado somente a staff; FastAPI continua autoridade de domínio; sem alteração de OpenAPI, banco, migrações, mobile ou fórmulas. Nenhum ADR necessário.
- Validação local: 261 testes passaram com `BACKEND_API_URL=http://127.0.0.1:9`, isolando a API local de desenvolvimento; os três testes web que falharam na primeira execução haviam recebido um mercado já resolvido dessa API e passaram no isolamento. OpenAPI `--check`, `manage.py check`, `makemigrations --check --dry-run`, links locais e `git diff --check` aprovados; visual do Admin Ops aprovado pelo usuário.
- Entrega: commit `a1b4eca` da branch `feat/editorial-market-guidelines` integrado pela PR `#124` via squash `e4b4081` na `main`; a branch local foi preservada.
- Validação produtiva: GitHub Action `36275879637` concluiu detect-changes, suíte completa e deploy via SSM com sucesso. Antes do deploy, `GET /admin-ops/editorial/` retornava `404`; depois, visitante recebeu `302` para `/login/`, `/api/health` retornou `200` e cada um dos três documentos renderizou `200` com sessão staff no container produtivo (`SSM 0b0c6f07-a5bc-4fec-a57d-e6b4008901f2`). O primeiro smoke interno usou uma sessão sintética incompleta e foi repetido com os campos exigidos pelo layout; nenhum ajuste de produto ou configuração produtiva foi necessário.
- Checklist universal: origem funcional, feature spec, arquitetura, testes, changelogs, implementation status, integration map e known gaps alinhados; contratos revisados sem alteração, sem migrations ou ADR. Evolução de IA e parecer estruturado permanece registrada fora deste escopo. Documentos no repositório público conforme decisão do usuário.
- Estado de implementação: `implementada_validada`.
- Pendências: nenhuma para a entrega editorial aprovada.
- Iniciado em: 2026-09-26
- Atualizado em: 2026-09-26
- Encerrado em: 2026-09-26
- Próxima ação: abrir novo ciclo se a equipe decidir implementar avaliação assistida por IA ou privacidade dos arquivos fora do site.

## WFLOW-20260926-EDITORIAL-ADMIN-031

- Tipo: `change-feature` + `implementation-cycle` + `test-review-cycle`
- Status: `concluido_local`
- Feature alvo: `FEAT-EDITORIAL-001`
- Objetivo: disponibilizar editorial aprovado no Admin Ops local e critérios estruturados para futura avaliação de mercados por IA.
- Etapa atual: implementação local concluída; disponível em `http://127.0.0.1:8000/admin-ops/editorial/` para avaliação do usuário.
- Artefatos afetados: Django Admin Ops, conteúdo editorial versionado, requisitos, testes e estado documental.
- Limites: consulta read-only, sem avaliação por IA, parecer persistido ou publicação automática; nenhuma operação em produção.
- Iniciado em: 2026-09-26
- Atualizado em: 2026-09-26
- Implementação: rota GET staff, manual/checklist/ficha renderizados do repositório, critérios JSON v1.2, menu, lista e atalhos no editor, CSS responsivo e dependência Markdown.
- Arquitetura e segurança: Django apenas lê o editorial e apresenta orientações; `admin_api_required`, GET exclusivo, escape de HTML bruto e `Cache-Control: private, no-store`. FastAPI continua responsável por mercado/publicação; nenhuma avaliação IA ou parecer persistido.
- Evidência local: 7 testes focados passaram (`tests.test_editorial_admin` e smoke real do editor); `manage.py check`, OpenAPI `--check` e `git diff --check` passaram. O banco de testes pré-existente foi reutilizado com `--keepdb`; não foi removido. `curl` confirmou redirect ao login no Django e `200` no health FastAPI.
- Ambiente para avaliação: PostgreSQL local já saudável; Django em `127.0.0.1:8000` e FastAPI em `127.0.0.1:8001` iniciados nesta sessão. Sem deploy ou alteração de mercados.
- Pendências: avaliação visual/funcional pelo usuário e revisão em PR antes de qualquer publicação. Automação de IA continua como evolução futura, fora do escopo.
- Atualizado em: 2026-09-26
- Encerrado localmente em: 2026-09-26
- Próxima ação: usuário testar a página como staff e retornar ajustes, se houver.

## WFLOW-20260926-EDITORIAL-030

- Tipo: `promote-spec`
- Status: `concluido`
- Feature alvo: `FEAT-EDITORIAL-001`, versão `1.2`
- Objetivo: registrar aprovação explícita do usuário à versão documental vigente.
- Decisão: spec `aprovada`; implementação permanece `documentada`. Integração Admin Ops e IA será uma evolução separada.
- Artefatos afetados: frontmatter e escopo da feature, implementation-status, changelogs e workflow.
- Validação: escopo, dependências, responsabilidades, contratos revisados e critérios de aceite conferidos; promoção sem mudança de conteúdo editorial, runtime ou contratos; `git diff --check` aprovado.
- Arquitetura: consultadas estrutura de navegação/editor Admin Ops e integração LLM existente para fundamentar recomendação; nenhuma alteração no site ou chamada a provedor.
- Iniciado em: 2026-09-26
- Atualizado em: 2026-09-26
- Encerrado em: 2026-09-26
- Próxima ação: definir evolução de consulta administrativa e pacote editorial versionado para avaliação assistida, sem presumir implementação ou aprovação automática.

## WFLOW-20260926-EDITORIAL-029

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-EDITORIAL-001`
- Objetivo: organizar o editorial pela construção de mercados de previsão, incluir contexto inicial sobre mercados/opções, separar checklist de publicação e planejamento de categorias, e agrupar indicadores por participação e qualidade.
- Artefatos afetados: manual, ficha, checklist, spec editorial, origem funcional, README e memória operacional.
- Decisões: usar mercado de previsão como termo do produto; explicar opções como respostas possíveis. Diversidade orienta catálogo, sem cotas obrigatórias para aprovar um mercado.
- Iniciado em: 2026-09-26
- Atualizado em: 2026-09-26
- Entrega: manual/ficha/checklist v1.2 com contexto de mercados de previsão e opções de resposta, seis etapas, planejamento de categorias separado e indicadores agrupados por participação e qualidade.
- Validação: `.venv/bin/python` verificou 27 links locais novos/alterados, sequência das seis etapas, introdução antes do processo, grupos de indicadores, correspondência E01–E11 e remoção das cotas/piloto nos guias; `git diff --check` aprovado. Leitura cruzada preservou definição protegida, prazo de correção e selagem.
- Arquitetura e testes: alteração documental, sem contratos novos ou mudanças de domínio. Aceite ampliado para definição do produto, fonte/critério acima do consenso e ausência de cotas de aprovação. Não requer ADR, testes de runtime ou deploy.
- Estado: origem funcional, spec, arquitetura Admin Ops, README, integration map, status e changelogs sincronizados. Nenhuma pendência desta entrega.
- Encerrado em: 2026-09-26
- Próxima ação: revisar conteúdo em PR; uso operacional e automação permanecem separados desta entrega.

## WFLOW-20260926-EDITORIAL-028

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-EDITORIAL-001`
- Objetivo: reescrever manual e ficha para staff sem conhecimento técnico, explicar regras com exemplos e substituir o piloto por acompanhamento dos indicadores.
- Artefatos afetados: manual, ficha, spec editorial e memória operacional.
- Decisão: preservar regras de publicação/integridade; linguagem técnica permanece na spec. Remover metas de cadência, duração e distribuição temática do piloto.
- Iniciado em: 2026-09-26
- Atualizado em: 2026-09-26
- Entrega: manual/ficha v1.1 com exemplos e orientações para staff; nomes de campos e contratos concentrados na spec; seção de indicadores sem metas de piloto.
- Validação: `.venv/bin/python` verificou 9 links locais, correspondência E01–E11, remoção do piloto e ausência dos termos técnicos revisados no manual/ficha; leitura cruzada preservou regras de integridade e publicação. `git diff --check` aprovado.
- Arquitetura e testes: sem alteração de contrato ou runtime; sem necessidade de ADR ou testes executáveis novos. Critérios de aceite ampliados para compreensão por staff e dados indisponíveis.
- Estado: changelogs, status e lacunas atualizados. Nenhuma pendência desta revisão documental.
- Encerrado em: 2026-09-26
- Próxima ação: revisão do conteúdo pelo usuário; publicação/automação continuam fora desta entrega.

## WFLOW-20260926-EDITORIAL-027

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-EDITORIAL-001`
- Objetivo: entregar manual editorial, ficha reutilizável e critérios de revisão/publicação como processo operacional documentado.
- Etapa atual: entrega documental concluída localmente; manual, ficha, spec e referências integrados.
- Artefatos afetados: spec funcional, feature editorial, manual e ficha em `docs/editorial/`, README, arquitetura Admin Ops e memória operacional.
- Escopo: documentação; sem novos campos, endpoints, bloqueio automático de publicação ou alterações de mercados.
- Base: `origin/main` atualizada por fetch, commit `6f156cc`, branch `feat/editorial-market-guidelines`.
- Iniciado em: 2026-09-26
- Atualizado em: 2026-09-26
- Encerrado em: 2026-09-26
- Arquitetura e segurança: revisadas com as skills software-architect/architecture-guard; FastAPI preserva autoridade, definição assinada não muda e selagem mantém correções append-only. Sem mudança estrutural, ADR, schema ou contrato.
- Aceite: estratégia de testes revisada com test-strategy; cenários de fonte inválida, duplicidade, ambiguidade, prazo incorreto, edição pós-parecer e correção pós-selagem documentados na feature e confrontados com manual/ficha.
- Validação: Python do ambiente `.venv` existente verificou 18 links locais novos/alterados, paridade E01–E11, campos de frontmatter e escopo docs-only; `git diff --check` aprovado. Leitura cruzada dos contratos de ciclo de vida/integridade realizada. Sem testes de runtime ou deploy, pois não há código alterado.
- Checklist universal: origem, dependências, feature-changelog, change-log-specs, implementation-status, integration-map e known-gaps sincronizados; contratos revisados sem alteração; nenhuma pendência para a entrega documental.
- Limites: nenhum mercado real criado/publicado, nenhuma consulta de métricas de produção e nenhuma alegação de gate automático. Parecer estruturado, enforcement e telemetria são evolução opcional separada.
- Próxima ação: revisar a entrega em PR; para operar uma pauta, copiar a ficha e aplicar o manual. Automação futura exige ciclo próprio.
- Reversão lógica: registrar revisão posterior do manual/spec e atualizar referências; preservar este histórico.
- Alterações locais pré-existentes preservadas: diretórios não rastreados `apps/mobile/ios/Runner.xcworkspace/xcshareddata/swiftpm/` e `apps/mobile/store-assets/`.

## WFLOW-20260926-MOBILE-GOOGLE-PLAY-CLOSED-TESTING-026

- Tipo: `release-prep`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`
- Objetivo: preparar, submeter e acompanhar o Android App Bundle assinado `1.2.0+14` para uma nova rodada de Google Play Closed testing, usando bases de produção e preservando o canal APK direto do site.
- Etapa atual: release `14 (1.2.0)` disponível aos testadores selecionados no track `Closed testing - Alpha`, com rollout de 100% para a audiência configurada.
- Artefatos afetados: `apps/mobile/pubspec.yaml`, `apps/mobile/README.md`, specs mobile, critérios de aceite e memória operacional.
- Release name preparado: `1.2.0+14 - Closed testing Android`; o envio foi submetido com o nome automático `14 (1.2.0)`.
- Release notes publicadas no Play Console (`pt-BR`):

```text
<pt-BR>
Conheça o GoTrendLabs, uma plataforma social de previsões sobre temas e acontecimentos relevantes. Explore mercados, registre suas previsões com créditos educativos, acompanhe seu desempenho, construa reputação e participe da comunidade. Tudo com resultados transparentes e verificáveis — sem envolver dinheiro real.
</pt-BR>
```

- Decisões: `versionCode 14` evita reutilizar builds anteriores; o AAB usa a assinatura release local e não altera `/app/android/latest.json`, o APK ativo `1.0.7 (8)` nem a política produtiva de build mínimo.
- Pendências: nenhuma para esta rodada de Closed testing; publicação pública/open testing permanece fora do escopo.
- Iniciado em: 2026-09-26
- Atualizado em: 2026-09-26
- Encerrado em: 2026-09-26
- Retomada: acompanhar instalações e feedback dos testadores pelo canal configurado. O canal direto do site permanece no APK `1.0.7 (8)` e não foi alterado por esta publicação.
- Reversão operacional: interromper a disponibilidade da release no track Alpha pelo Play Console se surgir regressão crítica; preservar o registro documental e usar um novo `versionCode` para qualquer bundle corretivo.
- Evidências de validação local: `flutter pub get`; `flutter analyze` sem issues; `flutter test` com 106 testes aprovados; build release com bases `https://gotrendlabs.com.br/api` e `https://gotrendlabs.com.br`; manifest processado com package `br.com.gotrendlabs.gotrendlabs_mobile`, `versionCode=14`, `versionName=1.2.0`, `minSdk=24` e `targetSdk=36`; ABIs `arm64-v8a`, `armeabi-v7a` e `x86_64`; URLs de produção confirmadas nos binários AOT.
- Evidências do AAB: assinatura verificada por `jarsigner` com certificado de upload `CN=GoTrendLabs, OU=Mobile, O=GoTrendLabs, L=Sao Paulo, ST=SP, C=BR`, fingerprint SHA-256 `3B:54:9C:B7:58:24:73:32:D5:EC:1C:DD:55:22:D3:5F:B1:53:60:D2:40:BD:39:74:E4:C4:AC:1D:4E:2B:E0:5F`; tamanho `57524579` bytes; SHA-256 do bundle `0f87b9634be842f69c0c257b6a41c35313a29750c13ae3cba9cd25068b172a16`.
- Evidências do Google Play: em 2026-09-26, a visão geral mostrou `14 (1.2.0)` como `Available to testers on Google Play`, `Full rollout`, ativa e habilitada em 177 países/regiões; os detalhes confirmaram `Available to selected testers`, rollout de 100% e publicação às 11:54. O App Bundle `Enhanced` inclui ReTrace mapping e símbolos nativos, API mínima 24, target SDK 36, quatro layouts, três ABIs e um recurso obrigatório; entrega estimada de `9.83 MB` em nova instalação e `2.24 MB` em atualização; o bundle 11 foi desativado. As notas gerais em `pt-BR` estão presentes no Console. Testadores usam o Google Group `gotrendlabs-testers@googlegroups.com`, feedback aponta para `https://gotrendlabs.com.br/feedback/` e adesão web usa `https://play.google.com/apps/testing/br.com.gotrendlabs.gotrendlabs_mobile`.

## WFLOW-20260919-ADULT-ONLY-AUTH-025

- Tipo: `change-feature` + `implementation-cycle` + `test-review-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`, `FEAT-MOBILE-001`
- Objetivo: restringir a criação de contas humanas a pessoas com 18 anos completos, usando data de nascimento obrigatória e validação autoritativa na FastAPI em cadastro por senha e social.
- Etapa atual: implementação integrada, migration aplicada e validada em produção na API/web; fluxo mobile validado no Galaxy S20 contra o contrato publicado.
- Artefatos afetados: spec funcional, feature de autenticação, arquiteturas backend/web/mobile, política de uso, schema/modelo/migration de perfil, contratos FastAPI/OpenAPI, cadastro Django/Flutter, OAuth social, testes e memória operacional.
- Decisões: `birth_date` passa a ser obrigatória e privada para contas humanas; maioridade é calculada pela FastAPI por data civil com limite de 18 anos completos; perfis pré-produção sem nascimento recebem `1990-01-01` em migration e não haverá fluxo de regularização de legado; contas técnicas internas criadas fora do cadastro público usam o mesmo fallback pré-produção; UI pode validar formato/completude, mas não decide elegibilidade.
- Reversão lógica: reverter contrato/UI e tornar a coluna novamente anulável em migration posterior; não apagar datas já coletadas.
- Arquitetura e segurança: FastAPI permanece autoridade única da maioridade; Django/Flutter apenas coletam e exibem; não houve mudança de fronteira que exija ADR; nascimento continua ausente de contratos públicos.
- Evidências locais: suíte Django/FastAPI completa com 255 testes aprovada usando `BACKEND_API_URL` isolada do servidor local; 3 testes focados adicionais de limite exato, menoridade, perfil, OAuth e formulário web aprovados após os últimos ajustes; revisão de branch corrigiu a possibilidade de limpar `birth_date` no perfil mobile; `flutter analyze` sem issues e 106 testes Flutter aprovados; cadastro e edição de perfil foram validados no Galaxy S20 físico com formato `DD/MM/AAAA`, normalização para `YYYY-MM-DD` e bloqueio local de data vazia; OpenAPI regenerado e validado; `manage.py check`, `makemigrations --check --dry-run`, `sqlmigrate accounts 0022`, compilação Python e `git diff --check` aprovados.
- Evidências de publicação: PR `#121` mergeada em `main` pelo merge commit `340ea869ea66891d2dc0f7bd262107b76f72e21c`; GitHub Actions `GoTrendLabs CI and Deploy` run `36246617456` concluiu teste e deploy com sucesso; o deploy executou a migration `accounts 0022` antes de subir os serviços.
- Evidências de produção: `/api/health` respondeu `status=ok`, `maintenance.web_enabled=false`, `maintenance.mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; OpenAPI exige `birth_date` nos contratos de cadastro por senha e conclusão social; cadastro sem nascimento, com nascimento futuro e de menor de idade retornou `422`, usando `code=minimum_age_required` no caso de menoridade; a data de limite exato de 18 anos ultrapassou a validação etária e foi interrompida no aceite de política, sem criação de conta. Após autorização explícita do proprietário, a manutenção web foi desativada via SSM `cc54c81d-a0cb-4dc3-9a9e-4f8eb563f79e`; home, `/register/` e `/use-policy/` responderam `HTTP 200`, e cadastro/política exibiram data obrigatória, aviso de 18 anos completos e privacidade do nascimento.
- Iniciado em: 2026-09-19
- Atualizado em: 2026-09-26
- Encerrado em: 2026-09-26

## WFLOW-20260919-DAEMON-DB-CONNECTIONS-024

- Tipo: `bugfix` + `test-review-cycle`
- Status: `concluido_local_aguardando_pr_e_deploy`
- Feature alvo: `FEAT-OPSLOG-001`, `FEAT-NOTIFY-001`
- Objetivo: evitar que o processo contínuo do daemon reutilize conexões Django encerradas entre ciclos, o que interrompia as rotinas de outbox de email e push em produção.
- Evidência produtiva: entre `2026-09-18 13:42 UTC` e `2026-09-19 13:42 UTC`, `daemon.email_failed` e `daemon.push_failed` ocorreram 287 vezes cada, em ciclos de cinco minutos, com `OperationalError` de conexão fechada/perdida.
- Implementação: `run_gotrendlabs_daemon` chama `close_old_connections()` antes e no `finally` de cada ciclo; nenhuma regra de domínio, contrato, migration ou configuração produtiva foi alterada.
- Validação local: 2 testes focados aprovados; `manage.py check`, `makemigrations --check --dry-run`, compilação Python e `git diff --check` aprovados.
- Reversão lógica: reverter somente o comando e seu teste; dados, filas e eventos persistidos permanecem intactos.
- Iniciado em: 2026-09-19
- Atualizado em: 2026-09-19

## WFLOW-20260907-PRODUCTION-AUDIT-FOLLOWUPS-023

- Tipo: `change-feature` + revisao operacional documental
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`, `FEAT-NOTIFY-001` e infraestrutura produtiva
- Objetivo: registrar como evolucoes planejadas os achados da auditoria posterior ao rollout, sem alterar runtime, reabrir a feature validada ou confundir hardening de infraestrutura com falha criptografica atual.
- Artefatos afetados: feature de integridade, arquiteturas de banco/API/scheduler/comunicacoes/Admin Ops, estrategia de testes, runbook de producao, known gaps e changelogs.
- Prioridades: P1 para separar owner/migrator das roles runtime do ledger e tornar alarmes realmente notificantes; P2 para capacidade/HA, retencao operacional, identidade por workload, rotacao versionada do commitment secret, headers FastAPI, tratamento de push terminal e carga/observacao continuada.
- Evidencias: cadeia/checkpoint e assinatura KMS permaneceram validos; API/banco e containers saudaveis. A auditoria encontrou ownership/privilegios amplos apesar dos triggers, alarmes sem destino, alarme de disco com dimensao incorreta, host/RDS pequenos e Single-AZ, retencao de logs de um dia, ausencia de fluxo permanente para push terminal e headers defensivos incompletos na FastAPI.
- Limpeza operacional associada: quatro `PushDelivery` antigas que haviam esgotado retries foram removidas em transacao, preservando duas `UserNotification` de origem e registrando `AdminEvent` id 96; nenhum retry pendente permaneceu. A spec registra o mecanismo definitivo ainda necessario, nao uma pendencia de dados atual.
- Decisao: nenhuma alteracao de infraestrutura ou codigo faz parte deste workflow; cada item futuro exige ciclo proprio, teste proporcional, rollback e atualizacao das evidencias.
- Validacao: revisao de consistencia documental e `git diff --check`.
- Iniciado em: 2026-09-07
- Atualizado em: 2026-09-07
- Encerrado em: 2026-09-07

## WFLOW-20260907-INTEGRITY-CLOSEOUT-022

- Tipo: `promote-spec` + `implementation-cycle` + `test-review-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`
- Objetivo: promover a spec para aprovada, publicar a implementação na `main`, provisionar KMS/IAM/segredo em produção, executar corte destrutivo controlado dos mercados pré-lançamento, adicionar um segundo worker Django e validar o rollout ponta a ponta.
- Etapa atual: implementação, rollout AWS, corte pré-lançamento, deploy, smoke produtivo e fechamento documental concluídos.
- Artefatos afetados: feature/status/changelogs/runbook, Compose de produção, exemplo de ambiente, comando de corte pré-produção, testes, GitHub Actions e recursos AWS de produção.
- Estado AWS pós-rollout: snapshot criptografado `gotrendlabs-prod-pre-integrity-20260907-01` disponível; chave KMS Ed25519 `bcbb43d0-cfba-465d-9c1d-500776ede30c` habilitada sob `alias/gotrendlabs-integrity-signing`; role EC2 com política restrita ao ARN da chave; segredo de commitment presente no Secrets Manager/runtime; alarme `gotrendlabs-prod-kms-sign-volume-high`; 1 GiB de swap persistente com `swappiness=10`.
- Decisões: aprovação funcional e execução produtiva foram autorizadas pelo usuário; implementação promovida para `implementada_validada`; Django opera com dois workers Uvicorn e o daemon permanece único; todos os mercados anteriores sem definição foram removidos sem assinatura retroativa nem camada de legado.
- Reversão lógica: antes do corte criar snapshot manual do RDS; preservar recursos/provas criptográficas após o primeiro registro; rollback de aplicação por commit anterior, retorno temporário do Django a um worker se houver pressão de memória e desativação de novas mutações se o KMS estiver indisponível.
- Evidências: PR principal `#114` e hotfix `#115` integradas por merge commit; workflows `34157223820` e `34158379066` aprovados com suíte completa e deploy. O primeiro corte foi revertido atomicamente por FK de `PushDelivery`; o hotfix adicionou inventário/remoção estritamente relacionada e regressão. A execução corrigida removeu 30 mercados, 4 previsões, 43 comentários, 7 notificações e 21 entregas push; a repetição retornou zero. Produção confirmou commit `c40fd61`, migrations `markets 0027–0031`, `admin_ops 0018–0019` e `communications 0008`, assinatura KMS real válida, fingerprint `b971f3baf64555002c200d2d34098aa0566da9a796feffae45e4b6145af5124a`, cadeia `verified`/válida sem pendências, FastAPI/banco `ok`, dois workers Django, um daemon e 101 testes Flutter locais aprovados.
- Iniciado em: 2026-09-07
- Atualizado em: 2026-09-07
- Encerrado em: 2026-09-07

## WFLOW-20260907-INTEGRITY-HARDENING-021

- Tipo: `change-feature` + `implementation-cycle` + `test-review-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`, `FEAT-MOBILE-001`
- Objetivo: fechar achados de revisao sobre selagem apoiada em checkpoint historico, exposicao publica de referencias individuais de previsao, validacao incompleta de metadados persistidos e repeticao custosa de auditoria integral apos divergencia confirmada.
- Etapa atual: specs, implementação, contratos, consumidores e regressão concluídos.
- Artefatos afetados: ADR-0007, feature/contrato/arquitetura/testes, verificador FastAPI, daemon, OpenAPI, consumidores Django/Flutter e memoria operacional.
- Decisoes: Seal exige auditoria global integral fresca sob lock; prova publica agrega compromissos e omite eventos/referencias individuais de previsao; definicao, compromisso, Seal, folhas e checkpoint confrontam metadados persistidos com payload/chave/relacoes; falha global identica usa backoff de uma hora sem novo checkpoint/KMS a cada ciclo e suprime previamente a fila de selagem.
- Evolucoes registradas: versionamento do segredo de pseudonimizacao e resumo de verificacao materializado por mercado ficam planejados para evolucao da plataforma, sem mudanca de schema nesta execucao.
- Reversao logica: reverter codigo/contrato por commit preservando eventos, provas e checkpoints append-only; nenhuma migration destrutiva sera criada.
- Evidencias: 32 testes de `tests.test_integrity_ledger` aprovados; 218 testes web aprovados na regressão combinada e os 3 casos afetados por interferência do servidor local aprovados isoladamente com backend externo desativado; 101 testes Flutter aprovados e `flutter analyze` sem issues; teste focado adicional do modal mobile aprovado; OpenAPI sincronizado; `manage.py check`, `makemigrations --check --dry-run`, compilação Python e `git diff --check` aprovados. Testes dedicados comprovam que adulteração histórica anterior ao checkpoint bloqueia Seal, metadados persistidos adulterados falham, divergência idêntica respeita backoff e estado global `failed` suprime a fila automática de selagem. A infraestrutura de teste desabilita a proteção contra `TRUNCATE` somente no banco isolado e apenas durante o flush do Django, mantendo a trigger de produção inalterada.
- Iniciado em: 2026-09-07
- Atualizado em: 2026-09-07
- Encerrado em: 2026-09-07

## WFLOW-20260907-INTEGRITY-CHECKPOINTS-020

- Tipo: `change-feature` + `implementation-cycle` + `test-review-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`, `FEAT-MOBILE-001`
- Objetivo: retirar a varredura integral da cadeia global das requisicoes publicas por meio de checkpoints assinados, auditoria incremental no daemon e auditoria integral periodica, mantendo selagem fail-closed.
- Etapa atual: arquitetura, contrato, implementacao, corte local, regressao e validacao de indices concluidos.
- Artefatos afetados: ADR, feature/contrato/arquitetura, PostgreSQL/migration, verificador FastAPI, daemon, OpenAPI, Django, Flutter, Admin Ops, testes e memoria operacional.
- Decisoes: contrato final sem compatibilidade com builds Flutter pre-producao; estados globais `verified`, `pending`, `failed` e `unavailable`; requisicao publica nunca faz full scan; cards nao oscilam por backlog normal, mas falha confirmada continua removendo sinal positivo; selagem valida delta sob lock.
- Reversao logica: desativar consumo publico do checkpoint por reversao de codigo, preservar checkpoints/eventos append-only e retornar temporariamente a auditoria integral backend; migration nao sera revertida destrutivamente em ambiente com provas.
- Evidencias: `ADR-0007`; migration `0031`; 28 testes de `tests.test_integrity_ledger` e 221 de `tests.test_web_smoke` aprovados; 101 testes Flutter aprovados e `flutter analyze` sem issues; OpenAPI regenerado e `--check` aprovado; `manage.py check`, `makemigrations --check --dry-run`, compilacao Python e `git diff --check` aprovados. Teste dedicado bloqueia qualquer chamada ao scanner global no request publico. `EXPLAIN` local confirmou `Index Scan Backward` para o head e `Index Scan` por intervalo/limite em `integrity_ledger_events_sequence_key`.
- Resultado local: PostgreSQL pre-producao reinicializado conforme autorizacao, migrations reaplicadas, dados anteriores descartados sem assinatura retroativa, tres mercados nativos criados (dois `sealed`, um `open`), checkpoint incremental valido ate o evento 11, nenhum alerta pendente; Django/FastAPI/daemon reiniciados e saudaveis.
- Iniciado em: 2026-09-07
- Atualizado em: 2026-09-07
- Encerrado em: 2026-09-07

## WFLOW-20260907-INTEGRITY-REVIEW-019

- Tipo: `change-feature` + `implementation-cycle` + `test-review-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`
- Objetivo: fechar achados de revisao que permitiam selagem de mercado divergente, validade positiva com cadeia global invalida, selo positivo diante de alerta conhecido, assinatura parcial dos metadados do evento, ausencia de auditoria para mercado publicado sem definicao e limpeza excessiva de historico de badges.
- Etapa atual: specs, implementacao, analise de indices e regressao concluidas.
- Artefatos afetados: feature/contrato/arquitetura/testes, FastAPI, daemon, comando de corte pre-producao, cards web/mobile por contrato e evidencias operacionais de indices.
- Decisoes: o Seal exige verificacao integral aprovada; cadeia global invalida torna `valid=false`; alerta de integridade pendente prevalece no resumo visual; todos os metadados persistidos do evento sao vinculados ao payload assinado; mercado publicado sem definicao e divergencia `high`; limpeza remove somente concessoes atribuiveis aos mercados-alvo. O custo linear da cadeia global permanece risco conhecido, com indices avaliados separadamente de cache/checkpoints futuros.
- Reversao logica: reverter codigo e specs por commit sem reescrever provas existentes; nenhuma migration destrutiva faz parte desta execucao.
- Evidencias: 25 testes de `tests.test_integrity_ledger` e 221 testes de `tests.test_web_smoke` aprovados; 101 testes Flutter aprovados e `flutter analyze` sem issues; OpenAPI sincronizado; `manage.py check`, `makemigrations --check --dry-run`, compilacao Python e `git diff --check` aprovados. `EXPLAIN` local confirmou indices unicos para definicao/Seal, index-only scan em `gtl_ialert_market_status_idx` e indice de `market_id` para eventos; a cadeia global pequena usa scan sequencial e permanece custo linear documentado.
- Iniciado em: 2026-09-07
- Atualizado em: 2026-09-07
- Encerrado em: 2026-09-07

## WFLOW-20260907-INTEGRITY-HARDENING-018

- Tipo: `change-feature` + `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`, `FEAT-PRED-001`, `FEAT-AIAGENT-001`, `FEAT-MOBILE-001`
- Objetivo: eliminar dados pre-producao sem prova, exigir compromissos para todas as previsoes, estabilizar taxonomia assinada e isolar a auditoria do daemon sem manter compatibilidade com builds mobile ainda nao publicados.
- Etapa atual: specs, implementacao, corte local, reconciliacao e validacao concluidos.
- Artefatos afetados: feature/contratos/arquitetura, FastAPI, daemon, comando de limpeza, PostgreSQL, testes, OpenAPI e validacao Django/Flutter.
- Decisoes: mercados sem definicao assinada serao removidos por comando explicito apos inventario/backup; nao havera assinatura retroativa; previsoes IA usam a mesma garantia transacional; nomes taxonomicos sao snapshot e IDs sao protegidos; falha da auditoria nao encerra o daemon.
- Reversao logica: restaurar o dump validado em `.runtime/backups/integrity-ledger-cutover-20260907/pre-unsigned-market-purge.dump` para recuperar os dados locais removidos; para provas existentes, nunca apagar ou reescrever eventos, apenas desativar novas mutacoes e corrigir append-only.
- Evidencias: backup PostgreSQL custom de 1,8 MiB validado antes do corte e copiado com SHA-256 `bd27ef3a77af01fade2d87ab6a745654b170b341a85431442d751560d10c0dbd`; `purge_unsigned_markets` removeu 44 mercados publicados sem prova, 33 previsoes e dependencias, e a segunda execucao encontrou zero candidatos; banco local final com 3 mercados abertos e 6 selados, todos com definicao; 6 demos seguem validas e 3 demos adulteradas permanecem para o caminho de falha; 21 testes de integridade e 221 testes web aprovados; `flutter analyze` sem issues e 101 testes Flutter aprovados; OpenAPI atual; `manage.py check`, `makemigrations --check --dry-run`, compilacao Python e `git diff --check` aprovados.
- Iniciado em: 2026-09-07
- Atualizado em: 2026-09-07
- Encerrado em: 2026-09-07

## WFLOW-20260906-MOBILE-DETAIL-DENSITY-017

- Tipo: `change-feature` + `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-UX-001`, `FEAT-MOBILE-001`, `FEAT-INTEGRITY-001`
- Objetivo: corrigir a hierarquia do critério de resolução, compactar `Sua mesa` e métricas e ampliar os detalhes técnicos da integridade no app.
- Etapa atual: specs, implementação Flutter, testes e QA visual física concluídos.
- Artefatos afetados: detalhe, cards/métricas, tela Hoje, comprovantes, testes mobile, specs, changelog e estado operacional.
- Impacto arquitetural: nenhum; o Flutter apenas reorganiza e apresenta contratos existentes da FastAPI.
- Reversão lógica: restaurar a ordem e expansões anteriores sem alterar mercados, posições ou provas criptográficas.
- Evidências: `flutter analyze` sem issues; `flutter test` com 101 testes aprovados; testes de widget cobrem ordem do detalhe, grade compacta de métricas, atalhos de `Sua mesa`, comprovantes recolhidos e conteúdo técnico da integridade; APK debug instalada no Galaxy S20 conectado, usando FastAPI/Django locais via `adb reverse`; QA física confirmou layout sem overflow, grade 3x2, comprovantes fechados e detalhes técnicos expansíveis.
- Iniciado em: 2026-09-06
- Atualizado em: 2026-09-06
- Encerrado em: 2026-09-06

## WFLOW-20260906-MARKET-POSITION-HIERARCHY-016

- Tipo: `change-feature` + `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`, `FEAT-PRED-001`, `FEAT-MARKET-001`
- Objetivo: padronizar a posição e o conteúdo de `Sua posição` no detalhe web em todo o ciclo do mercado.
- Etapa atual: specs, componente compartilhado, regressões e QA visual concluídos.
- Artefatos afetados: detalhe Django, parcial compartilhado de posição, CSS, specs web/i18n, testes, changelog e estado operacional.
- Impacto arquitetural: nenhum; a UI continua apresentando `viewer_position` e previsões retornadas pelo domínio.
- Reversão lógica: restaurar os blocos separados por estado sem alterar previsões, compromissos ou contratos da API.
- Evidências: 4 testes focados e 220 testes de `tests.test_web_smoke` aprovados; `manage.py check`; QA visual autenticado em mercado aberto, em apuração e resolvido; viewport móvel sem overflow; `git diff --check`.
- Iniciado em: 2026-09-06
- Atualizado em: 2026-09-06
- Encerrado em: 2026-09-06

## WFLOW-20260906-MARKET-DETAIL-LIFECYCLE-COPY-015

- Tipo: `change-feature` + `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`, `FEAT-MARKET-001`
- Objetivo: alinhar títulos, descrições, rótulos e métricas do detalhe web ao estado real do ciclo do mercado.
- Etapa atual: títulos, descrições, linha do tempo, rótulos, métricas, specs, regressões e QA visual concluídos.
- Artefatos afetados: detalhe Django, contexto de apresentação, specs web/i18n, testes, changelog e estado operacional.
- Impacto arquitetural: nenhum; a UI continua representando estados e timestamps fornecidos pela FastAPI.
- Reversão lógica: restaurar a copy e condicionais anteriores sem alterar mercados, previsões ou provas criptográficas.
- Evidências: 5 testes focados e 219 testes de `tests.test_web_smoke` aprovados; `manage.py check`; QA visual de `locked`, `resolved` e `sealed`; desktop sem sobreposição e viewport móvel sem overflow; `git diff --check`.
- Iniciado em: 2026-09-06
- Atualizado em: 2026-09-06
- Encerrado em: 2026-09-06

## WFLOW-20260906-INTEGRITY-WEB-COMPLETION-COPY-014

- Tipo: `change-feature` + `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`
- Objetivo: deixar claro no detalhe web selado que o mercado foi concluído, mantendo a integridade verificável como informação complementar.
- Etapa atual: copy, hierarquia, espaçamento, specs, regressão web e QA visual concluídos.
- Artefatos afetados: detalhe Django, specs web/i18n, teste de renderização, changelog e estado operacional.
- Impacto arquitetural: nenhum; somente copy e hierarquia de apresentação sobre o estado `sealed` já retornado pela FastAPI.
- Reversão lógica: restaurar os textos anteriores no template e nas specs, sem alterar contratos, mercado ou provas criptográficas.
- Evidências: 3 testes focados de detalhe/card aprovados; `manage.py check`; QA visual no mercado local selado; `git diff --check`.
- Iniciado em: 2026-09-06
- Atualizado em: 2026-09-06
- Encerrado em: 2026-09-06

## WFLOW-20260906-INTEGRITY-MOBILE-HIERARCHY-013

- Tipo: `change-feature` + `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`, `FEAT-MOBILE-001`
- Objetivo: renomear e reposicionar a secao de integridade do detalhe mobile para reduzir confusao e preservar a hierarquia da acao principal.
- Etapa atual: copy `Integridade do mercado`, mensagens contextuais, nova ordem, specs, testes e QA visual concluidos.
- Artefatos afetados: detalhe Flutter, teste de widget, specs mobile, README, changelog e estado operacional.
- Impacto arquitetural: nenhum; somente hierarquia e copy sobre os contratos existentes da FastAPI.
- Reversao logica: restaurar o titulo dinamico e a posicao anterior sem alterar contratos ou provas.
- Evidencias: `flutter analyze`; suite Flutter; QA visual no iPhone 17 Simulator; `git diff --check`.
- Iniciado em: 2026-09-06
- Atualizado em: 2026-09-06
- Encerrado em: 2026-09-06

## WFLOW-20260906-INTEGRITY-MOBILE-SEAL-012

- Tipo: `change-feature` + `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`, `FEAT-MOBILE-001`
- Objetivo: simplificar o selo de integridade dos cards mobile para um escudo circular sobre a imagem, em paridade com o site e sem texto redundante.
- Etapa atual: cards hero/compacto, acessibilidade, specs, testes e validacao visual no iPhone 17 Simulator concluidos.
- Artefatos afetados: Flutter de cards, testes mobile, specs de UX/aceite, README, changelog e estado operacional.
- Impacto arquitetural: nenhum; somente apresentacao do resumo de integridade ja retornado pela FastAPI.
- Reversao logica: restaurar o pill/rotulo textual no card sem alterar contratos ou dados de integridade.
- Evidencias: `flutter analyze`; 12 testes focados de cards; QA visual no iPhone 17 Simulator; `git diff --check`.
- Iniciado em: 2026-09-06
- Atualizado em: 2026-09-06
- Encerrado em: 2026-09-06

## WFLOW-20260906-INTEGRITY-MOBILE-RECEIPTS-011

- Tipo: `change-feature` + `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`, `FEAT-MOBILE-001`
- Objetivo: dar paridade ao mobile com o web para listar e abrir o comprovante assinado de cada previsao inicial, reforco e revisao.
- Etapa atual: lista persistente, acesso imediato apos mutacao, modal leigo/tecnico, estados de loading/erro/retry, specs e testes concluidos; validacao visual realizada no iPhone 17 Simulator com tres recibos reais do banco local.
- Artefatos afetados: Flutter de previsao/detalhe, testes mobile, specs de UX/MVP/contrato/aceite, README e estado operacional.
- Impacto arquitetural: nenhuma nova fronteira; Flutter usa `viewer_position.history` apenas para descoberta e carrega cada recibo autoritativo da FastAPI, sem recalcular hash ou assinatura.
- Reversao logica: remover bloco/modal mobile e restaurar a confirmacao simples por hash, sem alterar previsoes, compromissos ou contratos persistidos.
- Evidencias: `flutter analyze`; 98 testes Flutter; QA visual da lista com previsao inicial, reforco e revisao e do modal de reforco no iPhone 17 Simulator; `git diff --check`.
- Iniciado em: 2026-09-06
- Atualizado em: 2026-09-06
- Encerrado em: 2026-09-06

## WFLOW-20260906-INTEGRITY-ADMIN-AUDIT-010

- Tipo: `change-feature` + `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`
- Objetivo: disponibilizar auditoria administrativa de integridade em todos os estados e identificar precisamente cada controle aprovado, divergente ou ainda nao aplicavel.
- Etapa atual: specs, contrato, FastAPI, Admin Ops e testes concluidos; 17 testes focados e 232 testes integrados aprovados, com validacao visual desktop/mobile.
- Artefatos afetados: feature, contrato de verificacao, arquitetura Admin Ops, FastAPI, Django Admin Ops, testes e estado operacional.
- Impacto arquitetural: nenhuma nova fronteira; Django apresenta o resultado read-only calculado pela FastAPI.
- Reversao logica: remover os novos acessos e restaurar `prediction_commitments_valid=null` antes do Seal, sem alterar provas persistidas.
- Iniciado em: 2026-09-06
- Atualizado em: 2026-09-06

## WFLOW-20260906-INTEGRITY-EARLY-AUDIT-009

- Tipo: `change-feature` + `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`
- Objetivo: executar a auditoria de integridade no inicio de todo ciclo, cobrindo qualquer estado e sem dependencia de selagem.
- Etapa atual: comportamento normativo, ordem do daemon e regressao automatizada concluidos; 15 testes de integridade e 230 testes integrados aprovados.
- Artefatos afetados: feature, contrato, arquitetura do scheduler, daemon, testes e estado operacional.
- Impacto arquitetural: nenhuma nova fronteira; o daemon continua chamando o verificador autoritativo da FastAPI em modo interno e somente leitura.
- Reversao logica: restaurar a ordem anterior do ciclo sem alterar alertas ou provas persistidas.
- Iniciado em: 2026-09-06
- Atualizado em: 2026-09-06

## WFLOW-20260906-INTEGRITY-AUDIT-UX-008

- Tipo: `change-feature` + `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`, `FEAT-MARKET-001`
- Objetivo: manter comprovantes visiveis apos fechamento, alinhar CTA/compartilhamento dos cards e criar auditoria recorrente de integridade com alerta `high` na fila operacional.
- Etapa atual: comprovantes persistentes, controles dos cards, auditoria compartilhada, migration e fila operacional implementados e validados.
- Artefatos afetados: feature/contrato/arquitetura/testes, PostgreSQL/migration, verificador FastAPI, daemon, fila Admin Ops, templates/CSS web, OpenAPI e estado operacional.
- Impacto arquitetural: FastAPI preserva a verificacao autoritativa; daemon apenas agenda a auditoria; PostgreSQL persiste alertas operacionais separados do ledger append-only; Django apenas apresenta e revisa.
- Reversao logica: desativar a chamada de auditoria e ocultar `integrity_alert` da fila, preservando alertas e provas existentes; restaurar rotulos/controles web sem alterar dados criptograficos.
- Migration: `markets.0030_integrity_alert_queue`, aplicada localmente.
- Evidencias: 229 testes de integridade/web aprovados; QA visual dos cards e da fila/detalhe de alerta; auditoria local de 9 mercados com materializacao dos cenarios de falha conhecidos; `manage.py check`; `makemigrations --check --dry-run`; OpenAPI export/check; compilacao Python; `node --check`; `git diff --check`.
- Encerrado em: 2026-09-06
- Iniciado em: 2026-09-06
- Atualizado em: 2026-09-06

## WFLOW-20260906-PREDICTION-RECEIPT-MODAL-007

- Tipo: `change-feature` + `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`
- Objetivo: abrir comprovantes de previsao em modal alinhado ao design system e manter acesso individual a entrada inicial, reforcos e revisoes.
- Etapa atual: modal responsivo, fallback de pagina completa e lista por acao implementados e validados.
- Artefatos afetados: feature/arquitetura web, templates e JavaScript/CSS Django, testes e estado operacional.
- Impacto arquitetural: somente apresentacao Django sobre recibos autenticados da FastAPI; assinatura, ownership e encadeamento continuam autoritativos no backend.
- Reversao logica: remover o acionamento modal e restaurar links de pagina completa, sem alterar ou apagar compromissos persistidos.
- Evidencias: QA visual no navegador em mercado real com modal sem overflow; confirmacao de tres recibos encadeados para previsao inicial, reforco e revisao; 215 testes de `tests.test_web_smoke`; `node --check`; `manage.py check`; `makemigrations --check --dry-run`; `git diff --check`.
- Encerrado em: 2026-09-06
- Iniciado em: 2026-09-06
- Atualizado em: 2026-09-06

## WFLOW-20260906-MARKET-INTEGRITY-UX-006

- Tipo: `change-feature` + `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`
- Objetivo: reduzir ressalvas que assustam no modal, restaurar o CTA `Ver resolução`, evidenciar o comprovante assinado apos a previsao e disponibilizar demos locais validas do caminho feliz.
- Etapa atual: copy, CTA, comprovante persistente/imediato, contrato de erros/avisos, paridade mobile e dados locais validados.
- Artefatos afetados: feature de integridade, templates/CSS Django, testes web, changelogs, estado operacional e dados locais de demonstracao.
- Impacto arquitetural: apresentacao Django consumindo o recibo autoritativo ja retornado pela FastAPI; sem mudanca de contrato ou persistencia produtiva.
- Reversao logica: restaurar copy/CTA anteriores e remover apenas os novos mercados locais de demonstracao se explicitamente desejado; nenhuma prova existente sera reescrita.
- Demos locais: `demo-integridade-valida-definicao`, `demo-integridade-valida-resultado` e `demo-integridade-valida-finalizado`; todas retornam `valid=true`, `errors=[]` e verificacoes especificas aplicaveis aprovadas.
- Evidencias: 214 testes de `tests.test_web_smoke`; 15 testes focados de ledger/web; 96 testes Flutter; `flutter analyze`; `manage.py check`; `makemigrations --check --dry-run`; OpenAPI export/check; `git diff --check`; QA visual no modal registrado e selado e no CTA do card.
- Encerrado em: 2026-09-06
- Iniciado em: 2026-09-06
- Atualizado em: 2026-09-06

## WFLOW-20260906-MARKET-INTEGRITY-SEMANTICS-005

- Tipo: `change-feature` + `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`
- Objetivo: eliminar ambiguidades entre processo ativo, retry operacional, etapa nao aplicavel e diferenca criptografica, reforcando a verificacao contra o estado operacional atual.
- Etapa atual: implementacao, migracao, contratos, consumidores e regressao concluidos; ambientes FastAPI/Django reiniciados e demos abertas, pendente e selada conferidas visualmente.
- Artefatos afetados: feature/contrato de integridade, FastAPI, OpenAPI, Django publico/Admin Ops, Flutter e testes.
- Impacto arquitetural: mantem FastAPI como autoridade; amplia verificacao v1 com campos aditivos e adiciona registro append-only apenas de chaves publicas historicas.
- Migration: `markets.0029_integrity_signing_keys` aplicada localmente.
- Evidencias: `manage.py test --keepdb` com 224 testes; `flutter test` com 96 testes; `flutter analyze`; `makemigrations --check --dry-run`; OpenAPI export/check; `git diff --check`; verificacao visual local dos estados `registered`, `resolved_pending_seal` e `sealed` em modal.
- Encerrado em: 2026-09-06
- Reversao logica: clientes antigos ignoram campos aditivos; restaurar os mapeamentos anteriores nao altera provas persistidas.
- Iniciado em: 2026-09-06
- Atualizado em: 2026-09-06

## WFLOW-20260906-MARKET-INTEGRITY-COPY-004

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`
- Objetivo: explicar de forma compacta hash, assinatura, encadeamento e deteccao de manipulacao, removendo o botao redundante do detalhe do mercado.
- Etapa atual: concluido; metodo criptografico compacto e acionador unico no escudo validados em desktop e mobile em 2026-09-06.
- Artefatos afetados: spec de integridade, arquitetura web, partial de verificacao, detalhe do mercado, CSS e testes de renderizacao.
- Impacto arquitetural: apenas apresentacao Django; contratos, regras de verificacao e persistencia nao mudam.
- Evidencias: `manage.py check`, 3 testes focados, suite `tests.test_web_smoke` com 212 testes e inspecao visual em desktop e 390 px, todos aprovados; console sem erros.
- Encerrado em: 2026-09-06
- Reversao logica: restaurar a copy anterior e o acionador textual do detalhe sem alterar provas ou dados.
- Iniciado em: 2026-09-06
- Atualizado em: 2026-09-06

## WFLOW-20260906-MARKET-INTEGRITY-COPY-003

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`
- Objetivo: tornar a verificacao publica compreensivel para publico leigo, priorizando proposito, resposta objetiva, linha do tempo, efeito de alteracoes e limites antes dos detalhes tecnicos.
- Etapa atual: concluido; hierarquia de linguagem simples, linha do tempo, limites, detalhes tecnicos progressivos e estados honestos validados em desktop e mobile em 2026-09-06.
- Artefatos afetados: spec de integridade, arquitetura web, partial Django, CSS e testes de renderizacao.
- Impacto arquitetural: somente apresentacao Django de dados retornados pela FastAPI; nenhuma regra de validade muda de camada.
- Evidencias: `manage.py check`, 2 testes focados de renderizacao, suite `tests.test_web_smoke` com 212 testes e inspecao visual em viewport desktop e 390 px, todos aprovados.
- Encerrado em: 2026-09-06
- Reversao logica: restaurar a estrutura anterior do partial sem alterar provas, contratos ou persistencia.
- Iniciado em: 2026-09-06
- Atualizado em: 2026-09-06

## WFLOW-20260905-MARKET-INTEGRITY-UX-002

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`
- Objetivo: refinar a sinalizacao de integridade nos cards e no detalhe web, preservar thumbnails e apresentar a verificacao em modal acessivel com linguagem para publico leigo.
- Etapa atual: implementacao concluida e validada localmente em desktop e viewport mobile.
- Artefatos afetados: `docs/specs/`, templates Django, CSS/JavaScript web e testes de regressao.
- Impacto arquitetural: apenas apresentacao Django; FastAPI, OpenAPI, persistencia, daemon e Flutter permanecem inalterados.
- Reversao logica: restaurar os links de pagina inteira e o badge textual anterior, sem alterar provas ou dados de integridade.
- Iniciado em: 2026-09-05
- Atualizado em: 2026-09-05
- Encerrado em: 2026-09-05
- Evidencias: `manage.py check`; quatro testes focados de selo/modal/fallback/download; `manage.py test tests.test_web_smoke --keepdb` com 211 testes; `node --check`; download JSON via rota Django com HTTP 200; QA visual no feed, detalhe e modal em desktop/mobile, sem overflow horizontal ou erros no console.

## WFLOW-20260905-MARKET-INTEGRITY-001

- Tipo: `new-feature` + `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-INTEGRITY-001`
- Objetivo: implementar ledger criptografico interno assinado cobrindo publicacao, previsoes, resolucao, selagem, verificacao, Admin Ops, web, mobile, comunicacoes e paginas institucionais.
- Etapa atual: implementação local concluída e validada; aguardando rollout controlado com IAM/KMS, secrets e migrations de produção.
- Artefatos afetados: `docs/specs/`, `apps/api/backend_api/`, `apps/web/django/`, `apps/web/templates/`, `apps/web/static/`, `apps/mobile/`, `packages/contracts/openapi/`, `requirements.txt`, migrations e testes.
- Decisoes: assinatura sincrona/atomica; KMS Ed25519 em producao; chave efemera apenas em desenvolvimento/testes; HMAC-SHA-256 para pseudonimo; Merkle deterministica; ledger global sob lock; legado sem assinatura retroativa.
- Bloqueios: configuracao IAM/KMS e segredo de commitment sao requisitos de deploy, nao bloqueiam implementacao/testes locais.
- Iniciado em: 2026-09-05
- Atualizado em: 2026-09-05
- Encerrado em: 2026-09-05
- Retomada: executar o runbook `docs/specs/operations/market-integrity-deploy.md` em staging, provisionar a chave KMS Ed25519 e validar o smoke concorrente antes de produção. Mercados legados permanecem `legacy_unregistered` e não devem ser apresentados como prova original.
- Reversao logica: desabilitar novas mutacoes dependentes do signer, preservar integralmente provas ja emitidas e manter mercados `resolved` para retry; nunca apagar o ledger.
- Evidências de validação local: `.venv/bin/python manage.py check`; `.venv/bin/python manage.py makemigrations --check --dry-run`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `.venv/bin/python manage.py test` com 217 testes; `cd apps/mobile && flutter analyze`; `cd apps/mobile && flutter test` com 95 testes; teste dedicado cobre dois workers concorrentes, idempotência, falha/retry de assinatura, prova Merkle, verificação pública e trigger append-only.
- Limitações conhecidas: integração real com AWS KMS, políticas IAM e alarmes CloudWatch exigem validação de staging; não há ancoragem Polygon; mercados legados não recebem assinatura retroativa; o pacote público v1 é JSON servido pela API, sem formato ZIP independente.

## WFLOW-20260829-MARKET-CARD-LAYOUT-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`
- Objetivo: compactar os cards web do feed, removendo metadados secundários e reposicionando as tags de classificação para aproveitar o espaço abaixo da miniatura, sem alterar domínio, contratos ou app mobile.
- Etapa atual: implementado, publicado na PR #112, mesclado em `main` e implantado em produção com smoke externo aprovado.
- Artefatos afetados:
  - `apps/web/templates/components/market_card.html`
  - `apps/web/static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/architecture/frontend-web.md`
  - `docs/specs/features/market-feed.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/change-log-specs.md`
  - `docs/specs/state/workflow-runs.md`
- Impacto arquitetural: somente apresentação Django; FastAPI, OpenAPI, banco e Flutter permanecem inalterados.
- Testes esperados: renderização do card preserva tags e prazo relativo, omite metadados secundários e `Crédito distribuído` em cards resolvidos, exibe `Consenso final` como contexto do gráfico/opções e mantém título/CTAs/favoritos/curtidas/comentários funcionais.
- Bloqueios: nenhum.
- Iniciado em: 2026-08-29
- Atualizado em: 2026-08-29
- Evidências finais: PR #112 mesclada por squash no commit `458b127`; workflow `GoTrendLabs CI and Deploy` #33257650695 aprovado (detecção, suíte completa e deploy); `https://gotrendlabs.com.br/` e `/api/health` responderam HTTP 200, com API e banco `ok`. O HTML público apresentou `Consenso final` e as novas faixas de tags, sem os metadados removidos.
- Retomada: encerrado; para reversão, aplicar a reversão lógica abaixo em uma nova mudança.
- Reversão lógica: restaurar os quatro metadados no componente do card e reverter a regra visual da faixa de tags, sem migração, mudança de contrato ou efeito no mobile.

## WFLOW-20260620-MOBILE-GOOGLE-PLAY-CLOSED-TESTING-002

- Tipo: `release-prep`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`
- Objetivo: preparar nova rodada de Android App Bundle assinado para Google Play Closed testing, com versao `1.0.10+11`, release name e release notes `pt-BR` prontos para Play Console, sem alterar comportamento funcional do app.
- Etapa atual: `versionCode 10` foi recusado pelo Play Console por já ter sido usado; AAB assinado `1.0.10+11` gerado localmente e pronto para upload manual no track Closed testing do Play Console.
- Artefatos afetados:
  - `apps/mobile/pubspec.yaml`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/workflow-runs.md`
- Release name Play Console: `1.0.10+11 - Closed testing Android`.
- Release notes Play Console:

```text
<pt-BR>
Nova versão para teste fechado do GoTrendLabs no Android, mantendo o app conectado à produção e preservando o canal beta direto do site. Esta rodada atualiza o bundle da Google Play para validação interna, sem alterar as regras de negócio nem o canal APK público atual.
</pt-BR>
```

- Bloqueios: nenhum conhecido.
- Iniciado em: 2026-06-20
- Atualizado em: 2026-06-20
- Encerrado em: 2026-06-20
- Retomada: subir `apps/mobile/build/app/outputs/bundle/release/app-release.aab` no track Closed testing do Play Console; o canal direto do site permanece com o APK ativo `1.0.7 (8)` ate uma publicacao propria.
- Reversao logica: voltar `apps/mobile/pubspec.yaml` para `1.0.8+9` e remover esta documentacao da segunda rodada de Google Play Closed testing se a operacao adiar o novo bundle.
- Evidencias de validacao local: `cd apps/mobile && flutter pub get`; `cd apps/mobile && flutter analyze` sem issues; `cd apps/mobile && flutter test` com 94 testes OK; `cd apps/mobile && flutter build appbundle --release --dart-define=GTL_API_BASE_URL=https://gotrendlabs.com.br/api --dart-define=GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br` gerou o bundle release; `jarsigner -verify -verbose -certs build/app/outputs/bundle/release/app-release.aab` retornou `jar verified` com certificado upload self-signed `CN=GoTrendLabs, OU=Mobile, O=GoTrendLabs, L=Sao Paulo, ST=SP, C=BR`.
- Evidencias do AAB: `apps/mobile/build/app/outputs/bundle/release/app-release.aab`; tamanho `57383320` bytes; SHA-256 `6592ccd9e65d323127bbbf2050866f58f050d85bbe9303280182237570e0d476`.

## WFLOW-20260620-MOBILE-COMPATIBILITY-POLICY-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `backend-api`, `Admin Ops`
- Objetivo: implementar política de compatibilidade mobile controlada pela API atual, sem versionamento de rotas, usando Android build/versionCode como autoridade.
- Etapa atual: PR #109 publicada e mergeada em `main`; deploy de produção concluído pelo GitHub Actions e smoke público validado.
- Artefatos afetados:
  - `apps/api/backend_api/`
  - `apps/web/django/admin_ops/`
  - `apps/mobile/`
  - `packages/contracts/openapi/gotrendlabs-api.json`
  - `docs/specs/`
  - `tools/skills/gotrendlabs/`
- Bloqueios: nenhum conhecido.
- Iniciado em: 2026-06-20
- Atualizado em: 2026-06-20
- Encerrado em: 2026-06-20.
- Retomada: para forçar atualização em produção, primeiro publicar/ativar uma release Android compatível em `MobileAppRelease` com `version_code` igual ou maior que o build mínimo desejado; depois ajustar `min_supported_android_build` no Admin Ops. Para updates opcionais, usar `recommended_android_build`. Em 2026-06-20, o canal direto do site permaneceu em `1.0.7 (8)` enquanto o Closed testing Google Play já tinha AABs preparados como `1.0.8+9` e `1.0.10+11`; por isso a política de produção ficou com mínimo `0` e nenhum bloqueio obrigatório foi ativado.
- Reversão lógica: zerar `min_supported_android_build`/`recommended_android_build`, ocultar a seção de compatibilidade no Admin Ops, remover o middleware `426`, manter `GET /health` compatível ou restaurar o snapshot OpenAPI anterior conforme necessidade.
- Evidências de validação local: `.venv/bin/python -m py_compile apps/api/backend_api/main.py apps/api/backend_api/schemas.py apps/web/django/admin_ops/models.py apps/web/django/admin_ops/forms.py apps/web/django/admin_ops/views.py`; `.venv/bin/python manage.py makemigrations --check --dry-run`; `.venv/bin/python manage.py check`; `.venv/bin/python manage.py test tests.test_web_smoke.MobileMaintenanceGateTests --keepdb`; `.venv/bin/python manage.py test tests.test_web_smoke.WebSmokeTests.test_admin_config_mobile_compatibility_requires_superuser_and_audits_change tests.test_web_smoke.WebSmokeTests.test_admin_config_rejects_mobile_compatibility_above_active_release --keepdb`; `.venv/bin/python manage.py test tests.test_web_smoke --keepdb` com 207 testes OK; após revisão final, `.venv/bin/python manage.py test tests.test_web_smoke.WebSmokeTests.test_admin_config_rejects_mobile_compatibility_above_active_release --keepdb`; `.venv/bin/python manage.py test tests.test_web_smoke.MobileMaintenanceGateTests --keepdb`; `cd apps/mobile && flutter test test/api_client_test.dart test/maintenance_gate_test.dart test/market_detail_screen_test.dart`; `cd apps/mobile && flutter analyze`; `.venv/bin/python manage.py makemigrations --check --dry-run`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `git diff --check` sem problemas.
- Evidências de publicação: PR #109 (`Adiciona política de compatibilidade mobile por build`) mergeada em `main` por squash commit `6982a764a2f17a4670acad91f5306e514e82feb6`; GitHub Actions `GoTrendLabs CI and Deploy` run `27882938261` concluiu `detect-changes`, `test` e `deploy` com sucesso.
- Evidências de produção: `https://gotrendlabs.com.br/api/health` respondeu `HTTP 200`, `status=ok`, `maintenance.web_enabled=false`, `maintenance.mobile_enabled=false`, `checks.api=ok`, `checks.database=ok` e bloco `mobile` com `min_supported_android_build=0`, `latest_android_build=8`, `latest_android_version=1.0.7`, `update_required=false`, `update_available=false` e mensagem padrão segura; a mesma rota com headers `X-GoTrendLabs-Client: mobile`, `X-GoTrendLabs-App-Version: 1.0.8`, `X-GoTrendLabs-App-Build: 9` retornou `current_app_build=9` sem bloqueio; `/api/health` com build `8` continuou acessível; `/api/markets` com build `8` retornou `HTTP 200` porque o mínimo produtivo segue `0`; `/app/android/latest.json` confirmou a release direta ativa `1.0.7 (8)` com SHA-256 `54822fc7aa84ebad2e923c0af75076ba43f7d73433c918f1a365bcd2d4ffe5ae`.

## WFLOW-20260618-MOBILE-GOOGLE-PLAY-CLOSED-TESTING-001

- Tipo: `release-prep`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`
- Objetivo: preparar o primeiro Android App Bundle assinado para Google Play Closed testing, com versao `1.0.8+9`, release name e release notes `pt-BR` prontos para Play Console.
- Etapa atual: AAB assinado `1.0.8+9` gerado localmente e pronto para upload manual no track Closed testing do Play Console.
- Artefatos afetados:
  - `apps/mobile/pubspec.yaml`
  - `apps/mobile/README.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
  - `ops/deploy/production/README.md`
- Release name Play Console: `1.0.8+9 - Closed testing Android`.
- Release notes Play Console:

```text
<pt-BR>
Primeira versão de teste fechado do app GoTrendLabs no Google Play. Inclui feed e detalhe de mercados, previsões com GT₵ educativo, carteira, ranking, alertas, perfil, suporte, proteção local da sessão, manutenção mobile e push Android via FCM quando autorizado.
</pt-BR>
```

- Bloqueios: nenhum conhecido.
- Iniciado em: 2026-06-18
- Atualizado em: 2026-06-20
- Encerrado em: 2026-06-20
- Retomada: subir `apps/mobile/build/app/outputs/bundle/release/app-release.aab` no track Closed testing do Play Console; o canal direto do site permanece com o APK ativo `1.0.7 (8)` ate uma publicacao propria.
- Reversao logica: voltar `apps/mobile/pubspec.yaml` para `1.0.7+8` e remover a documentacao de Google Play Closed testing se a operacao adiar o canal Play.
- Evidencias de validacao local: `cd apps/mobile && flutter pub get`; `cd apps/mobile && flutter analyze` sem issues; `cd apps/mobile && flutter test` com 87 testes OK; `cd apps/mobile && flutter build appbundle --release --dart-define=GTL_API_BASE_URL=https://gotrendlabs.com.br/api --dart-define=GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br` gerou o bundle release; `jarsigner -verify -verbose -certs build/app/outputs/bundle/release/app-release.aab` retornou `jar verified` com certificado upload self-signed `CN=GoTrendLabs, OU=Mobile, O=GoTrendLabs, L=Sao Paulo, ST=SP, C=BR`; `git diff --check` sem problemas; `.venv/bin/python manage.py check` sem issues.
- Evidencias do AAB: `apps/mobile/build/app/outputs/bundle/release/app-release.aab`; tamanho `57316771` bytes; SHA-256 `8871e060f9e49833ab459e42e00f98b6ffd832a73720fa6103c4c8ed6a436bf2`.

## WFLOW-20260618-MOBILE-PERFORMANCE-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `FEAT-REP-001`
- Objetivo: criar a tela mobile autenticada `Desempenho` com placar, historico auditavel de resolucoes e progressao, usando contrato agregado da FastAPI e dados quentes.
- Etapa atual: implementacao local concluida em branch `feature/mobile-user-performance`, com `origin/main` atualizado antes da branch.
- Artefatos afetados:
  - `apps/api/backend_api/main.py`
  - `apps/api/backend_api/schemas.py`
  - `apps/mobile/lib/src/features/performance/`
  - `apps/mobile/lib/src/features/live_refresh.dart`
  - `apps/mobile/lib/src/features/shell/shell_screen.dart`
  - `apps/mobile/lib/src/features/profile/profile_screen.dart`
  - `tests/test_web_smoke.py`
  - `apps/mobile/test/`
  - `packages/contracts/openapi/gotrendlabs-api.json`
  - `docs/specs/`
- Bloqueios: nenhum conhecido.
- Iniciado em: 2026-06-18
- Atualizado em: 2026-06-18
- Reversao logica: remover `GET /users/me/performance`, retirar a tela `Desempenho` do app/menu/perfil/live refresh e voltar a usar apenas Perfil/Ranking/Badges como superficies de reputacao.
- Evidencias de validacao local: `.venv/bin/python -m py_compile apps/api/backend_api/main.py apps/api/backend_api/schemas.py`; `.venv/bin/python manage.py check`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `.venv/bin/python manage.py test tests.test_web_smoke.BackendAuthAPITests.test_admin_resolve_market_applies_payout_loss_and_reputation_formula --keepdb`; `.venv/bin/python manage.py test tests.test_web_smoke --keepdb` com 201 testes OK; `cd apps/mobile && flutter test test/performance_screen_test.dart test/shell_screen_test.dart test/push_placement_test.dart`; `cd apps/mobile && flutter analyze`; `cd apps/mobile && flutter test` com 87 testes OK; apos ajuste final de copy, `.venv/bin/python -m py_compile apps/api/backend_api/main.py`; `.venv/bin/python manage.py test tests.test_web_smoke.BackendAuthAPITests.test_admin_resolve_market_applies_payout_loss_and_reputation_formula --keepdb`; `cd apps/mobile && flutter test test/performance_screen_test.dart`; `cd apps/mobile && flutter analyze`; `git diff --check`; APK debug instalado no Galaxy S20 `SM G980F` com API/web locais via `adb reverse` para `127.0.0.1:8001` e `127.0.0.1:8000`.

## WFLOW-20260618-MOBILE-PROFILE-DATE-DESK-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`
- Objetivo: melhorar a digitação de data de nascimento no perfil mobile e corrigir os contadores/recorte da mesa autenticada para considerar somente posições ativas.
- Etapa atual: concluído; PR #104 mergeada em `main`, deploy de produção concluído pelo workflow `GoTrendLabs CI and Deploy` run `27792783182` e smokes públicos validados.
- Artefatos afetados:
  - `apps/mobile/lib/src/features/profile/profile_screen.dart`
  - `apps/mobile/lib/src/features/markets/market_models.dart`
  - `apps/mobile/lib/src/features/markets/markets_screen.dart`
  - `apps/mobile/test/push_placement_test.dart`
  - `apps/mobile/test/markets_screen_test.dart`
  - `docs/specs/features/mobile-ux.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
- Bloqueios: nenhum conhecido.
- Iniciado em: 2026-06-18
- Atualizado em: 2026-06-18
- Encerrado em: 2026-06-18
- Retomada: se a operação decidir disponibilizar a correção para todos os usuários do canal direto Android, gerar nova APK release assinada em follow-up próprio; este fechamento atualizou `main`/produção backend-site e manteve o APK público em `1.0.7 (8)`, enquanto o APK debug com a feature foi instalado no Galaxy S20 para QA físico.
- Reversão lógica: remover o formatter local de data, voltar o campo a aceitar apenas a digitação anterior e restaurar `Sua mesa`/`Posições` para o comportamento anterior baseado em `viewer_has_prediction`.
- Evidências de validação local: `cd apps/mobile && flutter test test/push_placement_test.dart`; `cd apps/mobile && flutter test test/markets_screen_test.dart`; `cd apps/mobile && flutter analyze`; `cd apps/mobile && flutter test`; `git diff --check`; APK debug instalado no Galaxy S20 `SM G980F` apontando para `https://gotrendlabs.com.br/api`, versão `1.0.7 (8)`.
- Evidências de publicação: PR #104 (`Ajusta data do perfil e mesa mobile`) mergeada por squash `266a663`; workflow `GoTrendLabs CI and Deploy` run `27792783182` concluiu `test` em 4m20s e `deploy` em 50s.
- Evidências de produção: `/api/health` respondeu `status=ok`, `maintenance.web_enabled=false`, `maintenance.mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; homepage retornou `HTTP 200`; `/api/openapi.json` retornou `HTTP 200`; `/app/android/latest.json` permaneceu em `version_name=1.0.7`, `version_code=8` e SHA-256 `54822fc7aa84ebad2e923c0af75076ba43f7d73433c918f1a365bcd2d4ffe5ae`, confirmando que o canal APK público não foi alterado por esta publicação.

## WFLOW-20260618-MOBILE-PROFILE-CONTRIBUTION-WALLET-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `FEAT-AUTH-001`, `FEAT-WALLET-001`, `FEAT-SUGGEST-001`
- Objetivo: limpar UX mobile de contribuição/wallet, expor dados privados de perfil para conferência/edição, permitir correção de email em login limitado e preservar FastAPI como autoridade de domínio.
- Etapa atual: concluído; PR #102 mergeada em `main`, deploy de produção concluído pelo workflow `GoTrendLabs CI and Deploy` run `27759222223` e smokes públicos validados.
- Artefatos afetados:
  - `apps/api/backend_api/main.py`
  - `apps/mobile/lib/src/features/auth/auth_controller.dart`
  - `apps/mobile/lib/src/features/profile/profile_screen.dart`
  - `apps/mobile/lib/src/features/support/contribution_sheets.dart`
  - `apps/mobile/lib/src/features/wallet/wallet_screen.dart`
  - `apps/mobile/test/`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/auth-and-session.md`
  - `docs/specs/features/mobile-ux.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/`
- Bloqueios: nenhum conhecido.
- Iniciado em: 2026-06-18
- Atualizado em: 2026-06-18
- Encerrado em: 2026-06-18
- Retomada: acompanhar feedback físico do app; para ativar a UX mobile em APK público do canal direto, gerar nova release Android assinada em follow-up próprio, pois esta publicação atualizou backend/site e manteve o APK ativo em `1.0.7 (8)`.
- Reversão lógica: restaurar a posição anterior do desafio anti-abuso nas folhas mobile, remover o painel privado/edit sheet do perfil mobile, voltar `/users/me` a exigir email confirmado para qualquer patch e recolocar a copy/quadros técnicos da recarga apenas se a operação decidir expô-los novamente.
- Evidências de validação local: `.venv/bin/python -m py_compile apps/api/backend_api/main.py apps/api/backend_api/schemas.py`; `.venv/bin/python manage.py check`; `.venv/bin/python manage.py test tests.test_web_smoke.BackendAuthAPITests.test_email_confirmation_outbox_blocks_sensitive_actions_until_confirmed tests.test_web_smoke.BackendAuthAPITests.test_unconfirmed_user_can_update_email_and_get_new_confirmation tests.test_web_smoke.BackendAuthAPITests.test_register_requires_terms_profile_update_and_logical_deletion --keepdb`; `cd apps/mobile && flutter test test/push_placement_test.dart`; `cd apps/mobile && flutter test`; `cd apps/mobile && flutter analyze`; `git diff --check`; APK debug instalado no Galaxy S20 `SM G980F` apontando para `https://gotrendlabs.com.br/api`.
- Evidências de publicação: PR #102 (`Ajusta perfil e contribuições no mobile`) mergeada por squash `ace00832`; workflow `GoTrendLabs CI and Deploy` run `27759222223` concluiu `test` em 4m17s e `deploy` em 55s.
- Evidências de produção: `/api/health` respondeu `status=ok`, `maintenance.web_enabled=false`, `maintenance.mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; homepage retornou `HTTP 200`; `/api/openapi.json` expôs `PATCH /users/me` com resposta `UserProfileResponse`; `/app/android/latest.json` permaneceu em `version_name=1.0.7`, `version_code=8`, confirmando que o canal APK público não foi alterado por esta publicação backend/site.

## WFLOW-20260618-MARKET-PROBABILITY-SOURCE-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FastAPI public contract`, `Admin Ops`
- Objetivo: remover as colunas duplicadas `primary_probability_exact` e `secondary_probability_exact` de `gotrendlabs_markets`, mantendo `gotrendlabs_market_options.probability_exact` como fonte unica de probabilidade e derivando os atalhos publicos de mercado das opcoes.
- Etapa atual: publicado em `main` pela PR #100; deploy de producao concluido pelo workflow `GoTrendLabs CI and Deploy` run `27730715944` e smokes publicos/schema validados.
- Artefatos afetados:
  - `apps/web/django/markets/models.py`
  - `apps/web/django/markets/migrations/0026_remove_market_primary_probability_exact_and_more.py`
  - `apps/api/backend_api/main.py`
  - `apps/api/backend_api/agent_services.py`
  - `apps/api/backend_api/schemas.py`
  - `apps/web/django/core/domain_client.py`
  - `apps/web/django/admin_ops/`
  - `ops/scripts/`
  - `data/fixtures/domain.json`
  - `packages/contracts/openapi/gotrendlabs-api.json`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum conhecido.
- Iniciado em: 2026-06-18
- Atualizado em: 2026-06-18
- Encerrado em: 2026-06-18
- Evidencias de validacao local: `.venv/bin/python -m py_compile apps/api/backend_api/main.py apps/api/backend_api/agent_services.py apps/api/backend_api/schemas.py apps/web/django/core/domain_client.py apps/web/django/admin_ops/forms.py apps/web/django/admin_ops/views.py`; `.venv/bin/python manage.py check`; `.venv/bin/python manage.py makemigrations --check --dry-run`; `.venv/bin/python manage.py migrate`; introspeccao local confirmou ausencia de `primary_probability_exact` e `secondary_probability_exact` em `gotrendlabs_markets`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `.venv/bin/python manage.py test tests.test_web_smoke --keepdb` com 200 testes OK; `GET /markets` local retornou atalhos publicos de consenso derivados da opcao lider por `options[].probability_exact`; `git diff --check`.
- Evidencias de publicacao: PR #100 (`Remove duplicidade de probabilidades de mercado`) mergeada por squash `a63baa8`; workflow `GoTrendLabs CI and Deploy` run `27730715944` concluiu `test` e `deploy` com sucesso.
- Evidencias de producao: `/api/health` respondeu `status=ok`, `checks.api=ok` e `checks.database=ok`; homepage retornou `HTTP 200`; `/api/openapi.json` manteve `primary_probability_exact`/`secondary_probability_exact` em `MarketResponse` e removeu esses campos de `AdminMarketPayload`; `/api/markets` retornou 19 mercados, 2 de multipla escolha e nenhuma divergencia entre `primary_outcome`/`primary_probability_exact` e a opcao lider por `options[].probability_exact`; SSM read-only `b30ad49e-b606-426c-8a13-e52a6f460210` confirmou ausencia de `primary_probability_exact` e `secondary_probability_exact` em `gotrendlabs_markets`.
- Reversao logica: recriar as colunas removidas apenas se um cache materializado de consenso voltar a ser necessario, garantindo entao rotina atomica de sincronizacao com `gotrendlabs_market_options.probability_exact`.

## WFLOW-20260617-BADGE-REQUIREMENT-GRANTS-HOTFIX-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-REP-001`, `Admin Ops`
- Objetivo: corrigir permissão runtime da FastAPI na tabela `gotrendlabs_badge_rule_requirements`, após o detalhe administrativo de usuário retornar erro interno ao avaliar badges durante `_ensure_user_core`.
- Etapa atual: concluído; produção restaurada com grant operacional, hotfix versionado pela PR #98 e deploy concluído pelo workflow `GoTrendLabs CI and Deploy` run `27727206127`.
- Artefatos afetados:
  - `apps/web/django/accounts/migrations/0021_grant_badge_requirement_runtime_permissions.py`
  - `docs/specs/state/workflow-runs.md`
- Bloqueios: nenhum conhecido.
- Iniciado em: 2026-06-17
- Atualizado em: 2026-06-17
- Encerrado em: 2026-06-17
- Evidências de validação local: `.venv/bin/python manage.py check`; `.venv/bin/python manage.py makemigrations --check --dry-run`; `.venv/bin/python manage.py test --keepdb tests.test_web_smoke.BackendAuthAPITests.test_admin_user_management_contracts_audit_wallet_and_sessions`; `git diff --check`.
- Evidências de produção: logs FastAPI mostraram `psycopg.errors.InsufficientPrivilege: permission denied for table gotrendlabs_badge_rule_requirements` em `GET /admin/users/8`; SSM `5a6428bd-9e81-4048-b1ba-967977c416e1` aplicou `GRANT` para `gotrendlabs_fastapi`; SSM `01f749c3-e603-4089-a3c8-4a41ab4950cd` confirmou `_admin_user_detail(8)` retornando `@karlascardua` com badges `['founding_member']`.
- Evidências de publicação: PR #98 (`Corrige permissão runtime dos requisitos de badges`) mergeada com squash `8b9b11b`; workflow `GoTrendLabs CI and Deploy` run `27727206127` concluiu `test` em 4m16s e `deploy` em 54s; `/api/health` respondeu `status=ok`, `checks.api=ok` e `checks.database=ok`; SSM final `a6523ed0-e953-4257-8959-52a4b9998338` confirmou `_admin_user_detail(8)` retornando `@karlascardua` com badges `['founding_member']`.
- Reversão lógica: remover a migration complementar apenas se a estratégia de roles runtime for substituída por privilégios padrão gerenciados no provisionamento do banco.

## WFLOW-20260617-BADGE-RULE-REQUIREMENTS-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-REP-001`
- Objetivo: evoluir badges administráveis para requisitos adicionais configuráveis, sem lógica específica por nome/código de badge, garantindo que `Top 10` dependa de posição global 10 ou melhor e ao menos 3 previsões resolvidas.
- Etapa atual: concluído; PR #96 mergeada em `main`, deploy de produção concluído pelo workflow `GoTrendLabs CI and Deploy` run `27725980398`, e concessão indevida `top_ten` removida operacionalmente de `@karlascardua`.
- Artefatos afetados:
  - `apps/api/backend_api/badge_engine.py`
  - `apps/api/backend_api/main.py`
  - `apps/api/backend_api/schemas.py`
  - `apps/web/django/accounts/models.py`
  - `apps/web/django/accounts/migrations/0020_badge_rule_requirements.py`
  - `apps/web/django/admin_ops/`
  - `apps/web/static/js/gotrendlabs.js`
  - `docs/specs/contracts/reputation-ranking.md`
  - `docs/specs/features/reputation-and-ranking.md`
  - `packages/contracts/openapi/gotrendlabs-api.json`
  - `tests/test_web_smoke.py`
- Bloqueios: nenhum conhecido.
- Iniciado em: 2026-06-17
- Atualizado em: 2026-06-17
- Encerrado em: 2026-06-17
- Evidências de validação local: `.venv/bin/python manage.py check`; `.venv/bin/python manage.py makemigrations --check --dry-run`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `.venv/bin/python manage.py test --keepdb tests.test_web_smoke`; `git diff --check`.
- Evidências de publicação: PR #96 (`Adiciona requisitos configuráveis para badges`) mergeada com squash `92f98025`; workflow `GoTrendLabs CI and Deploy` run `27725980398` concluiu `test` em 4m25s e `deploy` em 50s.
- Evidências de produção: `/api/health` respondeu `status=ok`, `checks.api=ok` e `checks.database=ok`; `/api/badges` exibiu a descrição nova da `Top 10`; `/badges/` respondeu HTTP 200; SSM read-only `23fae723-f778-4793-b5c9-d971ad6bc2e9` confirmou uma conquista `top_ten` indevida para `@karlascardua`/`karla.flor@ne.com`; SSM corretivo `d3d615ba-cbff-4eec-9362-ffd314ca340a` removeu 1 `UserBadgeAward` `top_ten`, removeu notificações `badge_awarded:top_ten`, deixou `remaining_top_ten=0` e preservou `remaining_badges=['founding_member']`.
- Reversão lógica: remover `BadgeRuleRequirement`, retirar `requirements` do contrato administrativo de badges, voltar a `BadgeAwardEngine` a avaliar apenas a regra principal e restaurar a descrição/configuração anterior da `Top 10`.

## WFLOW-20260617-AI-COMMENT-MARKET-LIMIT-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AIAGENT-001`
- Objetivo: tornar administrável o limite total de comentários IA oficiais visíveis por mercado, adicionar override opcional por agente `analyst`, manter `ai_commenting_enabled` como kill switch e preservar cooldown/limites por dia/ciclo como proteções adicionais.
- Etapa atual: concluído; PR #93 mergeada em `main`, hotfix OpenAPI #94 mergeado, deploy de produção concluído pelo workflow `GoTrendLabs CI and Deploy` run `27690438066`, e duplicados históricos de comentários IA visíveis ocultados operacionalmente em produção.
- Artefatos afetados:
  - `apps/api/backend_api/agent_services.py`
  - `apps/api/backend_api/main.py`
  - `apps/api/backend_api/schemas.py`
  - `apps/web/django/agents/`
  - `apps/web/django/admin_ops/`
  - `docs/specs/features/official-ai-agents.md`
  - `docs/specs/state/`
  - `tests/test_web_smoke.py`
- Bloqueios: nenhum conhecido.
- Iniciado em: 2026-06-17
- Atualizado em: 2026-06-17
- Encerrado em: 2026-06-17
- Evidências de validação local: `.venv/bin/python manage.py check` sem issues; `.venv/bin/python manage.py makemigrations --check --dry-run` sem mudanças pendentes; recorte focado de 8 testes IA/Admin Ops OK; `.venv/bin/python manage.py test tests.test_web_smoke --keepdb` com 198 testes OK; `git diff --check` limpo; migration `agents.0005_aiagent_max_comments_per_market_override` aplicada no banco local.
- Evidências de publicação: PR #93 (`Controla comentários IA por mercado no Admin Ops`) mergeada com squash `e309c6b`; PR #94 (`Atualiza snapshot OpenAPI dos agentes IA`) mergeada com squash `41e7925`; workflow `GoTrendLabs CI and Deploy` run `27690438066` concluiu `test` em 4m14s e `deploy` em 49s, com deploy SSM `9e71e997-865c-4597-b927-6282466bc928`; produção respondeu `GET /api/health` com `status=ok`.
- Evidências de produção: consulta read-only SSM `e60dff52-0fa8-4711-9b4a-87460dead67f` encontrou 10 mercados com duplicados visíveis de IA e 22 comentários extras; limpeza SSM `8825bf8e-6a6a-4782-8fe8-986212cc4159` ocultou os 22 extras preservando o comentário IA visível mais antigo por mercado; verificação SSM `69d5f9b6-a430-4aca-afc9-eea633c7f3e8` confirmou `duplicate_markets=0`, `extra_visible_comments=0`, `ai_max_comments_per_market=1`, `ai_commenting_enabled=true` e `GoTrendLabs AI Analyst` sem override.
- Reversão lógica: remover os campos `ai_max_comments_per_market` e `max_comments_per_market_override` e suas migrations, retirar o bloqueio `market_ai_comment_limit` da seleção de candidatos do agente `analyst` e restaurar a documentação para limites baseados apenas em cooldown/dia/ciclo.

## WFLOW-20260616-MOBILE-RANKING-LIVE-REFRESH-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `FEAT-REP-001`
- Objetivo: incluir Ranking no contrato mobile de refresh em tempo de consulta, reconsultando `GET /rankings` ao abrir a tela ativa, voltar do background, tocar na aba, trocar filtros e usar pull-to-refresh, sem polling continuo, sem regra local de reputacao e sem consulta antecipada/duplicada quando a tela esta apenas montada fora da aba ativa.
- Etapa atual: concluido; PR #91 mergeada em `main`, deploy de producao concluido e APK Android beta `1.0.7 (8)` publicada no canal direto do site.
- Artefatos afetados:
  - `apps/mobile/lib/src/features/live_refresh.dart`
  - `apps/mobile/lib/src/features/ranking/`
  - `apps/mobile/lib/src/features/shell/`
  - `apps/mobile/test/`
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/`
- Bloqueios: nenhum conhecido.
- Iniciado em: 2026-06-16
- Atualizado em: 2026-06-16
- Retomada: acompanhar feedback de Ranking no Android beta `1.0.7 (8)`; se a proxima fatia mobile exigir nova publicacao, incrementar `version` em `apps/mobile/pubspec.yaml`, gerar APK release assinada com bases de producao e publicar pelo canal direto.
- Evidências de validação local: `cd apps/mobile && flutter test test/ranking_screen_test.dart test/shell_screen_test.dart` com 8 testes OK; `cd apps/mobile && flutter analyze` sem issues; `cd apps/mobile && flutter test` com 78 testes OK; `git diff --check` limpo.
- Evidências de publicação: PR #91 (`Atualiza Ranking mobile com dados quentes`) mergeada em `main` por squash commit `585733fa69bdccdd4b6d8a90280c9afbcc25e3b2`; GitHub Actions `GoTrendLabs CI and Deploy` run `27658699222` concluiu jobs `test` e `deploy` com sucesso; producao respondeu `https://gotrendlabs.com.br/api/health` com `status=ok`, `maintenance.web_enabled=false`, `maintenance.mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; homepage retornou `HTTP/2 200`; APK release `1.0.7 (8)` gerada com `GTL_API_BASE_URL=https://gotrendlabs.com.br/api` e `GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br`, SHA-256 `54822fc7aa84ebad2e923c0af75076ba43f7d73433c918f1a365bcd2d4ffe5ae` e tamanho `57636557` bytes; APK publicada em producao via SSM `1d347ac1-7a64-496f-b6d4-578926566bc3` com limpeza temporaria posterior via SSM `5c26639f-2a22-4352-a855-56ffd44135e8`; bucket S3 temporario de transporte foi removido; `https://gotrendlabs.com.br/app/android/latest.json` retornou `version_name=1.0.7`, `version_code=8`, `file_size=57636557` e o mesmo SHA-256; download publico da APK retornou `HTTP/2 200`, `content-type: application/vnd.android.package-archive`, `content-length=57636557` e hash recalculado identico.
- Reversao lógica: remover invalidacao/refresh de ranking do helper central, shell e `RankingScreen`, mantendo `GET /rankings` e filtros existentes inalterados.

## WFLOW-20260616-MOBILE-LIVE-REFRESH-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `FEAT-WALLET-001`, `FEAT-NOTIFY-001`
- Objetivo: corrigir refresh em tempo de consulta no app mobile para que mercados/status, detalhe, wallet, ledger, recargas e alertas sejam reconsultados ao abrir telas criticas, voltar do background, trocar para abas dependentes de mercado e usar pull-to-refresh, sem mudar contratos backend.
- Etapa atual: concluído; PR #89 mergeada em `main`, deploy de produção concluído e APK Android beta `1.0.6 (7)` publicado no canal direto do site.
- Artefatos afetados:
  - `apps/mobile/lib/src/features/live_refresh.dart`
  - `apps/mobile/lib/src/features/shell/`
  - `apps/mobile/lib/src/features/markets/`
  - `apps/mobile/lib/src/features/wallet/`
  - `apps/mobile/test/`
  - `apps/mobile/pubspec.yaml`
  - `apps/mobile/README.md`
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
- Bloqueios: nenhum conhecido.
- Iniciado em: 2026-06-16
- Atualizado em: 2026-06-16
- Encerrado em: 2026-06-16
- Retomada: acompanhar feedback físico do app Android publicado; se o usuário ainda perceber dados desatualizados, validar evento específico contra logs/API de produção antes de adicionar polling contínuo.
- Reversão lógica: remover invalidações/refetches centralizados do Flutter, voltar `RefreshIndicator` aos callbacks anteriores e manter a versão Android ativa anterior `1.0.5 (6)` no Admin Ops.
- Evidências de validação local: `cd apps/mobile && flutter test test/markets_screen_test.dart`; `cd apps/mobile && flutter pub get`; `cd apps/mobile && flutter analyze`; `cd apps/mobile && flutter test`; `git diff --check`; `cd apps/mobile && flutter build apk --release --dart-define=GTL_API_BASE_URL=https://gotrendlabs.com.br/api --dart-define=GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br` gerou APK assinado `1.0.6 (7)` com SHA-256 `ce4ea6e23305474b2ec1e5d73708b680ec12a9c4018bd845d77c076e369c2288` e tamanho `57636557` bytes; APK debug com API de produção instalado no Galaxy S20 `192.168.18.148:43831`, sem `adb reverse`, com `GTL_API_BASE_URL=https://gotrendlabs.com.br/api`, Activity `br.com.gotrendlabs.gotrendlabs_mobile/.MainActivity` focada e SHA-256 `48011f20ada65846c0f823d784d11449057ffe116bb61c6029ddcf51f520f756`.
- Evidências de publicação: PR #89 (`Corrige refresh vivo no mobile`) mergeada em `main` por squash commit `db0f9757fbc75df172563af0e03e7561cd1154a8`; GitHub Actions `GoTrendLabs CI and Deploy` run `27656995985` concluiu jobs `test` e `deploy` com sucesso; produção respondeu `https://gotrendlabs.com.br/api/health` com `status=ok`, `maintenance.web_enabled=false`, `maintenance.mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; homepage retornou `HTTP/2 200`; APK release `1.0.6 (7)` publicada em produção via SSM `096bb6c7-e31f-4101-81b0-30d01c370fc9`, com limpeza temporária posterior via SSM `b48ae9f8-9234-4f13-94c6-4ec996d19d96`; bucket S3 temporário de transporte foi removido; `https://gotrendlabs.com.br/app/android/latest.json` retornou `version_name=1.0.6`, `version_code=7`, `file_size=57636557` e SHA-256 `ce4ea6e23305474b2ec1e5d73708b680ec12a9c4018bd845d77c076e369c2288`; download público da APK retornou `HTTP/2 200`, `content-type: application/vnd.android.package-archive`, `content-length=57636557` e hash recalculado idêntico.

## WFLOW-20260616-MOBILE-MARKET-WALLET-UX-FIXES-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `FEAT-PRED-001`, `FEAT-WALLET-001`, `FEAT-NOTIFY-001`, `FastAPI public contract`, `frontend-web`
- Objetivo: corrigir UX mobile de mercado, comentários, alertas e wallet, remover `Insights` enquanto não houver contrato recorrente e alinhar mercados `open` com `auto_close_enabled=true` e `close_at` vencido como efetivamente `locked`.
- Etapa atual: publicado em `main` pela PR #87, deploy de produção concluído e smokes públicos confirmaram API/site saudáveis e Royal Ascot 2026 como `locked`/`Fechado` no contrato público.
- Artefatos afetados:
  - `apps/api/backend_api/main.py`
  - `apps/web/django/core/domain_client.py`
  - `apps/web/django/communications/push_services.py`
  - `apps/mobile/lib/src/`
  - `apps/mobile/test/`
  - `tests/test_web_smoke.py`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/features/mobile-mvp.md`
  - `docs/specs/features/mobile-ux.md`
  - `docs/specs/features/market-detail.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
- Bloqueios: nenhum conhecido; publicação de nova APK beta fica fora desta entrega.
- Iniciado em: 2026-06-16
- Atualizado em: 2026-06-16
- Encerrado em: 2026-06-16
- Retomada: acompanhar feedback mobile de mercado, comunidade, alertas e wallet; se a próxima publicação Android exigir essas telas no canal beta, gerar nova APK em follow-up próprio.
- Reversão lógica: remover overlay de status efetivo em FastAPI/fallback web, restaurar `Insights` no shell mobile, voltar wallet/ticket/alertas/cards ao comportamento anterior e retirar as notas documentais desta fatia.
- Evidências de validação local: `.venv/bin/python manage.py check`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `.venv/bin/python manage.py test tests.test_web_smoke.BackendAuthAPITests.test_market_api_seed_filters_and_detail_contract --keepdb`; `.venv/bin/python manage.py test tests.test_web_smoke.BackendAuthAPITests.test_market_api_treats_expired_auto_close_market_as_locked tests.test_web_smoke.BackendAuthAPITests.test_expired_auto_close_market_blocks_prediction_and_position_actions --keepdb`; `.venv/bin/python manage.py test tests.test_web_smoke.WebSmokeTests.test_main_pages_render --keepdb`; `.venv/bin/python manage.py test tests.test_web_smoke.WebSmokeTests.test_market_pages_consume_api_and_fallback_to_fixture tests.test_web_smoke.WebSmokeTests.test_market_and_result_share_pages_expose_social_cards tests.test_web_smoke.WebSmokeTests.test_home_stays_market_focused_for_guest_and_user tests.test_web_smoke.WebSmokeTests.test_home_stats_show_real_total_predictions tests.test_web_smoke.WebSmokeTests.test_site_local_fallback_treats_expired_auto_close_market_as_locked --keepdb`; `.venv/bin/python manage.py test tests.test_web_smoke.BackendAuthAPITests.test_push_outbox_uses_user_notification_policy_and_safe_payload --keepdb`; `.venv/bin/python -m py_compile apps/web/django/communications/push_services.py tests/test_web_smoke.py`; `cd apps/mobile && flutter pub get`; `cd apps/mobile && flutter analyze`; `cd apps/mobile && flutter test`; `cd apps/mobile && flutter test test/alerts_screen_test.dart test/market_detail_screen_test.dart`; `git diff --check`.
- Evidências de publicação: PR #87 (`Ajusta UX mobile de mercados, alertas e wallet`) mergeada em `main` por squash commit `9f724c989b7d054356fed83130415b14b518dd08`; GitHub Actions `GoTrendLabs CI and Deploy` run `27654353053` concluiu jobs `test` e `deploy` com sucesso; produção respondeu `https://gotrendlabs.com.br/api/health` com `status=ok`, `maintenance.web_enabled=false`, `maintenance.mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; homepage retornou `HTTP/2 200`; `/api/markets` retornou 19 mercados; `/api/markets/rei-rainha-royal-ascot-2026` retornou `status=locked`, `status_label=Fechado`, `auto_close_enabled=true`, `close_at=2026-06-16T15:55:00+00:00` e `comment_count=6`; o mesmo slug ficou ausente de `/api/markets?status=open` e presente em `/api/markets?status=locked`; a página web `/markets/rei-rainha-royal-ascot-2026/` retornou `HTTP 200`, exibiu `Mercado fechado` e manteve o trilho de ciclo sem reabrir o ticket.

## WFLOW-20260616-CADDY-PROBE-BLOCK-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-OPSLOG-001`, infra de produção
- Objetivo: bloquear no Caddy probes comuns de WordPress, PHP, `.env`, `.git` e `vendor` antes que cheguem ao Django, reduzindo ruído em `gotrendlabs_system_logs`
- Etapa atual: publicado em `main` pelas PRs #84 e #85, deploy de produção concluído, proxy recriado e probes validados sem persistência em logs Django
- Artefatos afetados:
  - `ops/deploy/production/Caddyfile`
  - `ops/deploy/production/README.md`
  - `docs/specs/state/feature-changelog.md`
- Bloqueios: nenhum
- Iniciado em: 2026-06-16
- Atualizado em: 2026-06-16
- Encerrado em: 2026-06-16
- Retomada: acompanhar logs técnicos; se surgirem novos padrões de probe recorrentes, adicioná-los ao matcher Caddy em novo follow-up pequeno
- Reversão lógica: remover o matcher `@blocked_probe` e o `handle` correspondente do `Caddyfile`, mantendo as notas documentais como histórico ou revertendo-as em PR separado
- Evidências de validação local: `docker run --rm -v "$PWD/ops/deploy/production/Caddyfile:/etc/caddy/Caddyfile:ro" caddy:2 caddy validate --config /etc/caddy/Caddyfile` com `Valid configuration`; `docker run --rm -v "$PWD/ops/deploy/production/Caddyfile:/etc/caddy/Caddyfile:ro" caddy:2 caddy adapt --config /etc/caddy/Caddyfile --pretty` confirmou `@blocked_probe` antes dos handlers de `/static`, `/media`, `/api` e do proxy Django; após smoke da PR #84 mostrar `/admin/phpinfo.php` ainda chegando ao Django, o matcher foi convertido para `path_regexp` e revalidado com `caddy validate`/`caddy adapt`; `git diff --check`; `docker compose -f ops/deploy/production/docker-compose.yml config` ficou bloqueado localmente pela ausência intencional de `.env.prod`
- Evidências de publicação: PR #84 mergeada em `main` com merge commit `71dbb9f567b671cbebe74aaf3c06b9e357a4a271` e GitHub Actions `GoTrendLabs CI and Deploy` run `27651554576` com jobs `test` e `deploy` em sucesso; PR #85 mergeada em `main` com merge commit `499782e8e6376078d571efec55cacf29b33a5afa` e run `27652030681` com jobs `test` e `deploy` em sucesso; proxy de produção recriado por SSM e validado com `caddy validate` mostrando `path_regexp blocked_probe`; smokes públicos confirmaram `404` direto do Caddy para `/admin/phpinfo.php?codex=final-regexp` e `/admin/.env?codex=final-regexp`, `200` saudável para `/api/health` e home; consulta read-only em `gotrendlabs_system_logs` nos 15 minutos finais retornou `probe_log_count=0`, `recent_error_count=0` e `recent_5xx_count=0`

## WFLOW-20260614-MOBILE-ANTI-ABUSE-CONTRIBUTIONS-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `FEAT-AUTH-001`, `FEAT-SUGGEST-001`
- Objetivo: manter cadastro, feedback e sugestao de mercado de visitantes dentro do app mobile com desafio anti-abuso validado pela FastAPI, corrigindo envio de feedback guest e tornando `Sugerir mercado` visivel no menu principal
- Etapa atual: publicado em `main` pela PR #82, deploy de produção concluído e endpoint anti-abuso mobile validado por smoke
- Artefatos afetados:
  - `apps/api/backend_api/`
  - `apps/mobile/`
  - `packages/contracts/openapi/gotrendlabs-api.json`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/features/mobile-mvp.md`
  - `docs/specs/features/mobile-ux.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/`
- Bloqueios: nenhum conhecido; publicação de APK release/beta permanece fora deste follow-up
- Iniciado em: 2026-06-14
- Atualizado em: 2026-06-15
- Retomada: acompanhar feedback de cadastro, feedback e sugestão no app; para QA física, usar build mobile apontando para `https://gotrendlabs.com.br/api`
- Reversão lógica: remover `GET /anti-abuse/challenge`, remover campos `anti_abuse_token`/`anti_abuse_answer` dos payloads, voltar cadastro/feedback/sugestão mobile ao comportamento anterior e retirar `Sugerir mercado` do menu principal
- Evidências de validação local: `.venv/bin/python -m py_compile apps/api/backend_api/main.py apps/api/backend_api/schemas.py`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `.venv/bin/python manage.py check`; `.venv/bin/python manage.py test tests.test_web_smoke.BackendAuthAPITests.test_recaptcha_blocks_register_and_guest_queue_when_required tests.test_web_smoke.BackendAuthAPITests.test_mobile_anti_abuse_challenge_allows_register_and_guest_queue tests.test_web_smoke.BackendAuthAPITests.test_mobile_anti_abuse_challenge_rejects_wrong_answer tests.test_web_smoke.BackendAuthAPITests.test_recaptcha_not_required_for_authenticated_queue_items --keepdb`; `cd apps/mobile && flutter analyze`; `cd apps/mobile && flutter test test/anti_abuse_repository_test.dart test/support_repository_test.dart test/auth_biometric_test.dart test/shell_screen_test.dart`; `cd apps/mobile && flutter test` com 57 testes OK; `git diff --check`; `cd apps/mobile && flutter build apk --debug --dart-define=GTL_API_BASE_URL=http://127.0.0.1:8001 --dart-define=GTL_PUBLIC_WEB_BASE_URL=http://127.0.0.1:8000`; APK debug instalada no Galaxy S20 via `adb install -r`, com `adb reverse tcp:8001 tcp:8001` e `tcp:8000 tcp:8000`; QA visual física ficou pendente porque o aparelho estava no lockscreen/Bouncer, embora a Activity do app tenha ficado focada atrás do bloqueio
- Evidências de publicação: PR #82 (`Implementa posição mobile e desafio anti-abuso`) mergeada em `main` com merge commit `88b80fe0bd1065e07e75b942716823503c8ba0aa`; GitHub Actions `GoTrendLabs CI and Deploy` run `27542726255` concluiu jobs `test` e `deploy` com sucesso; produção respondeu `https://gotrendlabs.com.br/api/health` com `status=ok`, `web_enabled=false`, `mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; `/api/anti-abuse/challenge` respondeu com `prompt`, `token` e `expires_at`; `/api/openapi.json` expôs `/anti-abuse/challenge` e os campos `anti_abuse_token`/`anti_abuse_answer` em `RegisterPayload`; `/api/markets` retornou 19 mercados

## WFLOW-20260614-MOBILE-POSITION-REVISION-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `FEAT-PRED-001`, `FEAT-WALLET-001`
- Objetivo: implementar no Flutter/mobile a experiência de reforço e revisão de posição já exposta pela FastAPI, preservando backend como autoridade de domínio
- Etapa atual: publicado em `main` pela PR #82, deploy de produção concluído e contratos de posição mobile validados por smoke
- Artefatos afetados:
  - `apps/mobile/`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/features/mobile-ux.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/`
- Bloqueios: nenhum conhecido; QA autenticado de reforço/revisão em dispositivo físico ainda depende de usuário real com posição ativa
- Iniciado em: 2026-06-14
- Atualizado em: 2026-06-15
- Retomada: acompanhar feedback de uso mobile em mercados com posição ativa; QA visual autenticado de reforço/revisão em dispositivo físico deve usar usuário real com posição ativa
- Reversão lógica: remover parsing de `viewer_position` e métodos `position-preview`/`position-actions` no mobile, voltar `PredictionTicket` ao fluxo exclusivo de primeira previsão e restaurar docs/state para reforço/revisão mobile pendente
- Evidências de validação local: `cd apps/mobile && flutter test test/markets_repository_test.dart`; `cd apps/mobile && flutter test test/prediction_ticket_test.dart`; `cd apps/mobile && flutter analyze`; `cd apps/mobile && flutter test` com 55 testes OK; `.venv/bin/python packages/contracts/export_openapi.py --check`; `.venv/bin/python manage.py check`; `git diff --check`; `cd apps/mobile && flutter build apk --debug` gerando `build/app/outputs/flutter-apk/app-debug.apk` com aviso não bloqueante já conhecido de Kotlin Gradle Plugin transitivo em `package_info_plus`/`share_plus`
- Evidências UX incrementais: linguagem mobile simplificada em 2026-06-15 para expor `Aumentar posição` e `Trocar escolha`, mantendo contratos `reinforcement`/`revision`; validação com `dart format lib/src/features/markets/prediction_ticket.dart test/prediction_ticket_test.dart`, `flutter test test/prediction_ticket_test.dart`, `flutter analyze`, `flutter test` com 57 testes OK e `git diff --check`
- Evidências UX incrementais: ações de posição convertidas em frames sempre fechados em 2026-06-15, inclusive quando apenas uma ação estiver disponível, e preview de posição sem `allowed` agora bloqueia confirmação por padrão; validação com `dart format lib/src/features/markets/market_models.dart test/markets_repository_test.dart`, `flutter test test/markets_repository_test.dart test/prediction_ticket_test.dart`, `flutter analyze`, `flutter test` com 59 testes OK, `git diff --check` e APK debug instalada no Galaxy S20 apontando para `https://gotrendlabs.com.br/api` / `https://gotrendlabs.com.br`
- Evidências de publicação: PR #82 (`Implementa posição mobile e desafio anti-abuso`) mergeada em `main` com merge commit `88b80fe0bd1065e07e75b942716823503c8ba0aa`; GitHub Actions `GoTrendLabs CI and Deploy` run `27542726255` concluiu jobs `test` e `deploy` com sucesso; produção respondeu `https://gotrendlabs.com.br/api/health` com `status=ok`, `web_enabled=false`, `mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; `/api/openapi.json` expôs `/markets/{slug}/position-preview` e `/markets/{slug}/position-actions`; `/api/markets` retornou 19 mercados

## WFLOW-20260614-POSITION-REVISION-WEB-FIRST-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-PRED-001`, `FEAT-WALLET-001`, `Admin Ops`, `FastAPI public contract`, `frontend-web`
- Objetivo: implementar reforço e revisão auditável de posições primeiro no backend/site, preservando FastAPI como autoridade e deixando mobile para fase posterior
- Etapa atual: publicado em `main` pela PR #80, deploy de produção concluído e contrato novo validado por smoke
- Artefatos afetados:
  - `apps/api/backend_api/`
  - `apps/web/django/markets/`
  - `apps/web/django/admin_ops/`
  - `apps/web/static/js/gotrendlabs.js`
  - `packages/contracts/openapi/gotrendlabs-api.json`
  - `docs/specs/`
- Bloqueios: nenhum; mobile permanece como fase posterior documentada em `known-gaps.md`
- Iniciado em: 2026-06-14
- Atualizado em: 2026-06-14
- Retomada: acompanhar feedback de uso web e planejar a fase mobile sem mover regra de domínio para o app
- Reversão lógica: remover endpoints `position-preview`/`position-actions`, restaurar unicidade `uniq_prediction_user_market`, remover campos de posição/config, voltar UI para estado somente leitura após primeira previsão e retirar `prediction_revision_penalty`
- Evidências de validação local: `.venv/bin/python manage.py check`; `.venv/bin/python manage.py makemigrations --check --dry-run`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `git diff --check origin/main`; suíte completa `.venv/bin/python manage.py test --keepdb` com 186 testes OK; testes focados de reforço/revisão, bloqueios por cutoff/config, lock transacional de previsão inicial, auditoria de resolução com posições revisadas, Admin Ops Config e regressões de dashboard/AI/resolução/web também executados durante o ciclo de correção
- Evidências incrementais: limite máximo de reforços, grupos de configuração por reforço/revisão e resumo de entradas abertas validados com `.venv/bin/python manage.py test tests.test_web_smoke.BackendAuthAPITests.test_position_reinforcement_and_revision_are_auditable_wallet_mutations tests.test_web_smoke.BackendAuthAPITests.test_position_reinforcement_respects_admin_limit tests.test_web_smoke.BackendAuthAPITests.test_position_revision_respects_admin_config_and_cutoff_window tests.test_web_smoke.WebSmokeTests.test_admin_config_persists_maintenance_json_and_smtp_database_config --keepdb`; `.venv/bin/python manage.py check`; `.venv/bin/python manage.py makemigrations --check --dry-run`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `git diff --check`
- Evidências UX: detalhe web reorganizado para resumo compacto, entradas abertas recolhíveis e abas `Reforçar`/`Revisar`, validado com `.venv/bin/python manage.py test tests.test_web_smoke.WebSmokeTests.test_market_detail_position_actions_use_compact_tabs tests.test_web_smoke.BackendAuthAPITests.test_position_reinforcement_and_revision_are_auditable_wallet_mutations tests.test_web_smoke.BackendAuthAPITests.test_position_reinforcement_respects_admin_limit --keepdb`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `git diff --check`
- Evidências UX incrementais: confirmação de revisão passou a exibir entradas encerradas, total ativo, custo em GT₵/percentual e nova posição estimada vindos da FastAPI, validado com `.venv/bin/python manage.py test tests.test_web_smoke.WebSmokeTests.test_market_detail_position_actions_use_compact_tabs tests.test_web_smoke.BackendAuthAPITests.test_position_reinforcement_and_revision_are_auditable_wallet_mutations tests.test_web_smoke.BackendAuthAPITests.test_position_reinforcement_respects_admin_limit --keepdb`; `.venv/bin/python manage.py check`; `.venv/bin/python manage.py makemigrations --check --dry-run`
- Evidências de publicação: PR #80 (`Reforço e revisão de posição web-first`) mergeada em `main` com merge commit `dc785eac6e0a7c996f0bc312d4c91f90606407fb`; GitHub Actions `GoTrendLabs CI and Deploy` run `27507258490` concluiu jobs `test` e `deploy` com sucesso; produção respondeu `https://gotrendlabs.com.br/` com HTTP 200, `https://gotrendlabs.com.br/api/health` com `status=ok`, `web_enabled=false`, `mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; `/api/markets` retornou o campo `viewer_position`; `/api/openapi.json` expôs `/markets/{slug}/position-preview` e `/markets/{slug}/position-actions`.

## WFLOW-20260613-BADGE-HISTORICAL-OWNERSHIP-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-REP-001`, `Admin Ops`, `FastAPI public contract`
- Objetivo: separar exibição pública/histórica de badges da concessão automática, garantindo que badges pausadas continuem no catálogo visível para todos, sem novas concessões, e que conquistas persistidas continuem compartilháveis e presentes no ranking enquanto a badge estiver visível
- Etapa atual: publicado em `main` e validado em produção
- Artefatos afetados:
  - `apps/api/backend_api/`
  - `apps/web/django/admin_ops/`
  - `apps/web/static/js/gotrendlabs.js`
  - `tests/test_web_smoke.py`
  - `packages/contracts/openapi/gotrendlabs-api.json`
  - `docs/specs/contracts/reputation-ranking.md`
  - `docs/specs/features/reputation-and-ranking.md`
  - `docs/specs/spec_prediction_social_market_pt.md`
  - `docs/specs/state/change-log-specs.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
- Bloqueios: nenhum
- Iniciado em: 2026-06-13
- Atualizado em: 2026-06-13
- Encerrado em: 2026-06-13
- Retomada: evolução futura pode adicionar filtros administrativos por estado de catálogo/concessão ou ações dedicadas de reexibição, preservando a separação `is_active`/`rule_active`
- Reversão lógica: voltar `POST /admin/badges/{code}/deactivate` a ocultar definição e regra, remover `rule_active` do payload administrativo e restaurar filtros públicos para exigir badge ativa e regra ativa no catálogo
- Evidencias de validacao local: testes focados de badges/ranking/compartilhamento e catálogo pausado visível com `.venv/bin/python manage.py test --keepdb tests.test_web_smoke.BackendAuthAPITests.test_badge_catalog_public_personalized_and_admin_contracts tests.test_web_smoke.BackendAuthAPITests.test_badge_awards_are_idempotent_for_automatic_rules tests.test_web_smoke.BackendAuthAPITests.test_rankings_include_recent_active_badges tests.test_web_smoke.WebSmokeTests.test_public_badges_page_renders_for_guest_and_authenticated_user tests.test_web_smoke.WebSmokeTests.test_public_badge_share_link_is_unique_to_awarded_user`; regressao do checkbox Admin Ops com `.venv/bin/python manage.py test --keepdb tests.test_web_smoke.WebSmokeTests.test_admin_badge_form_sends_unchecked_rule_active_false`; `.venv/bin/python manage.py check`; `.venv/bin/python manage.py makemigrations --check --dry-run`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `.venv/bin/python manage.py test --keepdb tests.test_web_smoke` com 180 testes OK
- Evidencias de publicacao: PR #78 mergeada em `main` por squash (`65f8d3d6bdbaa414c73e616015347576a21adc7a`); GitHub Actions `GoTrendLabs CI and Deploy` run `27478757690` concluiu com jobs `test` e `deploy` em sucesso; smoke PRD confirmou `https://gotrendlabs.com.br/`, `/badges/`, `/api/health` e `/api/badges` com HTTP 200, `health.status=ok`, `checks.api=ok`, `checks.database=ok` e payload público de badges contendo `rule_active`.

## WFLOW-20260613-MOBILE-MAINTENANCE-GATE-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `Admin Ops`, `FastAPI public contract`
- Objetivo: implementar manutencao mobile independente da web, controlada pelo Admin Ops, com `GET /health` enriquecido e bloqueio autoritativo da FastAPI para clientes mobile sem excecao por papel no app
- Etapa atual: concluido; PR #75 publicada e mergeada em `main`, GitHub Actions `GoTrendLabs CI and Deploy` verde, producao respondendo com o contrato `/api/health` enriquecido e APK Android beta `1.0.5 (6)` publicada no canal direto
- Artefatos afetados:
  - `apps/api/backend_api/main.py`
  - `apps/web/django/admin_ops/`
  - `apps/web/django/core/platform_config.py`
  - `apps/mobile/`
  - `tests/test_web_smoke.py`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/integration-map.md`
  - `apps/mobile/README.md`
- Bloqueios: nenhum para publicacao; validacao funcional do toggle mobile em sessao Admin Ops autenticada de producao segue como QA operacional recomendado
- Iniciado em: 2026-06-13
- Atualizado em: 2026-06-13
- Encerrado em: 2026-06-13
- Retomada: validar o toggle `Manutenção do app` em sessao Admin Ops autenticada de producao quando houver janela operacional; acompanhar feedback da APK Android beta `1.0.5 (6)` para estados de backend indisponivel/degradado
- Reversao logica: remover `mobile_maintenance_enabled`/mensagem do runtime JSON/Admin Ops, retirar middleware mobile por `X-GoTrendLabs-Client`, voltar `/health` ao contrato simples e remover o gate Flutter `features/maintenance`
- Evidencias de validacao local: `dart format`; `.venv/bin/python manage.py test tests.test_web_smoke.MobileMaintenanceGateTests --keepdb` com 5 testes OK; `cd apps/mobile && flutter test test/maintenance_gate_test.dart` com 4 testes OK; `.venv/bin/python manage.py check`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `cd apps/mobile && flutter analyze`; `cd apps/mobile && flutter test` com 50 testes OK; `git diff --check`; FastAPI e Django locais reiniciados com `.venv/bin/python`; `/health` local retornou `checks.api=ok` e `checks.database=ok`; APK debug Android atualizado foi instalado e aberto no emulador `gotrendlabs_pixel` apos wipe do AVD travado em `RUNNING_LOCKED`
- Evidencias de producao: PR #75 mergeada como `8fe120b6816e08ed86519834b8916fc852e482d9`; GitHub Actions `GoTrendLabs CI and Deploy` run `27473013601` concluiu jobs `test` e `deploy` com sucesso; `https://gotrendlabs.com.br/api/health` retornou `status=ok`, `maintenance.web_enabled=false`, `maintenance.mobile_enabled=false`, `checks.api=ok` e `checks.database=ok`; homepage retornou `HTTP/2 200`; `https://gotrendlabs.com.br/admin-ops/config/` redirecionou para login com `HTTP/2 302`, confirmando a rota protegida em producao; `flutter build apk --release --dart-define=GTL_API_BASE_URL=https://gotrendlabs.com.br/api --dart-define=GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br` gerou APK assinada `1.0.5 (6)` com SHA-256 `c061681f2495759cca2d2eaf38282541d4a82fd1309fefb4037f9f4ac0b2109b` e tamanho `57292289` bytes; APK publicada via SSM `e8a5e7b6-4123-4a34-a547-bf136b99e665` com registro ativo em `gotrendlabs_mobile_app_releases`; limpeza de temporario no container concluida via SSM `bc234076-9b0c-41ae-aac9-a18db56b6e63`; `https://gotrendlabs.com.br/app/android/latest.json` retornou `version_name=1.0.5`, `version_code=6`, `file_size=57292289` e o mesmo SHA-256; download publico da APK retornou `HTTP/2 200`, `content-type: application/vnd.android.package-archive`, `content-length=57292289` e hash recalculado identico; bucket S3 temporario de transporte foi removido

## WFLOW-20260613-MOBILE-BIOMETRIC-AUTH-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `FEAT-AUTH-001`, `future-mobile`
- Objetivo: implementar desbloqueio biométrico/local para sessão mobile lembrada no Android e iOS, sem criar endpoint novo e mantendo a FastAPI como autoridade de sessão
- Etapa atual: concluído; PR #73 publicada e mergeada em `main`, GitHub Actions `GoTrendLabs CI and Deploy` verde, produção fora de maintenance mode e APK Android beta `1.0.4 (5)` publicada no canal direto
- Artefatos afetados:
  - `apps/mobile/`
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/feature-changelog.md`
  - `apps/mobile/README.md`
- Bloqueios: nenhum para publicação; smoke real de prompt biométrico em dispositivo físico de usuário segue como QA operacional recomendado
- Iniciado em: 2026-06-13
- Atualizado em: 2026-06-13
- Encerrado em: 2026-06-13
- Retomada: acompanhar feedback da APK Android beta `1.0.4 (5)` e validar em dispositivo físico real com biometria/senha local quando disponível
- Reversão lógica: remover `local_auth`, preferência biométrica, estado `Sessão protegida`, ajustes nativos Android/iOS e restaurar docs/state para a sessão lembrada simples
- Evidências de validação local: `flutter pub get`; `dart format`; `flutter test test/auth_biometric_test.dart` cobrindo login, cadastro, sessão protegida, preferência desligada sem botão `Entrar com biometria` e desbloqueio sem backfill de preferência; `flutter analyze`; `flutter test` com 46 testes OK; `git diff --check`; `flutter build apk --debug` gerou `build/app/outputs/flutter-apk/app-debug.apk` com aviso não bloqueante já conhecido de Kotlin Gradle Plugin transitivo em `package_info_plus`/`share_plus`; APK debug reinstalado no `emulator-5554`; emulador confirmado com PIN ativo (`1234`) e app debug instalado; `plutil -lint apps/mobile/ios/Runner/Info.plist`; `flutter build ios --simulator --debug` passou após alinhar `IPHONEOS_DEPLOYMENT_TARGET=15.0` às dependências Firebase mobile; iOS Simulator `iPhone 17 Pro` com iOS 26.5 carregou dados locais usando `GTL_API_BASE_URL=http://127.0.0.1:8001`; `flutter build apk --release --dart-define=GTL_API_BASE_URL=https://gotrendlabs.com.br/api --dart-define=GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br` gerou APK assinada `1.0.4 (5)` com SHA-256 `43f8c1184ce7c913070d9bc2c09344a70f2ed8f4c14a12749d8e688d831bc81c` e tamanho `57292069` bytes
- Evidências de produção: PR #73 mergeada como `88808880e9f18b4b9c4dd33a5c45be774819541a`; GitHub Actions `GoTrendLabs CI and Deploy` run `27468406864` concluiu `test` e `deploy` com sucesso; APK release assinada `1.0.4 (5)` foi publicada via SSM `f0f9e3de-7c60-40cd-bdc9-40329db9f1cd`; SSM `727013d0-b5ea-48b4-a72c-63fae0f3b09c` desligou maintenance mode; `https://gotrendlabs.com.br/app/android/latest.json` retornou `version_name=1.0.4`, `version_code=5`, `file_size=57292069` e SHA-256 `43f8c1184ce7c913070d9bc2c09344a70f2ed8f4c14a12749d8e688d831bc81c`; download público da APK retornou `HTTP/2 200`, `content-type: application/vnd.android.package-archive` e hash recalculado idêntico; `https://gotrendlabs.com.br/api/health` retornou `{"status":"ok"}`; homepage retornou `HTTP/2 200`; bucket S3 temporário de transporte foi removido

## WFLOW-20260612-MOBILE-FIREBASE-PUSH-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-NOTIFY-001`, `FEAT-MOBILE-001`, `communications`, `future-mobile`
- Objetivo: implementar push mobile FCM real para Android, preservando defaults seguros, credenciais fora do Git/Admin Ops e o app como cliente da FastAPI
- Etapa atual: concluído; PR #71 publicada e mergeada em `main`, GitHub Actions `GoTrendLabs CI and Deploy` verde, PRD com FCM real habilitado fora do Git/Admin Ops e APK Android beta `1.0.3 (4)` publicada com Firebase ativo
- Artefatos afetados:
  - `apps/mobile/`
  - `apps/web/django/communications/`
  - `apps/web/django/admin_ops/`
  - `config/urls.py`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
  - `.env.example`
  - `requirements.txt`
- Bloqueios: nenhum para a ativação operacional; teste ponta a ponta de recebimento ainda depende de usuário autenticado/dispositivo Android com APK `1.0.3 (4)` instalado e permissão de notificação aceita
- Iniciado em: 2026-06-12
- Atualizado em: 2026-06-12
- Encerrado em: 2026-06-12
- Retomada: validar recebimento real no Android com usuário autenticado, acompanhar novos devices em Admin Ops e publicar nova APK apenas quando houver incremento de versão/canal
- Reversão lógica: voltar Flutter para provider noop/fake-token, remover dependências Firebase mobile, canal Android, sender Firebase Admin SDK e restaurar docs/state para fase dry-run/noop mantendo outbox `PushDelivery` intacta
- Evidências de validação local: `dart format lib test`; `git diff --check`; `flutter analyze`; `flutter test`; `flutter test test/push_controller_test.dart test/push_repository_test.dart test/about_screen_test.dart`; `flutter build apk --debug`; `.venv/bin/python manage.py check`; `.venv/bin/python packages/contracts/export_openapi.py --check`; `RECAPTCHA_ENABLED=0 .venv/bin/python manage.py test --keepdb` com os testes focados `BackendAuthAPITests.test_fcm_provider_marks_successful_delivery_as_sent`, `test_fcm_provider_retries_transient_send_errors`, `test_push_outbox_uses_user_notification_policy_and_safe_payload`, `test_push_preferences_block_outbox_and_provider_invalidates_bad_tokens`, `WebSmokeTests.test_admin_push_devices_tab_lists_devices_without_raw_tokens` e `WebSmokeTests.test_admin_ops_requires_staff_and_renders_api_data`; teste local com service account Firebase carregada confirmou `provider=fcm`, `dry_run=False`, `fcm_secret_configured=True` sem imprimir segredo
- Evidências de produção: PR #71 mergeada como `e51465e8f5894521edbaf716d0e35750dc386fe9`; GitHub Actions `GoTrendLabs CI and Deploy` run `27445681561` concluiu `test` e `deploy` com sucesso; SSM `5582a581-d8ee-4a8e-9034-b6251797c7d6` atualizou `/opt/gotrendlabs/.env.prod`, recriou `django`, `fastapi` e `daemon`, `manage.py check` passou e `push_runtime_config` retornou `enabled=True`, `provider=fcm`, `dry_run=False`, `fcm_secret_configured=True`; APK release assinada `1.0.3 (4)` com SHA-256 `88e5620dd7d6989e01b785f9c2ebee94cce11817fd4b0687681ea286da133713` foi publicada via SSM `2f08493a-2337-4507-be4c-20972982b75c`; `https://gotrendlabs.com.br/app/android/latest.json` retornou `version_name=1.0.3`, `version_code=4`, `file_size=56555211` e o mesmo SHA-256; download público da APK retornou `HTTP/2 200` e hash recalculado idêntico; `https://gotrendlabs.com.br/api/health` retornou `{"status":"ok"}`; maintenance permaneceu desligado; bucket S3 temporário de transporte foi removido

## WFLOW-20260611-MOBILE-UX-FEED-RANKING-SESSION-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`
- Objetivo: implementar melhorias de feed mobile, ranking, confirmação de previsão, consenso multi-série, push informativo em `Sobre`, tracking de view/share, sessão com `Lembrar login` e APK Android beta `1.0.2+3`
- Etapa atual: concluído; branch `feature/mobile-ux-feed-ranking-session` publicada, PR #70 criada, `main` atualizada para `0577280`, deploy de produção executado via SSM e APK Android beta `1.0.2 (3)` publicada em produção
- Artefatos afetados:
  - `apps/mobile/`
  - `apps/mobile/test/`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/features/mobile-mvp.md`
  - `docs/specs/features/mobile-ux.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/integration-map.md`
  - `docs/specs/state/known-gaps.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `apps/mobile/README.md`
- Bloqueios: GitHub API/Actions ficou indisponível por timeout durante o fechamento; merge foi aplicado por fast-forward via `git push` para `main` e deploy foi executado diretamente por SSM
- Iniciado em: 2026-06-11
- Atualizado em: 2026-06-12
- Encerrado em: 2026-06-12
- Retomada: acompanhar feedback de usuários no Android beta `1.0.2 (3)`; se precisar publicar nova APK, incrementar `version` em `apps/mobile/pubspec.yaml`, gerar release assinada com os defines de produção e publicar pelo Admin Ops/canal direto
- Reversão lógica: reverter ajustes Flutter de feed/ranking/sessão/consenso/push informativo/tracking, restaurar splash/header anterior e voltar README/specs/state para o comportamento mobile anterior
- Evidências de validação local: `git diff --check`; `flutter pub get`; `flutter analyze` sem issues; `flutter test` com 35 testes OK; `flutter build apk --release --dart-define=GTL_API_BASE_URL=https://gotrendlabs.com.br/api --dart-define=GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br --dart-define=GTL_PUSH_FIREBASE_ENABLED=false` gerou APK assinada com SHA-256 `ae52faaf0525cd22dd45da3ced89ba6f7f208864da3c7c26384e9a0b0c3337bb`; QA local em Android Emulator e iPhone Simulator durante a implementação; revisão documental contra `gotrendlabs-mobile-docs-governor`
- Evidências de produção: deploy SSM `43bc0576-7521-4c1d-be4e-ccb107be40cf` concluiu `Success`, sem migrations pendentes e com containers `django`, `fastapi`, `daemon` e `proxy` recriados; release Android publicada por SSM `8bc28e39-0fd1-4306-a807-9598b5256c8f`, `https://gotrendlabs.com.br/app/android/latest.json` retornou `version_name=1.0.2`, `version_code=3`, `file_size=55753713` e SHA-256 `ae52faaf0525cd22dd45da3ced89ba6f7f208864da3c7c26384e9a0b0c3337bb`; download público de `https://gotrendlabs.com.br/media/app_releases/android/gotrendlabs-android-1.0.2-3.apk` retornou `HTTP/2 200`, `content-type: application/vnd.android.package-archive`, `content-length: 55753713` e hash recalculado idêntico; `https://gotrendlabs.com.br/api/health` retornou `{"status":"ok"}`

## WFLOW-20260611-SOCIAL-AUTH-IMMEDIATE-EMAIL-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`, `FEAT-NOTIFY-001`
- Objetivo: implementar login social real para Google/Facebook/X, envio imediato filtrado para emails críticos de autenticação e rodapé institucional automático em emails transacionais
- Etapa atual: concluído; branch `feature/social-login-immediate-email` criada a partir de `origin/main`, login social real, dreno imediato filtrado de emails críticos e rodapé transacional automático implementados
- Artefatos afetados:
  - `apps/api/backend_api/`
  - `apps/web/django/accounts/`
  - `apps/web/django/communications/`
  - `docs/specs/`
  - `packages/contracts/openapi/gotrendlabs-api.json`
  - `tests/test_web_smoke.py`
- Bloqueios: credenciais OAuth informadas em chat/notes devem ser rotacionadas antes de produção e instaladas apenas via ambiente
- Iniciado em: 2026-06-11
- Atualizado em: 2026-06-11
- Encerrado em: 2026-06-11
- Retomada: instalar credenciais OAuth rotacionadas em PRD, configurar callbacks dos provedores, recriar `django`, `fastapi` e `daemon`, validar `/api/health`, login social com conta teste, cadastro/reset imediato e rodapé em novo email
- Reversão lógica: voltar botões sociais para placeholder, remover variáveis OAuth do ambiente, manter outbox/daemon como caminho único e remover rodapé automático do renderizador
- Evidências de validação local: `python manage.py check`; `python manage.py makemigrations --check --dry-run`; `python manage.py test --keepdb tests.test_web_smoke` com 167 testes OK; `python packages/contracts/export_openapi.py --check`; `git diff --check`

## WFLOW-20260609-RESEND-TRANSACTIONAL-EMAIL-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-NOTIFY-001`, `communications`
- Objetivo: adicionar Resend como provider de email transacional via API HTTPS, preservando outbox, templates, retries, logs e SMTP genérico como fallback
- Etapa atual: concluído; branch `feature/resend-transactional-email` criada a partir de `origin/main`, provider Resend implementado, integração antiga de email removida do app/docs, resíduos de banco/env limpos, reset de senha com envio imediato e links absolutos
- Artefatos afetados:
  - `apps/web/django/communications/`
  - `apps/web/django/admin_ops/`
  - `apps/api/backend_api/main.py`
  - `config/settings.py`
  - `.env.example`
  - `.env.prod.example`
  - `docs/specs/`
  - `tests/test_web_smoke.py`
- Bloqueios: ativação real em produção depende de instalação de `GOTRENDLABS_RESEND_API_KEY`, DNS Resend verificado e rotação da key compartilhada no chat
- Iniciado em: 2026-06-09
- Atualizado em: 2026-06-09
- Encerrado em: 2026-06-09
- Retomada: após deploy, definir provider `resend` no Admin Ops, preencher `no-reply@gotrendlabs.com.br`, instalar `GOTRENDLABS_RESEND_API_KEY` fora do Git, recriar containers e validar com `send_resend_test_email`
- Reversão lógica: voltar `email_provider` para `smtp`, remover `GOTRENDLABS_RESEND_API_KEY` do ambiente e manter outbox/templates/SMTP existentes intactos
- Evidências de validação local: `manage.py makemigrations --check --dry-run`; `manage.py check`; suíte completa `manage.py test --keepdb` com 163 testes OK; `git diff --check`; busca local confirmou ausência da key real Resend nos arquivos alterados

## WFLOW-20260608-MOBILE-LAUNCHER-BRANDING-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`
- Objetivo: alinhar a identidade nativa do app ao site, usando nome exibido `GoTrendLabs`, icone de launcher derivado do logo de constelacao e splash Android escuro
- Etapa atual: concluido; nome iOS, icones iOS/Android, variantes iOS `dark`/`tinted` e launch theme Android moderno com lockup/branding da marca atualizados e validados localmente em 2026-06-08
- Artefatos afetados:
  - `apps/mobile/ios/Runner/Info.plist`
  - `apps/mobile/ios/Runner/Assets.xcassets/AppIcon.appiconset/`
  - `apps/mobile/android/app/src/main/res/mipmap-*/ic_launcher.png`
  - `apps/mobile/android/app/src/main/res/drawable*/launch_background.xml`
  - `apps/mobile/android/app/src/main/res/drawable-nodpi/launch_*.png`
  - `apps/mobile/android/app/src/main/res/values*/`
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/state/feature-changelog.md`
- Bloqueios: nenhum local
- Iniciado em: 2026-06-08
- Atualizado em: 2026-06-08
- Encerrado em: 2026-06-08
- Retomada: se o visual do launcher/splash for refinado novamente, gerar novas variantes `Any`, `Dark` e `Tinted` a partir da mesma marca do site e validar no iOS/Android Simulator
- Reversao logica: restaurar `CFBundleDisplayName` anterior, icones de launcher anteriores em iOS/Android e launch theme Android padrao do Flutter
- Evidencias de validacao local: `plutil -lint apps/mobile/ios/Runner/Info.plist`; `flutter analyze`; `flutter build apk --debug`; `flutter build ios --simulator --debug`; `assetutil --info build/ios/iphonesimulator/Runner.app/Assets.car` confirmou `UIAppearanceDark` e `Tinted`; `xcrun simctl listapps` confirmou `CFBundleDisplayName = GoTrendLabs`; app relancado no `GTL iPhone 16` com `GTL_API_BASE_URL=http://127.0.0.1:8001` e `GTL_PUBLIC_WEB_BASE_URL=http://127.0.0.1:8000`; APK debug reinstalado no `emulator-5554`, label `GoTrendLabs` confirmado via `aapt dump badging`, gaveta Android validada visualmente, launch theme escuro validado ao abrir `br.com.gotrendlabs.gotrendlabs_mobile/.MainActivity` e frames capturados confirmaram splash moderno com badge, wordmark, tagline e fundo escuro

## WFLOW-20260608-ANDROID-DIRECT-DOWNLOAD-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`
- Objetivo: distribuir beta Android publico pelo site oficial com APK release assinado, Admin Ops de upload, CTA discreto no rodape/login/cadastro/compartilhamento, checksum publico e API mobile em `/api/*`
- Etapa atual: concluido; APK Android `1.0.1 (2)` assinado com a identidade nativa atual foi publicado em producao e o link HTTPS direto foi validado em 2026-06-08
- Artefatos afetados:
  - `apps/mobile/android/`
  - `apps/mobile/README.md`
  - `apps/web/django/admin_ops/`
  - `apps/web/django/core/`
  - `apps/web/templates/`
  - `apps/web/static/css/gotrendlabs.css`
  - `ops/deploy/production/Caddyfile`
  - `docs/specs/`
  - `tests/test_web_smoke.py`
- Bloqueios: nenhum para o canal direto
- Observacao operacional: a release anterior `1.0.0 (1)` foi assinada com certificado SHA-256 `5a5bf9444b9ac753a59af2514e84897179de4b3d311f42844b7eae856d89afe4`, diferente da nova chave estavel local `3b549cb758247332d5ec1cdd5522d35fb15360d240bd3974e4c4ac1d4e2be05f`; quem instalou a APK anterior pode precisar desinstalar e reinstalar uma vez
- Iniciado em: 2026-06-08
- Atualizado em: 2026-06-08
- Encerrado em: 2026-06-08
- Retomada: quando o canal for revisado, conferir `/app/android/latest.json`, rodape/login/cadastro/compartilhamento com link direto, download HTTPS, SHA-256 e smokes de API publica em `/api/health` e `/api/markets`
- Reversao logica: remover CTA Android do rodape/login/cadastro/compartilhamento, modelo `MobileAppRelease`, tela Admin Ops e rota Caddy `/api/*`, mantendo o app mobile local intacto
- Evidencias de validacao local: `manage.py check`; `manage.py makemigrations --check --dry-run`; testes focados de pagina Android/Admin Ops/Caddy; suite Django completa `manage.py test --keepdb` com 160 testes OK; `flutter analyze`; `flutter test`; `flutter build apk --debug`; `flutter build apk --release` falhando sem signing conforme esperado; `flutter build apk --release` com keystore temporaria local e defines de producao gerando APK assinado; segredo/keystore temporarios removidos apos validacao
- Evidencias de validacao de producao: release ativa `1.0.1 (2)` criada em `gotrendlabs_mobile_app_releases` com arquivo `app_releases/android/gotrendlabs-android-1.0.1-2.apk`, SHA-256 `065c352e10d942d86c8665745fe91d374bd168db81377fd666c858fedbf8d186` e `file_size=55458673`; `curl -I -L https://gotrendlabs.com.br/media/app_releases/android/gotrendlabs-android-1.0.1-2.apk` retornou `HTTP/2 200`, `content-type: application/vnd.android.package-archive` e `content-length: 55458673`; download HTTPS recalculado com `shasum -a 256` retornou o mesmo SHA-256; apos recriar o container `proxy` para aplicar o `Caddyfile` versionado, `https://gotrendlabs.com.br/api/health` retornou `HTTP/2 200` com `{"status":"ok"}`, `https://gotrendlabs.com.br/api/markets` retornou JSON de mercados e `/app/android/latest.json` retornou a release ativa `1.0.1 (2)`.

## WFLOW-20260608-MOBILE-PUSH-NOTIFICATIONS-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-NOTIFY-001`, `FEAT-MOBILE-001`, `communications`, `future-mobile`
- Objetivo: iniciar push notifications mobile com FCM como arquitetura alvo, começando por provider `none`/dry-run/noop desligado por padrão
- Etapa atual: concluído; PR #63 mergeada em `main`, `GoTrendLabs CI and Deploy` run `27162536605` passou testes e deploy em 2026-06-08
- Artefatos afetados:
  - `apps/web/django/communications/`
  - `apps/api/backend_api/`
  - `apps/web/django/admin_ops/`
  - `apps/mobile/lib/src/features/push/`
  - `packages/contracts/openapi/gotrendlabs-api.json`
  - `docs/specs/`
- Bloqueios: envio FCM real depende de projeto Firebase, credencial fora do Git/Admin Ops, dependências Flutter Firebase e aprovação operacional explícita
- Iniciado em: 2026-06-08
- Atualizado em: 2026-06-08
- Encerrado em: 2026-06-08
- Retomada: evoluir para FCM real somente com projeto Firebase, credenciais em ambiente/secret manager, dependências Flutter Firebase e aprovação operacional explícita
- Reversão lógica: remover modelos/migration/serviços/endpoints/admin/templates push, retirar Flutter `features/push`, restaurar OpenAPI/specs/state e manter `gotrendlabs_user_notifications`/email intactos
- Evidências de validação local/remota: `manage.py check`; `manage.py makemigrations --check --dry-run`; `packages/contracts/export_openapi.py --check`; suíte Django completa `manage.py test --keepdb` com 155 testes OK; `flutter analyze`; `flutter test`; testes focados de push/Admin Ops/dashboard; `git diff --check`; FastAPI/Django locais reiniciados e `/admin-ops/` renderizou `Push mobile` em Saúde técnica; emulador Android `emulator-5554` executou o app com `GTL_PUSH_FAKE_TOKEN` e registrou `PushDevice` local em `gotrendlabs_push_devices`; GitHub Actions `GoTrendLabs CI and Deploy` run `27162536605` concluiu `test` e `deploy` com sucesso

## WFLOW-20260608-MOBILE-IOS-SIMULATOR-001

- Tipo: `change-feature`
- Status: `em_publicacao`
- Feature alvo: `FEAT-MOBILE-001`, `future-mobile`
- Objetivo: preparar o app Flutter mobile para iOS Simulator sem alterar contratos FastAPI nem regras de domínio
- Etapa atual: estrutura iOS gerada em `apps/mobile/ios`, Xcode/CocoaPods validados localmente, app executado no iPhone Simulator com bases locais via `127.0.0.1` e aguardando aprovação do usuário para abrir PR em português, mergear em `main` e acompanhar `GoTrendLabs CI and Deploy` quando disparado
- Artefatos afetados:
  - `apps/mobile/ios/`
  - `apps/mobile/.metadata`
  - `apps/mobile/README.md`
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/change-log-specs.md`
  - `docs/specs/state/integration-map.md`
  - `docs/specs/state/known-gaps.md`
- Bloqueios: nenhum local; PR, merge e monitoramento de produção dependem de aprovação explícita do usuário
- Iniciado em: 2026-06-08
- Atualizado em: 2026-06-08
- Encerrado em: pendente
- Retomada: após aprovação, stage/commit, push da branch `codex/mobile-ios-simulator-support`, abrir PR em português, mergear em `main`, acompanhar `GoTrendLabs CI and Deploy` se disparado e atualizar este registro para `concluido` ou `bloqueado`
- Reversão lógica: remover `apps/mobile/ios/`, retirar a plataforma iOS de `.metadata`, restaurar README/specs/state para escopo Android-only e manter contratos FastAPI inalterados
- Evidências de validação local: `flutter doctor -v` sem issues com Xcode 26.5 e CocoaPods 1.16.2; `flutter analyze` sem issues; `flutter test` com 16 testes OK; `flutter run -d 53BDA0A2-23E9-4F01-A468-593A2AF0C8A8 --dart-define=GTL_API_BASE_URL=http://127.0.0.1:8001 --dart-define=GTL_PUBLIC_WEB_BASE_URL=http://127.0.0.1:8000` abriu o app no iPhone 17 Simulator; `flutter run -d 207EDA52-ED42-4CCB-AD4E-35F0CAE5A29C` abriu o app no iPhone 17 Pro Max Simulator; screenshots confirmaram a tela mobile carregando dados locais da API

## WFLOW-20260607-MOBILE-ANDROID-MVP-001

- Tipo: `new-feature`
- Status: `em_publicacao`
- Feature alvo: `FEAT-MOBILE-001`, `future-mobile`
- Objetivo: implementar e polir o app Flutter Android do GoTrendLabs como cliente da FastAPI, com design dark-first editorial, feed, detalhe, auth, previsão, comentários, wallet, perfil, ranking, badges, alertas, busca, áreas pessoais e tela `Sobre`
- Etapa atual: implementação local validada; docs/specs reconciliados; aguardando aprovação do usuário para abrir PR em português, mergear em `main` e acompanhar o workflow de produção quando disparado
- Artefatos afetados:
  - `apps/mobile/`
  - `apps/mobile/lib/src/ui/`
  - `apps/mobile/lib/src/features/info/about_screen.dart`
  - `apps/mobile/test/about_screen_test.dart`
  - `apps/mobile/test/markets_screen_test.dart`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/integration-map.md`
  - `docs/specs/state/known-gaps.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `apps/mobile/README.md`
- Bloqueios: nenhum local; PR, merge e monitoramento de produção dependem de aprovação explícita do usuário
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Encerrado em: pendente
- Retomada: após aprovação, stage/commit, push da branch `feature/mobile-android-design-refresh`, abrir PR em português, mergear em `main`, acompanhar `GoTrendLabs CI and Deploy` e atualizar este registro para `concluido` ou `bloqueado`
- Reversão lógica: reverter o refresh visual em `apps/mobile`, remover a tela `Sobre`, filtros pessoais e componentes compartilhados novos, restaurar README/status/changelog/acceptance/integration map/workflow desta fatia e manter os contratos FastAPI sem alteração
- Evidências de validação local: `flutter pub get`; `flutter analyze` sem issues; `flutter test` com 16 testes OK; `flutter build apk --debug` gerou APK debug com aviso não bloqueante do Kotlin Gradle Plugin transitivo em `package_info_plus`/`share_plus`; APK instalado no `emulator-5554`; smoke visual em emulador para `Hoje`, `Mercados`, detalhe, alertas e `Sobre`; `Sobre` exibe apenas saúde da API, versão/build, pacote/plataforma e dados seguros da conta, sem endereço de API/web, token, segredo ou ID interno; contratos OpenAPI e regras de domínio permanecem inalterados

## WFLOW-20260607-MOBILE-SPECS-SKILLS-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`, `future-mobile`
- Objetivo: criar specs e skills locais para iniciar o app Flutter Android do GoTrendLabs com design mobile inspirado nas referências fornecidas pelo usuário e governança docs/memória
- Etapa atual: concluido; specs mobile criadas, skills mobile adicionadas, README mobile atualizado, estado/changelog/integration map/known gaps alinhados e projeto Flutter mantido como próxima etapa
- Artefatos afetados:
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/features/mobile-mvp.md`
  - `docs/specs/features/mobile-ux.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/change-log-specs.md`
  - `docs/specs/state/integration-map.md`
  - `docs/specs/state/known-gaps.md`
  - `apps/mobile/README.md`
  - `tools/skills/gotrendlabs/`
- Bloqueios: nenhum para specs; antes de login persistente falta decisão técnica de autenticação mobile segura
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Encerrado em: 2026-06-07
- Retomada: revisar specs com o usuário e criar o projeto Flutter em `apps/mobile` quando aprovado
- Reversão lógica: remover as specs/skills mobile criadas nesta fatia e restaurar `apps/mobile/README.md` como reserva sem spec Flutter
- Evidências de validação: revisão documental contra skills mobile, arquitetura existente e referências visuais fornecidas; sem testes executáveis porque não houve código Flutter

## WFLOW-20260607-ADMIN-CONTRACTS-TIMELINE-001

- Tipo: `change-feature`
- Status: `em_validacao`
- Feature alvo: `FEAT-MARKET-001`, `admin-ops`
- Objetivo: adicionar painel administrativo read-only para organização operacional de contratos/mercados ativos e pendentes
- Etapa atual: implementação local concluída; aguardando publicação via PR e validação do workflow de produção
- Artefatos afetados:
  - `apps/web/django/admin_ops/views.py`
  - `apps/web/django/admin_ops/templates/admin_ops/contracts.html`
  - `apps/web/django/admin_ops/templates/admin_ops/markets.html`
  - `apps/web/static/css/gotrendlabs.css`
  - `config/urls.py`
  - `tests/test_web_smoke.py`
  - `docs/specs/architecture/admin-ops.md`
  - `docs/specs/architecture/backend-api.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
- Bloqueios: nenhum
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Retomada: após aprovação, abrir PR em português, mergear em `main`, acompanhar `GoTrendLabs CI and Deploy` e atualizar este registro para `concluido` ou `bloqueado`
- Reversão lógica: remover rota `/admin-ops/contracts/`, botão no browse de mercados, helper de timeline no Django, template/CSS do painel e teste focado
- Evidências de validação local: `manage.py check`, `makemigrations --check --dry-run`, teste focado `tests.test_web_smoke.WebSmokeTests.test_admin_contracts_timeline_uses_active_market_contract_dates`, render manual com API mockada e `git diff --check`

## WFLOW-20260607-WEB-ASSETS-LAYOUT-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `frontend-web`, `repo-layout`
- Objetivo: mover templates e assets compartilhados da web para `apps/web/` sem mover apps Django
- Etapa atual: concluido; `templates/` movido para `apps/web/templates/`, `static/` movido para `apps/web/static/`, settings/docs/skills atualizados e apps Django preservados nos caminhos historicos
- Artefatos afetados:
  - `apps/web/templates/`
  - `apps/web/static/`
  - `config/settings.py`
  - `README.md`
  - `docs/specs/architecture/frontend-web.md`
  - `docs/specs/state/feature-changelog.md`
  - `tools/skills/gotrendlabs/`
- Bloqueios: nenhum
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Encerrado em: 2026-06-07
- Retomada: próxima reorganização web deve avaliar se vale mover apps Django para `apps/web/django/`, preservando `AppConfig.label`, migrations e imports
- Reversão lógica: mover `apps/web/templates/` de volta para `templates/`, `apps/web/static/` de volta para `static/` e restaurar `TEMPLATES["DIRS"]`/`STATICFILES_DIRS`
- Evidências de validação: `manage.py check`, `manage.py findstatic css/gotrendlabs.css js/gotrendlabs.js brand/gtl-logo.svg`, suite `manage.py test --keepdb` com 150 testes OK e `manage.py collectstatic --noinput`

## WFLOW-20260607-OPS-LAYOUT-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `infra-deploy-mvp`, `repo-layout`
- Objetivo: mover deploy, scripts e Docker local para `ops/` como terceira etapa da reorganização do monorepo
- Etapa atual: concluido; deploy de produção movido para `ops/deploy/production/`, scripts operacionais movidos para `ops/scripts/`, Compose local atualizado para `ops/docker/postgres/data/`, README/specs/skills/testes alinhados e workflow SSM ajustado para atualizar o checkout remoto antes de chamar o script movido
- Artefatos afetados:
  - `ops/deploy/production/`
  - `ops/scripts/`
  - `ops/docker/README.md`
  - `docker-compose.yml`
  - `.github/workflows/deploy.yml`
  - `tests/test_web_smoke.py`
  - `docs/specs/state/feature-changelog.md`
  - `tools/skills/gotrendlabs/`
- Bloqueios: nenhum
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Encerrado em: 2026-06-07
- Retomada: próxima reorganização deve preparar a camada web Django com cuidado para preservar labels, migrations, templates e static
- Reversão lógica: restaurar `deploy/production/`, `scripts/ops/` e `docker/postgres/data/` como caminhos oficiais e reverter referências em workflow, Compose, docs e testes
- Evidências de validação: `manage.py check`, `docker compose config --quiet`, `docker compose -f ops/deploy/production/docker-compose.yml config --quiet --no-env-resolution`, suite `manage.py test --keepdb` com 150 testes OK e correção pós-merge para o checkout SSM antigo que ainda não continha `ops/deploy/production/deploy.sh`

## WFLOW-20260607-FASTAPI-LAYOUT-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `backend-api`, `repo-layout`
- Objetivo: mover fisicamente o runtime FastAPI para `apps/api/backend_api/` como segunda etapa da reorganização do monorepo
- Etapa atual: concluido; pacote FastAPI movido, imports e patches atualizados para `apps.api.backend_api`, comando `uvicorn` local/producao alinhado, specs/skills/docs atualizados e validação local concluida
- Artefatos afetados:
  - `apps/api/backend_api/`
  - `ops/deploy/production/docker-compose.yml`
  - `tests/test_web_smoke.py`
  - `docs/specs/architecture/backend-api.md`
  - `docs/specs/state/feature-changelog.md`
  - `tools/skills/gotrendlabs/`
- Bloqueios: nenhum
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Encerrado em: 2026-06-07
- Retomada: próxima reorganização deve mover `ops/` ou iniciar a preparação da camada web, sem misturar com mudanças funcionais
- Reversão lógica: selecionar provider `smtp` ou desabilitar `email_enabled`, mantendo outbox para auditoria.
- Evidências de validação: `manage.py check`, `manage.py makemigrations --check --dry-run`, suite `manage.py test --keepdb`, `git diff --check`, `send_resend_test_email --dry-run` e teste real retornando erro Resend de domínio não verificado.

## WFLOW-20260606-SECURITY-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`, `FEAT-OPSLOG-001`, `FEAT-MARKET-001`, `infra-deploy-mvp`
- Objetivo: executar auditoria local de seguranca e endurecer endpoints publicos, redirects, uploads Admin Ops, headers de media e defaults de producao sem alterar regras funcionais de dominio
- Etapa atual: concluido; auditoria local registrada em `docs/audits/security-audit-2026-06-06.md`, hardening aplicado, specs/state alinhados e `.env.prod.example` explicita `GOTRENDLABS_RATE_LIMITS_ENABLED=1`
- Artefatos afetados:
  - `backend_api/main.py`
  - `config/settings.py`
  - `accounts/`, `core/views.py`, `markets/views.py`
  - `admin_ops/views.py`
  - `ops/deploy/production/Caddyfile`, `.env.prod.example`, `ops/deploy/production/README.md`
  - `tests/test_web_smoke.py`
  - `docs/audits/security-audit-2026-06-06.md`
  - `docs/specs/state/`
- Bloqueios: atualizacao de dependencias vulneraveis segue pendente porque o indice local de pacotes ainda nao disponibiliza versoes corrigidas de Pillow/Starlette/python-dotenv
- Iniciado em: 2026-06-06
- Atualizado em: 2026-06-06
- Encerrado em: 2026-06-06
- Retomada: substituir rate limit em memoria por store distribuido quando houver multiplas instancias, atualizar dependencias assim que o indice permitir e acompanhar alertas de scanner no CI
- Reversão lógica: desligar temporariamente `GOTRENDLABS_RATE_LIMITS_ENABLED=0` apenas em contingencia, manter `DJANGO_DEBUG=0` e reverter validacao de upload/redirects somente por PR corretiva com teste
- Evidências de validação: `manage.py check`, `check --deploy` com variaveis de producao, `tests.test_web_smoke.SecurityHardeningTests` com 7 testes OK, suite `tests.test_web_smoke --keepdb` com 150 testes OK, Bandit sem achados High e `pip-audit` registrando pendencias de pacote sem versao corrigida disponivel no indice local

## Modelo

```md
## WFLOW-YYYYMMDD-001

- Tipo: `change-feature`
- Status: `aberto`
- Feature alvo: `FEAT-XXX`
- Objetivo: descrição curta
- Etapa atual: etapa do workflow canônico
- Artefatos afetados:
  - `docs/specs/features/example.md`
- Bloqueios: nenhum
- Iniciado em: YYYY-MM-DD
- Atualizado em: YYYY-MM-DD
- Encerrado em: pendente
- Retomada: próxima ação objetiva
- Reversão lógica: como cancelar ou substituir sem apagar histórico
```

## WFLOW-20260604-GOTRENDLABS-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-I18N-001`, `FEAT-WALLET-001`, `FEAT-AUTH-001`, `FEAT-OPSLOG-001`
- Objetivo: substituir profundamente a identidade da plataforma por GoTrendLabs, com moeda GTL Credits/GT₵ e contratos técnicos `_gtl`
- Etapa atual: concluído; rebrand de código, docs, deploy, migrations de schema/domínio controlado, assets GTL, favicon de navegador, correções de mídia pública, topo Admin Ops e validação local/cloud finalizados em 2026-06-05
- Artefatos afetados:
  - `backend_api/`, `accounts/`, `markets/`, `admin_ops/`, `agents/`, `system_logs/`
  - `templates/`, `static/css/gotrendlabs.css`, `static/js/gotrendlabs.js`, `static/brand/`
  - `ops/deploy/production/`, `.github/workflows/deploy.yml`, `.env.example`, `.env.prod.example`
  - `docs/specs/`, `tools/skills/gotrendlabs/`
- Bloqueios: nenhum
- Iniciado em: 2026-06-04
- Atualizado em: 2026-06-05
- Encerrado em: 2026-06-05
- Retomada: evoluir i18n por catálogos em workflow futuro
- Reversão lógica: restaurar backup `git-all-refs.bundle` e dump local criado antes da mudança; em produção, reverter por snapshot RDS e app dir anterior se o deploy for iniciado
- Evidências de validação: `manage.py check`, `makemigrations --check --dry-run`, suíte completa `129/129` com `--keepdb`, scans de resíduos em código/schema local e cloud, `docker compose config`, containers `gotrendlabs-*` em execução, `maintenance_enabled=False`, `market_thumbnails=39`, `badge_images=30`, domínios `gotrendlabs.com.br`, `www.gotrendlabs.com.br`, `gotrendlabs.com` e `www.gotrendlabs.com` com HTTP 200 e SSL válido; PR #43 publicou favicon SVG nos templates base, GitHub Actions `GoTrendLabs CI and Deploy` concluiu `test` e `deploy` com sucesso e produção respondeu os assets `gtl-constellation-mark-*.svg` como `image/svg+xml`.

## WFLOW-20260528-PUBLIC-COPY-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`, `FEAT-AUTH-001`, `FEAT-REP-001`, `FEAT-SUGGEST-001`
- Objetivo: simplificar a home pública e alinhar a linguagem de produto para tom claro, social e confiável
- Etapa atual: concluído
- Artefatos afetados:
  - `accounts/templates/accounts/`
  - `core/templates/core/`
  - `markets/templates/markets/detail.html`
  - `templates/components/market_card.html`
  - `static/css/gotrendlabs.css`
  - `static/js/gotrendlabs.js`
  - `docs/specs/`
  - `PRODUCT.md`
  - `DESIGN.md`
- Bloqueios: nenhum
- Iniciado em: 2026-05-28
- Atualizado em: 2026-05-28
- Encerrado em: 2026-05-28
- Retomada: extrair strings públicas para `FEAT-I18N-001` quando a internacionalização for priorizada
- Reversão lógica: reintroduzir blocos da home e labels anteriores por nova mudança de UI, preservando specs desta decisão como histórico

## WFLOW-20260524-RETENTION-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-OPSLOG-001`, `FEAT-AIAGENT-001`
- Objetivo: tornar configurável no Admin Ops a retenção de logs técnicos e auditoria de agentes IA
- Etapa atual: concluído
- Artefatos afetados:
  - `admin_ops/`
  - `backend_api/daemon_services.py`
  - `system_logs/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-24
- Atualizado em: 2026-05-24
- Encerrado em: 2026-05-24
- Retomada: acompanhar em produção o primeiro ciclo do daemon após deploy para validar contadores de prune
- Reversão lógica: ocultar campos de retenção no Admin Ops e voltar defaults de 90 dias, preservando colunas em `gotrendlabs_site_config` para compatibilidade

## WFLOW-20260517-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `sistema-documental`
- Objetivo: criar base canônica de specs, contratos, arquitetura, testes, estado e skills
- Etapa atual: concluído
- Artefatos afetados:
  - `docs/specs/`
  - `tools/skills/gotrendlabs/`
  - `docs/guides/ia-spec-workflow.md`
- Bloqueios: nenhum
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: usar novos workflows para mudanças futuras
- Reversão lógica: substituir por novo workflow que revise a estrutura documental

## WFLOW-20260520-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-OPSLOG-001`
- Objetivo: implementar daemon operacional com regras temporizadas centralizadas no backend
- Etapa atual: concluído
- Artefatos afetados:
  - `backend_api/`
  - `system_logs/management/commands/`
  - `admin_ops/templates/admin_ops/dashboard.html`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: daemon ja possui container de producao no deploy EC2; proxima evolucao e alertas externos/observabilidade
- Reversão lógica: desativar execução do comando `run_gotrendlabs_daemon` preservando serviços backend e eventos já registrados

## WFLOW-20260520-018

- Tipo: `change-infra`
- Status: `concluido`
- Feature alvo: `infra-deploy-mvp`, `FEAT-OPSLOG-001`
- Objetivo: preparar deploy MVP em AWS EC2 com Docker Compose, RDS gerenciado, Caddy HTTPS e daemon em container dedicado
- Etapa atual: concluído
- Artefatos afetados:
  - `Dockerfile`
  - `.dockerignore`
  - `.env.prod.example`
  - `ops/deploy/production/`
  - `config/settings.py`
  - `README.md`
  - `docs/specs/spec_prediction_social_market_pt.md`
  - `docs/specs/decisions/ADR-0003-ec2-compose-rds-mvp.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: configurar EC2/RDS reais, preencher `.env.prod` fora do Git, apontar DNS e executar `ops/deploy/production/deploy.sh`
- Reversão lógica: remover artefatos de deploy de producao e voltar settings para defaults locais, preservando specs/ADR como decisão substituída

## WFLOW-20260521-001

- Tipo: `change-infra`
- Status: `concluido`
- Feature alvo: `infra-deploy-mvp`, `FEAT-OPSLOG-001`
- Objetivo: provisionar a base AWS real do MVP com EC2 ARM, RDS PostgreSQL privado, SSM, CloudWatch minimo, segredos/configuracao e role OIDC para GitHub Actions
- Etapa atual: concluido
- Artefatos afetados:
  - `ops/deploy/production/README.md`
  - `ops/deploy/production/deploy.sh`
  - `.github/workflows/deploy.yml`
  - `docs/specs/decisions/ADR-0003-ec2-compose-rds-mvp.md`
  - `docs/specs/state/`
- Bloqueios: nenhum para a infra base; deploy da aplicacao depende de `.env.prod` criado fora do Git na EC2
- Iniciado em: 2026-05-21
- Atualizado em: 2026-05-21
- Encerrado em: 2026-05-21
- Retomada: criar `.env.prod` na EC2, configurar secrets/variables do GitHub, executar primeiro deploy e apontar DNS quando houver dominio
- Reversão lógica: remover recursos AWS provisionados em `us-east-1` usando tags `Project=gotrendlabs`, `Environment=prod`, `ManagedBy=codex-mcp`, preservando ADR como decisão substituída se a estratégia mudar

## WFLOW-20260521-002

- Tipo: `change-infra`
- Status: `concluido`
- Feature alvo: `infra-deploy-mvp`, `FEAT-OPSLOG-001`
- Objetivo: endurecer a autenticacao OIDC do GitHub Actions para o deploy via SSM, adicionando preflight de configuracao e prova explicita da identidade AWS assumida
- Etapa atual: concluido
- Artefatos afetados:
  - `.github/workflows/deploy.yml`
  - `ops/deploy/production/README.md`
  - `docs/specs/state/workflow-runs.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/integration-map.md`
  - `docs/specs/state/known-gaps.md`
- Bloqueios: o deploy automatico ainda depende de `.env.prod` existente na EC2 e do repositório GitHub possuir as variables esperadas
- Iniciado em: 2026-05-21
- Atualizado em: 2026-05-21
- Encerrado em: 2026-05-21
- Retomada: executar o workflow na `main` com `ENABLE_PROD_DEPLOY=1` e validar a etapa `Verify assumed AWS identity` antes do primeiro deploy automatico real
- Reversão lógica: voltar o workflow para a leitura exclusiva de secrets e remover o preflight, preservando esta entrada como histórico de endurecimento operacional

## WFLOW-20260522-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AIAGENT-001`
- Objetivo: implementar agentes IA oficiais para comentários, previsão bot controlada, Admin Ops, saúde técnica e auditoria
- Etapa atual: concluído; app `agents`, ciclo IA, Admin Ops, auditoria, saúde técnica, métricas humano/bot, exclusão de bots, simulações Bedrock e ajustes UX finais validados localmente em 2026-05-23
- Artefatos afetados:
  - `agents/`
  - `backend_api/`
  - `admin_ops/`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-23
- Encerrado em: 2026-05-23
- Retomada: acompanhar deploy em `main`, validar migrations em produção e observar primeiro ciclo daemon com IA desligada por padrão
- Reversão lógica: desativar `ai_agents_enabled` em `gotrendlabs_site_config`, manter auditoria histórica e remover integração do ciclo IA por workflow substituto

## WFLOW-20260520-002

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-WALLET-001`, `FEAT-AUTH-001`
- Objetivo: padronizar símbolo público `GT₵`, expor métricas educativas na home e reorganizar rodapé/Admin Ops
- Etapa atual: concluído
- Artefatos afetados:
  - `backend_api/main.py`
  - `core/domain_client.py`
  - `accounts/api_client.py`
  - `core/templates/core/home.html`
  - `templates/base.html`
  - `templates/components/footer.html`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: evoluir um formatador central de moeda/i18n quando `FEAT-I18N-001` avançar
- Reversão lógica: restaurar labels visíveis antigos, remover métricas públicas da home e voltar Admin Ops para a navegação anterior preservando contratos internos `_gtl`

## WFLOW-20260517-002

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `sistema-documental`
- Objetivo: adicionar changelog por feature e skills técnicas por stack
- Etapa atual: concluído
- Artefatos afetados:
  - `docs/specs/state/feature-changelog.md`
  - `tools/skills/gotrendlabs/gotrendlabs-django-web/`
  - `tools/skills/gotrendlabs/gotrendlabs-fastapi-domain/`
  - `tools/skills/gotrendlabs/gotrendlabs-postgres-modeling/`
  - `tools/skills/gotrendlabs/gotrendlabs-ops-scheduler-communications/`
  - `docs/guides/ia-spec-workflow.md`
- Bloqueios: nenhum
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: usar skills técnicas junto do orquestrador
- Reversão lógica: substituir por novo workflow que altere ou remova skills específicas

## WFLOW-20260517-003

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `sistema-documental`
- Objetivo: adicionar governança de workflows, reforçar testes no guia e revisar eficácia das skills
- Etapa atual: concluído
- Artefatos afetados:
  - `docs/specs/workflows/`
  - `docs/specs/state/workflow-runs.md`
  - `docs/specs/state/workflow-checklists.md`
  - `docs/specs/state/governance-review.md`
  - `tools/skills/gotrendlabs/gotrendlabs-workflow-governor/`
  - `tools/skills/gotrendlabs/README.md`
  - `docs/guides/ia-spec-workflow.md`
  - `tools/skills/gotrendlabs/*/SKILL.md`
- Bloqueios: nenhum
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: abrir novo workflow para qualquer mudança multi-documento
- Reversão lógica: criar workflow substituto que altere o processo canônico

## WFLOW-20260517-004

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `sistema-documental`
- Objetivo: adicionar skills de arquiteto de software/segurança e engenheiro de testes, atualizando fluxos obrigatórios
- Etapa atual: concluído
- Artefatos afetados:
  - `tools/skills/gotrendlabs/gotrendlabs-software-architect/`
  - `tools/skills/gotrendlabs/gotrendlabs-test-engineer/`
  - `tools/skills/gotrendlabs/README.md`
  - `docs/specs/workflows/`
  - `docs/specs/state/workflow-checklists.md`
  - `docs/specs/state/integration-map.md`
  - `docs/guides/ia-spec-workflow.md`
- Bloqueios: nenhum
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: usar `gotrendlabs-software-architect` antes de mudanças relevantes e `gotrendlabs-test-engineer` para testes executáveis
- Reversão lógica: criar workflow substituto que ajuste obrigatoriedade ou escopo das skills

## WFLOW-20260517-005

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`
- Objetivo: mover autenticação/cadastro/sessão para `backend-api` FastAPI e manter Django como web layer consumidor
- Etapa atual: concluído
- Artefatos afetados:
  - `backend_api/`
  - `accounts/`
  - `config/settings.py`
  - `tests/test_web_smoke.py`
  - `requirements.txt`
  - `docs/specs/features/auth-and-session.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/known-gaps.md`
- Bloqueios: login social real depende de credenciais OAuth e decisão de provedor/configuração
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: implementar OAuth Google/Facebook real e endurecer cookies/tokens para ambiente não local
- Reversão lógica: substituir por workflow que troque o contrato de auth/session mantendo a migração de dados explícita

## WFLOW-20260517-006

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-WALLET-001`, `FEAT-REP-001`
- Objetivo: implementar núcleo completo do usuário com perfil, wallet, ledger inicial, reputação base, badges e ranking via FastAPI
- Etapa atual: concluído
- Artefatos afetados:
  - `backend_api/`
  - `accounts/`
  - `profiles/`
  - `wallet/`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/wallet-and-ledger.md`
  - `docs/specs/features/reputation-and-ranking.md`
  - `docs/specs/state/implementation-status.md`
  - `docs/specs/state/feature-changelog.md`
  - `docs/specs/state/known-gaps.md`
- Bloqueios: fórmula avançada de reputação depende de previsões e resolução de mercados
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: implementar previsão/stake usando o saldo derivado do ledger e depois resolução/payout/reputação avançada
- Reversão lógica: criar workflow substituto que migre ou remova tabelas de núcleo do usuário mantendo trilha de ledger

## WFLOW-20260517-007

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-WALLET-001`
- Objetivo: adicionar projeção `gotrendlabs_wallet_balances` para leitura rápida de saldo mantendo ledger como fonte auditável
- Etapa atual: concluído
- Artefatos afetados:
  - `accounts/`
  - `backend_api/`
  - `tests/test_web_smoke.py`
  - `docs/specs/contracts/wallet-ledger.md`
  - `docs/specs/features/wallet-and-ledger.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: usar helper ledger + balance ao implementar stake, refund, payout e ajustes manuais
- Reversão lógica: reconstruir a projeção a partir do ledger ou substituir por nova projeção versionada

## WFLOW-20260517-008

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`
- Objetivo: adicionar aceite obrigatório de política de uso, edição de perfil e exclusão lógica de conta
- Etapa atual: concluído
- Artefatos afetados:
  - `accounts/`
  - `backend_api/`
  - `profiles/`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/auth-and-session.md`
  - `docs/specs/state/`
- Bloqueios: confirmação de email em alteração de endereço fica para communications
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: implementar confirmação de email, política versionada administrável e OAuth real
- Reversão lógica: criar workflow substituto que reative contas ou migre estados sem apagar histórico

## WFLOW-20260517-009

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`
- Objetivo: mover feed e detalhe de mercado para FastAPI/Postgres mantendo fixture apenas como fallback
- Etapa atual: concluído
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `core/`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/market-feed.md`
  - `docs/specs/features/market-detail.md`
  - `docs/specs/state/`
- Bloqueios: admin CRUD, cálculo real de probabilidades e comentários reais ficam para features futuras
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: implementar FEAT-PRED-001 usando os mercados persistidos como base
- Reversão lógica: fixture permanece disponível como fallback; uma reversão pode desativar consumo da API no Django sem apagar tabelas

## WFLOW-20260518-001

- Tipo: `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-SUGGEST-001`
- Objetivo: implementar primeira fatia real de filas operacionais para sugestões e feedback recompensável
- Etapa atual: concluído; `.venv/bin/python manage.py test` executado com sucesso em 2026-05-18
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `core/`
  - `admin_ops/`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/market-suggestions.md`
  - `docs/specs/features/wallet-and-ledger.md`
  - `docs/specs/contracts/wallet-ledger.md`
  - `docs/specs/contracts/domain-events.md`
  - `docs/specs/architecture/admin-ops.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: próxima fatia pode adicionar event bus assíncrono, histórico público de feedback, comunicações transacionais e moderação de comentários
- Reversão lógica: substituir por workflow que desative endpoints e mantenha dados históricos de filas preservados

## WFLOW-20260518-010

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`, `admin-ops`
- Objetivo: implementar admin real de mercados e taxonomia com FastAPI/Postgres como autoridade e Django como camada web
- Etapa atual: concluído
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `admin_ops/`
  - `accounts/api_client.py`
  - `accounts/session.py`
  - `tests/test_web_smoke.py`
  - `docs/specs/architecture/admin-ops.md`
  - `docs/specs/contracts/market-lifecycle.md`
  - `docs/specs/state/`
- Bloqueios: resolução real, payout, sugestões, feedback, moderação avançada, scheduler e gestão de operadores ficam para features próprias
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: implementar FEAT-PRED-001 ou FEAT-RES-001 usando mercados persistidos e auditados
- Reversão lógica: manter tabelas e eventos; desativar rotas admin ou ocultar ações no Django se for preciso suspender operação

## WFLOW-20260518-011

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`, `admin-ops`
- Objetivo: corrigir regras de opções por tipo de mercado e filtros do browse administrativo
- Etapa atual: concluído
- Artefatos afetados:
  - `backend_api/`
  - `admin_ops/`
  - `accounts/api_client.py`
  - `static/`
  - `tests/test_web_smoke.py`
  - `docs/specs/architecture/admin-ops.md`
  - `docs/specs/contracts/market-lifecycle.md`
  - `docs/specs/state/`
- Bloqueios: probabilidades reais continuam dependentes de FEAT-PRED-001
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: evoluir cálculo real de probabilidade e stake em FEAT-PRED-001
- Reversão lógica: voltar o Admin Ops para options fixas antigas e remover o filtro por status da query administrativa

## WFLOW-20260518-012

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`, `admin-ops`
- Objetivo: corrigir UX e validação do editor administrativo de mercado
- Etapa atual: concluído
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `admin_ops/`
  - `static/`
  - `templates/`
  - `config/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: histórico superado; daemon operacional implementado em `WFLOW-20260520-001`
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: histórico superado; evoluir supervisor/deploy do daemon se necessário
- Reversão lógica: manter campos no banco e ocultar controles avançados no editor se necessário

## WFLOW-20260518-013

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`, `admin-ops`
- Objetivo: melhorar objetividade do formulário administrativo, feedback de sucesso e regra de fechamento manual
- Etapa atual: concluído
- Artefatos afetados:
  - `backend_api/`
  - `admin_ops/`
  - `accounts/api_client.py`
  - `static/`
  - `templates/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: histórico superado; daemon operacional implementado em `WFLOW-20260520-001`
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: histórico superado; evoluir supervisor/deploy do daemon se necessário
- Reversão lógica: ocultar botão de fechamento manual e desabilitar endpoint `/admin/markets/{slug}/lock` se necessário

## WFLOW-20260518-014

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `admin-ops`
- Objetivo: redesenhar Admin Ops de taxonomia e substituir exclusão física por bloqueio lógico de categorias/subcategorias
- Etapa atual: concluído
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `admin_ops/`
  - `accounts/api_client.py`
  - `static/`
  - `templates/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: evoluir ordenação, tradução e políticas de publicação da taxonomia quando houver i18n operacional
- Reversão lógica: manter campos de bloqueio e ocultar ações de bloqueio/desbloqueio no Admin Ops se a operação precisar ser suspensa

## WFLOW-20260518-015

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `admin-ops`
- Objetivo: vincular seleção de categoria/subcategoria do mercado à taxonomia persistida e refinar dark mode do editor
- Etapa atual: concluído
- Artefatos afetados:
  - `admin_ops/`
  - `static/`
  - `templates/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: evoluir busca/combobox de taxonomia se o volume de categorias crescer
- Reversão lógica: voltar campos de categoria/subcategoria para texto livre apenas no Django, mantendo validação FastAPI de bloqueio

## WFLOW-20260518-016

- Tipo: `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-PRED-001`
- Objetivo: implementar primeira fatia real de previsão e stake com uma previsão por usuário/mercado
- Etapa atual: concluído; `.venv/bin/python manage.py test` executado com sucesso em 2026-05-18
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `accounts/api_client.py`
  - `config/urls.py`
  - `static/js/gotrendlabs.js`
  - `tests/test_web_smoke.py`
  - `docs/specs/state/`
- Bloqueios: resolução, payout real, reputação avançada, comunicações e refund/cancelamento ficam fora desta entrega
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: implementar FEAT-RES-001 usando `gotrendlabs_predictions`, `prediction_stake_lock` e snapshots de entrada como base
- Reversão lógica: desativar rota de confirmação no Django e endpoint FastAPI, preservando `gotrendlabs_predictions` e ledger para auditoria/migração

## WFLOW-20260518-017

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-PRED-001`, `FEAT-MARKET-001`, `FEAT-MARKET-002`
- Objetivo: alinhar gráficos de consenso, UX de previsão bloqueada/visitante e fallback local em Postgres
- Etapa atual: concluído; `.venv/bin/python manage.py test` executado com sucesso em 2026-05-18
- Artefatos afetados:
  - `backend_api/`
  - `core/`
  - `markets/`
  - `templates/components/market_card.html`
  - `static/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: histórico materializado de snapshots, realtime/websocket e analytics avançado ficam fora desta entrega
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: criar tabela de snapshots se o volume de previsões tornar caro recalcular séries a partir de `gotrendlabs_predictions`
- Reversão lógica: ocultar sparklines nos templates preservando snapshots atuais de opção e registros de previsão

## WFLOW-20260518-018

- Tipo: `bugfix`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`, `FEAT-PRED-001`
- Objetivo: corrigir edição administrativa de mercado quando opções já possuem previsões vinculadas
- Etapa atual: concluído; `.venv/bin/python manage.py test` executado com sucesso em 2026-05-18
- Artefatos afetados:
  - `backend_api/`
  - `accounts/api_client.py`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: criar operação explícita de desativação/arquivamento de opção quando a UX administrativa exigir retirar opções já usadas
- Reversão lógica: bloquear edição de opções em mercados com previsões, preservando edição dos demais campos

## WFLOW-20260518-019

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-PRED-001`, `FEAT-MARKET-001`, `FEAT-MARKET-002`
- Objetivo: usar probabilidade decimal exata como fonte de verdade e truncar apenas a apresentação inteira
- Etapa atual: concluído; colunas inteiras redundantes removidas; `.venv/bin/python manage.py test` executado com sucesso em 2026-05-18
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `core/`
  - `admin_ops/`
  - `templates/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: histórico materializado de snapshots segue fora desta entrega
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: criar tabela de snapshots caso a evolução visual precise consultar histórico já materializado
- Reversão lógica: continuar serializando `probability_exact`, mas voltar templates a usar os inteiros se houver problema visual temporário

## WFLOW-20260518-020

- Tipo: `bugfix`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `admin-ops`
- Objetivo: recuperar tela administrativa de mercados após remoção de colunas inteiras e documentar fallback operacional
- Etapa atual: concluído; `.venv/bin/python manage.py test` executado com sucesso em 2026-05-18
- Artefatos afetados:
  - `admin_ops/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: observar logs da FastAPI depois de futuras migrations destrutivas e considerar healthcheck/versionamento de schema
- Reversão lógica: remover fallback local do browse administrativo se a operação passar a exigir falha explícita quando a API estiver fora

## WFLOW-20260518-021

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `admin-ops`
- Objetivo: simplificar ações da listagem administrativa removendo CTA público da tabela
- Etapa atual: concluído; teste de renderização do Admin Ops atualizado em 2026-05-18
- Artefatos afetados:
  - `admin_ops/templates/admin_ops/markets.html`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: se operadores precisarem abrir público diretamente da lista, reavaliar como ação contextual por status
- Reversão lógica: reintroduzir CTA público na tabela sem alterar contratos de domínio

## WFLOW-20260518-022

- Tipo: `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-COMMENT-001`
- Objetivo: implementar comentários reais em mercados com reações e moderação básica auditável
- Etapa atual: concluído; `.venv/bin/python manage.py test` executado com sucesso em 2026-05-18
- Artefatos afetados:
  - `docs/specs/features/comments.md`
  - `markets/`
  - `backend_api/`
  - `accounts/api_client.py`
  - `admin_ops/`
  - `tests/test_web_smoke.py`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: evoluir denúncias por usuários, paginação, edição/exclusão pelo autor ou respostas/thread quando forem priorizados
- Reversão lógica: ocultar formulários e ações de comentário mantendo tabelas históricas preservadas para auditoria/migração

## WFLOW-20260518-023

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`
- Objetivo: registrar filtros rápidos funcionais, curtidas nos cards e regra de destaque/fallback do feed
- Etapa atual: concluído; specs e estado documental atualizados em 2026-05-18
- Artefatos afetados:
  - `docs/specs/features/market-feed.md`
  - `docs/specs/architecture/frontend-web.md`
  - `docs/specs/spec_prediction_social_market_pt.md`
  - `docs/specs/state/`
  - `README.md`
- Bloqueios: nenhum
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: se favoritos por usuário forem priorizados, criar nova feature/contrato em vez de reaproveitar `is_featured`
- Reversão lógica: manter `GET /markets` estável e remover apenas ordenações client-side/chips visuais se houver regressão de UX

## WFLOW-20260519-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`, `FEAT-SUGGEST-001`
- Objetivo: adicionar reCAPTCHA v2 checkbox ao cadastro e aos envios guest de sugestão/feedback
- Etapa atual: concluído; testes automatizados executados em 2026-05-19
- Artefatos afetados:
  - `backend_api/`
  - `accounts/`
  - `core/`
  - `templates/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-19
- Atualizado em: 2026-05-19
- Encerrado em: 2026-05-19
- Retomada: configurar `RECAPTCHA_SITE_KEY` e `RECAPTCHA_SECRET_KEY` por ambiente e ativar `RECAPTCHA_ENABLED=1`
- Reversão lógica: desativar `RECAPTCHA_ENABLED` sem remover contratos ou campos opcionais

## WFLOW-20260519-002

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-REP-001`
- Objetivo: implementar badges administráveis com catálogo público e concessão automática por regras controladas
- Etapa atual: concluído; `python manage.py test` executado com sucesso em 2026-05-19
- Artefatos afetados:
  - `docs/specs/features/reputation-and-ranking.md`
  - `docs/specs/contracts/reputation-ranking.md`
  - `docs/specs/architecture/`
  - `accounts/`
  - `backend_api/`
  - `admin_ops/`
  - `core/`
  - `profiles/`
  - `tests/test_web_smoke.py`
- Bloqueios: nenhum
- Iniciado em: 2026-05-19
- Atualizado em: 2026-05-19
- Encerrado em: 2026-05-19
- Retomada: evoluir raridade, temporadas, compartilhamento completo de badge ou reprocessamento administrativo em lote quando priorizado
- Reversão lógica: ocultar rotas/telas de badges administráveis e manter tabelas novas preservadas para migração futura

## WFLOW-20260519-003

- Tipo: `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`
- Objetivo: implementar métricas operacionais de visualizações e compartilhamentos por mercado
- Etapa atual: concluído; `.venv/bin/python manage.py test` e testes focados do Admin Ops executados com sucesso em 2026-05-19
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `core/`
  - `accounts/api_client.py`
  - `admin_ops/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-19
- Atualizado em: 2026-05-19
- Encerrado em: 2026-05-19
- Retomada: evoluir para deduplicação ou analytics por origem quando priorizado
- Reversão lógica: remover exibição/admin e descontinuar incrementos mantendo colunas zeráveis para migração futura

## WFLOW-20260519-004

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`, `FEAT-WALLET-001`
- Objetivo: implementar gestão administrativa de usuários cadastrados no Admin Ops
- Etapa atual: concluído; suíte `.venv/bin/python manage.py test` executada com sucesso em 2026-05-19 após refinamentos de layout/menu, badges adquiridas e ajuste manual sem direção pré-selecionada
- Artefatos afetados:
  - `backend_api/`
  - `accounts/api_client.py`
  - `admin_ops/`
  - `config/urls.py`
  - `templates/admin_base.html`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-19
- Atualizado em: 2026-05-19
- Encerrado em: 2026-05-19
- Retomada: evoluir gestão de operadores, mascaramento seletivo de dados sensíveis ou ajuste de reputação apenas com nova decisão técnica
- Reversão lógica: ocultar rotas/telas de usuários no Admin Ops e manter eventos/ledger preservados para auditoria

## WFLOW-20260520-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-OPSLOG-001`
- Objetivo: implementar logs técnicos persistidos para troubleshooting em Django, FastAPI, logging Python e Admin Ops
- Etapa atual: concluído; `.venv/bin/python manage.py test`, checks de migration e testes focados de Admin Ops/logs executados com sucesso em 2026-05-20
- Artefatos afetados:
  - `system_logs/`
  - `backend_api/`
  - `admin_ops/`
  - `accounts/api_client.py`
  - `config/`
  - `templates/admin_base.html`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: evoluir alertas, paginação avançada e integração externa de observabilidade quando priorizado
- Reversão lógica: ocultar telas/rotas de logs no Admin Ops e manter tabela para auditoria técnica temporária até expiração

## WFLOW-20260520-002

- Tipo: `implementation-cycle`
- Status: `concluido`
- Feature alvo: `FEAT-NOTIFY-001`, `FEAT-OPSLOG-001`
- Objetivo: implementar Config operacional, modo manutenção, separação de credenciais PostgreSQL por serviço, SMTP não sensível persistido e Dashboard Admin Ops ampliado com saúde operacional
- Etapa atual: concluído; `.venv/bin/python manage.py check`, `.venv/bin/python manage.py makemigrations --check --dry-run`, `.venv/bin/python manage.py test` e `git diff --check` executados com sucesso em 2026-05-20
- Artefatos afetados:
  - `backend_api/`
  - `accounts/api_client.py`
  - `admin_ops/`
  - `core/`
  - `config/`
  - `templates/`
  - `static/css/gotrendlabs.css`
  - `.env.example`
  - `README.md`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: evoluir envio real em `communications`, criação operacional de roles PostgreSQL de menor privilégio e gráficos/históricos do dashboard quando priorizado
- Reversão lógica: ocultar Config/Dashboard ampliado no Admin Ops, manter `gotrendlabs_site_config` preservada e desativar middleware de manutenção se necessário

## WFLOW-20260520-003

- Tipo: `refactor-feature`
- Status: `concluido`
- Feature alvo: `FEAT-RES-001`
- Objetivo: centralizar ciclo de vida de mercado em engine backend, adicionar auditoria read-only de resolução no Admin Ops e validar fluxo hard com 100 usuários simulados
- Etapa atual: concluído; `.venv/bin/python manage.py test tests`, testes focados de Admin Ops/resolução e `git diff --check` executados com sucesso em 2026-05-20
- Artefatos afetados:
  - `backend_api/market_lifecycle_engine.py`
  - `backend_api/main.py`
  - `backend_api/schemas.py`
  - `accounts/api_client.py`
  - `admin_ops/`
  - `markets/management/commands/reconcile_canceled_market_refunds.py`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/research/qa-simulacao-hard-100-usuarios-20260520.md`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: evoluir auditorias públicas/usuário final, snapshots históricos materializados e exportação operacional quando priorizado
- Reversão lógica: remover ação/tela/contrato de auditoria, manter `MarketLifecycleEngine` se o refactor permanecer desejável; se necessário, mover chamadas de lifecycle de volta para handlers preservando testes de ledger/reputação

## WFLOW-20260520-004

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-WALLET-001`, `FEAT-REP-001`
- Objetivo: implementar recarga educativa por fila Admin Ops com piso configurável, histórico/extrato paginados e ranking web paginado
- Etapa atual: concluído; `.venv/bin/python manage.py check`, `.venv/bin/python manage.py makemigrations --check --dry-run`, `.venv/bin/python manage.py test tests.test_web_smoke`, `git diff --check` e migração local executados com sucesso em 2026-05-20
- Artefatos afetados:
  - `accounts/`
  - `backend_api/`
  - `admin_ops/`
  - `wallet/`
  - `profiles/`
  - `config/urls.py`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: evoluir cadência/janela automática de recargas, materialização futura do ranking ou controles operacionais mais granulares quando priorizado
- Reversão lógica: ocultar botões/rotas de recarga e filtro `wallet_recharge`, manter ledger/solicitações preservados para auditoria; remover paginação web apenas na camada Django se houver regressão de UX

## WFLOW-20260520-005

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`
- Objetivo: restaurar rodapé público nas telas standalone de autenticação e alinhar a regra documental de apresentação pública
- Etapa atual: concluído; testes focados de auth web, verificação HTTP local de `/login/` e `git diff --check` executados com sucesso em 2026-05-20
- Artefatos afetados:
  - `accounts/templates/accounts/`
  - `templates/base.html`
  - `templates/components/footer.html`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/auth-and-session.md`
  - `docs/specs/architecture/frontend-web.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: manter novos layouts públicos usando o partial de rodapé compartilhado para evitar divergência visual
- Reversão lógica: remover o include do rodapé nas telas standalone de auth e ajustar a spec para voltar a exigir apenas navegação pública

## WFLOW-20260520-006

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`
- Objetivo: padronizar botões sociais iconizados em login/cadastro, incluir X no placeholder social e corrigir espaçamento vertical das telas de auth
- Etapa atual: concluído; `.venv/bin/python manage.py test tests.test_web_smoke.BackendAuthAPITests.test_social_auth_placeholder_supports_initial_providers`, `.venv/bin/python manage.py test tests.test_web_smoke.WebSmokeTests.test_login_page_has_focused_auth_layout`, `.venv/bin/python manage.py test tests.test_web_smoke`, `git diff --check` e screenshots locais via Chrome/Playwright executados com sucesso em 2026-05-20
- Artefatos afetados:
  - `accounts/templates/accounts/login.html`
  - `accounts/templates/accounts/register.html`
  - `backend_api/main.py`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/auth-and-session.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: implementar OAuth real para `google`, `facebook` e `x` quando credenciais/callbacks forem priorizados
- Reversão lógica: restaurar botões textuais antigos e remover `x` do placeholder FastAPI, mantendo o ajuste de altura natural de auth se a correção visual permanecer desejável

## WFLOW-20260520-007

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`
- Objetivo: reduzir atrito de navegação tornando o título do card de mercado clicável para o detalhe
- Etapa atual: concluído; `.venv/bin/python manage.py test tests.test_web_smoke.WebSmokeTests.test_market_card_title_links_to_market_detail`, suíte `.venv/bin/python manage.py test tests.test_web_smoke` e `git diff --check` executados com sucesso em 2026-05-20
- Artefatos afetados:
  - `templates/components/market_card.html`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/market-feed.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: avaliar métricas de CTR do título versus CTA quando a instrumentação de eventos do feed for priorizada
- Reversão lógica: remover o link do título e manter apenas os CTAs explícitos `Prever`/`Ver resolução`

## WFLOW-20260520-008

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-REP-001`, `FEAT-WALLET-001`, `FEAT-OPSLOG-001`, `admin-ops`
- Objetivo: padronizar listas web e browses principais do Admin Ops com `Carregar mais` em blocos cumulativos de 10 itens
- Etapa atual: concluído; `.venv/bin/python -m py_compile admin_ops/views.py profiles/views.py wallet/views.py`, testes focados de Admin Ops e `.venv/bin/python manage.py test tests.test_web_smoke` executados com sucesso em 2026-05-20
- Artefatos afetados:
  - `profiles/`
  - `wallet/`
  - `admin_ops/`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: aplicar o mesmo padrão a novos browses web simples, mantendo paginação por offset apenas em auditorias ou telas que precisem de posição explícita
- Reversão lógica: restaurar os controles de página/offset nas views/templates afetados, preservando contratos backend e documentação histórica

## WFLOW-20260520-009

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-I18N-001`, `sistema-documental`
- Objetivo: renomear a marca pública da plataforma para `GoTrendLabs` preservando identificadores técnicos e `GTL Credits`
- Etapa atual: concluído; testes e busca final registrados na implementação desta branch
- Artefatos afetados:
  - `templates/`
  - `accounts/templates/accounts/`
  - `core/`
  - `backend_api/main.py`
  - `static/js/gotrendlabs.js`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: extrair strings de marca para catálogos quando `FEAT-I18N-001` avançar
- Reversão lógica: restaurar textos públicos para `GoTrendLabs`, mantendo `GTL Credits` e identificadores técnicos inalterados

## WFLOW-20260520-010

- Tipo: `docs-tooling`
- Status: `concluido`
- Feature alvo: `sistema-documental`, `curadoria-de-mercados`
- Objetivo: criar skill local para sugerir mercados de previsão com dados internos da GoTrendLabs, trends sociais, links exatos de verificação, diversidade editorial e anti-repetição
- Etapa atual: concluído; `python3 /Users/williamsca/.codex/skills/.system/skill-creator/scripts/quick_validate.py tools/skills/gotrendlabs/gotrendlabs-prediction-markets` executado com sucesso em 2026-05-20
- Artefatos afetados:
  - `tools/skills/gotrendlabs/gotrendlabs-prediction-markets/`
  - `tools/skills/gotrendlabs/README.md`
  - `docs/guides/gotrendlabs-prediction-markets-skill.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: configurar tokens opcionais de redes sociais quando a operação quiser consultar APIs externas diretamente
- Reversão lógica: remover a skill e o guia, mantendo apenas o histórico documental desta decisão

## WFLOW-20260521-001

- Tipo: `docs-tooling`
- Status: `concluido`
- Feature alvo: `sistema-documental`, `curadoria-de-mercados`
- Objetivo: reforçar a skill `gotrendlabs-prediction-markets` para validar que a fonte de resolução consegue fundamentar e certificar o resultado antes de sugerir mercados
- Etapa atual: concluído; `python3 /Users/williamsca/.codex/skills/.system/skill-creator/scripts/quick_validate.py tools/skills/gotrendlabs/gotrendlabs-prediction-markets` e `git diff --check` executados com sucesso em 2026-05-21
- Artefatos afetados:
  - `tools/skills/gotrendlabs/gotrendlabs-prediction-markets/SKILL.md`
  - `tools/skills/gotrendlabs/gotrendlabs-prediction-markets/references/fontes-sociais-e-verificacao.md`
  - `tools/skills/gotrendlabs/gotrendlabs-prediction-markets/references/framework-de-mercados.md`
  - `docs/guides/gotrendlabs-prediction-markets-skill.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-21
- Atualizado em: 2026-05-21
- Encerrado em: 2026-05-21
- Retomada: integrar checagens automatizadas por API/navegador quando credenciais sociais oficiais estiverem configuradas
- Reversão lógica: remover a etapa obrigatória de validação da fonte e voltar ao requisito anterior de link exato com fallback

## WFLOW-20260521-002

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`, `FEAT-MARKET-001`, `FEAT-MARKET-002`, `FEAT-PRED-001`, `FEAT-WALLET-001`
- Objetivo: corrigir perfil autenticado com dados reais do banco, adicionar marcação administrativa de bots, remover indução de escolha no ticket, ajustar métricas públicas de wallet, melhorar share de mercado e estados de saldo
- Etapa atual: concluído; `.venv/bin/python manage.py check`, testes focados de perfil/ticket/share/admin e `.venv/bin/python manage.py test` executados com sucesso durante a implementação em 2026-05-21
- Artefatos afetados:
  - `accounts/`
  - `admin_ops/`
  - `backend_api/`
  - `core/`
  - `markets/templates/markets/detail.html`
  - `profiles/views.py`
  - `static/css/gotrendlabs.css`
  - `static/js/gotrendlabs.js`
  - `templates/`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/`
  - `docs/specs/contracts/`
  - `docs/specs/architecture/`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-21
- Atualizado em: 2026-05-21
- Encerrado em: 2026-05-21
- Retomada: avaliar cache-busting centralizado para assets estáticos e teste visual automatizado quando o navegador MCP estiver disponível
- Reversão lógica: remover `is_bot`, restaurar ticket com botão desabilitado até escolha, voltar métrica `distributed_gtl` para todos os créditos e retirar opções/CTA do share de mercado

## WFLOW-20260521-003

- Tipo: `infra-data`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`
- Objetivo: impedir que mercados fixture sejam semeados em produção e limpar os fixtures criados no primeiro deploy
- Etapa atual: concluído; migration inicial de mercados sem `RunPython` de seed, seed explícito restrito ao harness de testes e RDS de produção validado com `gotrendlabs_markets = 0`
- Artefatos afetados:
  - `markets/migrations/0001_initial.py`
  - `tests/test_web_smoke.py`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-21
- Atualizado em: 2026-05-21
- Encerrado em: 2026-05-21
- Retomada: criar mercados reais via Admin Ops/curadoria antes de liberar tráfego editorial de produção
- Reversão lógica: reintroduzir seed apenas em ambiente não-produtivo, nunca via migration aplicada em PRD

## WFLOW-20260521-004

- Tipo: `infra-data`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-AUTH-001`, `FEAT-WALLET-001`
- Objetivo: criar fluxo one-off idempotente para popular PRD com dados editoriais bons de DEV, admin inicial, wallet conciliada, badges com mídia e site config
- Etapa atual: concluído; PRD populado com `@admin`, wallet conciliada, 10 badges com mídia, site config, 27 mercados editoriais, 65 opções e 47 arquivos de mídia; snapshot RDS pré-import `gotrendlabs-prod-before-bootstrap-20260521215807`; senha de `admin@gotrendlabs.com.br` resetada e validada, parâmetros temporários de senha removidos do SSM
- Artefatos afetados:
  - `ops/scripts/export_dev_bootstrap.py`
  - `ops/scripts/import_prod_bootstrap.py`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-21
- Atualizado em: 2026-05-21
- Encerrado em: 2026-05-21
- Retomada: seguir criando novos conteúdos diretamente em PRD; se novo reset administrativo for necessário, usar `SecureString` temporário e removê-lo após validação
- Reversão lógica: restaurar snapshot RDS pré-import e remover mídia copiada do volume `mediafiles`

## WFLOW-20260522-001

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`
- Objetivo: tornar a ação de favorito visível para visitantes na home e no detalhe, em estado readonly com aviso de login, mantendo mutação e recorte `Favoritos` autenticados
- Etapa atual: concluído; `.venv/bin/python manage.py test tests.test_web_smoke`, `.venv/bin/python manage.py check`, `git diff --check` e validação local da home/detalhe no `runserver` executados com sucesso em 2026-05-22
- Artefatos afetados:
  - `templates/components/market_card.html`
  - `markets/templates/markets/detail.html`
  - `static/js/gotrendlabs.js`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/`
  - `docs/specs/architecture/frontend-web.md`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: avaliar CTA direto para login caso métricas mostrem muitos cliques de visitante sem conversão
- Reversão lógica: ocultar novamente affordance de favorito para visitantes e remover handler `data-guest-favorite-button`

## WFLOW-20260522-002

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-SUGGEST-001`, `FEAT-OPSLOG-001`
- Objetivo: expor `Sugerir mercado` no topo público e incluir indicador `Backend API` no Dashboard Admin Ops consultando `GET /health`
- Etapa atual: concluído; testes de navegação pública, health online/offline do dashboard, `manage.py check` e `git diff --check` executados em 2026-05-22
- Artefatos afetados:
  - `templates/base.html`
  - `admin_ops/`
  - `accounts/api_client.py`
  - `tests/test_web_smoke.py`
  - `docs/specs/features/`
  - `docs/specs/architecture/`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: avaliar se o healthcheck deve expor versão/build quando houver necessidade operacional
- Reversão lógica: remover o link público de sugestão no topo e ocultar o card `Backend API`, mantendo `/health` disponível para infraestrutura

## WFLOW-20260522-003

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`
- Objetivo: ampliar a curadoria assistida para mercados cripto com fontes objetivas, aviso de risco e seed DEV inicial com thumbnails autorais
- Etapa atual: concluído; skill `gotrendlabs-prediction-markets` atualizada para cripto, 3 mercados DEV criados como `draft`, thumbs 512x512 geradas em `media/market_thumbnails/`, `quick_validate.py` e `git diff --check` executados com sucesso em 2026-05-22
- Artefatos afetados:
  - `tools/skills/gotrendlabs/gotrendlabs-prediction-markets/`
  - `tools/skills/gotrendlabs/README.md`
  - `docs/guides/gotrendlabs-prediction-markets-skill.md`
  - `docs/specs/state/`
  - `media/market_thumbnails/generated-bitcoin-acima-80000-30-junho-2026.png`
  - `media/market_thumbnails/generated-solana-acima-bsc-tvl-31-maio-2026.png`
  - `media/market_thumbnails/generated-pepe-acima-shiba-meme-coins-15-junho-2026.png`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: revisar odds/fontes no Admin Ops antes de publicar os mercados cripto; em PRD, aplicar via fluxo operacional controlado, não por migration automática
- Reversão lógica: remover/arquivar os mercados cripto em DEV/PRD e retirar `cripto` da skill se a categoria for descontinuada

## WFLOW-20260522-004

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`, `FEAT-REP-001`
- Objetivo: implementar `evento` como terceira camada da taxonomia de mercado e aplicar o recorte em mercado público/Admin Ops/badges
- Etapa atual: concluído; migrations, contratos FastAPI, Admin Ops, renderização pública e testes focados de evento executados em 2026-05-22; suíte smoke completa fica registrada na validação da branch
- Artefatos afetados:
  - `markets/`
  - `accounts/`
  - `backend_api/`
  - `admin_ops/`
  - `templates/components/market_card.html`
  - `markets/templates/markets/detail.html`
  - `static/js/gotrendlabs.js`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: decidir se ranking público e sugestão de mercado também passam a capturar/filtrar evento em uma próxima fatia
- Reversão lógica: ocultar seleção/exibição de evento na UI e tratar regras de badge com `event` preenchido como inativas, preservando tabelas para nova migração corretiva

## WFLOW-20260522-005

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`
- Objetivo: redesenhar Admin Ops Taxonomia em master-detail e adicionar aviso opcional por evento para mercados sensíveis
- Etapa atual: concluído; migration `MarketEvent.notice`, contratos FastAPI/Django, UI pública de detalhe/ticket, Admin Ops master-detail, testes e specs atualizados em 2026-05-22
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `core/`
  - `admin_ops/`
  - `markets/templates/markets/detail.html`
  - `static/js/gotrendlabs.js`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: avaliar templates de aviso pré-cadastrados por categoria sensível se operadores repetirem o mesmo texto
- Reversão lógica: manter `notice` vazio e ocultar o alerta público, preservando o layout master-detail e a coluna para compatibilidade

## WFLOW-20260522-006

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`
- Objetivo: adicionar avisos opcionais em categoria/subcategoria e corrigir a operação visual da tela Admin Ops Taxonomia
- Etapa atual: concluído; migration para `MarketCategory.notice` e `MarketSubcategory.notice`, contratos FastAPI/Django, Admin Ops, detalhe/ticket público, testes e specs atualizados em 2026-05-22
- Artefatos afetados:
  - `markets/`
  - `backend_api/`
  - `core/`
  - `admin_ops/`
  - `markets/templates/markets/detail.html`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: avaliar previews consolidados de avisos quando categoria/subcategoria/evento possuírem textos longos simultaneamente
- Reversão lógica: manter avisos de categoria/subcategoria vazios e ocultar seus campos na UI, preservando colunas para compatibilidade

## WFLOW-20260522-007

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-MARKET-002`, `FEAT-REP-001`
- Objetivo: reposicionar avisos no detalhe de mercado, permitir exclusão segura de eventos sem mercado e exibir miniatura no browse Admin Ops de badges
- Etapa atual: concluído; template público, API FastAPI, proxy Django, Admin Ops, testes e specs atualizados em 2026-05-22
- Artefatos afetados:
  - `backend_api/`
  - `accounts/`
  - `admin_ops/`
  - `markets/templates/markets/detail.html`
  - `static/css/gotrendlabs.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: avaliar se categorias/subcategorias sem mercados também devem ter limpeza controlada ou seguir somente bloqueio lógico
- Reversão lógica: ocultar ação `delete_event`, manter validação 422 para eventos vinculados e voltar avisos para posição anterior se a UI de negociação pedir destaque maior

## WFLOW-20260522-008

- Tipo: `change-ui`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`
- Objetivo: substituir o indicador circular dos cards por indicador horizontal de prazo tecnicamente baseado em tempo restante e exibir thumbnail no detalhe de negociação
- Etapa atual: concluído; card, detalhe de mercado, CSS, JS de hidratação, testes e specs atualizados em 2026-05-22
- Artefatos afetados:
  - `templates/components/market_card.html`
  - `markets/templates/markets/detail.html`
  - `static/css/gotrendlabs.css`
  - `static/js/gotrendlabs.js`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: validar visualmente em browser se a rail horizontal economiza espaço nos cards de 3 colunas sem perder legibilidade
- Reversão lógica: restaurar o indicador circular textual mantendo a regra de não usar probabilidade como progresso de tempo

## WFLOW-20260522-009

- Tipo: `change-content`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`
- Objetivo: aplicar lote cripto mainstream com taxonomia `Mercado > Cripto > moeda`, aviso de subcategoria e thumbnails autorais
- Etapa atual: concluído; comando idempotente `seed_crypto_markets_20260522`, memória editorial, changelogs e 3 thumbs 512x512 adicionados; lote aplicado em PRD via SSM/container Django em 2026-05-22, com 3 mercados `open`, aviso de subcategoria e imagens no volume `production_mediafiles`
- Artefatos afetados:
  - `markets/management/commands/seed_crypto_markets_20260522.py`
  - `media/market_thumbnails/generated-ethereum-acima-3000-30-junho-2026.png`
  - `media/market_thumbnails/generated-dogecoin-top10-30-junho-2026.png`
  - `media/market_thumbnails/generated-solana-acima-xrp-ranking-30-junho-2026.png`
  - `docs/specs/state/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-22
- Atualizado em: 2026-05-22
- Encerrado em: 2026-05-22
- Retomada: revisar odds/fechamento no Admin Ops e publicar ajustes editoriais caso a curadoria queira destacar algum card no feed
- Reversão lógica: cancelar/arquivar os três mercados e limpar ou alterar o aviso da subcategoria `Cripto` se a taxonomia for revista

## WFLOW-20260524-002

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-REP-001`
- Objetivo: exibir badges conquistadas no ranking e ampliar filtros públicos para evento
- Etapa atual: concluído; FastAPI, Django, CSS/JS, testes e specs atualizados em 2026-05-24
- Artefatos afetados:
  - `backend_api/`
  - `profiles/`
  - `static/css/gotrendlabs.css`
  - `static/js/gotrendlabs.js`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-24
- Atualizado em: 2026-05-24
- Encerrado em: 2026-05-24
- Retomada: avaliar visualmente em produção se o limite `3 +N` preserva legibilidade em usuários com muitos reconhecimentos
- Reversão lógica: ocultar badges no template do ranking e ignorar `event` no filtro web, mantendo campos adicionais do contrato como compatibilidade não disruptiva

## WFLOW-20260524-003

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-AUTH-001`
- Objetivo: exibir progressão neutra para operadores autenticados e permitir geração administrativa auditada de link de reset de senha
- Etapa atual: concluído; FastAPI, Django Admin Ops, home autenticada, testes e specs atualizados em 2026-05-24
- Artefatos afetados:
  - `backend_api/`
  - `accounts/`
  - `admin_ops/`
  - `core/templates/core/home.html`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-24
- Atualizado em: 2026-05-24
- Encerrado em: 2026-05-24
- Retomada: se reset por email real for priorizado, integrar communications/SMTP em vez de expor apenas link operacional
- Reversão lógica: ocultar a ação `password_reset` no detalhe de usuário e voltar o filtro da home para não carregar `user_summary` de operadores

## WFLOW-20260607-DJANGO-APPS-LAYOUT-001

- Tipo: `architecture-change`
- Status: `concluido`
- Feature alvo: reorganizacao do monorepo GoTrendLabs
- Objetivo: mover apps Django para `apps/web/django/`, preservando `AppConfig.label`, migrations e comandos locais
- Etapa atual: concluido; codigo, docs, skills, checks, collectstatic e suite Django validados em 2026-06-07
- Artefatos afetados:
  - `apps/web/django/`
  - `config/`
  - `apps/api/backend_api/`
  - `ops/scripts/`
  - `tests/test_web_smoke.py`
  - `README.md`
  - `docs/specs/architecture/`
  - `tools/skills/gotrendlabs/`
- Bloqueios: nenhum
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Retomada: abrir PR, acompanhar CI/deploy e fazer smoke pos-merge
- Reversão lógica: restaurar apps Django para a raiz mantendo os imports novos fora do merge, se alguma incompatibilidade de import path for encontrada

## WFLOW-20260607-OPENAPI-CONTRACTS-001

- Tipo: `architecture-change`
- Status: `concluido`
- Feature alvo: contratos OpenAPI versionados para web/mobile futuro
- Objetivo: versionar o snapshot OpenAPI da FastAPI e validar sincronismo em CI antes de novos clientes
- Etapa atual: concluido; snapshot, exportador, docs, skills, CI, checks e suite Django validados em 2026-06-07
- Artefatos afetados:
  - `packages/contracts/`
  - `apps/api/backend_api/main.py`
  - `.github/workflows/deploy.yml`
  - `README.md`
  - `docs/specs/architecture/`
  - `tools/skills/gotrendlabs/`
- Bloqueios: nenhum
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Retomada: abrir PR, acompanhar CI/deploy e fazer smoke pos-merge
- Reversão lógica: remover snapshot/versionador e voltar `packages/contracts/` para estado reservado, mantendo a documentação viva da FastAPI em `/docs`

## WFLOW-20260607-MOBILE-ANDROID-MVP-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MOBILE-001`
- Objetivo: implementar o MVP Android Flutter consumindo a FastAPI como fonte da verdade
- Etapa atual: concluido; app Flutter, ajustes de contrato, docs, testes, build Android debug e smoke em emulador validados em 2026-06-07
- Artefatos afetados:
  - `apps/mobile/`
  - `apps/api/backend_api/`
  - `packages/contracts/openapi/gotrendlabs-api.json`
  - `docs/specs/architecture/mobile-api-contracts.md`
  - `docs/specs/testing/mobile-acceptance.md`
  - `docs/specs/state/`
  - `tests/test_web_smoke.py`
- Bloqueios: nenhum para o MVP Android local
- Iniciado em: 2026-06-07
- Atualizado em: 2026-06-07
- Encerrado em: 2026-06-07
- Retomada: ampliar QA autenticado real em emulador, avaliar refresh token/offline/push/iOS e consolidar cliente gerado quando contratos estabilizarem
- Reversão lógica: ocultar entrada mobile/reverter `apps/mobile`, manter contratos backend compatíveis de recarga como extensao segura, e preservar docs para retomada futura

## WFLOW-20260919-SKILLS-DISCOVERY-001

- Tipo: `architecture-change`
- Status: `concluido`
- Feature alvo: governança de skills do repositório
- Objetivo: tornar as skills versionadas do GoTrendLabs automaticamente descobertas pelo Codex, sem duplicar sua fonte de verdade
- Etapa atual: concluído; as 19 skills foram movidas para `.agents/skills/`, o índice e as referências vigentes foram atualizados, os `SKILL.md`/`openai.yaml` passaram por validação estrutural, a PR #119 foi integrada em `main` e o workflow GitHub Actions 35449181143 concluiu CI, validação OpenAPI, suíte de testes e deploy SSM em produção com sucesso em 2026-09-19
- Artefatos afetados:
  - `.agents/skills/`
  - `README.md`
  - `docs/guides/ia-spec-workflow.md`
  - `docs/specs/architecture/system-overview.md`
  - `docs/specs/architecture/mobile-flutter.md`
  - `docs/specs/state/change-log-specs.md`
  - `docs/specs/state/workflow-runs.md`
- Bloqueios: nenhum
- Iniciado em: 2026-09-19
- Atualizado em: 2026-09-19
- Encerrado em: 2026-09-19
- Retomada: use `$gotrendlabs-review-branch-impact` para revisar branches; ao criar ou renomear skills, atualize `.agents/skills/README.md`
- Reversão lógica: mover as skills de volta para `tools/skills/gotrendlabs/` e restaurar as referências vigentes se a política de descoberta do Codex for substituída por outra

## WFLOW-20261009-AI-THUMBNAILS-001

- Retomada autorizada: migração para Bedrock/Core e parâmetros em Configurações do Sistema, specs/aceite v1.1 formalizados antes do código; implementação e validação local concluídas nesta retomada. Artefatos: provider, serviço/configuração, fila, Django/config, migrations, contratos/OpenAPI, ADR, testes/runbook/estado. Sem consumo pago ou mudanças produtivas.

- Ajuste solicitado pelo usuário em 2026-10-09: preferir Bedrock/modelo produtivo também em DEV. Configuração local persistida alinhada a `bedrock`/Mantle us-east-1/`openai.gpt-oss-20b` (principal e high-reasoning), com snapshot reversível em `.runtime/dev/llm-config-before-bedrock.json`; credencial Bedrock já presente, não copiada de produção. Nenhuma inferência executada. Mudança da integração de thumbnails pendente de esclarecer incompatibilidade: documentação oficial do gpt-oss-20b declara imagem não suportada, e guia OpenAI Bedrock declara ferramenta image_generation indisponível. Consulta metadata AWS retornou Nova Canvas v1 end-of-life; catálogo us-west-2 lista Stable Image Core `stability.stable-image-core-v1:1` ACTIVE, disponibilidade authorization AUTHORIZED/entitlement AVAILABLE/region AVAILABLE, agreement NOT_AVAILABLE. Isso não confirma invocação pelo token atual. A implementação OpenAI anterior permanece desativada enquanto se define um modelo de imagem Bedrock; não marcar migração como entregue.

- Verificação produtiva posterior autorizada em 2026-10-09: consulta SSM no container FastAPI, transação PostgreSQL somente leitura, confirmou `ai_llm_provider=bedrock`, endpoint `https://bedrock-mantle.us-east-1.api.aws/v1`, modelos principal e high-reasoning `openai.gpt-oss-20b`; agentes/comentários/predições habilitados. Variáveis de habilitação/modelos de thumbnails ausentes no container consultado. Não houve inferência, alteração produtiva ou exposição de segredos. Isso complementa o registro anterior de produção não consultada durante a implementação; thumbnails seguem integração OpenAI separada, ainda sem deploy.

- Reinício local solicitado em 2026-10-09: runtime anterior em `gotrendlabs-mcp` substituído por `gotrendlabs-ai-thumbnails`; API, Django/static, MCP e executor dedicado reiniciados; PostgreSQL e proxy Caddy reiniciados. Migration `admin_ops.0022_thumbnail_jobs` aplicada no banco local. Health API/web/proxy e discovery MCP HTTP 200; rota de thumbnails presente no OpenAPI servido e controlador JS servido pelo proxy. Configurações/mídias anteriores preservadas. Geração continua desativada (`GTL_THUMB_ENABLED=0`), sem chamadas pagas; worker sem credencial do provedor. Acesso local: http://127.0.0.1:8000.

- Tipo: new-feature + implementation-cycle + test-review-cycle.
- Status: implementação e validação local concluídas; homologação real/habilitação produtiva pendentes por ausência de autorização de consumo/deploy. Feature FEAT-THUMB-001; escopo: prompt autorizado de 2026-10-09.
- Base: origin/main 80c0a5b; branch feature/admin-ai-thumbnails no worktree ../gotrendlabs-ai-thumbnails. Checkout original e alterações locais preservados intactos.
- Skills: governor/orchestrator, architect/guard, FastAPI/Django/PostgreSQL, test strategy/engineer, OpenAI Docs.
- Arquitetura revisada: FastAPI autoridade, worker separado, volume privado, confirmação sob lock, cotas persistidas; ADR-0012. Gate editorial atual preservado.
- Etapa: specs/contratos/aceite formalizados antes do código; fila/provider/worker/contratos/seleção/upload/limpeza entregues, documentação e memória atualizadas. Checklist universal/local satisfeito.
- Config local revalidada read-only: OpenAI/gpt-5.4-mini. agent_llm.py de comentários preservado. Compose da main tinha API mídia RO e daemon sem mount; worker dedicado/volume privado/subpath RW explícitos nesta branch. Produção não consultada.
- Ambiente original .venv Python 3.9 preservado; main MCP exige >=3.10, portanto ambiente separado Python 3.11 criado no worktree com requirements atuais. Nenhum banco real migrado.
- Evidências: suíte completa inicial 389 testes/OK em PostgreSQL isolado (715.312s); suíte focada final 23 testes/OK (29.649s), incluindo duas corridas; browser real Chrome/template/CSS/JS com HTTP simulado, loading/sucesso/erro, File/undo, submit continuar/aguardar, três categorias/crops desktop/mobile. Checks Django, migration drift, OpenAPI, JS, lint F e Compose config --no-env-resolution aprovados. Grants/mounts produtivos e geração real não validados.
- Artefatos: FEAT-THUMB-001, contrato admin-thumbnails/OpenAPI, admin_ops.0022/grants, ADR-0012, runbook/env/Compose/Dockerfile e matriz ai-thumbnails-acceptance.
- Próxima ação externa: obter autorização de consumo, homologar conta/modelos/qualidade/latência, depois rollout autorizado com migrations/volumes/grants e smoke. Não reenfileirar resultados uncertain; nenhuma medição de engajamento feita.
- Sem commit/push/deploy/produção/consumo pago. Homologação real pendente.

### Encerramento da retomada Bedrock — WFLOW-20261009-AI-THUMBNAILS-001

- Feature/contrato/ADR v1.1 implementados: Bedrock Core default, adapters SD3.5/Ultra, configuração persistida via FastAPI e painel separado; modelos textuais, URLs arbitrárias/extra fields e payload parcial rejeitados. Nenhum acoplamento/mudança em agent_llm.py.
- Snapshot provider/model/region/aspect/timeout/seed/instruções por job; mudanças no painel só para novas solicitações; kill switch operacional e habilitação DB. Jobs OpenAI anteriores preservados e explicitamente sem invocação/fallback. Limites DB, retenção por candidata, state machine/locks/preview privado/image_url anteriores preservados.
- Evidências: 37 testes/OK (52.845s), 5 complementares/OK (2.144s), 4 settings/schema/CSRF/OK (2.874s) em DBs isolados, provider simulado. Browser config/model/formulário independente/teclado e fluxo editorial completo aprovado; screenshots desktop/mobile/card inspecionados. Ruff F/Django/migration drift/OpenAPI/Node/Compose/diff aprovados. Matriz ai-thumbnails-acceptance e runbook atualizados.
- Local: admin_ops.0023 aplicada; campos/default Core/disabled e grants runtime confirmados; settings protegido 401 anônimo e OpenAPI GET/PUT/10 campos obrigatório servido; site HTTP 200; worker atualizado mantendo GTL_THUMB_ENABLED=0. DEV textual alinhado à configuração produtiva como autorizado anteriormente. Config anterior preservada em snapshot ignorado, checkout original/alterações prévias intactos.
- Status: trabalho local concluído; somente homologação real/habilitação produtiva pendente. Próxima ação externa: autorização explícita de consumo e verificação de acesso Runtime/Oregon/token/modelos/assinatura, qualidade real de cards e rollout posterior autorizado. Não houve geração paga, commit/push/deploy ou modificação produtiva.

### Habilitação do acordo Bedrock autorizada — 2026-10-09

- Usuário autorizou prosseguir especificamente com a habilitação do modelo, sem inferência paga/deploy. Oferta `offer-olze3cligtub4` conferida via ListFoundationModelAgreementOffers: Stable Image Core `stability.stable-image-core-v1:1`, us-west-2, USD 0.04/imagem. CreateFoundationModelAgreement executado com sucesso; consulta passou de NOT_AVAILABLE para PENDING e finalmente AVAILABLE. Último GetFoundationModelAvailability: agreement AVAILABLE, authorization AUTHORIZED, entitlement AVAILABLE, region AVAILABLE.
- Alteração externa limitada ao acordo de acesso na conta AWS; nenhuma capacidade reservada/servidor criado, nenhuma geração, alteração de IAM/token, deploy, migration produtiva ou habilitação da aplicação. Credencial Runtime da aplicação e qualidade real continuam sem homologação. Modelos alternativos não habilitados por esta ação. Não persistidos offerToken, URL assinada ou credenciais.

### Liberação de consumo no DEV autorizada — 2026-10-09

- Usuário autorizou explicitamente geração paga no DEV após diagnóstico do 503: launcher forçava GTL_THUMB_ENABLED=0 apesar do painel habilitado. Launcher ignorado atualizado para ler `.env.thumbnails.local` e aceitar reinício seletivo; override local 0600 GTL_THUMB_ENABLED=1. Somente API e thumbnail-worker reiniciados. Nenhuma configuração produtiva ou agente de comentários alterado.
- Verificação: política DB habilitada/Core/Oregon/3:2/180s, limites operador 10/mercado 5/global 50 por 24h, retenção 24h; fila sem jobs ativos na liberação; credencial Bedrock presente (sem exposição) nos ambientes de ambos, enabled(cursor)=true; API health e web HTTP 200 e processos ativos. Nenhuma chamada paga iniciada pelo assistente nesta etapa; geração real/credencial Runtime/qualidade ainda não homologadas. Operador pode testar no editor local.

### Ajuste completo do layout do editor — 2026-10-09

- Pedido do usuário: layout do editor de mercados inteiro sem encaixe visual. Aceite de apresentação formalizado na FEAT-THUMB-001 antes dos edits. Cabeçalho comum, título compacto, formulário sem molduras aninhadas, prévia/publicação alinhadas em coluna independente, ajuda recolhível; fechamento/resolução separados do card e notas. Textareas 4/4/3 linhas redimensionáveis; upload e geração na mesma linha no desktop; revisão/status editorial ocupa largura integral. Tabela de participantes com rolagem própria e região focável. Cache CSS administrativo atualizado. Campos/contratos/gate/seleção e agentes preservados.
- Evidências: 7 testes existentes Web/Settings aprovados (0.154s), Django check e git diff --check aprovados. Browser real com HTTP simulado mantém geração/regeneração/undo/upload/corridas/submit e config; página inteira em 1440/1100/390 px, temas claro/escuro, sem overflow horizontal, screenshots inspecionadas. Log `.runtime/thumbnail-validation/thumbnail-editor-layout.log`. Nenhuma geração paga nesta revisão; sem commit/push/deploy.

## Correção de CI da PR #143

Primeiro CI: build completo aprovado, 408 testes executados com 2 erros/1 skip. Inserções SQL históricas de SiteConfig omitiam colunas novas não nulas, pois defaults Django não ficam no PostgreSQL. Migration 0024_thumbnail_runtime_defaults fornece defaults SQL conservadores, mantendo inicialização existente e recurso off. Ambos os testes que falharam passaram localmente (2/5.798s, DB isolado). Repetir CI completo antes de merge.

## 2026-10-09 — Fechamento técnico e rollout de thumbnails

PR #143 integrada, merge 15b980585982cfa6706a38d57016614a41ba956d. CI final 408 testes aprovados/1 skip por roles CI, build completo aprovado. Actions 37963430113 e 37964971891 Success (PR e main/produção), SSM deploy Success. Migrations 0022–0024 aplicadas; defaults SQL preservam inicialização existente. Executor dedicado/grants/mounts/UIDs verificados: worker privado RW, API privado RO/subpath público RW, sem candidatas no proxy/Django. Arquivo efêmero próprio removido.

Habilitação produtiva de thumbnails autorizada e concluída: banco e GTL_THUMB_ENABLED=1 na API/worker, Core/Oregon/3:2/180s, limites 10/5/50 por 24h e retenção 24h. Configuração preservada, alteração auditada como operação de sistema; backups de envs 0600 no host. Fila vazia antes/depois, nenhuma chamada paga iniciada, nenhum mercado editado pelo assistente. Site/API HTTP 200 e configurações anônimas 401. Branch local preservada.

Fechamento técnico concluído; homologação de fluxo autenticado/MFA, consumo produtivo e qualidade visual real permanece pendente. Não afirmar inferência real validada em produção. Fonte externa atual: [PR #143](https://github.com/wscardua/gotrendlabs/pull/143) e [Actions](https://github.com/wscardua/gotrendlabs/actions/runs/37964971891). Registros anteriores descrevem etapas históricas, substituídos por esta atualização para estado operacional atual. Evidência documental pós-rollout preparada localmente para versionamento na próxima PR aprovada.
