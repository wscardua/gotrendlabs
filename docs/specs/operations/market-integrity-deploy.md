# Deploy e rollback — Ledger de Integridade

## Antes do deploy

1. Fazer snapshot/backup verificável do PostgreSQL e registrar o ponto de restauração.
2. Criar chave KMS assimétrica `ECC_NIST_EDWARDS25519`, uso `SIGN_VERIFY`, rotação por nova chave/alias e retenção das chaves públicas históricas.
3. Conceder `kms:GetPublicKey` aos processos verificadores. Conceder `kms:Sign` somente ao adaptador/processos de FastAPI e daemon estritamente necessários; negar Django e Flutter.
4. Configurar `GOTRENDLABS_INTEGRITY_KMS_KEY_ID` e `GOTRENDLABS_USER_COMMITMENT_SECRET` pelo secret manager. Nunca registrar seus valores.
5. No ambiente pre-producao, executar `.venv/bin/python manage.py purge_unsigned_markets` para inventario, criar/validar backup externo e somente entao executar `.venv/bin/python manage.py purge_unsigned_markets --execute --backup-confirmed`.
6. Aplicar migrations `admin_ops 0018–0019`, `communications 0008` e `markets 0027–0030` antes de liberar escrita da nova versão.
7. Confirmar que mercados em `open`, `locked`, `resolved`, `sealed` ou `canceled` possuem `market_integrity_definitions`; `draft` e `scheduled` ainda nao exigem prova.
8. Validar permissões `SELECT/INSERT`, triggers de `UPDATE/DELETE`, ausência de cascades e exclusão das tabelas de integridade de purges.

## Smoke de staging

- publicar mercado de teste e confirmar definição/ledger/assinatura com a chave pública;
- registrar previsão, reforço e revisão e confirmar comprovantes distintos sem PII;
- resolver, desfazer dentro da janela, resolver novamente e conferir novo prazo completo;
- forçar vencimento, executar dois ciclos concorrentes do daemon e confirmar Seal único/notificação única;
- adulterar cópia isolada de definição, compromisso, resultado, folha, assinatura e elo e confirmar falha;
- criar previsao humana e previsao de agente IA e confirmar cobertura exata por compromisso; remover um compromisso em copia isolada e confirmar bloqueio da selagem;
- renomear categoria/subcategoria/evento e confirmar prova valida; trocar associacao taxonomica do mercado e confirmar divergencia;
- simular timeout da auditoria e confirmar que fechamento/comunicacoes continuam, o daemon permanece vivo e apenas a selagem do ciclo e adiada;
- simular `kms:Sign` negado e confirmar mercado em `resolved`, alerta e retry seguro.

## Rollback

- desabilitar novas publicações/previsões dependentes do signer e pausar selagem, preservando todas as tabelas de integridade;
- como o Flutter ainda nao esta em producao, limpar/reinstalar dados locais do app e distribuir somente o contrato final; nao manter fallback temporario de `sealed` para builds antigos;
- reverter aplicações para a versão anterior somente se ela tolerar `sealed`; caso contrário manter leitura em manutenção até hotfix;
- não executar migration reversa destrutiva nem apagar eventos, Seals ou chaves públicas históricas;
- restaurar banco apenas para desastre integral, usando o snapshot registrado e reconciliando eventos externos posteriores;
- registrar toda correção pós-selagem por `market_corrected`, nunca por `UPDATE` no registro original.
