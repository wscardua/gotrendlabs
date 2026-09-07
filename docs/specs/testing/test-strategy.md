# Estratégia de Testes

## Objetivo

Garantir que cada feature tenha critérios de aceite verificáveis e cobertura suficiente para evolução guiada por specs.

## Princípios

- Testes acompanham contratos e comportamento, não apenas telas.
- Mudanças de spec devem atualizar os testes esperados.
- Features críticas precisam de testes em múltiplos níveis.
- Compatibilidade mobile deve ser testada por build/versionCode: `/health` sem headers, `/health` com build compatível, `/health` com build antigo, middleware `426` em endpoint não isento, cliente web sem bloqueio, gate Flutter para update obrigatório/opcional e promoção global de `426 code=app_update_required` pelo `ApiClient`.

## Níveis mínimos

- unitário: funções e regras isoladas
- integração: fronteiras entre camadas e persistência
- fluxo/end-to-end: jornadas principais do usuário e da operação

## Ciclo recomendado

1. atualizar spec da feature
2. revisar contratos afetados
3. ajustar critérios de aceite
4. definir testes esperados
5. implementar ou revisar código

## Governança

- Mudanças que alterem testes de feature devem atualizar `docs/specs/state/feature-changelog.md`.
- Revisões amplas de testes devem abrir workflow `test-review-cycle`.
- Uma feature não deve ser marcada como `validada` sem evidência de teste ou pendência documentada.
- `gotrendlabs-test-strategy` define o que deve ser testado; `gotrendlabs-test-engineer` transforma isso em testes executáveis e evidência.
- Integridade exige testes de adulteracao, assinatura, cadeia, Merkle, concorrencia, atomicidade KMS, ausencia de PII e contratos/UI web e mobile.
- A regressao de integridade deve distinguir retry operacional de adulteracao, detectar divergencia entre mercado/resultado atuais e snapshots assinados, exigir exatamente um compromisso correspondente para toda previsao humana ou IA, validar compromissos incluidos no Merkle e garantir que `null`/nao aplicavel/cancelado nao sejam apresentados como falha criptografica.
- O corte pre-producao deve ser testado em `dry-run`, exigir confirmacao de backup para executar, recusar mercados com prova protegida, reconciliar projecoes relacionadas e ser idempotente.
- Renomeacoes editoriais da taxonomia devem preservar a verificacao; troca de IDs associados ao mercado deve falhar. Timeout/erro da auditoria deve manter fechamento, retencao, email, push e processo daemon ativos, adiando apenas a selagem dependente.
- O daemon deve ser testado para criar alerta `high` deduplicado por divergencia, reabrir alerta revisado se a falha persistir, nao alertar mercados validos nem retries operacionais e expor o item na fila staff sem permitir recompensa.
- A regressao deve provar que nenhuma divergencia aplicavel, inclusive cadeia global invalida ou definicao ausente em estado publicado, permite `overall_valid=true` ou Seal; metadados persistidos do evento tambem devem estar cobertos pela assinatura.
- O contrato de resumo deve priorizar alerta pendente e impedir selo positivo em cards web/mobile ate revalidacao.
- O purge pre-producao deve preservar badges e notificacoes sem causalidade exata com um mercado removido.
- A verificacao publica deve ter plano de carga com volume representativo e `EXPLAIN (ANALYZE, BUFFERS)`: lookups de head/limite devem usar o indice unico de `sequence`; a auditoria integral `O(E)` permanece fora do request path e deve ser medida separadamente.
- Checkpoints exigem testes de assinatura/append-only, bootstrap integral, delta incremental, head concorrente, checkpoint regressivo/adulterado, paridade integral-incremental e auditoria diaria. Teste de consultas deve provar que o endpoint publico nao varre `integrity_ledger_events`; selagem deve executar auditoria integral fresca sob lock e detectar adulteracao historica anterior ao checkpoint. Divergencia identica no mesmo head deve respeitar backoff sem criar checkpoint/assinatura por ciclo e deve suprimir a fila automática de Seal antes de iterar candidatos. Contrato publico deve provar ausencia de eventos, IDs, referencias e timestamps individuais de previsao. Metadados persistidos de definicao, compromisso, Seal e folhas devem ter testes de adulteracao coluna a coluna.
- O guard de `TRUNCATE` dos checkpoints permanece identico em qualquer banco. A infraestrutura de testes desabilita temporariamente apenas esse trigger durante o `flush` do banco isolado e o reativa imediatamente; `UPDATE` e `DELETE` append-only continuam rejeitados para preservar a regressao de seguranca sem contaminar casos posteriores.
