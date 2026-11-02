# MCP lifecycle — fechamento produtivo em 02/11/2026

## Resultado

Implantação técnica concluída pela [PR #182](https://github.com/wscardua/gotrendlabs/pull/182), merge `0ffa4a0f759447e7ddc1dd8e391903bf5d6b8f2f`. Código do lifecycle/exclusão MCP e recuperação de sessão do consentimento estão ativos. Esta conclusão substitui as pendências de implantação nos registros locais anteriores; homologação humana de clientes externos e concessão de novos scopes são etapas distintas.

## GitHub e CI

- Branch feature/mcp-resolve-cancel-markets preservada localmente. Commits de implementação c778b88 e preparação efc8b1d integrados pelo merge.
- [CI da PR: 41462209156](https://github.com/wscardua/gotrendlabs/actions/runs/41462209156): sucesso; build principal/MCP, OpenAPI, JS e 637 testes em 551,246s, OK (skipped=2).
- [CI/deploy da main: 41464155882](https://github.com/wscardua/gotrendlabs/actions/runs/41464155882): detect-changes, test e deploy success; 637 testes em 683,282s, OK (skipped=2). Os dois skips são checks de roles nomeadas ausentes no PostgreSQL temporário; grants reais foram verificados no smoke produtivo abaixo.
- ENABLE_PROD_DEPLOY=1; deploy padrão GitHub Actions/SSM, sem procedimento paralelo. SSM `e6402bf9-1fdb-4a6a-b8c3-da5eb8b202a2`: Success, ResponseCode=0.
- Pré-flight SSM `3c7bc498-ec28-4eda-be81-e0c5299e8215`: host online, serviços running e 8,2 GiB livres. SHA antes do deploy era 33bbd40; a main documental b6a0649 não havia exigido novo runtime.

## Smoke produtivo

SSM `7dce1c8c-aded-41d8-83b3-5d2e5db914c1`: Success, ResponseCode=0, stderr vazio.

- SHA do checkout implantado igual ao merge 0ffa4a0. Hashes dos arquivos relevantes conferidos entre checkout e containers: serviço de ações/schema FastAPI, view Django, adaptador/schema MCP.
- Django, FastAPI, daemon, proxy, MCP e thumbnail-worker running; MCP healthy e enabled=true.
- HTTP público 200 para home, /api/health, discovery OAuth e metadata MCP. Admin Ops anônimo redireciona ao login (302).
- Runtime MCP lista 21 ferramentas, incluindo as três novas com annotations destrutivas/idempotentes; metadata anuncia nove scopes e resource https://gotrendlabs.com.br/mcp.
- FastAPI contém as três rotas novas. POSTs sem delegação/workload, com payloads válidos e IDs inexistentes, receberam 401 unauthenticated nas rotas resolve, cancel e delete.
- Nenhuma resolução/cancelamento/exclusão privilegiada foi executada em mercados produtivos para smoke. Testes de efeitos de domínio, rollback e concorrência foram feitos somente em PostgreSQL isolado.

## Migration e ACLs efetivas

editorial_integrations.0007 aplicada; constraints agent_market_request_unique/agent_market_request_operation presentes; trigger agent_market_requests_append_only enabled.

| Recurso | FastAPI | Django |
| --- | --- | --- |
| gotrendlabs_agent_market_requests | SELECT/INSERT, sem UPDATE/DELETE | SELECT, sem INSERT/UPDATE/DELETE |
| Sequência do recibo | USAGE/SELECT, sem UPDATE | Sem USAGE/SELECT/UPDATE |
| Função delete_prepublication_editorial | EXECUTE permitido | EXECUTE negado |
| Revisões editoriais | Sem DELETE geral | Sem nova ampliação |

As consultas SQL do smoke usaram transação READ ONLY e a role efetiva da API. Não foi necessário ajuste manual adicional: migration/deploy produziram o estado esperado. Recibos, provas, ledger e mercados existentes foram preservados.

## Ativação e limites

O código está habilitado e saudável; nenhuma nova flag, variável ou segredo foi necessário. Uma integração produtiva ativa conserva os seis scopes anteriores (editorial:read, catalog:read, metrics:read, analytics:read, drafts:write, drafts:submit). O deploy não concedeu markets:resolve, markets:cancel ou drafts:delete e não emitiu grant privilegiado. Para usar essas tools, operador staff/superuser com MFA deve conceder os scopes desejados e concluir novo consentimento OAuth/token de serviço. [Guia](../../guides/mcp-market-lifecycle.md).

MCP não publica, fecha manualmente ou desfaz resolução; cancelar resolved/sealed e excluir publicados/previsões/provas continuam bloqueados. A recuperação da sessão inválida está implantada, mas o fluxo humano LM Studio/Dot em produção depende do cliente/conta concretos; o SDK real serviço/OAuth e os testes web foram validados no ambiente isolado. Carga/latência e falhas de KMS real não foram injetadas em produção. Mobile não impactado: não consome os endpoints de integração/OAuth alterados, sem necessidade de release.

Specs, contratos, OpenAPI, ADRs, aceites, rollout e memória operacional acompanham este recibo. A atualização documental posterior registra a evidência real e deve seguir CI docs-only, sem nova implantação de runtime. [Rollout](../operations/mcp-market-lifecycle-rollout.md), [review](mcp-market-lifecycle-review.md), [validação local](mcp-market-lifecycle-results.md).
