# Workflows

Este diretório define processos canônicos para mudanças guiadas por specs. Use workflows quando a tarefa tocar mais de um artefato, como feature spec, contrato, testes, estado, decisão ou código.

## Objetivo

- evitar documentos órfãos ou descasados
- permitir retomada de onde parou
- manter memória operacional curta e útil
- registrar bloqueios, reversões lógicas e conclusão

## Status de workflow

- `aberto`: execução iniciada
- `em_andamento`: alguma etapa foi concluída
- `bloqueado`: existe pendência explícita
- `concluido`: checklist completo
- `cancelado`: encerrado sem aplicar a mudança
- `substituido`: trocado por outro workflow

## Tipos canônicos

- `new-feature`
- `change-feature`
- `promote-spec`
- `implementation-cycle`
- `test-review-cycle`

## Regra de uso

Toda mudança que afete mais de uma área deve ter uma entrada em `docs/specs/state/workflow-runs.md`.
