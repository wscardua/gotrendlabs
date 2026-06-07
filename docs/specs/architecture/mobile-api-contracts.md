---
id: ARCH-MOBILE-API-001
titulo: "Contratos API para mobile"
versao: 0.1
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-06-07
origem:
  - docs/specs/architecture/backend-api.md
  - packages/contracts/openapi/gotrendlabs-api.json
contratos_afetados:
  - prediction-payloads.md
  - wallet-ledger.md
  - reputation-ranking.md
dependencias:
  - ARCH-MOBILE-001
impacta:
  - future-mobile
  - backend-api
aprovacao: pendente
---

# Contratos API para mobile

## Objetivo

Definir o conjunto inicial de contratos FastAPI que o app Flutter deve consumir no MVP, evitando acoplamento com templates Django e evitando endpoints novos sem necessidade comprovada.

## Diretriz principal

O mobile deve consumir a FastAPI como cliente JSON. Sempre que um endpoint ja atender web e mobile com payload adequado, o app deve reutilizar esse contrato. Novos campos ou endpoints devem atualizar o OpenAPI versionado e as specs afetadas.

## Base URL local

- Emulador Android API: `http://10.0.2.2:8001`
- Emulador Android web/media: `http://10.0.2.2:8000`
- Aparelho fisico na mesma rede: `http://<ip-do-mac>:8001`
- Chrome/web local: `http://127.0.0.1:8001`

Para o emulador renderizar imagens em `/media/...`, o Django local precisa escutar em host acessivel ao emulador e aceitar `10.0.2.2` em `GOTRENDLABS_ALLOWED_HOSTS`; caso contrario thumbnails de mercado e badges caem no fallback visual mesmo com `image_url` correto na API.

## Contratos de leitura publica

### Feed de mercados

Endpoint esperado:

- `GET /markets`

Uso no mobile:

- aba `Hoje`
- aba `Mercados`
- carrossel de destaque
- listas por categoria, subcategoria, evento e status

Campos minimos esperados:

- `slug`
- `title`
- `status`
- `category`
- `subcategory`
- `event`
- `image_url`
- `options[]`
- `primary_probability`
- `primary_probability_exact`
- `volume_gtl`
- `human_volume_gtl`
- `participants`
- `market_like_count`
- `comment_count`
- `viewer_has_prediction`
- `viewer_has_favorite`
- `viewer_has_like`
- `created_at`
- `close_at`
- `sparkline_series`

O app pode ordenar e filtrar visualmente os itens ja carregados, mas filtros autoritativos e recortes paginados devem vir da API quando o volume exigir.

### Detalhe de mercado

Endpoint esperado:

- `GET /markets/{slug}`

Uso no mobile:

- tela de detalhe
- ticket de previsao
- grafico de consenso
- bloco de comentarios
- resumo de ciclo do mercado

Campos minimos esperados:

- todos os campos relevantes do feed
- `description` ou contexto equivalente quando disponivel
- `resolution_criteria`
- `category_notice`
- `subcategory_notice`
- `event_notice`
- `resolved_at`
- `resolved_at_label`
- `resolution_timezone`
- `winning_option_id`
- `resolution_note`
- `viewer_prediction` ou sinal equivalente quando existir

O app nao deve reconstruir regras de status; deve apresentar o estado vindo da API.

### Taxonomia publica

Endpoint esperado:

- `GET /taxonomy`

Uso no mobile:

- filtros de mercado
- filtros de ranking
- descoberta por categoria/subcategoria/evento
- seletor de categoria em `Sugerir mercado`, usando o nome canonico retornado pela API

Itens bloqueados logicamente nao devem aparecer para selecao publica.

### Estatisticas publicas

Endpoint esperado:

- `GET /stats`

Uso no mobile:

- resumo educativo em onboarding, Hoje ou perfil publico
- numeros de produto sem sugerir dinheiro real

## Contratos autenticados

### Autenticacao e sessao

Endpoints esperados, conforme implementacao FastAPI vigente:

- login
- cadastro
- logout/revogacao de sessao quando disponivel
- recuperacao de senha
- `GET /users/me`
- edicao de perfil autenticado

Requisitos mobile:

- respostas devem diferenciar credencial invalida, email nao confirmado, sessao expirada e conta desativada
- o app deve conseguir restaurar sessao de forma segura ao abrir
- usuario com email nao confirmado deve ver modo limitado e bloqueio de acoes sensiveis

Se a autenticacao atual estiver orientada a cookie web, uma decisao tecnica deve definir a estrategia mobile antes de implementar login persistente.

Decisao v1 para a implementacao autenticada:

- usar Bearer simples retornado em `AuthResponse.session.token`
- persistir token no Flutter com secure storage
- restaurar sessao por `GET /auth/session`
- encerrar sessao por `POST /auth/logout`
- usar a expiracao existente em `AuthResponse.session.expires_at`
- deixar refresh token, renovacao automatica e revogacao avancada para etapa futura

### Favoritos e curtidas de mercado

Endpoints esperados:

- `POST /markets/{slug}/favorite`
- `DELETE /markets/{slug}/favorite`
- `POST /markets/{slug}/like`
- `DELETE /markets/{slug}/like`

Requisitos mobile:

- mutacoes idempotentes
- atualizacao otimista permitida apenas como estado visual temporario
- rollback visual quando a API rejeitar a acao
- visitante recebe CTA de login em vez de formulario mutavel

### Preview e criacao de previsao

Endpoints esperados:

- `POST /markets/{slug}/prediction-preview`
- endpoint de criacao de previsao conforme contrato `prediction-payloads.md`

Requisitos mobile:

- preview sempre calculado pela API
- app pode chamar preview de forma reativa ao selecionar opcao ou mover o controle de GT₵, com debounce, sem calcular retorno localmente
- criacao exige usuario autenticado, opcao explicita e stake valido
- duplicidade de previsao, saldo insuficiente e mercado fechado devem gerar erro mapeavel
- resposta de sucesso deve retornar saldo atualizado e snapshot de probabilidade

### Comentarios

Endpoints esperados:

- `GET /markets/{slug}/comments`
- `POST /markets/{slug}/comments`
- `POST /comments/{id}/like`
- `DELETE /comments/{id}/like`
- `POST /comments/{id}/dislike`
- `DELETE /comments/{id}/dislike`

Requisitos mobile:

- visitantes leem comentarios e recebem CTA de login para comentar
- autores aparecem por handle publico
- autores IA oficiais exibem selo `IA oficial`
- comentarios ocultos por moderacao nao aparecem

### Wallet

Endpoints esperados:

- `GET /users/me/wallet`
- `GET /users/me/ledger`
- `GET /users/me/wallet/recharge-requests`
- `POST /users/me/wallet/recharge-requests`

Requisitos mobile:

- saldo e extrato sao leitura da API
- recarga controlada usa `available_gtl`, `min_balance_gtl`, `eligible` e `requests` retornados pela API
- app mostra pendencia e historico, mas o `POST` continua sendo a autoridade para elegibilidade, duplicidade e email confirmado
- labels humanos devem evitar codigos tecnicos de ledger
- `GTL` ou `GT₵` deve ser tratado como moeda educativa, sem copy de dinheiro real, saque ou investimento

### Ranking e badges

Endpoints esperados:

- `GET /rankings`
- `GET /badges`
- `GET /users/me/badges`
- compartilhamento de badge conquistada quando disponivel

Requisitos mobile:

- staff, superuser e bots nao aparecem no ranking publico
- app nao calcula elegibilidade de badge
- imagens de badge em `/media/...` sao resolvidas contra o web/public base, nao contra a FastAPI
- compartilhamento nao altera reputacao, wallet ou ranking

### Indicacao

Endpoint esperado:

- `GET /users/me/referral`

Requisitos mobile:

- app apenas exibe e compartilha o codigo/link retornado pelo backend
- bonus, habilitacao, razao de bloqueio e credito ficam sob autoridade backend/Admin Ops

### Sugestoes e feedback

Endpoints esperados:

- `POST /suggestions`
- `POST /feedback`

Requisitos mobile:

- formulario mobile envia payload JSON para a FastAPI
- sugestao de mercado usa categorias ativas de `GET /taxonomy`
- feedback usa as mesmas opcoes publicas da web e envia `severity=medium` como compatibilidade de contrato
- usuario autenticado nao informa nome/email de visitante
- visitante identificado informa nome/email quando o backend exigir
- app nao aprova sugestao, nao converte sugestao em mercado e nao calcula recompensa
- app nao recompensa feedback; status, revisao e creditos ficam no backend/Admin Ops

## Erros padronizados para UX

O app deve mapear erros de API para categorias:

- `unauthenticated`: solicitar login
- `forbidden`: acao nao permitida
- `validation`: campos invalidos
- `domain_state`: mercado fechado, resolvido, cancelado ou previsao duplicada
- `insufficient_balance`: saldo educativo insuficiente
- `network`: indisponibilidade local ou conexao
- `server`: falha inesperada

Mensagens tecnicas devem ficar fora da UI final.

## OpenAPI e clientes gerados

- Toda alteracao de contrato deve atualizar `packages/contracts/openapi/gotrendlabs-api.json`.
- O mobile pode usar cliente HTTP manual no MVP para manter velocidade.
- Cliente gerado a partir do OpenAPI pode ser avaliado quando os contratos estabilizarem.
- `gotrendlabs-mobile-api-contract-guard` deve revisar qualquer PR que altere payload consumido pelo app.

## Criterios de aceite

- o app consegue listar mercados via API local no emulador
- o app consegue abrir detalhe de mercado sem depender do Django
- visitante ve estados autenticados bloqueados sem erro bruto
- mutacoes autenticadas usam apenas FastAPI
- contrato novo necessario e documentado antes de implementado
- lacunas de auth mobile estao registradas antes de login persistente
