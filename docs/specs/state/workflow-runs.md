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
