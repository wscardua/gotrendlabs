# Seguranca E Ambiente Local

Pode inspecionar `.env` locais somente para acesso autorizado e read-only a APIs, banco ou fontes internas necessarias para pesquisa de mercados.

Arquivos candidatos:

- `.env`
- `.env.local`
- `.env.development`
- arquivos `.env` especificos de backend

Variaveis internas esperadas:

- `BACKEND_API_URL`
- `DJANGO_POSTGRES_DB`
- `DJANGO_POSTGRES_USER`
- `DJANGO_POSTGRES_PASSWORD`
- `DJANGO_POSTGRES_HOST`
- `DJANGO_POSTGRES_PORT`
- `FASTAPI_POSTGRES_DB`
- `FASTAPI_POSTGRES_USER`
- `FASTAPI_POSTGRES_PASSWORD`
- `FASTAPI_POSTGRES_HOST`
- `FASTAPI_POSTGRES_PORT`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `ORYNTH_ADMIN_EMAIL`
- `ORYNTH_ADMIN_PASSWORD`
- `ORYNTH_ADMIN_TOKEN`

Variaveis externas opcionais:

- `YOUTUBE_API_KEY`
- `X_BEARER_TOKEN`
- `TWITCH_CLIENT_ID`
- `TWITCH_CLIENT_SECRET`
- `META_ACCESS_TOKEN`
- `FACEBOOK_ACCESS_TOKEN`
- `INSTAGRAM_ACCESS_TOKEN`
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `TIKTOK_ACCESS_TOKEN`

Regras obrigatorias:

- Nunca imprimir valores secretos.
- Nunca copiar credenciais para arquivos da skill.
- Nunca commitar credenciais.
- Nunca incluir senhas, tokens, cookies ou URLs sensiveis em respostas.
- Mencionar apenas nomes das variaveis, nunca seus valores.
- Usar credenciais apenas para consultas autorizadas e read-only.
- Preferir endpoints `GET` e consultas ORM sem mutacao.
- Nao criar, editar, publicar, resolver ou deletar mercados sem pedido explicito do usuario.
- Manter tokens apenas em memoria durante a tarefa.
- Evitar logs verbosos que possam expor secrets.

Se credenciais necessarias estiverem ausentes, informe quais nomes de variaveis faltam e continue com fontes publicas apenas quando isso ainda produzir sugestoes verificaveis.
