---
name: gotrendlabs-software-architect
description: Use esta skill para definir arquitetura profissional, estrutura de sistemas, segurança, modularidade, escalabilidade, auditabilidade e decisões técnicas do GoTrendLabs antes de novas features, alterações relevantes ou implementação sensível.
---

# GoTrendLabs Software Architect

Use esta skill quando a tarefa precisar de definição arquitetural, desenho de solução, revisão de segurança ou decisão técnica de impacto.

## Objetivo

Propor arquitetura de software eficiente, segura e sustentável para features e mudanças do GoTrendLabs, antes da implementação.

## Uso obrigatório

Use esta skill antes de codar quando a mudança envolver:

- nova feature
- alteração de contrato
- alteração de banco ou ledger
- autenticação, autorização, sessão ou dados sensíveis
- wallet, stake, resolução, reputação ou ranking
- eventos, scheduler, emails ou operação assíncrona
- fronteiras entre Django, FastAPI, PostgreSQL, scheduler, communications ou admin
- qualquer decisão que possa exigir ADR

## Fluxo padrão

1. Verificar workflow aberto em `docs/specs/state/workflow-runs.md`.
2. Ler feature, contratos, arquitetura, testes e decisões relacionadas.
3. Identificar riscos de segurança, integridade, acoplamento, escalabilidade e operação.
4. Definir responsabilidades por camada.
5. Propor estrutura de módulos, serviços, entidades e integrações.
6. Indicar contratos, testes e ADRs necessários.
7. Encaminhar para `gotrendlabs-architecture-guard` validar aderência ao desenho.

## Regras

- Prefira simplicidade profissional e rastreável a abstrações prematuras.
- Segurança e auditabilidade são requisitos de arquitetura, não ajustes finais.
- Dados financeiros internos, identidade e resolução exigem trilha clara.
- Decisões estruturais devem ser documentadas em ADR.
- Se o design exigir mudar a spec, volte para `gotrendlabs-spec-editor`.

## Entradas principais

- `docs/specs/features/`
- `docs/specs/contracts/`
- `docs/specs/architecture/`
- `docs/specs/testing/`
- `docs/specs/decisions/`
- `docs/specs/state/workflow-runs.md`

## Saídas esperadas

- desenho de solução por camada
- riscos e mitigação
- contratos ou ADRs necessários
- orientação de testes arquiteturais e de segurança
