# Ensaio local de rajadas e indisponibilidade — 05/11/2026

Vinculado a `WFLOW-20261105-PRD-DB-RESILIENCE`. Este ensaio usou somente uma stack isolada em `127.0.0.1`: PostgreSQL 16 em tmpfs com `max_connections=79`, uma FastAPI, dois workers Django, quatro mercados sintéticos migrados/semeados e Python 3.11. Portas de ensaio: 15435, 18001 e 18003. Nenhum endpoint de PRD foi chamado. A stack local normal (8000–8003) permaneceu separada.

Configuração final: pool FastAPI máximo 8/fila 8, pool psycopg web máximo 2 por worker, admissão API 12/200 ms e web 5 ativos + 20 aguardando até 750 ms por worker. O monitor de conexões usou uma conexão própria.

## Resultado com endpoints reais

Mistura igual de `GET /markets`, `GET /stats`, home web, detalhe web e integridade web:

| Perfil | Requisições | 200 | 503/500/timeout | p95 | Máximo |
| --- | ---: | ---: | ---: | ---: | ---: |
| 3 rajadas de 10 | 30 | 30 | 0 | 83 ms | 87 ms |
| 3 rajadas de 20 | 60 | 60 | 0 | 169 ms | 183 ms |
| 3 rajadas de 40 | 120 | 120 | 0 | 305 ms | 339 ms |
| 1 rajada de 80 | 80 | 80 | 0 | 615 ms | 695 ms |
| 20 req/s por 10 s | 200 | 200 | 0 | 57 ms | 71 ms |

Rajadas somente web, divididas entre home, detalhe e integridade: 60/60 respostas 200 em 3 rajadas de 20 (p95 201 ms), 120/120 em 3 rajadas de 40 (p95 383 ms) e 80/80 numa rajada de 80 (p95 834 ms, máximo 864 ms). O pico observado na rodada mista foi **15 conexões PostgreSQL**, incluindo o monitor, e quatro conexões ativas no momento amostrado. Não houve 500 nem timeout nessas cargas isoladas por perfil. Ao executar os dois geradores ao mesmo tempo, sete páginas web receberam 503 controlado entre 750 requests sobrepostas; não houve 500 ou timeout. Isso confirma que a fila não elimina 503 sob sobrecarga combinada.

Ensaios de limite: pool máximo 4/fila 8 sob 40 consultas `pg_sleep(0.25)` simultâneas teve oito conclusões, 32 rejeições controladas e consulta subsequente bem-sucedida. API HTTP isolada, com handler sintético de 500 ms, teve 12 respostas 200 e 28 respostas 503 em rajada de 40, seguida de 200; o controle de admissão é finito.

## Banco sem resposta

O contêiner PostgreSQL isolado foi pausado e liberado sem perda de dados. Cinco acessos web de detalhe responderam **503** antes do timeout de cliente de 6 s. Na API direta, quatro leituras responderam **503** e uma atingiu o timeout do cliente enquanto uma conexão existente aguardava o banco. Web e API voltaram a responder 200 após liberar o banco; o segundo poll de recuperação foi bem-sucedido. O logger técnico foi retirado do caminho de resposta após o primeiro ensaio ter causado dois timeouts web adicionais.

## Limites da evidência

Os dados são sintéticos e pequenos; CPU, memória, rede, latência, distribuição de tráfego e reservas de conexão não reproduzem o RDS/EC2 de PRD. Uma conexão estabelecida com servidor que deixa de responder pode continuar bloqueada até o timeout do cliente. Mobile e MCP precisam preservar o tratamento de timeout/resultado indeterminado já testado; não se presume rollback. A fila web reduz 503 em rajadas curtas, mas não promete zero 503 sob sobrecarga ou falha de banco. Antes de rollout, validar build/CI Python 3.12, topologia efetiva, memória, p95/p99 e taxa de 503 em ambiente equivalente, como no [runbook](../operations/db-resilience-rollout.md).
