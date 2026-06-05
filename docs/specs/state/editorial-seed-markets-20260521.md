# Lote Editorial Seed de Mercados - 2026-05-21

Este documento registra a memoria versionada do lote editorial criado para povoar a base local de testes da GoTrendLabs em 21 de maio de 2026, com adicoes editoriais posteriores quando aprovadas.

## Decisoes Operacionais

- Quantidade total: 27 mercados, multiplo de 3.
- Status inicial: `draft`.
- Taxonomia: criar categorias/subcategorias ausentes de forma idempotente e preservar as existentes.
- Thumbnails: imagens locais autorais em `media/market_thumbnails/generated-<slug>.png`.
- Regra visual das thumbnails: imagem pura do evento/tema, sem titulo, texto, categoria, fonte ou marca embutidos. A UI/API continuam sendo a fonte de verdade de metadados textuais.
- Fonte de resolucao: cada mercado deve manter fonte publica verificavel em `source` e criterio/fallback em `resolution_criteria`.
- Publicacao: nenhum mercado seed deve ser publicado automaticamente; operador revisa odds, horario, fonte e criterio antes de publicar.

## Categorias e Subcategorias Do Lote Inicial

| Categoria | Subcategorias | Mercados |
| --- | --- | ---: |
| Esporte | Futebol | 4 |
| Games | Steam, Eventos, GTA, Nintendo | 4 |
| Tecnologia | Apple | 2 |
| Economia | EUA, Juros | 2 |
| Espaco | SpaceX | 1 |
| Realeza | Reino Unido, Royal Ascot | 3 |
| Cinema | Cannes | 2 |
| Fofoca | Pop | 1 |
| Series | Netflix, HBO Max | 3 |
| Filmes | Bilheteria, Marvel, Cannes | 2 |
| Influencers | YouTube, Twitch, TikTok | 3 |

## Mercados

| # | Slug | Categoria > Subcategoria | Tipo | Fonte principal |
| ---: | --- | --- | --- | --- |
| 1 | `brasil-vencera-marrocos-copa-2026` | Esporte > Futebol | binary | FIFA calendario/resultados |
| 2 | `vencedor-grupo-c-copa-2026` | Esporte > Futebol | multiple | FIFA tabela do grupo |
| 3 | `anfitriao-mais-longe-copa-2026` | Esporte > Futebol | multiple | FIFA chave/resultados |
| 4 | `final-copa-2026-prorrogacao-ou-penaltis` | Esporte > Futebol | binary | Relatorio oficial FIFA |
| 5 | `steam-ranking-1-junho-2026` | Games > Steam | multiple | Steam Most Played |
| 6 | `summer-game-fest-video-5m-views-72h` | Games > Eventos | binary | YouTube The Game Awards |
| 7 | `rockstar-novo-video-gta-vi-junho-2026` | Games > GTA | binary | YouTube Rockstar Games |
| 8 | `nintendo-direct-video-junho-2026` | Games > Nintendo | binary | YouTube Nintendo America |
| 9 | `apple-siri-release-wwdc26` | Tecnologia > Apple | binary | Apple Newsroom |
| 10 | `apple-preview-publico-proximo-ios-wwdc26` | Tecnologia > Apple | binary | Apple Newsroom / apple.com |
| 11 | `cpi-eua-maio-2026-maior-igual-03` | Economia > EUA | binary | BLS CPI release |
| 12 | `fomc-cortara-juros-junho-2026` | Economia > Juros | binary | Federal Reserve |
| 13 | `starship-flight-12-explodira-ou-sera-perdida` | Espaco > SpaceX | binary | SpaceX Launches / webcast oficial |
| 14 | `rei-charles-varanda-trooping-colour-2026` | Realeza > Reino Unido | binary | Household Division / Royal Family |
| 15 | `william-kate-trooping-colour-2026` | Realeza > Reino Unido | binary | Royal Family |
| 16 | `rei-rainha-royal-ascot-2026` | Realeza > Royal Ascot | binary | Court Circular / Royal Ascot |
| 17 | `palme-dor-cannes-2026-diretora-mulher` | Cinema > Cannes | binary | Festival de Cannes |
| 18 | `taylor-swift-novo-video-junho-2026` | Fofoca > Pop | binary | YouTube Taylor Swift |
| 19 | `netflix-serie-top1-global-julho-2026` | Series > Netflix | multiple | Netflix Tudum Top 10 |
| 20 | `avatar-live-action-top10-netflix-estreia` | Series > Netflix | binary | Netflix Tudum Top 10 |
| 21 | `filme-lider-bilheteria-eua-10-12-julho-2026` | Filmes > Bilheteria | multiple | Box Office Mojo |
| 22 | `avengers-doomsday-novo-trailer-junho-2026` | Filmes > Marvel | binary | Marvel / YouTube oficial |
| 23 | `palme-dor-streaming-anunciado-junho-2026` | Filmes > Cannes | binary | Festival de Cannes + distribuidora |
| 24 | `hbo-max-top10-original-julho-2026` | Series > HBO Max | binary | HBO Max Top 10 / FlixPatrol |
| 25 | `mrbeast-video-100m-views-7-dias-junho-2026` | Influencers > YouTube | binary | YouTube MrBeast |
| 26 | `kai-cenat-live-twitch-junho-2026` | Influencers > Twitch | binary | Twitch Kai Cenat |
| 27 | `khaby-lame-novo-tiktok-junho-2026` | Influencers > TikTok | binary | TikTok Khaby Lame |

## Observacoes de Retomada

- O banco local foi populado por operacao aprovada pelo usuario; bancos remotos devem ser populados por fluxo operacional controlado, nao por assumir que `db.sqlite3` ou volumes locais serao versionados.
- As thumbnails estao versionadas como arquivos de midia locais para preservar a experiencia visual do lote.
- Se o lote for reaplicado, usar `slug` como chave natural para evitar duplicatas.

## Adicao DEV - Cripto - 2026-05-22

Em 22 de maio de 2026, foram adicionados 3 mercados cripto no banco DEV local, todos com status inicial `draft`, categoria/subcategoria criadas de forma idempotente e thumbnails autorais locais.

Regras especificas da adicao:

- Categoria: `Cripto`.
- Subcategorias: `Preço`, `DeFi / On-chain`, `Meme coins`.
- Aviso obrigatorio em `resolution_criteria`: `Não caracteriza recomendação de investimento.`
- Fonte de resolucao: cada mercado usa link publico verificavel em `source` e fallback no criterio.
- Thumbnails: imagens locais autorais em `media/market_thumbnails/generated-<slug>.png`, sem texto, logos ou marcas oficiais embutidas.
- Publicacao: nenhum mercado foi publicado automaticamente; operador revisa odds, fonte, horario e criterio antes de publicar.

| # | Slug | Categoria > Subcategoria | Tipo | Fonte principal | Thumbnail |
| ---: | --- | --- | --- | --- | --- |
| 28 | `bitcoin-acima-80000-30-junho-2026` | Cripto > Preço | binary | CoinGecko Bitcoin | `media/market_thumbnails/generated-bitcoin-acima-80000-30-junho-2026.png` |
| 29 | `solana-acima-bsc-tvl-31-maio-2026` | Cripto > DeFi / On-chain | binary | DefiLlama Chains | `media/market_thumbnails/generated-solana-acima-bsc-tvl-31-maio-2026.png` |
| 30 | `pepe-acima-shiba-meme-coins-15-junho-2026` | Cripto > Meme coins | binary | CoinGecko Meme Token | `media/market_thumbnails/generated-pepe-acima-shiba-meme-coins-15-junho-2026.png` |

## Adicao Aprovada - Mercado / Cripto - 2026-05-22

Em 22 de maio de 2026, foi aprovado um segundo lote cripto mais acessivel para publicacao operacional, com uma taxonomia unica para reduzir fragmentacao no feed e permitir aviso de risco no nivel de subcategoria.

Regras especificas da adicao:

- Categoria: `Mercado`.
- Subcategoria: `Cripto`.
- Aviso de subcategoria: `Mercados de criptoativos envolvem alta volatilidade. Nao caracteriza recomendacao de investimento.`
- Eventos: `Ethereum`, `Dogecoin`, `Solana`.
- Status inicial operacional: `open` quando aplicado pelo comando aprovado; usar `--status draft` apenas se a curadoria quiser revisar antes de publicar.
- Fonte de resolucao: cada mercado usa link publico verificavel em `source` e fallback no criterio.
- Thumbnails: imagens locais autorais em `media/market_thumbnails/generated-<slug>.png`, sem texto, logos ou marcas oficiais embutidas.
- Aplicacao: usar o comando idempotente `python manage.py seed_crypto_markets_20260522`.

| # | Slug | Categoria > Subcategoria > Evento | Tipo | Fonte principal | Thumbnail |
| ---: | --- | --- | --- | --- | --- |
| 31 | `ethereum-acima-3000-30-junho-2026` | Mercado > Cripto > Ethereum | binary | CoinGecko Ethereum | `media/market_thumbnails/generated-ethereum-acima-3000-30-junho-2026.png` |
| 32 | `dogecoin-top10-30-junho-2026` | Mercado > Cripto > Dogecoin | binary | CoinGecko ranking geral | `media/market_thumbnails/generated-dogecoin-top10-30-junho-2026.png` |
| 33 | `solana-acima-xrp-ranking-30-junho-2026` | Mercado > Cripto > Solana | binary | CoinGecko ranking geral | `media/market_thumbnails/generated-solana-acima-xrp-ranking-30-junho-2026.png` |
