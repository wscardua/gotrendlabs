# Workflow: Alterar Feature Existente

Use para alterar comportamento, contrato, status ou critérios de aceite de uma feature existente.

## Etapas

1. Abrir execução em `docs/specs/state/workflow-runs.md`.
2. Ler feature atual, changelog da feature e integração.
3. Registrar objetivo da mudança e artefatos esperados.
4. Atualizar somente a feature afetada e dependências diretas.
5. Passar por `orynth-software-architect` quando houver impacto em contrato, banco, segurança, domínio, eventos ou fronteira.
6. Atualizar contratos explicitamente impactados.
7. Validar arquitetura com `orynth-architecture-guard`.
8. Atualizar testes esperados, regressões e aceite com `orynth-test-strategy`.
9. Atualizar ou planejar testes executáveis com `orynth-test-engineer`.
10. Atualizar `feature-changelog.md`.
11. Atualizar `implementation-status.md` quando código ficar defasado.
12. Atualizar `change-log-specs.md` se a mudança for documental relevante.
13. Fechar workflow ou registrar bloqueio.

## Reversão lógica

Não apagar histórico. Para desfazer uma mudança, registre nova entrada marcando a alteração anterior como `substituida`, `cancelada` ou revertida por novo workflow.
