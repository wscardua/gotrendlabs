---
id: TEST-MOBILE-001
titulo: "Criterios de aceite mobile"
versao: 0.2
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-06-16
origem:
  - docs/specs/testing/test-strategy.md
  - docs/specs/features/mobile-mvp.md
dependencias:
  - ARCH-MOBILE-001
  - FEAT-MOBILE-001
impacta:
  - future-mobile
  - backend-api
aprovacao: pendente
---

# Criterios de aceite mobile

## Objetivo

Definir como validar que o app Flutter Android do GoTrendLabs esta pronto para a primeira rodada de desenvolvimento e demonstracao.

## Validacao de ambiente

Deve passar:

- `flutter doctor -v` com Android toolchain valido
- `flutter devices` listando emulador Android quando iniciado
- `flutter emulators` listando `gotrendlabs_pixel`
- `flutter pub get`
- `flutter analyze`
- `flutter test`

Alerta de Xcode/CocoaPods nao bloqueia Android MVP.

Para simulacao iOS local, tambem deve passar:

- `flutter doctor -v` com Xcode completo ativo
- CocoaPods disponivel
- `flutter devices` listando um iOS Simulator
- app executado com bases locais via `127.0.0.1`

## Revisao por skills

Antes de encerrar qualquer fatia mobile:

- `gotrendlabs-mobile-docs-governor` confirma workflow, status, changelog, integration map e README.
- `gotrendlabs-mobile-architect` confirma fronteiras e estrutura Flutter.
- `gotrendlabs-mobile-api-contract-guard` confirma contratos, OpenAPI e erros.
- `gotrendlabs-mobile-ux-designer` confirma direcao visual e inspiracao sem copia literal.
- `gotrendlabs-mobile-test-strategy` confirma cobertura e comandos de validacao.
- `gotrendlabs-mobile-flutter-implementer` confirma build, execucao e pendencias de codigo quando houver implementacao.

## Validacao de build

Deve passar:

- app compila em modo debug para Android
- app compila em modo release para Android quando `apps/mobile/android/key.properties` esta configurado localmente
- build release falha explicitamente sem `apps/mobile/android/key.properties`
- app abre no emulador `gotrendlabs_pixel`
- app nao trava quando a API local esta indisponivel
- app exibe erro recuperavel quando `http://10.0.2.2:8001` nao responde
- app consulta `GET /health` ao abrir e mostra tela de manutencao quando a API falha, fica degradada ou retorna `maintenance.mobile_enabled=true`
- tela de manutencao mobile segue o design dark-first, tem mensagem operacional e `Tentar novamente`, sem entrada operacional visivel
- em manutencao mobile, usuarios publicos, staff e superusers permanecem bloqueados no shell mobile
- APK beta de producao usa `https://gotrendlabs.com.br/api` e `https://gotrendlabs.com.br`; FCM depende de `google-services.json` local no build e backend com provider `fcm`

## Validacao de distribuicao beta

Deve passar:

- nao existe pagina publica dedicada `/app/android/`
- rodape, telas de acesso e paginas de compartilhamento renderizam estado "Android em breve" sem link quebrado quando nao ha release ativa
- rodape, telas de acesso e paginas de compartilhamento apontam direto para o APK ativo quando ha release publicada
- estado `iOS em breve` aparece ao lado do Android, sem link baixavel
- `/app/android/latest.json` retorna metadados corretos da release ativa
- Admin Ops em `/admin-ops/mobile-releases/` aceita apenas staff
- upload Admin Ops calcula SHA-256 e tamanho do APK no servidor
- publicar uma release Android ativa desativa a anterior
- Caddy roteia `/api/*` para `fastapi:8001` removendo o prefixo `/api`
- smoke em producao confirma `/api/health`, rodape/login/cadastro/compartilhamento com link direto, download HTTPS do APK e checksum do arquivo baixado

## Smoke test manual

Com backend local ativo:

1. Abrir app no emulador.
2. Ver tela `Hoje`.
3. Ver ao menos um mercado aberto vindo da API em destaque/tendencias.
4. Abrir detalhe de mercado.
5. Ver acoes de favoritar, curtir e compartilhar no detalhe.
6. Alternar entre `Visao geral` e `Comunidade`.
7. Voltar para lista.
8. Abrir aba `Mercados`.
9. Aplicar filtro de categoria.
10. Alternar recortes `Todos`, `Favoritos` e `Posições`.
11. Abrir uma acao autenticada como visitante e ver CTA de login.

## Fluxo autenticado

Quando houver usuario de teste:

1. Fazer login.
2. Abrir `GET /users/me` via app.
3. Ver perfil resumido.
4. Favoritar um mercado.
5. Curtir um mercado.
6. Abrir mercado aberto.
7. Selecionar uma opcao explicitamente.
8. Informar stake educativo.
9. Chamar preview.
10. Confirmar previsao.
11. Ver saldo/estado atualizado pela resposta da API.
12. Ver o mercado favoritado no recorte `Favoritos`.
13. Ver o mercado com previsão no recorte `Posições`.
14. Ver atalhos de `Sua mesa` na tela `Hoje` quando houver favoritos ou posições.
15. Abrir `Sobre` e conferir versão/build, saúde da API e diagnóstico seguro sem endereço de endpoint.
16. Fazer login com `Lembrar login` ligado e validar restauracao da sessao pelo token seguro.
17. Fazer login com `Lembrar login` desligado e validar que o token nao fica persistido para reabertura futura.
18. Ativar `Proteger sessao com biometria`, fechar/reabrir o app e validar que a sessao so restaura apos biometria ou senha do aparelho.
19. Cancelar o desbloqueio local e validar que o app nao chama endpoint autenticado, nao apaga o token persistido e mostra `Sessao protegida` com acoes de desbloquear ou sair deste dispositivo.
20. Validar que cadastro com protecao local ligada por padrao tambem salva a preferencia e que a tela de entrada mostra `Entrar com biometria` quando houver sessao lembrada protegida.

## Fluxo de manutencao mobile

Deve validar:

- Admin Ops Config salva `Manutenção do app` independentemente do modo manutencao web
- `/health` retorna `maintenance.mobile_enabled` e `maintenance.mobile_message`
- app com backend indisponivel mostra a tela de manutencao, sem crash
- app com manutencao mobile ativa mostra a tela de manutencao antes do shell
- usuarios publicos, staff e superusers permanecem na tela de manutencao, sem entrada operacional visivel
- sessao lembrada protegida continua exigindo biometria/senha local apenas quando o backend voltar a um estado saudavel

## Fluxo de previsao bloqueada

Deve validar:

- visitante nao consegue prever sem login
- usuario sem email confirmado ve bloqueio apropriado quando aplicavel
- mercado locked/resolved/canceled nao permite previsao
- previsao duplicada mostra erro claro
- saldo insuficiente mostra erro claro
- app nao altera saldo localmente quando API rejeita

## Fluxo de comentarios

Deve validar:

- visitante le comentarios e ve CTA de login para comentar
- usuario autenticado cria comentario
- comentario aparece apos sucesso da API
- like/dislike sao mutuamente exclusivos
- comentario de IA oficial exibe selo quando contrato indicar

## Wallet e reputacao

Deve validar:

- saldo vem da API
- extrato mostra labels humanos
- app nao usa linguagem de dinheiro real
- reputacao/ranking/badges sao exibidos como leitura da API
- app nao calcula elegibilidade de badge

## Testes automatizados minimos

### Unitarios

- formatacao de GTL/GT₵
- formatacao de probabilidade inteira e decimal
- formatacao de datas de fechamento/resolucao
- mapeamento de erros de API para estados de UX

### Widget tests

- `MarketHeroCard`
- `MarketCompactCard`
- `TodayScreen` excluindo mercados fechados em destaque/tendencias
- grafico de consenso multi-serie por opcao
- `MarketMetricPanel`
- recortes `Favoritos` e `Posições` em `MarketsScreen`
- `AboutScreen`
- `PredictionTicket`
- `RankingScreen` exibindo `@handle`, badges e overflow `+N`
- estado informativo de push em `Sobre`, ausente em Perfil e Alertas
- `CommentItem`
- estados `loading`, `empty`, `error` e `unauthenticated`

### Repository tests

- feed de mercados
- detalhe de mercado
- preview de previsao
- criacao de previsao
- favoritos/curtidas
- comentarios
- wallet
- badges autenticadas em resposta de lista na raiz
- suporte/feedback
- sugestao de mercado
- protecao biometrica local: preferencia persistida, cancelamento sem ativar token, desbloqueio ativando token em memoria e sem armazenamento de senha

### Integration tests

- feed -> detalhe -> voltar
- visitante tenta prever -> login CTA
- login -> detalhe -> preview de previsao
- perfil -> badges/reputacao/ranking
- menu -> suporte/feedback
- menu -> sugerir mercado
- perfil -> sugerir mercado
- erro de API -> retry
- sem Firebase configurado, push nao registra token real
- token fake registra dispositivo apos autenticacao
- revoke explicito chama `DELETE /users/me/push-devices/{device_id}`
- sessao lembrada protegida exige biometria ou senha do aparelho antes de chamar `GET /auth/session`

## QA visual

Antes de considerar a UI pronta:

- testar viewport do emulador padrao Pixel
- capturar screenshot de `Hoje/Mercados` e detalhe de mercado
- testar fonte ampliada
- testar textos longos de mercado
- testar imagem ausente
- testar fallback iconizado/neutro de mercado quando `image_url` e `thumb` vierem vazios, sem iniciais geradas a partir da categoria
- confirmar que `thumb` cadastrado aparece tambem quando houver thumbnail de mercado
- confirmar que `thumb` cadastrado nao aparece sobreposto quando `image_url` de mercado estiver disponivel
- confirmar que o ticket de previsao replica o preview web com `Opcao escolhida`, `Credito possivel se acertar` e `Credito reservado`, atualizando o retorno pelo backend ao mover o controle
- confirmar que usuario com posicao ativa ve escolha atual, movimentos ativos, total ativo, credito possivel, aumentos/trocas restantes e historico resumido no detalhe mobile
- confirmar que `Aumentar posição` e `Trocar escolha` aparecem sempre como frames fechados, inclusive quando apenas uma acao estiver disponivel, com resumo curto e contador/bloqueio no cabecalho
- confirmar que `Aumentar posição` usa `/position-preview` e `/position-actions`, abre a mesma opcao ativa, exige preview valido e mostra novo total ativo e aumentos restantes retornados pela FastAPI
- confirmar que `Trocar escolha` usa `/position-preview` e `/position-actions`, abre apenas opcoes diferentes da ativa, exige preview valido e mostra movimentos encerrados, custo da troca, nova posicao estimada e trocas restantes retornadas pela FastAPI
- confirmar que bloqueios de aumento/troca por limite, cutoff, flag, saldo, sessao ou status do mercado exibem mensagens retornadas pelo backend
- confirmar que o bottom sheet de confirmacao de previsao nao estoura em aparelho fisico, viewport compacto ou fonte ampliada
- confirmar que o ticket de previsao mostra `Disponível` e `Bloqueado` vindos da wallet da API antes da escolha/stake
- confirmar que contador de comentarios em cards e metricas abre `/markets/:slug?tab=community`
- confirmar que o detalhe mostra pergunta/contexto completo fora do hero truncado
- confirmar que mercado auto-close vencido aparece como `Fechado` no mobile e bloqueia preview/criacao/reforco/revisao pela FastAPI
- confirmar que alertas de comentario abrem o mercado direto na aba `Comunidade`
- confirmar que a wallet prioriza `Disponível` e `Bloqueado`, mantendo recarga controlada com elegibilidade, pendencia, historico e criacao via API como secao secundaria
- confirmar que Hoje/Mercados/Busca, detalhe de mercado, Wallet e Alertas reconsultam a FastAPI ao entrar, voltar do background ou usar pull-to-refresh, sem exigir encerrar e abrir o app para atualizar status ou saldo
- confirmar que o acesso a perfil usa icone neutro, sem parecer acao de sair
- confirmar que perfil mostra dados de perfil, reputacao, badges conquistadas, catalogo de badges e convite
- confirmar que o menu segue a ordem Wallet, Badges, Suporte, Sugerir mercado, Política e segurança, Sobre e Sair quando autenticado
- confirmar que sugestao de mercado segue acessivel pelo Perfil
- confirmar que sugestao de mercado segue acessivel pelo menu principal
- confirmar que cadastro, feedback e sugestao de mercado como visitante exibem desafio anti-abuso dentro do app e enviam `anti_abuse_token`/`anti_abuse_answer` para a FastAPI
- confirmar que feedback/sugestao autenticados nao exigem desafio anti-abuso
- confirmar que politica de uso, conceitos e seguranca estao acessiveis no menu e perfil
- confirmar que sugestao de mercado carrega categorias ativas da taxonomia
- confirmar que feedback usa as opcoes da web sem seletor de prioridade, valida nome/email para visitante e mostra erro inline quando a API bloquear o envio
- confirmar que compartilhamento aparece no hero ao lado de favoritar/curtir
- confirmar que abrir detalhe mobile incrementa `view_count` via `POST /markets/{slug}/view`
- confirmar que compartilhar pelo app incrementa `share_count` via `POST /markets/{slug}/share`
- confirmar que o detalhe nao repete o titulo do mercado logo abaixo do hero
- confirmar que o ticket de previsao aparece antes do criterio de resolucao no detalhe
- confirmar que erros de validacao aparecem em linguagem final, sem payload tecnico da API
- confirmar que `Sobre` mostra o estado informativo de push como item de saude/configuracao quando Firebase não está configurado
- confirmar que Perfil e Alertas nao mostram painel operacional de push
- confirmar que logout normal não revoga dispositivo de push
- confirmar que revogação de dispositivo ocorre apenas por ação explícita
- confirmar que payloads de push abrem rotas e refazem fetch na FastAPI quando FCM real estiver habilitado
- confirmar que o login sheet mostra `Sessao protegida` com acoes claras quando o desbloqueio local for cancelado
- confirmar que Perfil mostra `Protecao local` e explica que a proxima abertura usa biometria ou senha do aparelho
- confirmar que ranking permite filtrar por categoria, subcategoria e evento como na web
- confirmar que ranking identifica usuarios pelo `@handle`, nao pelo nome publico, e mostra ate 3 badges com `+N`
- testar mercado sem comentarios
- testar mercado resolvido
- testar erro de rede
- testar tema dark como padrao
- confirmar que tema, app shell, cards, detalhe, ticket, wallet, ranking, alertas, busca, perfil, badges e bottom sheets usam o mesmo design system dark-first/editorial, sem cards genéricos ou estados soltos
- confirmar que `Mercados` permite alternar `Todos`, `Favoritos` e `Posições`, com estados vazios claros quando não houver itens
- confirmar que `Hoje` exibe `Sua mesa` para usuário autenticado com favoritos/posições e abre `Mercados` no recorte escolhido
- confirmar que `Hoje` nao exibe mercados fechados em destaque/tendencias e prioriza mercados abertos com mais engajamento
- confirmar que cards exibem prazo restante compacto sem aumentar a altura atual e que a barra muda de cor conforme o fechamento se aproxima
- confirmar que tocar no hero de imagem dentro do detalhe nao empilha a mesma tela novamente
- confirmar que cards sinalizam `Favorito` e `Sua posição` quando a API retornar os flags do usuário autenticado
- confirmar que `Sobre` aparece no menu e perfil, mostra versão/build, saúde da API e copia diagnóstico sem token, senha, segredo, ID interno ou endereço de API
- comparar contra a direcao das referencias visuais fornecidas pelo usuario: card destaque, detalhe com hero, abas, painel de metricas e bottom navigation

## Criterios de aceite finais do MVP

- app Android abre e navega sem crash
- feed e detalhe consomem FastAPI local
- fluxo visitante e fluxo autenticado estao separados claramente
- previsao so e criada por sucesso da API
- wallet, reputacao e badges sao leitura do backend
- UI segue a direcao dark-first definida em `mobile-ux.md`
- nenhuma regra critica foi duplicada no app
