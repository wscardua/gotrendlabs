# Integration Map

## 2026-10-10 — documento editorial único

- PR #148/Actions 38060102537 implantados: contrato MCP/API, UI, migrations e dados convertidos ativos em produção. Quatro documentos e 27 URLs preservados; smoke técnico aprovado. [Evidência](../testing/editorial-document-production-20261010.md). Piloto externo e parecer humano autenticado em PRD permanecem pendentes.
- Dot/MCP → `EditorialRecord(policy_version, policy_hash, document)` → FastAPI → PostgreSQL; Admin Ops consome o documento persistido e registra assessment com um aceite humano. `/record` e `/decision` deixam de ser contratos ativos. Migration 0004 converte registros anteriores uma vez, preservando snapshots; drafts/agendados convertidos exigem nova revisão.
- FastAPI valida `Anúncio esperado` contra `close_at` quando o horário constar no documento e exige declaração textual de pendências resolvidas antes de aprovar. Migration 0005 restaura a decisão histórica somente para mercados já publicados; drafts/agendados continuam exigindo novo parecer. Mobile não consome essas rotas.

- 2026-10-07: ajuste exclusivamente na serialização da resposta DCR (`scope` ausente omitido), PR #140 implantada/Actions 37710313470 aprovado; sem mudanças em MCP, permissões, audience, MFA, banco ou consumidores web/mobile. Smoke público DCR 201 e MCP sem token 401 aprovados; cadastro ChatGPT pendente. WFLOW-20261007-MCP-CHATGPT-DCR-001.

- 2026-10-07: WFLOW-20261007-MCP-CODEX-OAUTH-001 corrige DCR Codex (extra application_type) e issuer exato no discovery MCP; 50 testes locais/OK e CI PR/main 371 testes/OK (um skip por roles CI ausentes); implantada pela PR #138/Actions 37699380266, registro CLI real conferido em produção. Sem migrations/permissões novas; homologação humana permanece pendente.

- 2026-10-07: PR #136 + Actions 37692274600 concluídos; MCP ativo em HTTPS, grants/isolamento conferidos, snapshot anterior ao merge e domínio preservado. [Rollout](../testing/mcp-production-rollout-20261007.md). Dot/piloto autenticado externos permanecem pendentes.

- 2026-10-07: pacote de rollout/ativação/rollback MCP integrado ao fluxo de produção, PR CI e isolamento conferidos localmente. [Fechamento](../testing/mcp-closeout-20261007.md).

- 2026-10-07, follow-up review MCP: módulos e migrations/grants do percurso adicionados ao índice Git e conferidos em snapshot limpo com instalação independente e 74 testes PostgreSQL aprovados. [Evidências](../testing/mcp-branch-review-followup-20261007.md).

## Ensaio DEV atual — 2026-10-07

- Admin Ops humano → #6 resolvido; MCP SDK/OAuth → #7 submetido, aprovado na UI e fechado automaticamente. Serviço client_credentials/revogação validado. Logs existentes e auditoria criptográfica verificados; precisão e fuso dos formulários corrigidos. [Evidência](../testing/dev-catalog-rehearsal-20261007.md).

## MCP editorial — FEAT-MCP-001 (implantado, homologação externa pendente)

- Dot/outro executor → MCP HTTPS → FastAPI → PostgreSQL. MCP sem banco/ORM/segredos KMS/MFA; pesquisa e agenda permanecem externas.
- Admin Ops → FastAPI com staff ou superuser + MFA, capacidades iguais → integrações, credenciais/grants, cotas e revisão editorial.
- OAuth interativo e serviço → identidade técnica/delegação verificável → contratos editoriais restritos, ficha/revisões privadas e autoria de draft.
- MCP → ingestão técnica autenticada FastAPI → `gotrendlabs_system_logs`; mutações → `gotrendlabs_admin_events` na mesma transação. Filtros/aba atividade reutilizam registros existentes.
- Catálogo/editorial aprovados são dependências; analytics opcional indisponível não vira zero. Bots oficiais e daemon operacional não são executor do radar.
- Humano no Admin Ops → assessment FastAPI/MFA → ficha/snapshot/evento/parecer numa transação → gate de publicação. Uma ação na UI; `/record` e `/decision` anteriores removidos.
- Publicação humana de todos os mercados → MarketLifecycleEngine → lock/revisão/hash/parecer humano vigente → assinatura/abertura. Recusa 409 antes da assinatura; edição invalida aprovação; gate universal de novas publicações, com validação de fechamento antes da assinatura.
- Runtime: `apps/mcp/server.py` → delegação interna FastAPI → dez rotas editoriais restritas. Admin Ops → gestão/consentimento/parecer FastAPI; grants PostgreSQL exclusivos da API. Deploy preparado com override MCP + import Caddy e CI de PR; primeira instalação desligada. Ativação explícita pós-merge preserva workload privado 0600. Rollout produtivo executado pela PR #136; API/MCP habilitados explicitamente e dados preservados.
- Catálogo documental: `tools/list` do MCP direto usa `editorial_record.document` em validação/criação/edição e devolve o mesmo registro em consultas; `submit_draft_for_review` referencia a revisão persistida. `get_editorial_policy` vem da FastAPI e mantém política v1.2, com hashes independentes de checklist/modelo implantados pela PR #150/Actions 38090503977. O catálogo do app `MyGoTrendLabsMCP-v2` recebeu **Refresh tools** e sua validação com `document` passou; uma conversa nova ainda precisa confirmar a declaração visível ao modelo. Nenhuma mudança de mercado, grant ou agenda decorreu disso.
- Evidências: [resultados](../testing/mcp-editorial-results.md), [piloto](../../guides/mcp-editorial-pilot.md). Mobile permanece consumidor dos contratos existentes; campos novos são opcionais/aditivos.
- Fontes: [feature](../features/mcp-editorial-agents.md), [contrato](../contracts/agent-integrations.md), [ADR](../decisions/ADR-0011-mcp-editorial-integrations.md).

## Analytics proprio (`FEAT-ANALYTICS-001`)

- Browser web → `POST /analytics/events/` no Django com CSRF → `POST /analytics/events` na FastAPI com token de sessao, IP assinado opcional e catalogo validado → PostgreSQL analytics.
- Flutter → `POST /analytics/events` na FastAPI com os headers mobile existentes; tela/aba sao registradas por navegacao real, sem contar rebuild/polling.
- FastAPI → GeoLite City em arquivo local opcional; ausencia do arquivo produz geografia desconhecida.
- Produção: o arquivo GeoLite City está no volume `runtime`, o proxy usa segredo compartilhado Django/FastAPI e a rede Caddy confiável está configurada; a atualização da base é manual. A PR `#133` ativou o contrato e as migrations `admin_ops.0020/0021`.
- Importador GeoLite backend → arquivo no volume runtime + tabela de execuções; ingestão FastAPI → status da última remessa + eventos persistidos; resumo staff lê ambos e verifica o arquivo ativo, sem cálculo operacional no Django.
- Admin Ops Django → `GET /admin/analytics/summary` com staff + MFA → metricas/insights da FastAPI; Django somente renderiza.
- Retenção: FastAPI combina `gotrendlabs_users.date_joined` e eventos autenticados para contas, e `analytics_visitors`/sessões/eventos anônimos para visitantes; Django exibe numeradores, denominadores e coortes semanais sem recalcular percentuais.
- Mapa: SVG estático local gerado da API de Malhas do IBGE em tempo de desenvolvimento; no runtime o navegador não chama o IBGE, e cores/filtros usam apenas `regions` da FastAPI.
- A FastAPI agrega UF/cidade, cobertura temporal e etapas de desistência por sessão/mercado; a tela administrativa consome os campos sem recalcular funis. O mobile registra seleção de opção no ticket inicial pelo mesmo contrato de eventos.
- Daemon → funcao backend de retencao analytics; ledger e auditoria permanecem separados.


## Governança editorial — FEAT-EDITORIAL-001

- Implementação: `docs/editorial/*.md` e `criteria-v1.2.json` → `apps/web/django/admin_ops/editorial_content.py` → `GET /admin-ops/editorial/` e atalhos do editor. A leitura é staff/read-only; critérios JSON alimentam ficha/parecer universal na FastAPI. Entrega documental produtiva validada em 2026-09-26; evolução universal local em 2026-10-07, sem deploy.

- Spec funcional → `features/editorial-governance.md` → `docs/editorial/manual-editorial.md`, `docs/editorial/ficha-de-mercado.md` e `docs/editorial/checklist-de-publicacao.md`.
- Dependências documentais: feed/taxonomia (`FEAT-MARKET-001`), sugestões (`FEAT-SUGGEST-001`), resolução (`FEAT-RES-001`) e integridade (`FEAT-INTEGRITY-001`).
- Admin Ops continua consumindo FastAPI; referência da ficha em `admin_notes` do rascunho, sem novos campos, endpoints, eventos ou migrations.
- Manual não modifica definição publicada, contratos de ciclo de vida/selagem, consenso, ranking ou destaque; aprovação automática e telemetria editorial ficam fora desta entrega.

## Dependências principais

- `FEAT-AUTH-001` suporta as demais features autenticadas
- `FEAT-AUTH-001` centraliza credenciais em `packages/security/passwords.py` e na FastAPI: ela executa cadastro/login/reset e e a unica runtime que recebe `GOTRENDLABS_PASSWORD_PEPPER`. Django web usa um hasher que recusa senha utilizavel; web e Flutter consomem os endpoints FastAPI existentes. `ops/scripts/auth_db_boundary.py` separa owner/migrator e privilegios de coluna no PostgreSQL, com verificacao no deploy; fronteira ativa e validada no RDS produtivo pela PR `#126`.
- `FEAT-AUTH-001` mantém MFA administrativo na FastAPI: login de `is_staff`/`is_superuser` retorna desafio, a API persiste fator TOTP cifrado/códigos hashados e só emite sessão administrativa após prova; Django apresenta as telas e guarda apenas a sessão web derivada. `.env.auth.prod` entrega a chave Fernet somente ao container FastAPI, a partir de `gotrendlabs/prod/app-secrets`; a fronteira e migrations foram validadas no deploy produtivo do workflow `36425169684`. Flutter deliberadamente não consome esse contrato enquanto não existir superfície administrativa mobile.
- `FEAT-AUTH-001` centraliza na FastAPI a maioridade de contas humanas; Django e Flutter enviam `birth_date`, e novos cadastros sociais concluem o perfil privado antes da criação da conta.
- `FEAT-MARKET-001` depende de `FEAT-AUTH-001` para visão autenticada e personalização
- `FEAT-MARKET-002` depende de `FEAT-MARKET-001`
- `FEAT-PRED-001` depende de `FEAT-MARKET-002`, `FEAT-WALLET-001` e `FEAT-AUTH-001`
- `FEAT-RES-001` depende de `FEAT-PRED-001`, `FEAT-WALLET-001`, `FEAT-REP-001` e `admin-ops`
- `FEAT-REP-001` depende de `FEAT-RES-001`
- `FEAT-COMMENT-001` depende de `FEAT-MARKET-002` e `FEAT-AUTH-001`
- `FEAT-SUGGEST-001` depende de `FEAT-AUTH-001` e `admin-ops`
- `FEAT-NOTIFY-001` depende de eventos do domínio, preferências de idioma, configuração SMTP em `gotrendlabs_site_config` e segredo de envio em ambiente/secret manager
- `FEAT-I18N-001` é transversal às demais features
- `FEAT-OPSLOG-001` depende de `FEAT-AUTH-001` para autorização staff dos contratos administrativos
- `FEAT-MOBILE-001` depende de `FEAT-AUTH-001`, `FEAT-MARKET-001`, `FEAT-MARKET-002`, `FEAT-PRED-001`, `FEAT-WALLET-001`, `FEAT-COMMENT-001`, `FEAT-REP-001` e contratos FastAPI/OpenAPI para operar como cliente mobile sem regra crítica local
- `FEAT-INTEGRITY-001` depende de `FEAT-MARKET-001/002`, `FEAT-PRED-001`, `FEAT-RES-001`, PostgreSQL, daemon, comunicações e AWS KMS; web/mobile dependem somente de seus contratos FastAPI/OpenAPI.
- O rollout produtivo de `FEAT-INTEGRITY-001` usa o alias KMS `alias/gotrendlabs-integrity-signing`, política IAM restrita na role da EC2, segredo de commitment no Secrets Manager, snapshot/corte dos mercados pré-lançamento e dois workers Django com swap/monitoramento no host único; dependências ativadas e validadas em 2026-09-07.

## Contratos com maior reutilização

- `market-lifecycle.md`
- `prediction-payloads.md`
- `wallet-ledger.md`
- `reputation-ranking.md`
- `i18n-content.md`
- `domain-events.md`
- `integrity-ledger.md`

## Integrações já materializadas

- `FEAT-INTEGRITY-001` integra publicação e previsão atomicamente ao signer, encadeia eventos globais sob advisory lock, sela mercados vencidos no daemon e distribui `market_sealed` por in-app/push/email idempotentes.
- `FEAT-INTEGRITY-001` usa checkpoints globais assinados: o daemon audita delta por ciclo e cadeia integral diariamente; FastAPI valida checkpoint/head na consulta publica sem full scan; selagem executa auditoria global integral fresca sob lock; Django e Flutter apresentam somente o contrato publico agregado, sem referencias individuais de previsoes de terceiros.
- O daemon reutiliza o verificador autoritativo de `FEAT-INTEGRITY-001` e materializa divergencias confirmadas em `gotrendlabs_integrity_alerts`; FastAPI inclui esses alertas na fila staff e Django Admin Ops apenas os apresenta/revisa.
- Previsoes iniciais humanas e de agentes IA compartilham `prediction_write_service`; reforcos/revisoes usam o mesmo `commit_prediction`. A auditoria exige correspondencia exata entre cada linha de previsao e seu compromisso antes de permitir Seal.
- Nomes taxonomicos sao snapshots editoriais na definicao; IDs de categoria/subcategoria/evento protegem a associacao estavel sem gerar falso alerta em renomeacao.
- O daemon isola auditoria, fechamento, selagem, retencao, email e push. Auditoria indisponivel adia a selagem do ciclo, mas nao derruba o processo nem impede tarefas independentes.
- Django Admin Ops configura a janela de 1 a 168 horas e apresenta filas/métricas; cards e detalhe web, Flutter e páginas de confiança consomem status/provas sem assinar ou recalcular autoridade no cliente.

- `FEAT-COMMENT-001` usa `FEAT-AUTH-001` para autor/reação autenticada e staff em moderação.
- `FEAT-COMMENT-001` usa `FEAT-MARKET-002` para vínculo com mercado e exposição em `MarketResponse.comments`.
- `FEAT-MARKET-001` fornece taxonomia `categoria -> subcategoria -> evento` para criação/edição de mercados, cards públicos e filtros administrativos; avisos opcionais de categoria/subcategoria/evento alimentam somente detalhe/ticket público abaixo do critério de resolução, e eventos sem mercados vinculados podem ser excluídos no Admin Ops.
- `FEAT-REP-001` consome a mesma taxonomia para recorte opcional de badges por categoria/subcategoria/evento; regras por evento só contam dados de domínio que carregam evento persistido.
- Admin Ops consome comentários via FastAPI e pode degradar para Postgres local em desenvolvimento quando a API estiver desatualizada.
- `FEAT-AUTH-001` e `FEAT-SUGGEST-001` compartilham validação anti-abuso server-side configurável por ambiente.
- Django renderiza o widget reCAPTCHA v2 e encaminha `recaptcha_token`; Flutter mobile usa `GET /anti-abuse/challenge` e encaminha `anti_abuse_token`/`anti_abuse_answer`; FastAPI é a autoridade de validação para cadastro e envios guest.
- `FEAT-OPSLOG-001` registra requests Django/FastAPI e logs Python em `gotrendlabs_system_logs`; Admin Ops consome `/admin/system-logs` para troubleshooting sem alterar domínio e configura `system_log_retention_days`.
- Admin Ops consome `GET /admin/dashboard-summary` via FastAPI para consolidar métricas operacionais de mercados, filas, usuários, engajamento, wallet, badges, logs, manutenção, email e reCAPTCHA.
- Config operacional usa duas fontes por fronteira: modo manutenção web/mobile em JSON runtime para sobreviver sem banco/API e parâmetros não sensíveis de email em `gotrendlabs_site_config`.
- Resend usa API HTTPS com domínio remetente verificado; SMTP permanece como fallback genérico configurável. O app usa apenas parâmetros não sensíveis em `gotrendlabs_site_config` e segredo em ambiente/secret manager.
- `communications` integra `FEAT-AUTH-001`, `FEAT-RES-001`, `FEAT-WALLET-001` e o daemon por meio de `EmailDelivery`: boas-vindas, confirmação de email, reset de senha, mercado fechado/resolvido e crédito concedido são enfileirados com idempotência e enviados conforme provider SMTP/Resend.
- Admin Ops expõe `Politica de Emails`, consumindo `EmailTemplate` para edição simples de assunto/corpos por chave/idioma, incluindo o rodapé transacional especial `system.transactional_footer`, e `EmailDelivery` para logs filtráveis de outbox, sem expor senha/API key de email nem contexto/corpo com links sensíveis.
- `communications` integra push mobile por meio de `PushDelivery`: toda entrega deriva de `gotrendlabs_user_notifications`, aplica `PushEventPolicy`/`PushPreference`, usa provider `none`/dry-run por padrão e envia FCM real apenas quando `GOTRENDLABS_PUSH_ENABLED=1`, provider `fcm`, dry-run desligado e credencial Firebase vier do ambiente/secret manager.
- Admin Ops expõe `Política de Push`, consumindo `PushTemplate`, `PushEventPolicy` e `PushDelivery` para edição operacional e logs sem expor token de dispositivo, payload sensível ou credencial Firebase.
- Recarga educativa de wallet usa `gotrendlabs_site_config.wallet_recharge_min_balance_gtl` como piso operacional configurado no Admin Ops; Django e FastAPI bloqueiam solicitação quando `available_gtl` está acima desse valor.
- Reforço/revisão de posição usa `gotrendlabs_site_config` para flags, limite de reforços, limite de revisões, cutoff, penalidade e mínimos; FastAPI valida e executa as mutações de previsão/wallet com lock transacional por usuário/mercado, enquanto Django web e Flutter mobile apenas consomem preview/ação e exibem estados/bloqueios retornados pela API.
- Status do daemon no Dashboard usa `gotrendlabs_site_config.daemon_stale_after_minutes` e `gotrendlabs_site_config.daemon_missing_after_minutes` como limites operacionais configurados no Admin Ops.
- Ranking web consome `GET /rankings` como fonte autoritativa, filtra por categoria/subcategoria/evento, exibe badges conquistadas resumidas após o handle e usa `Carregar mais` em blocos cumulativos de 10 linhas sem recalcular reputação ou elegibilidade de badges no Django.
- Deploy MVP usa EC2 com Docker Compose para `proxy`, `django`, `fastapi` e `daemon`; PostgreSQL de producao fica em RDS/servico gerenciado fora do Compose.
- O volume Docker `gotrendlabs_mediafiles` é compartilhado por Caddy/Django e montado read-only no FastAPI para que mídia `/media/...` seja servida pelo proxy e validada pela API antes de aparecer em payloads públicos.
- Infra AWS base de producao foi provisionada em `us-east-1` com EC2 `t4g.micro`, RDS PostgreSQL 16 `db.t4g.micro`, VPC dedicada, SSM, CloudWatch minimo, Parameter Store, Secrets Manager e role OIDC restrita para GitHub Actions no branch `main`; o workflow de deploy agora faz preflight de variables/secrets e valida `aws sts get-caller-identity` antes do `ssm send-command`.
- Acesso administrativo ao RDS usa tunel SSM pela EC2; o RDS permanece privado e aceita `5432` somente do security group da EC2.
- Workflow `.github/workflows/deploy.yml` roda testes em `main` e esta preparado para disparar `ops/deploy/production/deploy.sh` via SSM quando os secrets/variables do GitHub e `.env.prod` da EC2 estiverem configurados.
- `FEAT-AIAGENT-001` integra `apps/api/backend_api/agent_services.py` ao daemon operacional, usa `gotrendlabs_site_config` para flags/limites/retenção de auditoria, `gotrendlabs_ai_agents` para personas oficiais, `gotrendlabs_ai_agent_actions` para auditoria e exclui bots de ranking/badges/reputação pública. O daemon usa o vinculo por `user_id` e `is_bot`, sem senha ou login das contas bot; senhas inutilizaveis desses usuarios nao interrompem os ciclos.
- Admin Ops consome contratos staff de mercado para busca textual no browse e detalhe de participantes por mercado, mantendo Django como camada de exibição e FastAPI/backend como fonte das métricas humano/bot/total.
- `FEAT-MOBILE-001` integra o app Flutter em `apps/mobile` à FastAPI como cliente JSON, reutilizando `GET /markets`, `GET /markets/{slug}`, `POST /markets/{slug}/view`, `POST /markets/{slug}/share`, `GET /taxonomy`, `GET /stats`, `GET /health`, contratos autenticados de sessão/usuário, favoritos, curtidas, comentários, preview/criação de previsão inicial, reforço/revisão de posição, wallet/recarga, ranking, badges, desempenho e alertas; flags autenticados como `viewer_has_favorite`, `viewer_has_prediction` e `viewer_position` alimentam recortes pessoais, mesa de posição e ações de reforço/revisão no app sem recalcular domínio no cliente.
- `FEAT-MOBILE-001` usa `viewer_position.history` para listar as acoes da propria posicao e carrega cada comprovante assinado por `GET /markets/{slug}/predictions/{prediction_id}/receipt`; a assinatura, o payload e a prova Merkle continuam autoritativos na FastAPI, e o app apenas os apresenta ao titular.
- `FEAT-MOBILE-001` consome `GET /users/me/performance` para a tela autenticada `Desempenho`, exibindo placar, historico de resolucoes, resultado GT₵ educativo, impacto em reputacao e ultimas conquistas; o app reconsulta esse contrato ao abrir a tela, voltar do background, usar pull-to-refresh e apos mutacoes de previsao/posicao.
- `FEAT-MOBILE-001` consome `GET /anti-abuse/challenge` para cadastro, feedback e sugestão de mercado de visitantes, mantendo o desafio dentro do app e validado pela FastAPI; usuários autenticados enviam feedback/sugestão sem desafio.
- `FEAT-MOBILE-001` usa `GET /health` enriquecido para o boot gate de manutencao mobile; Admin Ops controla `mobile_maintenance_enabled` em runtime JSON separado do modo web, FastAPI bloqueia chamadas mobile por `X-GoTrendLabs-Client: mobile`, e nao ha excecao por papel no app.
- `FEAT-MOBILE-001` usa a API atual única para compatibilidade de build: Flutter envia versão/build por headers, FastAPI compara `X-GoTrendLabs-App-Build` com `gotrendlabs_site_config.min_supported_android_build`, `/health` permanece isento, endpoints não isentos retornam `426 code=app_update_required` para builds antigos e o `ApiClient` promove esse 426 para estado global de update obrigatório.
- A política mobile lê `gotrendlabs_site_config` e a release Android ativa em `gotrendlabs_mobile_app_releases`; migrations de compatibilidade devem manter `SELECT` para o papel runtime da FastAPI nessas tabelas.
- `FEAT-MOBILE-001` consome os contratos autenticados de push (`/users/me/push-devices` e `/users/me/push-preferences`) por repository/controller; QA local pode registrar um device fake autenticado com `GTL_PUSH_FAKE_TOKEN`, e Android com `google-services.json` local coleta token FCM apenas após autenticação.
- A tela mobile `Sobre` pode consultar a saúde da API e dados seguros da sessão, mas não deve expor endereços de API/web, tokens, segredos ou ID interno do usuário na UI nem no diagnóstico copiado.
- `FEAT-MOBILE-001` publica o beta Android pelo site: Django expõe CTA direto no rodape, nas telas de acesso e nas paginas de compartilhamento, expõe `/app/android/latest.json`, Admin Ops gerencia `MobileAppRelease`, arquivos ficam em media e Caddy serve `/media/app_releases/android/...` por HTTPS.
- Produção expõe a FastAPI para o app mobile em `https://gotrendlabs.com.br/api/*`, com Caddy removendo o prefixo `/api` antes de encaminhar para `fastapi:8001`; mudanças no `Caddyfile` precisam recriar/recarregar o container `proxy` para que o roteamento em execucao acompanhe o arquivo versionado.
- No emulador Android, o mobile consome a API local por `http://10.0.2.2:8001`; `127.0.0.1` dentro do emulador aponta para o próprio dispositivo emulado.
- No iOS Simulator, o mobile consome a API/web local do Mac por `http://127.0.0.1:8001` e `http://127.0.0.1:8000`, mantendo o mesmo contrato FastAPI e apenas trocando a base local por plataforma.
- A estratégia v1 de autenticação persistente mobile usa Bearer em secure storage quando `Lembrar login` está ligado e token apenas em memória quando desligado; refresh token, renovação automática e revogação avançada continuam como evolução futura.

## Skills técnicas por stack

- `gotrendlabs-django-web`: páginas, templates, HTMX, Alpine.js, i18n de interface e admin Django
- `gotrendlabs-fastapi-domain`: domínio, contratos, autenticação, endpoints e regras centrais
- `gotrendlabs-postgres-modeling`: modelagem relacional, ledger, integridade, índices e rastreabilidade
- `gotrendlabs-ops-scheduler-communications`: jobs temporizados, eventos, emails, observabilidade operacional e fluxos assíncronos
- `gotrendlabs-mobile-architect`: arquitetura Flutter, navegação, estado, ambiente Android e fronteiras mobile/FastAPI
- `gotrendlabs-mobile-api-contract-guard`: contratos FastAPI, OpenAPI, auth, payloads e erros consumidos pelo app mobile
- `gotrendlabs-mobile-flutter-implementer`: implementação Flutter em `apps/mobile` guiada por specs
- `gotrendlabs-mobile-test-strategy`: testes unitários, widget, repository, integration, smoke Android e QA visual mobile
- `gotrendlabs-mobile-ux-designer`: UX/UI dark-first, componentes, telas e aderência às referências visuais fornecidas sem cópia literal

## Skills de produto e curadoria

- `gotrendlabs-prediction-markets`: sugere mercados de previsão binários ou múltiplos usando dados internos da GoTrendLabs, trends sociais/cripto, links exatos de verificação, diversidade editorial, aviso de risco para cripto e checagem anti-repetição

## Skill de governança de processo

- `gotrendlabs-workflow-governor`: abre, acompanha, retoma, bloqueia, conclui, cancela ou substitui workflows que tocam múltiplos documentos
- `gotrendlabs-software-architect`: define arquitetura, segurança, módulos, riscos, ADRs e desenho técnico para mudanças relevantes
- `gotrendlabs-test-engineer`: implementa, revisa e executa testes concretos de backend, frontend, contratos, integração e fluxos
- `gotrendlabs-mobile-docs-governor`: mantém docs, status, changelog, workflow, integration map, README e memória sincronizados para mobile

## Documentos de workflow

- `docs/specs/workflows/`: templates canônicos de processo
- `docs/specs/state/workflow-runs.md`: memória operacional de execuções
- `docs/specs/state/workflow-checklists.md`: checklists de conclusão e qualidade

- Admin Ops Integrações → `GET /admin/agent-integration-responsibles`: projeção mínima de responsáveis humanos elegíveis pela FastAPI, com sessão MFA e paginação; alimenta seleções de criação/transferência. Não adiciona ferramenta MCP nem acesso ORM no Django.

## 2026-10-07 — revisão editorial universal

WFLOW-20261007-UNIVERSAL-EDITORIAL-001: criação humana/conversão → ficha pendente (origem humana, integration nullable); MCP → ficha com autoria técnica; Admin Ops → assessment humano atestado; MarketLifecycleEngine → configuração de fechamento + aprovação atual → definição assinada. Legados recebem ficha sem mudança de estado/provas. OpenAPI expõe editorial_origin e closure_configuration_errors somente com informação administrativa. FEAT-MCP-001 permanece parcial por homologação externa e deploy. Evidências: [relatório](../testing/universal-editorial-20261007.md).

## FEAT-THUMB-001 — geração administrativa

- Admin Ops template/form/JS → Django session/CSRF/proxy → FastAPI thumbnail_routes/service → gotrendlabs_thumbnail_jobs.
- Worker dedicado thumbnail_worker → single Bedrock Runtime InvokeModel Core/SD3.5/Ultra (snapshot do job, us-west-2) → thumbnail_private (RW worker/RO API).
- PATCH administrativo confirma candidata sob lock do mercado e promoção/prune → mediafiles subpath market_thumbnails RW → image_url público existente. Candidata privada nunca é servida pelo proxy /media.
- Grants admin_ops.0022/0023: fila só FastAPI/runtime worker; Django é adaptador. Sessão staff/MFA vigente revalidada no claim/finalização; estado draft/revisão editorial autoritativos.
- Sem mudanças em agentes de comentários, daemon, contratos públicos web/mobile, ledger de integridade, notificações ou MCP editorial.
- Config thumbnail_* separada de ai_* no painel → Django sessão/CSRF → GET/PUT FastAPI /admin/thumbnail-settings → SiteConfig + auditoria; snapshot por job. GTL_THUMB_ENABLED é kill switch; segredo Bedrock do executor. [ADR-0012](../decisions/ADR-0012-private-thumbnail-worker.md), [runbook](../../guides/admin-ai-thumbnails-runbook.md).

- Fechamento FEAT-THUMB-001: deploy padrão → bootstrap do subdiretório → profiles MCP e opcional thumbnails → parada dos escritores → migrations/grants → restart. `.env.thumbnails.prod` existente inclui worker no ciclo mesmo pausado; autorização de consumo segue switches operacionais/DB. CI verifica build completo. Duas invocações Core DEV concluídas; rollout produtivo pendente de aprovação/CI.

## 2026-10-09 — Imagens IA de badges

FEAT-BADGE-IMAGE-001: badge_form/contexto → Django session/CSRF → badge_image_routes/service → fila tipada compartilhada → executor/Bedrock 1:1 → candidata privada → confirmação por ID no POST/PATCH → badge_images/image_url. Painel habilita badges separadamente; modelo e cotas globais compartilhados, nenhuma mudança em agentes/concessões.


Imagens de badges: worker → duas invocações nativas Bedrock (light/dark) → dois PNG privados → proxy administrativo com theme validado → seleção indivisível no editor → POST/PATCH confirma par → image_url/image_dark_url públicos. Reserva global/operador de duas imagens; lease para ambas as chamadas e checkpoint de uso por tema sem retry incerto.


Fechamento WFLOW-20261009-BADGE-CLOSE-001: commit local → aprovação da descrição → push/PR própria → CI/build → merge main → Actions/SSM → migration0025/grants/mount badge_images/worker compartilhado → habilitação auditada de badges → smokes técnicos. Thumbnails produtivas PR #143 preservadas; sem novo recurso AWS/provedor e sem geração paga automática.


## 2026-10-09 — Estado produtivo atual de imagens administrativas

PR #144 integrada em main edac7c7; CI PR e main/build/deploy Success, 442 testes em ambos com um skip por roles CI ausentes (cenário aprovado localmente). Migration0025/grants/constraints/mounts/executor conferidos; habilitação auditada de badges concluída, política de thumbnails preservada. Stable Image Core/Oregon, badges1:1, timeout180s, limites10 imagens/operador e50 globais por24h,5 solicitações/item, retenção24h. Fila vazia, sem inferência paga ou alteração de mercados/concessões reais. Branch local preservada. Manutenção pública ativa preservada; Admin Ops exige login. Homologação humana/MFA e coerência visual real permanecem pendentes. [Evidência produtiva](../testing/ai-badge-images-production-20261009.md). Registros anteriores são histórico das etapas.


## 2026-10-09 — Incidente: auditoria do worker de imagens

Incidente WFLOW-20261009-IMAGE-WORKER-AUDIT-FIX-001: primeira solicitação produtiva informada permanece queued, sem started_at/provider_id/arquivo. Worker falha na auditoria porque thumbnail_service.event importava main, ativando exigência de pepper/TOTP exclusivos da API. Diagnóstico por SSM/read-only e probes com rollback, sem inferência ou mutação em mercados. Correção local usa diretamente admin_events, sem distribuir segredos HTTP ao executor. Teste em subprocesso com ambiente production, segredos HTTP vazios e provedor simulado cobre claim, sucesso e eventos persistidos. Rollout corretivo e conclusão da solicitação real ainda pendentes; não afirmar latência do provedor, acesso efetivo ou qualidade real por esse incidente.


## 2026-10-09 — Recuperação produtiva do executor

Incidente resolvido pela PR #146/main b033afe4, CI PR37981039913 e main37981803447/build/deploy Success (443 testes, um skip de roles CI). SSM deploy3e165a28 e verificação0d584e9f Success: auditoria do worker sem main, serviços ativos. Pedido original cdbe1f42-d75b-44ec-8f0c-11ece3d6952e succeeded em 6.451679s de processamento, arquivo privado presente e ID de provedor registrado; sem nova solicitação/replay pelo assistente ou salvamento/publicação do mercado. Primeira execução Core produtiva iniciada pelo operador confirma acesso efetivo do token/modelo, mas não avaliação visual ou custo faturado. [Evidência externa](https://github.com/wscardua/gotrendlabs/pull/146). Recibo atualizado localmente para próximo versionamento autorizado.


Thumbnails: montagem visual v3 no backend (thumbnail_prompt.py), chamada Runtime/modelo configurado inalterados; sem tradutor/modelo adicional, novos endpoints, banco ou dependência externa. V2 continua executável com instruções históricas. Badges seguem par v2 independente.


2026-10-09 — Etapa histórica v4, substituída pela v5: prompt market-thumbnail-bedrock-v4 sem temas, entidades, cenas ou condicionais fixos por categoria. Pergunta/resumo/classificação atuais determinam o assunto; regras fixas somente de composição, qualidade, neutralidade e segurança. Substitui a proposta local v3 de âncoras temáticas, rejeitada pelo usuário. Executor DEV reiniciado com fila vazia, PID82614; imagens/estados v3 existentes preservados, sem reinterpretar/repetir solicitações. V3 queued não chama provedor (unsupported_instructions); v2 histórico preservado. Produção e modelos não alterados; sem nova inferência paga. Validação v4: 70 testes de thumbnails/badges aprovados em 102.686s com PostgreSQL isolado/provedor simulado; rechecagem dos 6 testes do provedor aprovada em 0.053s, incluindo invariância do template entre temas, contexto completo e rejeição de v3 sem invocação. Django check, compilação Python e diff aprovados. Nenhuma inferência paga iniciada; qualidade real permanece pendente de avaliação pelo operador. Log thumbnail-dynamic-tests.log e thumbnail-dynamic-provider-tests.log em .runtime/badge-validation.


2026-10-09 — Direção vigente v5: interpretação semântica em modelo textual Bedrock seguida da imagem configurada. Sem templates/presets de assunto ou composição por categoria. Configuração textual própria GTL_THUMB_PLANNER_* congelada no job; default openai.gpt-oss-20b/Mantle us-east-1, timeout45s, saída2048tokens (allowlist20b/120b; timeout10–120s/tokens512–4096). Uma chamada textual e uma imagem por reserva, sem retry/fallback; checkpoints planner/image sob fencing/elegibilidade, lease soma timeouts e brief final privado persistido para auditoria/regeneração. Falha textual impede imagem. V2 histórico preservado; v3/v4 não reinterpretados. Substitui as soluções v3/v4; badges/comentários/interface não mudam. ADR-0014 formaliza a mudança justificada pelos exemplos reais irrelevantes e exigência do usuário. Validação v5: 75 testes aprovados em 103.334s, PostgreSQL isolado/provedor simulado, cobrindo planejamento→imagem, falhas/recusa/timeout sem imagem, checkpoints/fencing, preservação de uso após erro desconhecido e ausência de replay, snapshot/lease, regeneração e badges. Dois testes adicionais dos agentes textuais aprovados (3.271s e1.718s), sem alteração de seu comportamento. Django check, OpenAPI --check, compilação Python e diff aprovados. Executor DEV reiniciado sem geração ativa, PID93387; v5 posteriormente homologado informalmente pelo operador no DEV, conforme recibo abaixo. Nenhuma inferência paga pelo assistente ou mudança produtiva; commit local preparado no fechamento, PR/deploy aguardam aprovação. Credencial/acesso e avaliação visual informal do novo fluxo confirmados no DEV; homologação PRD permanece pendente. Logs thumbnail-semantic-*.log em .runtime/badge-validation.


## Homologação DEV e preparação de PRD v5

2026-10-09 — Homologação DEV v5: operador informou “em dev local parece estar legal” e autorizou preparar PRD. Consulta local somente leitura confirmou três jobs v5 succeeded (34ccb8f0, bcc57be2, 5cb97131), iniciados pelo operador, com planner openai.gpt-oss-20b/Mantle us-east-1 e imagem Core/us-west-2. Tempos de processamento: 17.804s, 9.663s e 15.883s; uso textual retornado registrado, sem afirmar custo faturado. Acesso efetivo e aprovação visual informal do fluxo DEV confirmados; não substituem matriz visual sistemática, medição de engajamento ou homologação do token/modelo em PRD. Nenhuma inferência paga iniciada pelo assistente. Próxima etapa: aprovação da descrição atualizada da PR, CI completo, merge/deploy e verificação produtiva; preservar modelo de imagem e políticas atuais de PRD.


2026-10-09 — Preflight PRD somente leitura: SSM3c6b5fda confirmou SHA b033afe4, seis serviços ativos e credencial Bedrock presente no executor (valor não exposto), switch ambiental 1, defaults textuais 20b/us-east-1. Consulta inicial da política precisou ser corrigida por uso inadequado do context manager; SSM8f95b96a concluiu Success sem stderr: thumbnail_enabled=true, Core/stability.stable-image-core-v1:1, us-west-2, 3:2, timeout180s, limites operador50/mercado50/global50 por24h e retenção24h; nenhum queued/running. Valores atuais substituem o recibo histórico de defaults10/5 no que se refere à configuração efetiva observada, sem alterar os defaults da spec. Preservar essas escolhas no deploy. Nenhuma mutação produtiva ou inferência; preflight não comprova acesso de inferência Mantle do token produtivo.
