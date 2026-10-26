# Wallet web simplificada — fechamento produtivo (26/10/2026)

- [PR #180](https://github.com/wscardua/gotrendlabs/pull/180), merge `33bbd40c53d0ce11f1c2b0acfeee56ed71cdd7ba`: removido de `/wallet/` o painel `Retornos por acerto`; saldos, recarga e extrato permanecem. API `/users/me/ledger`, cálculos, banco e app Flutter não mudaram.
- [CI da PR](https://github.com/wscardua/gotrendlabs/actions/runs/40316330605) e [CI/build/deploy de main](https://github.com/wscardua/gotrendlabs/actions/runs/40317433044) aprovados, incluindo o teste de regressão com PostgreSQL.
- SSM de leitura `2fa64a13-b7ec-48d5-b946-37d3b98622a1` confirmou HEAD `33bbd40` na instância. O Django produtivo renderizou com dados de teste em memória: saldo, lançamento e extrato presentes; título e métricas do painel removido ausentes. Nenhum dado de usuário ou lançamento produtivo foi alterado para o smoke.
- HTTPS público: `/api/health` respondeu 200; `/wallet/` sem sessão respondeu 302 para login. O fluxo autenticado com conta humana em navegador produtivo não foi ensaiado nesta operação.
- Impacto MCP revisado: sem mudança de ferramenta, schema, contrato, scope, permissão, erro, replay ou orientação editorial. A alteração fica na apresentação Django; o contrato usado pelo Flutter continua obrigatório.

O teste PostgreSQL isolado local não iniciou por falta de espaço no armazenamento Docker; o contêiner temporário foi removido. A suíte completa no GitHub Actions passou antes e depois do merge. Fonte de estado: WFLOW-20261026-WALLET-WEB-SIMPLIFY.
