# Workflow Checklists

Use este arquivo como checklist rápido antes de encerrar processos.

## Checklist universal

- existe execução em `workflow-runs.md`
- feature ou contrato alvo foi identificado
- docs afetados foram listados
- revisão de arquitetura e segurança foi feita ou justificada como não aplicável
- testes esperados foram revisados
- testes executáveis foram implementados, executados ou registrados como pendência quando havia código
- `feature-changelog.md` foi atualizado quando a mudança tocou feature
- `implementation-status.md` foi atualizado quando houve impacto em código
- `integration-map.md` foi atualizado quando dependências mudaram
- ADR foi criado quando fronteira, contrato estável ou regra estrutural mudou
- pendências foram registradas em `known-gaps.md` ou no workflow

## Publicação e deploy

- implementações/correções da entrega estão commitadas e integradas à main; distinguir validação local de integração/distribuição
- comparar funcionalidades e origem da versão distribuída anterior com a nova base; inspecionar recibos e worktrees pendentes para não perder alterações locais já empacotadas
- divergência funcional ou alteração distribuída sem reconciliação bloqueia a próxima distribuição; registrar pendência sem apagar histórico
- artefato distribuível parte de checkout limpo do commit atual de origin/main após fetch; mudança de versão/build também precisa estar integrada antes do build
- recibo registra commit completo, versão/build, canal, checksum e regressões verificadas; conferir o artefato selecionado no upload contra o recibo
- Android: gate validateReleaseSource obrigatório em preReleaseBuild/assembleRelease/bundleRelease/packageRelease; falha de fetch, HEAD divergente e alterações locais bloqueiam release; debug permanece permitido

- mudanças docs-only continuam usando branch, PR e merge em `main`, mas devem rodar apenas validação leve no `GoTrendLabs CI and Deploy` e não devem acionar deploy PRD
- docs-only é restrito a `docs/**` e arquivos Markdown na raiz, como `README.md` e `notes.md`
- mudanças em `.github/**`, `ops/**`, `apps/**`, `packages/**`, migrations, fixtures, contratos, configs, exemplos de env e workflows nunca contam como docs-only, mesmo quando forem texto
- mudanças produtivas seguem CI completo, deploy PRD quando `ENABLE_PROD_DEPLOY=1` e smoke pós-merge
- `workflow_dispatch` permanece caminho manual produtivo e não é bloqueado pela detecção docs-only

## Nova feature

- frontmatter completo
- escopo incluído e excluído claros
- contratos afetados declarados
- camadas impactadas declaradas
- testes esperados e critérios de aceite definidos
- desenho de solução e riscos avaliados por `gotrendlabs-software-architect`

## Alterar feature

- mudança vinculada a objetivo claro
- contratos afetados revisados
- dependências diretas revisadas
- arquitetura e segurança revisadas quando a mudança for relevante
- status de implementação ajustado se necessário
- alteração registrada no changelog da feature

## Implementação

- spec lida antes do código
- arquitetura validada antes da edição
- testes executados ou pendências registradas
- `gotrendlabs-test-engineer` usado quando houver testes concretos a criar ou revisar
- estado atualizado no final

## Testes

- unitários esperados definidos
- integração esperada definida
- fluxo/end-to-end esperado definido
- regressões por contrato mapeadas
- aceite observável registrado
- evidência de execução ou lacuna registrada
