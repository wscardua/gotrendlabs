# Correção — gráfico pessoal de administradores

## Estado final — integrado e implantado

Correção autorizada após diagnóstico com screenshot produtivo. PR [#209](https://github.com/wscardua/gotrendlabs/pull/209) aberta/mergeada pelo MCP GitHub após aprovação explícita da descrição, integrada em `6dde14010f58002adff24ca9eb3d4d752b4db6bf`. Commit funcional `eaebb0a49da1d62cb767bfb11ed5c2a0cfb31445`. Branch local `fix/web-performance-admin-chart`, demais branches e alterações do checkout original preservadas.

- CI da PR [42485739272](https://github.com/wscardua/gotrendlabs/actions/runs/42485739272): sucesso; 700 testes Python em 427,626 s, OK/3 skips, builds principal/MCP, OpenAPI e quatro checks JavaScript aprovados.
- CI/main e deploy [42486520746](https://github.com/wscardua/gotrendlabs/actions/runs/42486520746): sucesso em todos os jobs; 700 testes em 372,306 s, OK/3 skips, builds/checks e implantação aprovados.
- SSM `bf43a08a-dadc-4716-9edc-1f4f3a33b8cd`: Success/0; deploy concluído em 08/11 às 13:56:36 UTC (10:56:36 de Brasília).
- Conferência SSM `13776ce0-f814-4e03-b559-122507d7723a`: Success/0; commit produtivo igual ao merge, checkout limpo, rota performance registrada e quatro hashes de template/view/CSS/JS idênticos ao código integrado. Seis serviços running, MCP healthy. IDs das imagens e checksums no [relatório](evidence/web-performance-admin-chart-20261108/production/report.json).
- Conferência anterior SSM `c7525237-7688-4a3c-8077-4e9a9c376c7a`: checkout limpo no commit produtivo anterior b499dc5 e seis serviços ativos. Main anterior acrescentava somente documentação; nenhuma divergência funcional não reconciliada.
- Sem migration, flag, configuração, carga de dados ou nova permissão para ativação. Somente condição de template; mesmo agregado FastAPI e mesma sessão. Nenhuma fixture/credencial local distribuída.

## Smoke autenticado em produção

Chrome nativo, sessão administrativa já existente, `/desempenho/`. Antes do deploy, ausência do gráfico com histórico real confirmada. Depois do deploy, página recarregada e **gráfico pessoal visível nos temas claro e escuro**, com deltas e links dos mercados do histórico pessoal; placar continua oculto e mensagem administrativa permanece.

Capturas observadas e árvore de acessibilidade confirmam barras positivas/negativas e rótulos textuais. Não houve criação de conta, previsão, mercado ou dado de teste, nem concessão de permissão. Tema e aba originais restaurados após QA. Nenhuma credencial ou payload pessoal foi incluído no relatório versionado. Esse smoke supera a limitação anterior de acesso ao navegador para o caso administrativo desta correção.

## Smoke HTTPS e limites

- `/api/health`: 200, API/database ok.
- Visitante em `/desempenho/`, inclusive com query de identidade: 302 para login com retorno seguro e private/no-store.
- API sem token ou com token inválido: 401.
- CSS/JS: 200 e SHA256 exato; ranking público: 200.
- Sem Safari/Firefox/aparelho físico. Celular e dois temas cobertos pela matriz local de 54 cenários. Nenhuma pendência funcional/produtiva desta correção; este recibo consolida sua publicação.

Spec FEAT-REP-001 v0.9, arquitetura, workflow, status, changelogs e lacunas reconciliados. Feature ampla permanece parcial/draft. MCP sem ajuste de ferramentas, schemas, contratos, autenticação, permissões, erros, replays/editorial; mobile/API/domínio preservados. Nenhuma permissão inferida de ações humanas do Admin Ops. Regra de ranking público inalterada.

## Histórico da preparação local

WFLOW-20261108-WEB-PERFORMANCE-ADMIN-CHART / FEAT-REP-001 v0.9. Branch `fix/web-performance-admin-chart`, base remota main `46e2ec9af994ab5d6d09d05476075a77910b65d2`, worktree isolado. Implementação testada localmente e commitada na branch de trabalho; integração e publicação ainda pendentes.

## Problema e regra corrigida

Screenshot produtivo de @admin confirmou histórico próprio preenchido e ausência do gráfico, enquanto a mensagem de exclusão do placar era exibida. O template usava `reputation_chart and show_performance_scorecard`; a segunda condição excluía staff/superuser mesmo com dados autorizados.

A condição passa a depender de `reputation_chart`. Administradores e superusuários veem somente os impactos das próprias resoluções retornados pelo agregado da API, assim como o histórico já visível. Placar administrativo e ranking público mantêm as regras anteriores. Vazio/falha não ganham dados fictícios. Não há mudança de view, dados, API, domínio ou autenticação.

## Validação

- Regressão reproduzida antes da correção: teste novo falhou para is_staff e is_superuser por ausência do gráfico.
- Após a correção: 17 testes Django específicos aprovados, incluindo gráfico para os dois papéis sem placar, deltas/links e token pessoais, vazio em usuário comum/staff/superuser/bot e falhas 403/503 administrativas. Regressões existentes de sessão/menu/isolamento/dados/links/Carregar mais preservadas.
- `manage.py check`, export OpenAPI `--check`, sintaxe JavaScript e `git diff --check` aprovados. Snapshot OpenAPI inalterado.
- QA de navegador: **54 cenários aprovados**, 30 existentes mais 24 administrativos (staff/superuser × desktop/celular × dados/vazio/erro × claro/escuro). Gráfico administrativo, ausência do placar, links/deltas, temas, imagens, teclado/foco, Carregar mais, funcionamento sem JS e ausência de overflow/erros JS aprovados. Vinte screenshots locais em `.runtime/performance`; desktop claro/staff e celular escuro/superuser inspecionados visualmente. Sem fixture ou parâmetro novo no produto: role existe apenas no servidor de preview dos testes.

Não foi repetida a suíte Python completa nem o build Docker local para a alteração de uma condição de template; os testes afetados e a matriz de apresentação verificam o comportamento alterado. O fluxo de publicação existente continua exigindo CI completo antes do merge.

## Impacto no MCP e arquitetura

Sem ajuste MCP: ferramentas, schemas, contratos, autenticação, permissões, erros, replays e orientação editorial permanecem iguais. O endpoint existente já autoriza o histórico pessoal da conta administrativa; a correção somente deixa de ocultar sua representação gráfica. Nenhuma nova permissão inferida do Admin Ops. Sem ORM/fallback, cálculos de domínio locais, migration, configuração, ADR ou mudança mobile.

## Publicação e limites

Esta correção ainda não está em produção. É necessário apresentar a descrição da PR e obter a aprovação solicitada pelo usuário antes da abertura, acompanhar CI/merge/deploy e verificar a exibição para conta administrativa com histórico próprio. Branches locais existentes preservadas. QA em Chrome com viewports móveis, sem aparelho físico ou Safari/Firefox; nenhum dado produtivo alterado para teste.
