# Workflow: Nova Feature

Use para propor e estruturar uma feature ainda inexistente.

## Etapas

1. Abrir execução em `docs/specs/state/workflow-runs.md`.
2. Criar spec em `docs/specs/features/` com frontmatter completo.
3. Declarar dependências, camadas impactadas e contratos afetados.
4. Passar por `orynth-software-architect` para desenho técnico, segurança e impactos.
5. Criar ou atualizar contratos necessários.
6. Validar fronteiras com `orynth-architecture-guard`.
7. Definir testes esperados e critérios de aceite com `orynth-test-strategy`.
8. Definir testes executáveis esperados com `orynth-test-engineer` quando houver código.
9. Atualizar `implementation-status.md`.
10. Criar entrada em `feature-changelog.md`.
11. Atualizar `integration-map.md`.
12. Registrar ADR se houver nova fronteira, regra estrutural ou decisão irreversível.
13. Fechar workflow como `concluido` ou marcar bloqueios.

## Evidência mínima para concluir

- feature spec existe
- contratos afetados estão listados
- testes esperados existem na feature
- estado e changelog foram atualizados
- revisão de arquitetura e segurança foi registrada ou justificada
