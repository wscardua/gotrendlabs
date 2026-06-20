---
name: gotrendlabs-mobile-test-strategy
description: Use esta skill para definir, revisar ou atualizar testes do app Flutter/mobile do GoTrendLabs, incluindo unit tests, widget tests, repository tests, integration tests, smoke tests Android e QA visual.
---

# GoTrendLabs Mobile Test Strategy

Use esta skill quando a tarefa envolver critérios de aceite mobile, testes Flutter, integração com emulador, regressões de UX ou validação de contratos no app.

## Objetivo

Garantir que o MVP Android seja verificável por testes automatizados, smoke tests e QA visual alinhados às specs.

## Fluxo padrão

1. Ler `docs/specs/testing/mobile-acceptance.md`.
2. Ler a feature mobile afetada.
3. Mapear risco em unit, widget, repository, integration e smoke manual.
4. Validar comandos esperados: `flutter analyze`, `flutter test`, build/run no emulador.
5. Atualizar critérios de aceite quando comportamento ou design mudar.
6. Registrar evidências ou pendências em `docs/specs/state/`.

## Regras

- Testes protegem contratos e comportamento, não só aparência.
- Fluxos críticos: feed -> detalhe, visitante bloqueado, login, preview, previsão, erro de API e wallet.
- Widget tests devem cobrir estados `loading`, `empty`, `error`, `unauthenticated` e bloqueado.
- Testes de compatibilidade mobile devem cobrir headers do `ApiClient`, `/health` com e sem headers, build antigo em `/health`, `426 code=app_update_required` em endpoint não isento, promoção global desse 426 pelo cliente HTTP, manutenção `503` separada e gate Flutter para update obrigatório/opcional.
- QA visual deve testar texto longo, imagem ausente, mercado resolvido, fonte ampliada e tema dark.
- Xcode/CocoaPods não bloqueia Android MVP.

## Entradas principais

- `docs/specs/testing/mobile-acceptance.md`
- `docs/specs/features/mobile-mvp.md`
- `docs/specs/features/mobile-ux.md`
- `docs/specs/architecture/mobile-api-contracts.md`
- `apps/mobile/`

## Saídas esperadas

- matriz de testes mobile
- critérios de aceite objetivos
- comandos de validação
- lacunas e riscos documentados
