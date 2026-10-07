# Rollout produtivo MCP editorial — 2026-10-07

Workflow `WFLOW-20261007-MCP-CLOSEOUT-001`. Usuário aprovou a descrição e autorizou o fluxo GitHub/produção. Entrega técnica integrada, implantada e habilitada; homologação Dot e piloto autenticado continuam pendentes.

## GitHub, backup e deploy

- Commit de implementação `de9e797ef25e3a31a8d552a942470bad4a7f0d2f`; [PR #136](https://github.com/wscardua/gotrendlabs/pull/136), merge `b36ea44b215c423497e6eae1706f84e87349ac73`. Branch/worktree local `feature/mcp-editorial` preservados; checkout original/analytics/mobile não alterados.
- [CI da PR](https://github.com/wscardua/gotrendlabs/actions/runs/37691056081): 369 testes/265,287 s/OK em Python 3.12/PostgreSQL 16; OpenAPI aprovado. Deploy corretamente não executado no evento PR.
- Snapshot RDS `gotrendlabs-pre-mcp-20261007` criado e aguardado até `available`/100% **antes do merge**. Backup mantido; nenhum restore/descarte executado.
- [CI e deploy da main](https://github.com/wscardua/gotrendlabs/actions/runs/37692274600): 369 testes/311,575 s/OK; jobs detect-changes/test/deploy com sucesso. Build, preflights, janela sem writers durante migrations/grants, collectstatic, startup com saúde, validação/reload Caddy realizados pelo deploy padrão. SSM `3ef9b804-e94a-4166-bea2-60578970718f`: Success.
- Ativação explícita com configure_environment `--enabled 1` e recriação API/MCP; SSM `662a9726-a0e0-43db-b844-4c7af8cfceaf`: Success. Sem integração/credencial/mercado criado pelo bootstrap ou pela ativação.

## Migrations e isolamento efetivo

- Conferidas no PostgreSQL: editorial_integrations.0001_initial, .0002_runtime_grants_and_audit, .0003_universal_editorial e markets.0032_adminevent_execution_id_adminevent_integration_and_more.
- Onze tabelas novas: FastAPI com SELECT/INSERT; UPDATE/DELETE recusados em revisões, permitidos nas tabelas mutáveis; Django sem SELECT/INSERT/UPDATE/DELETE editorial. Revisões append-only e autoridade FastAPI preservadas.
- Container MCP: usuário mcp, filesystem somente leitura, cap_drop ALL, memória 268435456 bytes, CPU 0,5, sem host port bindings. Django/psycopg ausentes; nenhuma variável DB/AWS/TOTP/pepper/KMS. Saúde retorna status=ok/enabled=true.
- Arquivos .env.mcp.prod/.env.mcp-api.prod em modo 0600; workload preservado sem divulgação. API/adapter configurados com resource canônico https://gotrendlabs.com.br/mcp. Segredos permanecem fora de Git, relatório e prompts.
- Após rollout: MCP 35,87 MiB/256 MiB; memória disponível no host 298 MiB, swap livre 695 MiB. É observação pontual, não comprovação de carga sustentada.

## Smoke externo HTTPS (certificado verificado)

| Requisição | Resultado |
| --- | --- |
| GET /api/health | 200 |
| GET /.well-known/oauth-protected-resource/mcp | 200, resource/authorization server canônicos |
| GET /.well-known/oauth-authorization-server | 200, issuer/token endpoint corretos, PKCE S256, authorization_code/refresh_token/client_credentials anunciados |
| POST /mcp initialize sem credencial | 401, WWW-Authenticate aponta metadata canônica |
| POST /internal/agent-integrations/delegate e /api/internal/agent-integrations/delegate | 404 no proxy |
| GET /api/integrations/editorial/policy sem delegação | 401 |
| POST /oauth/token com credencial fictícia inválida | 401 |
| GET Admin Ops integrações/revisão/mercados sem sessão | 302 para login |
| GET assets CSS/JS | 200 |

O primeiro smoke usou metadata sem sufixo /mcp e recebeu 404. A URL anunciada pelo SDK/WWW-Authenticate e pelo runbook é /.well-known/oauth-protected-resource/mcp e respondeu 200. Teste corrigido para conferir esse endpoint canônico; nenhum relaxamento de autenticação/proxy necessário. URI de authorization server normalizada para comparação de trailing slash.

UI autenticada positiva e dez tools/OAuth/serviço foram conferidos em DEV/cliente SDK real e na CI. Os redirects produtivos não são uma validação da UI autenticada, nem as chamadas negativas comprovam um grant produtivo válido.

## Preservação de dados

Inventários somente leitura antes/depois via role API (SSM 12025bd2-a10a-420b-8d6e-fd0325bead70 e 6a0994b7-809e-44be-9800-bfda6091c8a5): mercados, opções, previsões, definições e selos permanecem com zero registros e SHA-256 idêntico de lista vazia. Dados não foram exportados; somente contagens/hashes sanitizados. Não foram criados mercados reais em produção. Contas/configuração e backups operacionais existentes preservados.

## Resultado de aceite e próxima ação

- MCP-O01: infraestrutura/deploy/HTTPS/discovery/grants/isolamento produtivos conferidos. Rollback de acesso documentado e testado localmente; não houve rollback/restore produtivo desnecessário.
- MCP-O02: regressão CI aprovada e smoke público pós-deploy aprovado. UI positiva/fluxos de domínio têm evidências DEV; piloto autenticado produtivo continua etapa operacional.
- MCP-X01 e demais critérios: evidências locais/CI na [matriz](mcp-editorial-results.md), [ensaio DEV](dev-catalog-rehearsal-20261007.md) e [fechamento local](mcp-closeout-20261007.md).
- MCP-X02: Dot real **não homologado**. Consentimento, chamadas de escrita, recorrência/renovação/revogação e logs na conta externa só podem ser declarados após execução real. Credencial de serviço não substitui OAuth.

FEAT-MCP-001 permanece parcial por homologação externa/piloto autenticado; entrega técnica/rollout concluídos. Iniciar pelo [runbook](../../guides/mcp-editorial-pilot.md): operador staff/superuser com MFA cria/ativa integração pequena, escolhe responsável/scopes/cotas, conecta OAuth em https://gotrendlabs.com.br/mcp; serviço recebe credencial própria emitida uma vez pela FastAPI/Admin Ops. Não reutilizar credenciais DEV ou staff no adaptador. Registrar cliente/conta/data/resultados sanitizados do piloto.
