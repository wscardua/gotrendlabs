# Database

## Responsabilidades

- Persistir usuários, perfis, mercados, opções, previsões, ledger da wallet, comentários, notificações in-app, sugestões, decisões de moderação e histórico operacional.
- Garantir integridade relacional e rastreabilidade temporal.
- Suportar consultas transacionais e relatórios administrativos.

## Diretrizes

- Modelos críticos devem preservar histórico quando o produto exigir auditabilidade.
- Wallet deve usar razão de transações (`ledger`) em vez de depender apenas de saldo derivado.
- Resolução de mercado deve registrar origem, operador, evidência, data efetiva e timezone usado para apresentação/auditoria.
- Sempre que possível, usar identificadores estáveis independentes de textos traduzidos.
- Categorias, subcategorias e eventos vinculados a mercados devem usar bloqueio lógico (`is_blocked`, motivo e data) em vez de exclusão física operacional; eventos sem mercados vinculados podem ser excluídos para limpeza de cadastros criados por engano.
- Eventos ficam em `gotrendlabs_market_events`, pertencem a uma subcategoria e formam a terceira camada da taxonomia `categoria -> subcategoria -> evento`.
- `gotrendlabs_market_categories.notice`, `gotrendlabs_market_subcategories.notice` e `gotrendlabs_market_events.notice` guardam avisos opcionais, vazios por padrão, para exibição contextual no detalhe/ticket de mercados sensíveis vinculados.
- `gotrendlabs_markets.event_id` referencia `gotrendlabs_market_events`; mercados migrados sem evento explícito devem apontar para o evento ativo `Geral` da subcategoria.
- Mercados existentes devem manter vínculo com taxonomia bloqueada para preservar histórico e auditoria.
- Probabilidades de mercado/opção devem preservar precisão decimal (`*_probability_exact`/`probability_exact`); inteiros de exibição são derivados na serialização/UI, não persistidos.
- Métricas operacionais simples de popularidade de mercado ficam denormalizadas em `gotrendlabs_markets.view_count` e `gotrendlabs_markets.share_count` para leitura rápida no Admin Ops; nesta etapa cada evento incrementa o contador sem deduplicação.
- Comentários de mercado são preservados em `gotrendlabs_market_comments` com status `visible`/`hidden`, nota de moderação, moderador e timestamps.
- Reações de comentário ficam em `gotrendlabs_comment_reactions`, com uma reação ativa por usuário/comentário e valores `like` ou `dislike`.
- Ocultação de comentário é lógica; não há exclusão física operacional nesta fatia.
- Gestão administrativa de usuários reutiliza `gotrendlabs_users`, `gotrendlabs_user_profiles`, `gotrendlabs_auth_sessions`, `gotrendlabs_auth_events`, `gotrendlabs_wallet_ledger`, `gotrendlabs_wallet_balances` e `gotrendlabs_user_badge_awards` para suporte sem criar nova tabela.
- Ações administrativas de usuário devem registrar `user.deactivate`, `user.reactivate`, `user.sessions_revoke` ou `user.wallet_adjust` em `gotrendlabs_admin_events`.
- Ajuste manual de wallet deve ser persistido em `gotrendlabs_wallet_ledger` como `manual_adjustment` e atualizar `gotrendlabs_wallet_balances` na mesma transação.
- Logs técnicos de troubleshooting ficam em `gotrendlabs_system_logs`, com `expires_at`, purge por `created_at` conforme retenção configurável, índices de consulta operacional e contexto JSON redigido/truncado.
- Parâmetros operacionais persistentes ficam em `gotrendlabs_site_config`, uma configuração singleton expansível para novos ajustes do site; nesta fatia inclui SMTP não sensível e retenção de logs/auditoria IA, com host, porta, usuário, TLS/SSL, timeout, remetente, reply-to, operador e timestamp de alteração.
- Senhas, API keys e segredos SMTP não são persistidos no banco.
- Configuração operacional de agentes IA fica em `gotrendlabs_site_config`; o segredo do provedor LLM permanece fora do banco (`OPENAI_API_KEY` para OpenAI ou `AWS_BEARER_TOKEN_BEDROCK` para Bedrock).
- `gotrendlabs_ai_agents` liga um agente oficial a um usuário `is_bot=true` e guarda persona/estilo editáveis sem substituir o template seguro de código.
- `gotrendlabs_ai_agent_actions` guarda auditoria de ações IA com status, motivo, payload resumido, referência a mercado/comentário/previsão e hash/versão do prompt; o purge operacional remove ações mais antigas que `gotrendlabs_site_config.ai_audit_retention_days`.
- Métricas públicas devem conseguir distinguir participantes/volume humanos e bots; rótulos legados preservam leitura humana.
- Notificações in-app ficam em `gotrendlabs_user_notifications`, com destinatário obrigatório, ator/mercado/comentário opcionais, `event_type`, `source_key`, título, corpo, `metadata`, estado de leitura e constraint única por `(recipient_id, source_key)`.
- `source_key` deve representar a origem idempotente do evento por destinatário, permitindo uma notificação por usuário afetado sem duplicar ações repetidas.

## Não Responsabilidades

- Aplicar regra de negócio isoladamente.
- Calcular reputação ou probabilidades fora do backend.
