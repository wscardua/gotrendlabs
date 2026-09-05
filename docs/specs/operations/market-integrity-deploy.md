# Deploy e rollback — Ledger de Integridade

## Antes do deploy

1. Fazer snapshot/backup verificável do PostgreSQL e registrar o ponto de restauração.
2. Criar chave KMS assimétrica `ECC_NIST_EDWARDS25519`, uso `SIGN_VERIFY`, rotação por nova chave/alias e retenção das chaves públicas históricas.
3. Conceder `kms:GetPublicKey` aos processos verificadores. Conceder `kms:Sign` somente ao adaptador/processos de FastAPI e daemon estritamente necessários; negar Django e Flutter.
4. Configurar `GOTRENDLABS_INTEGRITY_KMS_KEY_ID` e `GOTRENDLABS_USER_COMMITMENT_SECRET` pelo secret manager. Nunca registrar seus valores.
5. Aplicar migrations `admin_ops 0018–0019`, `communications 0008` e `markets 0027–0028` antes de liberar escrita da nova versão.
6. Validar permissões `SELECT/INSERT`, triggers de `UPDATE/DELETE`, ausência de cascades e exclusão das tabelas de integridade de purges.

## Smoke de staging

- publicar mercado de teste e confirmar definição/ledger/assinatura com a chave pública;
- registrar previsão, reforço e revisão e confirmar comprovantes distintos sem PII;
- resolver, desfazer dentro da janela, resolver novamente e conferir novo prazo completo;
- forçar vencimento, executar dois ciclos concorrentes do daemon e confirmar Seal único/notificação única;
- adulterar cópia isolada de definição, compromisso, resultado, folha, assinatura e elo e confirmar falha;
- simular `kms:Sign` negado e confirmar mercado em `resolved`, alerta e retry seguro.

## Rollback

- desabilitar novas publicações/previsões dependentes do signer e pausar selagem, preservando todas as tabelas de integridade;
- reverter aplicações para a versão anterior somente se ela tolerar `sealed`; caso contrário manter leitura em manutenção até hotfix;
- não executar migration reversa destrutiva nem apagar eventos, Seals ou chaves públicas históricas;
- restaurar banco apenas para desastre integral, usando o snapshot registrado e reconciliando eventos externos posteriores;
- registrar toda correção pós-selagem por `market_corrected`, nunca por `UPDATE` no registro original.
