# Diagnóstico ChatGPT e resposta DCR — 2026-10-07

WFLOW-20261007-MCP-CHATGPT-DCR-001; FEAT-MCP-001 permanece parcial.

## Evidência externa somente leitura

- Formulário real ChatGPT: URL HTTPS /mcp, OAuth, Dynamic Client Registration, endpoints descobertos corretos e cinco scopes. OIDC não anunciado/desabilitado. Erro genérico de app settings não identifica o campo rejeitado.
- Discovery produtivo respondeu 200. Logs FastAPI na janela de investigação mostram POST /oauth/register 201, sem rejeição 422 do registro; isso não comprova aceitação do cadastro pelo ChatGPT.
- Tentativa anterior de consentimento usava ID de credencial de serviço como client_id OAuth: consulta produtiva somente leitura encontrou integração ativa/revisão 2, cliente OAuth inexistente e validação invalid_client. Não criar cliente fictício para esse ID nem aceitar credencial de serviço no fluxo interativo.
- Nenhum segredo, código, challenge, state ou token real incluído neste relatório; nenhuma configuração produtiva, integração, grant ou mercado alterado pela investigação.

## Correção local

O registro devolvia `scope: null` quando scope era omitido. Segundo RFC 7591, scope é metadado string opcional. Serialização `exclude_none=True` omite o campo ausente e conserva o informado. Não muda validação, persistência, permissões, MFA, audience, PKCE ou redirect. Não adiciona scopes default ao consentimento.

Teste novo cobre resposta sem valores nulos/sem client_secret, scope explícito preservado e consent-info com callback HTTPS ChatGPT e ui_locales. Suíte existente cobre OAuth completo/refresh/reuse, serviço, SDK MCP real e segurança.

OpenAPI não muda: resposta de registro não possui schema específico no snapshot atual; verificador aprovou snapshot existente. Ruff e diff aprovados.

## Pendências

Suite PostgreSQL isolada: **51 testes/156,480 s/OK**, com destruição do banco de teste pelo runner. Comando: `.venv/bin/python ops/scripts/test_mcp_local.py --db-admin-env /Users/williamsca/Documents/gotrendlabs/.env.db-admin.local --database gtl_mcp_chatgpt_dcr tests.test_mcp_editorial tests.test_mcp_adapter`. DEV preservado.

Correção ainda não implantada. Após aprovação da descrição: commit/PR/CI/merge/deploy e repetir cadastro ChatGPT, consentimento humano e leitura editorial. `scope: null` é defeito confirmado do contrato, mas sua causalidade exclusiva para o erro ChatGPT ainda não foi demonstrada. Se persistir, obter evidência específica de validação do cadastro sem coletar segredos.
