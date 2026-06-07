---
id: TEST-MOBILE-001
titulo: "Criterios de aceite mobile"
versao: 0.1
status_spec: draft
status_impl: nao_iniciada
ultima_atualizacao: 2026-06-07
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
- app abre no emulador `gotrendlabs_pixel`
- app nao trava quando a API local esta indisponivel
- app exibe erro recuperavel quando `http://10.0.2.2:8001` nao responde

## Smoke test manual

Com backend local ativo:

1. Abrir app no emulador.
2. Ver tela `Hoje`.
3. Ver ao menos um mercado vindo da API.
4. Abrir detalhe de mercado.
5. Alternar entre `Visao geral` e `Comunidade`.
6. Voltar para lista.
7. Abrir aba `Mercados`.
8. Aplicar filtro de categoria.
9. Abrir uma acao autenticada como visitante e ver CTA de login.

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

### Integration tests

- feed -> detalhe -> voltar
- visitante tenta prever -> login CTA
- login -> detalhe -> preview de previsao
- erro de API -> retry

## QA visual

Antes de considerar a UI pronta:

- testar viewport do emulador padrao Pixel
- capturar screenshot de `Hoje/Mercados` e detalhe de mercado
- testar fonte ampliada
- testar textos longos de mercado
- testar imagem ausente
- testar mercado sem comentarios
- testar mercado resolvido
- testar erro de rede
- testar tema dark como padrao
- comparar contra a direcao das referencias visuais fornecidas pelo usuario: card destaque, detalhe com hero, abas, painel de metricas e bottom navigation

## Criterios de aceite finais do MVP

- app Android abre e navega sem crash
- feed e detalhe consomem FastAPI local
- fluxo visitante e fluxo autenticado estao separados claramente
- previsao so e criada por sucesso da API
- wallet, reputacao e badges sao leitura do backend
- UI segue a direcao dark-first definida em `mobile-ux.md`
- nenhuma regra critica foi duplicada no app
