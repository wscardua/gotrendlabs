# Estratégia de Testes

## Objetivo

Garantir que cada feature tenha critérios de aceite verificáveis e cobertura suficiente para evolução guiada por specs.

## Princípios

- Testes acompanham contratos e comportamento, não apenas telas.
- Mudanças de spec devem atualizar os testes esperados.
- Features críticas precisam de testes em múltiplos níveis.
- Compatibilidade mobile deve ser testada por build/versionCode: `/health` sem headers, `/health` com build compatível, `/health` com build antigo, middleware `426` em endpoint não isento, cliente web sem bloqueio, gate Flutter para update obrigatório/opcional e promoção global de `426 code=app_update_required` pelo `ApiClient`.

## Níveis mínimos

- unitário: funções e regras isoladas
- integração: fronteiras entre camadas e persistência
- fluxo/end-to-end: jornadas principais do usuário e da operação

## Ciclo recomendado

1. atualizar spec da feature
2. revisar contratos afetados
3. ajustar critérios de aceite
4. definir testes esperados
5. implementar ou revisar código

## Governança

- Mudanças que alterem testes de feature devem atualizar `docs/specs/state/feature-changelog.md`.
- Revisões amplas de testes devem abrir workflow `test-review-cycle`.
- Uma feature não deve ser marcada como `validada` sem evidência de teste ou pendência documentada.
- `gotrendlabs-test-strategy` define o que deve ser testado; `gotrendlabs-test-engineer` transforma isso em testes executáveis e evidência.
