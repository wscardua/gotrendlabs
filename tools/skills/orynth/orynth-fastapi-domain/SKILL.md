---
name: orynth-fastapi-domain
description: Use esta skill para implementar regras de domínio, autenticação, serviços e endpoints do Orynth em FastAPI/Python, mantendo o backend como fonte de verdade e preservando contratos estáveis para frontend, admin e automações.
---

# Orynth FastAPI Domain

Use esta skill quando a tarefa principal estiver na camada de domínio e API em Python/FastAPI.

## Objetivo

Centralizar regras críticas do produto em serviços e endpoints claros, auditáveis e alinhados às specs técnicas.

## Fluxo padrão

1. Verificar workflow de implementação aberto quando houver mudança multi-documento.
2. Ler a feature alvo em `docs/specs/features/`.
3. Ler `docs/specs/architecture/backend-api.md`.
4. Ler contratos associados em `docs/specs/contracts/`.
5. Revisar dependências e efeitos colaterais em `docs/specs/state/integration-map.md`.
6. Implementar a regra de domínio e os endpoints necessários.
7. Registrar impacto em testes, contratos e estado quando o comportamento mudar.

## Regras

- O backend é a fonte principal da verdade.
- Contratos devem ser explícitos e previsíveis.
- Erros precisam ser consistentes para UI, admin e operação.
- Regras de saldo, reputação e estados de mercado não devem ficar espalhadas.
- Mudanças de shape em payloads exigem revisão de contratos e testes.
- Se a implementação exigir regra nova, atualizar spec antes de concluir.

## Entradas principais

- `docs/specs/features/`
- `docs/specs/architecture/backend-api.md`
- `docs/specs/contracts/`
- `docs/specs/testing/`
- `docs/specs/state/`

## Saídas esperadas

- serviços e endpoints alinhados à spec
- regras críticas centralizadas
- erros previsíveis e auditáveis
- integração clara com eventos, wallet e estados
