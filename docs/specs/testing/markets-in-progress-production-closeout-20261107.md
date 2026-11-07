# Fechamento produtivo — Em andamento

## Origem e integração

- Workflow: WFLOW-20261107-MARKETS-IN-PROGRESS / FEAT-MARKET-001 v0.15.
- PR: [#199](https://github.com/wscardua/gotrendlabs/pull/199), descrição aprovada pelo usuário antes da abertura.
- Commit da implementação: `d9c149f46ec4881b2009b096e43287478381b553`.
- Merge na main: `ca0cab9de589fb4df74b8fac38d0704aa6f73588`.
- CI da PR: [42393869734](https://github.com/wscardua/gotrendlabs/actions/runs/42393869734), sucesso: 681 testes Python, três skips (449,058s); imagens de produção/MCP, OpenAPI e testes JS aprovados.
- Validação local: 139 testes Flutter, analyze sem issues, oito Django isolados, JS/checks e build debug Android 16/API 36 com fixtures locais.
- Branch local `feature/markets-in-progress` e worktree de desenvolvimento preservadas.

## Comportamento entregue

Em andamento mostra open primeiro e locked em seção Em apuração expandida por padrão, com contagem. Resolvidos inclui resolved/sealed; favoritos e previsões pessoais mantêm encerrados. Web mantém visualizações/criação/origem nos abertos e paginação de 18 independente por seção. Mobile preserva ordem API dos abertos, Hoje preserva engajamento; ambos ordenam locked por close_at programado decrescente/origem. Posições ativas segue como acesso secundário Flutter.

Faixa diagonal NOVO é apenas visual para open com created_at <= agora < created_at+48h; cobre Categorias e expira automaticamente sem interação. Os dois findings do review foram corrigidos com testes de inicialização, relógio e descarte do timer.

## Implantação e validação

Actions main [42394768559](https://github.com/wscardua/gotrendlabs/actions/runs/42394768559) concluído com sucesso em 07/11/2026. Suíte Python: 681 testes, três skips, sem falhas (324,999s); imagens, OpenAPI e testes JS aprovados. Deploy SSM `d11f4c17-eb39-41dc-be1c-9a62e20ab6d9`: Success, código zero. Sem migrations a aplicar; collectstatic copiou os dois assets alterados. Serviços em execução e MCP healthy.

Conferência read-only SSM `777756dd-cef5-4c33-9f06-01a428169ccf` confirmou HEAD produtivo `ca0cab9de589fb4df74b8fac38d0704aa6f73588`, sem alterações em arquivos versionados. Backups locais preexistentes foram preservados.

Smoke HTTPS e Chrome autenticado pós-deploy:

- `/api/health`: 200, status ok, API/database ok.
- Home: 200, Em andamento inicial, quatro open na seção principal e cinco locked em apuração expandida; retornar de recortes pessoais restaura expansão.
- JS e CSS `?v=20261107-ribbon-expiry`: 200, SHA256 idêntico ao código integrado.
- Categorias: 200, markup da faixa presente. Nenhum open elegível ao selo no cenário produtivo observado; aparência/expiração cobertas por fixtures DEV e testes de relógio, sem criar dados PRD.
- Resolvidos: seis sealed visíveis com CTA Resultado e histórico verificável; Minhas previsões mantém sealed e demais participações. Favoritos da sessão estava vazio e exibiu mensagem correta; nenhum favorito/previsão foi criado para smoke.
- Mercado selado `quem-avanca-a-final-da-libertadores-masculina-2026-fluminense-ou-palmeiras`: detalhe, modal de integridade, pacote e endpoints API detalhe/integridade/verify retornaram 200. Verify retornou verification_status=verified, market_valid/overall_valid/definition_valid/seal_valid/merkle_root_valid=true, errors=[] e warnings=[].
- GET /markets preserva 15 mercados públicos, incluindo seis sealed/cinco locked/quatro open, sem fixtures qa-visual.

Limites do smoke: não havia resolved nem mais de 18 itens por seção nessa amostra PRD; inclusão de resolved, paginação e selados favoritos têm cobertura comportamental local. Nenhum novo dado de domínio foi criado. Sem necessidade de ajuste produtivo adicional.

## Contratos e MCP

Sem mudança de API/OpenAPI, lifecycle, resolução, selagem, contabilidade, persistência ou autorização. Sem migration/flag/segredo/configuração adicional. Ferramentas, schemas, contratos, permissões, erros, replays e orientação editorial MCP não precisam mudar; nenhuma permissão foi inferida de ações humanas Admin Ops. Fixtures QA permaneceram exclusivamente DEV.

## Distribuição mobile

Código Flutter integrado à main, com build debug em emulador. Deploy web não distribui APK/AAB. Distribuição Android segue WFLOW-20261107-MARKET-DISCOVERY-ANDROID-RELEASE, agora incluindo esta navegação/faixa Novo, a partir da main integrada e limpa, com versão/build integrados antes de gerar release. Nenhuma nova distribuição Play/site ou QA em Android físico foi realizada neste fechamento.
