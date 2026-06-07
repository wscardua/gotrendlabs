---
id: ARCH-MOBILE-001
titulo: "Arquitetura mobile Flutter"
versao: 0.1
status_spec: draft
status_impl: nao_iniciada
ultima_atualizacao: 2026-06-07
origem:
  - docs/specs/architecture/system-overview.md
  - apps/mobile/README.md
contratos_afetados:
  - mobile-api-contracts.md
dependencias:
  - FEAT-AUTH-001
  - FEAT-MARKET-001
  - FEAT-MARKET-002
impacta:
  - future-mobile
  - backend-api
aprovacao: pendente
---

# Arquitetura mobile Flutter

## Objetivo

Definir a primeira arquitetura do app Flutter Android do GoTrendLabs, mantendo o mobile como cliente da FastAPI e preservando as fronteiras de dominio existentes.

## Escopo incluido

- projeto Flutter em `apps/mobile`
- suporte inicial a Android
- consumo dos contratos publicos e autenticados da FastAPI
- sessao/token, preferencias locais e cache leve no dispositivo
- navegacao mobile para feed, detalhe de mercado, previsao, comentarios, wallet, perfil, ranking/badges e alertas
- camada de design system mobile alinhada ao produto

## Escopo excluido

- iOS nesta primeira etapa
- logica critica de dominio no app
- calculo local autoritativo de probabilidade, saldo, payout, reputacao, ranking, badges ou resolucao
- modo offline completo
- streaming em tempo real
- push notification nativo ate haver contrato especifico de notificacao mobile

## Principios

- `backend-api` e a fonte de verdade para dominio, sessao, wallet, reputacao, probabilidade, previsao, comentarios e resolucao.
- `future-mobile` apresenta dados, coleta intencoes do usuario e envia comandos para a FastAPI.
- O app pode manter estado local de UI, filtros, tema, token/sessao, cache de leitura e preferencias de idioma.
- Qualquer numero exibido com implicacao de dominio deve vir do contrato da API ou ser marcado como preview visual nao autoritativo.
- Fallback local mutavel e proibido para previsao, stake, wallet, reputacao, resolucao, badges e auditoria.

## Skills de governanca mobile

Mudancas mobile devem usar as skills locais apropriadas em `tools/skills/gotrendlabs/`:

- `gotrendlabs-mobile-docs-governor`: abrir/fechar workflow, atualizar estado, changelog, integration map, README e memoria operacional.
- `gotrendlabs-mobile-architect`: revisar arquitetura Flutter, estrutura, navegacao, estado, ambiente e fronteiras.
- `gotrendlabs-mobile-api-contract-guard`: revisar endpoints, OpenAPI, payloads, auth e erros.
- `gotrendlabs-mobile-ux-designer`: revisar direcao visual dark-first e aderencia as referencias fornecidas pelo usuario sem copia literal.
- `gotrendlabs-mobile-test-strategy`: revisar criterios de aceite e matriz de testes.
- `gotrendlabs-mobile-flutter-implementer`: criar ou alterar codigo Flutter em `apps/mobile/` quando a implementacao comecar.

Essas skills nao substituem as specs; elas orientam a execucao e a revisao.

## Estrutura alvo

O projeto Flutter deve nascer em `apps/mobile` e manter a organizacao abaixo como direcao inicial:

- `lib/main.dart`: bootstrap do app, tema e providers raiz.
- `lib/app/`: configuracao de app, roteamento, tema, localizacao e ambiente.
- `lib/core/`: cliente HTTP, armazenamento seguro, erros, formatadores e helpers compartilhados.
- `lib/features/auth/`: login, cadastro, recuperacao e contexto do usuario.
- `lib/features/markets/`: feed, filtros, detalhe, favoritos, curtidas e graficos compactos.
- `lib/features/predictions/`: preview e confirmacao de previsao.
- `lib/features/comments/`: leitura, envio e reacoes de comentarios.
- `lib/features/wallet/`: saldo, extrato e recarga educativa quando houver contrato consumivel.
- `lib/features/profile/`: perfil privado, perfil publico e configuracoes basicas.
- `lib/features/ranking/`: ranking, badges e recortes tematicos.
- `lib/features/alerts/`: central de alertas in-app, inicialmente sem push nativo.
- `test/`: testes unitarios e de widgets.
- `integration_test/`: fluxos principais em emulador.

## Ambiente local

- Flutter stable instalado via Homebrew em `/opt/homebrew/share/flutter`.
- Android SDK em `/Users/williamsca/Library/Android/sdk`.
- Emulador local inicial: `gotrendlabs_pixel`.
- No emulador Android, a API local do Mac deve ser acessada por `http://10.0.2.2:8001`, nao por `127.0.0.1`.
- O Django web local pode continuar em `http://127.0.0.1:8000`; o mobile nao deve depender dele para regras de dominio.

## Configuracao de ambiente

O app deve ter configuracao explicita por ambiente:

- `local`: `http://10.0.2.2:8001`
- `device_local`: IP LAN do Mac, usado quando testar em aparelho fisico
- `staging`: futuro ambiente homologado
- `production`: dominio publico da API

Segredos nao devem ser versionados no Flutter. Tokens de sessao devem usar armazenamento seguro do dispositivo quando a estrategia de auth mobile for definida.

## Navegacao

A navegacao inicial deve combinar:

- bottom navigation persistente para areas recorrentes
- stack navigation para detalhe de mercado, previsao, comentarios e perfil
- modal/bottom sheet para confirmacao de previsao e mensagens de erro recuperaveis
- rotas nomeadas para permitir deep link futuro de mercado e badge

Abas iniciais recomendadas:

- `Hoje`: mercados em destaque, tendencias e recortes editoriais
- `Insights`: conteudo explicativo, agentes IA e analises quando houver contrato
- `Mercados`: browse completo com filtros
- `Alertas`: notificacoes in-app e eventos relevantes
- `Busca`: busca e descoberta por categoria/evento

## Estado e cache

O app pode usar gerenciamento de estado adequado ao Flutter, escolhido na implementacao, desde que mantenha:

- repositories por feature para isolar chamadas HTTP
- modelos de resposta alinhados ao OpenAPI versionado
- estados explicitos de `loading`, `refreshing`, `empty`, `error`, `unauthenticated` e `stale`
- cache leve apenas para melhorar leitura e retomar tela
- invalidacao de cache apos mutacoes autenticadas

## Seguranca

- O app nao deve armazenar senha.
- Token/sessao deve ficar em storage seguro quando o contrato mobile de auth for consolidado.
- Logs locais nao podem imprimir token, senha, email privado, dados sensiveis de perfil ou payloads de recuperacao.
- Erros de API devem ser convertidos em mensagens de UX sem expor stack trace.
- Fluxos sensiveis devem tratar sessao expirada com reautenticacao clara.

## Observabilidade

Eventos analiticos futuros devem medir:

- abertura do app
- visualizacao de feed e detalhe
- uso de filtros
- preview de previsao
- confirmacao e erro de previsao
- login/cadastro/recuperacao
- favoritar, curtir e comentar

Analitica nao deve conter dados pessoais sensiveis nem valores que permitam reconstruir wallet privada.

## Responsabilidades por camada

- `future-mobile`: UI, estado de tela, navegacao, validacoes de formulario nao autoritativas, cache leve, exibicao de contratos e envio de comandos.
- `backend-api`: autenticacao, sessao, contratos JSON, validacao de dominio, preview de previsao, mutacoes, wallet, reputacao, badges e resolucao.
- `database`: persistencia e integridade.
- `communications`: emails e notificacoes transacionais.
- `admin-ops`: operacao e auditoria; nao e consumido diretamente pelo app comum.

## Testes esperados

- widget tests para cards de mercado, filtros, detalhe, ticket de previsao e estados vazios
- unitarios para formatacao de GTL, datas, percentuais e mapeamento de erros
- testes de repository com clientes HTTP mockados
- integration tests para abrir feed, navegar ao detalhe e bloquear previsao de visitante
- integration tests para login e previsao quando houver usuario fixture adequado

## Criterios de aceite

- o projeto Flutter compila para Android
- `flutter doctor` mostra Android toolchain valido
- app inicial roda no emulador `gotrendlabs_pixel`
- app consome `GET /markets` local via `10.0.2.2:8001`
- nenhuma regra critica e calculada no app como fonte de verdade
- erros e estados vazios possuem tratamento visual consistente
- workflow, status, changelog e integration map foram atualizados quando houver mudanca multi-documento

## Impacto de mudanca

Mudancas nesta arquitetura podem afetar contratos FastAPI, OpenAPI, estrutura do app Flutter e criterios de teste mobile.
