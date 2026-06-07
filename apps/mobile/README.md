# Mobile

Cliente Flutter Android do GoTrendLabs.

O app roda como cliente da FastAPI e usa `http://10.0.2.2:8001` como API local padrao no emulador Android. Imagens de mercado e badges em `/media/...` usam a web local em `http://10.0.2.2:8000`, portanto o Django local precisa aceitar `10.0.2.2` em `GOTRENDLABS_ALLOWED_HOSTS` e escutar em host acessivel pelo emulador.

Para trocar as bases locais:

```bash
flutter run \
  --dart-define=GTL_API_BASE_URL=http://10.0.2.2:8001 \
  --dart-define=GTL_PUBLIC_WEB_BASE_URL=http://10.0.2.2:8000
```

Specs principais:

- `docs/specs/architecture/mobile-flutter.md`
- `docs/specs/architecture/mobile-api-contracts.md`
- `docs/specs/features/mobile-mvp.md`
- `docs/specs/features/mobile-ux.md`
- `docs/specs/testing/mobile-acceptance.md`

## MVP implementado

- shell dark-first com bottom navigation: `Hoje`, `Insights`, `Mercados`, `Alertas`, `Busca`
- feed, browse, busca e detalhe de mercado via `GET /markets` e `GET /markets/{slug}`
- auth Bearer simples via `/auth/login`, `/auth/register`, `/auth/session` e `/auth/logout`, com token em secure storage
- favoritos, curtidas, comentarios, preview e criacao de previsao usando apenas FastAPI
- wallet, extrato, perfil, ranking, badges e alertas como leitura da API
- testes unitarios, widget e repository basicos

Guardrail: o mobile sera cliente da FastAPI. Ele podera manter estado de UI, sessao/token, cache leve e preferencias locais, mas nao deve calcular saldo, payout, probabilidade, reputacao, badges, resolucao, IA ou auditoria.

## Validacao local

```bash
flutter pub get
flutter analyze
flutter test
flutter build apk --debug
```
