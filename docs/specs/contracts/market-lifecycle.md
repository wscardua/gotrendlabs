# Contrato: Ciclo de Vida de Mercado

## Estados canônicos

- `draft`: mercado ainda não publicado
- `scheduled`: publicado com abertura futura
- `open`: recebendo previsões
- `locked`: fechado para novas previsões e aguardando resolução
- `resolved`: resultado definido e efeitos aplicados
- `canceled`: encerrado sem resultado válido

## Regras

- Criação administrativa inicia mercado em `draft`.
- Publicação administrativa exige campos mínimos completos e opções válidas; quando aprovada, muda para `open`.
- Mercado `binary` exige exatamente duas opções canônicas: `SIM` e `NAO`, ambas com snapshot inicial `50%`.
- Mercado `multiple` exige ao menos duas opções, sem limite máximo fixo nesta etapa; snapshots iniciais são distribuídos automaticamente e devem somar `100%`.
- Opções de mercado são entidades referenciáveis por previsões; edição administrativa deve atualizar opções existentes por identidade/label estável quando possível.
- Opção com previsão vinculada em `orynth_predictions` não pode ser removida fisicamente; tentativa de remoção deve retornar erro de domínio claro.
- Mercados administrativos devem persistir `close_at`, `close_timezone` e `auto_close_enabled` para permitir fechamento automático pelo scheduler/daemon.
- `closes_in` é rótulo derivado de `close_at` para apresentação; não deve ser informado manualmente pelo admin.
- `close_label` é mensagem pública opcional sobre fechamento; não substitui `close_at` nem controla transição de estado.
- Se `auto_close_enabled=true`, a transição para `locked` deve ser executada pelo daemon/scheduler quando `close_at` vencer.
- Se `auto_close_enabled=false`, a transição para `locked` deve ser executada por operador staff via Admin Ops.
- Fechamento manual só é permitido para mercados `open` ou `scheduled` e deve registrar `market.lock`.
- Fechamento automático só é permitido para mercados `open` ou `scheduled`, com `auto_close_enabled=true`, `close_at` preenchido e vencido.
- Fechamento automático deve registrar `market.lock` com ator nulo/sistema e nota operacional `Fechamento automático pelo daemon.`
- Mercado sem campos operacionais mínimos não deve ser salvo pelo admin customizado.
- Mercado novo ou editado não pode usar categoria/subcategoria/evento bloqueado.
- O evento pertence à subcategoria e é a terceira camada da taxonomia do mercado (`categoria -> subcategoria -> evento`).
- Categoria, subcategoria e evento podem possuir aviso opcional (`notice`) para mercados sensíveis; os avisos são herdados por mercados vinculados e expostos como `category_notice`, `subcategory_notice` e `event_notice` no contrato público.
- Categorias, subcategorias e eventos são preservados fisicamente; bloqueio/desbloqueio administrativo é a forma operacional de retirar ou devolver uso.
- Bloqueio de categoria/subcategoria/evento deve registrar evento administrativo e manter motivo/data do bloqueio.
- Apenas `open` aceita novas previsões.
- A transição `open -> locked` pode ser manual ou automática conforme `auto_close_enabled`.
- A transição `locked -> resolved` exige operador ou processo autorizado, evidência, justificativa, opção vencedora, data/hora efetiva e timezone de resolução.
- `resolved_at` deve guardar o momento efetivo da resolução; `resolution_timezone` deve preservar o timezone selecionado para apresentação/auditoria.
- Timezone de resolução no Admin Ops deve ser selecionado a partir de lista controlada, não informado em texto livre.
- No backend, publicação, fechamento manual, fechamento automático, cancelamento, resolução e desfazer resolução devem permanecer centralizados em `MarketLifecycleEngine`, operando sobre cursor/transação recebidos de fora.
- Cancelamento administrativo muda o mercado para `canceled`, preserva o registro e deve gravar evento administrativo.
- `canceled` devolve 100% dos stakes bloqueados por previsões abertas, marca previsões como `canceled` e não altera reputação.
- O fluxo normal de cancelamento deve validar que nenhuma previsão `open` permaneceu no mercado antes de concluir a transição para `canceled`.
- Estados históricos inconsistentes, como mercado `canceled` com previsões ainda `open`, devem ser corrigidos por reconciliação operacional idempotente, com refund ausente em `prediction_refund` e evento administrativo `market.cancel_reconcile`.
- `resolved -> locked` é uma operação administrativa excepcional para desfazer resolução; deve estornar payout líquido, rebloquear stakes, reabrir previsões internas como pendentes de resultado e recalcular reputação.
- Mercado `resolved` não pode ser editado; alterações exigem desfazer resolução antes.
- Mercados `resolved` devem expor auditoria staff read-only via `GET /admin/markets/{slug}/resolution-audit`, sem mutação e sem recalcular regra no Django.
- A auditoria de resolução deve retornar erro `422` para mercados que não estejam em `resolved`.
- A auditoria deve resumir totais de participantes, vencedores, perdedores, stakes, refunds, payouts, losses e badges concedidas na resolução.
- A lista de participantes da auditoria deve ser paginada, com default de UI em 10 itens por página, e expor escolha, stake, probabilidade de entrada, payout esperado, resultado, lançamentos de ledger e badges da resolução.

## Campos mínimos expostos

- `market_id`
- `status`
- `resolution_type`
- `close_at`
- `resolved_at`
- `resolution_timezone`
- `winning_option_id`
- `resolution_note`
- `category_id`
- `category_notice`
- `subcategory_id`
- `subcategory_notice`
- `event_id`
- `event_notice`
- estado de bloqueio da taxonomia no contrato administrativo
