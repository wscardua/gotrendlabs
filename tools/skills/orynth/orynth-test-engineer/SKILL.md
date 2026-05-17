---
name: orynth-test-engineer
description: Use esta skill para implementar, revisar e executar testes concretos de backend, frontend, contratos, banco, HTMX, APIs, fluxos e regressões do Orynth a partir da estratégia de testes e critérios de aceite.
---

# Orynth Test Engineer

Use esta skill quando a tarefa for transformar estratégia de testes em testes executáveis ou revisar evidência real de qualidade.

## Objetivo

Implementar e validar testes práticos para backend e frontend, mantendo aderência às specs, contratos e riscos de regressão.

## Fluxo padrão

1. Verificar workflow aberto em `docs/specs/state/workflow-runs.md`.
2. Ler feature alvo, contratos e `docs/specs/testing/`.
3. Ler saída esperada de `orynth-test-strategy`.
4. Identificar testes backend, frontend, integração, fluxo e regressão.
5. Implementar ou revisar testes executáveis conforme stack existente.
6. Executar testes aplicáveis ou registrar pendência objetiva.
7. Atualizar workflow, estado e changelogs com evidência.

## Regras

- Teste deve verificar comportamento observável, contrato ou risco real.
- Evite testes acoplados a detalhes frágeis de implementação sem ganho claro.
- Backend deve cobrir domínio, API, persistência e erros relevantes.
- Frontend deve cobrir renderização, interação, i18n, estados e fluxos críticos.
- Quando um teste necessário não puder ser implementado, registre pendência em `known-gaps.md` ou no workflow.

## Entradas principais

- `docs/specs/features/`
- `docs/specs/contracts/`
- `docs/specs/testing/`
- `docs/specs/state/workflow-runs.md`
- código existente da plataforma

## Saídas esperadas

- testes executáveis ou plano de lacuna explícito
- evidência de execução ou bloqueio
- regressões cobertas por contrato e fluxo
- atualização de workflow e status
