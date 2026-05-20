# Change Log de Specs

## 2026-05-17

- criada a estrutura canônica de specs técnicas, contratos, decisões, testes e memória operacional
- adicionadas 11 feature specs iniciais derivadas da spec funcional principal
- adicionadas 4 skills canônicas no repositório para edição de specs, orquestração, guarda arquitetural e estratégia de testes
- adicionado `feature-changelog.md` para histórico granular por feature
- adicionadas 4 skills técnicas por stack para Django, FastAPI, Postgres e operações assíncronas/comunicações
- adicionada governança de workflows para mudanças multi-documento, retomada e reversão lógica
- reforçada a presença de testes no guia rápido e nas regras de conclusão
- adicionado índice de skills em `tools/skills/orynth/README.md`
- adicionada revisão de governança em `governance-review.md`
- adicionadas skills `orynth-software-architect` e `orynth-test-engineer`
- workflows e guia atualizados para incluir arquitetura/segurança e testes executáveis
- registrada implementação parcial de `FEAT-AUTH-001` com backend FastAPI como autoridade de autenticação/sessão e Django como consumidor web
- registrada evolução de `FEAT-AUTH-001` com aceite obrigatório de política, edição de perfil e exclusão lógica de conta
- registrada implementação parcial de `FEAT-WALLET-001` e `FEAT-REP-001` com núcleo de usuário persistido em PostgreSQL e exposto pela FastAPI
- registrada projeção `orynth_wallet_balances` para leitura rápida de saldo sem substituir o ledger auditável
- registrada implementação parcial de `FEAT-MARKET-001` e `FEAT-MARKET-002` com mercados públicos persistidos em PostgreSQL, expostos pela FastAPI e consumidos pelo Django

## 2026-05-18

- registrada primeira fatia real do Admin Ops para mercados e taxonomia
- formalizada proteção por usuário `is_staff=true` nas rotas administrativas
- documentado cancelamento lógico de mercado e auditoria simples em `orynth_admin_events`
- atualizados gaps restantes de admin para separar CRUD básico real de fluxos operacionais ainda pendentes
- registrada regra de opções por tipo: `binary` fixo `SIM`/`NAO` em `50%`/`50%` e `multiple` com duas ou mais opções distribuídas automaticamente
- registrado filtro real por status no browse administrativo de mercados
- registrada persistência de `close_at`, `close_timezone`, `auto_close_enabled` e thumbnail de card para mercados administrativos
- registrada regra de não salvar mercado administrativo com campos operacionais mínimos ausentes
- registrado `closes_in` como rótulo automático derivado de `close_at`, removendo entrada manual do admin
- registrado fechamento manual para mercados sem daemon automático, com transição para `locked` e evento `market.lock`
- registrada resolução manual com `resolved_at`, `resolution_timezone`, payout/reputação, undo operacional e refund total de cancelamento
- registrada preservação de gráficos de consenso após resolução usando previsões `open` e `resolved`
- registrado que `close_label` é mensagem pública opcional e que percentuais ficam em `orynth_market_options.probability_exact`
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
- atualizado mapa de integração para refletir JSON runtime de manutenção, `orynth_site_config`, SMTP via ambiente e resumo operacional centralizado na FastAPI
- registrada `MarketLifecycleEngine` como ponto central do ciclo operacional de mercado no backend
- registrado `GET /admin/markets/{slug}/resolution-audit` como contrato staff read-only para auditoria de resolução
- registrado que Admin Ops mostra ação “Auditoria” em mercados resolvidos, com paginação de 10 participantes e legenda de ledger
- registrada rodada QA hard com 100 usuários simulados em `docs/research/qa-simulacao-hard-100-usuarios-20260520.md`
