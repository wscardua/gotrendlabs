# Fechamento local — suíte completa em 02/11/2026

WFLOW-20261102-MCP-LIFECYCLE-CLOSEOUT, base origin/main b6a0649, branch feature/mcp-resolve-cancel-markets. Estado: preparado para PR após aprovação do título/descrição; nenhuma submissão/merge/deploy desta fatia nesta etapa.

Executado `.venv/bin/python .runtime/run_tests.py` sem filtros em PostgreSQL 16 isolado (container temporário gtl-mcp-closeout-tests, porta 55439, tmpfs de 1 GiB). Resultado: **637 testes em 490,121s, OK (skipped=2)**: 635 aprovados. Os dois skips são checks de roles nomeadas ausentes no cluster temporário; a role temporária do teste da migration nova foi exercitada e aprovada, e as ACLs existentes foram verificadas por leitura no DEV conforme recibo anterior. Sem acesso ao banco operacional para a suíte. O ambiente virtual existente é Python 3.11; CI valida Python 3.12 e as duas imagens.

Também aprovados: node tests/test_analytics_web_events.js, node tests/test_prediction_preview_web.js, manage.py check, makemigrations --check --dry-run, export_openapi.py --check, Ruff F nos módulos/tests afetados e git diff --check. Validação documental comparou a tabela normativa com TOOL_SCOPES e a listagem do SDK: 21 ferramentas, nove scopes, correspondência exata. Nenhuma nova verificação repetida sem mudança/falha.

Triagem mobile: nenhum arquivo Flutter alterado; apps/mobile/lib não consome /integrations/editorial ou /oauth. A mudança de sessão é restrita à view Django do consentimento; contratos públicos de auth/mercados e MFA permanecem. Mobile não impactado por esta fatia.

GitHub MCP confirmou acesso ao repositório e ausência de PR aberta desta branch. Consulta de Actions/variável pela CLI confirmou ENABLE_PROD_DEPLOY=1 e último deploy main b6a0649 / Actions 40319310275 success; nenhuma evidência desse run se aplica ao código ainda local. [Rollout desta entrega](../operations/mcp-market-lifecycle-rollout.md) prevê migration 0007/ACL, build principal+MCP e smoke técnico após merge, sem conceder scopes ou mutar mercados produtivos por inferência. Recursos temporários de teste removidos após validação.

---

# Validação vigente — exclusão de draft MCP (02/11/2026)

WFLOW-20261102-MCP-DELETE-DRAFT, mesma branch. Acrescentados 6 testes funcionais e 1 de contrato para delete_market_draft/drafts:delete; catálogo 21. Atualizados os dois testes SDK de listagem. Integração Streamable HTTP real executou exclusão e replay por serviço e OAuth, confirmou ausência posterior pelo get_market e preservou cancelamento/validações existentes.

Comando: `.venv/bin/python .runtime/run_tests.py tests.test_mcp_editorial tests.test_mcp_market_actions tests.test_market_deletion tests.test_mcp_adapter tests.test_mcp_packaging tests.test_mcp_schedule_errors`. O runner local ignorado configura PostgreSQL 16 temporário em 55439 e banco de testes dedicado, sem usar banco operacional. Resultado: 117 testes em 158,138s, OK (skipped=2), portanto 115 aprovados e nenhuma falha. Os 2 skips são ACLs de roles nomeadas ausentes no cluster temporário; no DEV, consulta read-only confirmou EXECUTE da função restrita para gotrendlabs_fastapi, negação para gotrendlabs_django e ausência de DELETE geral em revisões para FastAPI. Teste ACL dos novos recibos com roles temporárias continuou aprovado.

Cobertura adicional: autoria própria, negação de draft humano/scope ausente/token antigo; preparação e revisão; rejeição de aprovados/devolvidos/rejeitados/publicados/terminais/previsões; revisões/updated_at obsoletos; exclusão física de ficha/revisões; auditoria técnica/motivo; rollback de auditoria inclusive marcadores de criação; concorrência idêntica; replay sem recriar ou excluir novo ID do mesmo slug; pausa bloqueando replay e payload diferente conflitante. Regressões humanas cobrem previsões/provas/dependências e corrida com revisão.

Django check, makemigrations --check --dry-run, OpenAPI --check, Ruff F e diff --check aprovados. Sem nova migration; reutiliza agent_idempotency e função de exclusão física existentes. Runtime DEV auto-recarregou: web/API/MCP 200, catálogo 21, metadata anuncia drafts:delete e OpenAPI atualizado. Nenhum mercado operacional foi excluído para smoke; os DELETEs reais ficaram no banco de testes. Nenhum scope/grant real foi ampliado e produção não foi alterada. Recursos temporários de teste removidos após validação.

---

# Evidências locais — MCP resolve/cancel

Data: 02/11/2026. Workflow WFLOW-20261102-MCP-RESOLVE-CANCEL. Branch feature/mcp-resolve-cancel-markets, base origin/main b6a0649. Checkout original preservado. Sem commit/push/merge/deploy ou alteração produtiva.

## Ambiente

Ambiente virtual existente `/Users/williamsca/Documents/gotrendlabs-mcp/.venv`, Python 3.11.0, Django 4.2.30, MCP SDK 1.30.0. O .venv do checkout original usa Python 3.9 e não atende MCP >=3.10; foi reutilizado o ambiente MCP já instalado, sem reinstalar dependências.

PostgreSQL 16 isolado em container temporário gtl-mcp-actions-tests, porta local 55439, banco de testes test_gtl_mcp_actions_20261102. O disco do Docker não comportou a primeira inicialização; o cluster temporário usou tmpfs, sem remover dados/volumes alheios. A primeira tentativa de teste ACL no banco compartilhado não tinha CREATEROLE; a validação final ocorreu no cluster isolado, incluindo roles restritas criadas transacionalmente. Recursos temporários removidos após validação.

## Resultados

| Execução | Resultado |
| --- | --- |
| 6 testes de fronteira do adaptador/consentimento | OK |
| 134 testes MCP, adaptador, consentimento, resolução confiável, ACL e agenda | 132 passaram, 1 skip por roles dedicadas ausentes e 1 expectativa antiga de catálogo falhou; expectativa atualizada para 20 tools |
| 21 testes novos + integração real Streamable HTTP (22 testes) | OK em 48,936s, incluindo reexecução da expectativa corrigida |
| Integração real ampliada + empacotamento MCP + erros de agenda (5 testes) | OK em 17,043s |
| Django check | Sem problemas |
| makemigrations --check --dry-run | Sem mudanças pendentes |
| Export OpenAPI e --check | Snapshot atual |
| Ruff F nos arquivos afetados e diff --check | OK |

Os erros de assinatura nos logs são falhas injetadas para testar rollback, com resposta 503 esperada. Suite completa do repositório não foi executada; foram selecionadas regressões de MCP e lifecycle.

## Cobertura

Os 21 testes novos cobrem scopes/catálogo/annotations, schemas estritos e dados obrigatórios, fonte HTTP(S), offset/fuso, datas futuras, opção alheia, estados, IDs e updated_at, grants/tokens sem ampliação, revogação/pausa inclusive entre admissão e transação, autoria técnica, respostas mínimas, rollback de assinatura/recibo, refunds/reputação, replay/undo/seal, conflitos de payload, namespace entre integrações, concorrência com humano/outra integração, drafts próprios, cancelamento open/scheduled, triggers append-only e ACLs reais consultadas via PostgreSQL.

O cliente SDK real usa autenticação de serviço e OAuth: lista 20 tools, chama as ferramentas editoriais existentes, lê IDs/versão, recebe resolution_state_conflict ao tentar resolver draft e executa cancel_market com replay confirmado. Resolução MCP bem-sucedida, liquidação e assinatura foram testadas via REST autenticado real/FastAPI TestClient com PostgreSQL e engine completos. Timeout do adaptador foi injetado e produziu operation_indeterminate sem novo POST.

## Limites e ativação

Migration editorial_integrations.0007 cria recibos imutáveis sem conceder scopes. Deploy API+MCP, CI produtivo, latência KMS real, ACLs produtivas e smoke controlado com cliente externo permanecem pendentes. Admin staff/MFA deve conceder markets:resolve/markets:cancel e obter novo consentimento OAuth ou novo token de serviço. A fatia local foi concluída; não representa promoção global do MCP nem implantação. [Runbook](../../guides/mcp-market-lifecycle.md).


Review de fechamento: intervalo versionado b6a0649..c778b88, 37 arquivos, nenhum finding identificável. [Escopo, triagem mobile e limites](mcp-market-lifecycle-review.md). Commit e branch locais preservados; PR ainda aguardando aprovação da descrição.
