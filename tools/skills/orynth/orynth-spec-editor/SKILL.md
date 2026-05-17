---
name: orynth-spec-editor
description: Use esta skill para derivar, traduzir, normalizar e atualizar specs técnicas do Orynth a partir da spec funcional, preservando rastreabilidade, impacto controlado e memória operacional do projeto.
---

# Orynth Spec Editor

Use esta skill quando a tarefa principal for mexer nos documentos que orientam o desenvolvimento.

## Objetivo

Transformar a spec funcional em specs técnicas utilizáveis pela IA e manter essas specs consistentes quando o produto mudar.

## Fluxo padrão

1. Para mudança multi-documento, abrir ou atualizar workflow via `docs/specs/state/workflow-runs.md`.
2. Ler a origem funcional em `docs/specs/spec_prediction_social_market_pt.md`.
3. Ler a feature alvo em `docs/specs/features/` quando ela já existir.
4. Revisar contratos associados em `docs/specs/contracts/`.
5. Atualizar apenas os artefatos explicitamente impactados.
6. Revisar testes esperados quando o comportamento mudar.
7. Atualizar `feature-changelog.md`, `change-log-specs.md` e, se necessário, `implementation-status.md`.
8. Se a mudança alterar fronteiras ou fórmulas estáveis, registrar uma decisão em `docs/specs/decisions/`.

## Regras

- Os docs são a fonte da verdade.
- Não reescreva features não impactadas.
- Preserve `id`, rastreabilidade de origem e histórico de versão.
- Ao traduzir conteúdo, não perca o vínculo com a versão base.
- Quando houver incerteza sobre arquitetura, consulte `docs/specs/architecture/`.
- Mudanças de comportamento precisam revisar testes e workflow antes de serem encerradas.

## Entradas principais

- `docs/specs/spec_prediction_social_market_pt.md`
- `docs/specs/features/`
- `docs/specs/contracts/`
- `docs/specs/decisions/`
- `docs/specs/state/`
- `docs/specs/workflows/`

## Saídas esperadas

- specs por feature criadas ou ajustadas
- contratos revisados
- changelog de alterações atualizado
- impacto de implementação sinalizado
