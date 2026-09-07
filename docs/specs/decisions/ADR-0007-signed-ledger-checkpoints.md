# ADR-0007: Checkpoints assinados e verificacao incremental do ledger

- Data: `2026-09-07`
- Status: `aceita`

## Contexto

A verificacao publica e a selagem percorriam toda a cadeia global em `integrity_ledger_events`. Como cada previsao, reforco e revisao adiciona evento, o custo cresceria linearmente e poderia degradar FastAPI, Django, Flutter e PostgreSQL.

## Decisao

O daemon produz checkpoints globais canonicos, assinados e append-only. Cada checkpoint atesta o ultimo segmento verificado, o head observado, o ultimo hash valido, o checkpoint anterior, o tipo de auditoria (`full` ou `incremental`), a versao do verificador e eventual falha detectada.

A auditoria incremental roda no inicio de cada ciclo do daemon. A auditoria integral roda quando nao existe checkpoint valido e, depois, ao menos a cada 24 horas. A verificacao publica valida o ultimo checkpoint e compara seu head ao head atual em tempo constante; ela nunca dispara silenciosamente uma varredura integral. Eventos posteriores ao checkpoint produzem estado `pending`, nao adulteracao.

Antes de selar, o backend adquire o lock global e executa auditoria integral fresca ate o head capturado na mesma transacao. O checkpoint acelera leituras publicas, mas nao autoriza sozinho uma transicao irreversivel. Seal continua bloqueado enquanto qualquer evento global ou registro aplicavel ao mercado estiver invalido ou indisponivel.

Depois de uma divergencia confirmada, o mesmo head e a mesma falha usam backoff de uma hora antes de outra varredura integral/assinatura. Mudanca do head e solicitacao explicita eliminam o backoff. O alerta operacional continua deduplicado e atualizado em todo ciclo.

## Consequencias

- A leitura publica global deixa de ser `O(E)` e passa a exigir poucos lookups e uma verificacao de assinatura.
- Auditoria integral independente continua existindo para detectar defeitos no verificador incremental ou no checkpoint.
- Cada selagem assume custo `O(E)` da auditoria global integral nesta fase, em troca de nao confiar em atestacao historica no ponto irreversivel; segmentacao autenticada fica como evolucao futura se a carga exigir.
- Checkpoints exigem assinatura KMS somente quando o head/estado muda ou quando a auditoria integral periodica e executada.
- Web e mobile distinguem `verified`, `pending`, `failed` e `unavailable`; `pending` nao e exibido como adulteracao.
- O mecanismo permanece um ledger interno e nao elimina a dependencia dos controles de banco, KMS e operacao.

## Alternativas rejeitadas

- confiar em booleano mutavel de cache sem assinatura;
- continuar varrendo toda a cadeia em requisicoes publicas;
- tratar atraso normal do daemon como falha criptografica;
- introduzir Merkle global, Polygon ou ancoragem publica nesta fase.
