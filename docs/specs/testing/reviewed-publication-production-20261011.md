# Recibo produtivo — identidade da publicação aprovada

- Data: 2026-10-11. Workflow: WFLOW-20261011-PUBLISH-FORM-IDENTITY.
- PR: https://github.com/wscardua/gotrendlabs/pull/158.
- Merge implantado: d80b1006a94ddbef09b55b852e625721beed5268.
- CI PR: https://github.com/wscardua/gotrendlabs/actions/runs/38169538314 — success, 496 testes/2 skips, 483.144 s na suíte.
- CI main/deploy: https://github.com/wscardua/gotrendlabs/actions/runs/38170273991 — success, 496 testes/2 skips, 650.346 s na suíte; build e OpenAPI aprovados.
- SSM deploy: 4d41d9a1-129a-45e0-813a-59f500101c36 — Success, serviços ativos, sem migrations a aplicar.
- SSM smoke: 03f9e381-169a-49e1-b4de-afdc2a1350ca — Success. SHA conferido no servidor; renderização do partial real no container Django com RequestFactory/contexto de teste confirma ID atual e ID original após erro. Leitura do banco confirma mercado 50 em draft e exclusão anterior no mesmo slug. Não houve mutação no mercado.
- GET /api/health: status ok, API e banco ok. GET /: 302 para /maintenance/, que responde 200; runtime informa manutenção web ativa. Não alteramos essa configuração.
- Nenhuma nova configuração, migration, ferramenta/permissão MCP ou mudança mobile. Branch local preservada.

## Limites da verificação

O smoke validou o template implantado e a leitura do mercado, sem sessão administrativa real e sem executar publicação. A rejeição backend de IDs antigos/ausentes foi validada nos testes. Não se afirma que houve publicação real do mercado ou teste ponta a ponta único em produção. O operador pode recarregar o editor e usar o fluxo normal de publicação com seu parecer vigente.

## Confirmação do operador

Em 2026-10-11, após o deploy, o usuário confirmou: “confirmado e funcionando”. Essa confirmação complementa a verificação técnica acima e encerra a homologação funcional desta correção; não implica publicação realizada pelo agente.
