# Workflow: Promover Status de Spec

Use para mover uma spec entre `draft`, `em_revisao`, `aprovada`, `substituida` ou `arquivada`.

## Etapas

1. Abrir execução em `workflow-runs.md`.
2. Confirmar frontmatter e dependências.
3. Validar contratos afetados.
4. Validar testes esperados.
5. Atualizar `status_spec`.
6. Atualizar `implementation-status.md`.
7. Registrar mudança em `feature-changelog.md`.
8. Fechar workflow.

## Critério para `aprovada`

- escopo incluído e excluído claros
- contratos afetados listados
- responsabilidades por camada descritas
- testes esperados e critérios de aceite definidos
