# Fontes Sociais E Verificacao

Toda sugestao precisa ter link exato de verificacao. Nao use apenas o nome da plataforma.

Ruim:

- Fonte: YouTube
- Fonte: TikTok
- Fonte: SteamDB
- Fonte: CoinGecko

Bom:

- Link exato: `https://www.youtube.com/@RockstarGames/videos`
- Link exato: `https://ads.tiktok.com/business/creativecenter/`
- Link exato: `https://api.x.com/2/tweets/counts/recent`
- Link exato: `https://steamdb.info/charts/`
- Link exato: `https://www.coingecko.com/en/coins/bitcoin`
- Link exato: `https://defillama.com/chains`

## Validacao Obrigatoria Da Fonte

Antes de aceitar uma fonte como fonte final de resolucao, confirme que ela consegue fundamentar e certificar o resultado.

Pode usar:

- navegador local do usuario, quando precisar de sessao, cookies, login, regiao ou interface visual
- browser automation, quando precisar abrir pagina, navegar, pesquisar, clicar, capturar tela ou conferir rankings visiveis
- APIs oficiais, quando houver token, chave ou endpoint publico
- web search, quando precisar confirmar que uma pagina oficial existe ou que o link mudou
- banco, ORM ou APIs internas da GoTrendLabs, quando a resolucao depender de dados internos

Checklist de validacao:

1. O link exato abre ou o endpoint responde?
2. A pagina/API mostra o dado necessario para resolver o mercado?
3. O dado e objetivo: data, ranking, view count, like count, post count, publicacao oficial, score, status ou resultado?
4. A fonte e primaria ou confiavel o bastante para certificar a resolucao?
5. A checagem tem data, horario e timezone definidos?
6. Existe fallback verificavel se a fonte principal ficar indisponivel?

Se qualquer resposta essencial for "nao", a fonte nao pode ser usada como juiz final. Use-a apenas como inspiracao ou substitua por fonte mais forte.

Classifique a fonte em cada sugestao:

- `validada`: link/API conferido e dado resolutivo disponivel
- `validavel`: fonte conhecida e objetiva, mas exige checagem futura no prazo de resolucao
- `condicional`: depende de login, token, geografia ou disponibilidade; precisa fallback
- `invalida`: nao usar como fonte final

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
- Validar que o canal/video mostra data de publicacao ou estatistica necessaria para resolver.

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
- Se depender de Creative Center, validar acesso pelo navegador antes de usar como fonte final.

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
- Para contagem de posts, registrar query, endpoint e parametros usados na API.

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
- Se a pagina exigir login e nao houver acesso autorizado, classificar como `condicional` ou `invalida`.

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
- Conferir se o subreddit e publico e se a URL de ranking abre sem contexto privado.

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
- Sem token/API, usar pagina web apenas se o ranking visivel for suficiente e validado no navegador.

### Google Trends

Uso: sinal amplo de interesse; resolucao secundaria.

Confiabilidade: media para resolucao, alta para inspiracao.

Links uteis:

- Trending now: `https://trends.google.com/trends/?geo=US`

Regras:

- Usar como apoio quando redes sociais estiverem ruidosas.
- Evitar ser a unica fonte final se houver alternativa mais objetiva.
- Se usado como fonte final, registrar regiao, termo, janela e metodologia de comparacao.

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
- Validar que o ranking escolhido exibe a metrica usada no criterio.

### Cripto E On-Chain

Uso: cripto, redes blockchain, tokens, rankings, precos, TVL, transacoes, status de rede e releases oficiais.

Confiabilidade: alta quando a fonte e publica, objetiva e historicamente conferivel; media quando depende de UI temporaria, API sem snapshot ou anuncio de terceiro.

Links uteis:

- CoinGecko Bitcoin: `https://www.coingecko.com/en/coins/bitcoin`
- CoinMarketCap Bitcoin: `https://coinmarketcap.com/currencies/bitcoin/`
- DefiLlama chains: `https://defillama.com/chains`
- Etherscan charts: `https://etherscan.io/charts`
- Solscan analytics: `https://solscan.io/analytics`
- GitHub releases: `https://github.com/<org>/<repo>/releases`
- Status pages oficiais quando existirem.

Regras:

- Incluir sempre: `Aviso de risco: Nao caracteriza recomendacao de investimento.`
- Formular mercados como eventos verificaveis, nao como conselho financeiro.
- Usar preco, ranking, TVL, volume, transacoes, bloco, status, listagem oficial, release ou anuncio oficial como dado resolutivo.
- Definir moeda, unidade, data, horario, timezone e fonte exata.
- Para preco, definir se a fonte usa valor spot, fechamento, media ou valor exibido no momento da checagem.
- Para listagens, usar pagina/anuncio oficial da exchange ou projeto; evitar rumor, "insider" ou agregador sem fonte primaria.
- Para on-chain, preferir explorers publicos, APIs oficiais ou dashboards publicos com metrica claramente descrita.
- Registrar fallback verificavel, como outro agregador publico, explorer equivalente, API oficial ou cancelamento se nenhum dado confiavel existir.
- Evitar linguagem de compra, venda, lucro, promessa de rendimento, recomendacao financeira ou incentivo de investimento.
- Evitar acusacoes de fraude, insolvencia ou irregularidade sem fonte oficial, decisao publica ou dado objetivo verificavel.

## Regra Dura

Fonte social sem link exato, endpoint exato, credencial disponivel ou validacao de acesso pode inspirar mercado, mas nao pode ser fonte final de resolucao.

Para cripto, fonte sem dado publico objetivo e aviso de risco nao pode ser fonte final de resolucao.
