---
name: gotrendlabs-mobile-docs-governor
description: Use esta skill para manter documentação, memória operacional, changelog, status, workflow runs, integration map e README sincronizados quando o trabalho envolver o app mobile Flutter do GoTrendLabs.
---

# GoTrendLabs Mobile Docs Governor

Use esta skill quando a tarefa mobile tocar múltiplos documentos, criar/alterar specs, criar skills, iniciar implementação ou mudar estado do projeto.

## Objetivo

Evitar que o mobile avance sem atualizar a memória operacional geral do GoTrendLabs.

## Fluxo padrão

1. Verificar ou abrir workflow em `docs/specs/state/workflow-runs.md`.
2. Atualizar `docs/specs/state/implementation-status.md` quando criar ou alterar feature mobile.
3. Atualizar `docs/specs/state/feature-changelog.md` com mudanças relevantes.
4. Atualizar `docs/specs/state/integration-map.md` quando houver nova relação mobile/API.
5. Atualizar `apps/mobile/README.md` quando o estado local mudar.
6. Atualizar `tools/skills/gotrendlabs/README.md` quando criar/renomear skills.
7. Criar nota de memória em `.codex/memories/extensions/ad_hoc/notes/` somente para fechamento/retomada relevante fora do repo.

## Regras

- Specs são fonte de verdade persistente.
- Workflow run é obrigatório para mudança mobile multi-documento.
- Não marcar implementação como concluída sem evidência.
- Se uma mudança mobile alterar fronteira, registrar necessidade de ADR.
- Memória geral deve resumir decisão e retomada, não duplicar specs inteiras.
- Preserve mudanças não relacionadas no worktree.

## Entradas principais

- `docs/specs/state/workflow-runs.md`
- `docs/specs/state/implementation-status.md`
- `docs/specs/state/feature-changelog.md`
- `docs/specs/state/integration-map.md`
- `apps/mobile/README.md`
- `tools/skills/gotrendlabs/README.md`
- `.codex/memories/`

## Saídas esperadas

- estado e memória sincronizados
- changelog atualizado
- retomada clara
- docs e skills descobríveis
