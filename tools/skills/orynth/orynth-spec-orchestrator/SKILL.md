---
name: orynth-spec-orchestrator
description: Use esta skill para conduzir o desenvolvimento do Orynth a partir das specs técnicas, contratos, arquitetura, testes e memória operacional, sem depender do histórico da conversa.
---

# Orynth Spec Orchestrator

Use esta skill quando a tarefa principal for implementar ou retomar implementação guiada por specs.

## Objetivo

Conduzir a execução da feature a partir dos documentos corretos, mantendo dependências, fronteiras e estado do projeto em sincronia.

## Fluxo padrão

1. Verificar workflow aberto em `docs/specs/state/workflow-runs.md`.
2. Ler `docs/specs/state/implementation-status.md`.
3. Ler a feature alvo em `docs/specs/features/`.
4. Ler contratos listados no frontmatter.
5. Revisar arquitetura e testes relevantes.
6. Planejar implementação por camada.
7. Após a execução, atualizar workflow, estado operacional e testes executados ou pendentes.

## Regras

- Não assuma comportamento fora do que está documentado.
- Respeite os limites entre `frontend-web`, `backend-api`, `database`, `scheduler-jobs`, `communications` e `admin-ops`.
- Se a spec estiver desatualizada, interrompa a improvisação e proponha ajuste documental primeiro.
- Não marque workflow como concluído sem validar `workflow-checklists.md`.

## Entradas principais

- `docs/specs/features/`
- `docs/specs/architecture/`
- `docs/specs/contracts/`
- `docs/specs/testing/`
- `docs/specs/state/`
- `docs/specs/workflows/`

## Saídas esperadas

- sequência de implementação por camada
- checklist de dependências
- atualização de status da feature
