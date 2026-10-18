# Resolução prevista — runbook vigente (revisão 1.1)

Esta revisão substitui o escopo de três prazos. A API, MCP/editorial, web e Flutter usam somente previsão e fuso. Backend e clientes devem usar o contrato atual.

1. Atualizar inventário v2 via consulta autorizada somente leitura; registrar cobertura, consulta e revisão/hash/estado. Não inferir horários nem transferir revisão do formato anterior. IDs 45/51/52 têm candidatos explícitos; demais exigem decisão operacional, sem preencher pelo fechamento. Nenhum item atual está aprovado.
2. Antes de aplicação futura, obter autorização, backup completo recuperável e verificar restauração/grants em staging. Preservar definição/assinaturas/previsões/histórico.
3. Aplicar schema 0033–0036 com migration role e backend coordenadamente. Migration 0036 retira corte/recuperação do modelo ativo e constraints; retém colunas físicas apenas para verificar provas já assinadas. Não executar purge nem remover essas colunas.
4. Publicar backend/MCP e clientes atuais coordenadamente; política 1.4 e ficha 1.8 exigem nova revisão/snapshot, sem reutilizar parecer anterior para conteúdo alterado.
5. Rodar `python manage.py migrate_resolution_agenda INVENTARIO_V2` (dry-run padrão); revisar os resultados. Aplicação autorizada exige `--apply --actor-id STAFF --backup-confirmed`. Revalidação estado/hash/revisão/versão, transação e idempotência continuam obrigatórias.
6. Conferir projeção versus ledger, assinaturas e provas históricas, rótulos/filtros/painel e todos os ativos abrangidos regularizados. Ausência em ativo é pendência, nunca data fictícia. Terminal histórico sem agenda não recebe previsão fabricada.
7. Reversão: interromper novas mutações e corrigir adiante preservando colunas/eventos; não voltar a um binário que imponha corte/recuperação nem apagar provas novas.

Publicação exige previsão futura posterior ao fechamento e fuso; resolução exige agenda regularizada/verificada e regras normais do ciclo, mas a previsão não bloqueia nem dispara decisão. Não há alteração financeira por atraso. Novos reagendamentos mantêm original e histórico, sem prorrogar/reinterpretar critérios.

Fechamento de 17/10/2026: o usuário solicitou commit/PR/merge/deploy com acompanhamento produtivo, condicionado à apresentação e aprovação prévia da descrição da PR. A descrição foi aprovada e a [PR #170](https://github.com/wscardua/gotrendlabs/pull/170) aberta. CI/backup/merge/deploy são acompanhados; a timeline da PR registra o resultado operacional posterior a esta revisão. Fazer backup/preflight antes do merge e acompanhar Actions/smoke. Complementos de dados continuam exigindo inventário atualizado e revisão explícita por mercado; autorização operacional não constitui parecer editorial nem permite inventar horários. Ver WFLOW-20261017-RESOLUTION-AGENDA-CLOSEOUT.

Incidente do primeiro rollout: migrations 0033–0036 e grants aplicados, mas imagem MCP falhou por dependência de módulo de domínio. Recuperação operacional concluída via imagem com contrato puro, sem backfill. Não reexecutar o deploy do código sem a correção de empacotamento; integrar contrato puro/Dockerfile e build MCP no CI antes do próximo deploy. Evidências e hashes no fechamento da agenda e timeline da PR #170.
