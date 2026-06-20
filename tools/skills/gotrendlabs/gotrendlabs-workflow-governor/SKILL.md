---
name: gotrendlabs-workflow-governor
description: Use esta skill para abrir, acompanhar, retomar, concluir, bloquear, cancelar ou substituir processos multi-documento do GoTrendLabs, evitando specs, contratos, testes, changelogs e estado operacional descasados.
---

# GoTrendLabs Workflow Governor

Use esta skill quando a tarefa tocar mais de um artefato ou quando houver risco de deixar docs, testes, contratos e estado desalinhados.

## Objetivo

Governar processos de mudança de ponta a ponta, mantendo memória operacional e permitindo retomada segura.

## Quando usar

- propor nova feature
- alterar feature existente
- promover spec de status
- iniciar ou retomar implementação
- revisar testes de uma feature
- cancelar, substituir ou bloquear uma mudança

## Fluxo padrão

1. Identificar o tipo em `docs/specs/workflows/`.
2. Abrir ou atualizar execução em `docs/specs/state/workflow-runs.md`.
3. Listar feature alvo, objetivo, etapa atual e artefatos afetados.
4. Executar etapas do workflow canônico.
5. Atualizar estado, changelog, testes, contratos e decisões conforme o checklist.
6. Fechar como `concluido`, `bloqueado`, `cancelado` ou `substituido`.

## Regras

- Não deixe mudança multi-documento sem workflow run.
- Não apague histórico para reverter; use reversão lógica.
- Mudanças mobile que alterem health, headers, OpenAPI, Admin Ops ou skills devem atualizar specs de arquitetura/teste, changelog, integration map, implementation status, known gaps e `workflow-runs.md`.
- Toda retomada precisa apontar a próxima ação objetiva.
- Toda conclusão precisa passar por `docs/specs/state/workflow-checklists.md`.
- Se uma etapa ficar pendente, registrar bloqueio em vez de fingir conclusão.

## Entradas principais

- `docs/specs/workflows/`
- `docs/specs/state/workflow-runs.md`
- `docs/specs/state/workflow-checklists.md`
- `docs/specs/state/implementation-status.md`
- `docs/specs/state/feature-changelog.md`

## Saídas esperadas

- workflow run atualizado
- checklist de conclusão satisfeito
- pendências e retomada explícitas
- docs, contratos, testes e estado sincronizados
