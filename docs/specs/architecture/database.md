# Database

## Responsabilidades

- Persistir usuários, perfis, mercados, opções, previsões, ledger da wallet, comentários, sugestões, decisões de moderação e histórico operacional.
- Garantir integridade relacional e rastreabilidade temporal.
- Suportar consultas transacionais e relatórios administrativos.

## Diretrizes

- Modelos críticos devem preservar histórico quando o produto exigir auditabilidade.
- Wallet deve usar razão de transações (`ledger`) em vez de depender apenas de saldo derivado.
- Resolução de mercado deve registrar origem, operador, evidência, data efetiva e timezone usado para apresentação/auditoria.
- Sempre que possível, usar identificadores estáveis independentes de textos traduzidos.
- Categorias e subcategorias de mercado devem usar bloqueio lógico (`is_blocked`, motivo e data) em vez de exclusão física operacional.
- Mercados existentes devem manter vínculo com taxonomia bloqueada para preservar histórico e auditoria.
- Probabilidades de mercado/opção devem preservar precisão decimal (`*_probability_exact`/`probability_exact`); inteiros de exibição são derivados na serialização/UI, não persistidos.
- Métricas operacionais simples de popularidade de mercado ficam denormalizadas em `orynth_markets.view_count` e `orynth_markets.share_count` para leitura rápida no Admin Ops; nesta etapa cada evento incrementa o contador sem deduplicação.
- Comentários de mercado são preservados em `orynth_market_comments` com status `visible`/`hidden`, nota de moderação, moderador e timestamps.
- Reações de comentário ficam em `orynth_comment_reactions`, com uma reação ativa por usuário/comentário e valores `like` ou `dislike`.
- Ocultação de comentário é lógica; não há exclusão física operacional nesta fatia.
- Gestão administrativa de usuários reutiliza `orynth_users`, `orynth_user_profiles`, `orynth_auth_sessions`, `orynth_auth_events`, `orynth_wallet_ledger`, `orynth_wallet_balances` e `orynth_user_badge_awards` para suporte sem criar nova tabela.
- Ações administrativas de usuário devem registrar `user.deactivate`, `user.reactivate`, `user.sessions_revoke` ou `user.wallet_adjust` em `orynth_admin_events`.
- Ajuste manual de wallet deve ser persistido em `orynth_wallet_ledger` como `manual_adjustment` e atualizar `orynth_wallet_balances` na mesma transação.

## Não Responsabilidades

- Aplicar regra de negócio isoladamente.
- Calcular reputação ou probabilidades fora do backend.
