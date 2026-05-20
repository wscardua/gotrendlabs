---
name: orynth-prediction-markets
description: Criar sugestoes diversificadas de mercados de previsao para Orynth usando dados internos da plataforma, ORM/API local em modo somente leitura, specs do projeto, credenciais locais em .env quando autorizadas, e trends verificaveis de YouTube, TikTok, X, Facebook, Instagram, Reddit, Twitch, Google Trends, SteamDB e outras fontes publicas. Use quando Codex precisar sugerir mercados binarios ou multiplos sobre games, tecnologia, espaco, filmes, series, fofocas publicas ou influencers, com prazos definidos, links exatos de verificacao, criterios objetivos de resolucao, diversidade editorial e checagem anti-repeticao contra mercados existentes.
---

# Orynth Prediction Markets

Use esta skill para sugerir mercados de previsao para a Orynth.

Priorize dados internos da plataforma antes de buscar trends externas. Redes sociais e fontes publicas devem complementar o historico real da Orynth, nao substituir os sinais do produto.

Leia as referencias conforme a necessidade:

- `references/seguranca-e-env.md` antes de ler `.env`, autenticar ou usar qualquer credencial.
- `references/acesso-dados-internos.md` antes de consultar ORM, banco, APIs internas, specs ou tabelas.
- `references/fontes-sociais-e-verificacao.md` antes de usar YouTube, TikTok, X, Facebook, Instagram, Reddit, Twitch, Google Trends, SteamDB ou fontes similares.
- `references/framework-de-mercados.md` antes de gerar o lote final.
- `references/mercados-anteriores.md` antes de finalizar sugestoes, para evitar repeticao.

## Fluxo Obrigatorio

1. Consultar dados internos read-only primeiro:
   - mercados existentes
   - views, shares, likes, favoritos, comentarios, previsoes e volume
   - categorias/subcategorias fortes e saturadas
   - temas, pessoas, franquias e formatos ja usados

2. Identificar lacunas e diversidade:
   - categorias dominantes
   - categorias subexploradas
   - temas repetidos
   - oportunidades novas dentro de games, tecnologia, espaco, filmes, series, fofocas publicas e influencers

3. Buscar trends externas apenas para enriquecer:
   - YouTube, TikTok, X, Facebook, Instagram, Reddit, Twitch, Google Trends, SteamDB e fontes oficiais
   - preferir links exatos de pagina, canal, video, endpoint, ranking ou post
   - usar fonte social sem link exato apenas como inspiracao, nunca como juiz final

4. Gerar mercados:
   - tipo `binario` ou `multiplo`
   - pergunta objetiva
   - prazo definido
   - link exato de verificacao
   - criterio objetivo de resolucao
   - fallback para link indisponivel, empate, exclusao ou ambiguidade
   - nota de diversidade
   - checagem anti-repeticao

5. Rejeitar sugestoes invalidas:
   - sem link exato de verificacao
   - sem prazo
   - sem criterio objetivo
   - repetidas ou quase repetidas
   - baseadas em acusacoes, vida privada sensivel, assedio, difamacao ou especulacao toxica

## Quando Faltar Informacao

Se faltar uma informacao essencial para gerar mercados assertivos, solicite exatamente essa informacao ao usuario de forma objetiva.

Peca informacao quando a ausencia impedir uma destas garantias:

- acesso aos dados internos
- recorte de categorias
- quantidade de mercados desejada
- periodo/prazo de resolucao
- pais/regiao das trends
- fonte de resolucao confiavel
- credencial ou variavel de ambiente necessaria
- lista de mercados ja publicados quando o banco local nao estiver disponivel

Faca perguntas curtas e acionaveis. Nao peca confirmacao para detalhes opcionais se houver uma premissa razoavel e segura.

Exemplos:

- "Preciso do pais/regiao das trends: Brasil, EUA ou global?"
- "Nao encontrei `X_BEARER_TOKEN`. Posso seguir sem X e usar YouTube, Reddit, SteamDB e Google Trends?"
- "Quantos mercados voce quer neste lote?"
- "O banco local nao esta acessivel. Voce pode enviar a lista de mercados ja publicados para evitar repeticao?"
- "Qual janela de resolucao prefere: 24h, 7 dias ou ate uma data especifica?"

## Saida Obrigatoria

Cada sugestao deve incluir:

- Tipo: `binario` ou `multiplo`
- Categoria
- Pergunta
- Opcoes
- Prazo de resolucao
- Fonte de resolucao
- Link exato de verificacao
- Momento da checagem
- Criterio objetivo de resolucao
- Regra de empate/ambiguidade/indisponibilidade
- Sinal interno usado
- Sinal externo usado
- Por que deve performar bem
- Nota de diversidade
- Checagem anti-repeticao

## Regras De Diversidade

Nao deixe a popularidade bruta decidir o lote inteiro.

Para lotes com 5 ou mais mercados:

- usar pelo menos 3 categorias diferentes
- limitar a categoria dominante a no maximo 40% do lote
- incluir ao menos 1 categoria subexplorada quando houver sinal externo verificavel
- alternar tipo `binario` e `multiplo` sempre que fizer sentido
- variar prazos, fontes e formatos de resolucao

Evite repetir:

- mesma franquia
- mesmo influencer
- mesma plataforma
- mesmo padrao de pergunta
- mesma fonte de resolucao
- mesmo prazo
- mesma tese com pequenas mudancas de texto

## Tom

Escreva mercados divertidos, atuais, claros e participativos.

Prefira perguntas que sejam entendidas rapidamente, tenham gancho social e incentivem debate sem virar toxicidade.
