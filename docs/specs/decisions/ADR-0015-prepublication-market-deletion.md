# ADR-0015: Exclusão física de mercados pré-publicação

Data: 2026-10-11. Status: aceita pelo usuário; substitui proposta lógica local não publicada.

Decisão: remover fisicamente mercado draft em preparation/in_review e seu parecer, ficha e revisões, mediante staff/MFA e revisão esperada. Não adicionar deleted_at. Publicados, previsões e provas impedem operação.

FastAPI mantém autorização/locks/validação/auditoria e transação. PostgreSQL permite remover revisões apenas via função SECURITY DEFINER restrita, com search_path fixo, objetos qualificados, PUBLIC sem EXECUTE e permissão exclusiva de runtime FastAPI. A função revalida elegibilidade antes de remover ficha/histórico e alertas mutáveis vinculados; grants gerais append-only não mudam. Dependências de apresentação são removidas; sugestões/auditorias de agentes são desvinculadas, preservando créditos/auditoria. Nenhuma prova criptográfica pode ser removida.

Recibos idempotentes MCP viram marcador mínimo com ID/deleted, mantendo chave/hash para recusar replays com not_found sem recriar o mercado; não retêm conteúdo editorial. Replays também verificam existência sob lock compartilhado. Uma nova chave pode criar outro mercado; slug fica livre. Jobs são desvinculados/expirados e perdem snapshot/usage, preservando cotas por operador/global; worker ignora retorno tardio; prune existente limpa candidatas/arquivos gerados órfãos. Uploads manuais ou compartilhados não são apagados indiscriminadamente.

O DELETE exige expected_market_id junto de expected_revision para distinguir mercado novo em slug reutilizado. Migrations editorial_integrations.0006 e admin_ops.0026 devem anteceder o runtime.
