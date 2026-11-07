# Review de impacto — convite contextual web

## Resumo

- Base: `origin/main` / merge-base `d93d5b918cba0b9802dfc2900b5882700b3d9030`, atualizada por fetch em 07/11/2026.
- Intervalo de código revisado: `d93d5b9...68b60c4e5a0e72e015ff60ed92462b77783759ec`. A preparação documental posterior apenas consolida estas evidências e o estado anterior à PR.
- Escopo: todos os arquivos do diff. Web: home, componente, base, CSS, scripts de convite/tema/analytics e cinco SVGs. Testes: Django, sorteio Node, filtros, navegador e servidor de fixtures read-only. CI: inclusão do teste de sorteio. Documentos: market-feed, estado, aceite e quatro capturas.
- Superfícies afetadas: apresentação web, testes, CI e documentação operacional.
- Mobile não impactado: `apps/mobile/`, documentação/contratos mobile, `apps/api/` e `packages/contracts/` não possuem diff. `/markets`, autenticação, `/health`, manutenção, headers e contratos JSON permanecem iguais; triagem não exige auditoria Flutter.
- MCP: sem mudanças de tools, schemas, contratos, permissões, erros, replays ou orientação editorial. Convite usa rotas web existentes, sem mutação, aprovação automática ou permissão inferida.
- Risco geral: **baixo** após a correção descrita abaixo. CI completo e smoke produtivo continuam pendentes da publicação autorizada.

## Findings

**Nenhum problema identificável no diff.** Não restam findings abertos na revisão final do código.

Na primeira passagem foi identificada uma regressão baixa de acessibilidade, corrigida antes do fechamento:

- Severidade: baixo; tipo: regressão; consumidor: web/Categorias.
- Local original: `apps/web/static/js/gotrendlabs.js:336` no commit `1fd83a0`.
- Evidência: a inicialização anteriormente aplicada a todos os `[data-filter-group]` foi restrita a grupos com `data-filter-target`; `core/categories.html` possui filtros genéricos sem esse atributo. Assim, ao carregar Categorias, botões deixavam de receber os valores iniciais de `aria-pressed`.
- Impacto: leitores de tela perdiam a informação da seleção inicial nessa superfície compartilhada.
- Correção aplicada em `68b60c4`: inicializar o estado acessível de todos os grupos, acionando ordenação do catálogo somente quando há uma lista alvo. Testes Node e navegador confirmam estado inicial `true/false/false` e alternância para `false/true/false`.

A lacuna de execução contínua do teste de sorteio foi encerrada pela nova etapa `Test contextual grid invitation selection` no workflow existente, sem dependências adicionais.

## Pontos a validar

- Publicação: após aprovação do usuário, abrir PR pelo MCP GitHub, acompanhar CI completo, integrar à main, acompanhar build/deploy GitHub Actions e realizar smoke da página/assets/recortes em produção. `ENABLE_PROD_DEPLOY=1` foi confirmado, mas isso não comprova implantação desta branch.
- Navegadores físicos/Safari/Firefox: não exercitados nesta execução. Evidência atual é Chrome desktop com viewport móvel e medições reais de CSS/DOM; validação adicional depende desses ambientes.

## Riscos residuais e cobertura

- Sem armazenamento legível/gravar disponível, o estado da visita fica em memória; impedir repetição entre documentos exige histórico e permanece best effort conforme a spec.
- Textos muito longos rolam dentro do convite; altura dos cards e largura da página permanecem preservadas.
- Browser suite usa templates/assets reais e fixtures locais, não revalida os serviços de autenticação dos destinos existentes. Não altera esses serviços ou contratos.
- A suíte de navegador é reproduzível localmente; CI executa Django e testes Node, sem adicionar Playwright ao projeto. CI completo ainda precisa concluir antes do merge.
- Testes locais aprovados: dois Django sem banco; Node de filtros/faixa Novo/acessibilidade genérica, sorteio, analytics e prediction preview; 54 combinações de layout/tema, limites 1080/1081/980, cinco opções/20 capturas, teclado/foco, armazenamento negado/quota/histórico inválido, HTMX real e paginação, tamanho/ordem dos cards e textos longos. Django check, OpenAPI check, sintaxe JS, YAML e diff check aprovados.

Nenhum arquivo de código foi alterado durante a passagem final de review; a correção ocorreu em fase separada de implementação, seguida de nova revisão do diff versionado.

## Adendo após primeiro CI remoto

O CI 42416671503 da PR205 identificou dois testes existentes que localizavam a grade por tag HTML literal. O novo atributo do convite invalidou o split e gerou dois IndexError, sem falha de domínio. Corrigidos os dois cenários em tests/test_web_smoke.py para assertNotContains sobre a resposta inteira, mantendo e reforçando a checagem de cancelados. Quatro cenários Django selecionados aprovados em PostgreSQL 16 isolado; nova execução completa do CI exigida antes de merge. Esse adendo encerra a lacuna de regressão detectada remotamente; não altera o risco do runtime ou os contratos MCP/mobile.
