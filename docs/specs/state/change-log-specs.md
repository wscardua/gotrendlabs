# Change Log de Specs

## 2026-06-13

- registrada evolução de `FEAT-REP-001` para tratar badges conquistadas como propriedade histórica: `BadgeDefinition.is_active` controla exibição pública/histórica e `BadgeRule.is_active` controla novas concessões.
- atualizado contrato de reputação/ranking para manter badges pausadas visíveis no catálogo público/autenticado para todos, sem novas concessões, e preservar ranking e compartilhamento público por token para quem já conquistou.
- registrada evolucao de `FEAT-MOBILE-001` para manutencao mobile independente da web, controlada pelo Admin Ops em runtime JSON e aplicada de forma autoritativa pela FastAPI para clientes com `X-GoTrendLabs-Client: mobile`.
- atualizado contrato mobile de `GET /health` para expor `maintenance.web_enabled`, `maintenance.mobile_enabled`, `maintenance.mobile_message`, `checks.api` e `checks.database`, com status degradado quando o backend nao estiver saudavel.
- registrado que a manutencao mobile nao possui entrada operacional visivel nem excecao por papel no app; usuarios publicos, staff e superusers permanecem bloqueados no shell mobile durante a janela.

## 2026-06-12

- registrada evolução de `FEAT-NOTIFY-001`/`FEAT-MOBILE-001` para push FCM real em Android com Firebase local, sender backend via Firebase Admin SDK, channel Android `gtl_default`, payloads seguros e defaults operacionais `none`/dry-run preservados.
- registrada aba Admin Ops `Dispositivos` em Push mobile para observabilidade de `PushDevice` sem expor token bruto.

## 2026-06-11

- registrada evolução de `FEAT-AUTH-001` para OAuth real em Google, Facebook e X, com vínculo seguro por identidade externa ou email verificado pelo provedor.
- registrada política de envio imediato para emails críticos de identidade/acesso já existentes, mantendo eventos de produto e volume no daemon.
- registrada exigência de rodapé institucional automático e customizável por template nos emails transacionais renderizados por `communications`.

## 2026-06-08

- registrada evolução de `FEAT-NOTIFY-001` para push mobile com provider `none`/dry-run, policies/templates/preferências, outbox `PushDelivery`, endpoints FastAPI e Flutter noop.
- atualizada arquitetura mobile para refletir estrutura iOS gerada em `apps/mobile/ios`, mantendo Android como MVP já validado e iOS Simulator como preparação local.
- atualizados contratos de base URL mobile para separar Android emulator (`10.0.2.2`), iOS Simulator/Chrome local (`127.0.0.1`) e aparelho físico (`<ip-do-mac>`).
- atualizados critérios de aceite mobile para simulação iOS local com Xcode completo, CocoaPods, device iOS listado por `flutter devices` e bases locais via `127.0.0.1`.
- atualizado estado operacional de FEAT-MOBILE-001 para remover iOS Simulator dos gaps e manter TestFlight/App Store, push, offline e QA visual amplo como pendências futuras.

## 2026-06-07

- criadas specs iniciais de mobile Flutter: `mobile-flutter.md`, `mobile-api-contracts.md`, `mobile-mvp.md`, `mobile-ux.md` e `mobile-acceptance.md`.
- registrada direção visual mobile dark-first inspirada nas imagens fornecidas pelo usuário, com cards fortes de mercado, detalhe com hero, abas `Visao geral`/`Comunidade`, bottom navigation e bottom sheets, sem copiar identidade de terceiros.
- adicionadas skills mobile locais para arquitetura, UX, contratos API, testes, implementação Flutter e governança docs/memória.
- atualizado status operacional, integration map, known gaps e README mobile para refletir que as specs existem, mas o projeto Flutter ainda não foi criado.

## 2026-06-06

- registrada evolução de `FEAT-OPSLOG-001` para daemon de produção com intervalo de 300 segundos e defaults de saúde 7/21 minutos no Dashboard Admin Ops.
- registrada evolução de `FEAT-SUGGEST-001` para categoria de sugestão baseada na taxonomia ativa administrada, endpoint público `GET /taxonomy` e validação backend contra categoria inexistente/bloqueada.
- registrada evolução de `FEAT-AUTH-001` e `FEAT-WALLET-001` para indicação bonificada com código opcional no cadastro, ledger `reward_referral`, configuração `referral_bonus_gtl` no Admin Ops e UI contextual em carteira/perfil.
- registrada evolução de `FEAT-AUTH-001` para prefixo `@` fixo no identificador editável e retorno contextual `← Voltar` com fallback seguro.
- registrada evolução de `FEAT-AIAGENT-001` para auditoria administrativa com rótulos e explicações de tipo, status e motivo, preservando códigos técnicos.
- atualizado `frontend-web.md` para fechamento legível em cards de mercado e remoção de ISO cru em labels públicos.

## 2026-06-05

- registrada evolução de `FEAT-NOTIFY-001` para emails transacionais com `EmailTemplate`, `EmailDelivery`, `EmailConfirmationToken`, templates editáveis no Admin Ops, daemon de outbox e retries por provider.
- registrada decisão operacional de agrupar templates e logs de entrega em `Politica de Emails`, mantendo edição PT-BR com variáveis documentadas, preview local de HTML e listagem de outbox sem expor links sensíveis.
- registrada evolução de `FEAT-AUTH-001` para confirmação de email por token expirável, login limitado até confirmação, reenvio limitado e recuperação de senha sem exposição pública do `reset_url`.
- atualizado contrato de eventos para refletir outbox transacional antes do event bus dedicado.
- registrado que o remetente operacional padrão é `no-reply@gotrendlabs.com.br` e que host, porta, TLS/SSL e usuário SMTP são parâmetros não sensíveis administráveis quando o fallback SMTP for usado.

## 2026-06-09

- registrada evolução de `FEAT-NOTIFY-001` para provider Resend via API HTTPS, mantendo outbox/templates/retries/logs existentes e segredo somente em `GOTRENDLABS_RESEND_API_KEY`.
- atualizado Admin Ops/Dashboard para configuração e saúde de email provider-aware, com SMTP genérico como fallback e Resend como opção transacional.
- registrado requisito de recuperação de senha com tentativa de envio imediato após commit e links absolutos nos templates transacionais.

## 2026-05-24

- registrada evolução de `FEAT-AUTH-001` para reset administrativo auditado por Admin Ops e exibição de `Sua progressão` para operadores sem participação no ranking público
- atualizado contrato `backend-api.md` com `POST /admin/users/{user_id}/password-reset`, nota obrigatória, bloqueios de autoação/conta desativada e permissão restrita para alvos administrativos
- registrada evolução de `FEAT-REP-001` para expor badges conquistadas resumidas no ranking e filtro público por evento
- atualizado contrato `reputation-ranking.md` para aceitar `event`, retornar `selected_event` e serializar eventos na taxonomia de filtros
- registrada decisão de UI de manter o handle como identificação principal da linha e renderizar badges após o nome/handle, com excedentes resumidos como `+N`
- registrada evolução de `FEAT-AIAGENT-001` para cobertura maior do ciclo de comentários IA, com candidatos configuráveis, tentativas LLM limitadas e fallback em respostas não publicáveis/validação segura
- registrado que erro real de provedor LLM interrompe tentativas do ciclo para evitar cascata de custo durante instabilidade
- registrada atualização de `scheduler-jobs.md` para explicitar avaliação local de múltiplos mercados e limite de chamadas LLM por ciclo
- registrada regra de cautela factual do prompt IA para evitar afirmações técnicas específicas, eventos, números, anúncios ou fontes ausentes do contexto do mercado
- registrada evolução de `FEAT-OPSLOG-001` e `FEAT-AIAGENT-001` para retenção configurável separada de logs técnicos e auditoria IA no Admin Ops
- registrado que o purge operacional passa a usar `created_at` e o prazo atual de `gotrendlabs_site_config`, afetando também registros antigos

## 2026-05-17

- criada a estrutura canônica de specs técnicas, contratos, decisões, testes e memória operacional
- adicionadas 11 feature specs iniciais derivadas da spec funcional principal
- adicionadas 4 skills canônicas no repositório para edição de specs, orquestração, guarda arquitetural e estratégia de testes
- adicionado `feature-changelog.md` para histórico granular por feature
- adicionadas 4 skills técnicas por stack para Django, FastAPI, Postgres e operações assíncronas/comunicações
- adicionada governança de workflows para mudanças multi-documento, retomada e reversão lógica
- reforçada a presença de testes no guia rápido e nas regras de conclusão
- adicionado índice de skills em `tools/skills/gotrendlabs/README.md`
- adicionada revisão de governança em `governance-review.md`
- adicionadas skills `gotrendlabs-software-architect` e `gotrendlabs-test-engineer`
- workflows e guia atualizados para incluir arquitetura/segurança e testes executáveis
- registrada implementação parcial de `FEAT-AUTH-001` com backend FastAPI como autoridade de autenticação/sessão e Django como consumidor web
- registrada evolução de `FEAT-AUTH-001` com aceite obrigatório de política, edição de perfil e exclusão lógica de conta
- registrada implementação parcial de `FEAT-WALLET-001` e `FEAT-REP-001` com núcleo de usuário persistido em PostgreSQL e exposto pela FastAPI
- registrada projeção `gotrendlabs_wallet_balances` para leitura rápida de saldo sem substituir o ledger auditável
- registrada implementação parcial de `FEAT-MARKET-001` e `FEAT-MARKET-002` com mercados públicos persistidos em PostgreSQL, expostos pela FastAPI e consumidos pelo Django

## 2026-05-18

- registrada primeira fatia real do Admin Ops para mercados e taxonomia
- formalizada proteção por usuário `is_staff=true` nas rotas administrativas
- documentado cancelamento lógico de mercado e auditoria simples em `gotrendlabs_admin_events`
- atualizados gaps restantes de admin para separar CRUD básico real de fluxos operacionais ainda pendentes
- registrada regra de opções por tipo: `binary` fixo `SIM`/`NAO` em `50%`/`50%` e `multiple` com duas ou mais opções distribuídas automaticamente
- registrado filtro real por status no browse administrativo de mercados
- registrada persistência de `close_at`, `close_timezone`, `auto_close_enabled` e thumbnail de card para mercados administrativos
- registrada regra de não salvar mercado administrativo com campos operacionais mínimos ausentes
- registrado `closes_in` como rótulo automático derivado de `close_at`, removendo entrada manual do admin
- registrado fechamento manual para mercados sem daemon automático, com transição para `locked` e evento `market.lock`
- registrada resolução manual com `resolved_at`, `resolution_timezone`, payout/reputação, undo operacional e refund total de cancelamento
- registrada preservação de gráficos de consenso após resolução usando previsões `open` e `resolved`
- registrado que `close_label` é mensagem pública opcional e que percentuais ficam em `gotrendlabs_market_options.probability_exact`
- registrado vínculo obrigatório entre categoria/subcategoria da taxonomia persistida no editor administrativo de mercado
- registrada primeira fatia real de filas operacionais para sugestão de mercado e feedback
- registrado envio autenticado ou guest com nome/email para feedback e sugestão
- registrado browse administrativo de filas com data de criação, tipo do item e ordenação por data
- registrada regra de ação específica por fila: conversão em rascunho apenas para sugestão de mercado e crédito operacional para itens com usuário cadastrado
- registrado bloqueio de crédito duplicado por item de fila e inclusão de `reward_suggestion` no contrato de wallet
- registrada regra de integridade para opções de mercado: opções com previsões vinculadas não podem ser removidas/recriadas silenciosamente durante edição administrativa
- registrada primeira fatia real de comentários em mercados com criação autenticada, like/dislike, ocultação/restauração administrativa e trilha via eventos administrativos
- registrados detalhes de contrato/arquitetura da FEAT-COMMENT-001: endpoints públicos/admin, tabelas de comentário/reação, handles `@`, ações iconizadas e fallback local de desenvolvimento
- registrada atualização da FEAT-MARKET-001 para filtros rápidos funcionais no feed, destaque principal por visualizações excluindo `draft`/`canceled` e contador de curtidas nos cards

## 2026-05-19

- registrada reconciliação operacional idempotente para mercados `canceled` com previsões `open`, incluindo `dry-run`, evento `market.cancel_reconcile` e preservação de reputação
- registrado que o cancelamento administrativo deve validar ausência de previsões abertas após refund antes de concluir a transição para `canceled`
- registrada evolução de FEAT-REP-001 para badges administráveis com catálogo público, imagem, regras controladas e concessão automática idempotente
- adicionados contratos públicos e administrativos de badges em `reputation-ranking.md`
- registradas responsabilidades de `backend-api`, `frontend-web` e `admin-ops` para impedir cálculo de elegibilidade fora do domínio
- registrado que regras temáticas de badge usam categoria/subcategoria da taxonomia dinâmica cadastrada no Admin Ops
- explicitado no contrato administrativo de badges quais campos são obrigatórios e quais permanecem opcionais no formulário
- registrado que o browse administrativo de badges expõe categoria/subcategoria da regra para auditoria operacional rápida
- registrado que o formulário administrativo de badges exibe prévia do card público antes de salvar
- registrado que badges possuem imagem padrão/tema claro e imagem opcional para tema escuro, com troca visual por tema e fallback
- registrada `BadgeAwardEngine` como fonte única de avaliação e persistência de conquistas de badge por eventos de domínio
- registrado compartilhamento MVP de badge conquistada via rota web autenticada, ação nativa do navegador e fallback de cópia de link/texto
- ajustado gap restante de badges naquele momento para separar compartilhamento básico de card social completo; gap posteriormente reduzido pela evolução de compartilhamento social com Open Graph/Twitter
- registrada evolução do compartilhamento social para pergunta, resultado e badge com links por rede, metadados Open Graph/Twitter e imagem social dinâmica
- registrado uso de origem pública configurável para crawlers sociais e aviso quando o host local não for rastreável
- registrado token opaco em link público de badge conquistada para evitar exposição de identificador direto de usuário
- registrado fallback visual de thumbnail para mercado sem imagem/thumb, aplicado ao feed e às imagens sociais
- registrada política pública de uso com leitura em modal no cadastro, mantendo aceite obrigatório versionado
- registrado que login/cadastro mantêm navegação pública compacta e retorno `← Feed` no primeiro painel de conteúdo
- registrado ticket de onboarding do cadastro selecionado por maior `view_count` entre mercados publicados não cancelados, excluindo `draft` e `canceled`, com fallback para mercado mais recente em empate/ausência de visualizações

## 2026-05-20

- registrado que telas públicas de autenticação mantêm rodapé público compartilhado além de navegação, tema e retorno `← Feed`
- registrado que login/cadastro expõem provedores sociais iniciais Google, Facebook e X como affordances iconizadas, mantendo OAuth real como gap
- registrado que títulos de cards de mercado navegam para o detalhe como redução de atrito no feed público
- registrada área Config no Admin Ops para modo manutenção em runtime JSON e parâmetros SMTP não sensíveis em banco
- registrado que segredo SMTP permanece fora do banco/interface, via ambiente ou secret manager
- registrada separação operacional de credenciais PostgreSQL por serviço Django/FastAPI com fallback local `POSTGRES_*`
- registrado `GET /admin/dashboard-summary` como contrato staff agregado para Dashboard Admin Ops
- registrado que o Dashboard Admin Ops usa métricas de saúde operacional sem consultas locais espalhadas no Django

## 2026-05-23

- registrada implementação parcial de `FEAT-NOTIFY-001` com inbox in-app persistida, sino no topo, contador de não lidas, dropdown e marcação de leitura
- registrado `comment_count` público em `MarketResponse`, cards da home/feed e detalhe do mercado, derivado apenas de comentários `visible`
- registrada regra de notificações sociais para mercados participados por previsão: nova previsão, curtida de mercado, comentário e curtida em comentário
- registrada regra de notificações sistêmicas para crédito recebido, mercado participado fechado/resolvido e badge recebida
- registrado roteamento contextual do dropdown: badges para `/badges/`, créditos para `/wallet/`, eventos de mercado para o detalhe do mercado e comentários para `#comments`
- atualizado mapa de integração para refletir JSON runtime de manutenção, `gotrendlabs_site_config`, SMTP via ambiente e resumo operacional centralizado na FastAPI
- registrada `MarketLifecycleEngine` como ponto central do ciclo operacional de mercado no backend
- registrado `GET /admin/markets/{slug}/resolution-audit` como contrato staff read-only para auditoria de resolução
- registrado que Admin Ops mostra ação “Auditoria” em mercados resolvidos, com paginação de 10 participantes e legenda de ledger
- registrada rodada QA hard com 100 usuários simulados em `docs/research/qa-simulacao-hard-100-usuarios-20260520.md`
- adicionada skill `gotrendlabs-prediction-markets` para curadoria assistida de mercados de previsão com dados internos, trends sociais, diversidade, links exatos de verificação e anti-repetição
- adicionado guia `docs/guides/gotrendlabs-prediction-markets-skill.md` para uso da skill de curadoria de mercados

## 2026-05-21

- reforçada a skill `gotrendlabs-prediction-markets` para exigir validação da fonte de resolução antes de aceitar mercados sugeridos
- documentado que a validação pode usar navegador local, browser automation, APIs, web search, ORM, banco ou APIs internas quando necessário
- adicionado `Status de validacao da fonte` ao formato esperado de mercados sugeridos
- registrado que operadores (`staff`/`superuser`) não recebem bootstrap público de reputação, wallet inicial, badges ou atividade social
- registrado que thumbnails de mercado com `image_url` devem ser imagens puras do evento, sem título/texto embutido, mantendo HTML/API como fonte de verdade de metadados
- documentado o lote editorial seed de 27 mercados em `docs/specs/state/editorial-seed-markets-20260521.md`
- registrado que `/profile/` usa dados reais de `gotrendlabs_user_profiles`, com `display_name` como fonte principal do nome editável
- registrado marcador administrativo `is_bot` restrito a Admin Ops, com filtro, badge, edição auditada e sem exposição pública
- registrado que ajuste manual de wallet da própria conta é permitido para operadores, mantendo auditoria, enquanto outras autoações sensíveis seguem bloqueadas
- registrado que `GT₵ distribuídas` exclui créditos de `staff` e `superuser`
- registrado que ticket de previsão não pré-seleciona opção, orienta escolha explícita, usa radio obrigatório e apresenta estado sem saldo disponível
- registrado que card social de mercado exibe opções/probabilidades e CTA editorial para o detalhe do mercado

## 2026-05-22

- ampliada a skill `gotrendlabs-prediction-markets` para suportar categoria `cripto`, fontes cripto/on-chain e aviso obrigatório de que mercados cripto não caracterizam recomendação de investimento
- documentado seed DEV de 3 mercados cripto em `docs/specs/state/editorial-seed-markets-20260521.md`, mantendo status `draft`, taxonomia idempotente e thumbs locais autorais
- documentado lote aprovado `Mercado > Cripto` com aviso no nível da subcategoria, eventos por moeda e comando idempotente `seed_crypto_markets_20260522`
