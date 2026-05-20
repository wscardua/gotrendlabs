# Fontes Sociais E Verificacao

Toda sugestao precisa ter link exato de verificacao. Nao use apenas o nome da plataforma.

Ruim:

- Fonte: YouTube
- Fonte: TikTok
- Fonte: SteamDB

Bom:

- Link exato: `https://www.youtube.com/@RockstarGames/videos`
- Link exato: `https://ads.tiktok.com/business/creativecenter/`
- Link exato: `https://api.x.com/2/tweets/counts/recent`
- Link exato: `https://steamdb.info/charts/`

## Matriz De Fontes

### YouTube

Uso: trends e resolucao.

Confiabilidade: alta para publicacao de videos, views, likes e comentarios publicos.

Links uteis:

- Canal: `https://www.youtube.com/@RockstarGames/videos`
- Canal: `https://www.youtube.com/@NintendoAmerica/videos`
- Canal: `https://www.youtube.com/@NASA/videos`
- Video especifico: `https://www.youtube.com/watch?v=<video_id>`
- API: `https://www.googleapis.com/youtube/v3/videos`
- Docs: `https://developers.google.com/youtube/v3/docs/videos`

Regras:

- Preferir canais oficiais.
- Usar video/canal oficial, nao reupload ou corte de fa.
- Para contagem de views, definir janela: 24h, 48h, 72h, 7 dias.
- Para API, procurar `YOUTUBE_API_KEY`.

### TikTok

Uso: trends; resolucao apenas com link direto ou Creative Center acessivel.

Confiabilidade: media.

Links uteis:

- Creative Center: `https://ads.tiktok.com/business/creativecenter/`
- Ajuda oficial: `https://ads.us.tiktok.com/help/article/how-to-use-trends?lang=en`
- Video/perfil direto quando disponivel: `https://www.tiktok.com/@<handle>/video/<id>`

Regras:

- Usar como fonte final somente se houver link direto, ranking visivel ou acesso autenticado.
- Sem link exato, usar apenas como sinal de tendencia.
- Registrar se a checagem exige login/manual.

### X

Uso: trends; resolucao por volume de posts quando API estiver disponivel.

Confiabilidade: alta com API/token; media via web.

Links uteis:

- API recent counts: `https://api.x.com/2/tweets/counts/recent`
- Docs: `https://docs.x.com/x-api/posts/get-count-of-recent-posts`
- Busca web: `https://x.com/search?q=<query>&src=typed_query&f=live`

Regras:

- Procurar `X_BEARER_TOKEN`.
- Definir query exata no mercado.
- Definir janela de busca e timezone.
- Sem token, usar X apenas como apoio, salvo se houver post/link especifico.

### Facebook E Instagram

Uso: trends e apoio; resolucao apenas com Meta Content Library/API, Graph API ou links publicos exatos.

Confiabilidade: media com API; baixa como fonte final sem acesso.

Links uteis:

- Meta Content Library: `https://transparency.fb.com/researchtools/meta-content-library`
- Info Meta: `https://about.fb.com/br/news/2023/11/novas-ferramentas-para-apoiar-pesquisas-independentes/`
- Post publico direto quando disponivel.

Regras:

- Procurar `META_ACCESS_TOKEN`, `FACEBOOK_ACCESS_TOKEN` ou `INSTAGRAM_ACCESS_TOKEN`.
- Se acesso nao estiver disponivel, nao usar como juiz final sem link direto conferivel.
- Evitar vida privada sensivel; usar apenas conteudo publico e verificavel.

### Reddit

Uso: trends e resolucao.

Confiabilidade: alta para posts publicos, subreddits e rankings `top`.

Links uteis:

- API/docs: `https://www.reddit.com/dev/api/`
- Games: `https://www.reddit.com/r/Games/top/?t=week`
- Gaming: `https://www.reddit.com/r/gaming/top/?t=week`
- Television: `https://www.reddit.com/r/television/top/?t=week`
- Movies: `https://www.reddit.com/r/movies/top/?t=week`

Regras:

- Usar subreddit e janela exata (`hour`, `day`, `week`, `month`, `year`, `all`).
- Preferir `top` para resolucao objetiva.
- Registrar criterio: posicao, upvotes, comentarios ou presenca no top N.

### Twitch

Uso: games e influencers ao vivo.

Confiabilidade: alta com API/token.

Links uteis:

- API streams: `https://api.twitch.tv/helix/streams`
- Docs: `https://dev.twitch.tv/docs/api/reference/#get-streams`
- Categoria web: `https://www.twitch.tv/directory/category/<slug>`

Regras:

- Procurar `TWITCH_CLIENT_ID` e `TWITCH_CLIENT_SECRET`.
- Definir horario exato da checagem.
- Usar `viewer_count` e `game_name` como criterio quando via API.

### Google Trends

Uso: sinal amplo de interesse; resolucao secundaria.

Confiabilidade: media para resolucao, alta para inspiracao.

Links uteis:

- Trending now: `https://trends.google.com/trends/?geo=US`

Regras:

- Usar como apoio quando redes sociais estiverem ruidosas.
- Evitar ser a unica fonte final se houver alternativa mais objetiva.

### SteamDB E Steam Charts

Uso: games e rankings objetivos.

Confiabilidade: alta.

Links uteis:

- SteamDB charts: `https://steamdb.info/charts/`
- Steam Charts: `https://steamcharts.com/top`
- Steam official charts: `https://store.steampowered.com/charts/mostplayed`

Regras:

- Definir horario de checagem.
- Usar posicao no ranking, jogadores atuais ou pico de 24h.
- Registrar fallback entre SteamDB, Steam Charts e ranking oficial Steam.

## Regra Dura

Fonte social sem link exato, endpoint exato ou credencial disponivel pode inspirar mercado, mas nao pode ser fonte final de resolucao.
