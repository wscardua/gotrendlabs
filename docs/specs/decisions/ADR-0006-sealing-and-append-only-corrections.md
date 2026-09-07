# ADR-0006: Selagem e correcoes append-only

- Data: `2026-09-05`
- Status: `aceita`

## Decisao

`resolved` inicia janela configuravel, default 12 horas. Antes de `seal_due_at`, operador pode desfazer com motivo e retornar a `locked`. Depois de `sealed`, nenhuma mutacao destrutiva e permitida; correcoes sao novos eventos `market_corrected` que referenciam o evento anterior.

## Consequencias

O resultado continua operacionalmente corrigivel durante a janela, mas o historico final passa a ser verificavel. Como o recurso ainda nao foi implantado em producao, mercados pre-producao sem prova original sao removidos por corte controlado e nao recebem assinatura retroativa.
