# Workflow: Ciclo de Implementação

Use para implementar, continuar ou revisar uma feature com base nas specs.

## Etapas

1. Abrir execução em `workflow-runs.md`.
2. Ler `implementation-status.md`, `feature-changelog.md`, feature spec e contratos.
3. Confirmar status da spec.
4. Planejar execução por camada.
5. Passar por `gotrendlabs-software-architect` quando a implementação envolver nova estrutura, segurança ou mudança de contrato.
6. Validar arquitetura antes de editar código.
7. Implementar por camada técnica.
8. Implementar ou revisar testes concretos com `gotrendlabs-test-engineer`.
9. Executar ou registrar testes aplicáveis.
10. Atualizar `implementation-status.md`.
11. Registrar lacunas restantes em `known-gaps.md` quando houver.
12. Fechar workflow com evidência de teste ou bloqueio.

## Regra

Se a implementação revelar comportamento não especificado, parar e abrir ou atualizar workflow de spec antes de continuar.
