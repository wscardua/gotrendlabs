# Status de Implementação

| Feature | Status spec | Status impl | Última atualização | Observação |
|---|---|---|---|---|
| FEAT-AUTH-001 | draft | parcial | 2026-05-19 | FastAPI auth/session com aceite de política, política pública/modal no cadastro, reCAPTCHA v2 opcional no cadastro, navegação pública e retorno `← Feed` em auth, edição inline de perfil com dados privados opcionais, exclusão lógica e gestão administrativa de usuários/sessões/badges adquiridas; Django consome a API |
| FEAT-MARKET-001 | draft | parcial | 2026-05-19 | Feed público vem da FastAPI/Postgres, com cards, mini gráficos, destaque editorial/fallback por curtidas, ticket de onboarding do cadastro por curtidas/data, fallback visual de thumbnail, ordenações rápidas client-side, recorte de resolvidos, métrica de previsões totais reais e contadores operacionais de popularidade para Admin Ops |
| FEAT-MARKET-002 | draft | parcial | 2026-05-19 | Detalhe público vem da FastAPI/Postgres com opções, consenso decimal, evolução por opção preservada após resolução, ticket de resultado personalizado, compartilhamento social de pergunta/resultado e tracking operacional de visualização/compartilhamento |
| FEAT-PRED-001 | draft | parcial | 2026-05-19 | Previsão autenticada com stake, bloqueio de saldo, ledger, snapshot decimal de probabilidade, uma previsão por usuário/mercado, prévia sem efeito colateral via FastAPI e séries visuais derivadas de `orynth_predictions`; fallback local mutável removido |
| FEAT-RES-001 | draft | parcial | 2026-05-19 | Resolução manual com opção vencedora, timestamp/timezone controlados, payout/reputação pela fórmula MVP, perda auditável, cancelamento com refund total, validação contra previsões abertas órfãs, reconciliação operacional idempotente e desfazer resolução para fechado |
| FEAT-REP-001 | draft | parcial | 2026-05-19 | Reputação base, ranking global/temático via FastAPI, exclusão de admins no backend, atualização por resolução usando `K=10`, badges administráveis com concessão automática e compartilhamento social por card/metadados |
| FEAT-WALLET-001 | draft | parcial | 2026-05-19 | Ledger auditável, projeção `orynth_wallet_balances`, grant inicial, stake lock, refund idempotente por cancelamento/reconciliação, payout, perda por resolução, extrato, recompensas operacionais e ajuste manual auditado por staff |
| FEAT-COMMENT-001 | draft | parcial | 2026-05-18 | Comentários reais em mercados com criação autenticada, listagem pública, like/dislike único por usuário e moderação staff por ocultar/restaurar |
| FEAT-SUGGEST-001 | draft | parcial | 2026-05-19 | Sugestões de mercado e feedback possuem persistência, envio autenticado/guest com reCAPTCHA v2 opcional para visitantes, fila real no Admin Ops, conversão em rascunho e crédito operacional idempotente; Admin Ops não executa fallback local mutável |
| FEAT-NOTIFY-001 | draft | nao_iniciada | 2026-05-17 | Estrutura documental criada |
| FEAT-I18N-001 | draft | nao_iniciada | 2026-05-17 | Estrutura documental criada |

## Regras de atualização

- Alterações relevantes em uma feature devem atualizar também `feature-changelog.md`.
- Quando o comportamento mudar sem implementação equivalente, marcar `status_impl` como `defasada_pela_spec`.
