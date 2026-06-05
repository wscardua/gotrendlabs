---
id: FEAT-NOTIFY-001
titulo: "Notificações e email"
versao: 0.3
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-06-05
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
aprovacao: pendente
---

# Notificações e email

## Objetivo

Enviar comunicações transacionais e de engajamento compatíveis com o idioma e o estado do usuário.

## Escopo incluído

- notificações in-app sociais persistidas para usuários autenticados
- templates transacionais editáveis no Admin Ops por chave em PT-BR
- email de boas-vindas com confirmação de endereço
- email de recuperação de senha com link expirável
- aviso de mercado fechado
- aviso de mercado resolvido
- aviso de crédito concedido
- comunicações de feedback/sugestão quando definido
- outbox `EmailDelivery` com idempotência, retries e trilha de falha/envio
- configuração operacional SMTP não sensível no Admin Ops
- área Admin Ops `Politica de Emails` com edição de templates PT-BR e logs de entrega da outbox
- infraestrutura SMTP SES em `us-east-1` com identidades de domínio verificadas por DKIM

## Escopo excluído

- automação de marketing complexa
- newsletter
- push mobile
- armazenamento de senha/API key SMTP no banco ou na interface administrativa
- feed em tempo real/websocket de notificações
- concessão de production access do SES
- bounce/complaint webhooks
- editor visual avançado de email

## Fluxo do usuário

Usuário recebe mensagens coerentes com ações relevantes ou estados importantes do produto.

Usuário autenticado vê um sino de notificações no topo com contador de não lidas e últimas interações sociais relacionadas a mercados em que registrou previsão.

## Comportamento esperado

- eventos de domínio disparam comunicações elegíveis
- emails transacionais são enfileirados em outbox antes do envio SMTP
- ações sociais geram notificações in-app sem duplicidade por evento de origem
- créditos recebidos, badges conquistadas e mudanças relevantes em mercados participados geram notificações in-app
- usuários podem marcar todas as notificações in-app como lidas
- idioma respeita preferência do usuário
- templates ativos usam PT-BR na edição operacional desta versão, com fallback controlado no código quando necessário
- em sandbox SES, o daemon suprime envio para destinatários comuns fora do simulator/allowlist

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
- `user.email_confirmation`, `account.password_reset`, `market.locked`, `market.resolved` e `wallet.credited` criam entregas idempotentes em `EmailDelivery`
- a resposta pública de recuperação de senha não expõe o link; o link é enviado apenas pelo template transacional

## Responsabilidades por camada

- `backend-api`: emitir eventos e contexto
- `communications`: selecionar template, idioma, renderizar conteúdo, registrar entrega e enviar por SMTP
- `database`: trilha de envio quando necessário e inbox persistida de notificações in-app
- `frontend-web`: sino, contador de não lidas, dropdown de últimas notificações e ação de marcar lidas

## Dados e persistência

- eventos consumidos
- templates
- `communications_emailtemplate`: chave, idioma, assunto, corpo texto/HTML, ativo e metadados de edição; Admin Ops expõe apenas PT-BR nesta fatia
- `communications_emaildelivery`: outbox com destinatário, template, contexto, status, tentativas, próximo retry, erro, timestamps e chave de idempotência
- `communications_emailconfirmationtoken`: hash de token, expiração, uso único e auditoria mínima
- `gotrendlabs_user_notifications`: destinatário, ator, mercado, comentário, tipo, chave de origem, título, corpo, estado de leitura, metadata e data
- configuração SMTP singleton: ativo, host, porta, usuário, TLS/SSL, timeout, remetente e reply-to
- identidades SES verificadas para `gotrendlabs.com.br` e `gotrendlabs.com`; credencial SMTP dedicada é mantida fora do banco e da interface

## Contratos afetados

- `domain-events.md`
- `i18n-content.md`

## I18n e conteúdo

- templates precisam existir pelo menos em `pt-BR` e `en`

## Observabilidade e operação

- taxa de entrega, falha e reenvio
- parâmetros SMTP são administráveis por staff; segredo de envio vem de variável de ambiente/secret manager
- teste sandbox usa `success@simulator.amazonses.com` antes de production access
- Admin Ops permite editar assunto e corpos de templates PT-BR ativos sem revelar segredos de SMTP
- Admin Ops lista entregas `EmailDelivery` com filtros por status, template, destinatário e período, sem renderizar contexto/corpo com links sensíveis
- Admin Ops mostra todas as variáveis disponíveis por template, com nome, descrição, exemplo de uso e valor de exemplo.
- Admin Ops permite visualizar localmente o email HTML renderizado com valores de exemplo, sem salvar alteração nem disparar envio.
- Dashboard/daemon reportam resumo do processamento de email por ciclo

## Testes esperados

- integração de evento para envio
- renderização de template, interpolação segura e fallback de idioma
- confirmação de email com expiração, uso único, token inválido e reenvio limitado
- login limitado para conta sem email confirmado e liberação após confirmação
- outbox com idempotência, retries, estados `queued`/`sending`/`sent`/`failed`/`suppressed` e bloqueio sandbox
- criação idempotente de notificações in-app para previsão, curtida de mercado, comentário, curtida de comentário, crédito recebido, fechamento/resolução de mercado e badge recebida
- listagem autenticada de notificações com contador de não lidas
- marcação de todas como lidas
- verificação de idioma correto
- validação de configuração SMTP, incluindo bloqueio de TLS e SSL simultâneos
- validação operacional do comando de teste SMTP sem expor segredo nem gravar credencial sensível

## Critérios de aceite

- mensagens são disparadas pelos eventos corretos e no idioma esperado
- usuários logados veem notificações sociais persistidas e podem limpar o contador de não lidas
- staff consegue visualizar e alterar parâmetros SMTP não sensíveis sem expor senha/API key
- staff consegue visualizar e editar templates PT-BR por chave, incluindo variáveis disponíveis e preview HTML local
- operador consegue validar SMTP sandbox com SES usando configuração persistida e segredo vindo do ambiente
- enquanto SES estiver em sandbox, destinatários reais não verificados são suprimidos pelo daemon

## Impacto de mudança

Mudanças podem afetar retenção, operação e experiência percebida, mesmo sem alterar o núcleo do domínio.
