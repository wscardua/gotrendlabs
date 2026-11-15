# Google Play — solicitação de acesso à produção, 15/11/2026

## Estado vigente

Solicitação enviada a pedido explícito do titular. Em 15/11/2026, por volta de12:07 de São Paulo (15:07UTC), o Dashboard confirmou `Application submitted`, `We have your application for production access` e `Applied today, 12:07 PM`. Google informa análise usual em até sete dias, eventualmente mais, com atualização por email ao titular. Canal Production permanece `Inactive`; não houve rollout público.

App: `br.com.gotrendlabs.gotrendlabs_mobile`. [Dashboard](https://play.google.com/console/u/0/developers/5780321057759640239/app/4973661897857186052/app-dashboard). O usuário informou aprovação/publicação da versão20 no teste fechado antes da solicitação. Essa informação é relato do titular; a verificação desta execução confirmou requisitos completos e recebimento da solicitação de acesso, sem consultar novamente o estado da release20.

## Execução e informações submetidas

- Acesso nativo CUA ao Google Chrome logado; botão Apply for production habilitado, com os três requisitos de teste fechado marcados completos pela Console.
- Formulário tinha respostas salvas sobre recrutamento por amigos/colegas, engajamento/feedback, público adulto, valor do app, estimativa0–10mil instalações, melhorias de navegação/estados e prontidão. Esses campos foram preservados; não foram inventadas estatísticas, novos relatos de testadores ou métricas de engajamento.
- Somente a quarta etapa, Additional testing, estava vazia. Texto submetido (226/300 caracteres):

> In the latest iteration, we corrected the New label to use publication time and expire after 48 hours. We ran 141 Flutter tests and static analysis, validated the signed bundle, and distributed build 20 through closed testing.

- Esse texto se baseia nas mudanças e validações comprovadas no [recibo20](../testing/mobile-new-publication-release-20-20261115.md). Testes automatizados não foram apresentados como testes humanos ou prova de engajamento.
- Apply acionado e retorno Application submitted observado. Nenhum termo novo, credencial, configuração produtiva, país/testador, build mínimo, AAB, APK do site ou canal de distribuição foi alterado.

## Limites e retomada

Solicitação concluída; aprovação do acesso à produção ainda depende da Google. Mesmo uma futura aprovação não significa publicar automaticamente a versão no track público. Quando a decisão chegar, consultar o estado real da Console e seguir o fluxo de release autorizado pelo titular. Não reenviar a solicitação já recebida sem verificar seu estado.

Sem novo código, build ou teste de instalação/MFA/push. Fonte e checksum do AAB20 permanecem os do recibo. Branch de release e checkout original preservados. Evidência desta operação: estado acessível observado na Console e este recibo; não há alegação de aprovação do pedido.

MCP: ferramentas, schemas/contratos, permissões, erros/replays e orientação editorial não mudam. Trata-se de solicitação operacional do titular na loja, sem novo poder de domínio ou permissão derivada do Admin Ops. Sem ADR, migration ou mudança de configuração de backend.

Registro documental: PR [#217](https://github.com/wscardua/gotrendlabs/pull/217), descrição aprovada pelo titular antes da submissão. Alterações apenas documentais, sem nova implantação de runtime.
