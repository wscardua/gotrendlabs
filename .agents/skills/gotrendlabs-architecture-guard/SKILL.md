---
name: gotrendlabs-architecture-guard
description: Use esta skill para validar fronteiras arquiteturais do GoTrendLabs, impedir mistura de responsabilidades entre camadas e revisar impactos estruturais de novas features ou mudanças de spec.
---

# GoTrendLabs Architecture Guard

Use esta skill quando a tarefa exigir decidir onde uma responsabilidade deve viver ou verificar se uma proposta está respeitando a arquitetura.

## Objetivo

Proteger a separação entre frontend web, futuro mobile, backend, banco, scheduler, comunicações e admin.

## Fluxo padrão

1. Verificar se a mudança faz parte de um workflow aberto.
2. Ler a feature alvo.
3. Ler os contratos associados.
4. Revisar os docs de arquitetura relevantes.
5. Mapear responsabilidades por camada.
6. Sinalizar violações, orientar correção e indicar necessidade de ADR.

## Regras

- `frontend-web` não calcula regras críticas.
- `future-mobile` será cliente e também não calcula regras críticas.
- `backend-api` é a fonte da verdade do domínio.
- `database` persiste; não decide política de produto sozinho.
- `scheduler-jobs` executa automações temporais, não cria regra nova.
- `communications` reage a eventos, não duplica elegibilidade de domínio.
- `admin-ops` opera o sistema, mas não substitui contratos do backend.
- `apps/api/backend_api/` é o runtime FastAPI; `apps/web/django/` concentra apps Django com labels historicos preservados; `apps/web/templates/` e `apps/web/static/` concentram templates/assets web; `packages/contracts/openapi/` versiona o snapshot OpenAPI; `ops/` concentra deploy, scripts e Docker local; `apps/mobile/` segue reservado para migração futura.
- Mudanças de fronteira devem atualizar workflow e decisões.

## Entradas principais

- `docs/specs/architecture/`
- `docs/specs/features/`
- `docs/specs/contracts/`
- `docs/specs/decisions/`
- `docs/specs/state/workflow-runs.md`

## Saídas esperadas

- validação de fronteiras
- alertas de acoplamento
- necessidade de ADR quando houver mudança estrutural
