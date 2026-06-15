# Feature Changelog

## 2026-06-15 — Publicação mobile de posição e anti-abuso

- PR #82 publicou em `main` a fase mobile de reforço/revisão de posição e o desafio anti-abuso para cadastro, feedback e sugestão de visitantes.
- GitHub Actions `GoTrendLabs CI and Deploy` run `27542726255` concluiu `test` e `deploy` com sucesso.
- Produção respondeu `/api/health` saudável, `/api/anti-abuse/challenge` com `prompt`/`token`/`expires_at`, `/api/openapi.json` com `/anti-abuse/challenge`, `/position-preview` e `/position-actions`, e `/api/markets` com dados públicos.

## 2026-06-14 — FEAT-MOBILE-001 desafio anti-abuso e contribuição mobile

- FastAPI ganhou `GET /anti-abuse/challenge`, retornando desafio simples com token assinado e expiração curta para clientes mobile.
- Payloads de cadastro, sugestão de mercado e feedback passaram a aceitar `anti_abuse_token` e `anti_abuse_answer`, mantendo reCAPTCHA v2 como mecanismo web e validando o desafio mobile apenas no backend.
- App Flutter passou a exibir o desafio dentro do cadastro, feedback e sugestão de mercado para visitantes, sem enviar o usuário para fora do app.
- Feedback e sugestão por visitante agora validam nome/email e mantêm erros visíveis no bottom sheet; usuários autenticados continuam enviando sem desafio.
- `Sugerir mercado` passou a aparecer no menu principal do app, além do Perfil, usando categorias ativas de `GET /taxonomy`.

## 2026-06-14 — FEAT-MOBILE-001 reforço e revisão de posição mobile

- App Flutter passou a interpretar `viewer_position` de `GET /markets/{slug}` e trocar o ticket de previsão inicial por uma mesa de posição quando o usuário já possui posição ativa.
- Mobile passou a consumir `POST /markets/{slug}/position-preview` e `POST /markets/{slug}/position-actions` para reforço/revisão, mantendo `/predict` reservado à primeira previsão.
- Mesa de posição exibe opção ativa, entradas abertas, total ativo, crédito possível agregado, histórico resumido, reforços/revisões restantes e motivos de bloqueio retornados pela FastAPI.
- Reforço mobile mantém a mesma opção ativa, exige preview válido e mostra novo total ativo, reforços restantes e crédito possível calculados pela API.
- Revisão mobile permite apenas opção diferente, exige preview válido e mostra entradas encerradas, penalidade, nova posição estimada, revisões restantes e crédito possível calculados pela API.
- UX mobile passou a apresentar reforço como `Aumentar posição` e revisão como `Trocar escolha`, reduzindo jargão sem alterar os contratos FastAPI `reinforcement`/`revision`.
- Ações de posição no mobile passaram a aparecer como frames fechados por padrão, com resumo e contador/bloqueio no cabeçalho, abrindo somente a ação escolhida pelo usuário.
- Prévia de reforço/revisão com campo `allowed` ausente passou a ser tratada como bloqueada pelo app, exigindo confirmação explícita da FastAPI antes de liberar ação.
- Testes Flutter de repository e widget cobrem chamadas de posição, reforço, revisão com penalidade e bloqueios de backend.

## 2026-06-14 — FEAT-PRED-001 reforço e revisão de posição web-first

- FastAPI ganhou contratos autenticados para prévia e criação de reforço/revisão de posição, mantendo `/predict` reservado à primeira previsão.
- `gotrendlabs_predictions` passou a suportar múltiplas posições auditáveis por usuário/mercado, com `action_type`, sequência e supersedência para posições revisadas.
- Revisão preserva histórico, libera posições antigas, aplica `prediction_revision_penalty` e bloqueia nova posição com o valor restante.
- Mutações de previsão/posição passaram a usar lock transacional por usuário/mercado para impedir concorrência entre primeira previsão, reforços e revisões.
- Auditoria de resolução considera apenas posições `resolved`; posições `revised` permanecem auditáveis no histórico/sparkline sem inflar liquidação.
- Admin Ops Config ganhou seção `Previsões e posições` para ajustar grupos de reforço e revisão, incluindo limite máximo de reforços, limite de revisões, janela de corte, penalidade e mínimos de GT₵ sem deploy.
- Detalhe web de mercado passou a mostrar reforço/revisão para usuários com posição ativa, incluindo resumo das entradas abertas, total afetado pela revisão e custo percentual; mobile passou a consumir os mesmos contratos FastAPI em fase publicada posteriormente pela PR #82.

## 2026-06-13 — FEAT-REP-001 badges conquistadas como propriedade histórica

- Admin Ops separou exibição histórica (`is_active`) de novas concessões (`rule_active`) para badges.
- A ação de pausa de badge agora interrompe somente novas concessões, preservando conquistas já registradas.
- Catálogo público/autenticado continua exibindo badges pausadas para todos, com estado de concessão pausada quando aplicável.
- Ranking e compartilhamento público por token continuam exibindo badges pausadas para quem já conquistou.
- Ocultar a badge com `is_active=false` remove do catálogo, ranking e compartilhamento público sem apagar conquistas persistidas.

## 2026-06-13 — FEAT-MOBILE-001 manutenção mobile independente

- Admin Ops Config ganhou controle separado de `Manutenção do app`, salvo no runtime JSON com mensagem propria, sem acoplar ao modo manutencao web.
- FastAPI passou a enriquecer `GET /health` com `maintenance.mobile_enabled`, `maintenance.mobile_message`, `checks.api` e `checks.database`, mantendo `status: ok` quando saudavel e retornando degradado quando o banco falha.
- O app Flutter envia `X-GoTrendLabs-Client: mobile`, checa `/health` no boot e mostra tela dark-first de manutencao quando a API falha, fica degradada ou o modo mobile esta ativo.
- Durante manutencao mobile, FastAPI bloqueia chamadas mobile nao isentas com `503`/`code=mobile_maintenance`; nao ha excecao por staff ou superuser no app.
- `AuthResponse` e `/auth/session` permanecem sem expor `is_superuser` no contrato publico; o gate mobile usa `GET /health` e a regra autoritativa da API.
- APK Android beta `1.0.5 (6)` publicada em produção no canal direto, com `/app/android/latest.json` apontando para o arquivo ativo e SHA-256 `c061681f2495759cca2d2eaf38282541d4a82fd1309fefb4037f9f4ac0b2109b`.

## 2026-06-13 — FEAT-MOBILE-001 autenticação biométrica local

- App mobile ganhou proteção local para sessões lembradas: com `Lembrar login` ligado e suporte do aparelho, a biometria vem ligada por padrão no login e a reabertura exige biometria ou senha do aparelho antes de ativar o Bearer token persistido.
- O token salvo agora pode ser lido sem ser instalado em memória; cancelamento ou falha do desbloqueio mantém a sessão em estado `Sessão protegida`, sem chamada autenticada e sem apagar o token persistido.
- Login sheet passou a oferecer `Proteger sessão com biometria` ligada por padrão no login e cadastro quando o aparelho suporta autenticação local; quando há sessão lembrada protegida, a tela de entrada mostra `Entrar com biometria`; Perfil ganhou o controle `Proteção local` para ativar/desativar a preferência neste dispositivo.
- Android passou a declarar `USE_BIOMETRIC`, usar `FlutterFragmentActivity`, `minSdk >= 24` e tema AppCompat para o diálogo biométrico; iOS ganhou `NSFaceIDUsageDescription`.
- A mudança não cria endpoint, não altera OpenAPI e não envia dados biométricos ao backend; `/auth/session` continua validando a sessão restaurada.
- APK Android beta `1.0.4 (5)` publicada em produção no canal direto, com `/app/android/latest.json` apontando para o arquivo ativo e SHA-256 `43f8c1184ce7c913070d9bc2c09344a70f2ed8f4c14a12749d8e688d831bc81c`.

## 2026-06-12 — FEAT-NOTIFY-001 / FEAT-MOBILE-001 push FCM real Android

- Admin Ops Push mobile ganhou aba `Dispositivos` para listar devices registrados, status, plataforma, versão/build, hash parcial do token e agregados de entrega, sem expor token bruto.
- App Android passou a inicializar Firebase opcionalmente, aplicar `google-services` apenas quando `google-services.json` local existir e manter o arquivo fora do Git.
- Flutter passou a coletar token FCM somente após autenticação, registrar `PushDevice` pela FastAPI, manter `GTL_PUSH_FAKE_TOKEN` para QA sem entrega real e mostrar estado seguro em `Sobre` sem expor token.
- Android ganhou permissão `POST_NOTIFICATIONS`, canal nativo `gtl_default` e metadado default de FCM para exibir notificações em Android 8+.
- Payloads FCM seguros agora abrem rotas permitidas (`/markets/:slug`, `/wallet`, `/badges`, `/alerts`) e o app busca o estado real na FastAPI ao abrir.
- Daemon de `communications` passou a enviar FCM real via Firebase Admin SDK quando `GOTRENDLABS_PUSH_ENABLED=1`, provider `fcm`, dry-run desligado e `GOTRENDLABS_FCM_CREDENTIALS_JSON` estiver configurado fora do Git/Admin Ops.
- Sender FCM grava `provider_message_id` em sucesso, agenda retry em falhas transitórias e invalida `PushDevice` quando o provedor rejeita token.
- Processamento de `PushDelivery` passou por revisão de segurança operacional: claim em transação curta, envio FCM fora de lock longo e recuperação de entregas antigas em `sending`.
- Contadores/filtros da aba `Dispositivos` em Admin Ops passaram a seguir status mutuamente exclusivo, alinhado ao rótulo renderizado na tabela.
- Defaults seguros continuam `GOTRENDLABS_PUSH_ENABLED=0`, `GOTRENDLABS_PUSH_PROVIDER=none` e `GOTRENDLABS_PUSH_DRY_RUN=1`.

## 2026-06-11 — FEAT-MOBILE-001 feed, ranking e sessão mobile

- Tela `Hoje` passou a destacar apenas mercados abertos e ordenar destaque/tendências por engajamento visual usando campos já retornados por `GET /markets`, sem criar regra de domínio local.
- Cards mobile passaram a exibir prazo restante compacto em barra de regressão/urgência na linha inferior do card, ao lado dos comentários, com cor que evolui conforme o fechamento se aproxima; o detalhe passou a usar hero não navegável, evitando empilhar a mesma rota ao tocar na imagem do mercado.
- Confirmação de previsão passou a usar bottom sheet com `SafeArea` e área rolável para evitar overflow em aparelho físico, viewport compacto ou fonte ampliada.
- Gráfico de consenso mobile passou a renderizar uma linha por opção usando `sparkline_series` da FastAPI.
- Ranking mobile passou a identificar participantes por `@handle` e exibir badges compactas com overflow `+N`, reutilizando `badges` e `badges_total` de `/rankings`.
- Ranking passou a ocupar a segunda aba da bottom navigation no lugar de `Insights`; `Insights` foi movido para o menu superior.
- Menu superior passou a seguir a ordem Wallet, Badges, Insights, Suporte, Política e segurança, Sobre e Sair; sugestão de mercado continua acessível pelo Perfil.
- Estado de push mobile saiu de `Perfil` e `Alertas` e passou para `Sobre` como item informativo de saúde/configuração do build; push real/FCM continua fora do escopo.
- Mobile passou a incrementar `view_count` ao abrir o detalhe do mercado, alinhando a semântica do web; `share_count` permanece incrementado na ação real de compartilhamento.
- Login mobile ganhou `Lembrar login` ligado por padrão; quando desligado, o token Bearer fica apenas em memória e não é persistido no secure storage.
- Splash Android e header do shell mobile foram refinados para manter `Preveja antes do consenso.` alinhado logo abaixo de `GoTrendLabs`.
- Versão mobile desta fatia definida como `1.0.2+3` para publicação Android beta após merge.
- APK Android beta `1.0.2 (3)` publicada em produção no canal direto, com `/app/android/latest.json` apontando para o arquivo ativo e SHA-256 `ae52faaf0525cd22dd45da3ced89ba6f7f208864da3c7c26384e9a0b0c3337bb`.

## 2026-06-11 — FEAT-AUTH-001 / FEAT-NOTIFY-001 login social e emails críticos

- Login social deixou de ser placeholder e passou a usar OAuth real para Google, Facebook e X, com Django cuidando de start/callback e FastAPI criando/vinculando usuário, sessão e auditoria.
- Vínculo social passou a exigir identidade externa existente ou email verificado pelo provedor para conta já existente, evitando duplicidade silenciosa e vínculo por email não confiável.
- X OAuth2 passou a aceitar conclusão de cadastro com email informado pelo usuário quando o provedor não retorna email, exigindo token pendente assinado pela FastAPI, criando conta limitada e disparando confirmação imediata; identidades X já vinculadas entram direto mesmo sem email no retorno do provedor.
- Emails críticos de autenticação (`user.welcome` em conta nova, `user.email_confirmation` em cadastro/reenvio/mudança de email e `account.password_reset`) passaram a tentar envio imediato após commit, mantendo fallback para outbox/daemon.
- Emails transacionais passaram a receber rodapé institucional automático no renderizador central; o conteúdo do rodapé agora é customizável pelo template especial `system.transactional_footer`, com fallback seguro no código.
- Eventos de produto, como mercado fechado/resolvido e crédito recebido, continuam sendo drenados pelo daemon.

## 2026-06-08 — FEAT-MOBILE-001 identidade nativa do app

- Nome exibido do app iOS ajustado para `GoTrendLabs`, removendo o sufixo técnico `Mobile` do launcher.
- Ícones de launcher iOS e Android foram regenerados a partir do símbolo de constelação do logo do site, mantendo a marca visual alinhada ao web; no iOS, o asset catalog inclui variantes `dark` e `tinted` para evitar adaptação automática ruim do sistema.
- Splash/launch theme Android foi alinhado ao app dark-first, substituindo a tela intermediária branca por uma abertura em fundo escuro com lockup da marca, badge de constelação, tagline e configuração Android 12+ com ícone/branding dedicados.
- A mudança é apenas de branding nativo: contratos FastAPI, OpenAPI, autenticação, regras de domínio e distribuição beta permanecem inalterados.

## 2026-06-08 — FEAT-MOBILE-001 beta Android pelo site

- Adicionado canal publico discreto para download de APK Android beta fora da Google Play, com CTA direto no rodape, nas telas de acesso e nas paginas de compartilhamento quando houver release ativa, e estado "Android em breve" quando nao houver release.
- Adicionado estado `iOS em breve` ao lado do CTA Android, sem link de download nesta etapa.
- Adicionado `/app/android/latest.json` com metadados da release Android ativa para uso futuro pelo app.
- Admin Ops ganhou `/admin-ops/mobile-releases/` para upload de APK, calculo servidor-side de SHA-256/tamanho e ativacao de uma unica release Android por vez.
- APKs ficam em `MEDIA_ROOT/app_releases/android/` e sao servidos por `/media/app_releases/android/...`; APK, keystore, senhas e `android/key.properties` permanecem fora do Git.
- Build Android release passou a exigir signing local via `apps/mobile/android/key.properties`; o exemplo versionado fica em `key.properties.example`.
- Caddy de producao passou a rotear `/api/*` para `fastapi:8001` removendo o prefixo `/api`.
- Build beta documentado com `GTL_API_BASE_URL=https://gotrendlabs.com.br/api`, `GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br` e `GTL_PUSH_FIREBASE_ENABLED=false`.
- Google Play, auto-update no app e envio FCM real seguem fora desta etapa.

## 2026-06-08 — FEAT-NOTIFY-001 / FEAT-MOBILE-001 push mobile noop

- Adicionada fundação de push mobile com `PushDevice`, `PushEventPolicy`, `PushTemplate`, `PushDelivery` e `PushPreference`, mantendo toda push derivada de `gotrendlabs_user_notifications`.
- FastAPI passou a expor endpoints autenticados para registrar/listar/revogar dispositivos e consultar/alterar preferências de push.
- Daemon operacional passou a drenar `PushDelivery` com provider `none`/dry-run, supressão quando desligado e invalidação automática de token rejeitado.
- Admin Ops ganhou `Política de Push` com templates/event policies por evento, fallback visível, preview seguro, logs filtráveis, teste manual por `PushDevice` e saúde de push no Dashboard sem expor token, payload sensível ou segredo FCM.
- A saúde de push no Dashboard foi ajustada para funcionar também no processo FastAPI standalone, inicializando o contexto Django antes de consultar modelos de `communications`.
- Flutter ganhou `features/push` com repository/controller, `NoopPushTokenProvider` e `FakePushTokenProvider` controlado por `GTL_PUSH_FAKE_TOKEN` para QA local; Firebase/dependências reais seguem fora desta fase.
- Defaults seguros: `GOTRENDLABS_PUSH_ENABLED=0`, `GOTRENDLABS_PUSH_PROVIDER=none`, `GOTRENDLABS_PUSH_DRY_RUN=1`.
- OpenAPI, specs mobile/communications, README e critérios de aceite foram atualizados para a fase noop/dry-run.

## 2026-06-08 — FEAT-MOBILE-001 suporte iOS Simulator

- Gerada estrutura iOS Flutter em `apps/mobile/ios`, mantendo o app como cliente da FastAPI e sem alterar contratos, OpenAPI ou regras críticas de domínio.
- `.metadata` passou a registrar Android e iOS como plataformas do projeto mobile.
- README e specs mobile passaram a documentar que o iOS Simulator usa `127.0.0.1` para acessar FastAPI/Django locais, enquanto o emulador Android continua usando `10.0.2.2`.
- Critérios de aceite passaram a separar Android MVP de simulação iOS local, exigindo Xcode completo, CocoaPods e device iOS listado por `flutter devices`.
- Validação local confirmou `flutter doctor -v` sem issues, app abrindo no iPhone 17 e iPhone 17 Pro Max Simulator e telas carregando dados da API local.
- Homologação iOS ampla, TestFlight, App Store, push nativo e QA visual completo seguem fora desta entrega.

## 2026-06-07 — FEAT-MOBILE-001 refresh visual Android

- App Flutter Android recebeu refresh visual dark-first/editorial no tema, shell, cards de mercado, detalhe, ticket de previsão, comunidade, wallet, ranking, alertas, busca, perfil, badges, confiança e bottom sheets.
- Adicionada camada compartilhada de componentes visuais mobile para headers editoriais, superfícies, métricas, pills, skeletons e estados vazios/erro.
- Tela `Mercados` passou a ter recortes `Todos`, `Favoritos` e `Posições`, filtrando pelos flags autenticados `viewer_has_favorite` e `viewer_has_prediction` retornados pela FastAPI.
- Tela `Hoje` passou a exibir `Sua mesa` para usuários autenticados com atalhos para posições, favoritos e mercados com posição em fechamento, sem criar regra de domínio local.
- Cards de mercado passaram a sinalizar quando o usuário já possui posição ou favorito naquele mercado.
- Adicionada tela mobile `Sobre`, acessível pelo menu e pelo perfil, com versão/build, saúde da API, dados mínimos da sessão e cópia de diagnóstico sem token, segredo ou endereço de API.
- A mudança é somente UX/UI: contratos FastAPI, OpenAPI, autenticação e regras críticas de domínio permanecem inalterados e autoritativos no backend.
- Critérios de QA visual mobile foram atualizados para exigir consistência do design system nas telas principais e secundárias.
- Status de implementação: `parcial`.

## 2026-06-07 — FEAT-MOBILE-001 MVP Flutter Android

- Criado projeto Flutter em `apps/mobile` para Android, com tema dark-first GoTrendLabs e bottom navigation `Hoje`, `Insights`, `Mercados`, `Alertas`, `Busca`.
- Feed, browse, busca e detalhe de mercado consomem a FastAPI local; o emulador usa `http://10.0.2.2:8001`.
- Auth mobile v1 usa Bearer simples retornado pela FastAPI e armazenado em secure storage, sem refresh token nesta fatia.
- Favoritos, curtidas, comentários, preview e criação de previsão chamam apenas endpoints backend; o app não calcula saldo, probabilidade, payout, reputação, badges ou resolução como fonte de verdade.
- Wallet, perfil, ranking, badges e alertas foram implementados como leitura da API.
- Perfil mobile passou a expor catalogo de badges, imagens de badges via `/media`, convite por referral, atalhos com icones para wallet/ranking/sair e forms de suporte/sugestao alinhados a web.
- Sugestao de mercado mobile passou a carregar categorias ativas de `GET /taxonomy`; feedback mobile passou a usar as opcoes publicas da web sem seletor de prioridade.
- Cards de mercado mobile passaram a resolver midia pelo web base, sem gerar iniciais locais de categoria nem sobrepor `thumb` quando `image_url` existir; fallback visual permanece apenas de apresentacao.
- Ticket de previsao mobile passou a espelhar o preview web com `Opcao escolhida`, `Credito possivel se acertar` e `Credito reservado`, atualizando o retorno via `/prediction-preview` com debounce ao selecionar opcao ou mover o controle.
- Wallet mobile ganhou recarga controlada com elegibilidade, pendencia, historico e solicitacao por `/users/me/wallet/recharge-requests`; o contrato passou a expor `available_gtl`, `min_balance_gtl` e `eligible`, mantendo o `POST` como autoridade de dominio.
- Ranking mobile passou a carregar filtros de categoria, subcategoria e evento a partir de `/rankings`, como na web.
- Mobile passou a expor `Politica de uso`, `Conceitos` e `Seguranca` em tela publica de confianca, acessivel pelo menu e perfil.
- Mensagens de erro mobile passaram a traduzir validacoes FastAPI comuns para copy final, evitando payload tecnico na UI.
- Validações locais: `flutter analyze`, `flutter test`, `flutter doctor -v`, `flutter build apk --debug`, `python manage.py check`, teste backend focado e `packages/contracts/export_openapi.py --check`.

## 2026-06-07 — FEAT-MOBILE-001 specs e skills mobile

- Criadas specs iniciais do app Flutter Android: arquitetura, contratos FastAPI, MVP, UX dark-first e critérios de aceite.
- A UX mobile incorpora as imagens de inspiração fornecidas pelo usuário como direção de padrões, sem copiar marca, naming, textos ou layout literal.
- Criadas skills locais para governança mobile: arquitetura, UX, contratos API, testes, implementação Flutter e docs/memória.
- `apps/mobile/README.md`, `tools/skills/gotrendlabs/README.md`, status, integration map, known gaps e workflow foram alinhados.
- Status de implementação: `nao_iniciada`; o ambiente Flutter/Android está preparado, mas o projeto Flutter ainda não foi criado.

## 2026-06-07 — Dashboard administrativo de contratos

- Admin Ops ganhou tela `Contratos` em `/admin-ops/contracts/`, com linha do tempo read-only para organizar mercados ativos e pendentes.
- A timeline usa `created_at` como início, `close_at` como fechamento previsto, `resolved_at` quando existir e linha pontilhada para o dia atual.
- A leitura operacional foi refinada para painel de fases (`Criação`, `Operação`, `Fechamento`, `Resolução`) com legenda no topo, marcos de trilho diferenciando passado/hoje/futuro, alerta visual para fechamento próximo/atrasado e carregamento em blocos de 10.
- A tela reutiliza `GET /admin/markets`, sem novo endpoint FastAPI, migration ou entidade de domínio.
- Specs de Admin Ops e Backend API foram alinhadas para documentar o uso operacional do contrato administrativo existente.

## 2026-06-07 — Organização de templates e assets web em `apps/web`

- Templates compartilhados foram movidos de `templates/` para `apps/web/templates/`.
- Assets compartilhados foram movidos de `static/` para `apps/web/static/`.
- `TEMPLATES["DIRS"]` e `STATICFILES_DIRS` passaram a apontar para os novos caminhos.
- Apps Django permanecem nos caminhos históricos nesta fatia para preservar labels, imports e migrations.

## 2026-06-07 — Organização operacional em `ops/`

- Deploy de produção foi movido de `deploy/production/` para `ops/deploy/production/`, mantendo Compose, Caddyfile, runbook e `deploy.sh` juntos.
- Scripts operacionais foram movidos de `scripts/ops/` para `ops/scripts/`.
- Compose local passou a reservar estado Postgres em `ops/docker/postgres/data/`, mantendo o diretório ignorado pelo Git e preservando dados locais antigos fora da migração.
- Workflow GitHub Actions, README, specs, skills e testes passaram a apontar para os novos caminhos operacionais.
- GitHub Actions passou a atualizar o checkout remoto na EC2 antes de chamar o script em `ops/deploy/production/`, cobrindo a transição em que o checkout existente ainda não tinha o caminho novo.

## 2026-06-07 — Organização da FastAPI em `apps/api`

- Pacote FastAPI movido de `backend_api/` para `apps/api/backend_api/`, preservando a autoridade de domínio e sem alterar contratos funcionais.
- Imports internos, comandos de daemon/suporte, testes e patches passaram a usar o namespace `apps.api.backend_api`.
- Comando local passou a usar `python -m uvicorn apps.api.backend_api.main:app`; Compose de produção aponta para `uvicorn apps.api.backend_api.main:app`.
- README, specs de arquitetura, integração e skills locais foram alinhados ao novo caminho.

## 2026-06-06 — Auditoria de seguranca local

- Autenticacao/sessao passaram a ter hardening automatico em modo producao, redirects `next` validados como locais e rate limit in-memory nos endpoints publicos sensiveis.
- Admin Ops passou a validar uploads de imagem por conteudo real, limitar tamanho e regravar PNG antes de persistir em `media`.
- Caddy passou a servir `/media/*` com `nosniff`, CSP restritiva e cache curto; relatório `docs/audits/security-audit-2026-06-06.md` registra achados, evidencias e pendencias.

## 2026-06-06 — FEAT-OPSLOG-001 cadência do daemon em produção

- Docker Compose de produção passou a executar `run_gotrendlabs_daemon` com intervalo de 300 segundos.
- Defaults de saúde do daemon passaram para 7 minutos até `Atrasado` e 21 minutos até `Sem sinal`, mantendo folga para ciclos de 5 minutos com IA, prune, emails e fechamento de mercados.
- Specs de scheduler/deploy passaram a documentar a cadência operacional e os limites padrão do Dashboard Admin Ops.

## 2026-06-06 — Polimento de experiência e auditoria

- Perfil autenticado passou a renderizar `@` como prefixo fixo do identificador, aceitando edição apenas do nome do handle e preservando normalização backend.
- Retorno contextual público passou de `← Feed` para `← Voltar`, usando origem local confiável quando disponível e fallback para o feed.
- Política de uso removeu a seção pública “O MVP ainda está evoluindo.”, mantendo a versão vigente.
- Cards de mercado passaram a expor fechamento em formato legível e a normalizar labels ISO vindos da API/fallback local.
- Auditoria IA no Admin Ops passou a explicar tipo, status e motivo no browse e detalhe, preservando códigos técnicos no detalhe operacional.

## 2026-06-06 — FEAT-AUTH-001 / FEAT-WALLET-001 indicação bonificada

- Cadastro FastAPI passou a aceitar `referral_code` opcional e creditar `reward_referral` ao indicador comum ativo quando a conta convidada é criada por código válido.
- Criadas tabelas `gotrendlabs_referral_codes` e `gotrendlabs_referral_rewards` para código estável, recompensa idempotente por convidado e vínculo com ledger.
- Admin Ops Config ganhou `referral_bonus_gtl`, com default `200 GT₵` e valor `0` como bônus desativado.
- Carteira e perfil autenticado passaram a renderizar card contextual de indicação com link copiável/compartilhável; compartilhamentos de mercado/resultado por usuário logado podem carregar `ref`.
- Django captura `?ref=` em sessão e preserva o código até o cadastro, sem criar página isolada de convite.

## 2026-06-06 — FEAT-SUGGEST-001 taxonomia na sugestão

- Tela pública/autenticada de sugerir mercado passou a carregar categorias ativas da taxonomia administrada em Admin Ops, com fallback local de desenvolvimento.
- FastAPI passou a expor `GET /taxonomy` sem exigir staff, retornando apenas taxonomia ativa para formulários públicos.
- `POST /suggestions` passou a validar a categoria contra categorias ativas cadastradas e preservar o nome canônico no item da fila editorial.

## 2026-06-05 — FEAT-AUTH-001 navegação administrativa

- Entrada administrativa no chip do usuário passou de `Admin` para `Painel Administrativo`, aparece como primeira ação para staff/superusers e recebe sinalização visual própria de acesso restrito.

## 2026-06-05 — FEAT-NOTIFY-001 emails transacionais

- Adicionado app `communications` com `EmailTemplate`, `EmailDelivery` e `EmailConfirmationToken`.
- Templates transacionais por chave/idioma passaram a ser editáveis no Admin Ops, com seeds para confirmação de email, recuperação de senha, mercado fechado/resolvido e crédito concedido.
- Cadastro e alteração de email passam a emitir link expirável de confirmação; contas não confirmadas entram em login limitado até confirmar o endereço.
- Recuperação de senha pública passou a enfileirar email transacional e não expõe mais `reset_url` na resposta pública.
- Fechamento/resolução de mercado para participantes humanos e créditos concedidos passam a criar entregas idempotentes na outbox.
- Daemon operacional passou a processar `EmailDelivery` com retries, status `queued`/`sending`/`sent`/`failed`/`suppressed` e registro de falhas de provider.
- Admin Ops passou a expor `Politica de Emails`, agrupando templates PT-BR, variáveis disponíveis, preview local do email HTML e logs filtráveis de entrega da outbox sem renderizar links sensíveis.
- Status de implementação: `parcial`; event bus dedicado, preferências/cadência avançadas e webhooks de bounce/complaint seguem fora desta fatia.

## 2026-06-09 — FEAT-NOTIFY-001 Resend transacional

- `SiteConfig` passou a registrar `email_provider`, mantendo SMTP genérico como fallback e adicionando Resend como provider de email transacional.
- `communications` passou a enviar emails via Resend API HTTPS quando selecionado, preservando outbox, templates, retries, snapshots renderizados, `provider_message_id` e `Idempotency-Key`.
- Admin Ops passou a exibir segredo Resend separado, seletor de provedor e teste operacional `send_resend_test_email`, sem persistir ou expor `GOTRENDLABS_RESEND_API_KEY`.
- Dashboard/Admin Summary passaram a reportar saúde de email de forma provider-aware.
- Recuperação de senha passou a tentar envio imediato após o commit e a renderizar links absolutos no email, mantendo o daemon como fallback de retry.
- Resend exige domínio remetente verificado no dashboard com SPF/DKIM; DMARC é recomendado. Bounce/complaint webhooks seguem fora desta fatia.

## 2026-06-05 — GoTrendLabs validação final e ajustes de produção

- Rebrand GoTrendLabs validado localmente e em produção com `manage.py check`, `makemigrations --check --dry-run`, suíte completa `129/129`, scans de resíduos em código/schema e checks HTTP/SSL dos domínios públicos.
- FastAPI passou a filtrar URLs locais de thumbnail inexistentes em payloads públicos, preservando a URL crua nos contratos Admin Ops; templates públicos possuem fallback textual quando a imagem falha no navegador.
- Docker Compose de produção passou a montar `mediafiles` também no serviço FastAPI, permitindo que a API valide existência de `/media/...`; volume `gotrendlabs_mediafiles` foi restaurado com thumbnails/badges.
- Topo do Admin Ops ganhou layout próprio com navegação rolável/empilhável em larguras intermediárias, evitando sobreposição de `Logs` com alternância de tema e `Ver site público`.
- Templates base público e Admin Ops passaram a declarar favicon SVG da marca GoTrendLabs, com variantes por preferência de tema do navegador e `theme-color` alinhado ao shell visual.
- Produção verificada fora de modo manutenção, com EC2 no commit validado, containers `gotrendlabs-*` em execução, schema ativo sem resíduos antigos e domínios `gotrendlabs.com.br`/`.com` servindo 200 com SSL válido.
- Status de implementação: `parcial`, com rebrand profundo concluído nesta fatia; internacionalização completa por catálogo permanece fora do escopo.

## 2026-06-04 — GoTrendLabs deep rebrand

- Plataforma renomeada para `GoTrendLabs` em produto, código, docs, deploy, templates, comandos e skills locais.
- Moeda educativa passou a usar `GTL Credits` e símbolo `GT₵`.
- Contratos técnicos de moeda passaram para o sufixo `_gtl`, substituindo o padrão técnico anterior.
- Tabelas ativas passam a usar prefixo `gotrendlabs_*`, com migrations de rename para preservar dados.
- Variáveis operacionais da marca passaram para `GOTRENDLABS_*` e domínio padrão `gotrendlabs.com.br`.
- Status de implementação: `parcial` até conclusão de testes e mutações externas GitHub/AWS.

## 2026-05-28 — FEAT-MARKET-001 linguagem pública e home simplificada

- Home pública passou a priorizar o grid de mercados, removendo hero narrativo, blocos laterais e progressão da primeira dobra.
- Copy pública foi alinhada para tom claro, social e confiável, incluindo `Prever`, `Em apuração`, `carteira educativa`, `crédito reservado`, `GT₵ reservadas` e microcopy de segurança sem dinheiro real.
- Cards do feed passaram a preservar ações na mesma linha em mobile, usar `NÃO` na camada pública e diferenciar `Prever`, `Em apuração` e `Ver resolução` por status.
- Páginas públicas de login, cadastro, badges, compartilhamento, sugestões, feedback, conceitos, segurança e detalhe receberam ajustes de linguagem sem alterar models, migrations, seeds ou schema.
- Status de implementação: `parcial`.

## 2026-05-24 — FEAT-OPSLOG-001 / FEAT-AIAGENT-001 retenção configurável

- Admin Ops Config passou a persistir retenção separada para logs técnicos e auditoria IA em `gotrendlabs_site_config`.
- Prune do daemon passou a aplicar o prazo atual por `created_at` para `gotrendlabs_system_logs` e `gotrendlabs_ai_agent_actions`, afetando também registros antigos.
- Comando operacional de prune passou a reportar logs técnicos e ações de auditoria IA removidos.
- Status de implementação: `parcial`.

## 2026-05-24 — FEAT-AUTH-001 progressão de operadores e reset administrativo

- Home autenticada passou a exibir `Sua progressão` também para `staff`/`superuser`, preservando exclusão do ranking público e exibindo estado neutro quando `ranking_position=0`.
- FastAPI passou a expor `POST /admin/users/{user_id}/password-reset`, gerando link de recuperação para conta ativa com nota operacional, auth event e auditoria `user.password_reset_request`.
- Reset administrativo bloqueia autoação, permite `staff` apenas para usuários comuns e exige `superuser` para alvos `staff`/`superuser`.
- Admin Ops passou a renderizar ação de geração de link no detalhe do usuário e exibir o link como campo read-only para envio ao usuário, evitando clique do operador logado.
- Testes cobrem contrato backend, permissões, auditoria, sessão preservada até confirmação, renderização Admin Ops e progressão de operador na home.
- Status de implementação: `parcial`.

## 2026-05-24 — FEAT-REP-001 badges no ranking e filtro por evento

- `GET /rankings` passou a retornar resumo público de badges ativas conquistadas por usuário ranqueado, limitado a 3 itens visíveis e `badges_total` para overflow visual.
- Ranking web passou a renderizar badges após o handle do usuário, preservando o handle como identificação principal da linha e resumindo excedentes como `+N`.
- Ranking público passou a aceitar filtro `event` quando `category` e `subcategory` estão selecionados; taxonomia do ranking agora inclui eventos por subcategoria.
- Django continua consumindo `GET /rankings` como fonte autoritativa e apenas normaliza dados de apresentação, sem calcular reputação ou elegibilidade de badges.
- Testes cobrem ranking global/temático/evento, badges ativas/inativas, payload legado sem badges, renderização web e preservação de filtros no `Carregar mais`.
- Status de implementação: `parcial`.

## 2026-05-24 — FEAT-AIAGENT-001 cobertura do ciclo IA

- Ciclo de comentários IA passou a avaliar lista configurável de mercados candidatos por ciclo, com default de 200 candidatos.
- Admin Ops passou a expor limite de tentativas LLM por ciclo de comentário, default 3, separado do número máximo de comentários publicados.
- Fallback de comentário tenta próximo mercado quando a LLM retorna `should_publish=false` ou texto inválido, mas para em erro real de provedor para controlar custo.
- Saúde IA passou a considerar recuperação após ciclo bem-sucedido, sem manter status visual de erro por falhas históricas já superadas.
- Prompt de comentário IA foi versionado para `gotrendlabs-ai-agent-v4` e passou a exigir cautela factual: sem upgrades, eventos, números, anúncios ou fontes específicas fora do contexto do mercado, usando linguagem condicional para inferências.

## 2026-05-23 — FEAT-AIAGENT-001 agentes IA oficiais

- Criado app `agents` com agentes oficiais vinculados a usuários `is_bot=true` e auditoria de ações IA.
- Configuração operacional de IA foi adicionada a `gotrendlabs_site_config`, mantendo o segredo do provedor LLM fora do banco (`OPENAI_API_KEY` ou `AWS_BEARER_TOKEN_BEDROCK`).
- Daemon passou a executar ciclo IA isolado e a registrar resumo de comentários, previsões, skips e erros.
- Comentários de bot expõem selo `IA oficial`; rankings, badges e reputação pública excluem bots.
- Mercado sem participação humana passa a ser cancelado no fechamento automático, com refund de previsões abertas.
- Admin Ops passou a oferecer gestão visual de agentes, edição de parâmetros IA, saúde técnica, auditoria paginada com filtro por motivo e detalhe operacional das ações.
- Browse administrativo de mercados passou a permitir busca textual, exibir participantes e o editor passou a mostrar participantes humanos/bots/total operacional em seção própria.

Use este arquivo para registrar mudanças relevantes por feature, com foco em impacto técnico e rastreabilidade para a IA.

## Modelo de entrada

```md
## FEAT-XXX

### YYYY-MM-DD - vX.Y
- mudança principal
- contratos afetados
- status de implementação resultante
```

## FEAT-NOTIFY-001

### 2026-05-23 - v0.2
- `gotrendlabs_user_notifications` passou a persistir inbox in-app com idempotência por destinatário e `source_key`
- FastAPI passou a expor `GET /users/me/notifications` e `POST /users/me/notifications/read-all`
- ações sociais notificam participantes humanos de mercados em que fizeram previsão: nova previsão, curtida de mercado, comentário em mercado e curtida em comentário próprio
- eventos sistêmicos notificam o beneficiário direto: crédito recebido, mercado participado fechado/resolvido e badge recebida
- home/feed e detalhe do mercado passaram a exibir `comment_count` público de comentários `visible`
- Django renderiza sino com contador/dropdown, botão desabilitado para visitantes, fallback local read-only em desenvolvimento e links contextuais para mercado, comentários, wallet e badges
- status de implementação: `parcial`

## FEAT-OPSLOG-001

### 2026-05-22 - v0.9
- Dashboard Admin Ops passou a exibir o indicador `Backend API` em Saúde técnica, validado por chamada read-only ao `GET /health`
- o healthcheck é consultado independentemente de `/admin/dashboard-summary`, preservando renderização do resumo quando apenas o health falha
- status de implementação: `parcial`

### 2026-05-21 - v0.8
- workflow `.github/workflows/deploy.yml` passou a validar `ENABLE_PROD_DEPLOY`, `AWS_GITHUB_ACTIONS_ROLE_ARN`, `AWS_EC2_INSTANCE_ID` e `AWS_REGION` antes de tentar assumir a role AWS
- deploy GitHub Actions passou a priorizar repository variables para ARN da role e instance id, mantendo fallback temporario para secrets legados
- etapa `Verify assumed AWS identity` passou a executar `aws sts get-caller-identity` antes do `ssm send-command`, endurecendo o diagnostico de OIDC no branch `main`
- status de implementação: `parcial`

### 2026-05-21 - v0.7
- infra AWS base passou a ter EC2 ARM gerenciada por SSM, CloudWatch Agent para métricas/logs mínimos de host e alarmes mínimos de EC2/RDS
- RDS PostgreSQL 16 foi provisionado privado, com acesso administrativo via túnel SSM e sem exposição pública de `5432`
- GitHub Actions OIDC foi preparado para deploy via SSM no branch `main`, mantendo `.env.prod` e segredos fora do Git
- status de implementação: `parcial`

### 2026-05-20 - v0.6
- daemon operacional passou a ter empacotamento de produção como serviço dedicado no Docker Compose da EC2
- deploy MVP documenta que apenas um container `daemon` deve rodar por ambiente
- status de implementação: `parcial`

### 2026-05-20 - v0.5
- Admin Ops Config passou a persistir limites de heartbeat do daemon em `gotrendlabs_site_config`
- Dashboard Summary passou a calcular `Ativo`, `Atrasado` e `Sem sinal` com base em `daemon_stale_after_minutes` e `daemon_missing_after_minutes`
- validação administrativa impede limite de `Sem sinal` menor ou igual ao limite de `Atrasado`
- status de implementação: `parcial`

### 2026-05-20 - v0.4
- rotinas de prune de logs e status do daemon passaram a viver em serviço backend reutilizável
- comando `prune_system_logs` deixou de conter regra própria e passou a chamar o backend
- daemon operacional passou a registrar heartbeat, início, falhas, fechamentos e prune em `gotrendlabs_system_logs`
- Dashboard Admin Ops passou a exibir status do daemon a partir do heartbeat calculado pela FastAPI
- status de implementação: `parcial`

### 2026-05-20 - v0.3
- FastAPI passou a expor `GET /admin/dashboard-summary` como contrato staff agregado para saúde operacional da plataforma
- Dashboard Admin Ops passou a renderizar KPIs, ação necessária, saúde técnica, top mercados e eventos administrativos recentes a partir desse contrato
- métricas recentes usam janela de 7 dias e preservam agregações operacionais sem recalcular regras de domínio
- status de implementação: `parcial`

### 2026-05-20 - v0.2
- Admin Ops passou a paginar o browse de logs e preservar filtros entre páginas
- filtro de usuário passou a usar identificador pesquisável por `@handle`, nome, email ou ID, carregando usuários comuns, staff e superusers
- contratos administrativos de logs passaram a expor `user_identifier` para exibição operacional amigável
- detalhe do log remove duplicações visuais de mensagem/request e mantém usuário apenas no card principal
- spec passou a explicitar cobertura de logs técnicos de segurança e fronteira com `gotrendlabs_auth_events`
- status de implementação: `parcial`

### 2026-05-20 - v0.1
- criada spec inicial para logs técnicos de troubleshooting
- adicionada persistência em `gotrendlabs_system_logs` com retenção, redaction e contexto JSON
- FastAPI passou a expor contratos staff para listagem e detalhe de logs
- Django Admin Ops passou a consultar logs técnicos com filtros e tela de detalhe
- status de implementação: `parcial`

## FEAT-AUTH-001

### 2026-05-21 - v0.14
- perfil autenticado passou a priorizar `gotrendlabs_user_profiles.display_name` como fonte real do nome editável, preservando `gotrendlabs_users.first_name` como compatibilidade
- Admin Ops passou a marcar contas controladas por robôs internos via `is_bot`, com filtro, badge e auditoria `user.bot_update`, sem exposição em contratos públicos/autenticados comuns
- ajuste manual de wallet da própria conta passou a ser permitido para `staff`/`superuser`, mantendo nota, ledger e auditoria, enquanto demais autoações sensíveis continuam bloqueadas
- status de implementação: `parcial`

### 2026-05-21 - v0.13
- bootstrap de núcleo de usuário passou a diferenciar usuário comum de operador: contas `staff`/`superuser` não recebem `grant_initial`, reputação pública, badges nem atividade social
- contexto web deixou de exibir reputação/acerto de operadores no chip, perfil, carteira e resumo da home
- testes cobrem que usuário comum mantém bootstrap completo e idempotente, enquanto operador permanece fora de métricas públicas
- status de implementação: `parcial`

### 2026-05-20 - v0.12
- rodapé público passou a ser organizado em quatro colunas: Institucional, Produto, Confiança e Suporte
- links de conta, mercados recorrentes e operações administrativas foram removidos do rodapé público
- Admin Ops passou a aparecer no chip do usuário apenas para contexto autenticado `is_staff` ou `is_superuser`
- status de implementação: `parcial`

### 2026-05-20 - v0.11
- login e cadastro passaram a renderizar botões sociais iconizados para Google, Facebook e X, preservando rótulos acessíveis
- placeholder FastAPI de login social passou a reconhecer `x` junto de `google` e `facebook`, ainda retornando `501` até existir OAuth real
- layout das páginas standalone de auth passou a usar altura natural para evitar espaçamento vertical divergente entre login, cadastro e rodapé
- status de implementação: `parcial`

### 2026-05-20 - v0.10
- telas standalone de autenticação passaram a renderizar o rodapé público compartilhado via partial reutilizável
- `base.html` passou a usar o mesmo componente de rodapé, reduzindo divergência entre páginas públicas comuns e fluxos de auth
- smoke tests passam a validar rodapé em login e cadastro
- status de implementação: `parcial`

### 2026-05-20 - v0.9
- recuperação de senha passou a usar tokens de uso único emitidos pela FastAPI, com confirmação por contrato e revogação de sessões antigas
- telas de recuperação de senha passaram a preservar navegação pública, retorno `← Feed` e alternância de tema
- Admin Ops passou a permitir gestão controlada de `is_staff`/`is_superuser` por superuser, com nota operacional e auditoria `user.roles_update`
- status de implementação: parcial

### 2026-05-19 - v0.8
- detalhe administrativo de usuário passou a exibir badges adquiridas sem recalcular elegibilidade na UI
- formulário de ajuste manual de wallet passou a exigir seleção explícita de direção, sem opção pré-selecionada
- navegação administrativa foi ordenada como Dashboard, Usuários, Categorias, Badge, Mercado, Resolução e Filas
- status de implementação: `parcial`

### 2026-05-19 - v0.7
- Admin Ops passou a ter gestão de usuários com listagem, busca, filtros por status/papel e detalhe operacional amplo
- FastAPI passou a expor contratos staff para detalhe de usuário, desativação/reativação, revogação de sessões e ajuste manual de wallet
- ações administrativas de usuário registram eventos `user.*` em `gotrendlabs_admin_events` e bloqueiam operações perigosas sobre a própria conta do operador
- status de implementação: `parcial`

### 2026-05-19 - v0.6
- login e cadastro passaram a exibir navegação pública compacta para mercados, badges e ranking
- login e cadastro passaram a exibir retorno compacto `← Feed` no primeiro painel de conteúdo, seguindo o padrão das páginas públicas fora da home
- cadastro passou a expor política de uso em modal, mantendo link para página pública completa `/use-policy/`
- painel de cadastro passou a apresentar prévia de onboarding com ticket de mercado, badges bloqueadas e confiança/GT₵ sem dinheiro real
- status de implementação: `parcial`

### 2026-05-19 - v0.5
- perfil autenticado passou a persistir e editar `birth_date` e `sex` opcionais em `gotrendlabs_user_profiles`
- `GET/PATCH /users/me` expõe e atualiza dados privados do perfil; perfil público não expõe email, data de nascimento, sexo nem metadados privados
- Django mantém edição básica inline na própria tela `/profile/`, com reputação em cards e exclusão lógica no painel lateral
- status de implementação: `parcial`

### 2026-05-19 - v0.4
- cadastro passou a aceitar `recaptcha_token` e validar reCAPTCHA v2 no servidor quando configurado
- Django renderiza widget v2 no formulário de cadastro usando `RECAPTCHA_SITE_KEY`
- configuração por ambiente adicionada via `RECAPTCHA_ENABLED`, `RECAPTCHA_SITE_KEY` e `RECAPTCHA_SECRET_KEY`
- status de implementação: `parcial`

### 2026-05-17 - v0.3
- cadastro exige aceite da política de uso e persiste versão/data do aceite
- perfil autenticado permite alterar nome, email, idioma, bio e categoria forte via FastAPI
- adicionada exclusão lógica de conta com `account_status`, `is_active=false`, revogação de sessões e preservação física dos dados
- respostas autenticadas expõem data de criação, último login e status da conta
- status de implementação: `parcial`

### 2026-05-17 - v0.2
- criada camada `backend-api` FastAPI para `POST /auth/register`, `POST /auth/login`, `GET /auth/session`, `POST /auth/logout` e placeholder de login social
- persistência em PostgreSQL com `gotrendlabs_users`, `gotrendlabs_auth_sessions`, `gotrendlabs_external_identities` e `gotrendlabs_auth_events`
- Django deixou de criar/login usuário diretamente e passou a consumir o contrato da API, mantendo apenas token/contexto na sessão web
- testes adicionados para contrato FastAPI de sessão e para fluxo web Django via API
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `i18n-content.md`, `domain-events.md`
- status de implementação: `nao_iniciada`

## FEAT-MARKET-001

### 2026-05-22 - v0.31
- adicionado comando idempotente `seed_crypto_markets_20260522` para aplicar o lote aprovado `Mercado > Cripto` com aviso de subcategoria e eventos Ethereum, Dogecoin e Solana
- adicionadas 3 thumbnails autorais 512x512 para o lote mainstream cripto, mantendo imagens sem texto/logos embutidos
- contratos relacionados: `market-feed.md`
- status de implementação: `parcial`

### 2026-05-22 - v0.30
- cards da home/feed trocaram o indicador circular por uma barra horizontal compacta de prazo, calculada com `created_at` e `close_at`
- detalhe do mercado passou a exibir a thumbnail/ícone encaixada à esquerda do título, preservando os metadados textuais em HTML
- a probabilidade deixou de alimentar visualmente o indicador de tempo; ela permanece nos textos e gráficos próprios de consenso
- contratos relacionados: `market-feed.md`, `frontend-web.md`
- status de implementação: `parcial`

### 2026-05-22 - v0.29
- eventos sem mercados vinculados podem ser excluídos pelo Admin Ops e por `DELETE /admin/categories/{category_slug}/subcategories/{subcategory_slug}/events/{event_slug}`; eventos vinculados continuam protegidos e devem ser bloqueados para preservar histórico
- contratos relacionados: `database.md`, `backend-api.md`, `admin-ops.md`
- status de implementação: `parcial`

### 2026-05-22 - v0.28
- categorias e subcategorias passaram a aceitar `notice` opcional de até 500 caracteres no Admin Ops e em `/admin/taxonomy`
- layout master-detail da taxonomia foi ajustado para abrir formulários como painéis contextuais estáticos, evitando sobreposição visual na gestão
- contratos relacionados: `market-feed.md`, `database.md`, `backend-api.md`, `admin-ops.md`, `frontend-web.md`
- status de implementação: `parcial`

### 2026-05-22 - v0.27
- Admin Ops de taxonomia passou para layout master-detail com categorias na lateral e subcategorias/eventos agrupados no painel principal
- eventos passaram a aceitar `notice` opcional de até 500 caracteres, retornado por `/admin/taxonomy`
- contratos relacionados: `market-feed.md`, `database.md`, `backend-api.md`, `admin-ops.md`, `frontend-web.md`
- status de implementação: `parcial`

### 2026-05-22 - v0.26
- taxonomia de mercado passou a ter terceira camada `evento`, vinculada à subcategoria e gerenciada no Admin Ops
- criação/edição administrativa de mercado seleciona evento ativo da subcategoria; mercados existentes são migrados para evento `Geral`
- `MarketResponse` e cards da home/feed passam a exibir categoria, subcategoria e evento
- contratos relacionados: `market-feed.md`, `market-lifecycle.md`, `database.md`, `backend-api.md`, `admin-ops.md`, `frontend-web.md`
- status de implementação: `parcial`

### 2026-05-22 - v0.25
- skill `gotrendlabs-prediction-markets` passou a aceitar categoria `cripto`, fontes cripto/on-chain e aviso obrigatório `Não caracteriza recomendação de investimento`
- DEV recebeu 3 mercados cripto em `draft` com taxonomia `Cripto`, subcategorias `Preço`, `DeFi / On-chain` e `Meme coins`
- adicionadas 3 thumbnails autorais para os mercados cripto, mantendo imagens sem texto/logos embutidos
- status de implementação: `parcial`

### 2026-05-22 - v0.24
- visitantes passaram a ver a affordance de favorito nos cards da home em estado apagado/readonly
- filtro `Favoritos` e mutação de favoritar/desfavoritar permanecem exclusivos para usuários autenticados
- clique de visitante na affordance mostra aviso de login, sem enviar formulário de mutação
- status de implementação: `parcial`

### 2026-05-21 - v0.23
- migration inicial de mercados deixou de executar seed automático a partir de `data/fixtures/domain.json`
- produção foi alinhada para não manter mercados fixture criados pelo primeiro deploy
- status de implementação: `parcial`

### 2026-05-21 - v0.22
- métrica pública `GT₵ distribuídas` passou a excluir créditos de `staff` e `superuser` no contrato `/stats` e no fallback local da home
- espaçamento visual do bloco `AO VIVO`/destaques da home foi ajustado para reduzir colisão entre rótulo e título
- status de implementação: `parcial`

### 2026-05-21 - v0.21
- adicionadas 27 thumbnails autorais de mercado como imagens puras, quadradas e específicas por evento, usadas via `image_url`
- documentado lote editorial seed de 27 mercados/categorias/subcategorias para retomada operacional e auditoria da fonte de verdade
- guia da skill `gotrendlabs-prediction-markets` passou a registrar que inclusão aprovada cria taxonomia idempotente e mantém mercados em `draft`
- status de implementação: `parcial`

### 2026-05-20 - v0.20
- home passou a exibir métricas públicas de economia educativa com `GT₵ distribuídas` e `GT₵ movimentadas em previsões`
- FastAPI passou a expor `GET /stats` com `open_markets`, `total_predictions`, `distributed_gtl`, `moved_gtl`, `resolution_sla` e `real_money`
- fallback local Django passou a calcular `distributed_gtl` a partir de créditos do ledger e `moved_gtl` a partir de stakes de previsões
- textos visíveis de moeda foram padronizados para `GT₵`, preservando campos e identificadores técnicos `_gtl`
- status de implementação: `parcial`

### 2026-05-20 - v0.19
- título dos cards de mercado passou a ser link para o detalhe, reduzindo atrito de navegação no feed/home e listas que reutilizam o card
- smoke test passa a proteger o link do título para o detalhe do mercado
- status de implementação: `parcial`

### 2026-05-20 - v0.18
- fechamento automático de mercados vencidos com `auto_close_enabled=true` foi centralizado em serviço backend e em entrada própria da `MarketLifecycleEngine`
- comando `run_gotrendlabs_daemon` foi adicionado como processo operacional fino, sem duplicar regra de domínio
- fechamentos automáticos registram `market.lock` com ator sistema/nulo e nota operacional padronizada
- status de implementação: `parcial`

### 2026-05-19 - v0.17
- mercados passaram a persistir `view_count` e `share_count` como contadores operacionais de popularidade sem deduplicação
- contrato público/admin expõe os contadores, e `view_count` passa a guiar a seleção pública de destaque da home e do ticket de cadastro
- Admin Ops lista popularidade por mercado em `Mercados ativos e rascunhos`, com indicadores compactos e ordenação por mais visualizados ou mais compartilhados
- status de implementação: `parcial`

### 2026-05-19 - v0.16
- ticket de onboarding do cadastro passou a usar o mercado publicado não cancelado com maior `view_count`, excluindo `draft` e `canceled`
- quando houver empate ou ausência de visualizações, o ticket de onboarding usa o mercado mais recente por `created_at`
- prévia reutiliza `sparkline_series`, opções e dados serializados do domínio, com fallback local quando a API está indisponível
- status de implementação: `parcial`

### 2026-05-19 - v0.15
- feed público passou a expor recorte rápido `Resolvidos`, filtrando client-side cards já renderizados com `status=resolved`
- hero do feed passou a mostrar `previsões totais` calculadas a partir de previsões persistidas reais, sem janela mensal
- páginas públicas fora da home passaram a usar retorno compacto `← Feed` dentro do primeiro painel, alinhado ao rótulo inicial da tela
- Admin Ops passou a usar apenas a navegação principal no topo, com link de Resolução incluído e sem menu secundário duplicado
- status de implementação: `parcial`

### 2026-05-19 - v0.14
- cards de mercado passaram a usar fallback visual de thumbnail quando `image_url` e `thumb` estão vazios, derivando iniciais de categoria/subcategoria/título
- fallback de thumbnail também é aplicado aos cards de compartilhamento social e imagens Open Graph de mercado/resultado
- curtidas do card foram separadas de reações em comentários; `market_like_count` passa a representar curtidas reais do mercado
- status de implementação: `parcial`

### 2026-05-18 - v0.13
- feed público passou a ter ordenações rápidas client-side por tendência, encerramento, volume, novidade e favoritos editoriais
- cards de mercado passaram a exibir contador compacto de curtidas
- contrato/renderização do feed usa `is_featured`, `market_like_count`, `view_count`, `created_at` e `close_at` para destaque e ordenação visual
- destaque principal do feed prioriza os mercados não cancelados mais visualizados, incluindo resolvidos quando liderarem por popularidade, com mercado mais novo como desempate
- status de implementação: `parcial`

### 2026-05-18 - v0.12
- listagem administrativa "Mercados ativos e rascunhos" removeu o CTA `Ver público`, mantendo apenas `Editar/visualizar`
- acesso à página pública permanece disponível dentro do editor de mercado
- status de implementação: `parcial`

### 2026-05-18 - v0.11
- página inicial/feed público padrão deixou de renderizar mercados cancelados
- endpoint público `GET /markets` sem filtro explícito passou a excluir `draft` e `canceled`
- status de implementação: `parcial`

### 2026-05-18 - v0.10
- browse administrativo de mercados passou a usar fallback local em Postgres quando a FastAPI administrativa retorna erro transitório
- documentado que mudanças de schema com SQL direto exigem reinício do processo FastAPI em ambientes long-running
- status de implementação: `parcial`

### 2026-05-18 - v0.9
- edição administrativa de mercado passou a sincronizar opções sem apagar/recriar opções que já possuem previsões vinculadas
- tentativa de remover opção com previsão vinculada retorna erro de domínio em vez de erro interno
- cliente Django passou a exibir erro de API genérico como falha de requisição, não como falha de autenticação
- status de implementação: `parcial`

### 2026-05-18 - v0.8
- cards do feed passaram a exibir mini gráficos de evolução do consenso com uma linha por opção
- CTA de mercados abertos passou a ser `Prever` também para múltipla escolha
- fallback do Django para feed/categorias passou a hidratar séries visuais e IDs de opção a partir do Postgres local quando a API entrega payload antigo
- status de implementação: `parcial`

### 2026-05-18 - v0.7
- Admin Ops de taxonomia passou a operar em formato de browse objetivo, com filtros por uso/bloqueio e política lateral
- categorias e subcategorias ganharam bloqueio lógico persistido (`is_blocked`, `blocked_at`, `blocked_reason`) em vez de exclusão física
- FastAPI expõe ações staff para bloquear/desbloquear categoria e subcategoria, registrando eventos administrativos
- criação/edição administrativa de mercado rejeita categoria ou subcategoria bloqueada
- status de implementação: `parcial`

### 2026-05-18 - v0.6
- Admin Ops passou a marcar campos obrigatórios e exibir feedback de sucesso ao salvar/publicar/cancelar/fechar mercado
- adicionada ação manual de fechamento para mercados `open`/`scheduled` com `auto_close_enabled=false`
- fechamento manual muda status para `locked` e registra evento `market.lock`
- editor administrativo passou a carregar categoria/subcategoria da taxonomia persistida, mantendo subcategoria vinculada à categoria selecionada
- categoria/subcategoria agora iniciam com opção “Selecione”, sem pré-seleção automática em novo mercado
- ajustado contraste de dark mode no editor de opções e no controle de fechamento automático
- status de implementação: `parcial`

### 2026-05-18 - v0.5
- editor administrativo passou a exigir campos operacionais mínimos antes de salvar mercado
- adicionados `close_at`, `close_timezone`, `auto_close_enabled` e `image_url` ao contrato persistido de mercado
- prévia do card no Admin Ops passou a atualizar conforme preenchimento e upload de thumbnail
- status canônico de mercado passou a ser exibido sem usar rótulos editoriais como status
- rótulo curto de prazo passou a ser derivado automaticamente de `close_at`
- status de implementação: `parcial`

### 2026-05-18 - v0.4
- browse administrativo de mercados passou a filtrar por status via `GET /admin/markets?status=...`
- chips do Django Admin Ops agora refletem filtro ativo e contadores globais por status
- status de implementação: `parcial`

### 2026-05-18 - v0.3
- adicionada primeira fatia real do Admin Ops para mercados e taxonomia
- FastAPI expõe endpoints staff para listar, criar, editar, publicar e cancelar mercados
- Django Admin Ops passou a consumir a API administrativa com bloqueio para guest e usuário comum
- criada auditoria simples em `gotrendlabs_admin_events`
- status de implementação: `parcial`

### 2026-05-17 - v0.2
- criadas tabelas PostgreSQL para categorias, subcategorias, mercados e opções
- adicionado seed inicial idempotente a partir de `data/fixtures/domain.json`
- FastAPI passou a expor `GET /markets` com filtros públicos básicos
- Django passou a consumir a FastAPI para o feed, preservando fixture como fallback
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `market-lifecycle.md`, `i18n-content.md`
- status de implementação: `nao_iniciada`

## FEAT-MARKET-002

### 2026-05-22 - v0.14
- avisos de categoria/subcategoria/evento continuam agrupados em alerta informativo, mas passam a renderizar abaixo de `Critério de resolução` no detalhe/ticket do mercado
- contratos relacionados: `market-feed.md`, `frontend-web.md`
- status de implementação: `parcial`

### 2026-05-22 - v0.13
- `MarketResponse` passou a expor `category_notice` e `subcategory_notice`
- detalhe público e ticket de previsão renderizam avisos informativos de categoria/subcategoria/evento quando preenchidos, sem exibir avisos nos cards da home/feed
- status de implementação: `parcial`

### 2026-05-22 - v0.12
- `MarketResponse` passou a expor `event_notice`
- detalhe público e ticket de previsão renderizam aviso informativo do evento quando preenchido, sem exibir aviso nos cards da home/feed
- status de implementação: `parcial`

### 2026-05-22 - v0.11
- detalhe/previsão pública do mercado passou a exibir o evento junto de categoria e subcategoria
- compartilhamento social/fallback visual passa a considerar o evento quando disponível
- status de implementação: `parcial`

### 2026-05-22 - v0.10
- detalhe de mercado passou a exibir favorito readonly para visitantes e favorito funcional para autenticados
- estado visitante usa o mesmo aviso de login da affordance pública da home, sem formulário de mutação
- status de implementação: `parcial`

### 2026-05-21 - v0.9
- card social de mercado passou a exibir opções/probabilidades com barras discretas de consenso
- CTA editorial `Dispute previsões, construa reputação e ganhe destaque.` passou a direcionar para o detalhe do mercado
- imagem social dinâmica de mercado passou a incluir resumo das opções principais
- status de implementação: `parcial`

### 2026-05-19 - v0.8
- abertura do detalhe público incrementa `view_count` do mercado com fallback local quando a API está indisponível
- controles de compartilhamento de pergunta/resultado incrementam `share_count` via rota leve de tracking, sem bloquear navegação/cópia
- editor administrativo exibe visualizações e compartilhamentos como campos read-only de popularidade operacional
- status de implementação: `parcial`

### 2026-05-19 - v0.7
- rotas web de compartilhamento de pergunta e resultado passaram a expor links por rede, metadados Open Graph/Twitter e imagem social dinâmica
- card social de mercado inclui contexto curto da plataforma e CTA de aquisição: "Dispute previsões, construa reputação e ganhe destaque."
- card social de resultado prioriza pergunta e exibe o resultado imediatamente abaixo como desfecho
- origem pública de compartilhamento pode ser configurada para crawlers sociais; host local exibe aviso de preview não rastreável
- status de implementação: `parcial`

### 2026-05-18 - v0.6
- detalhe do mercado passou a exibir gráfico de evolução do consenso com uma linha por opção
- gráfico de evolução passou a preservar histórico após resolução, considerando previsões `open` e `resolved` e excluindo `canceled`
- mercado resolvido passou a exibir data/hora/timezone da resolução e mensagem personalizada no ticket para usuário que acertou ou errou
- visitantes veem opções e consenso sem controle de stake; usuários com previsão existente veem aviso destacado e controles desabilitados
- fallback local do Django hidrata `option.id`, `sparkline_path` e `sparkline_series` quando a FastAPI está indisponível ou desatualizada
- status de implementação: `parcial`

### 2026-05-18 - v0.5
- documentado que percentuais iniciais das opções ficam persistidos em `gotrendlabs_market_options.probability_exact`
- status de implementação: `parcial`

### 2026-05-18 - v0.4
- formalizada regra de opções por tipo de mercado no admin
- `binary` persiste opções canônicas `SIM`/`NAO` com `50%`/`50%`
- `multiple` aceita duas ou mais opções sem limite máximo fixo e distribui percentuais automaticamente para somar `100%`
- status de implementação: `parcial`

### 2026-05-18 - v0.3
- dados-base do detalhe podem ser mantidos pelo Admin Ops real
- publicação administrativa preserva contrato público de detalhe em `GET /markets/{slug}`
- cancelamento administrativo preserva histórico sem exclusão física
- status de implementação: `parcial`

### 2026-05-17 - v0.2
- detalhe de mercado passou a ser persistido e serializado pela FastAPI em `GET /markets/{slug}`
- contrato mantém opções, probabilidade snapshot, categoria, subcategoria e critérios de resolução compatíveis com os templates
- Django passou a consumir a FastAPI no detalhe e nas páginas de compartilhamento, preservando fallback fixture
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `market-lifecycle.md`, `prediction-payloads.md`, `i18n-content.md`
- status de implementação: `nao_iniciada`

## FEAT-PRED-001

### 2026-05-21 - v0.6
- ticket de previsão em mercado aberto passou a iniciar sem opção pré-selecionada e usa radio obrigatório nativo para evitar confirmação ambígua
- UI do ticket passou a orientar seleção explícita com chamada visual discreta antes das opções
- usuário autenticado sem saldo disponível vê estado somente leitura com indicação de saldo indisponível e CTA para wallet
- status de implementação: `parcial`

### 2026-05-19 - v0.5
- prévia de retorno da previsão passou a ter contrato FastAPI sem efeito colateral
- fallback local mutável de criação de previsão no Django foi removido; falha da API não cria previsão nem altera wallet/ledger
- status de implementação: `parcial`

### 2026-05-18 - v0.4
- adicionados campos decimais para probabilidade real em mercado, opções e probabilidade de entrada da previsão
- colunas inteiras redundantes foram removidas; `probability` permanece apenas como campo derivado no contrato de leitura
- mercados de múltipla escolha distribuem `100 / quantidade_de_opções` igualmente, sem sobra artificial para a primeira opção
- `potential_payout` passa a usar a probabilidade decimal vigente antes da previsão
- status de implementação: `parcial`

### 2026-05-18 - v0.3
- séries visuais de consenso passaram a ser derivadas de `gotrendlabs_predictions` ordenadas por criação
- mercados binários e múltipla escolha expõem evolução por opção para cards e detalhe
- adicionado fallback local de confirmação/persistência quando a FastAPI separada está indisponível no ambiente de desenvolvimento
- testes cobrem confirmação local, payload antigo sem IDs/séries e hidratação visual dos cards
- status de implementação: `parcial`

### 2026-05-18 - v0.2
- adicionada primeira mutação real de previsão em `POST /markets/{slug}/predict`
- decisão de MVP: permitir apenas uma previsão por usuário em cada mercado
- stake positivo sem teto fixo é limitado pelo saldo disponível e gera `prediction_stake_lock`
- probabilidades do mercado são recalculadas com peso sintético base e peso `reputacao * stake`
- Django passou a confirmar previsão via FastAPI e exibir sucesso/erros de domínio
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `prediction-payloads.md`, `wallet-ledger.md`, `market-lifecycle.md`
- status de implementação: `nao_iniciada`

## FEAT-RES-001

### 2026-05-20 - v0.4
- ciclo operacional de mercado foi centralizado na `MarketLifecycleEngine`, mantendo handlers HTTP apenas com autenticação, transação, chamada da engine e serialização
- FastAPI passou a expor `GET /admin/markets/{slug}/resolution-audit` como contrato staff read-only para mercados resolvidos
- auditoria agrega participantes, winners/losers, stakes, refunds, payouts, losses e badges concedidas na resolução a partir de SQL no backend
- Admin Ops passou a mostrar ação “Auditoria” para mercados resolvidos, com tela própria, paginação de 10 participantes e legenda de ledger
- Dashboard Admin Ops recebeu ajustes de contraste em modo escuro para KPIs, métricas, saúde técnica, tabelas e alertas
- QA hard com 100 usuários simulados foi registrada em `docs/research/qa-simulacao-hard-100-usuarios-20260520.md`
- contratos relacionados: `market-lifecycle.md`, `wallet-ledger.md`, `reputation-ranking.md`, `domain-events.md`
- status de implementação: `parcial`

### 2026-05-19 - v0.3
- cancelamento administrativo passou a validar que não restam previsões `open` após aplicar refund total
- adicionada reconciliação operacional idempotente para mercados já `canceled` que ainda possuam previsões `open`
- reconciliação registra `market.cancel_reconcile` e preserva reputação
- adicionada regressão para estado órfão `canceled` + previsão `open`, cobrindo dry-run, refund, saldo e idempotência
- contratos relacionados: `market-lifecycle.md`, `wallet-ledger.md`, `domain-events.md`
- status de implementação: `parcial`

### 2026-05-18 - v0.2
- adicionada resolução manual por `POST /admin/markets/{slug}/resolve`
- resolução registra opção vencedora, evidência, operador, payout, perda e delta de reputação pela fórmula MVP
- resolução passou a registrar data/hora efetiva (`resolved_at`) e timezone controlado (`resolution_timezone`), com campos editáveis no Admin Ops
- cancelamento administrativo passou a aplicar refund total dos stakes bloqueados
- mercados resolvidos passaram a permanecer no browse de resolução com ação excepcional de desfazer resolução
- browse de resolução passou a exibir data/hora/timezone e ordenar por resolução recente, antiga ou pendências
- desfazer resolução retorna o mercado para `locked`, estorna payout líquido, rebloqueia stakes e recalcula reputação
- mercado resolvido passou a ficar somente leitura no editor administrativo
- Admin Ops passou a listar mercados `locked` e publicar resolução real
- contratos relacionados: `market-lifecycle.md`, `wallet-ledger.md`, `reputation-ranking.md`, `domain-events.md`
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `market-lifecycle.md`, `wallet-ledger.md`, `reputation-ranking.md`, `domain-events.md`
- status de implementação: `nao_iniciada`

## FEAT-REP-001

### 2026-05-22 - v1.2
- browse Admin Ops de badges passou a exibir miniatura da imagem cadastrada, com fallback textual compacto para badges sem imagem
- contratos relacionados: `admin-ops.md`, `frontend-web.md`
- status de implementação: `parcial`

### 2026-05-22 - v1.1
- regras administrativas de badge passaram a aceitar recorte opcional por evento, depois de categoria/subcategoria
- `BadgeAwardEngine` passou a aplicar `category/subcategory/event` para previsões resolvidas e comentários
- regras por evento não contam sugestões aprovadas antigas enquanto sugestão ainda não captura evento
- browse/formulário de badges exibem e validam o recorte de evento usando a taxonomia dinâmica
- contratos relacionados: `reputation-ranking.md`, `reputation-and-ranking.md`, `backend-api.md`, `admin-ops.md`
- status de implementação: `parcial`

### 2026-05-20 - v1.0
- padrão web de listas simples passou a usar `Carregar mais` em blocos cumulativos de 10 itens
- tela pública de ranking trocou navegação `Anterior`/`Próxima` por `Carregar mais`, preservando filtros de categoria/subcategoria
- browses principais do Admin Ops de usuários, mercados, resolução, filas e logs passaram a usar o mesmo padrão em blocos de 10
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `parcial`

### 2026-05-20 - v0.9
- tela pública de ranking passou a paginar a lista em 10 linhas por página
- paginação preserva filtros de categoria/subcategoria aplicados
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `parcial`

### 2026-05-19 - v0.8
- ranking web passou a consumir `GET /rankings` como fonte única
- fallback local de cálculo de ranking/reputação no Django foi removido; falha da API exibe erro/estado vazio
- status de implementação: `parcial`

### 2026-05-19 - v0.7
- compartilhamento de badge passou a gerar card social com metadados Open Graph/Twitter e imagem dinâmica
- link público de conquista usa token opaco para permitir preview social sem expor id, email ou handle na URL
- botão de cópia copia apenas o link canônico; links por rede mantêm texto contextual quando suportado
- cards de badge no perfil passaram a usar o mesmo padrão visual do catálogo e apontar para `share-badge`
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `parcial`

### 2026-05-19 - v0.6
- catálogo público de badges passou a exibir ação de compartilhar apenas para usuários autenticados em badges já conquistadas
- adicionada rota web autenticada `/share/badge/{code}/`, validando a conquista antes de renderizar a página de compartilhamento
- compartilhamento MVP usa ação nativa do navegador quando disponível e fallback de cópia de link/texto
- reforçado que compartilhar badge não altera reputação, ranking, ledger, wallet nem concessão de badges
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `parcial`

### 2026-05-19 - v0.5
- badges passaram de registros hardcoded por usuário para catálogo administrável com definição, regra e conquista separadas
- adicionados contratos públicos `GET /badges` e `GET /users/me/badges` com estado pessoal quando autenticado
- adicionados contratos staff para listar, criar, editar e desativar badges no Admin Ops
- concessão automática usa `rule_type` controlado no backend e é idempotente por usuário/badge
- regras temáticas de badge passaram a selecionar categoria/subcategoria da taxonomia dinâmica e aplicar recorte em previsões, acertos, comentários e sugestões aprovadas
- contrato administrativo de badges passou a distinguir campos obrigatórios de opcionais e exigir marcação visual no formulário
- browse administrativo de badges passou a exibir categoria/subcategoria da regra, usando `Todas / Todas` para regras globais
- formulário administrativo de badges passou a exibir prévia do card público, incluindo imagem local antes de salvar
- badges passaram a aceitar imagem padrão/tema claro e imagem opcional para tema escuro, com fallback para a imagem padrão quando a escura não existir
- concessão de badges passou a ser centralizada na `BadgeAwardEngine`, com eventos de domínio para cadastro, comentário, sugestão, feedback e resolução de mercado
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `parcial`

### 2026-05-19 - v0.4
- ranking público passou a aceitar filtros de categoria/subcategoria e expor metadados de taxonomia
- ranking temático é recalculado em leitura com previsões resolvidas do recorte usando a fórmula MVP
- tela de ranking passou a identificar usuários por handle e remover filtros decorativos sem contrato
- quadro "Seu recorte" passou a depender de sessão/dados reais, sem percentuais fictícios para visitantes
- usuários `is_staff` e `is_superuser` foram excluídos do ranking público na API e no fallback Django
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `parcial`

### 2026-05-18 - v0.3
- resolução de mercado passou a atualizar reputação com `K=10` usando `probability_at_entry`
- `accuracy_indicator`, `resolved_predictions_count` e `streak` passam a refletir previsões resolvidas
- cancelamento/refund não altera reputação
- status de implementação: `parcial`

### 2026-05-17 - v0.2
- criada reputação base provisória por usuário com score inicial `100`
- criado ranking público simples ordenado por reputação e data de criação
- criadas badges estruturadas com `founding_member` concedida no cadastro e demais badges bloqueadas
- Django passou a renderizar perfil/ranking a partir da FastAPI quando disponível
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `nao_iniciada`

## FEAT-WALLET-001

### 2026-05-21 - v1.2
- agregado público `GT₵ distribuídas` passou a considerar apenas créditos de usuários comuns, excluindo operadores `staff` e `superuser`
- ajuste manual de wallet permite autoajuste por operador com nota e auditoria, preservando bloqueio das demais autoações sensíveis
- status de implementação: `parcial`

### 2026-05-20 - v1.1
- ledger passou a alimentar o agregado público `GT₵ distribuídas` usado nas métricas da home
- agregado público considera apenas lançamentos `direction="credit"` e não expõe recorte individual de wallet ou extrato
- movimentação pública em previsões é exibida como soma de stakes registrados, mantendo o contexto educativo de `GT₵`
- status de implementação: `parcial`

### 2026-05-20 - v1.0
- extrato da wallet trocou navegação `Anterior`/`Próxima` por `Carregar mais` em blocos cumulativos de 10 lançamentos
- histórico de recargas permanece limitado às últimas 3 solicitações
- status de implementação: `parcial`

### 2026-05-20 - v0.9
- Admin Ops Config ganhou parâmetro `wallet_recharge_min_balance_gtl` para definir o saldo máximo elegível à solicitação de recarga educativa
- backend e wallet web bloqueiam nova solicitação quando `available_gtl` está acima do piso configurado
- histórico de recargas na wallet mostra apenas os 3 itens mais recentes e o extrato pagina 10 lançamentos por vez
- status de implementação: `parcial`

### 2026-05-20 - v0.8
- wallet passou a permitir solicitação autenticada de recarga educativa com uma pendência por usuário
- Admin Ops passou a listar `wallet_recharge` nas filas e aprovar ou rejeitar solicitações com auditoria
- aprovação cria ledger `educational_recharge`, atualiza `gotrendlabs_wallet_balances` e não altera reputação nem `total_earned_gtl`
- status de implementação: `parcial`

### 2026-05-19 - v0.7
- ajuste manual de wallet por staff passou a usar `manual_adjustment`, `admin_user_adjustment`, operador e nota obrigatória
- direção do ajuste manual deve ser escolhida explicitamente no Admin Ops, sem seleção padrão
- débito manual acima do saldo disponível é rejeitado pelo backend
- status de implementação: `parcial`

### 2026-05-19 - v0.6
- refund de cancelamento passou a ser idempotente por previsão enquanto não houver novo lock/relock posterior
- reconciliação operacional de mercado cancelado cria `prediction_refund` ausente e atualiza `gotrendlabs_wallet_balances` na mesma transação
- preservado caso de resolução desfeita seguida de cancelamento final, criando novo release após `prediction_resolution_relock`
- status de implementação: `parcial`

### 2026-05-18 - v0.5
- resolução vencedora libera stake por `prediction_refund` e credita ganho líquido por `prediction_payout`
- resolução perdedora baixa stake bloqueado por `prediction_loss` com `direction="settle"`
- cancelamento com previsão aberta devolve 100% do stake bloqueado por `prediction_refund`
- status de implementação: `parcial`

### 2026-05-18 - v0.4
- ledger passou a reconhecer recompensas operacionais de feedback e sugestão de mercado
- `reward_feedback` e `reward_suggestion` atualizam extrato e projeção `gotrendlabs_wallet_balances`
- aprovações de crédito em filas operacionais bloqueiam duplicidade por item
- recompensas operacionais não concedem reputação
- status de implementação: `parcial`

### 2026-05-17 - v0.3
- adicionada projeção operacional `gotrendlabs_wallet_balances` para leitura rápida de saldo
- mantido `gotrendlabs_wallet_ledger` como fonte auditável e regra de reconciliação
- FastAPI passou a ler saldo pela projeção e a centralizar mutações no helper ledger + balance
- migration inclui backfill de saldos existentes a partir do ledger
- status de implementação: `parcial`

### 2026-05-17 - v0.2
- criado ledger PostgreSQL `gotrendlabs_wallet_ledger` como fonte do saldo do usuário
- cadastro passou a registrar `grant_initial` de `2000 GT₵` na mesma transação do usuário
- adicionados endpoints FastAPI de wallet e extrato autenticado
- Django passou a renderizar carteira e extrato a partir da FastAPI
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `wallet-ledger.md`
- status de implementação: `nao_iniciada`

## FEAT-COMMENT-001

### 2026-05-18 - v0.3
- UI pública de comentários passou a identificar autores por `@handle`
- ações de `like` e `dislike` passaram a usar botões iconizados com estado ativo
- convite de login para visitante no bloco de comentários foi redesenhado como callout
- documentação de arquitetura/contratos passou a registrar endpoints, tabelas, moderação e fallback local
- status de implementação: `parcial`

### 2026-05-18 - v0.2
- adicionada persistência de comentários e reações em mercados
- FastAPI passou a expor criação/listagem pública, `like`/`dislike` autenticado e moderação staff por `visible`/`hidden`
- Django passou a renderizar formulário, lista e ações de reação no detalhe do mercado
- Admin Ops passou a listar e moderar comentários com evento `comment.hide`/`comment.restore`
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `domain-events.md`, `i18n-content.md`
- status de implementação: `nao_iniciada`

## FEAT-SUGGEST-001

### 2026-05-22 - v0.6
- navegação pública principal passou a exibir `Sugerir mercado` para visitantes e usuários autenticados
- o link usa o fluxo de sugestão existente, preservando envio guest e atalho autenticado no menu do usuário
- status de implementação: `parcial`

### 2026-05-19 - v0.5
- Admin Ops deixou de executar fallbacks locais mutáveis para filas, comentários, conversão de sugestão e créditos operacionais
- indisponibilidade da FastAPI passa a ser exibida como erro operacional sem alterar domínio diretamente pelo Django
- status de implementação: `parcial`

### 2026-05-19 - v0.4
- sugestões de mercado e feedback passaram a aceitar `recaptcha_token`
- FastAPI exige reCAPTCHA válido para envios de visitantes quando configurado
- Django renderiza widget v2 apenas para visitantes e preserva bypass para usuários autenticados
- fallback local de desenvolvimento valida reCAPTCHA antes de persistir envio guest
- status de implementação: `parcial`

### 2026-05-18 - v0.3
- formulários públicos passaram a aceitar envio autenticado ou visitante identificado por nome e email
- confirmação de envio passou a usar popup na home após redirecionamento
- fila operacional passou a exibir Mercado e Feedback com data de criação, tipo do item e ordenação por data
- removidas colunas operacionais não usadas nesta fatia, como aging e responsável
- tela de revisão passou a exibir status persistido, recompensa, contexto completo e ações específicas por tipo
- conversão em rascunho ficou restrita a sugestão de mercado e bloqueada após conversão
- créditos podem ser aprovados para feedback ou sugestão apenas quando houver usuário cadastrado, com bloqueio de reenvio
- status de implementação: `parcial`

### 2026-05-18 - v0.2
- adicionada persistência para sugestões de mercado e feedbacks operacionais
- FastAPI passou a expor submissão pública/autenticada e fila administrativa staff
- Admin Ops passou a listar itens reais, revisar, converter sugestão em rascunho e recompensar feedback via ledger
- feedback recompensável entra como fatia operacional mínima; event bus assíncrono segue pendente
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `domain-events.md`, `i18n-content.md`
- status de implementação: `nao_iniciada`

## FEAT-NOTIFY-001

### 2026-05-20 - v0.2
- Admin Ops passou a persistir configuração SMTP não sensível em `gotrendlabs_site_config`
- senha/API key SMTP permanecem fora do banco, via `GOTRENDLABS_SMTP_PASSWORD` ou `GOTRENDLABS_SMTP_API_KEY`
- TLS e SSL são mutuamente exclusivos na configuração operacional
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `domain-events.md`, `i18n-content.md`
- status de implementação: `nao_iniciada`

## FEAT-I18N-001

### 2026-05-20 - v0.2
- marca pública da plataforma alterada para `GoTrendLabs` em templates, compartilhamento social, API title/health, README e specs ativas
- nomes técnicos, identificadores `gotrendlabs_*`, arquivos, comandos, env vars e `GTL Credits` foram preservados
- extração completa de strings para catálogos `pt-BR`/`en` segue fora desta fatia
- status de implementação: `nao_iniciada`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `i18n-content.md`
- status de implementação: `nao_iniciada`

## Sistema documental e skills

### 2026-06-07 - v0.8
- adicionado snapshot OpenAPI versionado em `packages/contracts/openapi/gotrendlabs-api.json`
- adicionado exportador/verificador `packages/contracts/export_openapi.py`
- CI passou a validar o snapshot com `python packages/contracts/export_openapi.py --check` antes da suite
- README, specs de arquitetura e skills locais atualizados para a política de contratos
- status de implementação: `concluida`

### 2026-06-07 - v0.7
- apps Django movidos para `apps/web/django/`, preservando `AppConfig.label` historico e migrations existentes
- README, arquitetura web/admin/system overview e skills locais atualizados para a nova estrutura vigente
- status de implementação: `concluida`

### 2026-05-17 - v0.3
- adicionada skill `gotrendlabs-workflow-governor`
- adicionados templates em `docs/specs/workflows/`
- adicionados `workflow-runs.md` e `workflow-checklists.md`
- guia atualizado com fluxo de testes e governança de processo

### 2026-05-17 - v0.4
- adicionada skill `gotrendlabs-software-architect` para arquitetura, segurança e desenho técnico
- adicionada skill `gotrendlabs-test-engineer` para testes concretos de backend, frontend, integração e regressão
- workflows atualizados para exigir arquitetura/segurança em mudanças relevantes e testes executáveis quando houver código
