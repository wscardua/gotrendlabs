# Communications

## Responsabilidades

- Receber eventos de negócio.
- Selecionar template, idioma e contexto.
- Orquestrar envio de email transacional e futuras notificações.
- Registrar sucesso, falha, reenvio e trilha operacional.
- Consumir configuração operacional não sensível de email do banco.
- Orquestrar push mobile por outbox própria quando habilitado por ambiente.

## Limites

- Não decidir elegibilidade de negócio fora do contrato recebido.
- Não duplicar textos de produto fora do sistema de templates versionados.
- Não assumir idioma por padrão quando existir preferência do usuário.
- Não persistir nem expor senha/API key de SMTP ou Resend; segredos vêm do ambiente/secret manager.
- Não persistir nem expor credenciais Firebase; segredos vêm do ambiente/secret manager.
- Não enviar push diretamente no request que cria a notificação in-app.

## Eventos v1

- `user.welcome`: boas-vindas para conta nova, inclusive social com email já verificado.
- `user.email_confirmation`: link expirável de confirmação quando a conta ainda não tem email confirmado.
- `account.password_reset`: link expirável de recuperação de senha, sem expor `reset_url` na resposta pública.
- `market.locked`: aviso de mercado fechado para participantes humanos.
- `market.resolved`: aviso de mercado resolvido para participantes humanos.
- `wallet.credited`: aviso de créditos concedidos ao beneficiário.
- `notification.created`: fonte persistida para avaliar política de push mobile.

## Persistência e envio

- `EmailTemplate` guarda templates ativos por chave e idioma, com assunto, corpo texto/HTML e metadados de edição.
- `EmailDelivery` é a outbox idempotente de envio, com destinatário, template, contexto JSON, snapshots renderizados, status, tentativas, próximo retry, erro e data de envio.
- `EmailConfirmationToken` guarda hash do token, expiração, uso único e auditoria mínima.
- O daemon operacional drena entregas `queued`/`failed`, aplica retries e registra `sent`, `failed` ou `suppressed`.
- Emails críticos de identidade e acesso tentam drenar a outbox imediatamente após o commit da ação; nesta fatia isso inclui `user.welcome` em criação de conta, `user.email_confirmation` em criação de conta/reenvio/mudança de email e `account.password_reset`.
- Falhas no envio imediato não devem quebrar o fluxo principal: a entrega permanece rastreada como `queued`/`failed` para retry pelo daemon e visibilidade no Admin Ops.
- Eventos de produto e volume, como `market.locked`, `market.resolved`, `wallet.credited`, digest, notificações sociais e avisos operacionais menos urgentes, continuam drenados pelo daemon.
- Todos os emails transacionais renderizados recebem rodapé institucional automático. O conteúdo vem do template editável `system.transactional_footer`; se ele estiver ausente/inativo, `communications` usa fallback seguro do código com identificação da GoTrendLabs, descrição curta e URL oficial.
- Links transacionais renderizados em email devem ser absolutos, usando `GOTRENDLABS_PUBLIC_BASE_URL` ou o fallback local seguro em desenvolvimento.
- `PushDevice` guarda tokens mobile por usuário/dispositivo, com revogação lógica e invalidação por provedor.
- `PushEventPolicy` define `off`, `immediate` ou `digest` por evento; `digest` não envia nesta primeira fase.
- `PushTemplate` guarda título/corpo curto por evento/idioma, com preview seguro no Admin Ops.
- `PushDelivery` é a outbox idempotente por `UserNotification` e dispositivo, drenada pelo daemon.
- Provider `none` com dry-run marca entregas como `dry_run` sem chamada externa.
- A saúde operacional de push é agregada para o Dashboard Admin Ops com flags/provider, devices ativos, fila pendente/vencida, entregas dry-run/enviadas, falhas recentes e tokens inválidos, sem expor token bruto ou payload sensível.
- Admin Ops lista dispositivos de push registrados com estado operacional, app version/build, hash parcial e agregados de entrega, mas nunca renderiza token bruto.
- O provider Resend depende de domínio remetente verificado no dashboard Resend; erros de domínio/API são registrados como falhas com retry na outbox.
- A confirmação de email habilita login limitado: usuários recém-criados podem entrar, mas ações sensíveis continuam bloqueadas até confirmar o endereço.
- Reenvio de confirmação possui janela mínima simples para evitar abuso.

## Configuração operacional

- `gotrendlabs_site_config` é a tabela singleton de configurações persistentes do site; communications usa `email_provider`, status ativo, remetente, reply-to, timeout e, quando SMTP estiver selecionado, host, porta, usuário, TLS/SSL.
- `GOTRENDLABS_SMTP_PASSWORD` ou `GOTRENDLABS_SMTP_API_KEY` mantém o segredo de envio fora do banco.
- `GOTRENDLABS_RESEND_API_KEY` mantém a API key Resend fora do banco/Admin Ops/Git.
- `GOTRENDLABS_PUSH_ENABLED=0`, `GOTRENDLABS_PUSH_PROVIDER=none` e `GOTRENDLABS_PUSH_DRY_RUN=1` são os defaults seguros de push.
- Envio FCM real exige `GOTRENDLABS_PUSH_ENABLED=1`, `GOTRENDLABS_PUSH_PROVIDER=fcm`, `GOTRENDLABS_PUSH_DRY_RUN=0` e `GOTRENDLABS_FCM_CREDENTIALS_JSON` com o service account JSON cru ou base64 fora do banco/Git/Admin Ops.
- O daemon envia FCM via Firebase Admin SDK, grava `provider_message_id` em sucesso, agenda retry em falha transitória e invalida o `PushDevice` quando o provedor rejeita o token.
- O daemon faz claim de `PushDelivery` em transação curta, libera locks antes da chamada externa ao FCM e recupera entregas presas em `sending` há mais de 15 minutos.
- TLS e SSL são mutuamente exclusivos.
- Produção usa Resend como provider transacional preferencial; SMTP permanece apenas como fallback genérico configurável.
- O remetente operacional padrão é `no-reply@gotrendlabs.com.br`.
- O comando `send_resend_test_email` valida o envio Resend via API HTTPS usando o remetente/reply-to do Admin Ops e o segredo do ambiente.
- Para Resend, o domínio `gotrendlabs.com.br` deve estar verificado com SPF/DKIM no dashboard; DMARC é recomendado. Após verificação, não é necessário criar o endereço `no-reply@...` no Resend para usar esse remetente.
