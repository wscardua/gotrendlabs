# ADR-0004: Ledger criptografico interno

- Data: `2026-09-05`
- Status: `aceita`

## Contexto

Mercados precisam de prova verificavel de definicao, previsoes, resultado e historico, sem introduzir blockchain publica nesta fase.

## Decisao

Usar ledger global assinado, encadeado e append-only no PostgreSQL, complementado por definicoes, compromissos, Merkle proofs e Seals imutaveis por defesa no banco.

## Impacto

Adulteracoes passam a ser detectaveis e auditaveis. A garantia continua dependente dos controles do operador, banco, KMS e verificadores; nao equivale a consenso descentralizado.

Como a implementacao ainda nao chegou a producao, o corte inicial remove do ambiente mercados sem definicao assinada em vez de criar provas retroativas. O procedimento exige inventario, backup, `dry-run` e recusa qualquer mercado que ja possua prova/evento de integridade. Depois do corte, todo mercado ativo nasce pelo fluxo atomico de publicacao e toda previsao, humana ou de agente IA, possui compromisso correspondente.

## Alternativas rejeitadas

- apenas armazenar hashes sem assinatura/encadeamento
- blockchain publica, smart contracts ou Polygon nesta fase
