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
- O daemon drena a outbox de `communications_emaildelivery`, aplicando guarda de sandbox SES, retries e resumo de enviados/falhos/suprimidos no heartbeat operacional.
- O daemon drena a outbox de `communications_pushdelivery`, aplicando provider `none`/dry-run, retries, invalidação automática de tokens rejeitados e resumo de enviados/dry-run/falhos/suprimidos no heartbeat operacional.

## Dependências

- Estados de mercado definidos em contratos.
- Eventos do `backend-api`.
- Persistência e filas/cache quando adotados.
