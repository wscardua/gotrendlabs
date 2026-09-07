# Scheduler Jobs

## Responsabilidades

- Fechar mercados conforme janela configurada.
- Disparar reconciliações temporizadas e verificações operacionais.
- Acionar fluxos automáticos que dependem de tempo.
- Rodar como processo operacional separado quando necessário, sem carregar regra de domínio no comando/processo.

## Limites

- O scheduler executa ações previstas pelo domínio; ele não redefine regras.
- Regras temporizadas ficam centralizadas no `backend-api`; comandos Django ou processos daemon apenas orquestram chamadas a esses serviços.
- Reprocessamentos precisam ser idempotentes.
- Toda automação crítica deve registrar execução, sucesso, falha e tentativas.
- O daemon operacional registra heartbeat em logs técnicos para que o Admin Ops detecte processo ativo, atrasado ou sem sinal.
- No deploy MVP de produção, o container `daemon` executa ciclos a cada 300 segundos; os limites padrão de saúde são 7 minutos para `Atrasado` e 21 minutos para `Sem sinal`, podendo ser ajustados pelo Admin Ops.
- Reconciliação de mercado cancelado com previsões abertas não é necessária no fluxo normal; quando automatizada no futuro, deve iniciar em modo de auditoria/alerta e só aplicar correção com política operacional explícita.
- O daemon chama o ciclo de agentes IA como automação isolada: configs desligadas geram no-op, falhas LLM não interrompem rotinas principais e o heartbeat inclui resumo de comentários, previsões, skips e erros.
- O ciclo de comentários IA pode avaliar múltiplos mercados localmente, mas chamadas LLM devem respeitar limite explícito de tentativas por ciclo e parar em erro real de provedor.
- Fechamento automático deve cancelar mercados sem participantes humanos, liberando previsões abertas existentes, inclusive stakes bot criados por falha/configuração.
- O daemon drena a outbox de `communications_emaildelivery`, aplicando provider configurado, retries e resumo de enviados/falhos/suprimidos no heartbeat operacional.
- O daemon drena a outbox de `communications_pushdelivery`, aplicando provider `none`/dry-run, retries, invalidação automática de tokens rejeitados e resumo de enviados/dry-run/falhos/suprimidos no heartbeat operacional.
- O daemon sela mercados `resolved` vencidos com `FOR UPDATE SKIP LOCKED`; valida Merkle e assinatura antes do commit e mantem `resolved` em qualquer falha.
- A auditoria das provas nativas e da cadeia global e iniciada antes das mutacoes de mercado e independe de estado, vencimento ou selagem. Assim, divergencias em mercados `open`, `locked`, `resolved`, `sealed` ou `canceled` entram na fila na primeira passagem posterior ao problema. Divergencias geram alertas operacionais deduplicados de severidade alta; falhas de infraestrutura e retries continuam em seus rastros proprios e nao sao rotulados como adulteracao.
- Auditoria, fechamento, selagem, retencao, email, push e agentes possuem isolamento de falha por tarefa. Indisponibilidade da auditoria nunca encerra o processo daemon nem impede fechamento e comunicacoes independentes; por seguranca, a selagem do ciclo pode ser suprimida quando a auditoria nao conclui.
- A auditoria global usa checkpoint assinado: incremental em cada ciclo e integral no bootstrap ou a cada 24 horas. O head e capturado como fronteira; eventos posteriores ficam pendentes para o ciclo seguinte, sem serem classificados como adulteracao. Selagem executa auditoria integral fresca sob lock antes de prosseguir. Divergencia identica no mesmo head respeita backoff de uma hora para evitar full scan e assinatura KMS a cada ciclo, sem deixar de reapresentar o alerta deduplicado.

## Dependências

- Estados de mercado definidos em contratos.
- Eventos do `backend-api`.
- Persistência e filas/cache quando adotados.
