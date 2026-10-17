# Resolução prevista e fuso — revisão 1.1

Solicitação posterior do usuário em 17/10/2026 simplifica a agenda. Workflow WFLOW-20261017-SIMPLIFY-RESOLUTION-AGENDA; mesma branch/worktree isolada, alterações anteriores preservadas.

## Contrato e comportamento

Somente resolução prevista (`expected_resolution_at`) e fuso IANA (`schedule_timezone`) são entradas da agenda. Publicação exige previsão futura posterior ao fechamento; drafts podem ser incompletos. Fechamento, resolução efetiva e selagem continuam separados. Vencimento é atraso operacional, sem decisão, saldo, cancelamento ou bloqueio automático. Corte documental e recuperação pertencem aos critérios integrais quando necessários; removidos campos ativos, filtros, endpoint e UI específicos.

Histórico original/vigente, motivo/ator/instante, concorrência, staff/MFA/CSRF e evento assinado transacional continuam. Resolução não precisa aguardar a previsão; demais regras do ciclo e critérios permanecem. Sem alterações produtivas ou novas permissões.

Migration 0036 conserva fisicamente colunas aposentadas para verificar snapshots antigos; remove-as do ORM e retira constraints do contrato anterior. Eventos/definições antigos não são reescritos. Novas revisões ligam o snapshot anterior intacto à projeção simplificada. Teste cobre evento antigo com valores não nulos e nova revisão.

MCP existente usa o contrato simplificado em validate/create/update/search/get/submissão/snapshots; política 1.4/ficha 1.8, hashes recalculados pelo mecanismo existente. Sem scopes extras nem permissão administrativa. Inventário v2 remove campos retirados e exige nova revisão explícita; ninguém foi marcado como revisor humano. Origem/cobertura da consulta histórica preservada.

## Verificação

- Flutter analyze: sem problemas; flutter test: 115 aprovados.
- PostgreSQL Docker isolado `test_gtl_agenda_dev`: 125 testes backend/integridade/MCP/editorial/adapter aprovados (198.933s); rodada final de 27 testes de agenda, histórico com campos antigos não nulos, contrato/formulário, painel/paginação e erro de API aprovada (20.368s). Rodadas têm cobertura sobreposta; não são 152 testes distintos.
- Migration 0036 aplicada também no banco local de desenvolvimento, após backup completo recuperável (`.runtime/dev/before-simple-agenda.dump`, privado/ignorado). Nenhuma migration produtiva.
- Django check, makemigrations --check --dry-run, OpenAPI export e --check e git diff --check aprovados.
- Ruff não está instalado no ambiente Python usado; não foi alegada verificação com essa ferramenta.

## Visual e serviço local

Renderização real dos templates com fixtures identificadas, sem simular autenticação/MFA. Chromium em 1440×1000 e 390×844: formulário só previsão/fuso; painel e detalhe sem overflow horizontal. Capturas inspecionadas do formulário e Steam no painel estreito. Esta revisão não repetiu QA visual Android; widgets/repositories passaram nos testes Flutter e a apresentação existente foi preservada.

- [Campos simplificados](../../../output/resolution-agenda/simple-schedule-fields.png)
- [Painel estreito Steam](../../../output/resolution-agenda/simple-steam-contract-narrow.png)
- [Formulário desktop](../../../output/resolution-agenda/simple-form-desktop.png)
- [Formulário estreito](../../../output/resolution-agenda/simple-form-narrow.png)

API/web/MCP locais recarregados com código atual. Proxy `http://127.0.0.1:8000`: health HTTP 200; OpenAPI servido contém previsão/fuso e não contém campos ativos ou endpoint de recuperação. MFA e senha local previamente configurados preservados nesta revisão.

## Pendências externas

IDs 45/51/52: candidatos explícitos à previsão; demais IDs do inventário exigem decisão operacional/hora revisada. Nenhuma nova decisão editorial inventada. Atualizar inventário antes de aplicação autorizada e seguir runbook vigente. Produção, merge, deploy e backfill produtivo continuam pendentes e não foram executados.

O teste antigo do painel ainda exigia os rótulos retirados; foi atualizado para exigir sua ausência e aprovado na rodada final. A primeira rodada de agenda encontrou uma tupla de marcador sem vírgula após a redução a um único marco; corrigida antes da regressão consolidada. Não há falha pendente dessas verificações.

Checklist universal/alterar-feature/implementação/testes de workflow-checklists.md aplicado: spec, contratos/ADR/arquitetura/segurança, MCP/permissões/replays, testes, changelogs/status/integration-map/known-gaps e runbook/inventário atualizados. Estado local concluído; etapas produtivas continuam externas.

## Instalação física local — 17/10/2026

A pedido do usuário, APK debug 1.2.0+14 instalado e aberto em Samsung SM-G980F por ADB Wi-Fi. Pacote separado `br.com.gotrendlabs.gotrendlabs_mobile.local`, mantendo app principal/dados; applicationIdSuffix aplicado por init Gradle local ignorado, sem alteração no Gradle versionado. Build concluído. Entrada de QA conserva a UI atual e omite inicialização opcional Firebase (sem notificações).

API/web locais acessíveis no aparelho por adb reverse 8001/8000; serviços não foram expostos à rede. Instalação Success, processo/atividade em primeiro plano e feed local carregado verificados. Evidência privada ignorada em `.runtime/mobile-physical/installed-screen.png`; não é homologação de Firebase/release nem do fluxo completo autenticado no aparelho. Nenhuma previsão, login, dado de produção, merge ou deploy executado. Conexão de depuração e Mac/serviços locais precisam permanecer ativos durante o teste.
