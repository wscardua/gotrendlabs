---
name: gotrendlabs-postgres-modeling
description: Use esta skill para definir ou revisar a modelagem PostgreSQL do GoTrendLabs com foco em integridade relacional, ledger, auditabilidade, versionamento de estado e suporte consistente às regras de domínio.
---

# GoTrendLabs Postgres Modeling

Use esta skill quando a tarefa principal envolver persistência, esquema relacional ou rastreabilidade de dados.

## Objetivo

Garantir que o banco suporte o domínio sem esconder regra de negócio e sem perder histórico importante.

## Fluxo padrão

1. Verificar workflow aberto quando a modelagem alterar contratos, estado ou implementação.
2. Ler a feature alvo em `docs/specs/features/`.
3. Ler `docs/specs/architecture/database.md`.
4. Ler contratos relevantes, especialmente wallet, estados e reputação.
5. Mapear entidades, relacionamentos, constraints e índices.
6. Validar impacto em auditabilidade, extrato, performance e suporte operacional.
7. Registrar impacto em contratos, testes e status quando necessário.

## Regras

- O banco persiste a decisão; ele não substitui o domínio.
- Use ledger para movimentos financeiros internos.
- Preservar trilha de resolução, moderação e ajustes manuais.
- Estados relevantes precisam ser historicamente rastreáveis quando isso afetar operação ou confiança.
- Índices devem acompanhar os padrões principais de leitura do produto e do admin.
- Alteração de persistência que muda comportamento precisa passar por spec e workflow.

## Entradas principais

- `docs/specs/features/`
- `docs/specs/architecture/database.md`
- `docs/specs/contracts/`
- `docs/specs/state/integration-map.md`

## Saídas esperadas

- proposta de entidades e relacionamentos
- constraints e índices coerentes
- suporte a ledger e auditabilidade
- compatibilidade com fluxos de leitura e operação
