# Mobile

## Indisponibilidade transitória (branch local 05/11/2026)

O `/health` da FastAPI agora limita duas verificações simultâneas por processo e pode responder 503 degradado sob rajada, sem consultar o banco. O gate do app conserva a sessão, bloqueia a entrada e oferece nova tentativa. A publicação dessa UX depende de release mobile separada do deploy GitHub web/API.

503 por capacidade da FastAPI mantém a sessão e mostra indisponibilidade com nova tentativa explícita no detalhe. `mobile_maintenance` segue separado. Em escrita com resultado `operation_indeterminate`, o app orienta conferir o estado antes de nova tentativa e não faz replay automático. Contrato e aceite: `docs/specs/architecture/mobile-api-contracts.md` e `docs/specs/testing/db-resilience-acceptance.md`. Requer distribuição própria do Flutter; deploy web/API não atualiza instalações existentes.

Wallet agora apresenta `resolution_returns` da FastAPI (valor liberado, ganho líquido e total recebido), e mercados resolved/sealed preservam volume/participação final. 46 testes de regressão e análise estática aprovados na implementação; sem cálculo financeiro local. Distribuir o app somente após implantação do contrato backend.

Web/API implantadas pelas PRs #177/#178 em 2026-10-25; distribuição Flutter ainda pendente. O ajuste corretivo de ACL não muda o contrato mobile. [Recibo produtivo](../../docs/specs/testing/resolution-reliability-production-closeout-20261025.md) e [roteiro](../../docs/specs/operations/resolution-reliability-rollout.md).

Na branch local `feature/mcp-analytics-history`, o ticket inicial envia `prediction_preview_viewed` somente depois de mostrar uma prévia válida da API. A coleta usa o tracker existente e não altera previsão, autorização nem navegação quando falha. O backend informa cobertura por evento ao MCP; a distribuição do app exige release mobile própria.

Atualização 2026-10-17: Cards/painel usam `total_participants` obrigatório, com contagem humana + bot e singular/plural, sem fallback. Flutter mantém o motivo no subtítulo de Trocar escolha. Código validado; distribuição exige próxima release mobile (o workflow GitHub publica web/API). [Fechamento](../../docs/specs/testing/participants-closeout-20261017.md).

Cliente Flutter mobile do GoTrendLabs. O MVP validado hoje e Android; a estrutura iOS existe para preparacao de simulador, mas depende de Xcode completo ativo no Mac.

Analytics proprio: o app envia abertura de abas/detalhe, cliques em cards, busca concluida e abertura/escolha de opcao/clique de confirmacao do ticket para `POST /analytics/events` da FastAPI. Cada navegação real para o detalhe, inclusive A → B → A, registra nova visualização sem contar rebuilds. O identificador aleatorio da instalacao fica em secure storage e a sessao analitica roda em memoria, renovada apos inatividade; logout apaga o identificador. A coleta e de melhor esforco e nao bloqueia o produto. A cobertura de outros controles, fila offline e preferencia de coleta na UI estao registradas em `docs/specs/state/known-gaps.md`.

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

O target iOS minimo e 15.0, alinhado as dependencias mobile atuais de Firebase e autenticacao local.

Specs principais:

- `docs/specs/architecture/mobile-flutter.md`
- `docs/specs/architecture/mobile-api-contracts.md`
- `docs/specs/features/mobile-mvp.md`
- `docs/specs/features/mobile-ux.md`
- `docs/specs/testing/mobile-acceptance.md`

## MVP implementado

- shell dark-first editorial com bottom navigation: `Hoje`, `Ranking`, `Mercados`, `Alertas`, `Busca`, sem tela `Insights` enquanto nao houver contrato recorrente do backend
- design system mobile compartilhado em `lib/src/ui/`, com surfaces, headers editoriais, pills, métricas, painéis de estado, skeletons e componentes reutilizáveis
- feed, browse, busca e detalhe de mercado via `GET /markets` e `GET /markets/{slug}`, com abertura do detalhe incrementando `view_count` pelo mesmo endpoint de tracking usado pelo web
- dados vivos de mercado, detalhe, desempenho, wallet, ledger, recargas e alertas sao reconsultados ao abrir telas criticas, voltar do background, trocar para abas dependentes de mercado e usar pull-to-refresh, sem exigir reiniciar o app
- auth Bearer simples via `/auth/login`, `/auth/register`, `/auth/session` e `/auth/logout`, com `Lembrar login` ligado por padrao; token persistido em secure storage quando ligado e mantido apenas em memoria quando desligado
- cadastro humano exige data de nascimento e informa o limite de 18 anos; cadastro e perfil usam entrada `DD/MM/AAAA`, normalizam para `YYYY-MM-DD`, não permitem limpar o campo obrigatório e apresentam a decisão de maioridade retornada pela FastAPI sem duplicar a regra no app
- cadastro mobile de visitante usa desafio anti-abuso dentro do app via `GET /anti-abuse/challenge`, enviando `anti_abuse_token` e `anti_abuse_answer` para a FastAPI; reCAPTCHA permanece restrito aos fluxos web
- protecao local para sessao lembrada: quando `Lembrar login` esta ligado e o aparelho suporta autenticacao local, login e cadastro oferecem biometria ligada por padrao; a tela de entrada mostra `Entrar com biometria` quando ha sessao lembrada protegida; na reabertura, o app exige biometria ou senha do aparelho antes de ativar o Bearer token persistido; cancelamento deixa a sessao em estado protegido, sem chamar API autenticada nem apagar o token
- gate de manutencao mobile via `GET /health`: falha de backend, status degradado ou `maintenance.mobile_enabled=true` mostram uma tela dark-first de manutencao; o shell mobile permanece bloqueado enquanto a janela estiver ativa
- favoritos, curtidas, comentarios, compartilhamento, preview, criacao de previsao inicial, aumento e troca de posicao usando apenas FastAPI; compartilhar pelo app incrementa `share_count` antes de acionar o share nativo
- mesa de posicao no detalhe: quando `viewer_position.has_position=true`, o ticket mostra escolha atual, movimentos ativos, total ativo, historico resumido e dois frames de acao fechados por padrao, `Aumentar posição` na mesma opcao e `Trocar escolha` para opcao diferente, sempre exigindo preview valido de `/position-preview` antes de confirmar em `/position-actions`
- comprovantes assinados no detalhe autenticado: previsao inicial, cada reforco e cada revisao aparecem separadamente em todos os estados posteriores; cada item abre modal leigo/tecnico carregado por `/predictions/{id}/receipt`, sem calcular ou assinar no aparelho
- `Hoje` com destaque/tendencias apenas de mercados abertos, ordenados por engajamento visual, e recorte pessoal `Sua mesa` para mercados negociados e favoritos
- `Mercados` com filtros `Todos`, `Favoritos` e `Posicoes`, baseados nos flags autenticados da API
- cards de mercado com prazo restante compacto em barra de regressao/urgencia na linha inferior do card, ao lado dos comentarios, mudando de cor conforme o fechamento se aproxima sem aumentar a altura dos cards
- cards com selo de integridade circular apenas em icone no canto superior direito da imagem, preservando thumbnail, tooltip/semantics e cores distintas para registro, finalizacao, falha e historico selado
- detalhe de mercado com hero visual nao navegavel, evitando empilhar a mesma rota ao tocar na imagem
- detalhe com a secao secundaria `Integridade do mercado` depois da previsao/posicao, comprovantes, criterio e resultado, usando copy contextual e `Verificar integridade` sem competir com a acao principal
- grafico de consenso multi-serie, usando uma linha por opcao a partir de `sparkline_series`
- ranking mobile identificado por `@handle`, com badges compactas e overflow `+N` vindos de `/rankings`
- tela `Desempenho` autenticada, acessivel pelo menu e pelo Perfil, consumindo `GET /users/me/performance` para placar, historico de resolucoes, impacto em reputacao, resultado GT₵ educativo e ultimas conquistas sem regra critica local
- alertas com badge de nao lidas no shell e marcacao como lido ao visualizar a tela, sem painel operacional de push
- push mobile usa Firebase/FCM no Android quando `google-services.json` local existe, registra token somente apos autenticacao, cria o canal Android `gtl_default`, trata tap em payloads seguros (`/markets/:slug`, `/wallet`, `/badges`, `/alerts`) e continua exibindo saude/configuracao no `Sobre`
- wallet, extrato, recarga educativa, perfil, ranking, badges, busca, confianca e alertas como leitura/acao da API
- feedback e sugestao de mercado ficam no menu principal e no Perfil; visitante informa nome/email e responde desafio anti-abuso dentro do app, enquanto usuario autenticado envia direto para a fila FastAPI/Admin Ops
- tela `Sobre` com versao/build, pacote/plataforma, saude da API, estado informativo de push e diagnostico seguro para suporte; a UI nao exibe enderecos de API/web, tokens, segredos nem ID interno de usuario
- splash Android e header do shell com wordmark `GoTrendLabs` e tagline alinhada logo abaixo do nome
- testes unitarios, widget e repository cobrindo componentes, cards, ticket, filtros pessoais, ranking, push em `Sobre`, login em memoria/secure storage e `Sobre`

Guardrail: o mobile sera cliente da FastAPI. Ele podera manter estado de UI, sessao/token, cache leve e preferencias locais, mas nao deve calcular saldo, payout, probabilidade, reputacao, badges, resolucao, IA ou auditoria.

Biometria guardrail: biometria/Face ID/Touch ID/fingerprint e senha local do aparelho protegem apenas a sessao lembrada neste dispositivo. O app nao armazena senha da conta, nao envia dado biometrico ao backend e continua validando a sessao restaurada em `/auth/session`.

Push guardrail: o app so registra token de push depois de autenticado e apenas quando houver provider real. Logout normal nao revoga push; revogacao e preferencias sao acoes explicitas via FastAPI. Payloads de push devem conter apenas IDs/rota/evento e sempre buscar o estado real na API ao abrir.

Manutencao guardrail: o app sempre envia `X-GoTrendLabs-Client: mobile`; a FastAPI aplica o bloqueio de manutencao mobile de forma autoritativa e o Admin Ops controla esse modo separadamente da manutencao web. Nao ha entrada operacional visivel nem excecao por papel no app mobile.

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

Antes de gerar artefato para distribuição, todas as alterações (incluindo versão/build) devem estar commitadas e integradas à main. Use checkout limpo da main remota atualizada. O Gradle executa `ops/scripts/check_android_release_source.py` com Python 3: faz fetch de origin/main e bloqueia release se houver alterações locais/arquivos não rastreados ou se HEAD divergir da main remota. Falha de fetch também bloqueia; debug permanece disponível.

Compare também o recibo e as funcionalidades da versão anterior: main limpa não comprova conter código que antes foi empacotado sem commit. Pendências sem reconciliação impedem distribuição. Registre SHA completo, versão/build, canal, checksum e testes no recibo e confira-o antes do upload.

**Pendência identificada em 06/11/2026:** a versão 1.2.1+15 continha MFA e critério compacto a partir de alterações não commitadas do worktree `gotrendlabs-mobile-login-fix`. A versão 1.2.2+16 partiu de main sem essas alterações. MFA reconciliado na branch `fix/mobile-admin-mfa-20261106`; critério compacto requer reconciliação antes da próxima distribuição. Consulte WFLOW-20261106-RELEASE-SOURCE-INTEGRITY.

Build padrao do beta:

```bash
flutter build apk --release \
  --dart-define=GTL_API_BASE_URL=https://gotrendlabs.com.br/api \
  --dart-define=GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br
```

Versao ativa no canal direto do site: `1.0.7+8`.

O build release falha quando `android/key.properties` nao existe. Use `flutter build apk --debug` para validacao local sem assinatura release.

Depois do build, suba o APK pelo Admin Ops em `/admin-ops/mobile-releases/`; o servidor calcula SHA-256 e tamanho, guarda em `MEDIA_ROOT/app_releases/android/` e publica apenas uma release Android ativa por vez. O link publico aponta direto para o arquivo ativo quando existir release. Entrega FCM real depende tambem do backend em producao com `GOTRENDLABS_PUSH_ENABLED=1`, `GOTRENDLABS_PUSH_PROVIDER=fcm`, `GOTRENDLABS_PUSH_DRY_RUN=0` e `GOTRENDLABS_FCM_CREDENTIALS_JSON` configurado fora do Git/Admin Ops.

## Google Play closed testing

O pacote para Google Play Closed testing usa Android App Bundle assinado localmente, sem passar pelo upload de APK do Admin Ops e sem alterar o APK ativo no canal direto do site.

Build padrao do AAB para Play Console:

```bash
flutter build appbundle --release \
  --dart-define=GTL_API_BASE_URL=https://gotrendlabs.com.br/api \
  --dart-define=GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br
```

Versao atual do AAB no teste fechado: `1.2.2+16` (tratamento de indisponibilidade temporaria da PR #188).

Release name no Play Console: `16 (1.2.2)` (nome automático).

Release notes em `pt-BR`:

```text
<pt-BR>
Melhoramos a estabilidade quando o serviço fica temporariamente indisponível. O app agora mostra uma mensagem clara e permite tentar novamente ao consultar o detalhe de um mercado, sem encerrar sua sessão. Operações sem confirmação não são repetidas automaticamente.
</pt-BR>
```

Estado observado no Play Console em 05/11/2026: release `16 (1.2.2)` em `Active tracks` de `Closed testing - Alpha`, atualizada em 05/11/2026. O titular confirmou que ela aparece disponível aos testadores. O rollout foi configurado para 100% do grupo do teste fechado; instalação em dispositivo de um testador ainda não foi verificada neste workflow.

O AAB esperado fica em `build/app/outputs/bundle/release/app-release.aab`. O arquivo `.aab`, APKs, keystores, `android/key.properties` e `google-services.json` permanecem fora do Git.

Pacote enviado ao teste fechado em 05/11/2026: `build/app/outputs/bundle/release/gotrendlabs-1.2.2+16.aab`, 57.608.430 bytes, SHA-256 `3714e1f3f98d1e65f8d2e3908bbed70f0fcece46e2785d054915b6b65ba945a6`. A Console aceitou o código 16 e confirmou target SDK 36 e suporte a 16 KB. Este envio não altera o APK ativo do site.

Para simular iOS, tambem deve passar `flutter doctor -v` com Xcode completo e CocoaPods disponiveis.

## Agenda de resolução — 2026-10-17

O detalhe consome agenda FastAPI (`expected_resolution_at`, original, fuso, versão/classificação) e mostra previsão antes do critério integral. Reagendamento aparece com previsão original; ausência não produz data. Locked usa “Em apuração”; terminais não mostram contagem de fechamento pendente. Sem operações administrativas Flutter. Testes de repository/model/widget atualizados; evidências e limites no relatório `docs/specs/testing/resolution-agenda-results.md` (caminho relativo à raiz).

Detalhe: fechamento e resolução prevista são informações distintas recebidas da FastAPI. Critérios longos mostram quatro linhas, com “Ver critério completo / Recolher critério”; textos curtos não exibem botão. A expansão é apenas visual e preserva o texto integral. Ver `docs/specs/testing/mobile-criteria-deadlines.md`.


### Critério mobile: apresentação anterior restaurada — 17/10/2026

Restaurado ResolutionCriteriaText aprovado em 12/10: prévia de três linhas e leitura integral selecionável em painel inferior rolável com Fechar. Substitui a expansão inline de quatro linhas. Mantém fechamento/resolução prevista; sem mudança de API/MCP. Origem e validações em WFLOW-20261017-RESTORE-MOBILE-CRITERIA.


### Prazos no resumo mobile — 17/10/2026

Fechamento e resolução prevista passam ao rodapé do resumo com divisor e tipografia secundária. Card de critérios mantém apenas a regra e acesso ao painel completo. Labels da FastAPI preservados; sem alteração de API/MCP. Evidências em WFLOW-20261017-MOBILE-DEADLINE-PLACEMENT.

### MFA administrativo (2026-11-06)

Login de contas staff/superuser trata o desafio MFA da API e oferece configuração por chave manual, TOTP e código de recuperação. Sessão só é ativada após verificação; recovery codes são mostrados até confirmação de guarda. Nenhuma operação administrativa foi adicionada ao app. Ver workflow `WFLOW-20261106-MOBILE-MFA`; publicação e smoke com conta real pendentes.
