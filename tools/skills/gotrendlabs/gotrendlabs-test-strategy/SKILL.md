---
name: gotrendlabs-test-strategy
description: Use esta skill para definir critérios de aceite, cenários de teste e impacto de regressão das features do GoTrendLabs com base nas specs técnicas e nos contratos compartilhados.
---

# GoTrendLabs Test Strategy

Use esta skill quando a tarefa principal for definir, revisar ou atualizar testes esperados de uma feature.

## Objetivo

Garantir que mudanças de spec e implementação permaneçam cobertas por testes e critérios de aceite verificáveis.

## Fluxo padrão

1. Verificar workflow aberto ou abrir `test-review-cycle` quando a revisão tocar docs.
2. Ler a feature alvo.
3. Ler os contratos afetados.
4. Revisar `docs/specs/testing/`.
5. Listar cenários unitários, de integração e de fluxo.
6. Mapear regressões esperadas.
7. Atualizar `feature-changelog.md` e pendências quando testes mudarem.

## Regras

- Testes acompanham comportamento e contratos.
- Mudanças de spec devem atualizar testes esperados.
- Cada feature deve declarar critérios de aceite objetivos.
- Regressão deve ser mapeada pelo que pode quebrar, não só pela tela afetada.
- Uma feature só vira `validada` com evidência de teste ou pendência justificada.

## Entradas principais

- `docs/specs/features/`
- `docs/specs/contracts/`
- `docs/specs/testing/`
- `docs/specs/state/`
- `docs/specs/workflows/`

## Saídas esperadas

- cenários de teste
- matriz de cobertura
- regressões a proteger
- critérios de aceite revisados
