# Aceite local — etapas do Painel de contratos (18/10/2026)

WFLOW-20261018-CONTRACTS-TIMELINE. Branch `fix/contracts-timeline-states`, baseada em `origin/main` e914df7; worktree `/Users/williamsca/Documents/gotrendlabs-contracts-timeline`. As alterações preexistentes do checkout principal e da worktree da agenda não foram copiadas, descartadas ou modificadas.

## Resultado

- Fechamento: locked/resolved/sealed mostram Fechado por estado. A data continua explicitamente programada; não se fabrica instante efetivo. Open/scheduled com classificação `closure_inconsistent` mostram alerta sem concluir a etapa.
- Resolução prevista: `resolution_overdue` mostra Previsão vencida; nenhuma previsão recebe etapa ativa ou conclusão pelo relógio. Terminais mostram informação histórica, mesmo quando a antiga previsão ainda está no futuro.
- Cancelado: resolução/selagem sem registro mostram Não se aplica, sem obrigação futura. Resolved/sealed sem timestamp informam a ausência da data em vez de uma resolução futura pendente.
- Selagem: registro `sealed_at` e prazo `seal_due_at` têm identificação própria; prazo vencido não conclui a ação. Undo real preserva agenda e histórico e limpa resolução/prazo pelo backend existente.
- Marcos: Hoje com horário/fuso, datas completas em nomes acessíveis, faixas verticais distintas para coincidências, sem deslocar o instante horizontal. Escala inclui publicação/selagem/prazo e é construída antes de Carregar mais.
- Criação/publicação/resolução com registros efetivos continuam concluídas. Previsão original, histórico escapado, critérios e provas preservados.

## Consulta produtiva somente leitura

MCP `get_market`, em 18/10/2026, confirmou:

| ID | Estado atual | Fechamento programado (UTC) | Previsão (BRT) |
|---|---|---|---|
|35|locked|14/10 23:30Z|25/10/2026 20h|
|36|locked|15/10 19:00Z|09/11/2026 20h|
|52|locked|16/10 02:59Z|04/11/2026 20h|
|53|open|22/10 23:00Z|31/10/2026 20h|
|55|open|26/10 21:00Z|31/10/2026 20h|

35/36 retornaram inicialmente quota_exceeded; suas páginas públicas confirmaram encerramento para previsões e aguardo de resultado. Após intervalo natural do trabalho, nova consulta MCP confirmou locked. Sem reexecução do inventário, backfill, mutação, assinatura ou deploy.

## Testes e inspeção

Ambiente virtual existente: `/Users/williamsca/Documents/gotrendlabs-ai-thumbnails/.venv` (Python 3.11). A `.venv` principal usa Python 3.9 e não suporta os tipos atuais da main; foi preservada. PostgreSQL 16 em container dedicado `gotrendlabs-contracts-test`, porta 55439, banco de testes separado. A primeira inicialização falhou por falta de espaço no armazenamento Docker; o container exclusivo da tarefa foi recriado com armazenamento temporário em memória, sem limpeza de recursos alheios.

Com `POSTGRES_USER=gtl_test POSTGRES_PASSWORD=gtl_test POSTGRES_DB=gtl_contracts POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=55439 BACKEND_API_URL=http://127.0.0.1:59999`:

```
python manage.py test tests.test_resolution_agenda tests.test_web_smoke.WebSmokeTests.test_admin_contracts_timeline_uses_active_market_contract_dates tests.test_web_smoke.BackendAuthAPITests.test_market_resolution_distribution_math_undo_and_refund_audit --noinput --keepdb
```

37 testes aprovados em 11.566s. Incluem nova matriz de sete estados, passado/futuro/ausência, fronteiras de classificação, fusos, horário no mesmo dia, sete marcos coincidentes, data de selagem/prazo, resolução desfeita real, histórico, filtros/contadores/ordenação/paginação, assinatura/rollback e fluxo real de resolução/cancelamento isolado. `manage.py check` e `git diff --check` aprovados. Não houve alteração de API/schema nem necessidade de regenerar OpenAPI.

Chrome local com template/CSS/JS reais e fixtures sem chamadas produtivas, 1440×1000 e 390×844: leitura das etapas, datas/fusos, terminais, selagem, prazo vencido e coincidências conferidos; temas claro/escuro desktop, foco visível, Tab até reagendamento e Enter em histórico. Nenhuma fase com overflow (`scrollWidth > clientWidth`); documento sem overflow horizontal. Grade desktop com três colunas quando necessário; duas colunas estreitas e datas usando a largura completa do cartão. Capturas e fixture reproduzível ignoradas pelo Git em `.runtime/contracts-timeline/`: `desktop.png`, `narrow.png`, `narrow-row.png`, `coincident-narrow.png`, `terminal-dark-desktop.png`, `render_fixture.py`, `index.html`; logs locais preservados no mesmo diretório.

## Impactos e limites

Sem alterações em estado, persistência, transições, autenticação, elegibilidade, cliente API ou eventos. MCP: ferramentas, schemas, contratos, scopes, permissões, erros, replays e orientação editorial inalterados; sem novas permissões. Flutter não consome esta apresentação administrativa e continua no mesmo contrato. Integration map e ADR-0016 não exigem atualização, pois não mudam dependências ou decisões estruturais. Documento da aplicação produtiva e inventário permanecem fotografias imutáveis.

Checklist universal, alterar feature, implementação e testes de `workflow-checklists.md` aplicado. Escopo local concluído; PR aguarda aprovação explícita do título/descrição em português. Sem push, PR, merge ou deploy. A validação visual usa fixtures locais; não representa homologação do painel produtivo após implantação. O contrato não informa instante efetivo de fechamento; essa limitação é explicitada na UI.
