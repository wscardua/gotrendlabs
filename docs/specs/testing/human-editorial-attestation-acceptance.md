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
