# Review de impacto — MCP lifecycle

## Resumo

- Base: origin/main b6a06498ffca1b62901142014b4489efe2f8ead4, também merge-base.
- Intervalo versionado: b6a0649..c778b88, 37 arquivos, 2531 inserções/21 remoções. Os arquivos novos de domínio, migration e testes integram o commit; a revisão anterior sem commits não cobria a implementação.
- Escopo: apps/api/backend_api/{editorial_market_actions,editorial_routes,editorial_schemas,editorial_service,market_deletion}.py; apps/mcp/{server.py,README.md}; apps/web/django/admin_ops/integration_views.py; editorial_integrations/models.py e migration 0007; OpenAPI; testes test_mcp_market_actions/test_mcp_editorial/test_mcp_consent_query; README, specs, contratos, ADRs, aceites, rollout, evidências e estado listados no diff do commit.
- Superfícies: API/MCP, persistência/ACL, Admin Ops/consentimento, auditoria/eventos e documentação. Docker/configuração/scheduler/Flutter não têm mudanças de runtime nesta branch.
- Mobile não impactado: triagem apps/mobile/lib não encontrou consumidores de /integrations/editorial ou /oauth; API pública/auth/headers do app permanecem no contrato anterior. A recuperação de sessão alterada pertence à view Django do consentimento.
- Testes: suíte completa 637, 635 aprovados e dois skips de roles nomeadas ausentes no cluster temporário. Inclui domínio, concorrência/replay/rollback, exclusão humana, OAuth/serviço SDK real e ACL nova com roles temporárias. JS, Django, OpenAPI, migrations, Ruff F e diff check aprovados. [Evidências](mcp-market-lifecycle-results.md).
- Risco geral: médio, pelas novas operações de domínio delegadas e migration; verificações de produção são exigidas antes de promover o fechamento.

## Findings

Nenhum problema identificável no diff.

Revisados grants explícitos e ausência de ampliação automática, autorização corrente inclusive em replay, integração/responsável técnicos, callbacks sem impersonação, IDs/versionamento/locks, concorrência com humanos e outras integrações, recibos/ledger/auditoria atômicos, preservação do undo humano, exclusão própria limitada por estados/previsões/provas, hashes editoriais preservados, tratamento de timeout, códigos expostos, enum de eventos técnicos, schemas REST/MCP/OpenAPI e next OAuth seguro em sessão revogada.

## Pontos a validar

- CI remoto: build principal e MCP em Python 3.12 e suíte no SHA final; ambiente local usa Python 3.11. Evidência será o Actions da PR/main.
- Após merge: migration 0007, constraints/trigger e ACLs das roles efetivas no ambiente produtivo, particularmente retirada de grants amplos herdados. O teste local da migration passa e os checks das funções existentes foram conferidos por leitura no DEV; isso não comprova o estado produtivo futuro.
- Serviços/SHA/discovery/catálogo de 21 tools e negação de mutações sem delegação no deploy real, conforme runbook. Não testar efeitos reais sobre mercados produtivos por inferência.

## Riscos residuais e cobertura

- Latência/carga com KMS produtivo e perda de resposta real não foram injetadas em produção; assinatura indisponível e timeout foram testados por falhas controladas no ambiente isolado.
- Fluxo humano LM Studio/Dot após novo consentimento precisa de validação no cliente/conta concretos. SDK real por serviço/OAuth e redirect HTTP local cobrem servidor, não toda combinação de modelo/browser.
- Dois testes de roles nomeadas foram ignorados no cluster temporário por ausência delas. Teste da migration nova com roles próprias passou; ACL produtiva continua um gate do smoke.
- Habilitar capacidades de integração exige concessão explícita dos scopes desejados e novo consentimento/token; deploy não concede esses privilégios.


## Verificação dos gates produtivos — 02/11/2026

Build principal/MCP, suíte Python 3.12 no Actions e deploy aprovados pela PR #182. Migration/ACLs efetivas, hashes, saúde, catálogo e negação de chamadas anônimas conferidos por smoke read-only. [Recibo](mcp-market-lifecycle-production-closeout-20261102.md). Os riscos residuais de carga/KMS e cliente humano não são promovidos por esse smoke.
