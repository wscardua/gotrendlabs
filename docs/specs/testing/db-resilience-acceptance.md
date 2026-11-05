# Aceite: resiliência de conexões e indisponibilidade

WFLOW-20261105-PRD-DB-RESILIENCE. A investigação de PRD é [separada](../operations/prd-error-investigation-20261105.md).

## Cenários

- Follow-up de revisão: 404 de compartilhamento para mercado inexistente/draft, 503 de indisponibilidade e 4xx preservados; `IntegrityError` não é mascarado como capacidade. Rajada de 20 health checks com admissão saturada deve retornar 503 degradado sem consulta ao banco, enquanto request comum continua 200.

- Pool psycopg em PostgreSQL isolado: duas conexões ocupadas impedem a terceira após espera limitada; liberar uma permite nova consulta; erro dentro do contexto faz rollback; `close_pools()` encerra e nova aquisição recupera; configuração por PID/credencial mantém isolamento de roles.
- Admissão: web mantém cinco ativos e até vinte em espera por 750 ms; rajadas curtas observadas concluem sem 503, excedente recebe 503 estático e libera vaga após conclusão. FastAPI excedente recebe 503 sem iniciar domínio. `/health` continua com seu contrato de manutenção e checks.
- API: falha de admissão/aquisição antes da operação retorna 503 `dependency_unavailable`; perda de conexão durante escrita retorna 503 `operation_indeterminate`, sem detalhes internos, retry automático ou presunção de rollback.
- Web: timeout/503 da API não chama `local_market`, não conta view e retorna HTML 503 sem template/context processor; 404 fica 404; payload sem IDs é rejeitado; sessão autenticada não vaza draft.
- Logs: consulta de retenção é amortizada; middleware web/API envia log técnico em thread daemon, com uma vaga e sem fila, sem reter resposta; falha de banco não quebra request nem recursa; redaction permanece. Auditoria de domínio/ledger/recibos não depende dessa thread técnica.
- Mobile: 503 geral preserva token e mostra estado temporário; `mobile_maintenance` distinto; detalhe tem retry explícito; escrita incerta não é repetida automaticamente.
- MCP: leitura 503/timeout mapeia dependência; escrita incerta conserva payload/chave e replay; scopes, schemas, ferramentas e orientação editorial intactos.

## Evidências locais

- Reprodução do CI da PR #188 após falha de teardown do run 42077291104: o runner fecha pools antes de destruir o banco de testes. Execução local com a mesma seleção do CI (sem `GTL_RESILIENCE_TEST_DB`) em Python 3.12/PostgreSQL 16 isolado: **674 testes, 3 skips, zero falhas**, destruição do banco concluída. O run inicial do CI não foi aprovado, embora as asserções tenham passado; novo CI é obrigatório antes do merge.

- Fechamento local em Python 3.12.13 e PostgreSQL 16 temporário isolado em `127.0.0.1:15436`, com `GTL_RESILIENCE_TEST_DB=1`: suíte integral `manage.py test --noinput` executou **677 testes, 2 skips, nenhuma falha** em 286,506 s; banco de testes encerrado sem conexões remanescentes. A primeira execução no PostgreSQL DEV revelou permissão `CREATEROLE` ausente e corrida entre logger técnico e `flush`; o isolamento de testes foi corrigido. Uma execução isolada intermediária usou `FASTAPI_POSTGRES_DB` fixo incorretamente, fora do banco `test_gotrendlabs`; após remover esse override, o teste de health e a suíte integral passaram. Nenhuma dessas execuções com falha foi marcada como aprovada.

- Follow-up de revisão 05/11: `tests.test_db_resilience` executou 23 testes em Python 3.11, com 22 aprovados e um skip previsto de PostgreSQL isolado não configurado nesta rodada. O teste concorrente disparou 20 chamadas de `/health` saturadas, todas 503 degradadas sem conexão, e `GET /` continuou 200. Este ensaio não substitui a rajada anterior com endpoints reais nem comprova latência produtiva.
- Smoke HTTP local na worktree com recarga automática: `GET /` e `GET /health` 200; `POST /share/market/review-nonexistent-20261105/track/` 404. Rajada read-only de 40 chamadas a `/health` com 20 threads: 2 respostas 200 e 38 respostas 503 controladas; `GET /` voltou a 200 imediatamente depois. Nenhum endpoint de PRD foi chamado.

- `tests.test_db_resilience`, preview web e adaptador MCP: **34/34 aprovados** em PostgreSQL 16 isolado e Python 3.11 temporário; `.venv` existente Python 3.9 foi usado para inspeção, mas não importa módulos atuais com sintaxe 3.10+.
- Ensaio concorrente isolado: 40 consultas PostgreSQL simultâneas de 250 ms com pool máximo 4/fila 8 resultaram em 8 conclusões, 32 rejeições controladas, pico do pool 4 e recuperação na consulta seguinte. Web sintética com 10 requests simultâneos de 100 ms passou de 5 respostas 200/5 respostas 503 para 10 respostas 200 com fila de espera limitada. API HTTP real em porta isolada: 20 requests de 100 ms deram 20 respostas 200; 40 requests de 500 ms deram 12 respostas 200/28 respostas 503, seguidos de recuperação 200.
- Flutter `test/api_client_test.dart`: 10 testes aprovados; `flutter analyze --no-pub` sem issues.
- Django `manage.py check` e OpenAPI export/check aprovados no Python 3.11.
- Regressões web com fixtures PostgreSQL: primeira execução foi limitada pelo tmpfs de 128 MiB do contêiner isolado (`DiskFull`); após recriar apenas esse contêiner com tmpfs de 1 GiB, **107/107 aprovados**. Fixtures de páginas antes dependentes do fallback ORM agora fornecem payload API explícito.
- [Ensaio ponta a ponta](db-resilience-burst-20261105.md): 490 requisições de rajadas mistas e sustentadas, mais 260 somente web, sem 500/timeout e sem 503 na configuração final; pico amostrado de 18 conexões incluindo monitor. Pausa do banco isolado: cinco páginas web 503, quatro leituras API 503 e uma com timeout de cliente, com recuperação posterior.

Ensaio de carga/capacidade equivalente a PRD, rollout e smoke produtivo não foram executados. A imagem Docker local não pôde ser construída porque o disco interno do Docker está sem espaço para `apt-get` (357 MB adicionais), apesar de contexto reduzido; isso exige validação de build no CI antes de qualquer deploy. Python 3.12 foi validado localmente em runtime separado; o build dos contêineres e o CI ainda precisam ser comprovados.
