# Workflow: Revisão de Testes

Use para revisar cobertura, aceite e regressões esperadas de uma feature ou contrato.

## Etapas

1. Abrir execução em `workflow-runs.md`.
2. Ler feature alvo, contratos afetados e `docs/specs/testing/`.
3. Mapear cenários unitários.
4. Mapear cenários de integração.
5. Mapear fluxos end-to-end.
6. Mapear regressões por contrato e dependência.
7. Definir quais testes serão backend, frontend, integração, contrato ou fluxo.
8. Acionar `orynth-test-engineer` para implementar ou revisar testes executáveis quando houver código.
9. Atualizar a seção `Testes esperados` da feature quando necessário.
10. Atualizar `docs/specs/testing/` se houver regra transversal.
11. Registrar entrada em `feature-changelog.md`.
12. Fechar workflow.

## Critério de conclusão

- testes esperados estão vinculados a comportamento observável
- regressões estão ligadas a contratos ou fluxos críticos
- pendências estão em `known-gaps.md` ou no próprio workflow
- testes executáveis foram implementados, executados ou registrados como pendência
