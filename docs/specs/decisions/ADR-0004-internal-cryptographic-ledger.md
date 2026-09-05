# ADR-0004: Ledger criptografico interno

- Data: `2026-09-05`
- Status: `aceita`

## Contexto

Mercados precisam de prova verificavel de definicao, previsoes, resultado e historico, sem introduzir blockchain publica nesta fase.

## Decisao

Usar ledger global assinado, encadeado e append-only no PostgreSQL, complementado por definicoes, compromissos, Merkle proofs e Seals imutaveis por defesa no banco.

## Impacto

Adulteracoes passam a ser detectaveis e auditaveis. A garantia continua dependente dos controles do operador, banco, KMS e verificadores; nao equivale a consenso descentralizado.

## Alternativas rejeitadas

- apenas armazenar hashes sem assinatura/encadeamento
- blockchain publica, smart contracts ou Polygon nesta fase
