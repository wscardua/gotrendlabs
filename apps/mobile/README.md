# Mobile

Cliente Flutter mobile do GoTrendLabs. O MVP validado hoje e Android; a estrutura iOS existe para preparacao de simulador, mas depende de Xcode completo ativo no Mac.

O app roda como cliente da FastAPI e usa `http://10.0.2.2:8001` como API local padrao no emulador Android. Imagens de mercado e badges em `/media/...` usam a web local em `http://10.0.2.2:8000`, portanto o Django local precisa aceitar `10.0.2.2` em `GOTRENDLABS_ALLOWED_HOSTS` e escutar em host acessivel pelo emulador.

Para trocar as bases locais:

```bash
flutter run \
  --dart-define=GTL_API_BASE_URL=http://10.0.2.2:8001 \
  --dart-define=GTL_PUBLIC_WEB_BASE_URL=http://10.0.2.2:8000
```

Para exercitar o cadastro local de `PushDevice` sem Firebase, use um token fake explicito:

```bash
flutter run -d emulator-5554 \
  --dart-define=GTL_API_BASE_URL=http://10.0.2.2:8001 \
  --dart-define=GTL_PUBLIC_WEB_BASE_URL=http://10.0.2.2:8000 \
  --dart-define=GTL_PUSH_FAKE_TOKEN=fcm-local-emulator-001 \
  --dart-define=GTL_PUSH_FAKE_PLATFORM=android \
  --dart-define=GTL_PUSH_FAKE_DEVICE_LABEL="Android emulator"
```

Esse modo grava um device de teste em `gotrendlabs_push_devices` apos login, mas nao entrega push real.

No iOS Simulator, as bases locais do Mac devem usar `127.0.0.1`:

```bash
flutter run -d ios \
  --dart-define=GTL_API_BASE_URL=http://127.0.0.1:8001 \
  --dart-define=GTL_PUBLIC_WEB_BASE_URL=http://127.0.0.1:8000
```

Specs principais:

- `docs/specs/architecture/mobile-flutter.md`
- `docs/specs/architecture/mobile-api-contracts.md`
- `docs/specs/features/mobile-mvp.md`
- `docs/specs/features/mobile-ux.md`
- `docs/specs/testing/mobile-acceptance.md`

## MVP implementado

- shell dark-first editorial com bottom navigation: `Hoje`, `Insights`, `Mercados`, `Alertas`, `Busca`
- design system mobile compartilhado em `lib/src/ui/`, com surfaces, headers editoriais, pills, métricas, painéis de estado, skeletons e componentes reutilizáveis
- feed, browse, busca e detalhe de mercado via `GET /markets` e `GET /markets/{slug}`
- auth Bearer simples via `/auth/login`, `/auth/register`, `/auth/session` e `/auth/logout`, com token em secure storage
- favoritos, curtidas, comentarios, preview e criacao de previsao usando apenas FastAPI
- `Hoje` com recorte pessoal `Sua mesa` para mercados negociados e favoritos
- `Mercados` com filtros `Todos`, `Favoritos` e `Posicoes`, baseados nos flags autenticados da API
- alertas com badge de nao lidas no shell e marcacao como lido ao visualizar a tela
- push mobile preparado com repository/controller e provider noop; Firebase/FCM real, permissões nativas e arquivos `google-services.json`/`GoogleService-Info.plist` ficam para etapa aprovada separadamente
- wallet, extrato, recarga educativa, perfil, ranking, badges, busca, confianca e alertas como leitura/acao da API
- tela `Sobre` com versao/build, pacote/plataforma, saude da API e diagnostico seguro para suporte; a UI nao exibe enderecos de API/web, tokens, segredos nem ID interno de usuario
- testes unitarios, widget e repository cobrindo componentes, cards, ticket, filtros pessoais e `Sobre`

Guardrail: o mobile sera cliente da FastAPI. Ele podera manter estado de UI, sessao/token, cache leve e preferencias locais, mas nao deve calcular saldo, payout, probabilidade, reputacao, badges, resolucao, IA ou auditoria.

Push guardrail: o app so registra token de push depois de autenticado e apenas quando houver provider real. Logout normal nao revoga push; revogacao e preferencias sao acoes explicitas via FastAPI. Payloads de push devem conter apenas IDs/rota/evento e sempre buscar o estado real na API ao abrir.

## Validacao local

```bash
flutter pub get
flutter analyze
flutter test
flutter build apk --debug
```

Para simular iOS, tambem deve passar `flutter doctor -v` com Xcode completo e CocoaPods disponiveis.
