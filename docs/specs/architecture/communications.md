# Communications

## Responsabilidades

- Receber eventos de negócio.
- Selecionar template, idioma e contexto.
- Orquestrar envio de email transacional e futuras notificações.
- Registrar sucesso, falha, reenvio e trilha operacional.
- Consumir configuração SMTP operacional não sensível do banco.

## Limites

- Não decidir elegibilidade de negócio fora do contrato recebido.
- Não duplicar textos de produto fora do sistema de templates versionados.
- Não assumir idioma por padrão quando existir preferência do usuário.
- Não persistir nem expor senha/API key de SMTP; segredos vêm do ambiente/secret manager.

## Eventos v1

- `user.email_confirmation`: boas-vindas e link expirável de confirmação de email.
- `account.password_reset`: link expirável de recuperação de senha, sem expor `reset_url` na resposta pública.
- `market.locked`: aviso de mercado fechado para participantes humanos.
- `market.resolved`: aviso de mercado resolvido para participantes humanos.
- `wallet.credited`: aviso de créditos concedidos ao beneficiário.

## Persistência e envio

- `EmailTemplate` guarda templates ativos por chave e idioma, com assunto, corpo texto/HTML e metadados de edição.
- `EmailDelivery` é a outbox idempotente de envio, com destinatário, template, contexto JSON, snapshots renderizados, status, tentativas, próximo retry, erro e data de envio.
- `EmailConfirmationToken` guarda hash do token, expiração, uso único e auditoria mínima.
- O daemon operacional drena entregas `queued`/`failed`, aplica retries e registra `sent`, `failed` ou `suppressed`.
- Enquanto `GOTRENDLABS_SES_PRODUCTION_ACCESS` não estiver ativo, o envio SMTP real é bloqueado para destinatários fora do mailbox simulator do SES ou da allowlist operacional.
- A confirmação de email habilita login limitado: usuários recém-criados podem entrar, mas ações sensíveis continuam bloqueadas até confirmar o endereço.
- Reenvio de confirmação possui janela mínima simples para evitar abuso.

## Configuração operacional

- `gotrendlabs_site_config` é a tabela singleton de configurações persistentes do site; communications usa os campos SMTP: host, porta, usuário, TLS/SSL, timeout, remetente, reply-to e status ativo.
- `GOTRENDLABS_SMTP_PASSWORD` ou `GOTRENDLABS_SMTP_API_KEY` mantém o segredo de envio fora do banco.
- TLS e SSL são mutuamente exclusivos.
- Para produção MVP, o provedor SMTP é Amazon SES em `us-east-1`, com identidades `gotrendlabs.com.br` e `gotrendlabs.com` verificadas por Easy DKIM.
- O remetente operacional padrão é `no-reply@gotrendlabs.com.br`, usando `email-smtp.us-east-1.amazonaws.com`, porta `587`, STARTTLS ativo e SSL direto inativo.
- O comando `send_smtp_test_email` valida a configuração SMTP com o mailbox simulator do SES enquanto a conta estiver em sandbox.
