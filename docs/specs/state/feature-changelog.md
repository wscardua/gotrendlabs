# Feature Changelog

Use este arquivo para registrar mudanças relevantes por feature, com foco em impacto técnico e rastreabilidade para a IA.

## Modelo de entrada

```md
## FEAT-XXX

### YYYY-MM-DD - vX.Y
- mudança principal
- contratos afetados
- status de implementação resultante
```

## FEAT-OPSLOG-001

### 2026-05-20 - v0.2
- Admin Ops passou a paginar o browse de logs e preservar filtros entre páginas
- filtro de usuário passou a usar identificador pesquisável por `@handle`, nome, email ou ID, carregando usuários comuns, staff e superusers
- contratos administrativos de logs passaram a expor `user_identifier` para exibição operacional amigável
- detalhe do log remove duplicações visuais de mensagem/request e mantém usuário apenas no card principal
- spec passou a explicitar cobertura de logs técnicos de segurança e fronteira com `orynth_auth_events`
- status de implementação: `parcial`

### 2026-05-20 - v0.1
- criada spec inicial para logs técnicos de troubleshooting
- adicionada persistência em `orynth_system_logs` com retenção, redaction e contexto JSON
- FastAPI passou a expor contratos staff para listagem e detalhe de logs
- Django Admin Ops passou a consultar logs técnicos com filtros e tela de detalhe
- status de implementação: `parcial`

## FEAT-AUTH-001

### 2026-05-19 - v0.8
- detalhe administrativo de usuário passou a exibir badges adquiridas sem recalcular elegibilidade na UI
- formulário de ajuste manual de wallet passou a exigir seleção explícita de direção, sem opção pré-selecionada
- navegação administrativa foi ordenada como Dashboard, Usuários, Categorias, Badge, Mercado, Resolução e Filas
- status de implementação: `parcial`

### 2026-05-19 - v0.7
- Admin Ops passou a ter gestão de usuários com listagem, busca, filtros por status/papel e detalhe operacional amplo
- FastAPI passou a expor contratos staff para detalhe de usuário, desativação/reativação, revogação de sessões e ajuste manual de wallet
- ações administrativas de usuário registram eventos `user.*` em `orynth_admin_events` e bloqueiam operações perigosas sobre a própria conta do operador
- status de implementação: `parcial`

### 2026-05-19 - v0.6
- login e cadastro passaram a exibir navegação pública compacta para mercados, badges e ranking
- login e cadastro passaram a exibir retorno compacto `← Feed` no primeiro painel de conteúdo, seguindo o padrão das páginas públicas fora da home
- cadastro passou a expor política de uso em modal, mantendo link para página pública completa `/use-policy/`
- painel de cadastro passou a apresentar prévia de onboarding com ticket de mercado, badges bloqueadas e confiança/OC sem dinheiro real
- status de implementação: `parcial`

### 2026-05-19 - v0.5
- perfil autenticado passou a persistir e editar `birth_date` e `sex` opcionais em `orynth_user_profiles`
- `GET/PATCH /users/me` expõe e atualiza dados privados do perfil; perfil público não expõe email, data de nascimento, sexo nem metadados privados
- Django mantém edição básica inline na própria tela `/profile/`, com reputação em cards e exclusão lógica no painel lateral
- status de implementação: `parcial`

### 2026-05-19 - v0.4
- cadastro passou a aceitar `recaptcha_token` e validar reCAPTCHA v2 no servidor quando configurado
- Django renderiza widget v2 no formulário de cadastro usando `RECAPTCHA_SITE_KEY`
- configuração por ambiente adicionada via `RECAPTCHA_ENABLED`, `RECAPTCHA_SITE_KEY` e `RECAPTCHA_SECRET_KEY`
- status de implementação: `parcial`

### 2026-05-17 - v0.3
- cadastro exige aceite da política de uso e persiste versão/data do aceite
- perfil autenticado permite alterar nome, email, idioma, bio e categoria forte via FastAPI
- adicionada exclusão lógica de conta com `account_status`, `is_active=false`, revogação de sessões e preservação física dos dados
- respostas autenticadas expõem data de criação, último login e status da conta
- status de implementação: `parcial`

### 2026-05-17 - v0.2
- criada camada `backend-api` FastAPI para `POST /auth/register`, `POST /auth/login`, `GET /auth/session`, `POST /auth/logout` e placeholder de login social
- persistência em PostgreSQL com `orynth_users`, `orynth_auth_sessions`, `orynth_external_identities` e `orynth_auth_events`
- Django deixou de criar/login usuário diretamente e passou a consumir o contrato da API, mantendo apenas token/contexto na sessão web
- testes adicionados para contrato FastAPI de sessão e para fluxo web Django via API
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `i18n-content.md`, `domain-events.md`
- status de implementação: `nao_iniciada`

## FEAT-MARKET-001

### 2026-05-19 - v0.17
- mercados passaram a persistir `view_count` e `share_count` como contadores operacionais de popularidade sem deduplicação
- contrato público/admin expõe os contadores, e `view_count` passa a guiar a seleção pública de destaque da home e do ticket de cadastro
- Admin Ops lista popularidade por mercado em `Mercados ativos e rascunhos`, com indicadores compactos e ordenação por mais visualizados ou mais compartilhados
- status de implementação: `parcial`

### 2026-05-19 - v0.16
- ticket de onboarding do cadastro passou a usar o mercado publicado não cancelado com maior `view_count`, excluindo `draft` e `canceled`
- quando houver empate ou ausência de visualizações, o ticket de onboarding usa o mercado mais recente por `created_at`
- prévia reutiliza `sparkline_series`, opções e dados serializados do domínio, com fallback local quando a API está indisponível
- status de implementação: `parcial`

### 2026-05-19 - v0.15
- feed público passou a expor recorte rápido `Resolvidos`, filtrando client-side cards já renderizados com `status=resolved`
- hero do feed passou a mostrar `previsões totais` calculadas a partir de previsões persistidas reais, sem janela mensal
- páginas públicas fora da home passaram a usar retorno compacto `← Feed` dentro do primeiro painel, alinhado ao rótulo inicial da tela
- Admin Ops passou a usar apenas a navegação principal no topo, com link de Resolução incluído e sem menu secundário duplicado
- status de implementação: `parcial`

### 2026-05-19 - v0.14
- cards de mercado passaram a usar fallback visual de thumbnail quando `image_url` e `thumb` estão vazios, derivando iniciais de categoria/subcategoria/título
- fallback de thumbnail também é aplicado aos cards de compartilhamento social e imagens Open Graph de mercado/resultado
- status de implementação: `parcial`

### 2026-05-18 - v0.13
- feed público passou a ter ordenações rápidas client-side por tendência, encerramento, volume, novidade e favoritos editoriais
- cards de mercado passaram a exibir contador compacto de curtidas derivado de comentários visíveis
- contrato/renderização do feed usa `is_featured`, `market_like_count`, `view_count`, `created_at` e `close_at` para destaque e ordenação visual
- destaque principal do feed prioriza os mercados não cancelados mais visualizados, incluindo resolvidos quando liderarem por popularidade, com mercado mais novo como desempate
- status de implementação: `parcial`

### 2026-05-18 - v0.12
- listagem administrativa "Mercados ativos e rascunhos" removeu o CTA `Ver público`, mantendo apenas `Editar/visualizar`
- acesso à página pública permanece disponível dentro do editor de mercado
- status de implementação: `parcial`

### 2026-05-18 - v0.11
- página inicial/feed público padrão deixou de renderizar mercados cancelados
- endpoint público `GET /markets` sem filtro explícito passou a excluir `draft` e `canceled`
- status de implementação: `parcial`

### 2026-05-18 - v0.10
- browse administrativo de mercados passou a usar fallback local em Postgres quando a FastAPI administrativa retorna erro transitório
- documentado que mudanças de schema com SQL direto exigem reinício do processo FastAPI em ambientes long-running
- status de implementação: `parcial`

### 2026-05-18 - v0.9
- edição administrativa de mercado passou a sincronizar opções sem apagar/recriar opções que já possuem previsões vinculadas
- tentativa de remover opção com previsão vinculada retorna erro de domínio em vez de erro interno
- cliente Django passou a exibir erro de API genérico como falha de requisição, não como falha de autenticação
- status de implementação: `parcial`

### 2026-05-18 - v0.8
- cards do feed passaram a exibir mini gráficos de evolução do consenso com uma linha por opção
- CTA de mercados abertos passou a ser `Prever` também para múltipla escolha
- fallback do Django para feed/categorias passou a hidratar séries visuais e IDs de opção a partir do Postgres local quando a API entrega payload antigo
- status de implementação: `parcial`

### 2026-05-18 - v0.7
- Admin Ops de taxonomia passou a operar em formato de browse objetivo, com filtros por uso/bloqueio e política lateral
- categorias e subcategorias ganharam bloqueio lógico persistido (`is_blocked`, `blocked_at`, `blocked_reason`) em vez de exclusão física
- FastAPI expõe ações staff para bloquear/desbloquear categoria e subcategoria, registrando eventos administrativos
- criação/edição administrativa de mercado rejeita categoria ou subcategoria bloqueada
- status de implementação: `parcial`

### 2026-05-18 - v0.6
- Admin Ops passou a marcar campos obrigatórios e exibir feedback de sucesso ao salvar/publicar/cancelar/fechar mercado
- adicionada ação manual de fechamento para mercados `open`/`scheduled` com `auto_close_enabled=false`
- fechamento manual muda status para `locked` e registra evento `market.lock`
- editor administrativo passou a carregar categoria/subcategoria da taxonomia persistida, mantendo subcategoria vinculada à categoria selecionada
- categoria/subcategoria agora iniciam com opção “Selecione”, sem pré-seleção automática em novo mercado
- ajustado contraste de dark mode no editor de opções e no controle de fechamento automático
- status de implementação: `parcial`

### 2026-05-18 - v0.5
- editor administrativo passou a exigir campos operacionais mínimos antes de salvar mercado
- adicionados `close_at`, `close_timezone`, `auto_close_enabled` e `image_url` ao contrato persistido de mercado
- prévia do card no Admin Ops passou a atualizar conforme preenchimento e upload de thumbnail
- status canônico de mercado passou a ser exibido sem usar rótulos editoriais como status
- rótulo curto de prazo passou a ser derivado automaticamente de `close_at`
- status de implementação: `parcial`

### 2026-05-18 - v0.4
- browse administrativo de mercados passou a filtrar por status via `GET /admin/markets?status=...`
- chips do Django Admin Ops agora refletem filtro ativo e contadores globais por status
- status de implementação: `parcial`

### 2026-05-18 - v0.3
- adicionada primeira fatia real do Admin Ops para mercados e taxonomia
- FastAPI expõe endpoints staff para listar, criar, editar, publicar e cancelar mercados
- Django Admin Ops passou a consumir a API administrativa com bloqueio para guest e usuário comum
- criada auditoria simples em `orynth_admin_events`
- status de implementação: `parcial`

### 2026-05-17 - v0.2
- criadas tabelas PostgreSQL para categorias, subcategorias, mercados e opções
- adicionado seed inicial idempotente a partir de `data/fixtures/domain.json`
- FastAPI passou a expor `GET /markets` com filtros públicos básicos
- Django passou a consumir a FastAPI para o feed, preservando fixture como fallback
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `market-lifecycle.md`, `i18n-content.md`
- status de implementação: `nao_iniciada`

## FEAT-MARKET-002

### 2026-05-19 - v0.8
- abertura do detalhe público incrementa `view_count` do mercado com fallback local quando a API está indisponível
- controles de compartilhamento de pergunta/resultado incrementam `share_count` via rota leve de tracking, sem bloquear navegação/cópia
- editor administrativo exibe visualizações e compartilhamentos como campos read-only de popularidade operacional
- status de implementação: `parcial`

### 2026-05-19 - v0.7
- rotas web de compartilhamento de pergunta e resultado passaram a expor links por rede, metadados Open Graph/Twitter e imagem social dinâmica
- card social de mercado inclui contexto curto da plataforma e CTA de aquisição: "Dispute previsões, construa reputação e ganhe destaque."
- card social de resultado prioriza pergunta e exibe o resultado imediatamente abaixo como desfecho
- origem pública de compartilhamento pode ser configurada para crawlers sociais; host local exibe aviso de preview não rastreável
- status de implementação: `parcial`

### 2026-05-18 - v0.6
- detalhe do mercado passou a exibir gráfico de evolução do consenso com uma linha por opção
- gráfico de evolução passou a preservar histórico após resolução, considerando previsões `open` e `resolved` e excluindo `canceled`
- mercado resolvido passou a exibir data/hora/timezone da resolução e mensagem personalizada no ticket para usuário que acertou ou errou
- visitantes veem opções e consenso sem controle de stake; usuários com previsão existente veem aviso destacado e controles desabilitados
- fallback local do Django hidrata `option.id`, `sparkline_path` e `sparkline_series` quando a FastAPI está indisponível ou desatualizada
- status de implementação: `parcial`

### 2026-05-18 - v0.5
- documentado que percentuais iniciais das opções ficam persistidos em `orynth_market_options.probability_exact`
- status de implementação: `parcial`

### 2026-05-18 - v0.4
- formalizada regra de opções por tipo de mercado no admin
- `binary` persiste opções canônicas `SIM`/`NAO` com `50%`/`50%`
- `multiple` aceita duas ou mais opções sem limite máximo fixo e distribui percentuais automaticamente para somar `100%`
- status de implementação: `parcial`

### 2026-05-18 - v0.3
- dados-base do detalhe podem ser mantidos pelo Admin Ops real
- publicação administrativa preserva contrato público de detalhe em `GET /markets/{slug}`
- cancelamento administrativo preserva histórico sem exclusão física
- status de implementação: `parcial`

### 2026-05-17 - v0.2
- detalhe de mercado passou a ser persistido e serializado pela FastAPI em `GET /markets/{slug}`
- contrato mantém opções, probabilidade snapshot, categoria, subcategoria e critérios de resolução compatíveis com os templates
- Django passou a consumir a FastAPI no detalhe e nas páginas de compartilhamento, preservando fallback fixture
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `market-lifecycle.md`, `prediction-payloads.md`, `i18n-content.md`
- status de implementação: `nao_iniciada`

## FEAT-PRED-001

### 2026-05-19 - v0.5
- prévia de retorno da previsão passou a ter contrato FastAPI sem efeito colateral
- fallback local mutável de criação de previsão no Django foi removido; falha da API não cria previsão nem altera wallet/ledger
- status de implementação: `parcial`

### 2026-05-18 - v0.4
- adicionados campos decimais para probabilidade real em mercado, opções e probabilidade de entrada da previsão
- colunas inteiras redundantes foram removidas; `probability` permanece apenas como campo derivado no contrato de leitura
- mercados de múltipla escolha distribuem `100 / quantidade_de_opções` igualmente, sem sobra artificial para a primeira opção
- `potential_payout` passa a usar a probabilidade decimal vigente antes da previsão
- status de implementação: `parcial`

### 2026-05-18 - v0.3
- séries visuais de consenso passaram a ser derivadas de `orynth_predictions` ordenadas por criação
- mercados binários e múltipla escolha expõem evolução por opção para cards e detalhe
- adicionado fallback local de confirmação/persistência quando a FastAPI separada está indisponível no ambiente de desenvolvimento
- testes cobrem confirmação local, payload antigo sem IDs/séries e hidratação visual dos cards
- status de implementação: `parcial`

### 2026-05-18 - v0.2
- adicionada primeira mutação real de previsão em `POST /markets/{slug}/predict`
- decisão de MVP: permitir apenas uma previsão por usuário em cada mercado
- stake positivo sem teto fixo é limitado pelo saldo disponível e gera `prediction_stake_lock`
- probabilidades do mercado são recalculadas com peso sintético base e peso `reputacao * stake`
- Django passou a confirmar previsão via FastAPI e exibir sucesso/erros de domínio
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `prediction-payloads.md`, `wallet-ledger.md`, `market-lifecycle.md`
- status de implementação: `nao_iniciada`

## FEAT-RES-001

### 2026-05-19 - v0.3
- cancelamento administrativo passou a validar que não restam previsões `open` após aplicar refund total
- adicionada reconciliação operacional idempotente para mercados já `canceled` que ainda possuam previsões `open`
- reconciliação registra `market.cancel_reconcile` e preserva reputação
- adicionada regressão para estado órfão `canceled` + previsão `open`, cobrindo dry-run, refund, saldo e idempotência
- contratos relacionados: `market-lifecycle.md`, `wallet-ledger.md`, `domain-events.md`
- status de implementação: `parcial`

### 2026-05-18 - v0.2
- adicionada resolução manual por `POST /admin/markets/{slug}/resolve`
- resolução registra opção vencedora, evidência, operador, payout, perda e delta de reputação pela fórmula MVP
- resolução passou a registrar data/hora efetiva (`resolved_at`) e timezone controlado (`resolution_timezone`), com campos editáveis no Admin Ops
- cancelamento administrativo passou a aplicar refund total dos stakes bloqueados
- mercados resolvidos passaram a permanecer no browse de resolução com ação excepcional de desfazer resolução
- browse de resolução passou a exibir data/hora/timezone e ordenar por resolução recente, antiga ou pendências
- desfazer resolução retorna o mercado para `locked`, estorna payout líquido, rebloqueia stakes e recalcula reputação
- mercado resolvido passou a ficar somente leitura no editor administrativo
- Admin Ops passou a listar mercados `locked` e publicar resolução real
- contratos relacionados: `market-lifecycle.md`, `wallet-ledger.md`, `reputation-ranking.md`, `domain-events.md`
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `market-lifecycle.md`, `wallet-ledger.md`, `reputation-ranking.md`, `domain-events.md`
- status de implementação: `nao_iniciada`

## FEAT-REP-001

### 2026-05-19 - v0.8
- ranking web passou a consumir `GET /rankings` como fonte única
- fallback local de cálculo de ranking/reputação no Django foi removido; falha da API exibe erro/estado vazio
- status de implementação: `parcial`

### 2026-05-19 - v0.7
- compartilhamento de badge passou a gerar card social com metadados Open Graph/Twitter e imagem dinâmica
- link público de conquista usa token opaco para permitir preview social sem expor id, email ou handle na URL
- botão de cópia copia apenas o link canônico; links por rede mantêm texto contextual quando suportado
- cards de badge no perfil passaram a usar o mesmo padrão visual do catálogo e apontar para `share-badge`
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `parcial`

### 2026-05-19 - v0.6
- catálogo público de badges passou a exibir ação de compartilhar apenas para usuários autenticados em badges já conquistadas
- adicionada rota web autenticada `/share/badge/{code}/`, validando a conquista antes de renderizar a página de compartilhamento
- compartilhamento MVP usa ação nativa do navegador quando disponível e fallback de cópia de link/texto
- reforçado que compartilhar badge não altera reputação, ranking, ledger, wallet nem concessão de badges
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `parcial`

### 2026-05-19 - v0.5
- badges passaram de registros hardcoded por usuário para catálogo administrável com definição, regra e conquista separadas
- adicionados contratos públicos `GET /badges` e `GET /users/me/badges` com estado pessoal quando autenticado
- adicionados contratos staff para listar, criar, editar e desativar badges no Admin Ops
- concessão automática usa `rule_type` controlado no backend e é idempotente por usuário/badge
- regras temáticas de badge passaram a selecionar categoria/subcategoria da taxonomia dinâmica e aplicar recorte em previsões, acertos, comentários e sugestões aprovadas
- contrato administrativo de badges passou a distinguir campos obrigatórios de opcionais e exigir marcação visual no formulário
- browse administrativo de badges passou a exibir categoria/subcategoria da regra, usando `Todas / Todas` para regras globais
- formulário administrativo de badges passou a exibir prévia do card público, incluindo imagem local antes de salvar
- badges passaram a aceitar imagem padrão/tema claro e imagem opcional para tema escuro, com fallback para a imagem padrão quando a escura não existir
- concessão de badges passou a ser centralizada na `BadgeAwardEngine`, com eventos de domínio para cadastro, comentário, sugestão, feedback e resolução de mercado
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `parcial`

### 2026-05-19 - v0.4
- ranking público passou a aceitar filtros de categoria/subcategoria e expor metadados de taxonomia
- ranking temático é recalculado em leitura com previsões resolvidas do recorte usando a fórmula MVP
- tela de ranking passou a identificar usuários por handle e remover filtros decorativos sem contrato
- quadro "Seu recorte" passou a depender de sessão/dados reais, sem percentuais fictícios para visitantes
- usuários `is_staff` e `is_superuser` foram excluídos do ranking público na API e no fallback Django
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `parcial`

### 2026-05-18 - v0.3
- resolução de mercado passou a atualizar reputação com `K=10` usando `probability_at_entry`
- `accuracy_indicator`, `resolved_predictions_count` e `streak` passam a refletir previsões resolvidas
- cancelamento/refund não altera reputação
- status de implementação: `parcial`

### 2026-05-17 - v0.2
- criada reputação base provisória por usuário com score inicial `100`
- criado ranking público simples ordenado por reputação e data de criação
- criadas badges estruturadas com `founding_member` concedida no cadastro e demais badges bloqueadas
- Django passou a renderizar perfil/ranking a partir da FastAPI quando disponível
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `reputation-ranking.md`
- status de implementação: `nao_iniciada`

## FEAT-WALLET-001

### 2026-05-19 - v0.7
- ajuste manual de wallet por staff passou a usar `manual_adjustment`, `admin_user_adjustment`, operador e nota obrigatória
- direção do ajuste manual deve ser escolhida explicitamente no Admin Ops, sem seleção padrão
- débito manual acima do saldo disponível é rejeitado pelo backend
- status de implementação: `parcial`

### 2026-05-19 - v0.6
- refund de cancelamento passou a ser idempotente por previsão enquanto não houver novo lock/relock posterior
- reconciliação operacional de mercado cancelado cria `prediction_refund` ausente e atualiza `orynth_wallet_balances` na mesma transação
- preservado caso de resolução desfeita seguida de cancelamento final, criando novo release após `prediction_resolution_relock`
- status de implementação: `parcial`

### 2026-05-18 - v0.5
- resolução vencedora libera stake por `prediction_refund` e credita ganho líquido por `prediction_payout`
- resolução perdedora baixa stake bloqueado por `prediction_loss` com `direction="settle"`
- cancelamento com previsão aberta devolve 100% do stake bloqueado por `prediction_refund`
- status de implementação: `parcial`

### 2026-05-18 - v0.4
- ledger passou a reconhecer recompensas operacionais de feedback e sugestão de mercado
- `reward_feedback` e `reward_suggestion` atualizam extrato e projeção `orynth_wallet_balances`
- aprovações de crédito em filas operacionais bloqueiam duplicidade por item
- recompensas operacionais não concedem reputação
- status de implementação: `parcial`

### 2026-05-17 - v0.3
- adicionada projeção operacional `orynth_wallet_balances` para leitura rápida de saldo
- mantido `orynth_wallet_ledger` como fonte auditável e regra de reconciliação
- FastAPI passou a ler saldo pela projeção e a centralizar mutações no helper ledger + balance
- migration inclui backfill de saldos existentes a partir do ledger
- status de implementação: `parcial`

### 2026-05-17 - v0.2
- criado ledger PostgreSQL `orynth_wallet_ledger` como fonte do saldo do usuário
- cadastro passou a registrar `grant_initial` de `2000 OC` na mesma transação do usuário
- adicionados endpoints FastAPI de wallet e extrato autenticado
- Django passou a renderizar carteira e extrato a partir da FastAPI
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `wallet-ledger.md`
- status de implementação: `nao_iniciada`

## FEAT-COMMENT-001

### 2026-05-18 - v0.3
- UI pública de comentários passou a identificar autores por `@handle`
- ações de `like` e `dislike` passaram a usar botões iconizados com estado ativo
- convite de login para visitante no bloco de comentários foi redesenhado como callout
- documentação de arquitetura/contratos passou a registrar endpoints, tabelas, moderação e fallback local
- status de implementação: `parcial`

### 2026-05-18 - v0.2
- adicionada persistência de comentários e reações em mercados
- FastAPI passou a expor criação/listagem pública, `like`/`dislike` autenticado e moderação staff por `visible`/`hidden`
- Django passou a renderizar formulário, lista e ações de reação no detalhe do mercado
- Admin Ops passou a listar e moderar comentários com evento `comment.hide`/`comment.restore`
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `domain-events.md`, `i18n-content.md`
- status de implementação: `nao_iniciada`

## FEAT-SUGGEST-001

### 2026-05-19 - v0.5
- Admin Ops deixou de executar fallbacks locais mutáveis para filas, comentários, conversão de sugestão e créditos operacionais
- indisponibilidade da FastAPI passa a ser exibida como erro operacional sem alterar domínio diretamente pelo Django
- status de implementação: `parcial`

### 2026-05-19 - v0.4
- sugestões de mercado e feedback passaram a aceitar `recaptcha_token`
- FastAPI exige reCAPTCHA válido para envios de visitantes quando configurado
- Django renderiza widget v2 apenas para visitantes e preserva bypass para usuários autenticados
- fallback local de desenvolvimento valida reCAPTCHA antes de persistir envio guest
- status de implementação: `parcial`

### 2026-05-18 - v0.3
- formulários públicos passaram a aceitar envio autenticado ou visitante identificado por nome e email
- confirmação de envio passou a usar popup na home após redirecionamento
- fila operacional passou a exibir Mercado e Feedback com data de criação, tipo do item e ordenação por data
- removidas colunas operacionais não usadas nesta fatia, como aging e responsável
- tela de revisão passou a exibir status persistido, recompensa, contexto completo e ações específicas por tipo
- conversão em rascunho ficou restrita a sugestão de mercado e bloqueada após conversão
- créditos podem ser aprovados para feedback ou sugestão apenas quando houver usuário cadastrado, com bloqueio de reenvio
- status de implementação: `parcial`

### 2026-05-18 - v0.2
- adicionada persistência para sugestões de mercado e feedbacks operacionais
- FastAPI passou a expor submissão pública/autenticada e fila administrativa staff
- Admin Ops passou a listar itens reais, revisar, converter sugestão em rascunho e recompensar feedback via ledger
- feedback recompensável entra como fatia operacional mínima; event bus assíncrono segue pendente
- status de implementação: `parcial`

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `domain-events.md`, `i18n-content.md`
- status de implementação: `nao_iniciada`

## FEAT-NOTIFY-001

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `domain-events.md`, `i18n-content.md`
- status de implementação: `nao_iniciada`

## FEAT-I18N-001

### 2026-05-17 - v0.1
- spec inicial criada
- contratos relacionados: `i18n-content.md`
- status de implementação: `nao_iniciada`

## Sistema documental e skills

### 2026-05-17 - v0.3
- adicionada skill `orynth-workflow-governor`
- adicionados templates em `docs/specs/workflows/`
- adicionados `workflow-runs.md` e `workflow-checklists.md`
- guia atualizado com fluxo de testes e governança de processo

### 2026-05-17 - v0.4
- adicionada skill `orynth-software-architect` para arquitetura, segurança e desenho técnico
- adicionada skill `orynth-test-engineer` para testes concretos de backend, frontend, integração e regressão
- workflows atualizados para exigir arquitetura/segurança em mudanças relevantes e testes executáveis quando houver código
