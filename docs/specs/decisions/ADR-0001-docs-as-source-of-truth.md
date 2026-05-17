# ADR-0001: Docs como fonte de verdade operacional

- Data: `2026-05-17`
- Status: `aceita`

## Contexto

O projeto vai usar IA para derivar e implementar a solução a partir da spec funcional, com múltiplas sessões e mudanças incrementais ao longo do tempo.

## Decisão

- A spec funcional e seus derivados técnicos versionados no repositório são a fonte de verdade operacional.
- O código pode ficar temporariamente defasado em relação aos docs.
- Mudanças relevantes devem nascer na spec afetada antes de alcançar a implementação.

## Impacto

- As skills devem consultar docs antes do código quando houver divergência.
- O estado do projeto precisa indicar quando algo está `defasado_pela_spec`.

## Alternativas rejeitadas

- tratar o código como fonte principal
- manter memória apenas na conversa ou em prompt longo
