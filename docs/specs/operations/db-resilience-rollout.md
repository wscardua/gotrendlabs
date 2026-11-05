# Rollout proposto — resiliência de conexões

Implementação local `WFLOW-20261105-PRD-DB-RESILIENCE`; nenhuma etapa abaixo foi executada em PRD.

1. Conferir build CI Python 3.12, testes PostgreSQL e OpenAPI. Validar Compose com arquivos segregados e checar que Django/daemon usam apenas role Django; FastAPI/thumbnail worker usam role FastAPI.
2. Confirmar topologia efetiva: dois workers Django, um FastAPI, um daemon e um thumbnail worker. Para mais processos, recalcular [ADR-0020](../decisions/ADR-0020-database-capacity.md). Conferir limite RDS e margem sem modificar `max_connections`.
3. Fazer deploy pelo fluxo normal de PR/main somente após revisão. Durante sobreposição de gerações, acompanhar `DatabaseConnections`, memória livre, 5xx, timeouts percebidos pelo cliente e p95/p99. Verificar `/health`, `/api/markets`, detalhe web público/autenticado, integridade, analytics, login e leitura MCP. Um 503 controlado sob pico deve recuperar ao liberar capacidade; timeout direto da API permanece possível quando a conexão existente deixa de responder.

   Após o follow-up de revisão, conferir também a frequência dos probes: `/health` aceita duas consultas simultâneas por processo, sem fila. Excedente retorna 503 degradado com o shape de health e sem abrir conexão. Verificar que esse 503 não provoca tempestade de probes e que o tráfego normal mantém latência aceitável.
4. Se houver 503 persistente em tráfego normal, timeouts de cliente acima do limite aceito, indisponibilidade do pool, erro de permissão, resultado indeterminado sem possibilidade de confirmação ou queda de memória, interromper rollout e reverter código/imagem/limites como conjunto. Não repetir mutações com chave nova. Confirmar estado por recibo antes de ação humana.
5. Mudança de retenção PRD, TLS, capacidade RDS, alertas e pipeline externo ficam em processos separados. Não apagar logs/recibos para rollback.

Sem ensaio de carga equivalente em ambiente isolado, o orçamento é teto de configuração, não garantia de throughput. O build local foi bloqueado por espaço do Docker; CI deve comprovar a imagem antes da implantação.
