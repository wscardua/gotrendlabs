# Aceite local — usabilidade do Analytics

- Data: 2026-10-12; FEAT-ANALYTICS-001 v0.7.
- Branch/worktree: `feature/analytics-platform-comparison`, `/Users/williamsca/Documents/gotrendlabs-analytics-platform-comparison`. Mudanças v0.6 e correção de concorrência preservadas; sem commit/push/deploy.
- Venv existente: `gotrendlabs-ai-thumbnails/.venv`, Python 3.11. Sem instalação de dependências.

## Resultado e critérios

- Navegação por seções, cards compactos, tabelas extensas limitadas a 320px com cabeçalho fixo/rolagem própria e metodologia expansível, com ressalvas essenciais visíveis. Retenção global de 90 dias separada dos filtros de navegação; operação global identificada. Totais do domínio mantêm o período, sem aplicar plataforma/público/localização.
- Seleção das 27 UFs, sugestões de cidades derivadas do ranking atual (até 20, sem promessa de catálogo completo), limpar filtros e recorte aplicado explícito. Erro de API não apresenta atalhos para seções ausentes.
- Estado atual da GeoLite tem prioridade sobre a execução histórica. Arquivo ausente/configuração ausente/arquivo inválido geram aviso conhecido no topo; falta de eventos não é tratada como falha comprovada.
- `collection_platforms` agrega última recepção humana retida e eventos humanos em 24 h, por plataforma, globalmente, no mesmo snapshot dos totais operacionais. Não representa remessas por plataforma, instalações ou cobertura de instrumentação; ausência de registro explícita. Sem mudança Flutter, eventos, banco ou permissões.
- Gráfico com datas intermediárias responsivas, consulta por ponteiro/toque (Pointer Events) e controle nativo por teclado, valores em output/aria-valuetext. Legenda mobile tracejada; séries sobrepostas continuam distinguíveis. Tabela permanece aberta sem JS. Repetir o mesmo valor não dispara atualização textual redundante no live region.
- Formatação pt-BR/en testada; idioma preferido do operador controla renderização, HTML lang, Content-Language e Intl no gráfico. Textos preparados com tags i18n; não se afirma tradução integral inglesa do projeto, que não possui catálogo inglês.

## Evidência executada

- 17 testes Django sem banco aprovados: contrato, comparação, formatação, escopos/GeoLite, filtros encaminhados, idioma do operador, erro de API e navegação administrativa. Comando: `manage.py test tests.test_analytics_contract tests.test_analytics_web.AnalyticsPlatformPresentationTests tests.test_analytics_web.AnalyticsDashboardUsabilityTests tests.test_admin_navigation --noinput`.
- PostgreSQL: `test_collection_by_platform_is_global_human_and_reports_absent_history` passou em schema vazio isolado no banco de testes existente `gtl_mcp_pilot`. Confirmou filtros de navegação sem amostra, indicador global com web recente/mobile antigo, exclusão de bot/staff e plataforma sem histórico. Schema removido ao final; nenhum evento inserido no DEV ou em tabelas públicas.
- Regressões PostgreSQL v0.6 de filtros/distintos/zeros e consistência durante ingestão concorrente passaram novamente, cada uma em schema isolado removido ao final. Estruturas LIKE não replicam triggers/FKs; não substitui suíte normal com migrations. Helper/limite descritos no [aceite v0.6](analytics-platform-comparison-acceptance.md).
- Chrome via inspeção nativa no DEV autenticado (conferência final 12/10/2026 22:03 UTC): template/novo CSS/JS, formatação pt-BR (100,0%, datas dd/mm/aaaa), escopos, resultados do domínio na jornada e recepção por plataforma renderizados com dados reais.
- Chrome com fixtures de HTML sintéticas e templates/assets reais: desktop claro, viewport iframe 390px claro/escuro, comparação Web/App sobreposta (7 e 90 dias), Web único (24 h), período vazio de 30 dias e tabela aberta sem JavaScript. Controle de teclado Home, setas e End confirmou 07/10/2026 = Web 2/App 2 e 12/10/2026 = Web 7/App 7. Ponteiro na série de 90 dias selecionou 21/08/2026 = Web 6/App 6. Sem corte horizontal observado na área Analytics em 390px; tabelas mantêm rolagem própria.
- Fixtures reproduzíveis: `python tests/analytics_usability_fixtures.py`, saída ignorada em `.runtime/analytics-usability-qa/`. Servidas temporariamente em loopback 8889 para inspeção; servidor de QA encerrado após a validação; dados não representam uso real. Comparação diária não é soma de únicos do período.
- Django system check, ausência de migration drift, Node syntax check, diff check e OpenAPI export/--check aprovados. Snapshot OpenAPI não muda porque o endpoint existente não tipa a resposta; contrato textual atualizado.
- DEV API health HTTP 200. Reloaders continuam apontando para esta worktree; proxy/web/API/banco/media/MCP existentes preservados.

## Limites e MCP

- Suíte completa normal com migrations permanece pendente pelo travamento preexistente em CREATE/DROP DATABASE; não foi repetida nem houve reinício de serviço compartilhado.
- Toque físico, leitor de tela e carga volumétrica de produção não foram homologados. A inspeção estreita usa viewport de 390px em iframe; não é teste Flutter/Android. Não foi alegada auditoria integral WCAG.
- MCP sem ajuste: `apps/mcp/server.py` não consome resumo staff e `editorial_routes.py` mantém analytics editorial indisponível/null. Ferramentas, schemas MCP, permissões, erros, replays e orientação editorial preservados. Staff/MFA da API continua obrigatório; nova leitura operacional não cria acesso MCP.
