# Resolução confiável — validação local de 25/10/2026

## Escopo e base

WFLOW-20261025-RESOLUTION-RELIABILITY; branch `fix/market-resolution-reliability`, base `origin/main` `9407a8c`. Worktree `/Users/williamsca/Documents/gotrendlabs-resolution-fix`; alterações anteriores na pasta original preservadas.

Corrigidos: timeout ambíguo no Admin Ops, replay/concorrência de resolução, origem da janela de revisão e apresentação de comprovantes/resultado antes da selagem. Sem mudança das fórmulas de wallet/reputação nem reescrita de provas/prazos produtivos.

## Ambiente

Python 3.11.0 do venv existente `/Users/williamsca/Documents/gotrendlabs-ai-thumbnails/.venv`. PostgreSQL 16 em contêiner temporário exclusivo `gtl-resolution-tests`, porta local 55439 e dados efêmeros. O PostgreSQL compartilhado estava ocupado com outras criações de bancos; a criação de teste desta execução foi cancelada e a validação transferida ao contêiner isolado. Nenhum banco de aplicação foi migrado.

## Evidências executadas

| Execução | Resultado |
| --- | --- |
| `tests.test_resolution_reliability`, `tests.test_integrity_ledger`, `tests.test_resolution_agenda`, `tests.test_mcp_publication_ui.ResolutionWallTimezoneTests` | 84 testes, OK, 49,274s |
| 15 regressões selecionadas de `tests.test_web_smoke` | OK, 32,620s |
| `tests.test_resolution_reliability` ampliado, `tests.test_mcp_adapter`, `tests.test_mcp_schedule_errors` | 22 testes, OK, 12,097s; inclui repetição dos 11 cenários iniciais de confiabilidade |
| Replay/consulta/selagem com tentativa de alterar recibo | 1 teste repetido com asserção adicional, OK, 1,519s |
| `manage.py check` | Sem problemas |
| `manage.py makemigrations --check --dry-run` | Sem divergência modelo/migration |
| Exportação OpenAPI e `packages/contracts/export_openapi.py --check` | Snapshot sincronizado |
| Migration completa em banco vazio; markets.0037 → 0036 → 0037 | Aplicação, reversão e reaplicação OK |
| Grants da role `gotrendlabs_fastapi` no banco temporário | SELECT=true, INSERT=true, UPDATE=false, DELETE=false |
| Trigger `resolution_requests_append_only` | Presente; UPDATE de recibo rejeitado no teste |
| `git diff --check` | Sem erros |

São 110 cenários distintos nas três suítes, com repetições explicitadas acima; não confundir a soma das execuções com testes únicos. A suíte inteira do repositório/CI remoto não foi executada nesta entrega.

As 15 regressões incluem: ranking temático, reforço/revisão de posição, resolução com vencedores/perdedores, payout/loss/reputação, distribuição/undo/refund/auditoria, proteção de edição de mercado resolvido, cards/detalhe/modal/arquivo de integridade, estados ativo/resolvido/selado/cancelado/falha e navegação staff/Admin Ops.

## Aceites protegidos

- Dois operadores com resultados diferentes: exatamente um sucesso e um conflito, uma liquidação e resultado coerente com a previsão.
- Dois operadores com mesma chave/payload: ambos recebem sucesso; apenas um recibo/evento/notificação de resolução.
- Reenvio confirmado e consulta após selagem: retorno atual sem duplicação de wallet/reputação/notificações.
- Chave reutilizada com conteúdo diferente, mercado diferente por identidade ou ocorrência desfeita/substituída: conflito seguro.
- Falha de assinatura: rollback de estado, previsão, recibo e evento; mesma chave pode ser tentada novamente após falha revertida.
- Entrada retroativa: prazo de selagem igual a `market_resolved.occurred_at + janela`, independente de `resolved_at` declarado. Nova resolução após desfazer recebe janela nova.
- Timeout: GET da mesma operação, sem segundo POST automático. Confirmação ausente/indisponível é estado indeterminado; não informa rollback fictício.
- Formulário reapresentado preserva UUID/ID; botão de consulta não chama mutação.
- Comprovantes/resultado verificados antes do Seal; pendência ou falha não recebe confirmação positiva.
- Staff/MFA existentes aplicados às novas rotas; usuário comum recebe 403. Sem alteração de ferramenta ou escopo MCP; testes do adaptador/erros preservados.

## Arquitetura e consumidores

FastAPI é a fonte da verdade; `MarketLifecycleEngine` relê sob lock e decide transição/prazo. Recibo e efeitos compartilham transação. Django faz transporte, reconciliação por GET e apresentação dos booleanos existentes. UUID/identidade obrigatórios no contrato atual, sem fallback para clientes antigos. Migration aditiva e recibos sem tokens ou cópia de texto editorial.

MCP não consome as rotas administrativas e não recebe poderes humanos de resolver/desfazer. Na fatia exclusiva de confiabilidade administrativa, mobile não chama a nova consulta staff. A extensão wallet/métricas descrita no complemento abaixo altera o consumidor Flutter e exige release própria. Preservados contratos editoriais, orientação exposta, schemas e replays MCP.

## Rollout e limites

Entrega concluída localmente; sem commit/push/PR/merge/deploy nesta etapa. Antes do runtime produtivo, aplicar markets.0037 e verificar grants com a role efetiva. Após publicação, executar smoke staff de resolução/consulta/replay controlado e acompanhar o próximo ciclo de selagem. Não alterar retroativamente o prazo do mercado já resolvido nem reassinar eventos para acomodar a nova regra.

A auditoria original constatou integridade e liquidação válidas no mercado 35, mas esta bateria local não certifica sua selagem futura nem substitui a revisão editorial da fonte esportiva. A latência de cada chamada KMS não foi instrumentada; o timeout de 15s é mitigação, e a segurança funcional depende de reconciliação e idempotência.

## Complemento — wallet e métricas finais (2026-10-25)

- Produção auditada somente por leitura: previsão 100 GT₵ a 50%, retorno contratado 200; ledger release 100 e payout líquido 100. Zero volume/participantes vinha da projeção apenas open após liquidação. Nenhum saldo foi alterado.
- Nova projeção resolution_returns usa lançamentos posteriores ao último lock/relock, apenas winners atuais, agrupados por mercado e escopados ao usuário autenticado. Extensão obrigatória de LedgerResponse; não altera lançamentos/fórmula. Web/Flutter apresentam os valores calculados pelo backend.
- Métricas finais agregam resolved nos estados resolved/sealed e open nos demais; reforços não duplicam contas. Humans/bots preservados; elegibilidade continua usando _human_prediction_totals com open.
- PostgreSQL 16 isolado (container temporário, porta 55439); venv Python 3.11 existente em gotrendlabs-ai-thumbnails/.venv. Primeira execução encontrou expectativa de fixture 50% quando o seed era 62% e contexto incompleto no teste de template; fixtures corrigidas. Casos verificam tanto 100/100/200 a 50% quanto 100/61/161 a 62%, lucro zero, perdedor, cancelamento, isolamento e undo/re-resolve sem duplicação.
- Execução final: `manage.py test tests.test_wallet_returns tests.test_market_participants tests.test_mcp_adapter tests.test_analytics_mcp_contract --noinput --keepdb`: 14 testes, OK (14.817 s). 14 casos test_resolution_reliability passaram também na execução inicial desta fatia (21 casos, única falha era a fixture wallet corrigida depois).
- Flutter: wallet_screen_test, market_card_test, market_detail_screen_test, shell_screen_test e prediction_ticket_test: 46 testes, OK. Ajustadas as expectativas do painel para sua tipografia em maiúsculas. `flutter analyze`: sem problemas. Sem instalação/build/release/QA manual em aparelho nesta fatia.
- MCP: ferramentas editoriais usam projeções próprias e analytics usa participação persistida própria; sem wallet MCP, novos scopes ou permissões inferidas de ações administrativas. Adaptador e contrato analytics verificados.
- Sem nova migration/backfill nesta extensão; branch completa ainda exige 0037 antes do runtime. Sem commit/push/deploy desta fatia.

- Verificações finais: Django check, makemigrations --check --dry-run, snapshot OpenAPI e git diff --check aprovados.

## Revisão e preparação de fechamento

Review solicitado via gotrendlabs-review-branch-impact: nenhum problema identificável no diff, risco geral médio pela alteração transacional/migration. Reexecutados 8 testes Python de transporte/formulário/timezone e 21 Flutter de wallet/cards, todos aprovados; OpenAPI/diff válidos. A revisão não repetiu PostgreSQL. Pontos residuais: KMS/timeout real, volume de histórico da wallet, corrida de mesma chave entre mercados, GET durante POST e agrupamento de reforços vencedores.

Publicação segue WFLOW-20261025-RESOLUTION-CLOSEOUT e o [runbook](../operations/resolution-reliability-rollout.md). Nenhum sucesso remoto ou produção é antecipado.

Validação de fechamento: suíte completa `manage.py test --noinput` executou 606 testes em 483,378 s: 603 passaram, 2 skips e 1 falha de expectativa no teste de cancelamento repetido (422 esperado no contrato, asserção havia sido alterada para 409). Restaurado 422 sem mudar runtime; caso reexecutado e aprovado em 1,796 s. Resultado combinado: 604 cenários aprovados e 2 skips. Não houve segunda execução integral após essa correção exclusivamente de teste. OpenAPI, Django check, dois testes JavaScript e diff válidos; Flutter mantém os 46 testes/analyze da implementação e 21 reexecutados na revisão. CI remoto será acompanhado no último SHA da PR e no merge.
