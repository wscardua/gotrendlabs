# Guia: Skill Orynth Prediction Markets

Use a skill `orynth-prediction-markets` para gerar sugestoes de mercados de previsao baseadas nos dados internos da Orynth e em trends verificaveis de redes sociais/fontes publicas.

## Quando Usar

Use quando quiser:

- sugerir novos mercados binarios ou multiplos
- criar mercados sobre games, tecnologia, espaco, filmes, series, fofocas publicas ou influencers
- usar os mercados mais visualizados/curtidos/participados da Orynth como sinal
- evitar repeticao de mercados ja publicados
- trazer links exatos para verificacao de resolucao
- balancear diversidade e performance

## Prompt Recomendado

```text
Use $orynth-prediction-markets para sugerir 10 mercados de previsao para a Orynth.

Priorize dados internos da plataforma, evite repetir mercados existentes, mantenha diversidade entre categorias e use links exatos de verificacao. Inclua mercados binarios e multiplos, com prazo, fonte, criterio objetivo de resolucao e fallback.
```

## Fluxo Que A Skill Deve Seguir

1. Ler `references/seguranca-e-env.md` antes de qualquer credencial.
2. Consultar dados internos read-only pelo ORM/API local.
3. Levantar categorias dominantes e subexploradas.
4. Buscar trends externas em YouTube, TikTok, X, Facebook, Instagram, Reddit, Twitch, Google Trends, SteamDB ou fontes oficiais.
5. Exigir link exato de verificacao para cada mercado.
6. Validar se a fonte de resolucao consegue fundamentar e certificar o resultado.
7. Aplicar anti-repeticao contra banco local e `references/mercados-anteriores.md`.
8. Gerar lote com diversidade editorial.
9. Quando o usuario aprovar inclusao no banco, criar categorias/subcategorias necessarias de forma idempotente e manter os mercados como `draft` ate revisao/publicacao operacional.
10. Thumbnails de mercado, quando geradas, devem ser imagens puras e autorais do evento/tema, sem texto ou titulo embutido. Titulo, categoria, subcategoria e fonte pertencem ao HTML/API, nao ao bitmap.

## Validacao Da Fonte De Resolucao

A skill deve garantir que a fonte de resolucao seja valida antes de entregar um mercado.

Ela pode usar qualquer recurso autorizado e disponivel:

- navegador local do usuario
- browser automation
- APIs oficiais
- web search
- ORM, banco ou APIs internas da Orynth

A fonte precisa permitir conferir objetivamente o resultado por meio de dado como data de publicacao, ranking, contagem, score, status, resultado oficial ou resposta de API.

Se a fonte nao puder fundamentar a resolucao, a skill deve substituir o mercado ou perguntar objetivamente qual fonte autorizada usar.

## Quando Faltar Informacao

Se faltar uma informacao essencial para gerar sugestoes assertivas, a skill deve perguntar de forma objetiva o que precisa.

Exemplos de perguntas esperadas:

- "Quantos mercados voce quer neste lote?"
- "Qual regiao devo usar para trends: Brasil, EUA ou global?"
- "Nao encontrei `YOUTUBE_API_KEY`. Posso usar links publicos do YouTube sem API?"
- "O banco local nao esta acessivel. Voce pode enviar mercados ja publicados para eu evitar repeticao?"
- "Qual prazo prefere para resolucao: 24h, 7 dias ou data especifica?"

A skill nao deve pedir confirmacao para detalhes opcionais quando houver uma premissa segura. Ela deve pedir apenas o que for necessario para manter dados internos, diversidade, anti-repeticao, fonte exata ou resolucao objetiva.

## Dados Internos Usados

A skill deve considerar:

- `view_count`
- `share_count`
- likes
- favoritos
- comentarios
- previsoes
- categorias/subcategorias
- mercados existentes
- sugestoes anteriores

No repo local, a consulta preferida e via ORM Django read-only. Se API admin estiver disponivel, tambem pode usar:

- `GET /markets`
- `GET /admin/markets`
- `GET /admin/dashboard-summary`

## Fontes Externas

Fontes recomendadas:

- YouTube: videos, canais oficiais, views, likes e comentarios.
- TikTok: Creative Center, hashtags, videos, creators e sons.
- X: contagem de posts por query via API.
- Facebook/Instagram: Meta Content Library/API ou links publicos diretos.
- Reddit: subreddits e rankings `top`.
- Twitch: categorias e streams por espectadores via API.
- Google Trends: tendencia ampla de busca.
- SteamDB/Steam Charts: rankings objetivos de games.

Regra central: sem link exato, a fonte so pode inspirar mercado; nao pode resolver mercado sozinha.

## Formato De Saida Esperado

Cada mercado deve conter:

- Tipo: `binario` ou `multiplo`
- Categoria
- Pergunta
- Opcoes
- Prazo de resolucao
- Fonte de resolucao
- Link exato de verificacao
- Status de validacao da fonte
- Momento da checagem
- Criterio objetivo de resolucao
- Regra de empate/ambiguidade/indisponibilidade
- Sinal interno usado
- Sinal externo usado
- Por que deve performar bem
- Nota de diversidade
- Checagem anti-repeticao

## Credenciais Opcionais

Nao coloque credenciais na skill nem no guia.

Se precisar usar APIs externas, configure variaveis de ambiente localmente, por exemplo:

- `YOUTUBE_API_KEY`
- `X_BEARER_TOKEN`
- `TWITCH_CLIENT_ID`
- `TWITCH_CLIENT_SECRET`
- `META_ACCESS_TOKEN`
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`

A skill deve mencionar somente nomes de variaveis, nunca valores.

## Exemplo Curto

```markdown
Tipo: multiplo
Categoria: games
Pergunta: Qual jogo estara mais alto no ranking da SteamDB em 27 de maio de 2026?
Opcoes: Counter-Strike 2 / Dota 2 / Forza Horizon 6 / Subnautica 2 / Outro
Prazo de resolucao: 27 de maio de 2026, 23:59 BRT
Fonte de resolucao: SteamDB
Link exato de verificacao: https://steamdb.info/charts/
Status de validacao da fonte: validavel; ranking publico e objetivo, conferir acesso antes de finalizar e no prazo de resolucao.
Momento da checagem: 27 de maio de 2026, 23:59 BRT
Criterio objetivo de resolucao: vence o jogo melhor posicionado em "Most played games".
Regra de empate/ambiguidade/indisponibilidade: se SteamDB falhar por 24h, usar ranking oficial da Steam.
Sinal interno usado: games esta subexplorado no historico interno.
Sinal externo usado: ranking publico de jogadores simultaneos.
Por que deve performar bem: competitivo, facil de entender e verificavel.
Nota de diversidade: aumenta variedade fora de IA/politica/cultura.
Checagem anti-repeticao: nao repete mercado existente sobre genero vencedor em games.
```
