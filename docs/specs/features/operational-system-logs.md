---
id: FEAT-OPSLOG-001
titulo: "Logs técnicos de troubleshooting"
versao: 0.1
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-05-20
origem:
  - solicitação operacional de troubleshooting
contratos_afetados:
  - domain-events.md
dependencias:
  - FEAT-AUTH-001
impacta:
  - backend-api
  - frontend-web
  - database
  - admin-ops
aprovacao: pendente
---

# Logs técnicos de troubleshooting

## Objetivo

Persistir logs técnicos detalhados do sistema para diagnóstico operacional por staff, sem misturar esse histórico com eventos administrativos de domínio.

## Escopo incluído

- captura de requests/responses Django e FastAPI
- captura de exceções com tipo e stack trace
- persistência de registros emitidos pelo `logging` Python/frameworks
- inclusão de logs técnicos de segurança emitidos por frameworks/loggers, além de requests `401`, `403`, demais `4xx` e `5xx`
- `request_id` propagado por header `X-Request-ID`
- mascaramento de segredos antes de persistir contexto
- retenção padrão de 90 dias com comando de limpeza
- consulta administrativa paginada com filtros, identificador amigável de usuário e detalhe completo do log

## Escopo excluído

- pipeline externo de observabilidade
- métricas agregadas de performance em tempo real
- alertas, notificações ou escalonamento automático
- ingestão de logs de infraestrutura fora do processo Python

## Regras

- logs técnicos ficam em `orynth_system_logs`; ações administrativas de domínio continuam em `orynth_admin_events`
- eventos específicos de autenticação continuam também em `orynth_auth_events`; logs técnicos não substituem a trilha de auth
- o Admin Ops consome contratos staff da FastAPI para listar e abrir logs
- tokens, cookies, senhas, CSRF, session keys e chaves secretas nunca devem ser persistidos em claro
- contexto e textos longos devem ser truncados com indicação explícita
- falha ao persistir log não pode quebrar a request principal
- logs associados a usuários devem expor identificador operacional amigável (`@handle`, nome e/ou email) no Admin Ops, sem exigir que o operador saiba o ID numérico
- filtro administrativo de usuário deve aceitar `@handle`, nome, email ou ID e oferecer seleção pesquisável baseada nos usuários cadastrados, incluindo staff e superusers
- listagem administrativa deve ser paginada e não renderizar uma página infinita

## Contratos API

- `GET /admin/system-logs`: lista logs com filtros por texto, nível, origem, logger, evento, método, path, status, identificador de usuário, request id, exceção, período e paginação
- `GET /admin/system-logs/{id}`: retorna detalhe completo do log, incluindo `user_identifier` quando houver usuário associado
- ambos exigem usuário `is_staff=true`

## Critérios de aceite

- request bem-sucedida gera log consultável
- exceção gera log com `exception_type` e `stack_trace`
- handler de `logging` persiste registros sem recursão
- staff lista e abre detalhe no Admin Ops
- usuário comum não acessa endpoints administrativos
- filtros principais retornam registros esperados, incluindo usuário por `@handle`, nome, email ou valor completo selecionado no combo
- listagem permite navegação por páginas e limite por página
- dados sensíveis aparecem mascarados
