# Fechamento — convite contextual da grade web

## Estado final — integrado e implantado

Feature concluída em produção em 07/11/2026. PR [#205](https://github.com/wscardua/gotrendlabs/pull/205), com título/descrição aprovados pelo usuário antes da abertura, integrada à main em `4b9b8a5dd7197b22a00f2954e452b85899e065c2`. Código do convite, correção acessível de Categorias e atualização dos smoke tests fazem parte desse merge.

- CI da PR: [42417621167](https://github.com/wscardua/gotrendlabs/actions/runs/42417621167), sucesso; 683 testes Python/três skips em 323,518s. Builds de produção/MCP, OpenAPI, seleção do convite e demais regressões JS aprovados.
- CI/main e deploy: [42418237208](https://github.com/wscardua/gotrendlabs/actions/runs/42418237208), sucesso; 683 testes/três skips em 435,269s. Todos os jobs concluídos, incluindo build e deploy.
- Implantação SSM `8cba2537-c7b2-4825-bd76-046b5d1d80a8`: Success/código 0, encerrada em 07/11 às 22:07:52 UTC (19:07:52 em Brasília).
- Verificação read-only SSM `55bf9d14-2b3b-4347-a42d-68440aa76675`: Success/código 0; HEAD produtivo igual ao merge, sem alterações em arquivos versionados. Django, FastAPI, daemon, proxy e thumbnail-worker em execução; MCP em execução/healthy.
- Publicação feita pelo fluxo existente e collectstatic. Sem migração da feature, flag, configuração adicional ou ajuste de dados em produção. Banco/fixtures DEV não foram transportados.
- Branch local `feature/web-market-grid-invite` e checkout original preservados. Esta conclusão substitui os estados de preparação mantidos abaixo como histórico.

## Smoke produtivo

Verificação em https://gotrendlabs.com.br em 07/11/2026 às 22:08 UTC (19:08 em Brasília), Chrome desktop com viewports 1366/1000/390. Sessões de inspeção desativaram analytics no próprio navegador; não houve mutação de domínio, criação de mercados, previsões ou permissões.

- `/api/health`: 200; API/database ok.
- Nove assets públicos (CSS, três scripts e cinco SVGs): 200, SHA256 idêntico aos arquivos integrados. [Relatório com checksums](evidence/web-grid-invite-20261107/production/report.json).
- Catálogo público real: quatro open, cinco locked e seis sealed; nenhuma fixture qa-visual presente.
- Grade principal com quatro open: convite visível em duas colunas no desktop. Apuração conserva seus cinco mercados e não recebe convite.
- As cinco opções conferidas nos dois temas, total de dez capturas; conteúdo/destinos corretos. A escolha foi forçada somente na memória das sessões de QA para cobrir todos os intervalos, sem override ou parâmetro novo no produto.
- Quinze cenários de largura (cinco opções × 1366/1000/390): ocupação correta pelas colunas reais, seleção preservada e sem overflow horizontal; com quatro mercados, convite oculto nos layouts de duas/uma coluna.
- Clique em Ver resultados aciona o filtro existente e mostra os seis sealed; a grade completa não recebe convite. As cinco rotas de destino respondem 200. Sem erros JavaScript.
- [Captura produtiva clara](evidence/web-grid-invite-20261107/production/light.png) e [escura](evidence/web-grid-invite-20261107/production/dark.png) revisadas visualmente, com as thumbnails reais carregadas. Demais capturas ficam em `.runtime/closeout/production-evidence/`.

Limites: a amostra produtiva observada não tem cinco abertos, resolved ou mais de 18 itens por seção; cenários de 0–8, paginação, resolved e HTMX seguem cobertos pelo aceite local e CI aplicável, sem modificar dados PRD para reproduzi-los. Safari/Firefox/aparelhos físicos não exercitados. Sem storage, impedir repetição entre documentos continua best effort. Nenhuma pendência funcional desta fatia; FEAT-MARKET-001 ampla permanece parcial por lacunas independentes.

MCP confirmado sem ajuste: tools, schemas, contratos, permissões, erros, replays e orientação editorial preservados. Flutter, seus contratos e documentação não foram alterados; esta implantação não distribui novo APK/AAB/iOS.

## Histórico da preparação

Os registros abaixo preservam os estados anteriores. Para disponibilidade e fechamento, prevalecem o estado final e as evidências produtivas acima.

## Estado registrado antes da reexecução do CI

07/11/2026: implementação e correção de review **commitadas/testadas localmente** na branch `feature/web-market-grid-invite`, baseada na main remota `d93d5b918cba0b9802dfc2900b5882700b3d9030`. Commits de código: `1fd83a0` e `68b60c4e5a0e72e015ff60ed92462b77783759ec`.

PR [#205](https://github.com/wscardua/gotrendlabs/pull/205) aberta após aprovação explícita do usuário. O primeiro CI remoto [42416671503](https://github.com/wscardua/gotrendlabs/actions/runs/42416671503) executou 683 testes/três skips e detectou dois testes de home acoplados à tag HTML exata; a correção preserva a verificação de ausência de mercados cancelados sem depender dos atributos da grade. Quatro testes Django selecionados passaram em PostgreSQL 16 isolado. Reexecução do CI, integração à main e implantação em produção ainda pendentes. Esse estado prevalece sobre a conclusão restrita ao escopo local de WFLOW-20261107-WEB-GRID-INVITE. Fechamento/publicação acompanhados em WFLOW-20261107-WEB-GRID-INVITE-CLOSEOUT.

## Comportamento e fontes da verdade

- [Spec do feed v0.17](../features/market-feed.md#convite-contextual-na-grade-web-v017): um convite nos espaços restantes da grade principal, sem alterar cards ou apuração; cinco conteúdos/rotas existentes, estado estável por visita e histórico opcional protegido.
- [Aceite e capturas](web-grid-invite-acceptance-20261107.md): cenários de 4/5 mercados em claro/escuro e matriz de 0–8 em três/duas/uma coluna.
- [Review final](web-grid-invite-branch-review-20261107.md): risco baixo, sem findings abertos; regressão de acessibilidade de Categorias corrigida com cobertura Node/navegador.
- [Mapa de integração](../state/integration-map.md): apenas navegação web entre superfícies existentes, sem novo serviço ou contrato.
- FEAT-MARKET-001 ampla permanece parcial por lacunas independentes; o convite web está implementado, validado e preparado para integração.

## Validação local e dados de simulação

Dois testes Django, quatro scripts Node (sorteio, filtros/acessibilidade, analytics e prediction preview), suite de navegador completa e checks Django/OpenAPI/JS/YAML/diff aprovados. O CI passa a executar também o teste de sorteio, além da suíte Django e regressões já existentes.

A pedido do usuário, os serviços locais foram reiniciados apontando para este worktree e o banco DEV foi preparado para quatro mercados abertos e cinco resolvidos/selados efetivamente renderizados. Só fixtures sintéticas sem previsões, definição assinada ou eventos de integridade foram temporariamente retiradas da vitrine. Backup/restauração em `.runtime/dev/grid-invite-market-status-backup.json` e `.runtime/dev/configure_grid_invite_markets.py`; arquivos ignorados, não entram no commit nem em produção. Mercados existentes fora da fixture e dados críticos preservados.

## Publicação e ativação previstas

1. Mostrar ao usuário título e descrição da PR em português e aguardar autorização antes da abertura.
2. Abrir a PR pelo MCP GitHub sobre `main`; acompanhar o workflow GoTrendLabs CI and Deploy e resolver eventuais falhas.
3. Integrar somente com os checks aprovados; preservar a branch local.
4. Acompanhar o workflow da main, build de imagens, deploy SSM e smoke pós-merge. Confirmado `ENABLE_PROD_DEPLOY=1` na preparação.
5. Conferir home/templates, versões e conteúdo dos scripts/CSS, cinco SVGs, recortes, temas e responsividade em produção. O convite só aparece se sobrar espaço após a paginação; uma página inicial cheia de 18 cards deve permanecer sem convite.
6. Registrar PR, commit de merge, runs, resultado de implantação e smoke neste recibo e no estado operacional, distinguindo cada etapa.

O deploy existente executa `collectstatic` e publica os assets. **Não são necessárias migrations, alterações de banco/dados, flags ou configurações extras.** Fixtures não serão copiadas para produção. Não há novo serviço, analytics, Admin Ops ou dependência de runtime.

## MCP, mobile e limites

Tools, schemas, contratos, permissões, erros, replays e política/orientação editorial MCP permanecem iguais. O convite apenas encaminha aos fluxos web já existentes; não aprova/publica sugestões nem infere permissões de ações humanas.

App Flutter, seus contratos e documentação não foram alterados. A entrega web não requer release Android/iOS. Validação local de navegador em Chrome, sem aparelhos físicos ou Safari/Firefox; sem storage, prevenção de repetição entre visitas não é garantida. Traduções completas seguem FEAT-I18N-001 e não são requisito novo desta fatia.

## Correção do primeiro CI da PR

Os dois `IndexError` em test_home_does_not_render_canceled_markets e test_market_pages_consume_api_and_fallback_to_fixture vieram do split pela tag antiga da grade, agora com atributo adicional. A correção usa assertNotContains na resposta, reforçando a ausência de mercados cancelados em toda a página. Não houve alteração adicional de runtime, API, banco, MCP ou mobile. Quatro testes selecionados (os dois smoke + dois do convite) passaram em banco de teste isolado em 127.0.0.1:15439, sem tocar o DEV operacional.
