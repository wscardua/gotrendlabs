# Contrato: Reputação e Ranking

## Objetivo

Padronizar a forma como o sistema expõe reputação acumulada e ranking social sem acoplar a UX a uma fórmula fixa antes da implementação.

## Campos mínimos

- `user_id`
- `reputation_score`
- `ranking_position`
- `resolved_predictions_count`
- `accuracy_indicator`
- `last_updated_at`

## Endpoint público de ranking

`GET /rankings`

Query params opcionais:

- `category`: slug da categoria.
- `subcategory`: slug da subcategoria; só é aplicado quando `category` também está presente.

Resposta mínima:

- `rows`: lista ordenada de participantes do ranking.
- `categories`: taxonomia disponível para filtros, com `name`, `slug` e `subcategories`.
- `selected_category`: slug de categoria aplicado ou string vazia.
- `selected_subcategory`: slug de subcategoria aplicado ou string vazia.

Campos mínimos de cada linha em `rows`:

- `position`
- `user_id`
- `handle`
- `display_name`
- `reputation_score`
- `accuracy_indicator`
- `strong_category`

## Regras

- A fórmula MVP usa `K=10`, `delta_R = K * (1 - p)` para acertos e `delta_R = -K * p` para erros.
- `p` é `probability_at_entry` convertido para fração decimal.
- Reputação nunca fica negativa.
- Cancelamentos e refunds não alteram reputação.
- A fórmula pode evoluir, mas as mudanças precisam ser registradas em decisão técnica.
- O ranking deve ser explicável o suficiente para suporte e operação.
- O histórico público não pode depender apenas de posição agregada; deve haver lastro em previsões resolvidas.
- O ranking global usa a reputação persistida em `orynth_user_reputations`.
- Ranking filtrado por categoria/subcategoria é uma projeção de leitura recalculada a partir de previsões resolvidas daquele recorte, usando a mesma fórmula MVP.
- Usuários administrativos (`is_staff` ou `is_superuser`) não participam do ranking público.
- Usuários bot (`is_bot=true`) não participam do ranking público global ou temático.
- A UI pública deve exibir o identificador (`handle`) como identificação do usuário no ranking.
- A UI pública deve apresentar o ranking em blocos cumulativos de 10 linhas com `Carregar mais`, preservando filtros de categoria/subcategoria.
- Conteúdo personalizado do quadro "Seu recorte" deve depender de sessão/dados reais; visitantes não devem ver posição estimada ou percentual fictício.

## Contrato de badges

Badges são expostas como catálogo administrável e conquistas do usuário. A regra executável fica no backend e usa apenas `rule_type` controlado.

Conquistas de usuário são persistidas em `orynth_user_badge_awards`. A exibição pública não deve tratar badge conquistada como estado efêmero de tela.

### Shapes mínimos

`BadgeDefinition`:

- `code`
- `name`
- `description`
- `rule_description`
- `badge_type`: `global`, `category`, `performance` ou `engagement`
- `image_url`: imagem padrão/tema claro
- `image_dark_url`: imagem opcional para tema escuro
- `is_active`
- `created_at`
- `updated_at`

`BadgeRule`:

- `badge_code`
- `rule_type`
- `threshold_value`
- `category`
- `subcategory`
- `event`
- `is_active`

`category`, `subcategory` e `event` devem usar valores da taxonomia dinâmica exposta em `GET /admin/taxonomy` quando preenchidos pelo Admin Ops. Subcategoria só é válida junto de sua categoria; evento só é válido junto da subcategoria da mesma categoria. Os `notice` de categoria/subcategoria/evento são metadados de apresentação do mercado e não alteram elegibilidade de badges.

`UserBadgeAward`:

- `user_id`
- `badge_code`
- `awarded_at`
- `reason_snapshot`

### Endpoints públicos

`GET /badges`

- Sem token: lista badges ativas como catálogo público.
- Com token válido: lista badges ativas com estado pessoal do usuário.

Resposta mínima:

- `badges`: lista de badges.

Campos mínimos de cada badge:

- `code`
- `name`
- `description`
- `rule_description`
- `badge_type`
- `image_url`
- `image_dark_url`
- `status`: `earned` ou `locked`
- `earned_at`
- `reason_snapshot`

`GET /users/me/badges`

- Exige sessão válida.
- Antes de responder, o backend pode executar reconciliação leve pela `BadgeAwardEngine` para refletir conquistas recentes.
- Retorna lista de badges ativas com status pessoal.

### Rota web de compartilhamento

`GET /share/badge/{code}/`

- Sem token público, exige usuário autenticado.
- Usa `GET /users/me/badges`/contrato equivalente para validar que a badge pertence ao usuário e está com `status=earned` antes de iniciar o compartilhamento.
- Pode expor URL pública da conquista com token opaco, por exemplo `?t=...`, para permitir leitura por crawlers sociais sem expor id, email ou handle no query string.
- Deve redirecionar para o catálogo de badges quando a badge não existir para o usuário, ainda estiver bloqueada ou o token público for inválido.
- Renderiza imagem clara/escura, nome, descrição, texto mínimo da regra, contexto curto da plataforma e link canônico.
- Expõe metadados Open Graph/Twitter e imagem social ampla para preview em redes.
- A ação de compartilhamento usa links por rede e fallback por cópia somente do link.
- Compartilhar badge não cria `UserBadgeAward`, não altera reputação, ranking, ledger ou wallet.

### Endpoints administrativos

Todos exigem usuário `is_staff=true`:

- `GET /admin/badges`
- `POST /admin/badges`
- `PATCH /admin/badges/{code}`
- `POST /admin/badges/{code}/deactivate`

Payload administrativo mínimo:

- `name`: obrigatório
- `description`: obrigatório
- `badge_type`: obrigatório
- `rule_type`: obrigatório
- `threshold_value`: obrigatório
- `code`: opcional na criação; quando vazio, o backend pode derivar do nome
- `rule_description`: opcional; quando vazio, pode usar a descrição da badge como fallback
- `image_url`: opcional; usada como imagem padrão/tema claro
- `image_dark_url`: opcional; usada quando a interface estiver em tema escuro
- `is_active`: opcional com default ativo no formulário administrativo
- `category`: opcional; vazio significa todas as categorias
- `subcategory`: opcional; vazio significa todas as subcategorias da categoria escolhida ou todas as subcategorias quando categoria também estiver vazia
- `event`: opcional; vazio significa todos os eventos da subcategoria escolhida ou todos os eventos quando categoria/subcategoria também estiverem vazios

O Admin Ops deve marcar visualmente os campos obrigatórios do formulário de badge e manter `code`, `rule_description`, `image_url`, `image_dark_url`, `category`, `subcategory` e `event` sem marcador de obrigatoriedade. A UI pública e o Admin Ops devem usar `image_url` como fallback quando `image_dark_url` não estiver preenchida.

### Regras de concessão MVP

- `founding_member`
- `resolved_predictions_count`
- `correct_predictions_count`
- `streak_count`
- `ranking_position`
- `comments_count`
- `approved_suggestions_count`
- `rewarded_feedback_count`

Concessões são idempotentes por usuário e badge. Badges não alteram reputação, ranking, ledger nem saldo.
Usuários `is_bot=true` não recebem badges, streaks, recompensas ou reputação pública; eventos de comentários e previsões bot são ignorados pela engine de concessão.

### Engine de concessão

`backend-api` deve centralizar concessões na `BadgeAwardEngine`. Endpoints, ações administrativas e fluxos de domínio apenas disparam eventos; eles não calculam regra de badge diretamente.

Eventos MVP:

- `user_registered`: avalia `founding_member`.
- `comment_created`: avalia `comments_count`.
- `suggestion_approved`: avalia `approved_suggestions_count`.
- `suggestion_rewarded`: reavalia `approved_suggestions_count`.
- `feedback_rewarded`: avalia `rewarded_feedback_count`.
- `market_resolved`: avalia participantes com `resolved_predictions_count`, `correct_predictions_count`, `streak_count` e `ranking_position`.

`market_resolved` deve ser disparado após resolução/reputação dos participantes, para que métricas de acerto, sequência e ranking usem o estado final persistido.

Recorte por categoria/subcategoria/evento:

- `resolved_predictions_count`, `correct_predictions_count` e `comments_count` respeitam `category`, `subcategory` e `event` quando preenchidos.
- `approved_suggestions_count` respeita `category` e `subcategory`; regras com `event` preenchido não contam sugestões antigas enquanto o fluxo de sugestão não capturar evento.
- Campos vazios significam regra global para todas as categorias.
- O recorte por evento só deve ser aplicado quando a regra também possuir categoria e subcategoria preenchidas.
- `ranking_position`, `streak_count`, `founding_member` e `rewarded_feedback_count` são globais nesta fatia MVP.
