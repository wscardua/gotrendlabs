# Mobile

Diretorio reservado para o frontend mobile Flutter do GoTrendLabs.

As specs iniciais do mobile estao em:

- `docs/specs/architecture/mobile-flutter.md`
- `docs/specs/architecture/mobile-api-contracts.md`
- `docs/specs/features/mobile-mvp.md`
- `docs/specs/features/mobile-ux.md`
- `docs/specs/testing/mobile-acceptance.md`

O projeto Flutter ainda nao foi criado neste diretorio.

Guardrail: o mobile sera cliente da FastAPI. Ele podera manter estado de UI, sessao/token, cache leve e preferencias locais, mas nao deve calcular saldo, payout, probabilidade, reputacao, badges, resolucao, IA ou auditoria.
