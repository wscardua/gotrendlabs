# Known Gaps

- Fórmula de probabilidade agregada básica está implementada para previsão/stake; ainda falta decisão para amortecer peso de reputação e evitar concentração futura.
- Fórmula MVP de reputação foi fechada para resolução manual; ainda falta avaliar amortecimento futuro e impacto de concentração.
- Política MVP de cancelamento foi fechada como refund total; ainda falta comunicação transacional assíncrona ao usuário.
- Gráficos de consenso são recalculados sob demanda a partir de previsões `open`/`resolved`; ainda falta snapshot materializado por tempo para auditoria histórica mais rica e escala.
- FEAT-COMMENT-001 possui comentários, reações e ocultação/restauração; ainda faltam denúncias por usuários, respostas/thread, edição/exclusão pelo autor, paginação avançada e event bus assíncrono.
- Templates e cadência de comunicações ainda precisam de especificação adicional.
- FEAT-AUTH-001 ainda não possui OAuth real para Google/Facebook; endpoint social existe apenas como placeholder de contrato.
- FEAT-AUTH-001 ainda precisa de política final para cookie seguro, refresh/revogação avançada e hardening fora do ambiente local.
- FEAT-AUTH-001 ainda não confirma alteração de email por mensagem transacional; alteração é direta nesta fase.
- FEAT-AUTH-001 usa versão fixa de política de uso `2026-05-17`; versionamento administrável fica para etapa futura.
- FEAT-MARKET-001/002 possui admin CRUD básico real para mercado e taxonomia, e FEAT-RES-001 possui auditoria staff read-only de resolução aplicada; ainda faltam revisão editorial avançada, gestão de operadores e auditorias avançadas fora do ciclo de resolução.
- Fallbacks locais mutáveis foram removidos de previsão/stake, ranking, comentários e Admin Ops; em indisponibilidade da FastAPI, Django deve exibir erro/estado vazio em vez de alterar domínio diretamente.
- FEAT-MARKET-001/002 usa snapshots persistidos e séries visuais derivadas de `orynth_predictions`; ainda falta tabela materializada de histórico de snapshots para analytics/escala.
- FEAT-WALLET-001 já possui bloqueio de stake, refund, payout, perda por resolução, reconciliação operacional para cancelados inconsistentes e ajuste manual auditado por admin; ainda falta recarga educativa.
- FEAT-REP-001 usa fórmula MVP em resolução; fórmula avançada futura depende de decisão técnica registrada.
- FEAT-REP-001 possui badges administráveis, concessão automática MVP e compartilhamento social com card Open Graph/Twitter; ainda faltam raridade pública, temporadas e reprocessamento administrativo em lote.
- FEAT-SUGGEST-001 cobre a primeira fatia real de filas para sugestões de mercado e feedback recompensável; ainda faltam event bus assíncrono, histórico público de feedback do usuário, comunicações transacionais e moderação de comentários.
