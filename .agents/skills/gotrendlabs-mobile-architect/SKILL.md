---
name: gotrendlabs-mobile-architect
description: Use esta skill para definir ou revisar arquitetura Flutter/mobile do GoTrendLabs, estrutura do app, navegação, estado, ambiente Android e fronteiras com a FastAPI antes de criar ou alterar o app em apps/mobile.
---

# GoTrendLabs Mobile Architect

Use esta skill quando a tarefa envolver arquitetura do app Flutter, criação do projeto mobile, estrutura de pastas, dependências, navegação, estado, ambiente local ou decisões técnicas de mobile.

## Objetivo

Garantir que o mobile nasça como cliente da FastAPI, com arquitetura Flutter sustentável e sem duplicar regras críticas de domínio.

## Fluxo padrão

1. Verificar workflow aberto em `docs/specs/state/workflow-runs.md`.
2. Ler `docs/specs/architecture/mobile-flutter.md`.
3. Ler `docs/specs/architecture/mobile-api-contracts.md`.
4. Ler `docs/specs/architecture/system-overview.md` e `backend-api.md` quando houver dúvida de fronteira.
5. Definir impacto em `apps/mobile/`, contratos, testes e estado.
6. Indicar necessidade de ADR se mudar estratégia de autenticação, geração de cliente, armazenamento seguro, navegação base ou contrato mobile.

## Regras

- `future-mobile` é cliente; `backend-api` permanece fonte da verdade.
- O app pode manter estado de UI, cache leve, token/sessão e preferências locais.
- O app não calcula saldo, payout, probabilidade, reputação, badges, resolução, IA oficial, ranking ou auditoria como fonte de verdade.
- Ambiente local no emulador Android deve usar `http://10.0.2.2:8001`.
- Mudanças em endpoints, payloads ou schemas exigem atualização de OpenAPI e specs afetadas.
- Estrutura Flutter deve favorecer features isoladas, repositories por contrato e estados explícitos de UX.

## Entradas principais

- `docs/specs/architecture/mobile-flutter.md`
- `docs/specs/architecture/mobile-api-contracts.md`
- `docs/specs/features/mobile-mvp.md`
- `docs/specs/testing/mobile-acceptance.md`
- `apps/mobile/README.md`

## Saídas esperadas

- arquitetura Flutter revisada
- fronteiras por camada preservadas
- decisões técnicas documentadas
- pendências de contrato/teste/status apontadas
