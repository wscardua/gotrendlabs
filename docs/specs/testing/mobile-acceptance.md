---
id: TEST-MOBILE-001
titulo: "Criterios de aceite mobile"
versao: 0.2
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-06-08
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
- APK beta de producao usa `https://gotrendlabs.com.br/api`, `https://gotrendlabs.com.br` e `GTL_PUSH_FIREBASE_ENABLED=false`

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
3. Ver ao menos um mercado vindo da API.
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
- `MarketMetricPanel`
- recortes `Favoritos` e `Posições` em `MarketsScreen`
- `AboutScreen`
- `PredictionTicket`
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

### Integration tests

- feed -> detalhe -> voltar
- visitante tenta prever -> login CTA
- login -> detalhe -> preview de previsao
- perfil -> badges/reputacao/ranking
- menu -> suporte/feedback
- menu -> sugerir mercado
- erro de API -> retry
- push noop nao registra token
- token fake registra dispositivo apos autenticacao
- revoke explicito chama `DELETE /users/me/push-devices/{device_id}`

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
- confirmar que a wallet mostra recarga controlada com elegibilidade, pendencia, historico e criacao via API
- confirmar que o acesso a perfil usa icone neutro, sem parecer acao de sair
- confirmar que perfil mostra dados de perfil, reputacao, badges conquistadas, catalogo de badges e convite
- confirmar que suporte/feedback e sugestao de mercado estao acessiveis no menu com icones
- confirmar que politica de uso, conceitos e seguranca estao acessiveis no menu e perfil
- confirmar que sugestao de mercado carrega categorias ativas da taxonomia
- confirmar que feedback usa as opcoes da web sem seletor de prioridade
- confirmar que compartilhamento aparece no hero ao lado de favoritar/curtir
- confirmar que o detalhe nao repete o titulo do mercado logo abaixo do hero
- confirmar que o ticket de previsao aparece antes do criterio de resolucao no detalhe
- confirmar que erros de validacao aparecem em linguagem final, sem payload tecnico da API
- confirmar que a seção de push em Alertas/Perfil mostra estado preparado/noop quando Firebase não está configurado
- confirmar que logout normal não revoga dispositivo de push
- confirmar que revogação de dispositivo ocorre apenas por ação explícita
- confirmar que payloads de push abrem rotas e refazem fetch na FastAPI quando FCM real for habilitado
- confirmar que ranking permite filtrar por categoria, subcategoria e evento como na web
- testar mercado sem comentarios
- testar mercado resolvido
- testar erro de rede
- testar tema dark como padrao
- confirmar que tema, app shell, cards, detalhe, ticket, wallet, ranking, alertas, busca, perfil, badges e bottom sheets usam o mesmo design system dark-first/editorial, sem cards genéricos ou estados soltos
- confirmar que `Mercados` permite alternar `Todos`, `Favoritos` e `Posições`, com estados vazios claros quando não houver itens
- confirmar que `Hoje` exibe `Sua mesa` para usuário autenticado com favoritos/posições e abre `Mercados` no recorte escolhido
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
