---
id: FEAT-NOTIFY-001
titulo: "Notificações e email"
versao: 0.4
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-06-08
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - domain-events.md
  - i18n-content.md
dependencias:
  - FEAT-AUTH-001
  - FEAT-PRED-001
  - FEAT-RES-001
impacta:
  - backend-api
  - communications
  - database
  - future-mobile
aprovacao: pendente
---

# Notificações e email

## Objetivo

Enviar comunicações transacionais e de engajamento compatíveis com o idioma e o estado do usuário.

## Escopo incluído

- notificações in-app sociais persistidas para usuários autenticados
- templates transacionais editáveis no Admin Ops por chave em PT-BR
- email de boas-vindas para conta nova
- email de confirmação de endereço quando necessário
- email de recuperação de senha com link expirável
- aviso de mercado fechado
- aviso de mercado resolvido
- aviso de crédito concedido
- comunicações de feedback/sugestão quando definido
- outbox `EmailDelivery` com idempotência, retries e trilha de falha/envio
- configuração operacional não sensível de email no Admin Ops, com provider SMTP ou Resend
- área Admin Ops `Politica de Emails` com edição de templates PT-BR e logs de entrega da outbox
- envio transacional via Resend API HTTPS com domínio remetente verificado
- base de push mobile por FCM, com provider `none`/dry-run como default seguro e provider `fcm` real habilitável por ambiente
- políticas e templates de push editáveis no Admin Ops por evento, sem segredos
- outbox `PushDelivery` drenada pelo daemon, sempre derivada de `UserNotification`
- endpoints autenticados para registrar, listar e revogar dispositivos de push e preferências do usuário

## Escopo excluído

- automação de marketing complexa
- newsletter
- armazenamento de senha/API key SMTP ou Resend no banco ou na interface administrativa
- armazenamento de credenciais Firebase no banco, Git ou Admin Ops
- feed em tempo real/websocket de notificações
- armazenamento de API key Resend no banco, Git ou Admin Ops
- bounce/complaint webhooks
- editor visual avançado de email
- configuração APNs direta fora do Firebase

## Fluxo do usuário

Usuário recebe mensagens coerentes com ações relevantes ou estados importantes do produto.

Usuário autenticado vê um sino de notificações no topo com contador de não lidas e últimas interações sociais relacionadas a mercados em que registrou previsão.

## Comportamento esperado

- eventos de domínio disparam comunicações elegíveis
- emails transacionais são enfileirados em outbox antes do envio pelo provider configurado
- emails críticos de identidade e acesso tentam envio imediato após commit, com fallback para retry do daemon; nesta fatia: confirmação de conta, reenvio de confirmação, mudança de email e recuperação de senha
- alertas futuros de senha alterada, novo login suspeito, conta desativada e ações administrativas críticas devem seguir a mesma política de envio imediato
- eventos de produto, digest, notificações sociais, avisos operacionais menos urgentes e envios em massa permanecem processados pelo daemon
- todos os emails transacionais recebem rodapé institucional automático com identificação da GoTrendLabs e URL oficial
- push mobile é enfileirado em outbox antes de qualquer tentativa de entrega
- ações sociais geram notificações in-app sem duplicidade por evento de origem
- créditos recebidos, badges conquistadas e mudanças relevantes em mercados participados geram notificações in-app
- usuários podem marcar todas as notificações in-app como lidas
- idioma respeita preferência do usuário
- templates ativos usam PT-BR na edição operacional desta versão, com fallback controlado no código quando necessário
- falhas de provider são registradas com retry e sem expor segredo operacional

## Regras de domínio

- comunicações dependem de eventos confiáveis
- preferências do usuário e regras operacionais precisam ser respeitadas
- para notificações sociais, "mercados participados" significa mercados nos quais o usuário registrou previsão
- nova previsão, curtida de mercado e comentário em mercado notificam outros usuários que também previram naquele mercado
- curtida em comentário notifica o autor do comentário
- créditos recebidos notificam o usuário creditado
- fechamento e resolução de mercado notificam usuários humanos que registraram previsão naquele mercado
- badge conquistada notifica o usuário premiado
- ações próprias não geram auto-notificação
- ações de usuários `is_bot=true` não disparam notificações sociais nesta versão
- eventos operacionais/sistêmicos podem notificar o próprio usuário quando o destinatário é o beneficiário direto, como créditos e badges
- `user.welcome`, `user.email_confirmation`, `account.password_reset`, `market.locked`, `market.resolved` e `wallet.credited` criam entregas idempotentes em `EmailDelivery`
- a resposta pública de recuperação de senha não expõe o link; o link é enviado apenas pelo template transacional
- recuperação de senha deve tentar envio imediato após o commit, mantendo retry pelo daemon apenas como fallback operacional
- links enviados por email devem ser absolutos para funcionarem fora do navegador atual
- toda push notification nasce de uma `UserNotification` persistida
- nem toda `UserNotification` vira push; `PushEventPolicy` define `off`, `immediate` ou `digest`
- nesta fase, `digest` existe como contrato/configuração, mas não dispara envio agrupado
- `market_resolved`, `market_locked`, `wallet_credit`, `badge_awarded`, `market_comment` e `comment_like` são imediatos por padrão
- `market_prediction` e `market_like` ficam desligados por padrão
- templates padrão de push devem ser curtos, discretos e seguros:
  - `market_resolved`: "Resultado publicado" / "`{{ market_title }}` foi resolvido. Abra o app para ver o resultado."
  - `market_locked`: "Mercado em apuração" / "`{{ market_title }}` fechou para novas previsões"
  - `wallet_credit`: "Carteira atualizada" / "Sua carteira educativa foi atualizada. Confira no app."
  - `badge_awarded`: "Nova badge" / "Você desbloqueou `{{ badge_name }}`."
  - `market_comment`: "Novo comentário" / "`{{ actor_handle }}` comentou em `{{ market_title }}`"
  - `comment_like`: "Curtida no comentário" / "`{{ actor_handle }}` curtiu seu comentário."
  - `market_prediction`: "Nova previsão no mercado" / "`{{ actor_handle }}` fez uma previsão em `{{ market_title }}`"
  - `market_like`: "Mercado curtido" / "`{{ actor_handle }}` curtiu `{{ market_title }}`"
- logout normal no app mobile não revoga push automaticamente
- usuário pode revogar dispositivo ou desativar preferências de push
- tokens rejeitados pelo provedor devem desativar o dispositivo automaticamente
- payload de push contém apenas IDs, rota e `event_type`; dados sensíveis são buscados na FastAPI ao abrir o app
- Admin Ops deve exibir o fallback seguro do código ao lado do template editável, para o operador entender o texto usado quando o template salvo estiver inativo ou ausente
- Admin Ops pode criar teste manual escolhendo um `PushDevice` ativo; o teste cria `UserNotification` e `PushDelivery`, respeita flags/provider atuais e nunca renderiza o token bruto
- Admin Ops possui aba `Dispositivos` em Push mobile para listar devices registrados, status, plataforma, versão/build, hash parcial do token, última atividade e contadores de entrega, sem expor token bruto
- Dashboard Admin Ops deve exibir saúde de push mobile com estado de configuração, devices ativos, fila pendente/vencida e entregas/falhas recentes, apontando para os logs de `PushDelivery`

## Responsabilidades por camada

- `backend-api`: emitir eventos e contexto
- `communications`: selecionar template, idioma, renderizar conteúdo, registrar entrega e enviar por SMTP/push provider quando habilitado
- `database`: trilha de envio quando necessário e inbox persistida de notificações in-app
- `frontend-web`: sino, contador de não lidas, dropdown de últimas notificações e ação de marcar lidas
- `future-mobile`: registra token após autenticação quando houver provider real, exibe controles de revogação/preferência e refaz fetch na FastAPI ao abrir push

## Dados e persistência

- eventos consumidos
- templates
- `communications_emailtemplate`: chave, idioma, assunto, corpo texto/HTML, ativo e metadados de edição; Admin Ops expõe apenas PT-BR nesta fatia
- `communications_emaildelivery`: outbox com destinatário, template, contexto, status, tentativas, próximo retry, erro, timestamps e chave de idempotência
- `communications_emailconfirmationtoken`: hash de token, expiração, uso único e auditoria mínima
- `gotrendlabs_user_notifications`: destinatário, ator, mercado, comentário, tipo, chave de origem, título, corpo, estado de leitura, metadata e data
- `gotrendlabs_push_devices`: usuário, provider, plataforma, token, hash, metadados de app, flags de atividade/revogação/invalidação e timestamps
- `gotrendlabs_push_event_policies`: evento, modo, default de usuário, prioridade, template e variáveis permitidas
- `gotrendlabs_push_templates`: título/corpo por evento/idioma, ativo e variáveis permitidas
- `gotrendlabs_push_deliveries`: outbox idempotente por notificação/dispositivo, payload seguro, status, tentativas, erro e provider message id
- `gotrendlabs_push_preferences`: opt-in/opt-out global ou por evento
- configuração singleton de email: ativo, provider, remetente, reply-to, timeout e, para SMTP, host, porta, usuário e TLS/SSL
- domínio remetente Resend verificado para `gotrendlabs.com.br`; `GOTRENDLABS_RESEND_API_KEY` é mantida fora do banco e da interface
- SMTP genérico pode ser configurado como fallback, com senha/API key mantida fora do banco e da interface
- flags de push vêm do ambiente: `GOTRENDLABS_PUSH_ENABLED`, `GOTRENDLABS_PUSH_PROVIDER`, `GOTRENDLABS_PUSH_DRY_RUN` e `GOTRENDLABS_FCM_CREDENTIALS_JSON`

## Contratos afetados

- `domain-events.md`
- `i18n-content.md`

## I18n e conteúdo

- templates precisam existir pelo menos em `pt-BR` e `en`

## Observabilidade e operação

- taxa de entrega, falha e reenvio
- parâmetros não sensíveis de email são administráveis por staff; segredo de envio vem de variável de ambiente/secret manager
- teste operacional Resend usa `send_resend_test_email` e exige domínio remetente verificado
- Admin Ops permite editar assunto e corpos de templates PT-BR ativos sem revelar segredos de SMTP
- Admin Ops lista entregas `EmailDelivery` com filtros por status, template, destinatário e período, sem renderizar contexto/corpo com links sensíveis
- Admin Ops mostra todas as variáveis disponíveis por template, com nome, descrição, exemplo de uso e valor de exemplo.
- Admin Ops permite visualizar localmente o email HTML renderizado com valores de exemplo, sem salvar alteração nem disparar envio.
- O rodapé automático dos emails transacionais é customizável pelo template especial `system.transactional_footer`; a prévia dos demais templates mostra o rodapé configurado e o envio usa fallback seguro do código quando esse template não estiver ativo.
- Dashboard/daemon reportam resumo do processamento de email por ciclo
- Admin Ops permite editar políticas/templates de push por evento, com variáveis permitidas e preview seguro.
- Admin Ops lista entregas `PushDelivery` com filtros por status/evento/provider, sem renderizar token de dispositivo nem segredo.
- Dashboard/daemon reportam resumo do processamento de push por ciclo, incluindo sinal de fila pendente, dry-run, falhas recentes, tokens inválidos e devices ativos.

## Testes esperados

- integração de evento para envio
- renderização de template, interpolação segura e fallback de idioma
- confirmação de email com expiração, uso único, token inválido e reenvio limitado
- login limitado para conta sem email confirmado e liberação após confirmação
- outbox com idempotência, retries, estados `queued`/`sending`/`sent`/`failed`/`suppressed` e falhas de provider
- processamento de push com claim transacional curto, envio FCM fora de lock longo e recuperação de entregas antigas em `sending`
- recuperação de senha com envio imediato quando o provider está pronto e link absoluto no template renderizado
- criação idempotente de notificações in-app para previsão, curtida de mercado, comentário, curtida de comentário, crédito recebido, fechamento/resolução de mercado e badge recebida
- listagem autenticada de notificações com contador de não lidas
- marcação de todas como lidas
- verificação de idioma correto
- validação de configuração SMTP, incluindo bloqueio de TLS e SSL simultâneos, e de configuração Resend com remetente obrigatório
- validação operacional do comando de teste Resend sem expor segredo nem gravar credencial sensível
- registro autenticado, listagem e revogação de `PushDevice`
- preferências globais e por evento bloqueando enfileiramento
- outbox de push criada apenas quando existe `UserNotification` nova e política imediata
- defaults `market_prediction`/`market_like` desligados
- daemon marcando provider `none` como `dry_run` e tokens inválidos como `invalid_token`
- payload de push sem email, token, ledger, valores de wallet ou segredo
- Dashboard Admin Ops exibindo saúde de push sem expor token, payload sensível ou segredo FCM
- aba Admin Ops de dispositivos listando `PushDevice` com filtros por status/plataforma/provider, status mutuamente exclusivo, hash parcial e sem token bruto
- Flutter não registra token quando Firebase não está configurado; quando `google-services.json` local existe, o token FCM é coletado e registrado somente após autenticação

## Critérios de aceite

- mensagens são disparadas pelos eventos corretos e no idioma esperado
- usuários logados veem notificações sociais persistidas e podem limpar o contador de não lidas
- staff consegue visualizar e alterar parâmetros não sensíveis de email sem expor senha/API key
- staff consegue visualizar e editar templates PT-BR por chave, incluindo variáveis disponíveis e preview HTML local
- operador consegue validar Resend com domínio remetente verificado e segredo vindo do ambiente
- provider `none`/dry-run permite validar a outbox sem envio real
- Admin Ops controla políticas/templates de push sem expor credenciais
- Admin Ops permite consultar dispositivos de push registrados sem expor token bruto
- Admin Ops mostra saúde de push no Dashboard e permite navegar para logs de entrega quando houver fila/falha
- app mobile registra/revoga dispositivos via FastAPI quando Firebase está configurado, mantendo `GTL_PUSH_FAKE_TOKEN` como modo local sem entrega real

## Impacto de mudança

Mudanças podem afetar retenção, operação e experiência percebida, mesmo sem alterar o núcleo do domínio.
