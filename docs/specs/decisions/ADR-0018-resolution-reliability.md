# ADR-0018: Resolução transacional, replay e janela operacional

## Status

Aceita para a implementação solicitada em 2026-10-25; publicação pendente.

## Decisão

Bloquear/reler o mercado antes de qualquer validação de resolução. Persistir recibo UUID, hash canônico do pedido e prazo da resolução na mesma transação dos efeitos. O prazo identifica a ocorrência vigente (gerado pelo servidor); replay de ocorrência desfeita/substituída retorna conflito. Recibos não armazenam tokens nem cópia de PII ou payload editorial.

A consulta staff do recibo permite recuperar confirmação após perda da resposta. Ausência do recibo é indeterminada enquanto o POST pode estar em andamento. Nenhum retry automático de mutação. A chave pertence à operação e não é recriada em erros de formulário/transporte.

A janela começa no instante de publicação registrado no ledger pelo servidor, independente da data declarada. Substitui a fórmula anterior baseada em resolved_at apenas para novas resoluções; não reescreve provas históricas. Não altera fórmulas financeiras da ADR-0002 nem permissões MCP.

## Consequências

Migration aditiva de recibos obrigatória antes do runtime. Clientes administrativos e testes atualizados diretamente, sem fallback para contrato antigo. Timeout de 15s reduz erros transitórios, mas a segurança depende de replay e reconciliação. Testes concorrentes PostgreSQL, rollback de assinatura e UI indeterminada são obrigatórios.
