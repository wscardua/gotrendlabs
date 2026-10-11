# Aceite: responsabilidade editorial humana

2026-10-11, FEAT-EDITORIAL-001 v1.7, solicitação explícita do usuário.

- Approve + confirmação: aceitar documento sem frase obrigatória/seção final, relato com pendências, política antiga e anúncio inválido/duplicado/fora do prazo textual. Preservar documento, identidade do revisor, data, snapshot e decisão auditada.
- Publicação usa atestado da revisão/hash atual sem repetir gates de conteúdo editorial.
- Falta de confirmação, autorização/MFA, versão/hash obsoletos, estado inválido ou divergência do snapshot continuam rejeitados e sem gravação parcial. Edição posterior exige novo parecer.
- Schema/tamanho do documento e configuração operacional de fechamento continuam vigentes.
- Preparação/validação/submissão MCP preservam seus próprios critérios; integração não recebe capacidade de aprovar ou confirmar revisão humana.
- UI apresenta alertas como apoio e explica responsabilidade, sem exigir reescrever frases.

Execução e resultados no workflow WFLOW-20261011-HUMAN-EDITORIAL-ATTESTATION. Homologação/publicação produtiva ainda pendentes.

Resultado: 90 casos aprovados na suíte de 91 (251.951s); única expectativa antiga de revision=1 após aprovação foi atualizada para revision=3. Caso corrigido e seis testes de referência reexecutados: 7/OK (4.477s). Todos os 91 cenários validados cumulativamente. Django check/compilação/OpenAPI/diff aprovados; DEV HTTP200.

## Implantação técnica concluída — PR #156

Entrega técnica implantada em PRD pela PR #156, merge 32a45131920af6f1427f484531b26b249cb5ef76. CI final da PR (38149320217) e main/deploy (38150080993) aprovados, 495 testes/2 skips por execução; build/OpenAPI aprovados, SSM c7d84727-16a3-4495-8056-5d20048b350d Success. Migrations editorial_integrations.0006/admin_ops.0026 aplicadas, serviços/worker recriados. Smoke com role real FastAPI, fixtures e auditoria em transação revertida confirmou exclusão preparation/in_review, limpeza de revisões, ID antigo 409, atestação humana e gate de publicação; rollback verificado. Execução da função pela role Django negada com 42501; PUBLIC sem EXECUTE, FastAPI sem DELETE geral de revisões. Site/API/discovery HTTP200, administração anônima 401 e JS atualizado. MCP expõe checklist v1.3/modelo v1.6 com hashes corretos e política v1.2/hash preservada, sem nova ferramenta/permissão. Snapshot pré-migration disponível. Nenhum mercado real excluído/aprovado ou inferência paga iniciada. Branch local/remota preservadas; homologação final do painel por operador staff/MFA permanece pendente, sem impedir conclusão técnica deste escopo. [Recibo](prepublication-editorial-production-20261011.md). Esta entrada substitui pendências produtivas anteriores deste escopo, preservadas como histórico.
