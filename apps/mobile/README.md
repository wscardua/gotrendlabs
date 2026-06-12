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

Para usar FCM real no Android local, registre o app Firebase com o package name `br.com.gotrendlabs.gotrendlabs_mobile`, baixe `google-services.json` e coloque o arquivo em `apps/mobile/android/app/google-services.json`. Esse arquivo e local, ignorado pelo Git e ativa o plugin `google-services` somente nesta maquina/build. Depois do login, o app solicita permissao de notificacao, coleta o token FCM e registra o device autenticado na FastAPI.

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

- shell dark-first editorial com bottom navigation: `Hoje`, `Ranking`, `Mercados`, `Alertas`, `Busca`, deixando `Insights` no menu superior
- design system mobile compartilhado em `lib/src/ui/`, com surfaces, headers editoriais, pills, métricas, painéis de estado, skeletons e componentes reutilizáveis
- feed, browse, busca e detalhe de mercado via `GET /markets` e `GET /markets/{slug}`, com abertura do detalhe incrementando `view_count` pelo mesmo endpoint de tracking usado pelo web
- auth Bearer simples via `/auth/login`, `/auth/register`, `/auth/session` e `/auth/logout`, com `Lembrar login` ligado por padrao; token persistido em secure storage quando ligado e mantido apenas em memoria quando desligado
- favoritos, curtidas, comentarios, compartilhamento, preview e criacao de previsao usando apenas FastAPI; compartilhar pelo app incrementa `share_count` antes de acionar o share nativo
- `Hoje` com destaque/tendencias apenas de mercados abertos, ordenados por engajamento visual, e recorte pessoal `Sua mesa` para mercados negociados e favoritos
- `Mercados` com filtros `Todos`, `Favoritos` e `Posicoes`, baseados nos flags autenticados da API
- cards de mercado com prazo restante compacto em barra de regressao/urgencia na linha inferior do card, ao lado dos comentarios, mudando de cor conforme o fechamento se aproxima sem aumentar a altura dos cards
- detalhe de mercado com hero visual nao navegavel, evitando empilhar a mesma rota ao tocar na imagem
- grafico de consenso multi-serie, usando uma linha por opcao a partir de `sparkline_series`
- ranking mobile identificado por `@handle`, com badges compactas e overflow `+N` vindos de `/rankings`
- alertas com badge de nao lidas no shell e marcacao como lido ao visualizar a tela, sem painel operacional de push
- push mobile usa Firebase/FCM no Android quando `google-services.json` local existe, registra token somente apos autenticacao, cria o canal Android `gtl_default`, trata tap em payloads seguros (`/markets/:slug`, `/wallet`, `/badges`, `/alerts`) e continua exibindo saude/configuracao no `Sobre`
- wallet, extrato, recarga educativa, perfil, ranking, badges, busca, confianca e alertas como leitura/acao da API
- tela `Sobre` com versao/build, pacote/plataforma, saude da API, estado informativo de push e diagnostico seguro para suporte; a UI nao exibe enderecos de API/web, tokens, segredos nem ID interno de usuario
- splash Android e header do shell com wordmark `GoTrendLabs` e tagline alinhada logo abaixo do nome
- testes unitarios, widget e repository cobrindo componentes, cards, ticket, filtros pessoais, ranking, push em `Sobre`, login em memoria/secure storage e `Sobre`

Guardrail: o mobile sera cliente da FastAPI. Ele podera manter estado de UI, sessao/token, cache leve e preferencias locais, mas nao deve calcular saldo, payout, probabilidade, reputacao, badges, resolucao, IA ou auditoria.

Push guardrail: o app so registra token de push depois de autenticado e apenas quando houver provider real. Logout normal nao revoga push; revogacao e preferencias sao acoes explicitas via FastAPI. Payloads de push devem conter apenas IDs/rota/evento e sempre buscar o estado real na API ao abrir.

## Validacao local

```bash
flutter pub get
flutter analyze
flutter test
flutter build apk --debug
```

## APK beta de producao

O canal beta Android fora da Google Play usa APK release assinado, publicado pelo Admin Ops e divulgado discretamente no rodape do site e nas telas de acesso. O APK, keystore, senhas e `android/key.properties` nao entram no Git.

Crie o arquivo local `apps/mobile/android/key.properties` a partir de `apps/mobile/android/key.properties.example`:

```properties
storePassword=change-me
keyPassword=change-me
keyAlias=gotrendlabs-release
storeFile=/absolute/path/to/gotrendlabs-release.jks
```

Build padrao do beta:

```bash
flutter build apk --release \
  --dart-define=GTL_API_BASE_URL=https://gotrendlabs.com.br/api \
  --dart-define=GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br
```

Versao desta fatia: `1.0.2+3`.

O build release falha quando `android/key.properties` nao existe. Use `flutter build apk --debug` para validacao local sem assinatura release.

Depois do build, suba o APK pelo Admin Ops em `/admin-ops/mobile-releases/`; o servidor calcula SHA-256 e tamanho, guarda em `MEDIA_ROOT/app_releases/android/` e publica apenas uma release Android ativa por vez. O link publico aponta direto para o arquivo ativo quando existir release. Entrega FCM real depende tambem do backend em producao com `GOTRENDLABS_PUSH_ENABLED=1`, `GOTRENDLABS_PUSH_PROVIDER=fcm`, `GOTRENDLABS_PUSH_DRY_RUN=0` e `GOTRENDLABS_FCM_CREDENTIALS_JSON` configurado fora do Git/Admin Ops.

Para simular iOS, tambem deve passar `flutter doctor -v` com Xcode completo e CocoaPods disponiveis.
