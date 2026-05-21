# Framework De Mercados

## Tipos

Use apenas:

- `binario`: opcoes `Sim` e `Nao`
- `multiplo`: opcoes mutuamente exclusivas

Adicione `Outro` apenas quando as opcoes listadas nao cobrirem os resultados plausiveis.

## Pontuacao

Priorize sugestoes usando:

- performance interna da Orynth
- forca da trend recente
- clareza de resolucao
- link exato de verificacao
- potencial de participacao
- novidade
- contribuicao para diversidade

Penalize:

- tema repetido
- fonte fraca
- prazo vago
- resolucao subjetiva
- especulacao sensivel
- quase duplicata de mercados existentes
- falta de fallback

## Template Binario

```markdown
Tipo: binario
Categoria:
Pergunta:
Opcoes: Sim / Nao
Prazo de resolucao:
Fonte de resolucao:
Link exato de verificacao:
Status de validacao da fonte:
Momento da checagem:
Criterio objetivo de resolucao:
Regra de empate/ambiguidade/indisponibilidade:
Sinal interno usado:
Sinal externo usado:
Por que deve performar bem:
Nota de diversidade:
Checagem anti-repeticao:
```

## Template Multiplo

```markdown
Tipo: multiplo
Categoria:
Pergunta:
Opcoes:
Prazo de resolucao:
Fonte de resolucao:
Link exato de verificacao:
Status de validacao da fonte:
Momento da checagem:
Criterio objetivo de resolucao:
Regra de empate/ambiguidade/indisponibilidade:
Sinal interno usado:
Sinal externo usado:
Por que deve performar bem:
Nota de diversidade:
Checagem anti-repeticao:
```

## Bons Exemplos

```markdown
Tipo: multiplo
Categoria: games
Pergunta: Qual jogo estara mais alto no ranking da SteamDB em 27 de maio de 2026?
Opcoes: Counter-Strike 2 / Dota 2 / Forza Horizon 6 / Subnautica 2 / Outro
Prazo de resolucao: 27 de maio de 2026, 23:59 BRT
Fonte de resolucao: SteamDB
Link exato de verificacao: https://steamdb.info/charts/
Status de validacao da fonte: validavel; ranking publico e objetivo, conferir acesso no momento da geracao e novamente no prazo de resolucao.
Momento da checagem: 27 de maio de 2026, 23:59 BRT
Criterio objetivo de resolucao: vence o jogo melhor posicionado em "Most played games" no momento da checagem.
Regra de empate/ambiguidade/indisponibilidade: se SteamDB estiver indisponivel por mais de 24h, usar https://store.steampowered.com/charts/mostplayed no mesmo criterio.
Sinal interno usado: games esta subexplorado em relacao a categorias dominantes.
Sinal externo usado: rankings Steam mostram alta atividade verificavel.
Por que deve performar bem: ranking simples, competitivo e facil de conferir.
Nota de diversidade: adiciona games ao lote para reduzir dependencia de IA/politica/cultura.
Checagem anti-repeticao: nao repete mercados internos sobre genero vencedor em games.
```

```markdown
Tipo: binario
Categoria: games
Pergunta: A Rockstar publicara um novo video publico sobre GTA VI ate 30 de junho de 2026?
Opcoes: Sim / Nao
Prazo de resolucao: 30 de junho de 2026, 23:59 BRT
Fonte de resolucao: canal oficial da Rockstar Games no YouTube
Link exato de verificacao: https://www.youtube.com/@RockstarGames/videos
Status de validacao da fonte: validavel; canal oficial publico, confirmar acesso e existencia da aba de videos antes de finalizar a sugestao.
Momento da checagem: 1 de julho de 2026, 10:00 BRT
Criterio objetivo de resolucao: conta como Sim se houver video publico novo relacionado a GTA VI publicado no canal oficial ate o prazo.
Regra de empate/ambiguidade/indisponibilidade: videos removidos contam apenas se houver registro publico confiavel do canal oficial.
Sinal interno usado: games tem menor volume interno que IA/cultura, mas boa afinidade com mercados virais.
Sinal externo usado: YouTube oficial permite verificacao direta de publicacao.
Por que deve performar bem: GTA VI gera debate forte e resolucao objetiva.
Nota de diversidade: adiciona franquia gamer sem repetir mercados existentes.
Checagem anti-repeticao: nao usar se ja existir mercado sobre novo trailer/video de GTA VI no periodo.
```

## Regras De Resolucao

Toda resolucao deve responder:

- quem venceu
- quando foi verificado
- onde foi verificado
- como a fonte foi validada
- qual dado decidiu
- o que fazer se a fonte falhar

Evite:

- "vai viralizar?"
- "sera bem recebido?"
- "ficara famoso?"
- "causara polemica?"

Prefira:

- "atingira X views?"
- "aparecera no top N?"
- "sera publicado no canal oficial?"
- "tera mais posts que outro termo pela API?"
- "liderara ranking publico em data/hora definida?"
