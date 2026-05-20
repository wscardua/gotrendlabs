# Admin Ops

## Responsabilidades

- Criar, editar, revisar e resolver mercados.
- Moderar usuários, comentários e sugestões.
- Gerenciar taxonomia inicial.
- Acompanhar dashboards operacionais e troubleshooting.

## Princípios

- Operações administrativas devem seguir contratos do domínio.
- Ações sensíveis devem registrar operador, justificativa e momento.
- O painel principal pode oferecer UX específica, mas não deve burlar validações centrais.
- A FastAPI é a autoridade das operações administrativas de domínio; o Django Admin Ops é camada web consumidora.
- Rotas administrativas exigem sessão válida de usuário `is_staff=true`.
- Ações de fila operacional devem preservar estado concluído como informação auditável e impedir novo envio da mesma ação.

## Áreas principais

- mercados
- usuários
- badges
- resolução
- moderação
- taxonomia
- dashboards
- suporte técnico
- filas operacionais
- config operacional

## Implementação atual

- Admin Ops usa navegação principal única no topo nesta ordem: Dashboard, Config, Usuários, Categorias, Badge, Mercado, Resolução e Filas; menus secundários duplicados não devem ser renderizados nas telas internas.
- Dashboard consome o contrato staff `GET /admin/dashboard-summary` da FastAPI e exibe saúde operacional da plataforma em blocos de KPIs, ação necessária, saúde técnica, engajamento, economia/reputação, top mercados e eventos administrativos recentes.
- Dashboard não deve montar métricas por consultas locais espalhadas no Django; indisponibilidade da FastAPI deve renderizar estado operacional vazio/erro amigável sem mutação local.
- Métricas do Dashboard são agregações operacionais de leitura, incluindo contagens de mercados, filas, usuários, previsões, comentários, wallet, badges, logs técnicos, manutenção, SMTP, reCAPTCHA e status do daemon; não recalculam reputação, payout, probabilidade ou regra de domínio.
- Dashboard exibe o daemon como `Ativo`, `Atrasado` ou `Sem sinal` a partir do heartbeat calculado pela FastAPI, sem consultar processos locais no Django.
- Limites de status do daemon são configurados em Admin Ops Config por `daemon_stale_after_minutes` e `daemon_missing_after_minutes`; o limite de sem sinal deve ser maior que o limite de atraso.
- Dashboard deve manter contraste legível em modo escuro para KPIs, blocos de saúde, linhas métricas, tabelas e alertas.
- Mercado e taxonomia possuem primeira fatia real via FastAPI/Postgres.
- Endpoints administrativos cobrem listagem, criação, edição, publicação e cancelamento lógico de mercados.
- Categorias e subcategorias podem ser criadas, alteradas, bloqueadas e desbloqueadas pelo painel customizado.
- Taxonomia não possui exclusão física operacional; bloqueio lógico preserva histórico, mostra indicador visual no Admin Ops e impede uso em novos mercados.
- Criação/edição de mercado deve selecionar categoria e subcategoria a partir da taxonomia persistida; a subcategoria escolhida precisa pertencer à categoria selecionada.
- Na criação de mercado, categoria e subcategoria iniciam sem seleção para evitar publicação acidental em taxonomia errada.
- Eventos administrativos são registrados em `orynth_admin_events`.
- Mercados criados pelo admin nascem como `draft`; publicação válida muda para `open`; cancelamento muda para `canceled`.
- Mercados `binary` possuem opções fixas `SIM`/`NAO` com snapshot inicial `50%`/`50%`.
- Mercados `multiple` exigem pelo menos duas opções, sem limite máximo fixo nesta etapa, com percentuais iniciais decimais distribuídos igualmente.
- Edição de mercado deve sincronizar opções preservando registros existentes quando já houver previsões vinculadas; opções referenciadas por `orynth_predictions` não podem ser apagadas/recriadas silenciosamente.
- Criação/edição exige controles operacionais mínimos antes de salvar: resumo, fonte, critério de resolução, data/hora de fechamento, fuso e cor do card.
- Editor de mercado possui prévia ao vivo do card e aceita thumbnail do card como mídia local referenciada por URL.
- `close_at`, `close_timezone` e `auto_close_enabled` ficam persistidos para integração com scheduler/daemon.
- Quando `auto_close_enabled=true`, o fechamento para `locked` deve ser feito pelo daemon/scheduler; quando `false`, o Admin Ops deve oferecer ação manual de fechamento para mercados `open` ou `scheduled`.
- Fechamento manual move o mercado para `locked` e registra evento `market.lock` em `orynth_admin_events`.
- Cancelamento administrativo aplica refund total, cancela previsões abertas e deve validar que não restou previsão `open` antes de concluir a transição.
- Reconciliação de mercado já `canceled` com previsões `open` é operação excepcional de suporte; deve ser idempotente, preferir auditoria em `dry-run` antes da aplicação e registrar `market.cancel_reconcile`.
- Tela de resolução lista mercados `locked` e `resolved`, mostra data/hora/timezone da resolução e permite ordenação por resolução recente, resolução antiga ou pendências.
- Ação de resolver exige resultado, fonte pública, justificativa operacional, data/hora efetiva e timezone selecionado de lista controlada.
- Data/hora da resolução deve vir pré-preenchida com o momento atual no timezone do mercado, mas pode ser alterada pelo operador antes da publicação.
- Mercado `resolved` fica somente leitura no editor; alteração exige desfazer resolução antes.
- Mercado `resolved` deve exibir ação “Auditoria”, abrindo tela read-only consumida de `GET /admin/markets/{slug}/resolution-audit`.
- Tela de auditoria de resolução deve mostrar resumo do mercado, opção vencedora, data/hora/timezone, fonte/nota, totais de participantes, vencedores, perdedores, stake, refunds, payouts, losses e badges.
- Lista de participantes da auditoria deve paginar de 10 em 10 na UI e preservar `limit`/`offset`.
- Auditoria deve incluir legenda operacional do ledger explicando `refund`, `payout`, `loss`, `0 O₵` e badges, sem recalcular domínio no Django.
- O rótulo curto de prazo exibido nos cards é derivado automaticamente de `close_at`; admin não informa esse texto manualmente.
- A mensagem pública de fechamento (`close_label`) é opcional e textual; não controla o daemon.
- Percentuais iniciais das opções são persistidos em `orynth_market_options.probability_exact`; inteiros são derivados apenas na serialização/UI.
- Campos obrigatórios devem ser marcados visualmente no formulário e ações concluídas devem gerar feedback de sucesso para o operador.
- Browse de mercados administrativos filtra por status via query string e mantém contadores globais por status.
- Browse de mercados administrativos exibe `view_count` e `share_count` como indicadores compactos de popularidade operacional e permite ordenar por padrão, mais visualizados ou mais compartilhados.
- Browses principais de usuários, mercados, resolução, filas e logs usam `Carregar mais` em blocos cumulativos de 10 itens, preservando filtros aplicados.
- Browse de mercados administrativos deve degradar para leitura local em Postgres quando a FastAPI administrativa estiver indisponível ou retornar erro transitório, evitando bloquear a operação de visualização.
- Browse de mercados administrativos deve manter a ação primária focada em `Editar/visualizar`; acesso à página pública fica no editor do mercado, não na tabela de listagem.
- Gestão administrativa de usuários usa contratos staff da FastAPI para listagem, busca, detalhe operacional, desativação/reativação, revogação de sessões e ajuste manual de wallet.
- Browse administrativo de usuários permite filtrar por status/papel, buscar por email/handle/nome e ordenar por criação, último login, saldo ou reputação.
- Detalhe administrativo de usuário pode exibir dados privados para staff, incluindo perfil, wallet, ledger recente, reputação, previsões, comentários, filas, badges adquiridas, sessões e eventos.
- Ações administrativas de usuário exigem nota operacional, não podem ser executadas sobre a própria conta do operador e registram `user.deactivate`, `user.reactivate`, `user.sessions_revoke` ou `user.wallet_adjust`.
- Alteração de papel administrativo no detalhe do usuário usa contrato FastAPI, exige operador superuser, nota operacional, bloqueia alteração da própria conta e registra `user.roles_update`.
- Ajuste manual de wallet deve iniciar sem direção pré-selecionada, usar ledger/projeção na FastAPI e não pode alterar reputação.
- Browse de taxonomia administrativa usa tabela objetiva, filtros client-side por uso/bloqueio e card lateral com política de bloqueio.
- Filas operacionais possuem primeira fatia real para Mercado e Feedback, com dados persistidos e listagem no Admin Ops.
- Browse de filas operacionais exibe fila, item, tipo, data de criação, severidade interna, status e ação.
- Browse de filas operacionais permite filtrar por fila/status e ordenar por data de criação.
- A tela de revisão de item exibe contexto completo, status persistido, recompensa aprovada quando houver e ações disponíveis conforme tipo.
- Conversão em rascunho aparece apenas para sugestão de mercado; depois de convertida, a seção fica indisponível para novo envio.
- Aprovação de créditos aparece para Feedback e Mercado quando houver usuário cadastrado; depois de aprovada, a seção fica indisponível para alteração ou reenvio.
- Recompensas de fila usam ledger/projeção da wallet e bloqueiam duplicidade por item.
- Configuração geral de Admin Ops define `wallet_recharge_min_balance_oc`, o saldo máximo para usuário solicitar recarga educativa.
- Configuração geral de Admin Ops define os limites de heartbeat do daemon para status `Atrasado` e `Sem sinal`.
- Solicitações de recarga educativa entram na fila operacional como `wallet_recharge`; o Admin Ops aprova definindo valor em O₵ ou rejeita com nota, mantendo uma solicitação pendente por usuário.
- Aprovação de recarga educativa cria ledger `educational_recharge`, atualiza projeção de saldo e registra `wallet_recharge.approve`; rejeição registra `wallet_recharge.reject` sem alterar wallet.
- Comentários entram na fila operacional de moderação com filtro próprio e status `visible`/`hidden`.
- A tela de revisão de comentário permite ocultar/restaurar com nota operacional.
- Moderação de comentário registra `comment.hide` ou `comment.restore` em `orynth_admin_events`.
- Badges possuem catálogo administrável no Admin Ops, com upload de imagem para tema claro, upload opcional de imagem para tema escuro, texto público e regra automática selecionada de tipos controlados pelo backend.
- Browse administrativo de badges deve exibir nome/código, status, tipo, regra, categoria/subcategoria, contagem de conquistas e ação de edição.
- Formulário administrativo de badge deve exibir prévia do card público, atualizando nome, descrição, regra, imagens de tema e status antes de salvar.
- Regras de badge com recorte temático devem selecionar categoria e subcategoria a partir da taxonomia dinâmica persistida; subcategorias são filtradas pela categoria escolhida.
- Criação, edição e desativação de badge passam por contratos staff da FastAPI e registram `badge.create`, `badge.update` ou `badge.deactivate` em `orynth_admin_events`.
- Logs técnicos de troubleshooting ficam disponíveis no Admin Ops em área própria, com filtros operacionais e detalhe completo por contrato staff da FastAPI.
- Config operacional fica disponível no Admin Ops logo após Dashboard e permite controlar modo manutenção e parâmetros SMTP.
- Modo manutenção é persistido em arquivo runtime fora do banco para desviar acesso público para página estática de manutenção mesmo quando a conexão com PostgreSQL/FastAPI estiver indisponível.
- Config SMTP persiste parâmetros não sensíveis no banco; senha/API key ficam exclusivamente em variáveis de ambiente ou secret manager.
- Denúncias por usuários, moderação avançada, comunicações assíncronas de resolução, gestão de operadores e ajuste manual de reputação permanecem fora desta fatia.
