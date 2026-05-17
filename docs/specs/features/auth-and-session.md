---
id: FEAT-AUTH-001
titulo: "Autenticação e sessão"
versao: 0.1
status_spec: draft
status_impl: nao_iniciada
ultima_atualizacao: 2026-05-17
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - i18n-content.md
  - domain-events.md
dependencias: []
impacta:
  - frontend-web
  - backend-api
  - database
  - communications
aprovacao: pendente
---

# Autenticação e sessão

## Objetivo

Permitir cadastro, login, login social, manutenção de sessão e preferência de idioma para acesso às áreas autenticadas.

## Escopo incluído

- cadastro
- login por credencial ou provedor social
- criação e validação de sessão
- logout
- recuperação do contexto do usuário autenticado

## Escopo excluído

- MFA
- SSO corporativo
- gestão avançada de dispositivos

## Fluxo do usuário

Usuário chega à interface pública, cria conta ou faz login, escolhe ou herda idioma preferencial e passa a acessar feed, perfil, wallet e ações autenticadas.

## Comportamento esperado

- sessões inválidas redirecionam para autenticação
- login social cria ou vincula conta de forma rastreável
- idioma preferencial acompanha a sessão

## Regras de domínio

- um usuário deve possuir identidade única no domínio
- cada sessão precisa ser validável e revogável
- login social não pode gerar duplicidade silenciosa de contas

## Responsabilidades por camada

- `frontend-web`: formulários, telas, redirecionamento e mensagens localizadas
- `backend-api`: autenticação, sessão, vínculo de provedor, política de acesso
- `database`: usuário, credenciais externas, sessão e preferências
- `communications`: email de boas-vindas e fluxos transacionais futuros

## Dados e persistência

- usuário
- perfil básico
- provedores externos vinculados
- preferência de idioma
- sessões e rastros de autenticação

## Contratos afetados

- `i18n-content.md`
- `domain-events.md`

## I18n e conteúdo

- mensagens de erro e sucesso precisam existir em `pt-BR` e `en`
- idioma preferencial deve ser persistido

## Observabilidade e operação

- registrar falhas de login e origem de autenticação
- disponibilizar trilha mínima para suporte

## Testes esperados

- unitários para vínculo e validação de sessão
- integração para login social e persistência de preferência de idioma
- fluxo de cadastro, login e logout

## Critérios de aceite

- usuário consegue criar e acessar conta
- sessão inválida é tratada corretamente
- idioma preferencial é respeitado após autenticação

## Impacto de mudança

Mudanças nesta feature costumam afetar todas as experiências autenticadas e parte das comunicações.
