# Aceite local — convite contextual na grade web

WFLOW-20261107-WEB-GRID-INVITE / FEAT-MARKET-001 v0.17. Branch `feature/web-market-grid-invite`, worktree `/Users/williamsca/Documents/gotrendlabs-grid-invite`, criada após `git fetch origin main` sobre `d93d5b9`. Checkout original e todas as suas alterações locais preservados. Implementação/validação local em 07/11/2026, sem publicação ou deploy.

## Implementação

- Um componente na grade principal, com cinco templates inertes e apenas uma opção materializada. Cards de mercado e grade secundária de apuração preservados.
- Contagem somente de cards visíveis após filtro/paginação; ocupação a partir das colunas reais de CSS. `ResizeObserver` acompanha largura, `MutationObserver` acompanha cards/visibilidade e HTMX reidrata sem duplicar listeners ou sortear outra opção.
- Conteúdo permanece em memória durante a visita, inclusive enquanto o convite está oculto. Histórico localStorage guarda apenas a última chave de opção, com leitura/escrita protegidas. Primeiro sorteio tem cinco intervalos iguais; com histórico válido são quatro intervalos iguais excluindo o anterior. Sem banco ou dependência nova.
- SVGs vetoriais próprios inspirados nas cinco referências inspecionadas; nenhuma montagem, texto rasterizado, dado fictício ou asset mobile no produto. Textos HTML com `trans`, arte decorativa (`aria-hidden`, `alt=""`), tokens reais dos dois temas e foco nativo visível.
- Contenção de tamanho faz o convite acompanhar a altura da linha sem aumentar os cards. Textos excepcionalmente longos podem rolar dentro do convite; não são cortados nem causam overflow horizontal.
- Destinos: `suggestion`, `rankings`, `badges`, `concepts` e `home#resolvidos`. Resultados aciona o filtro `resolved` existente, incluindo `sealed`; clique comum não recarrega nem refaz sorteio, link aberto em nova aba também chega ao recorte correto. Não altera autenticação ou concessões.
- Reutiliza `navigation_clicked` da instrumentação existente, sem evento novo. Acesso ao storage de tema/analytics protegido para evitar interrupção da página; analytics não inicia quando não consegue ler preferências. Versões dos assets atualizadas contra cache anterior.

## Evidências visuais

Capturas do Chromium/Chrome local com templates e assets reais, usando fixtures sintéticas exclusivamente no servidor de testes. Nenhum banco, catálogo ou API produtiva recebeu esses dados.

| Cenário | Claro | Escuro |
| --- | --- | --- |
| 4 mercados, convite de duas colunas | [captura](evidence/web-grid-invite-20261107/4-light.png) | [captura](evidence/web-grid-invite-20261107/4-dark.png) |
| 5 mercados, convite de uma coluna | [captura](evidence/web-grid-invite-20261107/5-light.png) | [captura](evidence/web-grid-invite-20261107/5-dark.png) |

As 20 capturas das cinco opções × 4/5 mercados × dois temas ficam em `.runtime/grid-invite/`; quatro representativas são versionadas acima. Revisão visual confirmou composição horizontal/vertical, texto separado da arte, selo Resolvido com check, sequência de conceitos e adaptação aos temas.

## Verificações aprovadas

- Navegador: 54 combinações (0–8 × três/duas/uma coluna × claro/escuro), com medição real de grid/DOM, ausência de convite na apuração e de overflow horizontal.
- Geometria: comparar cards com convite visível/oculto confirmou dimensões, posição e ordem idênticas; altura do convite igual ao último card. Zero preserva o estado vazio.
- Limites de breakpoint em 1080/1081/980px: composição vertical preservada quando o convite ocupa só uma coluna.
- Cinco opções/destinos, 20 capturas, copy aprovada sem scroll em largura desktop testada, teclado Tab/Shift+Tab/Enter, foco visível e resultado acionando o filtro existente.
- Visita: filtros, ocultar/reexibir, redimensionamento e tema conservam seleção; reload com histórico não repete a anterior.
- HTMX real: request local/substituição do board por HTML Django com 20 abertos, primeira página de 18 sem convite e expansão para 20 com convite; filtros e paginação continuam ativos, eventos repetidos não duplicam componente.
- Armazenamento: getter indisponível/SecurityError, escrita recusada/QuotaExceededError e histórico inválido não quebram tema, filtros ou convite. Sem erros JavaScript na suíte.
- Contraste calculado a partir das cores computadas do navegador: rótulo 4,53:1 claro/5,77:1 escuro; títulos, descrição e ação acima de 13:1.
- Textos longos: sem aumento da altura dos mercados ou overflow horizontal; conteúdo continua acessível por rolagem interna e teclado.
- Sorteio Node: todos os intervalos de primeira visita e todos os quatro sucessores possíveis de cada opção anterior, histórico inválido, leitura/escrita recusadas.
- Django: dois testes `SimpleTestCase` sem banco (componente, rotas, assets decorativos sem texto SVG, inclusão única na grade principal/estado vazio).
- Regressão JS: `test_market_feed_filter.js` (filtros, ordenação, páginas independentes e faixa Novo) e `test_analytics_web_events.js` aprovados.
- `manage.py check`, sintaxe dos três scripts alterados, compilação dos testes Python e `git diff --check` aprovados.
- Diff de `apps/mobile`, documentação/contratos mobile e `packages/contracts` vazio.

## Reprodução

Reutilizado o ambiente existente `../gotrendlabs-mcp/.venv` (Python 3.11/Django 4.2). A `.venv` do checkout original usa Python 3.9 e não consegue importar os contratos atuais com unions PEP 604; não foi alterada nem houve instalação de dependências. Playwright Node e Chrome já instalados foram reutilizados.

```sh
../gotrendlabs-mcp/.venv/bin/python tests/web_grid_invite_preview.py
# Em outro terminal, com Playwright já disponível no NODE_PATH:
NODE_PATH=/Users/williamsca/.npm/_npx/e41f203b7505f1fb/node_modules node tests/test_web_grid_invite_browser.js
node tests/test_market_grid_invite_selection.js
node tests/test_market_feed_filter.js
node tests/test_analytics_web_events.js
../gotrendlabs-mcp/.venv/bin/python manage.py test tests.test_web_grid_invite
../gotrendlabs-mcp/.venv/bin/python manage.py check
```

## Arquitetura, MCP e limites

Revisão pelas skills software-architect/architecture-guard: apresentação exclusivamente web, sem nova fronteira, regra crítica, migração ou ADR. Não houve alteração de API, modelo, autenticação, contrato mobile, app Flutter ou documentação mobile. Sem mudança de dependências, `integration-map.md` não requer alteração.

MCP não precisa de ajustes: tools, schemas, contratos, permissões, erros, replays e orientação editorial permanecem iguais. O convite só navega para fluxos web já autorizados, não publica sugestões automaticamente e não infere permissões de ações humanas no Admin Ops.

Limites da validação: navegador Chromium/Chrome desktop com viewport móvel, sem ensaio em aparelhos físicos ou Safari/Firefox; UI exercitada com fixtures locais e templates reais, sem revalidar serviços/autenticação dos destinos existentes. Sem storage, o sorteio continua funcionando em memória, mas não pode prevenir repetição entre recarregamentos. Internacionalização segue os marcadores Django existentes; catálogos completos de tradução continuam na iniciativa FEAT-I18N-001. Escopo local concluído, sem pendência de implementação desta fatia.
