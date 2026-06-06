---
id: FEAT-OPSLOG-001
titulo: "Logs técnicos de troubleshooting"
versao: 0.1
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-05-24
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
- retenção padrão de 90 dias configurável no Admin Ops
- limpeza de logs expirada centralizada em serviço backend reutilizável, consumido pelo daemon e pelo comando operacional
- heartbeat e resultado de ciclos do daemon operacional para troubleshooting
- indicador de disponibilidade da Backend API no Dashboard Admin Ops a partir de `GET /health`
- consulta administrativa paginada com filtros, identificador amigável de usuário e detalhe completo do log

## Escopo excluído

- pipeline externo de observabilidade
- métricas agregadas de performance em tempo real
- alertas, notificações ou escalonamento automático
- ingestão de logs de infraestrutura fora do processo Python

## Regras

- logs técnicos ficam em `gotrendlabs_system_logs`; ações administrativas de domínio continuam em `gotrendlabs_admin_events`
- eventos específicos de autenticação continuam também em `gotrendlabs_auth_events`; logs técnicos não substituem a trilha de auth
- o Admin Ops consome contratos staff da FastAPI para listar e abrir logs
- tokens, cookies, senhas, CSRF, session keys e chaves secretas nunca devem ser persistidos em claro
- contexto e textos longos devem ser truncados com indicação explícita
- falha ao persistir log não pode quebrar a request principal
- logs do daemon usam `logger_name=gotrendlabs.daemon` e eventos como `daemon.heartbeat`, `daemon.run_started`, `daemon.markets_locked`, `daemon.logs_pruned` e `daemon.run_failed`
- ausência ou atraso de heartbeat deve aparecer no Dashboard Admin Ops como status operacional do daemon
- status do daemon usa limites configuráveis em `gotrendlabs_site_config`: `daemon_stale_after_minutes` e `daemon_missing_after_minutes`, com defaults de 7 e 21 minutos para a cadência de produção de 300 segundos
- retenção de logs técnicos usa `gotrendlabs_site_config.system_log_retention_days`, default 90 dias, e o purge aplica o prazo atual por `created_at` também a registros antigos
- logs associados a usuários devem expor identificador operacional amigável (`@handle`, nome e/ou email) no Admin Ops, sem exigir que o operador saiba o ID numérico
- filtro administrativo de usuário deve aceitar `@handle`, nome, email ou ID e oferecer seleção pesquisável baseada nos usuários cadastrados, incluindo staff e superusers
- listagem administrativa usa `Carregar mais` em blocos cumulativos de 10 registros e não renderiza uma página infinita

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
- listagem permite carregar mais registros em blocos de 10 preservando filtros
- dados sensíveis aparecem mascarados
- comando de prune e daemon usam a mesma rotina backend de retenção, sem duplicar regra em camada Django, limpando logs técnicos e auditoria IA juntos
- Admin Ops Config permite ajustar os limites de heartbeat do daemon, validando que `Sem sinal` seja maior que `Atrasado`
- Admin Ops Config permite ajustar a retenção de logs técnicos e auditoria IA, com valores separados de 1 a 3650 dias
- Dashboard Admin Ops exibe `Backend API` como online quando `GET /health` retorna `status=ok` e offline quando a consulta falha ou retorna payload inesperado
