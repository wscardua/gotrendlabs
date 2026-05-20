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
- Reconciliação de mercado cancelado com previsões abertas não é necessária no fluxo normal; quando automatizada no futuro, deve iniciar em modo de auditoria/alerta e só aplicar correção com política operacional explícita.

## Dependências

- Estados de mercado definidos em contratos.
- Eventos do `backend-api`.
- Persistência e filas/cache quando adotados.
