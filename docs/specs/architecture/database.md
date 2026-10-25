# Database

## Responsabilidades

- Persistir usuários, perfis, mercados, opções, previsões, ledger da wallet, comentários, notificações in-app, sugestões, decisões de moderação e histórico operacional.
- Persistir definicoes assinadas, compromissos de previsao, folhas/provas Merkle, Seals, eventos globais do ledger e chaves publicas historicas em `integrity_signing_keys`.
- Garantir integridade relacional e rastreabilidade temporal.
- `gotrendlabs_users` deve pertencer a `gotrendlabs_auth_owner` sem login; migrations usam credencial operacional separada, Django runtime recebe UPDATE somente das colunas nao sensiveis e FastAPI possui UPDATE de `password`. Um trigger pertencente ao owner impede que insercoes Django definam senha utilizavel.
- A credencial da role FastAPI deve ser injetada somente no processo FastAPI; Django web e daemon usam a role Django. O guard de banco e insuficiente se o ambiente compartilhado entregar a esses processos uma segunda credencial capaz de escrever `password`.
- Suportar consultas transacionais e relatórios administrativos.

## Diretrizes

- Modelos críticos devem preservar histórico quando o produto exigir auditabilidade.
- Tabelas de integridade sao append-only, protegidas contra UPDATE/DELETE, sem cascades destrutivos e fora de purge/retenção comum.
- O estado alvo de producao separa a role proprietaria/migradora das roles de runtime. FastAPI e daemon recebem apenas `SELECT`, `INSERT` e uso das sequences estritamente necessarias; Django recebe somente as leituras/contratos requeridos. Nenhuma role de aplicacao deve ser proprietaria das tabelas append-only nem possuir `UPDATE`, `DELETE` ou `TRUNCATE` nelas.
- A defesa append-only deve ser uniforme: triggers contra `UPDATE`, `DELETE` e `TRUNCATE`, grants minimos e ausencia de ownership runtime sao controles complementares, validados com as roles reais de producao apos cada migration/deploy.
- `integrity_signing_keys` armazena apenas material publico DER, algoritmo e fingerprint por `key_id`; material privado permanece fora do PostgreSQL e, em producao, exclusivamente no AWS KMS.
- `gotrendlabs_integrity_alerts` e uma fila operacional mutavel, separada das provas append-only. Deduplica por escopo/tipo de divergencia, preserva primeira e ultima deteccao, ocorrencias e revisao administrativa; nao participa da raiz Merkle nem da cadeia assinada.
- Wallet deve usar razão de transações (`ledger`) em vez de depender apenas de saldo derivado.
- Resolução de mercado deve registrar origem, operador, evidência, data efetiva e timezone usado para apresentação/auditoria.
- Sempre que possível, usar identificadores estáveis independentes de textos traduzidos.
- Definicoes assinadas guardam IDs estaveis de categoria, subcategoria e evento como campos protegidos e os nomes como snapshot editorial. Renomear o cadastro taxonomico nao altera a prova; trocar a associacao do mercado altera campo protegido.
- O corte de dados pre-producao sem prova e executado por comando operacional em `dry-run` por padrao, nunca por migration destrutiva automatica. O comando recusa mercados com definicao ou eventos assinados e reconcilia projecoes de wallet depois de remover referencias de previsoes eliminadas.
- Alertas operacionais de integridade vinculados a mercados elegiveis ao corte sao removidos antes da FK `PROTECT`; por serem fila mutavel, nao constituem prova e nao autorizam remover qualquer registro append-only.
- A limpeza de badges do corte usa causalidade exata no `reason_snapshot` (`market_resolved:{market_id}`) e remove somente a notificacao idempotente correspondente ao badge efetivamente removido; interacao ou autoria em um mercado eliminado nao autoriza apagar historico de badge nao relacionado.
- Os acessos de integridade possuem indices para sequencia/hash do ledger, FKs de mercado/prova, unicidade de definicao/Seal/compromisso, checkpoint e fila por `(market_id, status)`. A leitura publica usa lookups indexados de head/limite/checkpoint; somente a auditoria integral periodica preserva custo `O(E)` fora do request path.
- `integrity_ledger_checkpoints` materializa atestacoes globais assinadas e append-only, com indice por sequencia final e auditoria integral recente. Checkpoint nao substitui eventos nem permite UPDATE/DELETE; a leitura publica valida assinatura e head em poucos lookups, enquanto a auditoria integral periodica preserva verificacao independente.
- Categorias, subcategorias e eventos vinculados a mercados devem usar bloqueio lógico (`is_blocked`, motivo e data) em vez de exclusão física operacional; eventos sem mercados vinculados podem ser excluídos para limpeza de cadastros criados por engano.
- Saneamento excepcional de taxonomia duplicada sem mercados na origem deve usar plano explícito, backup e auditoria transacional; preservar IDs de mercados e mover somente eventos sem uso para pai equivalente. Procedimento: `../operations/taxonomy-duplicates-20261010.md`.
- Eventos ficam em `gotrendlabs_market_events`, pertencem a uma subcategoria e formam a terceira camada da taxonomia `categoria -> subcategoria -> evento`.
- `gotrendlabs_market_categories.notice`, `gotrendlabs_market_subcategories.notice` e `gotrendlabs_market_events.notice` guardam avisos opcionais, vazios por padrão, para exibição contextual no detalhe/ticket de mercados sensíveis vinculados.
- `gotrendlabs_markets.event_id` referencia `gotrendlabs_market_events`; mercados migrados sem evento explícito devem apontar para o evento ativo `Geral` da subcategoria.
- Mercados existentes devem manter vínculo com taxonomia bloqueada para preservar histórico e auditoria.
- Probabilidades de opção devem preservar precisão decimal em `gotrendlabs_market_options.probability_exact`; percentuais de mercado (`primary_probability*`/`secondary_probability*`) são derivados das opções ranqueadas por probabilidade na serialização e não são persistidos em `gotrendlabs_markets`.
- Métricas operacionais simples de popularidade de mercado ficam denormalizadas em `gotrendlabs_markets.view_count` e `gotrendlabs_markets.share_count` para leitura rápida no Admin Ops; nesta etapa cada evento incrementa o contador sem deduplicação.
- Comentários de mercado são preservados em `gotrendlabs_market_comments` com status `visible`/`hidden`, nota de moderação, moderador e timestamps.
- Reações de comentário ficam em `gotrendlabs_comment_reactions`, com uma reação ativa por usuário/comentário e valores `like` ou `dislike`.
- Ocultação de comentário é lógica; não há exclusão física operacional nesta fatia.
- Gestão administrativa de usuários reutiliza `gotrendlabs_users`, `gotrendlabs_user_profiles`, `gotrendlabs_auth_sessions`, `gotrendlabs_auth_events`, `gotrendlabs_wallet_ledger`, `gotrendlabs_wallet_balances` e `gotrendlabs_user_badge_awards` para suporte sem criar nova tabela.
- Ações administrativas de usuário devem registrar `user.deactivate`, `user.reactivate`, `user.sessions_revoke` ou `user.wallet_adjust` em `gotrendlabs_admin_events`.
- Ajuste manual de wallet deve ser persistido em `gotrendlabs_wallet_ledger` como `manual_adjustment` e atualizar `gotrendlabs_wallet_balances` na mesma transação.
- Logs técnicos de troubleshooting ficam em `gotrendlabs_system_logs`, com `expires_at`, purge por `created_at` conforme retenção configurável, índices de consulta operacional e contexto JSON redigido/truncado.
- Parâmetros operacionais persistentes ficam em `gotrendlabs_site_config`, uma configuração singleton expansível para novos ajustes do site; nesta fatia inclui SMTP não sensível e retenção de logs/auditoria IA, com host, porta, usuário, TLS/SSL, timeout, remetente, reply-to, operador e timestamp de alteração.
- Senhas, API keys e segredos SMTP não são persistidos no banco.
- Configuração operacional de agentes IA fica em `gotrendlabs_site_config`; o segredo do provedor LLM permanece fora do banco (`OPENAI_API_KEY` para OpenAI ou `AWS_BEARER_TOKEN_BEDROCK` para Bedrock).
- `gotrendlabs_ai_agents` liga um agente oficial a um usuário `is_bot=true` e guarda persona/estilo editáveis sem substituir o template seguro de código.
- `gotrendlabs_ai_agent_actions` guarda auditoria de ações IA com status, motivo, payload resumido, referência a mercado/comentário/previsão e hash/versão do prompt; o purge operacional remove ações mais antigas que `gotrendlabs_site_config.ai_audit_retention_days`.
- Métricas distinguem recortes humanos e bots para operação; a projeção pública `participants` representa o total de contas distintas humanas e bot com previsões abertas. O rótulo de volume mantém o recorte humano.
- Notificações in-app ficam em `gotrendlabs_user_notifications`, com destinatário obrigatório, ator/mercado/comentário opcionais, `event_type`, `source_key`, título, corpo, `metadata`, estado de leitura e constraint única por `(recipient_id, source_key)`.
- `source_key` deve representar a origem idempotente do evento por destinatário, permitindo uma notificação por usuário afetado sem duplicar ações repetidas.

## Não Responsabilidades

- Aplicar regra de negócio isoladamente.
- Calcular reputação ou probabilidades fora do backend.

## Exclusão física pré-publicação (2026-10-11)

Exceção restrita para revisões editoriais de draft preparation/in_review: função public.delete_prepublication_editorial(bigint,integer), SECURITY DEFINER, objetos qualificados, search_path pg_catalog, EXECUTE revogado de PUBLIC e concedido a gotrendlabs_fastapi. Revalida locks/estado/revisão e ausência de previsões/provas antes do DELETE. A função também remove os alertas mutáveis vinculados ao rascunho elegível; não desvincula alertas como globais nem remove provas. Nenhum grant geral DELETE/UPDATE de revisões é ampliado. Função e dependências são operadas na transação FastAPI auditada. [ADR-0015](../decisions/ADR-0015-prepublication-market-deletion.md).

ThumbnailJob admite mercado nulo apenas para tentativa de mercado expired/market_deleted, snapshot vazio e ausência de badge/editor. Essa exceção preserva as cotas históricas de geração sem reter mercado ou conteúdo editorial. Limpeza de mídia gerada permanece com o worker/prune existente.

## Agenda de resolução — 2026-10-17

Contrato e critérios: [market-resolution-agenda](../features/market-resolution-agenda.md); integridade: [ADR-0016](../decisions/ADR-0016-resolution-agenda.md). `expected_resolution_at` consolida `resolution_date`; sem duplicação ou fallback. Implementação e validação local acompanhadas em WFLOW-20261017-STRUCTURED-RESOLUTION-AGENDA.
# Histórico analítico MCP (branch local 2026-10-24)

`admin_ops.0027` adiciona checkpoints por dia local, contagens aditivas por evento/mercado/plataforma/ator, presença diária de atores para DISTINCT entre dias, funil derivado de eventos por sessão/mercado e snapshot de taxonomia na publicação. A role FastAPI recebe acesso; MCP não recebe acesso ao PostgreSQL. Checkpoint e derivados são atualizados na mesma transação com lock por dia; o expurgo só passa após validar contagem e último recebimento. Índices cobrem data e mercado/data em eventos e derivados. Fatos de previsão continuam nas tabelas de domínio. [ADR-0017](../decisions/ADR-0017-mcp-analytics-history.md).

## Recibos administrativos de resolução — 2026-10-25

`gotrendlabs_market_resolution_requests` guarda UUID único global, FK protegida/indexada para mercado, hash canônico do pedido, `seal_due_at` da ocorrência e `created_at`. Não armazena tokens nem cópia do texto editorial. UPDATE/DELETE são bloqueados por trigger; não participa do expurgo operacional. Migration markets.0037 concede SELECT/INSERT e uso da sequência à role FastAPI configurada/padrão, quando existente. Django consulta via API, nunca grava recibos. Inserção única e confirmação dos efeitos compartilham transação; conflito de chave entre mercados reverte a segunda transação inteira. Nenhuma prova ou prazo histórico é migrado.

## ACL efetiva dos recibos — 2026-10-25

Produção concede `arwd` por default ACL a novas tabelas FastAPI/Django. A migration `markets.0038_limit_resolution_request_privileges` retira UPDATE/DELETE do FastAPI e as escritas da role Django apenas em `gotrendlabs_market_resolution_requests`; mantém o trigger append-only como barreira adicional. A sequência fica com USAGE/SELECT para FastAPI, sem UPDATE. Não altera a default ACL global nem outras tabelas.
