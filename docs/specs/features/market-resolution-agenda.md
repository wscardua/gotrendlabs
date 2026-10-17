---
id: FEAT-RESOLUTION-AGENDA-001
titulo: Agenda estruturada de apuração
status_spec: aprovada_para_implementacao
status_impl: validado_localmente
ultima_atualizacao: 2026-10-17
aprovacao: escopo_autorizado_pelo_usuario
dependencias: [FEAT-RES-001, FEAT-INTEGRITY-001]
versao: 1.1
origem: spec_prediction_social_market_pt.md
impacta: [backend-api, database, admin-ops, frontend-web, mobile, mcp]
contratos_afetados: [market-lifecycle.md, integrity-ledger.md, agent-integrations.md, domain-events.md]
---

# Resolução prevista

Revisão 1.1 autorizada pelo usuário em 17/10/2026: a agenda tem somente `expected_resolution_at` e `schedule_timezone` IANA. `resolution_date` é o mesmo conceito, sem duplicação; `resolved_at` continua resolução efetiva e `suggested_resolution_date` uma sugestão. Corte documental e recuperação, quando necessários, são condições do critério integral, sem campos estruturados, filtros ou ações próprios.

FastAPI valida instantes com offset explícito, fuso válido e previsão estritamente posterior ao fechamento. Draft pode ser incompleto; publicação exige ambos e previsão futura. Ausência não inventa data. A previsão é operacional: não autoriza, bloqueia ou dispara resolução nem altera saldo/estado. A decisão segue critérios e gates normais do ciclo, sem parser de texto.

Classificações exclusivas: terminal; fechamento inconsistente para open/scheduled vencido; agenda pendente; previsão vencida (agora > previsão); apuração prevista. Igualdade na previsão ainda não é atraso. Filtros/contadores/ordenação são da API.

Reagendamento staff/MFA com motivo, versão esperada, lock e evento assinado conserva previsão original. Só open/locked; exige nova previsão futura posterior ao fechamento, sem alterar critérios/opções. Terminais recusam; undo mantém agenda/histórico.

Persistência UTC/timestamptz; projeção e eventos vinculados ao hash original, sem alterar definições antigas. Campos retirados ficam apenas em armazenamento histórico para verificar provas já emitidas; não integram contrato atual.

Admin: formulário só Resolução prevista/Fuso; painel distingue fechamento, previsão e resolução efetiva, mostra Hoje, pendências e histórico, sem conclusão por passagem de tempo. Web/Flutter usam o mesmo contrato; MCP revisa snapshot e mantém scopes/gates humanos.

## Critérios de aceite

Offsets/fusos/ordem; draft incompleto e publicação futura; atraso nos limites; resolução permitida antes da previsão respeitando demais regras; reschedule/concorrência/terminais/undo; assinatura/rollback/provas históricas; migração revisável sem escrita em dry-run; MCP schemas/replays/snapshot; formulário e painel simples/responsivos; Flutter analyze/test; OpenAPI export/check.

Fora do escopo: notificações, emails, resolução automática, parser editorial, merge/deploy/migração produtiva.

## Fechamento e estado de implantação

Produto final e evidências consolidados em [fechamento 17/10/2026](../testing/resolution-agenda-closeout-20261017.md). Implementação local validada; PR/CI/merge/deploy ainda pendentes da aprovação prévia solicitada pelo usuário. Inventário não aprovado não autoriza complemento de dados. Distribuição Flutter é distinta do deploy web/API.
