# Investigação e aceite — detalhes de pendências editoriais

05/11/2026. Base `origin/main` bf11a0c; worktree `gotrendlabs-editorial-pending-20261105`, branch `fix/editorial-pending-details-20261105`. Checkout original com alterações locais preservado. Nenhuma mutação remota de mercados, publicação ou resolução executada. Os resultados locais abaixo são históricos; a [implantação e o smoke em produção](editorial-pending-production-closeout-20261105.md) foram concluídos.

## Causa e divergências verificadas

`editorial_service.pending` combinava versão/hash obsoletos, documento vazio e `approval_document_pending`. Este último devolvia somente `unresolved_editorial_gaps` para: seção não encontrada; declaração ausente ou repetida; primeira linha diferente de `Pendências para aprovação: nenhuma`. A expressão do título aceitava somente texto simples, embora o modelo 1.8 publicado use `## PENDÊNCIAS E CONCLUSÃO`. Assim, uma ficha seguindo o modelo recebia o aviso mesmo sem lacuna editorial. Com título simples e a frase correta, outras pendências/contradições posteriores não eram examinadas.

A rota `/integrations/editorial/drafts/validate` retorna `structurally_valid: true` depois de validar schema, prazo/anúncio, taxonomia e opções. Esse booleano não atesta pesquisa, fontes, mérito ou aprovação. A rota acrescenta `schedule_incomplete` à lista. O MCP transporta o JSON e usa `ValidationResponse` para publicar/serializar a saída; seu schema anterior só permitia explicar a lista geral, sem detalhes.

Criação/edição não usam `unresolved_editorial_gaps` como gate. Submissão exige agenda, prazo/anúncio e política vigente; também não bloqueia pelo aviso. Aprovação é atestação humana confirmada com versão/hash; publicação exige aprovação vigente/snapshot e condições operacionais. Uma lacuna essencial pode, portanto, ser persistida e enviada ao revisor: isso não a torna editorialmente aceitável para aprovação. A política exige que o humano resolva as pendências antes de confirmar. Não há classificador semântico que diferencie automaticamente uma lacuna essencial de tarefa humana futura.

A política consultada pelo MCP em produção foi 1.4 (`5027fac6bd8449f91a4d8909913c5967aba559094b3049a9448615d8d7deb2b0`), modelo 1.8. O trecho histórico da spec MCP revisão 1.5 ainda descreve gate textual de aprovação; a revisão humana posterior, o checklist vigente e os testes `test_human_attestation_*` o substituem. Esta entrega explicita a precedência, sem restaurar esse gate ou criar outro por heurística.

Mercado 62: leitura MCP em 05/11 confirmou `draft`, ficha `in_review`, revisão 3, `updated_at=2026-11-01T08:12:04.229138Z`, política 1.4. A ficha usa título Markdown e registra pendências humanas E06/E09/E10/E11; isso é suficiente para explicar o código no algoritmo anterior. O estado observado é compatível com a submissão histórica relatada, sem provar cada resposta histórica. Não foi revalidado nem alterado. Não tivemos o documento exato do xadrez: o relato e o modelo explicam causas possíveis, mas não permitem afirmar qual trecho daquela ficha acionou o aviso.

## Solução e limites

A FastAPI explica os avisos em `editorial_pending.py`; MCP usa o mesmo schema, sem duplicar decisão. `pending` mantém os códigos/shape e os argumentos da ferramenta não mudam. Saída acrescenta `pending_details` e `assessment_scope=structural_and_explicit_declarations_only`.

Cada detalhe contém código geral, motivo específico, descrição, trecho (ou null), critérios explicitamente citados (lista vazia quando inexistentes), natureza declarada, etapa limite e efeitos separados sobre criação/submissão/aprovação/publicação. Critérios E05/E07 da agenda vêm do contrato e da política, não de inferência de texto. Natureza deriva apenas de rótulos explícitos: `Pendências humanas`, `Lacuna de fonte/regra`, `Pendências essenciais/de pesquisa`; demais casos são `unspecified`. Itens separados por ponto e vírgula são individualizados; itens de lista Markdown na conclusão somente quando precedidos por rótulo explícito de pendências sem conteúdo. Listas informativas após `nenhuma` são ignoradas. No máximo 50 itens declarados são expostos, seguidos por `details_truncated` quando houver mais. A etapa editorial é antes da aprovação humana; política desatualizada/agenda incompleta devem ser corrigidas antes da submissão pelo agente. `approval=human_attestation_required` descreve apenas a confirmação humana exigida pelo sistema; `resolve_by` orienta a resolução editorial. `allowed` significa que **este aviso** não bloqueia a operação; demais controles continuam aplicáveis.

Título simples e Markdown são aceitos, com LF/CRLF/CR. Pendências explícitas em qualquer parte do documento não são apagadas por uma declaração de ausência na conclusão; o conflito também gera detalhe próprio. Ausência, duplicação e posição inadequada da declaração recebem causas próprias. Texto livre não classificado exige revisão e não recebe critério inventado. Não exigimos frase de ausência quando há pendências reais.

Limite deliberado: o parser não certifica completude factual, não abre fontes, não resolve contradições semânticas arbitrárias, não classifica toda formulação em linguagem natural e não transforma relatos em verificação humana. Uma ficha sem alertas pode continuar insuficiente; `structurally_valid` não é autorização editorial. Introduzir bloqueio automático para toda lacuna de pesquisa exigiria contrato de entrada estruturado/regra nova; não foi feito nesta correção diagnóstica.

## Aceites e evidência

- Ficha com etapas humanas futuras: detalhes E06/E09/E10/E11, criação/submissão permitidas pelo aviso; resolução antes da aprovação humana.
- Lacuna essencial de fonte/regra: motivo/trecho preservados, tipo declarado reconhecido, sem novos gates; falta de referência explícita retorna lista de critérios vazia.
- Sem pendências: títulos do modelo e simples aceitos; nenhuma pendência fabricada por contingência condicional.
- Contradição explícita: `nenhuma` junto com lacuna declarada, inclusive em lista Markdown rotulada como pendência, mantém aviso, trecho e causa de conflito.
- REST e SDK MCP: detalhes serializados sem perda, schema tools/list atualizado, campos anteriores preservados.
- Integração PostgreSQL: validar → criar → submeter confirma efeitos reportados, documento permanece intacto. Regressões de atestação humana, publicação, versão/hash, agenda, auth e privacidade.

Execução concluída nesta branch: **90 testes, 89 aprovados e um skip**, em 119,022 s. Skip do check de grants das roles `gotrendlabs_django`/`gotrendlabs_fastapi`, ausentes no cluster isolado. O teste Streamable MCP real passou tanto com credencial de serviço quanto OAuth, incluindo `validate_market_draft` com detalhes. Os testes iniciais unitários/adapter do patch anterior também passaram; não são somados à execução desta branch.

### Correções após revisão de impacto — 05/11/2026

A revisão da branch encontrou três problemas no primeiro commit: listas informativas na conclusão eram chamadas de pendências; um documento de 58.038 caracteres produzia 29.000 detalhes e 10,73 MB de JSON; `approval=human_resolution_required` descrevia incorretamente o gate técnico, pois a atestação humana pode aprovar documento/política antigos sem atualização textual. A FastAPI agora interpreta bullets apenas após rótulo explícito e vazio de pendências, limita a 50 itens declarados e acrescenta o detalhe `details_truncated` quando ultrapassar o limite. `approval=human_attestation_required` expressa o gate efetivo; `resolve_by` conserva a orientação editorial. O código geral e os demais gates não mudaram.

Aceites adicionais: bullets informativos depois de `nenhuma` não criam aviso; `nenhuma` junto de uma lista marcada `Pendências:` produz contradição; lista `Pendências humanas:` preserva a natureza declarada; documento perto de 60 mil caracteres produz 50 itens e um marcador de truncamento. Sem alteração de permissão, erro, replay, snapshot, persistência ou política. O MCP transporta o mesmo schema compartilhado.

Validação incremental: 14 testes unitários/linha de término aprovados; três testes PostgreSQL direcionados (REST criar/submeter, SDK MCP real serviço/OAuth e aprovação humana de política antiga) aprovados; após ampliar o teste REST para a entrada grande, esse caso foi reexecutado e aprovado. OpenAPI exportado e checado; Ruff F e `git diff --check` aprovados. Os 90 testes anteriores permanecem como regressão do primeiro commit; não foram reexecutados integralmente após esta correção, pois a mudança adicional afeta apenas interpretação textual e o enum de saída cobertos pelos testes direcionados. Banco PostgreSQL temporário em tmpfs, sem mercado real alterado.

Ambiente: Python 3.11 do venv existente `gotrendlabs-mcp/.venv`; PostgreSQL 16 Alpine temporário `gtl-editorial-pending-20261105-tests`, loopback 55443, tmpfs, banco dedicado `editorial_pending`, sem acesso ao banco operacional. Comando com POSTGRES_* apontando apenas para esse container:

```sh
python manage.py test tests.test_editorial_pending tests.test_editorial_admin tests.test_mcp_editorial tests.test_mcp_adapter tests.test_mcp_schedule_errors --noinput
python packages/contracts/export_openapi.py
python packages/contracts/export_openapi.py --check
python -m ruff check --select F apps/api/backend_api/editorial_pending.py apps/api/backend_api/editorial_routes.py apps/api/backend_api/editorial_schemas.py apps/api/backend_api/editorial_service.py tests/test_editorial_pending.py tests/test_mcp_editorial.py
git diff --check
```

Django system check, OpenAPI e Ruff F/diff aprovados. Recursos temporários removidos ao encerrar. Log local em `/tmp/gtl-editorial-pending-20261105-tests.log` (não versionado).

Arquivos alterados:

- `apps/api/backend_api/editorial_pending.py`: diagnóstico determinístico novo.
- `apps/api/backend_api/editorial_service.py`: códigos gerais derivados do diagnóstico.
- `apps/api/backend_api/editorial_routes.py`: detalhes na resposta da validação.
- `apps/api/backend_api/editorial_schemas.py`: schema de saída compartilhado.
- `apps/mcp/server.py`, `apps/mcp/README.md`: orientação da ferramenta e do adaptador.
- `packages/contracts/openapi/gotrendlabs-api.json`: contrato exportado.
- `tests/test_editorial_pending.py`, `tests/test_mcp_editorial.py`: casos unitários/SDK, integração REST e fluxo.
- `docs/specs/features/mcp-editorial-agents.md`, `docs/specs/features/editorial-governance.md`, `docs/specs/contracts/agent-integrations.md`: comportamento e precedência normativa.
- Este relatório e `docs/specs/state/{workflow-runs,feature-changelog,change-log-specs,implementation-status,integration-map}.md`: evidência e retomada.

Deploy não faz parte desta entrega: produção continuará com o aviso antigo até implantação conjunta de API/MCP e atualização do catálogo em clientes com cache.
