---
id: ARCH-MOBILE-API-001
titulo: "Contratos API para mobile"
versao: 0.1
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-06-16
origem:
  - docs/specs/architecture/backend-api.md
  - packages/contracts/openapi/gotrendlabs-api.json
contratos_afetados:
  - prediction-payloads.md
  - wallet-ledger.md
  - reputation-ranking.md
dependencias:
  - ARCH-MOBILE-001
impacta:
  - future-mobile
  - backend-api
aprovacao: pendente
---

# Contratos API para mobile

## Objetivo

Definir o conjunto inicial de contratos FastAPI que o app Flutter deve consumir no MVP, evitando acoplamento com templates Django e evitando endpoints novos sem necessidade comprovada.

## Diretriz principal

O mobile deve consumir a FastAPI como cliente JSON. Sempre que um endpoint ja atender web e mobile com payload adequado, o app deve reutilizar esse contrato. Novos campos ou endpoints devem atualizar o OpenAPI versionado e as specs afetadas.

## Base URL local

- Emulador Android API: `http://10.0.2.2:8001`
- Emulador Android web/media: `http://10.0.2.2:8000`
- iOS Simulator API: `http://127.0.0.1:8001`
- iOS Simulator web/media: `http://127.0.0.1:8000`
- Aparelho fisico na mesma rede: `http://<ip-do-mac>:8001`
- Chrome/web local: `http://127.0.0.1:8001`

Para o emulador renderizar imagens em `/media/...`, o Django local precisa escutar em host acessivel ao emulador e aceitar `10.0.2.2` em `GOTRENDLABS_ALLOWED_HOSTS`; caso contrario thumbnails de mercado e badges caem no fallback visual mesmo com `image_url` correto na API.

No iOS Simulator, `127.0.0.1` aponta para o Mac host, portanto o app pode usar os mesmos hosts locais de Django/FastAPI usados pelo navegador durante smoke tests.

## Saude e manutencao mobile

Endpoint esperado:

- `GET /health`

Uso no mobile:

- checagem de boot antes de liberar o shell publico
- diagnostico seguro na tela `Sobre`
- fallback para tela de manutencao quando a API nao responder

Campos esperados sem quebrar compatibilidade:

- `status`: continua retornando `ok` quando a API esta saudavel
- `maintenance.web_enabled`
- `maintenance.mobile_enabled`
- `maintenance.mobile_message`
- `checks.api`
- `checks.database`

Requisitos mobile:

- toda chamada do app envia `X-GoTrendLabs-Client: mobile`
- quando `maintenance.mobile_enabled=true`, o app mostra tela de manutencao antes do shell publico
- falha de rede, timeout ou status degradado tambem mostram a tela de manutencao
- durante manutencao mobile, o shell mobile permanece bloqueado para todos os usuarios do app
- a manutencao mobile e mais restritiva que a web: nao ha excecao por papel dentro do app
- FastAPI e a autoridade do bloqueio e pode retornar `503` com `code=mobile_maintenance` para chamadas mobile nao isentas

## Anti-abuso mobile

Endpoint esperado:

- `GET /anti-abuse/challenge`

Uso no mobile:

- cadastro de visitante no app
- envio de feedback por visitante
- envio de sugestao de mercado por visitante

Campos esperados:

- `prompt`: texto do desafio simples exibido pelo app
- `token`: token assinado pela FastAPI, com resposta esperada protegida por hash e expiracao curta
- `expires_at`: timestamp ISO para orientar refresh visual

Requisitos mobile:

- app exibe o desafio dentro do fluxo, sem abrir navegador externo
- payloads protegidos enviam `anti_abuse_token` e `anti_abuse_answer`
- FastAPI valida assinatura, expiracao e resposta; Flutter nao calcula nem decide elegibilidade
- reCAPTCHA v2 continua sendo o mecanismo web; o desafio mobile e usado apenas para clientes com `X-GoTrendLabs-Client: mobile`
- usuario autenticado nao precisa de desafio para feedback/sugestao

## Contratos de leitura publica

### Feed de mercados

Endpoint esperado:

- `GET /markets`

Uso no mobile:

- aba `Hoje`
- aba `Mercados`
- carrossel de destaque
- listas por categoria, subcategoria, evento e status

Campos minimos esperados:

- `slug`
- `title`
- `status`
- `category`
- `subcategory`
- `event`
- `image_url`
- `options[]`
- `primary_probability`
- `primary_probability_exact`
- `volume_gtl`
- `human_volume_gtl`
- `participants`
- `market_like_count`
- `comment_count`
- `viewer_has_prediction`
- `viewer_has_favorite`
- `viewer_has_like`
- `created_at`
- `close_at`
- `sparkline_series`

O app pode ordenar e filtrar visualmente os itens ja carregados, mas filtros autoritativos e recortes paginados devem vir da API quando o volume exigir.

Para mercado `open` com `auto_close_enabled=true` e `close_at` vencido, a FastAPI deve expor `status=locked` e `status_label=Fechado` nos contratos publicos e bloquear preview/criacao/reforco/revisao. O mobile nao deve inferir fechamento por relogio local.

### Detalhe de mercado

Endpoint esperado:

- `GET /markets/{slug}`

Uso no mobile:

- tela de detalhe
- ticket de previsao
- grafico de consenso
- bloco de comentarios
- resumo de ciclo do mercado

Campos minimos esperados:

- todos os campos relevantes do feed
- `summary` ou contexto equivalente quando disponivel, exibido no detalhe sem truncamento como unica forma de leitura
- `resolution_criteria`
- `category_notice`
- `subcategory_notice`
- `event_notice`
- `resolved_at`
- `resolved_at_label`
- `resolution_timezone`
- `winning_option_id`
- `resolution_note`
- `viewer_prediction` ou sinal equivalente quando existir

O app nao deve reconstruir regras de status; deve apresentar o estado vindo da API.

### Tracking publico de mercado

Endpoints esperados:

- `POST /markets/{slug}/view`
- `POST /markets/{slug}/share`

Uso no mobile:

- abrir o detalhe de mercado incrementa `view_count` apos o detalhe carregar e renderizar
- compartilhar pelo app incrementa `share_count` antes de acionar o compartilhamento nativo

Requisitos mobile:

- tracking deve ser best-effort e nunca bloquear detalhe ou compartilhamento
- web e mobile devem manter a mesma semantica operacional para popularidade
- o app nao deve recalcular popularidade de dominio; apenas aciona os endpoints de tracking e consome contadores retornados pela API

### Taxonomia publica

Endpoint esperado:

- `GET /taxonomy`

Uso no mobile:

- filtros de mercado
- filtros de ranking
- descoberta por categoria/subcategoria/evento
- seletor de categoria em `Sugerir mercado`, usando o nome canonico retornado pela API

Itens bloqueados logicamente nao devem aparecer para selecao publica.

### Estatisticas publicas

Endpoint esperado:

- `GET /stats`

Uso no mobile:

- resumo educativo em onboarding, Hoje ou perfil publico
- numeros de produto sem sugerir dinheiro real

## Contratos autenticados

### Autenticacao e sessao

Endpoints esperados, conforme implementacao FastAPI vigente:

- login
- cadastro
- logout/revogacao de sessao quando disponivel
- recuperacao de senha
- `GET /users/me`
- edicao de perfil autenticado

Requisitos mobile:

- respostas devem diferenciar credencial invalida, email nao confirmado, sessao expirada e conta desativada
- o app deve conseguir restaurar sessao de forma segura ao abrir
- usuario com email nao confirmado deve ver modo limitado e bloqueio de acoes sensiveis

Se a autenticacao atual estiver orientada a cookie web, uma decisao tecnica deve definir a estrategia mobile antes de implementar login persistente.

Decisao v1 para a implementacao autenticada:

- usar Bearer simples retornado em `AuthResponse.session.token`
- oferecer `Lembrar login` ligado por padrao
- persistir token no Flutter com secure storage quando `Lembrar login` estiver ligado
- manter token apenas em memoria e limpar persistencia local quando `Lembrar login` estiver desligado
- restaurar sessao por `GET /auth/session`
- encerrar sessao por `POST /auth/logout`
- usar a expiracao existente em `AuthResponse.session.expires_at`
- manter o gate mobile de manutencao baseado em `GET /health` e no bloqueio autoritativo da FastAPI, sem excecao por papel no app
- deixar refresh token, renovacao automatica e revogacao avancada para etapa futura
- biometria no app e apenas desbloqueio local de sessao lembrada: nao cria endpoint, nao muda OpenAPI, nao envia dado biometrico ao backend e nao substitui validacao de sessao por `GET /auth/session`
- ao restaurar sessao protegida, o app deve ativar o Bearer token em memoria apenas apos sucesso da autenticacao local do aparelho; cancelamento deve deixar o usuario em estado `Sessao protegida`

### Favoritos e curtidas de mercado

Endpoints esperados:

- `POST /markets/{slug}/favorite`
- `DELETE /markets/{slug}/favorite`
- `POST /markets/{slug}/like`
- `DELETE /markets/{slug}/like`

Requisitos mobile:

- mutacoes idempotentes
- atualizacao otimista permitida apenas como estado visual temporario
- rollback visual quando a API rejeitar a acao
- visitante recebe CTA de login em vez de formulario mutavel

### Preview e criacao de previsao

Endpoints esperados:

- `POST /markets/{slug}/prediction-preview`
- endpoint de criacao de previsao conforme contrato `prediction-payloads.md`
- `POST /markets/{slug}/position-preview`
- `POST /markets/{slug}/position-actions`

Requisitos mobile:

- preview sempre calculado pela API
- app pode chamar preview de forma reativa ao selecionar opcao ou mover o controle de GT₵, com debounce, sem calcular retorno localmente
- criacao exige usuario autenticado, opcao explicita e stake valido
- duplicidade de previsao, saldo insuficiente e mercado fechado devem gerar erro mapeavel
- resposta de sucesso deve retornar saldo atualizado e snapshot de probabilidade
- `POST /markets/{slug}/predict` e usado somente quando `viewer_position.has_position=false`; usuario com posicao ativa usa os contratos de reforco/revisao
- reforco mobile usa `action=reinforcement`, a mesma `option_id` da posicao ativa e `stake_amount` informado pelo usuario
- revisao mobile usa `action=revision`, uma `option_id` diferente da ativa e `stake_amount=0`, preservando custo, valor encerrado e nova posicao estimada calculados pela FastAPI
- confirmacao de reforco/revisao exige preview valido da FastAPI com `allowed=true` e assinatura ainda coerente com acao/opcao/valor selecionados
- bloqueios devem exibir `blocked_reason`, `reinforcement_blocked_reason` ou `revision_blocked_reason` sem traduzir para regra local

### Comentarios

Endpoints esperados:

- `GET /markets/{slug}/comments`
- `POST /markets/{slug}/comments`
- `POST /comments/{id}/like`
- `DELETE /comments/{id}/like`
- `POST /comments/{id}/dislike`
- `DELETE /comments/{id}/dislike`

Requisitos mobile:

- visitantes leem comentarios e recebem CTA de login para comentar
- autores aparecem por handle publico
- autores IA oficiais exibem selo `IA oficial`
- comentarios ocultos por moderacao nao aparecem

### Wallet

Endpoints esperados:

- `GET /users/me/wallet`
- `GET /users/me/ledger`
- `GET /users/me/wallet/recharge-requests`
- `POST /users/me/wallet/recharge-requests`

Requisitos mobile:

- saldo e extrato sao leitura da API
- recarga controlada usa `available_gtl`, `min_balance_gtl`, `eligible` e `requests` retornados pela API
- app mostra pendencia e historico, mas o `POST` continua sendo a autoridade para elegibilidade, duplicidade e email confirmado
- labels humanos devem evitar codigos tecnicos de ledger
- `GTL` ou `GT₵` deve ser tratado como moeda educativa, sem copy de dinheiro real, saque ou investimento

### Ranking e badges

Endpoints esperados:

- `GET /rankings`
- `GET /badges`
- `GET /users/me/badges`
- compartilhamento de badge conquistada quando disponivel

Requisitos mobile:

- staff, superuser e bots nao aparecem no ranking publico
- app nao calcula elegibilidade de badge
- imagens de badge em `/media/...` sao resolvidas contra o web/public base, nao contra a FastAPI
- compartilhamento nao altera reputacao, wallet ou ranking

### Indicacao

Endpoint esperado:

- `GET /users/me/referral`

Requisitos mobile:

- app apenas exibe e compartilha o codigo/link retornado pelo backend
- bonus, habilitacao, razao de bloqueio e credito ficam sob autoridade backend/Admin Ops

### Push mobile

Endpoints esperados:

- `GET /users/me/push-devices`
- `POST /users/me/push-devices`
- `DELETE /users/me/push-devices/{device_id}`
- `GET /users/me/push-preferences`
- `PATCH /users/me/push-preferences`

Requisitos mobile:

- app so tenta registrar dispositivo apos autenticacao restaurada ou login concluido
- logout normal nao chama revoke de dispositivo
- revoke e desativacao de preferencias sao acoes explicitas do usuario
- quando Firebase nao esta configurado, o app nao coleta token real e pode usar `GTL_PUSH_FAKE_TOKEN` apenas para QA local sem entrega
- quando FCM esta configurado no Android, token real e enviado apenas para a FastAPI apos autenticacao
- payload de push contem apenas IDs, rota e `event_type`; o app busca o estado real na API ao abrir

### Sugestoes e feedback

Endpoints esperados:

- `GET /anti-abuse/challenge`
- `POST /suggestions`
- `POST /feedback`

Requisitos mobile:

- formulario mobile envia payload JSON para a FastAPI
- sugestao de mercado usa categorias ativas de `GET /taxonomy`
- feedback usa as mesmas opcoes publicas da web e envia `severity=medium` como compatibilidade de contrato
- usuario autenticado nao informa nome/email de visitante
- visitante identificado informa nome/email e completa desafio anti-abuso mobile quando o backend exigir
- app nao aprova sugestao, nao converte sugestao em mercado e nao calcula recompensa
- app nao recompensa feedback; status, revisao e creditos ficam no backend/Admin Ops

## Erros padronizados para UX

O app deve mapear erros de API para categorias:

- `unauthenticated`: solicitar login
- `forbidden`: acao nao permitida
- `validation`: campos invalidos
- `domain_state`: mercado fechado, resolvido, cancelado ou previsao duplicada
- `insufficient_balance`: saldo educativo insuficiente
- `network`: indisponibilidade local ou conexao
- `server`: falha inesperada

Mensagens tecnicas devem ficar fora da UI final.

## OpenAPI e clientes gerados

- Toda alteracao de contrato deve atualizar `packages/contracts/openapi/gotrendlabs-api.json`.
- O mobile pode usar cliente HTTP manual no MVP para manter velocidade.
- Cliente gerado a partir do OpenAPI pode ser avaliado quando os contratos estabilizarem.
- `gotrendlabs-mobile-api-contract-guard` deve revisar qualquer PR que altere payload consumido pelo app.

## Criterios de aceite

- o app consegue listar mercados via API local no emulador
- o app consegue abrir detalhe de mercado sem depender do Django
- visitante ve estados autenticados bloqueados sem erro bruto
- mutacoes autenticadas usam apenas FastAPI
- contrato novo necessario e documentado antes de implementado
- lacunas de auth mobile estao registradas antes de login persistente
