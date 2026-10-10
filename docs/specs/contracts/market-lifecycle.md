# Contrato: Ciclo de Vida de Mercado

## Estados canônicos

- `draft`: mercado ainda não publicado
- `scheduled`: publicado com abertura futura
- `open`: recebendo previsões
- `locked`: fechado para novas previsões e aguardando resolução
- `resolved`: resultado definido e efeitos aplicados
- `sealed`: historico final criptograficamente selado e verificavel
- `canceled`: encerrado sem resultado válido

## Regras

- Criação administrativa inicia mercado em `draft`.
- Publicação administrativa exige campos mínimos completos e opções válidas; quando aprovada, muda para `open`.
- Mercado `binary` exige exatamente duas opções canônicas: `SIM` e `NAO`, ambas com snapshot inicial `50%`.
- Mercado `multiple` exige ao menos duas opções, sem limite máximo fixo nesta etapa; snapshots iniciais são distribuídos automaticamente e devem somar `100%`.
- Opções de mercado são entidades referenciáveis por previsões; edição administrativa deve atualizar opções existentes por identidade/label estável quando possível.
- Opção com previsão vinculada em `gotrendlabs_predictions` não pode ser removida fisicamente; tentativa de remoção deve retornar erro de domínio claro.
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
- Os nomes enviados na criação/edição administrativa de mercado devem reutilizar os cadastros existentes no respectivo pai, mesmo com slug personalizado ou nome renomeado. A busca ignora caixa e espaços externos; ambiguidade retorna `409` e desfaz a transação. Slugs, avisos e bloqueios existentes são preservados.
- Categoria, subcategoria e evento podem possuir aviso opcional (`notice`) para mercados sensíveis; os avisos são herdados por mercados vinculados e expostos como `category_notice`, `subcategory_notice` e `event_notice` no contrato público.
- Categorias, subcategorias e eventos são preservados fisicamente; bloqueio/desbloqueio administrativo é a forma operacional de retirar ou devolver uso.
- Duplicados sem mercados na origem podem ser consolidados por operação excepcional com backup e auditoria, preservando todos os IDs/vínculos de mercados e os eventos distintos sem uso; nunca aplicar remapeamento em definições assinadas.
- Bloqueio de categoria/subcategoria/evento deve registrar evento administrativo e manter motivo/data do bloqueio.
- Apenas `open` aceita novas previsões.
- A transição `open -> locked` pode ser manual ou automática conforme `auto_close_enabled`.
- A transição `locked -> resolved` exige operador ou processo autorizado, evidência, justificativa, opção vencedora, data/hora efetiva e timezone de resolução.
- `resolved_at` deve guardar o momento efetivo da resolução; `resolution_timezone` deve preservar o timezone selecionado para apresentação/auditoria.
- Timezone de resolução no Admin Ops deve ser selecionado a partir de lista controlada, não informado em texto livre.
- Para todos os mercados (FEAT-EDITORIAL-001 v1.3 / FEAT-MCP-001 v1.4), `draft/scheduled -> open` exige parecer humano aprovado da revisão/hash/conteúdo/política atuais. Verificar após lock do mercado e antes da assinatura; recusar com `409 detail.code=editorial_approval_required`. Edição invalida aprovação. Ausência de ficha ou parecer atual bloqueia igualmente mercados humanos e MCP.
- No backend, publicação, fechamento manual, fechamento automático, cancelamento, resolução e desfazer resolução devem permanecer centralizados em `MarketLifecycleEngine`, operando sobre cursor/transação recebidos de fora.
- Cancelamento administrativo muda o mercado para `canceled`, preserva o registro e deve gravar evento administrativo.
- `canceled` devolve 100% dos stakes bloqueados por previsões abertas, marca previsões como `canceled` e não altera reputação.
- O fluxo normal de cancelamento deve validar que nenhuma previsão `open` permaneceu no mercado antes de concluir a transição para `canceled`.
- Estados históricos inconsistentes, como mercado `canceled` com previsões ainda `open`, devem ser corrigidos por reconciliação operacional idempotente, com refund ausente em `prediction_refund` e evento administrativo `market.cancel_reconcile`.
- `resolved` define `seal_due_at = resolved_at + market_seal_window_hours`.
- `resolved -> locked` é permitido somente antes de `seal_due_at`; exige motivo, estorna os efeitos atuais, reabre previsoes internas e limpa o prazo.
- `resolved -> sealed` e executado pelo daemon quando o prazo vence e exige Seal assinado e Merkle root validados na mesma transacao.
- `sealed` e terminal; correcoes posteriores sao novos eventos append-only.
- Mercado `resolved` não pode ser editado; alterações exigem desfazer resolução antes.
- Mercados `resolved` devem expor auditoria staff read-only via `GET /admin/markets/{slug}/resolution-audit`, sem mutação e sem recalcular regra no Django.
- A auditoria de resolução deve retornar erro `422` para mercados que não estejam em `resolved`.
- A auditoria deve resumir totais de participantes, vencedores, perdedores, stakes, refunds, payouts, losses e badges concedidas na resolução considerando apenas previsões `resolved`; posições `revised` permanecem no histórico de posição/sparkline e não entram na liquidação.
- A lista de participantes da auditoria deve ser paginada, com default de UI em 10 itens por página, e expor escolha, stake, probabilidade de entrada, payout esperado, resultado, lançamentos de ledger e badges da resolução para as previsões `resolved`.

## Campos mínimos expostos

- `market_id`
- `status`
- `resolution_type`
- `close_at`
- `resolved_at`
- `published_at`
- `seal_due_at`
- `sealed_at`
- `integrity_version`
- `integrity`
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

## Revisão aprovada pelo usuário em 2026-10-07 — gate universal

Todo mercado possui ficha editorial estruturada e revisão humana, independentemente de origem. Nova publicação exige aprovação vigente da versão/hash/política/conteúdo e configuração válida de fechamento. Ambos os modos exigem data/hora futura e fuso válido; automático registra auto_close_enabled=true para execução pelo daemon, manual registra false e deixa a ação staff disponível. A validação não comprova a disponibilidade momentânea do daemon. Legados publicados recebem ficha pendente sem mudar lifecycle, previsões ou provas; nenhum parecer fictício. Substitui explicitamente a exceção anterior para mercados humanos.

### Fechamento incompleto em definição publicada

O gate impede novas publicações incompletas; não autoriza alterar prazos/fuso/modo de uma definição já assinada. PATCH rejeitado conserva o registro original. A UI distingue informações submetidas de dados persistidos e explica essa proteção; não deve solicitar repetidamente o preenchimento como se a correção comum estivesse disponível. Correção de definição publicada exige fluxo auditável próprio, ainda fora deste contrato; cancelamento com refund permanece ação humana separada.

## Entrada de data/hora no Admin Ops

O formulário interpreta `datetime-local` como hora de parede no fuso explicitamente escolhido, tanto para fechamento quanto resolução; envia instante com offset à FastAPI. Não aplicar primeiro o fuso padrão Django. Recusar horas ambíguas/inexistentes em transições DST, orientando escolha inequívoca/UTC. Abertura e reenvio do editor preservam segundos/microssegundos de prazos originados por API/MCP. Criação humana salva draft para parecer; publicação é ação sobre versão salva e aprovada.

## Thumbnail administrativa de draft

FEAT-THUMB-001 acrescenta ao PATCH administrativo `thumbnail_candidate_id` e `thumbnail_expected_image_url`. Confirmação por ID sob o lock existente exige draft, autorização staff/MFA, arquivo/candidata validada não expirada e ausência de conflito. image_url é derivada no backend e permanece no contrato público. Geração/status não alteram mercado. Alteração mantém invalidação do parecer editorial; publicação da versão aprovada não incorpora uma seleção pendente silenciosamente. [Contrato detalhado](admin-thumbnails.md).
