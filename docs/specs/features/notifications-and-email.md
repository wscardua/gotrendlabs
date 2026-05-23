---
id: FEAT-NOTIFY-001
titulo: "Notificações e email"
versao: 0.1
status_spec: draft
status_impl: nao_iniciada
ultima_atualizacao: 2026-05-17
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
- email de boas-vindas
- confirmação de previsão
- aviso de mercado resolvido
- comunicações de feedback/sugestão quando definido
- configuração operacional SMTP não sensível no Admin Ops

## Escopo excluído

- automação de marketing complexa
- push mobile
- armazenamento de senha/API key SMTP no banco ou na interface administrativa
- feed em tempo real/websocket de notificações

## Fluxo do usuário

Usuário recebe mensagens coerentes com ações relevantes ou estados importantes do produto.

Usuário autenticado vê um sino de notificações no topo com contador de não lidas e últimas interações sociais relacionadas a mercados em que registrou previsão.

## Comportamento esperado

- eventos de domínio disparam comunicações elegíveis
- ações sociais geram notificações in-app sem duplicidade por evento de origem
- créditos recebidos, badges conquistadas e mudanças relevantes em mercados participados geram notificações in-app
- usuários podem marcar todas as notificações in-app como lidas
- idioma respeita preferência do usuário

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

## Responsabilidades por camada

- `backend-api`: emitir eventos e contexto
- `communications`: selecionar template, idioma e registrar entrega
- `database`: trilha de envio quando necessário e inbox persistida de notificações in-app
- `frontend-web`: sino, contador de não lidas, dropdown de últimas notificações e ação de marcar lidas

## Dados e persistência

- eventos consumidos
- templates
- trilha de envio
- `orynth_user_notifications`: destinatário, ator, mercado, comentário, tipo, chave de origem, título, corpo, estado de leitura, metadata e data
- configuração SMTP singleton: ativo, host, porta, usuário, TLS/SSL, timeout, remetente e reply-to

## Contratos afetados

- `domain-events.md`
- `i18n-content.md`

## I18n e conteúdo

- templates precisam existir pelo menos em `pt-BR` e `en`

## Observabilidade e operação

- taxa de entrega, falha e reenvio
- parâmetros SMTP são administráveis por staff; segredo de envio vem de variável de ambiente/secret manager

## Testes esperados

- integração de evento para envio
- criação idempotente de notificações in-app para previsão, curtida de mercado, comentário, curtida de comentário, crédito recebido, fechamento/resolução de mercado e badge recebida
- listagem autenticada de notificações com contador de não lidas
- marcação de todas como lidas
- verificação de idioma correto
- validação de configuração SMTP, incluindo bloqueio de TLS e SSL simultâneos

## Critérios de aceite

- mensagens são disparadas pelos eventos corretos e no idioma esperado
- usuários logados veem notificações sociais persistidas e podem limpar o contador de não lidas
- staff consegue visualizar e alterar parâmetros SMTP não sensíveis sem expor senha/API key

## Impacto de mudança

Mudanças podem afetar retenção, operação e experiência percebida, mesmo sem alterar o núcleo do domínio.
