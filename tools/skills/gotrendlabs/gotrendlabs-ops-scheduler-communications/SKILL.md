---
name: gotrendlabs-ops-scheduler-communications
description: Use esta skill para implementar e revisar jobs temporizados, eventos de domínio, comunicações, rastreamento operacional e fluxos assíncronos do GoTrendLabs sem duplicar regras centrais do backend.
---

# GoTrendLabs Ops Scheduler Communications

Use esta skill quando a tarefa principal envolver automações temporizadas, emails, eventos ou operação assíncrona.

## Objetivo

Integrar scheduler, comunicações e operação assíncrona ao domínio de forma observável, idempotente e orientada por eventos.

## Fluxo padrão

1. Verificar workflow aberto quando a mudança tocar eventos, jobs, comunicações ou estado.
2. Ler a feature alvo e os contratos de eventos.
3. Ler `docs/specs/architecture/scheduler-jobs.md` e `communications.md`.
4. Mapear gatilhos, payloads, retentativas e efeitos esperados.
5. Verificar dependências de tempo, idioma, entrega e monitoramento.
6. Implementar jobs, handlers e rastros operacionais necessários.
7. Registrar testes, falhas esperadas e pendências operacionais.

## Regras

- Jobs devem ser idempotentes sempre que possível.
- Eventos de domínio precisam ter shape estável.
- Comunicações não devem duplicar regra de elegibilidade.
- Falhas e reprocessamentos precisam ser observáveis.
- Idioma do usuário deve ser respeitado nas mensagens.
- Mudanças em eventos exigem revisão de contratos e testes de regressão.

## Entradas principais

- `docs/specs/features/`
- `docs/specs/contracts/domain-events.md`
- `docs/specs/architecture/scheduler-jobs.md`
- `docs/specs/architecture/communications.md`
- `docs/specs/testing/`

## Saídas esperadas

- desenho ou implementação de jobs
- integração baseada em eventos
- envio de comunicações rastreável
- fluxo operacional compatível com retries e auditoria
