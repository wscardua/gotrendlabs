# Parecer humano MCP em uma ação — 2026-10-07

Workflow WFLOW-20261007-MCP-SINGLE-REVIEW-001. O usuário considera burocrática a sequência de preparar/enviar e depois registrar parecer. UI v1.3 substitui essa sequência.

## Resultado

- Um formulário e um botão **Registrar parecer humano**, com escolhas aprovar/devolver/rejeitar. Funciona diretamente em preparação ou revisão, sem submissão humana prévia. Contexto e ajustes de fontes são recolhíveis/opcionais; critérios/fontes são verificados uma vez.
- Um POST assessment FastAPI com ficha + decisão. Reusa preparação/snapshot e decisão na mesma transação, com MFA, locks, versão/hash, auditoria humana e gate de publicação existentes. Falha reverte inclusive revisões e eventos. Publicar permanece separado.
- Endpoints /record e /decision continuam compatíveis. Atestação humana não é inferida/pré-marcada dos relatos do agente. Campos faltantes de critérios são apresentados para preenchimento, sem serem satisfeitos automaticamente. Links de fonte inválidos não viram ações de navegação.

## Validação

**47 testes passaram em 139,495 s**, exit 0, em PostgreSQL temporário `test_gtl_mcp_single_final` destruído ao terminar. Inclui MCP editorial (40), publicação UI (2), consentimento (1) e adapter (4), cliente MCP TCP real OAuth/serviço, dez tools e cenários negativos.

Novos casos: aprovação/devolução/rejeição diretas; ausência de MFA/usuário comum/agente negados; versão antiga; assinatura/publicação de aprovação atual; rollback integral de hash antigo, lacuna real e falta de atestação; CSRF/PRG e envio por um único assessment; ausência de status/checkbox duplicados e atestação pré-marcada. Regressões da sequência antiga continuam aprovadas.

Chrome real em DEV: ficha #5 observada em revisão 9/in_review após operações do usuário, parecer vazio. Interface nova mostra uma única ação, ajustes opcionais e nenhum selector status_E; sem overflow desktop. Nenhuma escrita de ficha, aprovação ou publicação no DEV pelo agente nesta rodada. Captura local ignorada `.runtime/mcp-single-review/review.jpg`. Não atualizar aba do usuário com formulário em preenchimento: nova aba aberta para a conferência.

Ruff F, Django check, OpenAPI export/check e diff check aprovados. Feature/contratos/ADR/aceite/runbook/estado/changelogs sincronizados; sem migrations novas.

## Pendências

Feature permanece parcial por Dot/HTTPS externo, homologação real LM Studio e deploy. Não há homologação responsiva adicional nesta rodada. Nenhuma ação em produção/merge/deploy. Revisão humana real do draft #5 continua com o usuário; pendências/gaps não removidos automaticamente.
