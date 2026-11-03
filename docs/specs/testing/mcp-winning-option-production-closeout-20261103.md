# MCP get_market — fechamento produtivo em 03/11/2026

## Resultado

FEAT-MCP-001 revisão 1.9 implantada pela [PR #184](https://github.com/wscardua/gotrendlabs/pull/184), merge `9d8933b1d55f673ba9c358e1440ac16341744368`. `get_market` retorna `winning_option_id` obrigatório nullable a partir da persistência, relacionado a `options[].id`. `status` continua independente e presente. Esta evidência substitui as pendências produtivas dos registros locais anteriores, sem promover o status global parcial de outras fatias MCP.

## GitHub, CI e implantação

- Usuário aprovou título/descrição e continuidade do fluxo; PR criada e merge executados via GitHub MCP. Commits e01c9ac e 9b39811; branch/worktree local `fix/mcp-get-market-winning-option` preservados.
- [CI da PR — 41712412435](https://github.com/wscardua/gotrendlabs/actions/runs/41712412435): sucesso, builds principal/MCP, OpenAPI, JS e 637 testes em 500,699s, OK (skipped=2).
- [CI/deploy da main — 41714398208](https://github.com/wscardua/gotrendlabs/actions/runs/41714398208): detect-changes/test/deploy success; 637 testes em 608,609s, OK (skipped=2). Os skips são checks de roles nomeadas ausentes no PostgreSQL de CI; esta entrega não muda grants/ACLs.
- ENABLE_PROD_DEPLOY=1; pipeline padrão GitHub Actions/SSM, sem implantação paralela. SSM `e06772bd-48ec-43a5-a2e6-45ae627a8991`: Success, ResponseCode=0.
- Pré-flight SSM `75b0fa67-a094-4abb-8cf2-268c2dc46708`: serviços running, MCP healthy, API/database ok, 8,4 GiB livres; runtime anterior 0ffa4a0. Baseline SQL READ ONLY: `cfd56bdc-6461-49c3-93b2-4f84786561df`.

## Smoke e leitura autenticada

SSM `364e0cdb-bb87-4bc8-9a26-da2a1d6fffd9`: Success, ResponseCode=0, stderr vazio. Checkout produtivo igual ao merge 9d8933b. Hashes conferidos dentro das imagens API/MCP:

| Arquivo | SHA-256 |
| --- | --- |
| editorial_service.py (API) | c348cd1ff951e605e528247e129f34d1677ae77b96dcfbd805466fcd376058d5 |
| editorial_schemas.py (API e MCP) | 8c1d2ee20c06ac002748333481487c09ad074b7a92cffb44c4e9edc5bc37a72d |
| server.py (MCP) | 0701ae51fe0afddcd27f90f8fefb4bcedf252c02bc1cfc6b617f9d11936d99fa |

Django, FastAPI, daemon, proxy, MCP e thumbnail-worker running; MCP healthy/enabled. Home, /api/health e metadata pública MCP responderam HTTP 200. Catálogo interno: 21 ferramentas/nove scopes; get_market read-only/catalog:read e schema com winning_option_id obrigatório anyOf integer/null.

Chamadas reais pela conexão MCP já autorizada, sem expor token/ficha em logs:

```json
{"id":35,"status":"sealed","winning_option_id":82}
```

O ID 82 corresponde a Palmeiras em options e ao valor persistido lido com role da API em transação READ ONLY. Antes do deploy, a mesma consulta MCP omitia o campo.

```json
{"id":36,"status":"locked","winning_option_id":null}
```

O campo está presente com null no payload estruturado efetivo, coerente com a ausência de vencedora no banco. Não foi necessário renovar grant/token para essas leituras.

## Integridade, ativação e limites

Hashes do mercado 35 iguais antes/depois: ficha `c97f719dcb68f1d8e6dc3c20c0f43bcf0ed4f5c4fdcb0ea96b5a4949baa975b8`; selo `b822192986f52f100890aff846a0acb8756a5c9500e2a342dd129cb222e33c16`. Resultado e status preservados. O updated_at avançou de 12:46:29 para 20:27:44 UTC durante a janela anterior ao deploy das 20:51 UTC; não é usado para afirmar imutabilidade integral dos metadados nem atribuído ao código novo. Esta execução enviou somente consultas de mercado; não resolveu/cancelou/excluiu mercados produtivos.

Nenhuma migration, flag, variável, scope, grant, consentimento novo ou ajuste manual de dados foi necessário: deploy coordenado tornou a funcionalidade ativa. Permissões, erros de negócio, replays e política/ficha editorial permanecem. Mobile não impactado: usa /markets/{slug}, não a projeção editorial alterada. Testes locais incluem SDK serviço/OAuth e lifecycle real; smoke produtivo é de leitura. Cache de metadados de clientes externos pode exigir atualizar catálogo, mas a conexão MCP usada já retornou o campo novo. Não houve ensaio de carga nem injeção de falhas produtivas.

Specs, contratos, OpenAPI, README, aceites, changelogs e memória operacional reconciliados com este recibo. A publicação documental posterior deve executar CI docs-only, sem redeploy de runtime. [Roteiro](../operations/mcp-winning-option-rollout.md), [review](mcp-winning-option-review.md), [validação local](mcp-winning-option-results.md).
