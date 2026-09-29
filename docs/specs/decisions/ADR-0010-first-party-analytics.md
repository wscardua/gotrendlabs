# ADR-0010 — Analytics proprio de produto

- Status: aceito para implementacao incremental
- Data: 2026-09-29
- Feature: `FEAT-ANALYTICS-001`

## Contexto

GoTrendLabs precisa observar navegacao, cliques, funis, geografia aproximada e diferencas web/mobile sem plataforma externa de analytics. O dashboard operacional atual agrega estado do dominio, mas nao registra jornadas de visitante.

## Decisao

- FastAPI e autoridade para validacao, identidade, persistencia, relatorios e insights. Django encaminha lotes da web e renderiza Admin Ops; Flutter envia lotes diretamente.
- PostgreSQL armazena visitantes, sessoes, visualizacoes e eventos de coleta. Eventos do navegador sao observacoes nao confiaveis, com catalogo fechado, propriedades limitadas, UUID idempotente e identidade definida pelo servidor.
- A conclusao de operacoes de dominio e lida das tabelas autoritativas existentes nesta primeira etapa. Totais gerais sao globais. O funil de primeira previsao para contas autenticadas vincula `user_id` e mercado entre o inicio observado do ticket e uma previsao persistida em ate sete dias; representa associacao temporal, nao um identificador transacional de tentativa. Nenhum evento de cliente pode se passar por conclusao.
- `user_id` em eventos e uma referencia logica sem FK para `gotrendlabs_users`: evita bloquear o flush/migracoes de tabelas de dominio e permite retencao independente; o ID so e atribuido a partir de sessao autenticada validada pela FastAPI.
- Localizacao e resolvida por consulta local opcional da GeoLite City. Sem arquivo, a geografia aparece desconhecida.
- Retencao detalhada padrao de 90 dias, executada pelo daemon por funcao da camada backend. Auditoria/ledger nao sao afetados.

## Consequencias

- Contagens de navegacao sao estimativas: bloqueio de scripts, ausencia de coleta e reenvios offline podem reduzir cobertura.
- `visitor_id` identifica navegador/instalacao, nao pessoa. A mesma conta pode ter varias sessoes e regioes.
- Funil de sessoes termina na intencao de confirmar; um indicador separado associa contas autenticadas que iniciaram ticket a primeira previsao persistida no mesmo mercado em ate sete dias. Atribuicao exata por tentativa exige contexto transacional futuro.
- Séries diárias e retenção D1/D7/D30 por coortes semanais estão no dashboard. Agregados materializados, controles de preferência, comparação avançada de coortes e ampliação do catálogo permanecem evoluções documentadas, sem afirmar cobertura onde ainda não há instrumentação.
