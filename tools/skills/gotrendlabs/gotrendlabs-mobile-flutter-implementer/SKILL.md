---
name: gotrendlabs-mobile-flutter-implementer
description: Use esta skill para criar ou alterar código Flutter em apps/mobile do GoTrendLabs seguindo as specs mobile, a arquitetura por features, o design dark-first e os contratos FastAPI.
---

# GoTrendLabs Mobile Flutter Implementer

Use esta skill quando a tarefa pedir criação do projeto Flutter, implementação de telas, repositories, modelos, tema, navegação, testes ou execução no emulador Android.

## Objetivo

Implementar o app Flutter com escopo conservador, aderente às specs e validado no Android.

## Fluxo padrão

1. Ler `docs/specs/architecture/mobile-flutter.md`.
2. Ler `docs/specs/features/mobile-mvp.md` e `mobile-ux.md`.
3. Ler `docs/specs/architecture/mobile-api-contracts.md` para contratos consumidos.
4. Criar/alterar código em `apps/mobile/` seguindo estrutura por feature.
5. Implementar estados explícitos de UX e erros mapeados.
6. Rodar validações Flutter cabíveis e registrar pendências.
7. Atualizar docs/state quando comportamento ou arquitetura mudar.

## Regras

- Não implementar regra crítica local.
- Não iniciar app com landing page; primeira tela deve ser experiência útil.
- No emulador, usar API local `http://10.0.2.2:8001`.
- Sem opção pré-selecionada no ticket de previsão.
- UI deve seguir design dark-first e componentes de `mobile-ux.md`.
- `ApiClient` deve enviar `X-GoTrendLabs-Client`, `X-GoTrendLabs-App-Version` e `X-GoTrendLabs-App-Build` em todas as chamadas usando `package_info_plus`.
- O gate inicial deve tratar `maintenance.mobile_enabled`, health degradado e `mobile.update_required` como estados separados; `mobile.update_available` sem obrigatoriedade não bloqueia o shell.
- `426 code=app_update_required` deve ser tratado no cliente HTTP comum e promovido para estado global de atualização obrigatória; não limite esse tratamento a uma tela ou provider específico.
- Flutter não decide compatibilidade por `versionName`; apenas exibe a política retornada pela FastAPI e usa `download_url` quando atualização obrigatória for sinalizada.
- Preferir implementação incremental: app shell, tema, navegação, feed mock/API, detalhe, auth, previsão.
- Não commitar segredos nem tokens.

## Entradas principais

- `apps/mobile/`
- `docs/specs/architecture/mobile-flutter.md`
- `docs/specs/features/mobile-mvp.md`
- `docs/specs/features/mobile-ux.md`
- `docs/specs/testing/mobile-acceptance.md`

## Saídas esperadas

- código Flutter compilável
- telas e componentes aderentes às specs
- testes Flutter relevantes
- validação no emulador ou pendência explícita
