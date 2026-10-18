# Fechamento — apresentação do Painel de contratos (18/10/2026)

Feature FEAT-RESOLUTION-AGENDA-001 v1.2. Workflows WFLOW-20261018-CONTRACTS-TIMELINE e WFLOW-20261018-CONTRACTS-TIMELINE-CLOSEOUT.

## Estado vigente

Implementação e documentação finais validadas localmente. Commit local preparado; PR/CI/merge/deploy pendentes; a submissão da PR exige a aprovação prévia do título/descrição pelo usuário. Não declarar implantação produtiva antes da evidência do Actions e smoke. Branch local `fix/contracts-timeline-states`, worktree `/Users/williamsca/Documents/gotrendlabs-contracts-timeline`, base origin/main e914df7 confirmada por fetch e GitHub MCP. O commit inicial 0b62a16 será complementado pelo fechamento.

Este recibo é a fonte vigente para o resultado final; as alternativas visuais e execuções anteriores em workflow-runs são históricas. Worktrees principal/agenda e seus arquivos não rastreados/documentação não commitada permanecem preservados.

## Comportamento final

- FastAPI mantém estado, classificação temporal e elegibilidade. Django apresenta geometria e labels.
- Locked/resolved/sealed mostram Fechado; close_at é sempre horário programado, sem fabricar instante efetivo da ação. Open/scheduled com closure_inconsistent exibem o alerta autoritativo.
- Previsão vencida usa resolution_overdue, nunca conclusão/início de apuração. Previsões de terminais são históricas; cancelamento não deixa obrigação de resolução/selagem.
- Criação/publicação/resolução/selagem usam registros efetivos. Ausência de data em terminal é explícita; seal_due_at é prazo, não selagem efetiva. Undo e reagendamento preservam agenda/histórico/provas pelo contrato existente.
- Linha simples ordenada com Hoje, datas e intervalos. Parte variável do espaçamento é linear à duração na janela global da consulta; piso de 136px preserva rótulos, portanto não é escala linear pura.
- Sem data permanece à direita na mesma linha; rolagem horizontal por teclado quando necessário. Cartões de todas as etapas permanecem abertos.
- Regiões acessíveis usam Cronograma + título do mercado por aria-labelledby e instrução separada por aria-describedby; IDs únicos antes/depois de Carregar mais.
- Filtros, contadores com escopo, ordenação, paginação cumulativa e escala antes do recorte preservados.

[Spec](../features/market-resolution-agenda.md), [contrato de ciclo](../contracts/market-lifecycle.md), [aceites vigentes](contracts-timeline-acceptance-20261018.md).

## Validação local final

Ambiente virtual existente Python 3.11: `/Users/williamsca/Documents/gotrendlabs-ai-thumbnails/.venv`. A venv Python 3.9 do checkout principal foi preservada. PostgreSQL 16 dedicado `gotrendlabs-contracts-closeout-test`, porta 55439, armazenamento temporário isolado em memória; nenhum banco DEV/PRD utilizado pelos testes.

```sh
POSTGRES_USER=gtl_test POSTGRES_PASSWORD=gtl_test POSTGRES_DB=gtl_contracts POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=55439 BACKEND_API_URL=http://127.0.0.1:59999 /Users/williamsca/Documents/gotrendlabs-ai-thumbnails/.venv/bin/python manage.py test tests.test_resolution_agenda tests.test_web_smoke.WebSmokeTests.test_admin_contracts_timeline_uses_active_market_contract_dates tests.test_web_smoke.BackendAuthAPITests.test_market_resolution_distribution_math_undo_and_refund_audit --noinput --keepdb
```

- 41 testes aprovados em 11.578s, incluindo os 23 testes de apresentação/regras (contagens sobrepostas).
- OpenAPI `packages/contracts/export_openapi.py --check` atualizado, sem mudança de schema.
- Django check sem problemas; JavaScript analytics e prediction preview aprovados.
- Dockerfile `docker build --check .` sem warnings. Build completo e suíte integral serão exigidos pelo CI da PR/main.
- QA Chrome com fixtures locais em 1440×1000/390×844, claro/escuro desktop; eventos, terminais, sete coincidências, Sem data na mesma linha, nomes acessíveis por mercado e teclado conferidos. Página sem overflow horizontal; ArrowRight rolou 40px na região focável.
- Review contra e914df7: finding de identificação acessível corrigido e coberto por teste de referências/IDs/carregamento. Sem vulnerabilidade ou mudança de autorização identificada no escopo.
- Evidências privadas ignoradas pelo Git: `.runtime/contracts-timeline/closeout-tests.log`, `duration-desktop.png`, `accessible-market-timeline.png` e fixtures reproduzíveis. Diff check aprovado e 21 links locais novos sem ausências. Container de testes exclusivo removido após a execução; serviços DEV preservados.

## Produção e ativação

A agenda já implantada e seus dados não devem ser reaplicados. Consulta somente leitura de 18/10/2026 confirmou 35/36/52 locked, 53/55 open; o inventário e as assinaturas foram preservados nesta tarefa. [Recibo independente da aplicação produtiva](../../operations/resolution-agenda-application-20261018.md).

Esta revisão não adiciona migration, flag, configuração, segredo, backfill ou release Flutter. Ativação acontece pelo deploy normal do Django e collectstatic (asset `css/gotrendlabs.css?v=20261018-contracts-timeline-008`). `.github/workflows/deploy.yml` executa build principal/MCP, OpenAPI, JavaScript e suíte integral na PR; em main, ENABLE_PROD_DEPLOY=1 dispara deploy via SSM. Valor 1 confirmado no GitHub durante o fechamento.

Após aprovação: enviar branch, criar PR via GitHub MCP, acompanhar CI, integrar à main preservando branch local e acompanhar Actions/test/deploy. Smoke somente leitura deve confirmar SHA implantada, serviços, API/DB/MCP, CSS versionado e renderização do template real com estados produtivos/fixtures somente em memória. Não alterar mercados ou recriar eventos/assinaturas para verificar a UI. Registrar PR, merge, runs, SHA e resultado abaixo antes de concluir.

### Evidência de publicação

Pendente da aprovação prévia do usuário. Sem PR, push, merge ou deploy desta branch neste momento.

## Impactos, limites e checklist

API/OpenAPI e cliente Django inalterados. Mobile não impactado: `apps/mobile/lib/src/features/markets/market_models.dart` continua consumindo resolution_schedule/published_at/seal_due_at/sealed_at existentes. MCP mantém ferramentas, schemas, contratos, scopes/permissões, códigos de erro, replays e orientação editorial; nenhuma capacidade nova inferida de ações humanas do Admin Ops. Eventos de domínio, ledger/assinaturas, finanças e automações não mudam.

Sem nova fronteira/dependência ou ADR; integration-map não requer ajuste. Specs, contrato de ciclo, aceites, README, changelogs, status, known-gaps, workflow e memória devem apontar este recibo. Checklist universal/alterar-feature/implementação/testes aplicado; publicação permanece aberta até CI/deploy/smoke. Limites: timestamp real de fechamento indisponível, escala adaptada com piso, QA visual local, VoiceOver nativo/fontes ampliadas não executados.
