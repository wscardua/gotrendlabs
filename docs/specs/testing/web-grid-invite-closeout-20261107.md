# Fechamento — convite contextual da grade web

## Estado vigente

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
