# Communications

## Responsabilidades

- Receber eventos de negócio.
- Selecionar template, idioma e contexto.
- Orquestrar envio de email e futuras notificações.
- Registrar sucesso, falha, reenvio e trilha operacional.
- Consumir configuração SMTP operacional não sensível do banco quando o módulo de envio estiver ativo.

## Limites

- Não decidir elegibilidade de negócio fora do contrato recebido.
- Não duplicar textos de produto fora do sistema de templates versionados.
- Não assumir idioma por padrão quando existir preferência do usuário.
- Não persistir nem expor senha/API key de SMTP; segredos vêm do ambiente/secret manager.

## Eventos iniciais

- boas-vindas/cadastro
- confirmação de previsão
- mercado resolvido
- lembrete de mercado relevante
- feedback/sugestão recebida

## Configuração operacional

- `gotrendlabs_site_config` é a tabela singleton de configurações persistentes do site; communications usa os campos SMTP: host, porta, usuário, TLS/SSL, timeout, remetente, reply-to e status ativo.
- `GOTRENDLABS_SMTP_PASSWORD` ou `GOTRENDLABS_SMTP_API_KEY` mantém o segredo de envio fora do banco.
- TLS e SSL são mutuamente exclusivos.
