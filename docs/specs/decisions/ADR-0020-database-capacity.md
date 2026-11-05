# ADR-0020 — Orçamento de conexões e degradação controlada

Status: aceito para implementação local em `WFLOW-20261105-PRD-DB-RESILIENCE` (05/11/2026). Implantação produtiva pendente.

## Contexto

O RDS produtivo possui `max_connections=79`, com vagas reservadas e cerca de 150 MiB de memória livre antes da rajada observada. Em 05/11, conexões chegaram ao limite e a web tentou consultar o mesmo banco após timeout da API. FastAPI usa psycopg em muitos serviços; Django usa ORM próprio; logs técnicos também consomem conexões. Pool por processo não é limite global.

## Decisão

Follow-up de revisão: `/health` admite no máximo duas requisições simultâneas por processo e rejeita as demais imediatamente com 503 degradado, sem abrir conexão; usa o pool FastAPI já orçado. A web preserva 4xx da API ao rastrear compartilhamentos e transforma apenas falhas de conexão Django em 503, sem mascarar `IntegrityError`.

- `get_connection()` usa pool Psycopg lazy por PID e configuração de credenciais. `min_size=0`, máximo e fila limitados, aquisição por até 1 segundo e `connect_timeout=2`. O contexto preserva commit/rollback e devolução em exceções. A imagem instala `psycopg[pool,binary]`.
- Web admite até cinco requests por worker antes de sessão, context processors e ORM; até vinte adicionais aguardam por no máximo 750 ms, sem abrir conexão. Excedente recebe página 503 estática. FastAPI admite até 12 requests, com espera de 200 ms. `/health` mantém sua verificação própria de banco e payload mobile.
- FastAPI converte falta de capacidade e `OperationalError` para 503 com código estável. Rejeição antes da operação (admissão ou aquisição do pool) usa `dependency_unavailable` em qualquer método. Falha de conexão durante escrita usa `operation_indeterminate`, pois resposta perdida não prova rollback. Nenhum retry automático é feito. Auth, manutenção mobile, atualização, OAuth e códigos de domínio continuam com os caminhos existentes quando a request é admitida.
- Detalhe, integridade e compartilhamento web não consultam ORM como fallback depois de falha da API. Erro web usa HTML independente de templates/context processors. Detalhe usa projeção API para posição aberta; para resultado pessoal terminal, a leitura ORM existente permanece protegida contra `DatabaseError` até contrato backend específico substituí-la.
- Logger técnico de request roda em thread daemon separada, sem reter a resposta HTTP, usa o mesmo pool limitado e cache de retenção de 60 s (5 s quando consulta falha). O handler de logging raiz ignora callbacks que ocorrem no event loop. Uma vaga não bloqueante por processo evita fila técnica e consultas aninhadas simultâneas; o excedente técnico é descartado. Eventos administrativos, recibos de idempotência e ledger continuam transacionais.

## Orçamento inicial do Compose produtivo

| Processo | ORM/admissão | Psycopg | Teto estimado |
| --- | ---: | ---: | ---: |
| Django, 2 workers | 5 por worker | 2 por worker | 14 |
| FastAPI, 1 processo | — | 8 | 8 |
| Daemon | até 1 | 2 | 3 |
| Thumbnail worker | — | 2 | 2 |
| **Uma geração** | | | **27** |
| **Duas gerações durante deploy** | | | **54** |
| Migração operacional eventual | até 1 | até 4 padrão | até 5 |

Pico estimado com sobreposição e migração: **59** conexões de aplicação, antes de conexões operacionais externas. Com limite SQL observado de 79 e cinco vagas PostgreSQL reservadas, restariam aproximadamente 15 vagas para RDS/operação. Este cálculo é teto de configuração, não capacidade de throughput comprovada. Pressupõe um daemon, um worker de thumbnails, um processo FastAPI e dois workers Django por geração; alteração de réplica/worker exige recálculo antes do deploy. Scripts administrativos externos não estão incluídos. Caddy/MCP não acessam PostgreSQL diretamente.

## Consequências e validação

Excedente pode receber 503 em vez de saturar o banco. Um 503 em escrita exige confirmação/replay pela chave existente, quando houver; cliente não inventa nova chave. Pool por role mantém fronteira de credenciais. Cache de retenção pode levar até 60 s para refletir configuração alterada. Logs técnicos podem ser perdidos sob saturação; auditoria transacional não.

Antes do rollout, ensaiar número real de workers em ambiente isolado, medir conexões, espera, memória e 5xx, conferir configuração resultante do Compose com ambientes segregados e planejar rollback completo de código/limites. Alterar apenas `max_connections` não é mitigação adotada.
