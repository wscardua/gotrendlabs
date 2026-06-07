---
name: gotrendlabs-mobile-api-contract-guard
description: Use esta skill para revisar contratos FastAPI consumidos pelo app mobile Flutter do GoTrendLabs, garantindo que o app reutilize OpenAPI/JSON existentes, trate erros previsíveis e não introduza regra crítica local.
---

# GoTrendLabs Mobile API Contract Guard

Use esta skill quando a tarefa envolver integração mobile/API, endpoints, payloads, autenticação mobile, erros, OpenAPI, repositories Flutter ou mudanças em contratos consumidos pelo app.

## Objetivo

Garantir que o app mobile consuma a FastAPI corretamente, com contratos estáveis, erros mapeáveis e sem dependência de Django/templates.

## Fluxo padrão

1. Ler `docs/specs/architecture/mobile-api-contracts.md`.
2. Ler a feature afetada em `docs/specs/features/`.
3. Ler contratos afetados em `docs/specs/contracts/`.
4. Conferir `packages/contracts/openapi/gotrendlabs-api.json` quando houver endpoint/payload existente.
5. Se mudar endpoint, payload ou schema, exigir atualização do OpenAPI.
6. Atualizar testes e estado quando o contrato mobile mudar.

## Regras

- Mobile consome FastAPI JSON; não consome templates Django.
- Reutilize endpoints existentes antes de propor novos.
- Preview de previsão, stake, saldo, reputação, ranking, badges e resolução vêm do backend.
- Erros devem mapear para UX: `unauthenticated`, `forbidden`, `validation`, `domain_state`, `insufficient_balance`, `network`, `server`.
- Atualização otimista no app é permitida só como estado visual reversível.
- Se auth atual for cookie/web e não atender mobile, registrar decisão técnica antes de persistir login mobile.

## Entradas principais

- `docs/specs/architecture/mobile-api-contracts.md`
- `docs/specs/architecture/backend-api.md`
- `docs/specs/contracts/`
- `packages/contracts/openapi/gotrendlabs-api.json`
- `apps/api/backend_api/`

## Saídas esperadas

- contratos mobile validados
- gaps de API listados
- OpenAPI atualizado quando necessário
- erros e estados de UX preservados
