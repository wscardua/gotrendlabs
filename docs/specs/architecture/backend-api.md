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
- `GET /admin/markets/{slug}/resolution-audit` deve expor auditoria staff read-only para mercados `resolved`, agregando previsões, ledger e badges sem mutação e retornando `422` para demais estados.
- Ranking público deve excluir usuários administrativos (`is_staff` e `is_superuser`).
- Ranking global usa reputação persistida; ranking por categoria/subcategoria pode ser calculado em leitura a partir de previsões resolvidas enquanto não houver materialização dedicada.
- Catálogo, regra executável e concessão de badges são autoridade do backend; Admin Ops e frontend apenas consomem contratos.
- `GET /admin/markets` deve suportar ordenações operacionais por popularidade (`views_desc` e `shares_desc`) usando os contadores persistidos do mercado.
- `GET /admin/users` deve suportar busca por email/handle/nome, filtros por status/papel e ordenações operacionais por criação, último login, saldo e reputação.
- `GET /admin/users/{user_id}` deve expor detalhe operacional amplo para staff, incluindo perfil privado, wallet, ledger recente, reputação, previsões, comentários, sugestões, feedback, sessões, eventos de auth, eventos administrativos e badges adquiridas.
- Ações staff em `/admin/users/{user_id}` devem cobrir desativação, reativação, revogação de sessões e ajuste manual de wallet, sempre com nota operacional e auditoria.
- `POST /admin/users/{user_id}/roles` deve exigir operador superuser, nota operacional, bloquear autoalteração, tratar `is_superuser` como implicando `is_staff` e registrar `user.roles_update`.
- Recuperação de senha deve expor `POST /auth/password-reset/request` e `POST /auth/password-reset/confirm`, armazenando apenas hash do token, expiração e uso único; confirmação revoga sessões ativas.
- Concessão automática de badge deve ser idempotente e não pode alterar reputação, ranking, wallet ou ledger.
- A `BadgeAwardEngine` é o ponto único para avaliar regras e persistir conquistas em `orynth_user_badge_awards`; handlers HTTP e ações administrativas devem apenas disparar eventos de domínio.
- Resolução de mercado deve chamar a engine após persistir resultado, reputation delta, streak e ranking derivado dos participantes afetados.
- Prévia de previsão deve ser calculada pelo backend sem efeitos colaterais; criação de previsão, stake, ledger, probabilidades e payout permanecem mutações exclusivas da FastAPI.
- Logs técnicos de troubleshooting devem ser expostos por contratos staff em `/admin/system-logs`, preservando redaction de segredos e sem substituir eventos administrativos de domínio.
- `GET /admin/dashboard-summary` deve expor resumo agregado para staff com blocos `markets`, `queues`, `users`, `engagement`, `wallet`, `badges`, `system`, `top_markets` e `recent_admin_events`.
- O resumo do Dashboard deve usar somente agregações SQL/contagens e janela fixa de 7 dias para métricas recentes, sem recalcular reputação, payout, probabilidade ou regras de domínio.
- O bloco `system` deve refletir manutenção via JSON runtime, SMTP via `orynth_site_config` mais segredo em ambiente, reCAPTCHA por ambiente e logs técnicos recentes por severidade.
