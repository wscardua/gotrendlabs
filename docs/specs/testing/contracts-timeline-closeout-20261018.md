# Fechamento — apresentação do Painel de contratos (18/10/2026)

Feature FEAT-RESOLUTION-AGENDA-001 v1.2. Workflows WFLOW-20261018-CONTRACTS-TIMELINE e WFLOW-20261018-CONTRACTS-TIMELINE-CLOSEOUT.

## Estado vigente

Encerramento técnico concluído e validado em produção pela [PR #173](https://github.com/wscardua/gotrendlabs/pull/173), criada e integrada via GitHub MCP após aprovação explícita do título/descrição pelo usuário. Commits locais 0b62a16 e 8a66e7b; merge e SHA produtiva `2c4ddd98a91aac7e898dc52c89b8b93a0688cf09`. Branch local `fix/contracts-timeline-states` preservada na worktree `/Users/williamsca/Documents/gotrendlabs-contracts-timeline`, árvore limpa. Base original e914df7; registro final preparado na branch documental separada `docs/contracts-timeline-production-20261018`.

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
- Dockerfile `docker build --check .` sem warnings. Build principal/MCP e suíte integral também aprovados no CI da PR/main (evidências abaixo).
- QA Chrome com fixtures locais em 1440×1000/390×844, claro/escuro desktop; eventos, terminais, sete coincidências, Sem data na mesma linha, nomes acessíveis por mercado e teclado conferidos. Página sem overflow horizontal; ArrowRight rolou 40px na região focável.
- Review contra e914df7: finding de identificação acessível corrigido e coberto por teste de referências/IDs/carregamento. Sem vulnerabilidade ou mudança de autorização identificada no escopo.
- Evidências privadas ignoradas pelo Git: `.runtime/contracts-timeline/closeout-tests.log`, `duration-desktop.png`, `accessible-market-timeline.png` e fixtures reproduzíveis. Diff check aprovado e 21 links locais novos sem ausências. Container de testes exclusivo removido após a execução; serviços DEV preservados.

## Produção e ativação

A agenda já implantada e seus dados não devem ser reaplicados. Consulta somente leitura de 18/10/2026 confirmou 35/36/52 locked, 53/55 open; o inventário e as assinaturas foram preservados nesta tarefa. [Recibo independente da aplicação produtiva](../../operations/resolution-agenda-application-20261018.md).

Esta revisão não adiciona migration, flag, configuração, segredo, backfill ou release Flutter. Ativação acontece pelo deploy normal do Django e collectstatic (asset `css/gotrendlabs.css?v=20261018-contracts-timeline-008`). `.github/workflows/deploy.yml` executa build principal/MCP, OpenAPI, JavaScript e suíte integral na PR; em main, ENABLE_PROD_DEPLOY=1 dispara deploy via SSM. Valor 1 confirmado no GitHub durante o fechamento.

### Evidência de publicação

- [PR #173](https://github.com/wscardua/gotrendlabs/pull/173), merge `2c4ddd98a91aac7e898dc52c89b8b93a0688cf09`.
- [CI da PR](https://github.com/wscardua/gotrendlabs/actions/runs/39135544210): sucesso, 567 testes em 507.612s, 2 skips; builds principal/MCP, OpenAPI e JavaScript aprovados.
- [CI/build/deploy da main](https://github.com/wscardua/gotrendlabs/actions/runs/39136374800): sucesso, 567 testes em 502.406s, 2 skips; jobs test/deploy aprovados.
- SSM de deploy `94047fef-486d-4a2f-8d78-e45aa2c61d9e`: Success/0, concluído em 18/10/2026 14:43:41 UTC (11:43 BRT).
- Preflight somente leitura `d08e4bfc-a07f-4262-8339-d465970d5d7e`: serviços ativos, migrations já aplicadas, permissões FastAPI corretas; 7.7 GiB livres no disco, swap disponível. RDS available, backup retention 1 dia e LatestRestorableTime `2026-10-18T14:16:42Z` antes do merge; nenhuma restauração executada. Backups locais/envs não rastreados do host preservados.
- Baseline `ae71418f-f3de-417b-ae45-3687e848241c` e smoke final `999c9c37-f97f-45ef-9ef9-ecc6a6ffc222`: Success/0. Consultas na role real da FastAPI em transação REPEATABLE READ READ ONLY e timeout de 10s; respostas do serializador `_market_response` consumidas pelo helper/template reais no container Django, somente em memória.
- Mercados 35/36/52 continuam locked e renderizam Fechado; 53/55 continuam open e renderizam fechamento Planejado. Previsões futuras permanecem Planejadas, sem etapa ativa. Cinco regiões acessíveis verificadas com referências válidas e IDs únicos.
- SHA-256 das agendas (incluindo original/versão/histórico) e hashes das definições assinadas antes/depois idêntico: `f5cbf6f654ec993dfb949083517cd5a8ca7a4bf61cef2c905743bb107500b93c`. Sem alteração de mercados, inventário, critérios ou assinaturas pelo smoke.
- HTTP público: `/api/health` 200 com API/database ok; `/` 200; `/admin-ops/contracts/` anônimo continua redirecionando para login. CSS versionado 008 HTTP 200, conteúdo idêntico ao arquivo da release, SHA-256 `48a5c5dae7867828887e19c5379e269460ce8eaef4deaad343ef631419fcc6cc`.
- Django/FastAPI/daemon/thumbnail-worker ativos e MCP healthy com health interno 200; proxy ativo. A feature ficou ativa pelo deploy/collectstatic normal, sem flag ou configuração adicional.
- Primeiro probe interno `b24cf13b-20bb-4e02-9f8b-9f04c0a702ba` falhou na invocação do renderer sem settings Django explícitos; repetição com `DJANGO_SETTINGS_MODULE=config.settings` passou. Não exigiu alteração/rollback do runtime ou dados.

Os dois runs completos têm cobertura sobreposta; não somar seus testes. Logs/evidências privadas em `.runtime/contracts-timeline/{pr-ci.log,main-ci.log,main-tests.log,production-http-before.json,production-http-after.json,release-evidence.json}` na worktree da implementação.

## Impactos, limites e checklist

API/OpenAPI e cliente Django inalterados. Mobile não impactado: `apps/mobile/lib/src/features/markets/market_models.dart` continua consumindo resolution_schedule/published_at/seal_due_at/sealed_at existentes. MCP mantém ferramentas, schemas, contratos, scopes/permissões, códigos de erro, replays e orientação editorial; nenhuma capacidade nova inferida de ações humanas do Admin Ops. Eventos de domínio, ledger/assinaturas, finanças e automações não mudam.

Sem nova fronteira/dependência ou ADR; integration-map não requer ajuste. Specs, contrato de ciclo, aceites, README, changelogs, status, known-gaps, workflow e memória devem apontar este recibo. Checklist universal/alterar-feature/implementação/testes aplicado; publicação técnica concluída com CI/deploy/smoke; registro documental final reconcilia o estado pendente anterior. Limites: timestamp real de fechamento indisponível, escala adaptada com piso, QA visual local e smoke técnico do template produtivo em memória, sem sessão humana autenticada no navegador produtivo; VoiceOver nativo/fontes ampliadas não executados.
