# Acesso A Dados Internos

Consulte dados internos antes de usar redes sociais. A GoTrendLabs ja possui historico de mercados e metricas que devem orientar ranking, diversidade e anti-repeticao.

## Fontes Internas

Modelos/tabelas relevantes:

- `apps.web.django.markets.models.Market` / `gotrendlabs_markets`
- `apps.web.django.markets.models.MarketOption` / `gotrendlabs_market_options`
- `apps.web.django.markets.models.Prediction` / `gotrendlabs_predictions`
- `apps.web.django.markets.models.MarketLike` / `gotrendlabs_market_likes`
- `apps.web.django.markets.models.MarketFavorite` / `gotrendlabs_market_favorites`
- `apps.web.django.markets.models.MarketComment` / `gotrendlabs_market_comments`
- `apps.web.django.markets.models.MarketCategory` / `gotrendlabs_market_categories`
- `apps.web.django.markets.models.MarketSubcategory` / `gotrendlabs_market_subcategories`
- `apps.web.django.markets.models.MarketSuggestion` / `gotrendlabs_market_suggestions`

Endpoints/clientes relevantes:

- `GET /markets`
- `GET /admin/markets`
- `GET /admin/dashboard-summary`
- `apps.web.django.accounts.api_client.get_markets`
- `apps.web.django.accounts.api_client.admin_get_markets`
- `apps.web.django.accounts.api_client.admin_get_dashboard_summary`

Specs relevantes:

- `docs/specs/features/market-suggestions.md`
- `docs/specs/architecture/backend-api.md`
- `docs/specs/architecture/database.md`
- `docs/specs/spec_prediction_social_market_pt.md`

## Consultas Recomendadas

Use ORM Django read-only quando estiver no repo local e o banco estiver acessivel.

Exemplo de leitura de performance:

```bash
.venv/bin/python manage.py shell -c 'from django.db.models import Count, Sum; from apps.web.django.markets.models import Market, MarketCategory; qs=Market.objects.annotate(likes_count=Count("likes", distinct=True), favorites_count=Count("favorites", distinct=True), comments_count=Count("comments", distinct=True), predictions_count=Count("predictions", distinct=True)).order_by("-view_count","-likes_count","-predictions_count")[:20]; [print(m.slug, m.status, m.kind, m.category.slug if m.category_id else "", m.title, m.view_count, m.share_count, m.likes_count, m.favorites_count, m.comments_count, m.predictions_count) for m in qs]'
```

Exemplo de equilibrio por categoria:

```bash
.venv/bin/python manage.py shell -c 'from django.db.models import Count, Sum; from apps.web.django.markets.models import MarketCategory; qs=MarketCategory.objects.annotate(markets_count=Count("markets"), views=Sum("markets__view_count"), predictions=Count("markets__predictions", distinct=True), likes=Count("markets__likes", distinct=True)).order_by("-views","name"); [print(c.slug, c.markets_count, c.views or 0, c.predictions, c.likes) for c in qs]'
```

## Como Usar Os Dados

Priorize sinais internos:

- mercados mais visualizados
- mercados mais curtidos
- mercados mais compartilhados
- mercados com mais previsoes
- mercados com mais comentarios
- categorias com maior volume
- categorias subexploradas
- formatos com melhor participacao

Ao gerar novas sugestoes:

- aproveite categorias fortes, mas limite saturacao
- inclua categorias subexploradas quando houver trend externa verificavel
- compare contra titulos, slugs, categorias, pessoas, franquias e eventos ja existentes
- nunca repita uma tese apenas trocando prazo ou palavras
- use dados internos como "sinal interno usado" em cada sugestao

## Fallback

Se API admin ou login admin nao estiverem disponiveis, use ORM local read-only.

Se ORM/banco tambem nao estiver disponivel, explique a limitacao e use somente fontes publicas com links exatos.
