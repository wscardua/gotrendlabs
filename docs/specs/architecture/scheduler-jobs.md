# Scheduler Jobs

## Responsabilidades

- Fechar mercados conforme janela configurada.
- Disparar reconciliações temporizadas e verificações operacionais.
- Acionar fluxos automáticos que dependem de tempo.

## Limites

- O scheduler executa ações previstas pelo domínio; ele não redefine regras.
- Reprocessamentos precisam ser idempotentes.
- Toda automação crítica deve registrar execução, sucesso, falha e tentativas.
- Reconciliação de mercado cancelado com previsões abertas não é necessária no fluxo normal; quando automatizada no futuro, deve iniciar em modo de auditoria/alerta e só aplicar correção com política operacional explícita.

## Dependências

- Estados de mercado definidos em contratos.
- Eventos do `backend-api`.
- Persistência e filas/cache quando adotados.
