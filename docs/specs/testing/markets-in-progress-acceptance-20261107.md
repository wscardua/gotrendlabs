## Atualização local — 14/11/2026

A regra temporal atual da faixa Novo substitui created_at por published_at (48h, open, sem fallback). Criação antiga com publicação recente recebe faixa; publicação ausente/inválida/futura não recebe. Testes de limites/expiração foram atualizados. O relato de 07/11 abaixo descreve a implementação anterior; nenhuma nova publicação em produção foi realizada. Fonte atual: FEAT-MARKET-001 v0.18 e WFLOW-20261114-NEW-FROM-PUBLICATION.

# Aceite local — navegação Em andamento

WFLOW-20261107-MARKETS-IN-PROGRESS / FEAT-MARKET-001 v0.15. Base remota `7d1dd314180efce510a2e7ceb57254f9fca579be`; branch `feature/markets-in-progress`, worktree `/Users/williamsca/Documents/gotrendlabs-markets-in-progress`. Checkout original e branches anteriores preservados.

## Comportamento aprovado

| Área | Regra |
| --- | --- |
| Navegação | Em andamento inicial, Resolvidos, Favoritos e Minhas previsões; recortes pessoais autenticados |
| Abertos web | Views decrescentes, criação mais recente, origem como último desempate |
| Abertos mobile | Ordem do GET /markets; Hoje mantém pontuação de engajamento |
| Apuração | Somente locked, expandida abaixo dos abertos, contagem total; close_at programado decrescente/origem, ausentes no fim |
| Expansão | Nativa details/summary no web; botão com semântica expandida no Flutter; retorno ao recorte expande filhos |
| Novo | Somente open, created_at <= agora < created_at + 48h; sem futuro e sem influência na ordem |
| Pessoal | Favoritos e Minhas previsões preservam encerrados/selados; posições ativas em acesso secundário Flutter |
| Paginação web | Blocos de 18 por lista após filtro/ordem; carregar abertos não altera limite ou expansão de apuração |
| Vazio | Sem open mantém mensagem e apuração disponível; sem ambos oferece Resolvidos; sem locked não há expansor vazio |

## Evidências executáveis

- `node tests/test_market_feed_filter.js`: aprovado. Exercita funções reais de ordenação/filtro, movimentação dos mesmos cards entre listas, página de 18/36, independência dos limites, recortes pessoais, exclusão de draft/canceled e limites temporais do selo.
- Flutter: 135 testes aprovados na suíte completa e `flutter analyze --no-pub` sem issues; testes de Hoje, recortes pessoais, apuração, ordem da API, selo, refresh e ausência de ativos. Widget test em 390x844 com escala de texto 1,4 sem overflow. Contagem final e comandos registrados no workflow.
- Django: oito testes de home/filtros, carregamento, API/fallback, card selado, detalhe e proxy de prova. PostgreSQL 16 isolado em 127.0.0.1:15438, dados temporários em tmpfs devido à falta de espaço do armazenamento Docker; nenhum banco existente alterado. Oito aprovados.
- A fixture do teste de páginas passou a usar `local_market`, que fornece IDs válidos das opções no contrato atual; o fixture JSON antigo dependia da ordem de outros testes e causava 503 no detalhe quando executado isoladamente. Sem fallback novo no runtime.
- `manage.py check`, `node --check apps/web/static/js/gotrendlabs.js`, `packages/contracts/export_openapi.py --check` e `git diff --check`: aprovados.

## Navegador e limites

Validação anterior ao ajuste de expansão inicial, em Chrome local com templates/CSS/JS reais e dados sintéticos: open popular antes de open novo, selo apenas no novo, locked ausente da árvore de acessibilidade enquanto recolhido, expansão em prazo decrescente, retorno recolhido após Resolvidos/Favoritos e selado preservado em Favoritos. Temas claro/escuro e acesso a Resolvidos no estado vazio conferidos.

Cenário anterior ao ajuste, com 21 open e 21 locked: início com 18 open, Carregar mais revelou 21; apuração continuou recolhida e expandiu pelo teclado com 18; seu próprio botão revelou 21 sem alterar os abertos. Sem submissão de formulários ou mutação em ambientes existentes.

A captura Flutter local usa widget test com fonte carregada para inspeção do card e espaçamento; a tipografia nativa de alguns controles não é reproduzida pelo ambiente de testes. Não equivale a instalação/sessão em Android físico. Nenhum APK/AAB release foi gerado, nenhum PR/merge/deploy ou ajuste produtivo foi executado. A apresentação nova exige integração/publicação web e release mobile próprias.

## Arquitetura e MCP

Somente apresentação sobre status efetivo, timestamps e flags existentes. Flutter passa a consumir created_at/close_at já publicados. Sem novo endpoint, campo de API, schema OpenAPI, persistência, lifecycle, contabilidade ou autorização. Ferramentas, schemas, contratos, permissões, erros, replays e orientação editorial MCP não precisam mudar; nenhuma permissão foi inferida de operações humanas do Admin Ops. Sem necessidade de ADR estrutural ou migration.

## Ajuste após teste do usuário — apuração expandida

O usuário solicitou mostrar a seção completa sem expansão manual. Web usa details aberto inicialmente e o JS o abre ao retornar a Em andamento; Flutter inicia e retorna com apuração expandida. Recolhimento manual continua possível, e carregar mais preserva essa escolha até mudar o recorte. Abertos seguem primeiro, paginação/ordem não mudam. Teste JS e 12 testes da tela Flutter atualizados/aprovados; análise Flutter sem issues, check Django e diff aprovados. HTTP local confirmou o atributo open e URLs estáticos novos. As evidências anteriores de recolhimento descrevem a primeira versão, superada por esta revisão. MCP sem ajuste, por mudar apenas estado local de apresentação.

## Faixa diagonal NOVO

Substitui a pill pela faixa no canto superior direito, conforme referência do usuário. Critério segue created_at/open/48h. Web: CSS/HTML, label acessível e pointer-events none, título com espaço reservado e assets versionados; Chrome local claro/escuro com fixtures aprovado. Flutter: overlay ignorando ponteiro, semântica Novo, espaço reservado para consenso e integridade; 32 testes de cards/telas aprovados, incluindo clique no canto e ausência de faixa em locked. Analyze sem issues, teste JS, check Django e diff aprovados. Sem mudança de domínio/API/MCP ou release instalada.


### Correção da faixa Novo após review — 2026-11-07

Correções do review: inicialização da faixa em cards sem grupo de filtros (Categorias), expiração automática em tela aberta e revalidação ao retornar à aba web. Teste JS executa inicialização real com relógio/timers controlados. Testes Flutter montam hero/compacto, avançam o relógio pelo limite sem interação e verificam remoção da faixa; desmontagem verifica descarte sem timer pendente. 40 testes Flutter de cards/telas/repository aprovados; analyze sem issues; teste JS, sintaxe JS e diff aprovados. Sem mudança API/domínio/MCP. Android físico continua não validado.

## Gate de fechamento

Reexecução final: 139 testes Flutter aprovados, analyze sem issues; oito testes Django de home, filtros, paginação, cancelados, API/fallback, card/detalhe selado e pacote de integridade aprovados em PostgreSQL 16 isolado (4,605s). JS funcional/sintaxe, check Django, snapshot OpenAPI e diff aprovados. Build debug executado em Android 16/API 36 no emulador; tela Hoje e faixa NOVO confirmadas com fixtures locais. Android físico não validado.

Publicação: aguardando aprovação da descrição antes de abrir a PR. Deploy produtivo usa Actions após merge, sem migration/configuração adicional; smoke deve confirmar assets `20261107-ribbon-expiry`, recortes, apuração expandida, detalhe/provas dos selados existentes e health. Nunca transferir fixtures QA para produção. Binário Android segue distribuição própria a partir da main integrada e limpa.

## Estado posterior: publicação concluída

Os gates de PR/deploy descritos acima foram atendidos pela PR #199 e Actions 42394768559. Consulte o [recibo produtivo](markets-in-progress-production-closeout-20261107.md), que prevalece para implantação. Android binário continua separado.
