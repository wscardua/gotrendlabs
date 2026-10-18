---
id: FEAT-RESOLUTION-AGENDA-001
titulo: Agenda estruturada de apuração
status_spec: aprovada
status_impl: implementada_validada
ultima_atualizacao: 2026-10-18
aprovacao: escopo_autorizado_pelo_usuario
dependencias: [FEAT-RES-001, FEAT-INTEGRITY-001]
versao: 1.2
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

A agenda e sua aplicação produtiva são registradas no [recibo de aplicação de 18/10/2026](../../operations/resolution-agenda-application-20261018.md); o [fechamento de 17/10](../testing/resolution-agenda-closeout-20261017.md) preserva o histórico do rollout. A correção v1.2 da apresentação do painel foi implantada pela PR #173/merge 2c4ddd9, com CI/build/deploy e smoke técnico produtivo aprovados: [fonte vigente do fechamento](../testing/contracts-timeline-closeout-20261018.md). Não reaplicar inventário ou assinaturas para corrigir a interface. Distribuição Flutter é distinta do deploy web/API.

## Apresentação das etapas — correção de 18/10/2026

O painel apresenta fechamento como Fechado em locked/resolved/sealed pelo estado autoritativo. A data exibida é explicitamente o horário programado; não existe timestamp efetivo de fechamento no contrato atual. Open/scheduled com `closure_inconsistent` exibem alerta, sem conclusão local. A previsão usa `resolution_overdue` para vencimento e permanece neutra, sem sugerir apuração iniciada; em terminais é histórica. Cancelamento não deixa obrigação futura de resolução/selagem. Resolução e selagem usam seus registros efetivos; estado terminal sem timestamp informa data não registrada. `seal_due_at` é prazo de selagem, nunca prova de ação. Marcos no dia local mostram Hoje com horário e fuso. Legenda separa estado da etapa e posição temporal. Histórico/original/provas, filtros, contadores e escala cumulativa permanecem preservados.

A faixa apresenta marcos em ordem cronológica com espaçamento variável conforme a duração, nome e data abaixo do símbolo. O espaço adicional é linear ao intervalo na janela da consulta, com piso de 136px para legibilidade; não é escala linear pura. Registros efetivos usam círculo e horários previstos losango vazado. Hoje integra cada sequência no instante de referência. Intervalos em dias/horas/minutos complementam a escala visual adaptada. Etapas sem timestamp aparecem no trecho Sem data com seu estado, sem posicionamento temporal fabricado. A faixa ocupa a largura da linha do mercado. Marcos coincidentes mantêm ordem estável; a paginação não muda a sequência por mercado. Rolagem horizontal por teclado em viewport estreito; todas as etapas permanecem abertas. Este desenho substitui as alternativas de eixo com ramificações e espaçamento uniforme avaliadas durante o QA.

Tratamento visual da faixa: linha fina, intervalos acima das ligações, nomes e datas alinhados abaixo. Hoje usa traço vertical e cor de destaque, sem caixa. Etapas sem data aparecem no canto direito ao lado da faixa; permanecem na mesma linha em todas as larguras, com rolagem horizontal da faixa inteira quando necessário; a sequência datada mantém rolagem por teclado.

A região focável de cada cronograma usa `aria-labelledby` associado ao título do mercado, com instruções de rolagem em `aria-describedby`. Nomes acessíveis distintos e IDs únicos são preservados ao carregar mais.
