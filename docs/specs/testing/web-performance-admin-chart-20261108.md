# Correção — gráfico pessoal de administradores

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
