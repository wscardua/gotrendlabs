# Recibo produtivo — descoberta de mercados abertos

07/11/2026. WFLOW-20261106-MARKET-DISCOVERY-OPEN-FIRST / FEAT-MARKET-001. Verificação somente de leitura; nenhum mercado, previsão, favorito ou permissão foi alterado em produção.

## Integração e distribuição web

- [PR #196](https://github.com/wscardua/gotrendlabs/pull/196), merge `8e920ca859660e3e0817b5a4b8f2102108b9f7d4`: filtros web/mobile, histórico pessoal, specs e testes. [Actions da PR](https://github.com/wscardua/gotrendlabs/actions/runs/42379533337) e [main](https://github.com/wscardua/gotrendlabs/actions/runs/42380529876) passaram; a main executou deploy SSM com sucesso.
- O primeiro smoke HTTP encontrou quatro `open`, cinco `locked` e seis `sealed` entre 15 mercados públicos. A home inicial mostrava só abertos, e `Em apuração` mostrou os cinco `locked`. Em um Chrome com cache anterior, `Resolvidos` ficou vazio; recarga forçada mostrou os seis selados. A causa era o URL de JS/CSS sem nova versão no template base.
- [PR #197](https://github.com/wscardua/gotrendlabs/pull/197), merge `6157d88ace92b6e300acd837b729505d08e938c4`: atualizou os URLs versionados dos assets e reconciliou a memória operacional. [Actions da PR](https://github.com/wscardua/gotrendlabs/actions/runs/42381773272) e [main](https://github.com/wscardua/gotrendlabs/actions/runs/42382587977) passaram: 681 testes Python, três skips, teste funcional JS, OpenAPI e builds de produção/MCP em cada execução. Deploy SSM `521fb95e-e2af-4975-aea5-27a8f46d40e3` terminou em `Success`.

## Smoke após a correção

- `GET /`, `/api/health` e `/api/markets`: HTTP 200. A home referencia `gotrendlabs.js` e `gotrendlabs.css` com `?v=20261107-market-discovery`.
- Em Chrome que já havia carregado a versão anterior, uma **recarga comum** mostrou apenas mercados abertos em `Em alta`. Ao tocar `Resolvidos`, apareceram seis mercados `sealed`, com rótulo de histórico finalizado e CTA `Resultado`.
- Depois de `Resolvidos`, `Minhas previsões` mostrou novamente mercados de diferentes estados, inclusive selados e em apuração; o filtro anterior não ficou implícito. Um detalhe de mercado selado e sua página `/integrity/` responderam HTTP 200.
- A suíte da PR/main confirmou paginação após filtro/ordem, desempates, vazios, favoritos, Today mobile e acesso a histórico e provas. O smoke produtivo não alterou favoritos nem realizou previsões.

## Contratos, MCP e limite de distribuição

`GET /markets` continua entregando todos os estados públicos e flags pessoais; o status efetivo segue vindo do domínio. Não houve mudança em lifecycle, resolução, selagem, contabilidade, autorização ou persistência. Ferramentas, schemas, contratos, permissões, erros, replays e orientação editorial MCP permanecem iguais; a PR #197 mudou apenas a URL dos assets web e documentação. Nenhuma permissão MCP foi inferida do Admin Ops.

O código Flutter foi integrado pela PR #196, mas o app instalado não recebeu este ajuste pelo deploy web: Google Play Closed testing Alpha ainda está em `1.2.3+17`, e o APK direto do site em `1.0.7`. A publicação Android e o QA em dispositivo seguem em `WFLOW-20261107-MARKET-DISCOVERY-ANDROID-RELEASE`. A fatia web está ativa e validada; FEAT-MARKET-001 ampla permanece parcial por lacunas independentes já registradas.
