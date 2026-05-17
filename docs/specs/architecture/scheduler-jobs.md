# Scheduler Jobs

## Responsabilidades

- Fechar mercados conforme janela configurada.
- Disparar reconciliações temporizadas e verificações operacionais.
- Acionar fluxos automáticos que dependem de tempo.

## Limites

- O scheduler executa ações previstas pelo domínio; ele não redefine regras.
- Reprocessamentos precisam ser idempotentes.
- Toda automação crítica deve registrar execução, sucesso, falha e tentativas.

## Dependências

- Estados de mercado definidos em contratos.
- Eventos do `backend-api`.
- Persistência e filas/cache quando adotados.
