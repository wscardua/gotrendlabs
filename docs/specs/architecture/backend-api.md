# Backend API

## Responsabilidades

- Ser a fonte principal da verdade do domínio.
- Autenticar usuários e emitir/validar sessão.
- Emitir e validar tokens de recuperação de senha de uso único.
- Expor contratos JSON consumidos pelo frontend e pelo admin.
- Centralizar regras de mercado, previsão, stake, wallet, reputação, ranking e resolução.
- Validar reCAPTCHA server-side nos fluxos públicos protegidos quando configurado.
- Emitir eventos de negócio consumidos por `communications` e `scheduler-jobs`.

## Não Responsabilidades

- Renderizar interface final.
- Definir templates de comunicação.
- Manter lógica operacional escondida em painéis de admin.

## Requisitos estruturais

- Todas as mutações relevantes devem ser auditáveis.
- Estados de mercado devem ser explícitos e consistentes.
- Regras de saldo devem usar ledger, não apenas campo de total agregado.
- Erros devem ser previsíveis e mapeados para UX e operação.
- reCAPTCHA v2 é configurável por ambiente; cadastro protegido exige token válido, e sugestão/feedback exigem token apenas para visitante.
- Mudanças de schema que removem colunas consumidas por SQL direto exigem reinício do processo FastAPI em ambientes locais/long-running.
- Comentários são expostos pela FastAPI como fonte de verdade para criação, listagem, reação e moderação.
- Reações de comentário devem ser tratadas como substituição idempotente por usuário/comentário: `like` substitui `dislike` e vice-versa.
- Moderação administrativa de comentário deve registrar evento administrativo e preservar o registro original.
- Resolução administrativa deve persistir opção vencedora, `resolved_at`, `resolution_timezone`, nota/fonte, efeitos de ledger e evento administrativo na mesma transação.
- O ciclo operacional de mercado deve ser centralizado na `MarketLifecycleEngine`; handlers HTTP apenas autenticam/autorizam staff, abrem transação/conexão, chamam a engine e serializam a resposta.
- Fechamento automático pelo daemon deve usar entrada própria da `MarketLifecycleEngine`, separada do fechamento manual, mantendo `market.lock` auditável com ator sistema/nulo.
- `GET /admin/markets/{slug}/resolution-audit` deve expor auditoria staff read-only para mercados `resolved`, agregando previsões, ledger e badges sem mutação e retornando `422` para demais estados.
- Ranking público deve excluir usuários administrativos (`is_staff` e `is_superuser`).
- Ranking global usa reputação persistida; ranking por categoria/subcategoria pode ser calculado em leitura a partir de previsões resolvidas enquanto não houver materialização dedicada.
- Contratos de mercado devem serializar `category_notice`, `subcategory_notice`, `event` e `event_notice` junto de `category` e `subcategory`; criação/edição administrativa valida que o evento ativo pertence à subcategoria selecionada.
- `GET /admin/taxonomy` deve retornar categorias, subcategorias e eventos com estado de bloqueio, contagem de mercados e `notice`.
- Staff pode criar, editar, bloquear e desbloquear eventos por `/admin/categories/{category_slug}/subcategories/{subcategory_slug}/events...`, incluindo `notice` opcional de até 500 caracteres; eventos sem mercados vinculados podem ser removidos por `DELETE /admin/categories/{category_slug}/subcategories/{subcategory_slug}/events/{event_slug}`, enquanto eventos vinculados continuam preservados por bloqueio lógico.
- Bootstrap de núcleo de usuário deve diferenciar usuário comum de operador. Usuário comum recebe perfil, reputação inicial, wallet inicial, badges e atividade pública de cadastro de forma idempotente; `staff`/`superuser` recebe apenas o mínimo operacional necessário para navegar, sem `grant_initial`, reputação pública, badges ou atividade social.
- Catálogo, regra executável e concessão de badges são autoridade do backend; Admin Ops e frontend apenas consomem contratos.
- A `BadgeAwardEngine` deve aplicar recorte `category/subcategory/event` em previsões resolvidas e comentários; sugestões aprovadas só entram em regras por evento quando o fluxo passar a registrar evento.
- `GET /admin/markets` deve suportar ordenações operacionais por popularidade (`views_desc` e `shares_desc`) usando os contadores persistidos do mercado.
- `GET /admin/users` deve suportar busca por email/handle/nome, filtros por status/papel e ordenações operacionais por criação, último login, saldo e reputação.
- `GET /admin/users` deve suportar filtro `bot=yes|no` e retornar `is_bot` apenas em contratos administrativos.
- `GET /admin/users/{user_id}` deve expor detalhe operacional amplo para staff, incluindo perfil privado, wallet, ledger recente, reputação, previsões, comentários, sugestões, feedback, sessões, eventos de auth, eventos administrativos e badges adquiridas.
- Ações staff em `/admin/users/{user_id}` devem cobrir desativação, reativação, revogação de sessões e ajuste manual de wallet, sempre com nota operacional e auditoria.
- `POST /admin/users/{user_id}/roles` deve exigir operador superuser, nota operacional, bloquear autoalteração, tratar `is_superuser` como implicando `is_staff` e registrar `user.roles_update`.
- `POST /admin/users/{user_id}/bot` deve marcar/desmarcar conta controlada por robôs internos, exigir nota operacional, bloquear autoalteração e registrar `user.bot_update`.
- `POST /admin/users/{user_id}/password-reset` deve gerar link de recuperação para conta ativa, exigir nota operacional, bloquear autoalteração, permitir staff apenas para usuários comuns, exigir superuser para alvo staff/superuser e registrar `user.password_reset_request`.
- Ajuste manual de wallet pode ser aplicado à própria conta do operador staff/superuser; as demais autoações sensíveis continuam bloqueadas.
- Recuperação de senha deve expor `POST /auth/password-reset/request` e `POST /auth/password-reset/confirm`, armazenando apenas hash do token, expiração e uso único; confirmação revoga sessões ativas.
- Concessão automática de badge deve ser idempotente e não pode alterar reputação, ranking, wallet ou ledger.
- A `BadgeAwardEngine` é o ponto único para avaliar regras e persistir conquistas em `gotrendlabs_user_badge_awards`; handlers HTTP e ações administrativas devem apenas disparar eventos de domínio.
- Resolução de mercado deve chamar a engine após persistir resultado, reputation delta, streak e ranking derivado dos participantes afetados.
- Prévia de previsão deve ser calculada pelo backend sem efeitos colaterais; criação de previsão, stake, ledger, probabilidades e payout permanecem mutações exclusivas da FastAPI.
- Logs técnicos de troubleshooting devem ser expostos por contratos staff em `/admin/system-logs`, preservando redaction de segredos e sem substituir eventos administrativos de domínio.
- Rotinas temporizadas operacionais, incluindo fechamento automático de mercado, prune de logs e cálculo de status do daemon, devem viver em serviços backend reutilizáveis; comandos/processos externos não duplicam SQL ou regra.
- `GET /admin/dashboard-summary` deve expor resumo agregado para staff com blocos `markets`, `queues`, `users`, `engagement`, `wallet`, `badges`, `system`, `top_markets` e `recent_admin_events`.
- `GET /health` deve permanecer disponível como healthcheck público read-only e pode ser consumido pelo Admin Ops para indicar se a Backend API está online, sem autenticação e sem efeitos colaterais.
- O resumo do Dashboard deve usar somente agregações SQL/contagens e janela fixa de 7 dias para métricas recentes, sem recalcular reputação, payout, probabilidade ou regras de domínio.
- O bloco `system` deve refletir manutenção via JSON runtime, SMTP via `gotrendlabs_site_config` mais segredo em ambiente, reCAPTCHA por ambiente, logs técnicos recentes por severidade e status do daemon por heartbeat recente.
- Status do daemon deve usar `gotrendlabs_site_config.daemon_stale_after_minutes` para `Atrasado` e `gotrendlabs_site_config.daemon_missing_after_minutes` para `Sem sinal`, com defaults `5` e `15` quando a configuração não existir.
- `GET /stats` deve expor métricas públicas de leitura para a home, incluindo mercados abertos, previsões totais, `GT₵` distribuídas e `GT₵` movimentadas, sem efeitos colaterais.
- `distributed_gtl` em `/stats` é agregado a partir de créditos do ledger de wallet de usuários comuns, excluindo `staff` e `superuser`; `moved_gtl` é agregado a partir de stakes de previsões registradas.
- Respostas públicas de moeda podem entregar labels prontos para apresentação com `GT₵`, preservando nomes técnicos `_gtl` nos contratos.
- Agentes IA oficiais são orquestrados por serviços backend reutilizáveis; frontend público apenas exibe comentários, selo e métricas serializadas.
- Prompts seguros de agentes ficam em código backend, personas editáveis ficam em banco e segredos LLM ficam exclusivamente no ambiente.
- Previsões bot oficiais usam o mesmo fluxo de `Prediction`, ledger e probabilidade por pesos, mas são bloqueadas sem participantes humanos e auditadas em `gotrendlabs_ai_agent_actions`.
- Contratos públicos de mercado devem separar métricas humanas, bot e total; `volume_gtl` e `participants` públicos representam humanos.
- Ranking, badges, reputação pública e recompensas devem excluir usuários `is_bot=true`.
