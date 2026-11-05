# GoTrendLabs editorial MCP v1

Na revisão editorial 1.5, `create_market_draft` e `update_market_draft` recebem
`editorial_record` com `policy_version`, `policy_hash` e `document`. O documento
único reúne pesquisa, regras, fontes com data de consulta, contingências e
pendências; o agente não envia aprovação nem confirmação humana. O formato
estruturado E01–E11 anterior não é aceito pelo contrato atual.
Se houver anúncio conhecido, o documento deve trazer `Anúncio esperado:` com data/hora e offset posteriores ao fechamento. `validate_market_draft` preserva `unresolved_editorial_gaps` em `pending` e explica causas, trechos, critérios explícitos, etapa e impacto em `pending_details`. Alertas orientam a preparação; o revisor humano confirma a resolução das pendências antes de aprovar, sem frase obrigatória no parecer. O aviso não impede o agente de submeter o draft para revisão.

Runtime separado, SDK oficial `mcp==1.30.0`, Streamable HTTP stateless em `/mcp`, protocolo testado `2025-11-25`. Nenhum banco/ORM no adaptador. Não execute `django.setup()` neste processo.

Instalação Python 3.11/3.12: `python -m pip install -r apps/mcp/requirements.txt`.
Com ambiente próprio configurado: `python -m uvicorn apps.mcp.server:app --host 127.0.0.1 --port 8002 --no-access-log`.

Ver [runbook](../../docs/guides/mcp-editorial-pilot.md), [prompt de radar](../../docs/guides/dot-editorial-radar.md) e [evidências de aceite](../../docs/specs/testing/mcp-editorial-results.md).

O adapter troca token destinado ao MCP por delegação API de até 40 segundos. FastAPI exige também workload e revalida origem, audiência, issuer, scopes, responsável e consentidor. Workload isolado não autoriza leituras/editorial ou mutações. Tokens e segredos não vão para spool. Cada chamada tem execução UUID e logs API autoritativos; erros MCP são `isError`, inclusive sobre HTTP 200.

Spool: arquivos privados JSON somente com IDs, ferramenta e resultado, máximo 128 arquivos/512 KiB, TTL 24h. Reenvio na próxima chamada autenticada da mesma integração, deduplicado na API pelo event ID. Não há promessa de captura perfeita: saturação produz `mcp_log_spool_capacity_exhausted`; integração revogada não pode reenviar, e entrada expira. Sem pesquisa/agenda/LLM/controle Dot no processo.

Deploy produtivo usa override MCP com rede/env exclusivos; configurador gera arquivos 0600 desligados na primeira instalação e preserva workload em redeploy. Ver [preparação e limites](../../docs/specs/testing/mcp-closeout-20261007.md); HTTPS produtivo/Dot somente após evidência real.


## Resolução e cancelamento delegados

Catálogo: 21 ferramentas, filtradas por scope. `resolve_market(resolution)` exige markets:resolve e mercado locked. `cancel_market(cancellation)` exige markets:cancel, aceita draft próprio ou scheduled/open/locked e nunca desfaz resolução. Leia get_market para obter options[].id e updated_at; envie market_id, expected_updated_at, note e idempotency_key UUID. Resolução também exige winning_option_id, source_url HTTP(S), resolved_at com offset e resolution_timezone IANA; cancelamento exige expected_status. Fonte é relato do executor, sem atestado humano fictício.

`get_market` retorna `winning_option_id` obrigatório (`integer | null`): ID persistido da vencedora, correspondente a `options[].id`, ou `null` sem vencedora registrada. O resultado permanece em resolved/sealed; não inferir pelo texto editorial ou ordem das opções. Mesmo scope `catalog:read` e mesmas regras de visibilidade; o campo operacional não altera snapshots editoriais.

Concessão: staff/MFA edita Integrações e agentes, marca individualmente os scopes desejados e salva; reconectar OAuth com consentimento desses scopes. Serviço deve obter novo access token. Grants/tokens anteriores não herdam privilégios. Publicação, fechamento manual e undo não são expostos.

Timeout retorna operation_indeterminate; mantenha exatamente payload/chave e repita o pedido para confirmar sem duplicar efeitos. Novo payload com a mesma chave conflita. Resolução desfeita/substituída retorna resolution_request_superseded. [Contrato](../../docs/specs/contracts/agent-integrations.md), [runbook](../../docs/guides/mcp-market-lifecycle.md).


`delete_market_draft(deletion)` exige drafts:delete explícito e exclui permanentemente apenas draft próprio preparation/in_review, sem publicação, previsões ou provas. Entrada: market_id, expected_revision, expected_updated_at, note e idempotency_key UUID. Reutiliza remoção humana/auditoria; replay confirma exclusão sem recriar recurso. Timeout mantém resultado indeterminado: repetir mesma chave/payload. Sem nova migration ou concessão automática.
