
- `ADR-0011-mcp-editorial-integrations.md`: MCP editorial sem banco, OAuth/serviço, gestão administrativa equivalente e reutilização de auditoria; implantação/habilitação produtiva pela PR #136, com HTTPS/grants/isolamento conferidos; Dot/piloto autenticado pendentes.
# Decisions


Use este diretório para registrar decisões técnicas estáveis e mudanças que alterem fronteiras, contratos ou fórmulas relevantes.

## Formato

- contexto
- decisão
- impacto
- alternativas rejeitadas
- data
- status

## Decisões registradas

- `ADR-0013-shared-admin-image-queue.md`: fila/executor compartilhados para mercados e badges, vínculos explícitos, cotas globais e confirmação na criação/edição.

- `ADR-0001-docs-as-source-of-truth.md`: docs como fonte de verdade operacional.
- `ADR-0002-resolution-payout-reputation-refund.md`: resolução, payout, reputação e refund.
- `ADR-0003-ec2-compose-rds-mvp.md`: deploy MVP em EC2 com Docker Compose e RDS.
- `ADR-0004-internal-cryptographic-ledger.md`: ledger interno verificavel, encadeado e append-only.
- `ADR-0005-aws-kms-ed25519.md`: assinaturas Ed25519 com chave privada protegida no AWS KMS.
- `ADR-0006-sealing-and-append-only-corrections.md`: janela de selagem e correcoes posteriores append-only.

- [ADR-0012 — fila persistente e thumbnails privadas](ADR-0012-private-thumbnail-worker.md), aceita em 2026-10-09, implementação local.

- [ADR-0014 — interpretação semântica de thumbnails](ADR-0014-semantic-thumbnail-brief.md), conceito visual via modelo textual e imagem com checkpoints separados.
