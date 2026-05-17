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

## Nova feature

- frontmatter completo
- escopo incluído e excluído claros
- contratos afetados declarados
- camadas impactadas declaradas
- testes esperados e critérios de aceite definidos
- desenho de solução e riscos avaliados por `orynth-software-architect`

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
- `orynth-test-engineer` usado quando houver testes concretos a criar ou revisar
- estado atualizado no final

## Testes

- unitários esperados definidos
- integração esperada definida
- fluxo/end-to-end esperado definido
- regressões por contrato mapeadas
- aceite observável registrado
- evidência de execução ou lacuna registrada
