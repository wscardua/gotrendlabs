# Encaixe do ciclo no detalhe web — 17/10/2026

WFLOW-20261017-MARKET-CYCLE-LAYOUT. Correção somente de apresentação em template/CSS e versão do asset, mantendo a branch da agenda e alterações anteriores. Data, fuso e histórico vêm do mesmo contrato; sem mutações de dados, MCP, domínio ou Flutter.

O título, seis etapas (3×2) e previsão agora formam um cartão único na coluna de participação. Previsão tem rótulo discreto e valor destacado após divisor; ausência/reagendamento e estados terminais permanecem. Sem quebra artificial nos rótulos das etapas. Heading h2 e lista de definição identificam o bloco para tecnologias assistivas.

Verificação no mercado local indicado pelo usuário, Chromium real: desktop 1374 CSS px e larguras 390/320 CSS px. Medidas de DOM confirmaram ausência de overflow horizontal e de corte dos seis rótulos; capturas inspecionadas em temas claro/escuro. Zoom preexistente do navegador preservado (viewport solicitado ajustado para obter larguras CSS medidas); tema claro e viewport original restaurados. Nenhuma previsão foi enviada durante QA.

Quatro testes existentes aprovados (5.323s): páginas principais, copy em cada estado não aberto, resultado/resolução e finalização/selagem. Python 3.11 do ambiente existente `gotrendlabs-editorial-single-document/.venv`; PostgreSQL isolado `test_gtl_agenda_dev`. Django check e git diff --check aprovados. Nenhum teste novo necessário para esta mudança reversível de apresentação; não se repetiram testes backend/Flutter inalterados.

- [Desktop](../../../output/market-cycle-layout/desktop-light.png)
- [390 px claro](../../../output/market-cycle-layout/mobile-light.png)
- [390 px escuro](../../../output/market-cycle-layout/mobile-dark.png)
- [320 px](../../../output/market-cycle-layout/mobile-320-light.png)

MCP analisado: sem alteração de ferramentas, schemas, permissões, erros, replay ou orientação editorial; sem ajuste necessário. Sem mudanças de contratos/integrações/arquitetura, produção, merge ou deploy. Web local reiniciada para invalidar o cache de templates; CSS tem nova versão para evitar cache antigo no navegador.

## Atalho junto ao fechamento

Retomada WFLOW-20261017-RESOLUTION-SHORTCUT: link no estilo das tags ao lado do fechamento; só aparece com previsão. Enter navega para `#market-cycle-title` e transfere o foco ao heading (`tabindex=-1`). Rolagem suave existente preservada, com recuo para o cabeçalho fixo; data/fuso permanecem no cartão. Em 390 CSS px os itens quebram de linha sem overflow. Tema e viewport restaurados ao final.

Duas regressões existentes aprovadas em PostgreSQL isolado (3.210s): páginas principais e cada estado não aberto. QA real do mercado indicado em 1374/390 CSS px, claro/escuro, navegação por teclado e destino visível. Não há regra/payload/permissionamento novo nem ajuste MCP/Flutter necessário.

- [Botão no desktop](../../../output/resolution-shortcut/desktop-light.png)
- [Botão no celular](../../../output/resolution-shortcut/mobile-light.png)
- [Tema escuro](../../../output/resolution-shortcut/mobile-dark.png)
- [Destino ao usar o botão](../../../output/resolution-shortcut/mobile-target.png)

## Decisão final — informação estática no cabeçalho

A pedido do usuário, substitui o atalho descrito acima: previsão/data/fuso são uma tag estática ao lado do fechamento, com a mesma classe/aparência; sem botão, ícone, link ou ação. A previsão e a nota original/reagendamento/ausência saíram do cartão do ciclo, que conserva apenas as etapas. Históricos/ausência permanecem no cabeçalho conforme dados do contrato. CSS sem uso do antigo atalho/rodapé foi retirado.

QA real do mercado indicado: desktop 1374 CSS px confirma as duas tags na mesma coordenada vertical; celular 390 CSS px adapta em linhas sem overflow. DOM confirma zero links/botões no grupo e nenhuma previsão duplicada no ciclo. Dois testes existentes aprovados (3.084s), Django check e git diff --check aprovados. Mudança exclusivamente visual, sem ajuste MCP/API/Flutter necessário. Web reiniciada, CSS versionado e viewport restaurado.

- [Informação no desktop](../../../output/resolution-info/desktop.png)
- [Informação no celular](../../../output/resolution-info/mobile.png)

### Fuso abreviado

Rótulos de previsão original/vigente agora usam BRT para America/Sao_Paulo, pela convenção já usada no fechamento. Nove testes de agenda e checagens diretas de BRT, UTC e rótulo completo preservado aprovados; OpenAPI --check/diff check aprovados. Página local confirma “Resolução prevista: 20/10/2026 18:03 BRT”. Sem alteração de fuso persistido, instante, schema ou permissões MCP. [Captura atual](../../../output/resolution-info/desktop-brt.png).
