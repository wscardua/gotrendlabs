# GoTrendLabs editorial MCP v1

Na revisão editorial 1.5, `create_market_draft` e `update_market_draft` recebem
`editorial_record` com `policy_version`, `policy_hash` e `document`. O documento
único reúne pesquisa, regras, fontes com data de consulta, contingências e
pendências; o agente não envia aprovação nem confirmação humana. O formato
estruturado E01–E11 anterior não é aceito pelo contrato atual.

Runtime separado, SDK oficial `mcp==1.30.0`, Streamable HTTP stateless em `/mcp`, protocolo testado `2025-11-25`. Nenhum banco/ORM no adaptador. Não execute `django.setup()` neste processo.

Instalação Python 3.11/3.12: `python -m pip install -r apps/mcp/requirements.txt`.
Com ambiente próprio configurado: `python -m uvicorn apps.mcp.server:app --host 127.0.0.1 --port 8002 --no-access-log`.

Ver [runbook](../../docs/guides/mcp-editorial-pilot.md), [prompt de radar](../../docs/guides/dot-editorial-radar.md) e [evidências de aceite](../../docs/specs/testing/mcp-editorial-results.md).

O adapter troca token destinado ao MCP por delegação API de até 40 segundos. FastAPI exige também workload e revalida origem, audiência, issuer, scopes, responsável e consentidor. Workload isolado não autoriza leituras/editorial ou mutações. Tokens e segredos não vão para spool. Cada chamada tem execução UUID e logs API autoritativos; erros MCP são `isError`, inclusive sobre HTTP 200.

Spool: arquivos privados JSON somente com IDs, ferramenta e resultado, máximo 128 arquivos/512 KiB, TTL 24h. Reenvio na próxima chamada autenticada da mesma integração, deduplicado na API pelo event ID. Não há promessa de captura perfeita: saturação produz `mcp_log_spool_capacity_exhausted`; integração revogada não pode reenviar, e entrada expira. Sem pesquisa/agenda/LLM/controle Dot no processo.

Deploy produtivo usa override MCP com rede/env exclusivos; configurador gera arquivos 0600 desligados na primeira instalação e preserva workload em redeploy. Ver [preparação e limites](../../docs/specs/testing/mcp-closeout-20261007.md); HTTPS produtivo/Dot somente após evidência real.
