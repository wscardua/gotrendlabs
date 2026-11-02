# ADR-0019 — Resolução e cancelamento por integração MCP

Data: 02/11/2026. Estado: aceito; implementação/validação locais concluídas e publicação em preparação. Workflow WFLOW-20261102-MCP-RESOLVE-CANCEL.

## Decisão

Acrescentar resolve_market e cancel_market com scopes explícitos e separados. FastAPI revalida delegação e mantém lock da integração até commit; depois bloqueia e relê o mercado. MarketLifecycleEngine continua único executor dos efeitos. Integração não usa conta staff compartilhada. Callback de auditoria registra ator técnico/responsável/correlação; ator humano nulo. Provas existentes conservam formato/hashes.

Precondição updated_at evita contexto alterado; cancelamento também confere expected_status. ID estável identifica mercado/opção. Leituras operacionais com IDs/versionamento são separadas do snapshot editorial para preservar aprovações atuais.

Recibos MCP imutáveis duráveis usam chave por integração/operação e hash completo; resolução reutiliza recibo do domínio com UUIDv5 derivado da integração/chave, sem colisão entre tenants. Ambos são gravados na transação dos efeitos, sem expurgo. Sem nova fila, scheduler ou acesso de banco no adaptador.

Cancelamento resolved é proibido nesta ferramenta porque o engine interpreta essa ação como undo humano. Concessões não são herdadas das ações humanas, grants ou migrations. Sem novas ferramentas de publicação/fechamento/undo.

## Consequências

Nova migration de recibos, ACL FastAPI SELECT/INSERT e sequência USAGE/SELECT, Django somente SELECT, trigger append-only. Exige deploy backend e MCP coordenado e concessão/novo consentimento explícitos após homologação. Timeout é indeterminado e exige repetir mesma chave/payload, sem afirmar rollback. Sem alterações de fórmulas de liquidação, refunds ou reputação.


Fechamento de 02/11/2026: a fatia inclui também exclusão MCP própria pelo serviço/recibo existentes, conforme ADR-0015, e reautenticação web no consentimento após sessão revogada. Essas extensões não alteram a decisão de transação/autoria. [Rollout](../operations/mcp-market-lifecycle-rollout.md).
