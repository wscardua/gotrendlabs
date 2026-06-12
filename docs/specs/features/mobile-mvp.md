---
id: FEAT-MOBILE-001
titulo: "MVP mobile Flutter"
versao: 0.2
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-06-07
origem:
  - docs/specs/spec_prediction_social_market_pt.md
  - docs/specs/features/market-feed.md
  - docs/specs/features/market-detail.md
dependencias:
  - ARCH-MOBILE-001
  - ARCH-MOBILE-API-001
  - FEAT-AUTH-001
  - FEAT-MARKET-001
  - FEAT-MARKET-002
  - FEAT-PRED-001
  - FEAT-WALLET-001
impacta:
  - future-mobile
  - backend-api
aprovacao: pendente
---

# MVP mobile Flutter

## Objetivo

Entregar a primeira experiencia Android do GoTrendLabs para descoberta de mercados, leitura de detalhe, autenticacao e previsao educativa, reaproveitando os contratos existentes da FastAPI.

## Publico inicial

- visitante que quer explorar mercados e entender o produto
- usuario autenticado que acompanha previsoes, reputacao e saldo educativo
- usuario recorrente que busca mercados por categoria e eventos relevantes

## Distribuicao beta

O beta Android inicial e publico, sem exigir login para baixar. Nao ha pagina dedicada para o app Android nesta etapa; o rodape do site, as telas de acesso e as paginas de compartilhamento exibem um icone/CTA Android e apontam direto para o APK ativo quando existir release publicada. Quando nao houver release ativa, os mesmos pontos mostram estado discreto "Android em breve" sem link quebrado. Ao lado do Android, a UI pode exibir `App iOS` / `iOS em breve` apenas como sinal de roadmap, sem link de download nesta etapa. O endpoint `gotrendlabs.com.br/app/android/latest.json` expoe metadados da release ativa para uso futuro pelo app.

O APK deve ser gerenciado no Admin Ops, armazenado em `MEDIA_ROOT/app_releases/android/` e servido por HTTPS via `/media/app_releases/android/...`. Apenas uma release Android pode ficar ativa por vez.

## Escopo incluido

- onboarding leve sem landing page extensa
- feed `Hoje` com destaques e mercados em alta
- browse de mercados por categoria/status
- busca simples por texto quando houver contrato adequado ou filtro local sobre lista carregada
- detalhe de mercado com hero visual, probabilidade, metricas, grafico compacto, opcoes e comentarios
- login, cadastro e recuperacao conforme contratos disponiveis
- preview de previsao via backend
- criacao de previsao autenticada
- favoritos e curtidas de mercado
- leitura e criacao de comentarios
- wallet resumida e extrato
- perfil autenticado
- ranking e badges em leitura
- suporte/feedback via fila FastAPI existente
- sugestao de mercados via fila FastAPI existente
- central de alertas in-app com abertura por payload de push e registro FCM autenticado quando Firebase Android estiver configurado
- canal publico beta Android por APK assinado no site oficial
- governanca documental por skills mobile locais antes de cada fatia de implementacao

## Escopo excluido

- iOS
- publicacao em loja, Google Play, TestFlight ou App Store
- entrega FCM em producao sem credencial backend em ambiente e aprovacao operacional
- atualizacao automatica dentro do app
- compra, saque, deposito real, blockchain ou linguagem financeira
- live updates por websocket
- admin ops mobile
- criacao administrativa de mercados
- edicao de badges, taxonomia ou usuarios

## Abas principais

### Hoje

Primeira tela util do app. Deve mostrar:

- saudacao ou contexto curto quando autenticado
- mercados em destaque por popularidade/curadoria existente
- cards grandes com imagem, categoria, pergunta, probabilidade e volume educativo
- secoes compactas de tendencias, novos e encerrando em breve

### Insights

Area para conteudo interpretativo e agentes IA quando contratos existirem. No MVP pode exibir:

- mercados com comentarios de IA oficial
- explicacoes de contexto vindas do backend
- estados vazios claros quando nao houver insight disponivel

O app nao deve gerar insight local com IA nem chamar provedor LLM diretamente.

### Mercados

Browse completo com:

- categorias em chips horizontais
- filtros por status
- lista/card grid responsivo para celular
- ordenacoes locais sobre dados carregados quando suficiente
- paginacao ou carregar mais quando contrato permitir

### Alertas

Central in-app inicial:

- mercados que o usuario favoritou
- mercados em que o usuario previu
- resolucoes recentes quando contrato expuser
- convite para configurar notificacoes futuras

Push real Android usa FCM quando `google-services.json` existe no build e o backend está habilitado com provider `fcm`; sem Firebase, o app permanece em modo indisponível/fake-token para QA local. A tela `Sobre` mostra o estado seguro de push sem expor tokens, e revogação/preferências continuam ações explícitas via FastAPI.

### Busca

Busca e descoberta:

- campo de busca
- categorias e eventos recentes
- resultados de mercados
- estado vazio com sugestao de categorias

## Telas de detalhe

### Detalhe de mercado

Deve mostrar:

- hero com imagem do mercado e gradiente escuro para legibilidade
- botao voltar e acoes de notificar/favoritar/compartilhar
- abas `Visao geral` e `Comunidade`
- titulo, categoria/evento e status
- probabilidade principal e opcoes
- metricas compactas: volume GTL, participantes, comentarios, encerramento, ultima atividade quando disponivel
- grafico de consenso baseado em `sparkline_series`
- ticket de previsao para mercado aberto
- resultado oficial para mercado resolvido

### Comunidade

Deve mostrar:

- comentarios visiveis
- selo para IA oficial
- reacoes like/dislike em comentarios
- composer para usuario autenticado
- CTA de login para visitante

## Fluxo de previsao

1. Usuario abre mercado aberto.
2. App mostra opcoes sem selecao inicial.
3. Usuario escolhe uma opcao explicitamente.
4. Usuario informa stake educativo.
5. App chama preview no backend.
6. App mostra confirmacao em bottom sheet.
7. Usuario confirma.
8. App envia mutacao para FastAPI.
9. App atualiza detalhe, saldo e estado de previsao a partir da resposta.

Erros esperados:

- visitante precisa autenticar
- email nao confirmado bloqueia acao sensivel
- saldo insuficiente
- mercado fechado, em apuracao, resolvido ou cancelado
- previsao duplicada
- opcao invalida
- indisponibilidade da API

## Ordem sugerida de implementacao

1. Criar projeto Flutter em `apps/mobile` com tema, roteamento, ambiente local e bottom navigation.
2. Implementar shell visual dark-first com abas `Hoje`, `Ranking`, `Mercados`, `Alertas` e `Busca`, mantendo `Insights` no menu superior até existir conteúdo recorrente.
3. Consumir `GET /markets` e renderizar cards visuais de mercado.
4. Implementar detalhe de mercado com hero, abas `Visao geral`/`Comunidade` e painel de metricas.
5. Resolver estrategia de autenticacao mobile antes de login persistente.
6. Implementar favoritos, curtidas, comentarios e preview de previsao.
7. Implementar criacao de previsao autenticada.
8. Implementar wallet, perfil, ranking e badges como leitura da API.
9. Fechar testes e QA visual no emulador.
10. Publicar APK beta assinado via Admin Ops e divulgar o link direto no rodape/login/cadastro/compartilhamento, mantendo metadados publicos em `/app/android/latest.json`.

## Wallet e perfil

Wallet no MVP:

- saldo GTL/GT₵ educativo
- extrato resumido
- labels humanos de origem
- aviso claro de que nao existe dinheiro real

Perfil no MVP:

- nome publico e handle
- reputacao
- badges conquistadas
- catalogo de badges com imagens e estado de conquista
- estatisticas resumidas quando contrato existir
- acesso a configuracoes basicas
- acesso a convite/indicacao quando backend habilitar
- acesso a suporte/feedback
- acesso a sugestao de mercado

## Regras de dominio

- uma previsao por usuario/mercado no MVP
- stake e preview sempre validados no backend
- probabilidade exibida usa contrato da API
- saldo e extrato usam ledger/projecao da API
- reputacao, ranking e badges sao leitura da API
- imagens de mercado/badges usam `image_url`/`thumb` retornados pela API, com fallback visual apenas de apresentacao
- feedback e sugestoes sao enviados para filas do backend; revisao, recompensa e conversao em mercado ficam no backend/Admin Ops
- visitantes podem explorar, mas mutacoes autenticadas exigem login

## Metricas de produto

MVP deve permitir medir futuramente:

- abertura de app
- CTR de card para detalhe
- uso de filtro/categoria
- preview iniciado
- previsao confirmada
- erros de previsao
- favoritos e curtidas
- comentarios enviados

## Criterios de aceite

- visitante consegue abrir o app, navegar por mercados e entrar em detalhe
- usuario autenticado consegue prever em mercado aberto usando saldo educativo
- usuario entende quando uma acao exige login ou email confirmado
- mercado resolvido mostra resultado oficial sem permitir nova previsao
- comentarios aparecem no detalhe e visitante nao ve formulario mutavel
- wallet exibe saldo e extrato sem linguagem de dinheiro real
- app roda no emulador `gotrendlabs_pixel`

## Impacto de mudanca

Mudancas neste MVP podem exigir ajustes em contratos publicos de mercado, auth, comentarios, wallet e ranking.
