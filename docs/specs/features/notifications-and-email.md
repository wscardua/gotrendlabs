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

- email de boas-vindas
- confirmação de previsão
- aviso de mercado resolvido
- comunicações de feedback/sugestão quando definido
- configuração operacional SMTP não sensível no Admin Ops

## Escopo excluído

- automação de marketing complexa
- push mobile
- armazenamento de senha/API key SMTP no banco ou na interface administrativa

## Fluxo do usuário

Usuário recebe mensagens coerentes com ações relevantes ou estados importantes do produto.

## Comportamento esperado

- eventos de domínio disparam comunicações elegíveis
- idioma respeita preferência do usuário

## Regras de domínio

- comunicações dependem de eventos confiáveis
- preferências do usuário e regras operacionais precisam ser respeitadas

## Responsabilidades por camada

- `backend-api`: emitir eventos e contexto
- `communications`: selecionar template, idioma e registrar entrega
- `database`: trilha de envio quando necessário

## Dados e persistência

- eventos consumidos
- templates
- trilha de envio
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
- verificação de idioma correto
- validação de configuração SMTP, incluindo bloqueio de TLS e SSL simultâneos

## Critérios de aceite

- mensagens são disparadas pelos eventos corretos e no idioma esperado
- staff consegue visualizar e alterar parâmetros SMTP não sensíveis sem expor senha/API key

## Impacto de mudança

Mudanças podem afetar retenção, operação e experiência percebida, mesmo sem alterar o núcleo do domínio.
