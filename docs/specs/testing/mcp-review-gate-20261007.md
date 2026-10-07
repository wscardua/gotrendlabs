# MCP revisão 1.1 — validação local em 2026-10-07

Workflow WFLOW-20261007-MCP-REVIEW-GATE-001, continuação de FEAT-MCP-001 e do ensaio persistente DEV. Pedido do usuário revisa a decisão anterior de ausência de bloqueio para mercados de integração; não introduz gate universal para mercados humanos legados.

## Resultado por critério

| Critério | Evidência local |
| --- | --- |
| Slug legível | Normalização comum do título, acentos removidos, reserva transacional, sufixo em colisão. Testes verificam replay, colisão e estabilidade após edição. |
| Parecer obrigatório | FastAPI/MarketLifecycleEngine recusa preparação, em revisão, devolvido e rejeitado com 409 `editorial_approval_required`, antes de assinatura/abertura. |
| Aprovação atual | Verifica origem humana, revisão/hash, snapshot persistido, conteúdo e política atuais. Hash/revisão/política antigos e conteúdo divergente recusados. Edição humana invalida aprovação e evidências. |
| Publicação segura | Aprovação positiva publica com signer efêmero e integridade verificada. Locks preservam serialização com agente; rascunho agendado revalida a aprovação. |
| Compatibilidade | Mercado humano existente segue criação/edição/publicação/cancelamento; integridade e previsões existentes passam nas regressões. Editor publica versão salva sem executar save/upload da edição. |
| Integrações | Indicadores, tabela de cadastros, criação separada e dez registros recentes dos logs existentes, seguindo estrutura Agentes IA. Gestão, responsável por nomes e calendário preservados. |
| DEV | Slug do draft #5 corrigido pelo editor humano, revisão 4/preparation, decisão vazia, publicação bloqueada. Fechamento preservado em 2026-10-21 02:59 UTC = 20/10 23:59 São Paulo. Hashes das linhas dos mercados 1–3 permanecem iguais ao baseline do radar. |

## Testes executados

- Suíte final: **44 testes passaram em 147,858 s**, exit 0. Inclui `tests.test_mcp_editorial` (35 testes), publicação do editor (2), consentimento (1), adapter/fronteiras/mocks de falha (4), gestão humana legada (1) e integridade/previsões (1).
- Complemento agendado: **1 teste passou em 4,403 s**, exit 0. Complemento de preservação de dados na edição humana: **1 teste passou em 4,003 s**, exit 0. Total de 46 casos distintos aprovados.
- Test runner usa PostgreSQL temporário e destrói as bases `test_gtl_mcp_final`/`test_gtl_mcp_scheduled`; fixtures destrutivas não executam no DEV. Cliente MCP SDK real via TCP continua cobrindo OAuth e serviço, todas as dez tools e recusas esperadas.
- Ruff F, Django check, sintaxe JavaScript, OpenAPI export/check e `git diff --check` passaram. OpenAPI acrescenta `editorial_market_id` opcional à projeção administrativa; sem migration nova.
- Navegador Chrome real em DEV: listagem, formulário de criação, seletor de responsável, calendário, editor e ficha de revisão conferidos. Evento homônimo Geral permanece selecionado na classificação correta. Editor exibe o fechamento no fuso escolhido e não transborda a prévia.
- Evidência local ignorada pelo Git: `.runtime/mcp-review-gate/{integrations.jpg,editor.jpg,dev-audit.json}`. Verificação do guard em DEV executou somente SELECT/locks e rollback, sem assinatura/publicação.

## Limites e retomada

Nenhuma publicação, merge ou deploy realizado. Dot/HTTPS externo e compatibilidade efetiva do executor LM Studio permanecem pendentes; feature continua `parcial`. QA responsivo desta revisão não foi comprovado: override de viewport do navegador não alterou a largura efetiva; somente desktop foi conferido nesta rodada.

Draft #5 precisa de ficha/evidências atualizadas e nova submissão via agente antes do parecer humano. Não aprovar automaticamente nem remover lacunas para contornar a revisão. Para ver o resultado: [Integrações](http://localhost:8000/admin-ops/integrations/) e [ficha #5](http://localhost:8000/admin-ops/agent-reviews/5/).

Rollback de código deve incluir a revisão do contrato e do bloqueio no lifecycle; desligar MCP impede novas chamadas, mas não deve remover inadvertidamente a exigência de aprovação dos drafts já persistidos. Histórico de fichas/decisões e logs permanece preservado.
