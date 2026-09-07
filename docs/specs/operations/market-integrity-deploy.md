# Deploy e rollback — Ledger de Integridade

## Antes do deploy

1. Criar snapshot manual do RDS `gotrendlabs-prod-db`, aguardar estado `available` e registrar seu identificador como ponto de restauração.
2. Criar chave KMS assimétrica regional `ECC_NIST_EDWARDS25519`, uso `SIGN_VERIFY`, descrição/tag de produção e alias `alias/gotrendlabs-integrity-signing`. Rotação ocorre por nova chave e troca controlada do alias; nunca agendar exclusão de chave que já tenha assinado registros.
3. Conceder à role `gotrendlabs-prod-ec2-role`, em política separada e restrita ao ARN da chave, somente `kms:Sign`, `kms:GetPublicKey` e `kms:DescribeKey`. O Django recebe `AWS_EC2_METADATA_DISABLED=true`; apenas FastAPI e daemon usam o signer. A EC2 compartilhada continua sendo limitação de isolamento do MVP, a ser substituída por identidade por workload quando houver separação física.
4. Gerar `GOTRENDLABS_USER_COMMITMENT_SECRET` com fonte criptográfica, armazenar junto de `GOTRENDLABS_INTEGRITY_KMS_KEY_ID` em `gotrendlabs/prod/app-secrets` e sincronizar somente essas duas entradas para `/opt/gotrendlabs/.env.prod`, com permissão `0600`. Nunca registrar seus valores em saída SSM, GitHub Actions ou logs.
5. Garantir em `.env.prod`: `GOTRENDLABS_ENV=production`, `AWS_DEFAULT_REGION=us-east-1`, o alias KMS e o segredo de commitment. Validar somente presença/comprimento, nunca conteúdo.
6. Criar 1 GiB de swap persistente na EC2 caso continue ausente, pois o Django passa de um para dois workers Uvicorn no mesmo host `t4g.micro`. Confirmar `vm.swappiness=10`, espaço em disco e memória disponível antes/depois do deploy.
7. Aplicar todas as migrations pendentes, incluindo `admin_ops 0018–0019`, `communications 0008` e `markets 0027–0031`, antes de liberar escrita da nova versão.
8. Como a plataforma ainda não foi lançada, executar no container da nova imagem `python manage.py purge_unsigned_markets` para inventário e, somente após o snapshot validado, `python manage.py purge_unsigned_markets --execute --backup-confirmed`. O comando remove todos os mercados atuais sem definição, inclusive `draft`/`scheduled`; não há assinatura retroativa nem convivência legada.
9. Confirmar que o corte deixou zero mercados sem definição. Novos `draft`/`scheduled` podem existir depois do corte e continuam sem prova até a publicação normal.
10. Validar permissões `SELECT/INSERT`, triggers de `UPDATE/DELETE/TRUNCATE`, ausência de cascades e exclusão das tabelas de integridade de purges.
11. Criar alarme CloudWatch sobre `AWS/KMS SuccessfulRequest` para volume anômalo de `Sign`. Estado desabilitado/negação/timeout da chave é observado pelos logs e alertas operacionais fail-closed da aplicação; acompanhar também memória/swap/CPU da EC2 durante o primeiro ciclo do daemon e nas primeiras 24 horas.

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
- confirmar dois processos worker do Django e apenas um container/processo de daemon;
- consultar `/api/integrity/public-key`, executar assinatura/verificação real sem persistir payload sensível e validar fingerprint/chave histórica;
- confirmar `/api/integrity/status`, dashboard/fila de integridade, cards sem falso selo positivo e ausência de mercados pré-lançamento sem prova;
- acompanhar logs de FastAPI/daemon, métricas KMS, memória e swap sem material sensível.

## Rollback

- desabilitar novas publicações/previsões dependentes do signer e pausar selagem, preservando todas as tabelas de integridade;
- como o Flutter ainda não está em produção, distribuir somente o contrato final; não manter fallback temporário de `sealed` para builds antigos;
- reverter aplicações para a versão anterior somente se ela tolerar `sealed`; caso contrário manter leitura em manutenção até hotfix;
- se o segundo worker pressionar memória, retornar temporariamente o comando Django a um worker e manter o swap até análise; isso não altera domínio nem dados;
- não executar migration reversa destrutiva nem apagar eventos, Seals ou chaves públicas históricas;
- restaurar o snapshot somente para desastre integral durante o corte pré-lançamento; depois da primeira prova real, preferir correção append-only e nunca apagar história válida;
- registrar toda correção pós-selagem por `market_corrected`, nunca por `UPDATE` no registro original.

## Registro da implantação — 2026-09-07

- PR principal `#114`, merge `c2e75b6`; hotfix transacional `#115`, merge final `c40fd61`.
- GitHub Actions `34157223820` e `34158379066`: testes e deploy concluídos com sucesso.
- Snapshot RDS criptografado: `gotrendlabs-prod-pre-integrity-20260907-01`, estado `available` antes do corte.
- KMS: chave `bcbb43d0-cfba-465d-9c1d-500776ede30c`, `ECC_NIST_EDWARDS25519`, `SIGN_VERIFY`, alias de produção e IAM limitado ao ARN exato.
- Fingerprint público validado: `b971f3baf64555002c200d2d34098aa0566da9a796feffae45e4b6145af5124a`; segredo de commitment permaneceu apenas no Secrets Manager e runtime.
- Primeira tentativa de corte: FK defensiva de `PushDelivery` abortou o commit e o PostgreSQL reverteu a transação integralmente. O hotfix passou por 32 testes especializados e pela suíte completa antes da nova execução.
- Corte final: 30 mercados, 4 previsões, 43 comentários, 7 notificações e 21 entregas push relacionadas removidos; repetição retornou zero em todas as contagens.
- Smoke: cadeia `verified`, auditoria integral, sequência atual/verificada `0`, zero pendências, assinatura KMS real válida, API/banco `ok`, dois workers Django, um daemon, swap de 1 GiB ativo. O site permaneceu intencionalmente em manutenção web pré-lançamento.
