# Workflow Runs

Use este arquivo como memória operacional de processos em andamento, concluídos, bloqueados, cancelados ou substituídos.

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

## WFLOW-20260517-001

- Tipo: `new-feature`
- Status: `concluido`
- Feature alvo: `sistema-documental`
- Objetivo: criar base canônica de specs, contratos, arquitetura, testes, estado e skills
- Etapa atual: concluído
- Artefatos afetados:
  - `docs/specs/`
  - `tools/skills/orynth/`
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
- Retomada: evoluir operação do daemon para supervisor/container e alertas externos quando houver decisão de deploy
- Reversão lógica: desativar execução do comando `run_orynth_daemon` preservando serviços backend e eventos já registrados

## WFLOW-20260520-002

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `FEAT-MARKET-001`, `FEAT-WALLET-001`, `FEAT-AUTH-001`
- Objetivo: padronizar símbolo público `O₵`, expor métricas educativas na home e reorganizar rodapé/Admin Ops
- Etapa atual: concluído
- Artefatos afetados:
  - `backend_api/main.py`
  - `core/domain_client.py`
  - `accounts/api_client.py`
  - `core/templates/core/home.html`
  - `templates/base.html`
  - `templates/components/footer.html`
  - `static/css/orynth.css`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: evoluir um formatador central de moeda/i18n quando `FEAT-I18N-001` avançar
- Reversão lógica: restaurar labels visíveis antigos, remover métricas públicas da home e voltar Admin Ops para a navegação anterior preservando contratos internos `_oc`

## WFLOW-20260517-002

- Tipo: `change-feature`
- Status: `concluido`
- Feature alvo: `sistema-documental`
- Objetivo: adicionar changelog por feature e skills técnicas por stack
- Etapa atual: concluído
- Artefatos afetados:
  - `docs/specs/state/feature-changelog.md`
  - `tools/skills/orynth/orynth-django-web/`
  - `tools/skills/orynth/orynth-fastapi-domain/`
  - `tools/skills/orynth/orynth-postgres-modeling/`
  - `tools/skills/orynth/orynth-ops-scheduler-communications/`
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
  - `tools/skills/orynth/orynth-workflow-governor/`
  - `tools/skills/orynth/README.md`
  - `docs/guides/ia-spec-workflow.md`
  - `tools/skills/orynth/*/SKILL.md`
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
  - `tools/skills/orynth/orynth-software-architect/`
  - `tools/skills/orynth/orynth-test-engineer/`
  - `tools/skills/orynth/README.md`
  - `docs/specs/workflows/`
  - `docs/specs/state/workflow-checklists.md`
  - `docs/specs/state/integration-map.md`
  - `docs/guides/ia-spec-workflow.md`
- Bloqueios: nenhum
- Iniciado em: 2026-05-17
- Atualizado em: 2026-05-17
- Encerrado em: 2026-05-17
- Retomada: usar `orynth-software-architect` antes de mudanças relevantes e `orynth-test-engineer` para testes executáveis
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
- Objetivo: adicionar projeção `orynth_wallet_balances` para leitura rápida de saldo mantendo ledger como fonte auditável
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
  - `static/js/orynth.js`
  - `tests/test_web_smoke.py`
  - `docs/specs/state/`
- Bloqueios: resolução, payout real, reputação avançada, comunicações e refund/cancelamento ficam fora desta entrega
- Iniciado em: 2026-05-18
- Atualizado em: 2026-05-18
- Encerrado em: 2026-05-18
- Retomada: implementar FEAT-RES-001 usando `orynth_predictions`, `prediction_stake_lock` e snapshots de entrada como base
- Reversão lógica: desativar rota de confirmação no Django e endpoint FastAPI, preservando `orynth_predictions` e ledger para auditoria/migração

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
- Retomada: criar tabela de snapshots se o volume de previsões tornar caro recalcular séries a partir de `orynth_predictions`
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
  - `static/css/orynth.css`
  - `.env.example`
  - `README.md`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: evoluir envio real em `communications`, criação operacional de roles PostgreSQL de menor privilégio e gráficos/históricos do dashboard quando priorizado
- Reversão lógica: ocultar Config/Dashboard ampliado no Admin Ops, manter `orynth_site_config` preservada e desativar middleware de manutenção se necessário

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
  - `static/css/orynth.css`
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
  - `static/css/orynth.css`
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
  - `static/css/orynth.css`
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
  - `static/css/orynth.css`
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
- Objetivo: renomear a marca pública da plataforma para `Orynth Trends` preservando identificadores técnicos e `Orynth Coins`
- Etapa atual: concluído; testes e busca final registrados na implementação desta branch
- Artefatos afetados:
  - `templates/`
  - `accounts/templates/accounts/`
  - `core/`
  - `backend_api/main.py`
  - `static/js/orynth.js`
  - `tests/test_web_smoke.py`
  - `docs/specs/`
- Bloqueios: nenhum
- Iniciado em: 2026-05-20
- Atualizado em: 2026-05-20
- Encerrado em: 2026-05-20
- Retomada: extrair strings de marca para catálogos quando `FEAT-I18N-001` avançar
- Reversão lógica: restaurar textos públicos para `Orynth`, mantendo `Orynth Coins` e identificadores técnicos inalterados
