> Registro histórico da entrega inicial. O contrato atual foi simplificado a pedido do usuário; ver [resultados da simplificação](resolution-agenda-simplification-results.md). As verificações abaixo descrevem a revisão anterior.

# Agenda de resolução — entrega local em 17/10/2026

Branch `feature/structured-resolution-agenda`, base remota `7029dd8` obtida por fetch. Worktree: `/Users/williamsca/Documents/gotrendlabs-structured-agenda`. Checkout original com alterações preexistentes preservado. Nenhum agente delegado. Workflow: WFLOW-20261017-STRUCTURED-RESOLUTION-AGENDA.

## Comportamento e arquitetura

- Corte documental inclusivo, previsão vigente/original, recuperação e fuso IANA explícitos. PostgreSQL UTC/timestamptz; constraints de ordenação/completude registrada, índices de fila e versão da projeção.
- FastAPI valida publicação e instantes, deriva classificação por relógio autoritativo, filtra/ordena fila e contratos e fornece contadores do conjunto filtrado antes do filtro temporal/paginação. `active_contracts` preserva o recorte inicial; terminais são consultáveis nos filtros. `resolution_queue` concentra ordenação e seleção da fila na API.
- Resolução exige agenda registrada e `now > evidence_cutoff_at`; timestamp enviado pelo cliente não contorna a espera. Recuperação esgotada exige encaminhamento, sem escolha de opção ou mutação financeira automática. Evidência válida pode ser analisada depois desse prazo.
- Reagendamento e acompanhamento explícito de evidência usam staff/MFA existentes, versão esperada, lock e evento transacional assinado com anterior/novo, motivo, ator e instante. Reagendamento não prorroga recuperação/corte e não altera critérios/opções. Undo mantém agenda; terminais recusam reagendamento.
- Definição v1 e sua reconstrução histórica não mudaram. Complementos e revisões no ledger existente vinculam o hash original. Auditoria compara assinaturas/histórico/projeção e participa da elegibilidade da selagem; pacote público leva snapshots/assinaturas dos eventos. `schedule_valid=null` em ausência histórica legítima, sem alegação de proteção de agenda inexistente.
- Admin Ops tem formulário, reagendamento, acompanhamento de evidências, fila, filtros e contadores. Painel conserva criação/publicação, separa marcos planejados e efetivos, inclui janela até recuperação e Hoje; sem barra de progresso por tempo. Percentuais CSS não são localizados com vírgula. Marcadores próximos são distribuídos em alturas diferentes e têm equivalente textual com segundos/fuso.
- Web e Flutter apresentam previsão e original reagendada; critério integral preservado. Flutter não ganha operações administrativas nem interpreta prazos como decisão. Locked e terminais não apresentam contagem pendente de fechamento.

## MCP e editorial

A revisão humana mostra os três marcos no fuso escolhido junto ao critério público integral; validate_market_draft retorna pendência explícita de agenda incompleta, permitindo preparação honesta de drafts.

Estendida a implementação real em `apps/mcp/server.py`, `editorial_schemas.py`, `editorial_service.py` e rotas existentes. Agenda participa de validação/criação/edição, projeções search/get, snapshot/hash e submissão; submissão incompleta é recusada. Mudança editorial invalida aprovação anterior pelos mecanismos existentes. Política 1.3, ficha 1.7 e checklist/manual atualizados, sem segundo MCP ou restauração de ficha antiga.

Scopes e permissões permanecem restritos: agentes não publicam, resolvem, cancelam, reagendam publicados nem registram recuperação administrativa. Testados replay idêntico, mesma chave com conteúdo alterado, revisão/concorrência, permissões e cliente MCP real HTTP. Nenhuma ficha ou revisão humana de mercado produtivo foi gerada/afirmada automaticamente.

## Verificações executadas

Python existente: `/Users/williamsca/Documents/gotrendlabs-editorial-single-document/.venv/bin/python` (3.11). O `.venv` do checkout original é 3.9 e não suporta o runtime atual. Banco local isolado: `gtl_agenda_dev`; Django cria `test_gtl_agenda_dev` no PostgreSQL Docker local. Não foram usados dados produtivos para mutações.

- Rodada consolidada: **123 testes aprovados**, incluindo `test_resolution_agenda`, `test_integrity_ledger`, `test_mcp_editorial`, `test_mcp_adapter`, `test_editorial_admin`, dashboard e painel de contratos. Cliente MCP real e piloto local executados.
- Rodada posterior de integridade/domínio/painel: **55 testes aprovados**; inclui filtros/contadores autoritativos, concorrência, rollback, backfill após previsão preservando bytes/hash/assinatura e totais financeiros, resolução/undo e auditoria/selagem.
- Rodada de UI/API/paginação/migração: **24 testes aprovados**, após mover a fila para seleção/ordenação única na FastAPI; rodada final com reforço de proveniência/rollback: **26 testes aprovados**.
- Smoke do daemon afetado pelo INSERT de fixture: **1 teste aprovado**; sem novo job. Teste de API indisponível no reagendamento: **1 aprovado**, com mensagem de erro e sem formulário de mutação.
- Revisão editorial final: **11 testes aprovados**, incluindo alerta de agenda incompleta em validate_market_draft e conferência estruturada dos marcos/critério no parecer humano.
- Flutter: `flutter analyze` sem problemas e `flutter test`: **115 aprovados**. Testes de modelo/repository/widget da previsão e original foram acrescentados. `flutter build apk --debug` concluiu.
- `python packages/contracts/export_openapi.py` e `--check` aprovados. `manage.py check`, `makemigrations --check --dry-run` e `git diff --check` aprovados. Migrations 0033–0035 aplicadas somente no banco isolado.

As primeiras rodadas encontraram fixtures sem agenda, expectativa de política 1.2 e teste de cota sujeito à virada de minuto. Foram corrigidos os consumidores/fixtures e estabilizado o relógio do teste, sem fallback de payload ou relaxamento de cota. Todas essas falhas passaram nas reexecuções pertinentes. Não foi executada a suíte inteira de todas as features do repositório.

## Ferramenta operacional e ensaio

`python manage.py migrate_resolution_agenda INVENTARIO` é dry-run padrão. Aplicação exige `--apply --actor-id STAFF --backup-confirmed`. Inventário revisado deve conter booleano verdadeiro, revisor, instante com offset, origem/trecho/fonte por campo, motivo e estado/hash/versão/revisão esperados. Decisão operacional pendente é recusada. Lote transacional; conflito ou signer indisponível reverte; reexecução verificada é idempotente.

Além dos testes, foi executado o CLI real em fixture isolada com revisão **simulada de teste**, explicitamente identificada, sem parecer humano real: dry-run retornou `would_apply`, aplicação retornou `apply`, replay retornou `already_applied` e auditoria da agenda retornou zero erros. Backup local via pg_dump custom foi restaurado em `gtl_agenda_restore_qa`: fixture com versão 0 no snapshot e versão 1 no banco aplicado. Nada disso se refere à aprovação de dados produtivos.

## QA visual

Capturas com Chromium instalado via Playwright, em 1440×1000 e 390×844: painel e detalhe público sem rolagem horizontal. Inspeção visual real dos PNGs; Steam mostra fechamento 15/10 e previsão 04/11 separadamente. Marcos planejados são descritos como planejados, sem conclusão decorrente do relógio. Foram conferidos o recorte estreito, datas textuais, marcador Hoje e a correção de decimais CSS.

- [Painel desktop](../../../output/resolution-agenda/contracts-desktop.png)
- [Painel estreito](../../../output/resolution-agenda/contracts-narrow.png)
- [Steam no painel](../../../output/resolution-agenda/steam-contract-desktop.png)
- [Detalhe web estreito](../../../output/resolution-agenda/market-narrow.png)
- [Agenda Flutter no emulador](../../../output/resolution-agenda/android-agenda.png)

Android: emulador `gotrendlabs_pixel`, API local em 8877 e fixture local identificada. O bootstrap padrão sem Firebase falhou em `Firebase.initializeApp` por configuração ausente; a atualização do APK de QA também encontrou pouco espaço. Sem apagar dados do emulador, foi usada entrada temporária sem Firebase e hot restart com a mesma UI/repositories e endpoints locais. Essa validação confirma a tela e o contrato, não o bootstrap Firebase de uma release. A entrada temporária saiu de `lib/` e foi conservada apenas nos artefatos locais de QA. A captura por widget com fonte Ahem não foi considerada evidência de legibilidade.

## Inventário e pendências

Consulta MCP em 17/10 às 17h01 de Brasília: 11 mercados visíveis, complete_for_query e sem próxima página; API pública: 9. Nove pacotes de integridade públicos recolhidos. Isso não é inventário irrestrito do banco nem confirmação de agendas externas. Checkout atual já contém MCP editorial implantado; não foi inferida paridade da revisão Git produtiva.

| IDs | Situação da agenda proposta |
| --- | --- |
| 35, 36, 38, 39, 44, 50 | Corte e recuperação candidatos; hora de apuração não explícita. Decisão operacional humana pendente. |
| 45, 51, 52 | Corte, consulta/apuração planejada e recuperação explícitos reconferidos no critério; ainda exigem revisão e revisão editorial atual. |
| 53 | Draft; detalhe agora acessível: corte 30/10 23:59:59 e recuperação 02/11 23:59:59; “a partir de 31/10” não fornece hora. |
| 55 | Draft; corte 30/10 23:59:00 e recuperação 06/11 23:59:00; “a partir de 31/10” não fornece hora. Preservada precisão explícita. |

Nenhuma entrada produtiva está marcada `reviewed=true`. Revisões editoriais não visíveis à integração precisam ser obtidas por acesso staff; null no inventário não prova inexistência de registro. Drafts seguem o fluxo editorial; não são aplicados pelo comando de complemento de publicados.

[Inventário revisável](../../operations/resolution-agenda-inventory-20261017.json), [runbook](../../operations/resolution-agenda-runbook.md) e [ADR-0016](../decisions/ADR-0016-resolution-agenda.md).

## Liberação futura e limites

Implementado e verificado localmente; migração preparada e ensaiada somente em isolamento. Produção aguarda revisão por mercado, inventário atualizado, backup recuperável, verificação de roles separadas em staging e rollout coordenado de schema/backend/MCP/web/Flutter/backfill. O estado final exige todos os ativos abrangidos regularizados. Não houve merge, deploy, migração produtiva ou criação de mercado real.

Próxima ação objetiva: revisar o diff da branch e o inventário, fechar decisões de horários sem inferi-las e executar o runbook somente após autorização própria para implantação/aplicação produtiva.

## Entradas de código para revisão

| Camada | Arquivos principais |
| --- | --- |
| Domínio/API | apps/api/backend_api/resolution_schedule.py; main.py; schemas.py; market_lifecycle_engine.py |
| Provas | apps/api/backend_api/integrity_service.py; ADR-0016 |
| Persistência | apps/web/django/markets/models.py; migrations/0033_resolution_agenda.py, 0034_resolution_agenda_constraints.py, 0035_resolution_agenda_queue_index.py |
| MCP/editorial | apps/mcp/server.py; editorial_schemas.py; editorial_service.py; docs/editorial/criteria-v1.3.json e ficha/manual/checklist |
| Admin Ops/web | admin_ops/views.py, forms.py, templates/admin_ops/contracts.html, resolution.html, market_reschedule.html, market_form.html; markets/templates/markets/detail.html; gotrendlabs.css |
| Flutter | market_models.dart; market_detail_screen.dart; market_cards.dart; market_detail_screen_test.dart; markets_repository_test.dart |
| Migração | apps/web/django/markets/management/commands/migrate_resolution_agenda.py; inventário e runbook em docs/operations |
| Verificação | tests/test_resolution_agenda.py; test_integrity_ledger.py; test_mcp_editorial.py; test_web_smoke.py; packages/contracts/openapi/gotrendlabs-api.json |

Resumo executável local dos resultados: [verification-summary.json](../../../output/resolution-agenda/verification-summary.json).
