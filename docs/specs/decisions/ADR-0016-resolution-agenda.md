# ADR-0016 — Agenda assinada por complemento append-only

Data: 2026-10-17. Estado: aceita para implementação local.

A definição v1 e sua reconstrução permanecem byte a byte estáveis: adicionar campos à reconstrução invalidaria assinaturas e compromissos já emitidos. Agenda inicial de nova publicação e complemento revisado de mercado publicado são eventos assinados `market_schedule_registered` no ledger existente, vinculados ao hash da definição. Revisões `market_schedule_rescheduled` conservam anterior/novo, versão, motivo, ator, instante e proveniência. Nenhuma rotina purge é executada.

A tabela de mercado contém apenas projeção consultável e versão. Ledger guarda snapshots completos; primeira previsão é imutável. Auditoria verifica assinatura/hash/vínculo/continuidade e igualdade da projeção, incluindo antes da selagem. Pacote público inclui os eventos já existentes do ledger. Toda assinatura ocorre na mesma transação da mutação; falha aborta. Grants existentes de mercados/ledger são reutilizados, sem nova tabela ou permissão MCP.

Migração não reescreve definição, previsões, opções, estados ou finanças. Inventário explicitamente revisado é comparado sob lock ao hash, revisão e estado atuais. Ausências ativas continuam pendentes; terminais não recebem previsão fabricada. Reversão preserva eventos e colunas: desativar novas mutações e corrigir por novos eventos, nunca apagar provas.

## Revisão de produto 1.1 — 17/10/2026

A pedido do usuário, o contrato ativo passa a conter apenas resolução prevista e fuso. As decisões acima sobre corte/recuperação estruturados são substituídas; regras editoriais continuam no critério. Não há gate temporal de resolução baseado na previsão. Mantêm-se histórico original/vigente e transações assinadas.

Migration aditiva de estado remove campos aposentados do ORM e constraints antigas, preservando colunas físicas e todos os bytes assinados. Verificação histórica usa as chaves de cada snapshot original; novas revisões referenciam o snapshot anterior intacto, com projeção atual simplificada. Não se recalculam assinaturas. Essa retenção é preservação de prova, não fallback de API.
