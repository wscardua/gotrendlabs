# Piloto MCP editorial e operação

FEAT-MCP-001 no worktree `gotrendlabs-mcp`, branch `feature/mcp-editorial`, baseado em `origin/main` `9df08bc`. Checkout original, documentos e mobile preservados. Entrega local validada e rollout preparado; PR/merge/produção aguardam autorização neste fechamento. Dot exige homologação real.

## Preparar rollout autorizado posterior

1. Usar Python 3.11/3.12: `requirements.txt` na API/web; `apps/mcp/requirements.txt` no adapter. Venv 3.9 original preservado; este worktree tem `.venv` próprio.
2. Aplicar migrations com role migradora via `ops/scripts/migrate_with_role.py`: `editorial_integrations.0001`, auditoria `markets.0032`, grants/índices `editorial_integrations.0002` e backfill universal `editorial_integrations.0003`. FastAPI escreve; Django não recebe acesso às tabelas privadas novas. Conferir grants efetivos; runtime não usa role migradora.
3. Configurar HTTPS com iguais `GTL_MCP_RESOURCE=https://DOMINIO/mcp` e `GTL_MCP_ISSUER=https://DOMINIO` nos dois processos. Workload aleatório ≥32 caracteres entregue somente API/adapter via secret manager/arquivo 0600, nunca Git/prompts/logs. Exemplos separados `.env.mcp-api.prod.example` e `.env.mcp.prod.example`.
4. Adapter sem PostgreSQL/DATABASE_URL, pepper, MFA, KMS ou `.env.prod`. Imagem mínima `ops/deploy/mcp/Dockerfile`; override Compose `ops/deploy/mcp/docker-compose.override.yml`, profile `mcp`, rede interna, filesystem read-only, spool privado. O deploy padrão inclui o override e importa os handles de `Caddyfile.example` antes de API/Django. Bloquear também `/api/internal/agent-integrations*`; rotas internas não são públicas. Proxy sem cache de auth/dados privados.
5. Iniciar com `GTL_MCP_ENABLED=0` nos dois processos. Conferir `/health`, isolamento, grants, redaction e discovery; depois habilitar explicitamente. Admin Ops → Integrações: criar pausada, definir responsável/scopes/cotas e ativar para piloto pequeno.
6. Observar logs por integração/execução/ferramenta/resultado. Autoria automática é técnica, não personificação do responsável. Revisão/hash humanos ficam preservados; Nova publicação de qualquer mercado exige aprovação humana da versão atual; legados já publicados mantêm lifecycle e provas.

Loopback com proxy local: endereço público DEV `http://127.0.0.1:8000`, Django interno 8003, API 8001 e MCP interno 8002. Issuer `http://127.0.0.1:8000`, resource `http://127.0.0.1:8000/mcp`, API do adapter `http://127.0.0.1:8001`. O proxy encaminha `/oauth/*` e discovery para FastAPI, `/mcp` e metadata protegida para MCP e os demais caminhos para Django, bloqueando rotas internas. O issuer deve servir API OAuth e consentimento Django; portas separadas sem proxy não completam o fluxo de navegador. Apenas neste ambiente usar `AUTHLIB_INSECURE_TRANSPORT=1` na API; nunca em produção. Não apontar para contas ou mercados reais.

## Conectar OAuth — preferido para Dot

URL MCP canônica `/mcp`, sem trailing slash adicional. Metadata protegida `/.well-known/oauth-protected-resource/mcp`; authorization server `/.well-known/oauth-authorization-server` no issuer.

Cliente público registra redirect HTTPS exato ou loopback em `/oauth/register`; DCR não autoriza dados. Navegador abre `/oauth/authorize`, faz login GoTrendLabs/MFA e consentimento Django com CSRF, mostrando cliente, redirect, integração e scopes. Code flow exige PKCE S256/resource, código de 5 minutos/uso único, state conferido pelo cliente e callback com `iss`.

`/oauth/token`: formulários `authorization_code`/`refresh_token`. Access até 10 minutos; refresh rotaciona e grant tem prazo absoluto até 90 dias, sem extensão infinita. Reuso de código/refresh revoga família. Cliente confere issuer/audience e guarda tokens em storage seguro. Secret de serviço não é OAuth client secret.

SDK pode selecionar automaticamente todos os scopes anunciados. Consentimento não amplia scopes da integração; limite permissões no Admin Ops e reautorize conforme necessário. Tools/list e execução respeitam permissões atuais, incluindo redução/revogação.

A [documentação oficial custom MCP OpenAI](https://developers.openai.com/api/docs/guides/custom-mcp-server) descreve conexão OAuth em superfícies compatíveis. Confirmar custom MCP/escrita/recorrência na conta Dot concreta; SDK local não homologa Dot.

## Conectar serviço

No detalhe, **Gerar credencial de serviço** mostra ID público e segredo uma única vez, `private, no-store`. A UI com JavaScript mantém documento GET: reload não reapresenta nem reemite. Sem JavaScript, emissão POST exibe a resposta uma vez; navegue pelo link para voltar ao GET, evitando resubmissão do formulário.

Guardar segredo em secret manager. Nova emissão não revoga antigas. Rotação: emitir nova, migrar executor, comprovar uso e revogar antiga explicitamente; tokens derivados também ficam inválidos.

Executor envia formulário a `ISSUER/oauth/token`: `grant_type=client_credentials`, `client_id=ID_CREDENCIAL`, `client_secret=SEGREDO`, `resource=URL_MCP`, `scope=SCOPES`. Obter valores do secret manager, sem argumentos de shell, Git ou prompts. Access vai em Authorization Bearer a cada requisição MCP, nunca diretamente à API de domínio. Renovar pela troca de serviço; não há refresh de serviço.

## Domínio, retry e quotas

Defaults: pausada, 5 drafts/dia São Paulo, 60 tentativas autenticadas/minuto, 2 leases concorrentes/45s, credencial/grant até 90 dias. HTTP 3s conexão/15s operação, statement 15s/lock 5s. Contadores persistem entre workers/reinícios; redução bloqueia consumo novo. Validação/scopes negados contam tentativa autenticada.

Create/update/submit exigem chave 8–100 caracteres e payload estável. Mesmo conteúdo retorna resultado original; mesma chave/conteúdo diferente conflita. Auth atual é revalidada antes do replay. Garantia mínima 30 dias; versão inicial conserva idempotência indefinidamente. Resposta perdida: repetir com backoff/jitter e Retry-After. Adapter não repete escritas automaticamente.

Preparação/devolvido permitem edição própria. Submissão cria snapshot/in_review. Parecer approved/returned/rejected referencia revisão/hash e preserva histórico. Pendência obrigatória/política antiga impede aprovação; E06/E08 exigem fonte relatada aberta e atestação humana. Edição humana invalida parecer/evidências e incrementa versão; editor existente envia expected_revision. Publicação permanece humana/serializada com assinatura existente. Todos os mercados exigem aprovação humana atual para nova publicação na FastAPI; ausência/recusa/versão antiga retorna 409 `editorial_approval_required`. No editor, publicar a versão aprovada é ação separada de salvar; qualquer save exige nova revisão. Legados publicados recebem ficha pendente sem mudança retroativa de lifecycle.

Backend não busca URLs, faz downloads ou pesquisa LLM. Ficha privada é domínio, independente da retenção técnica; evidências são relatos e renderizadas com escape. [Prompt de radar](dot-editorial-radar.md).

## Logs e rollback

Reutiliza `gotrendlabs_system_logs` e `gotrendlabs_admin_events`. Falha técnica não aborta operação; auditoria transacional falha aborta. Adapter sem gravador SQL. Ingestão exige workload + delegação, deduplica event ID e deriva ator do token. Resultado do adapter é relatado, API é autoridade.

Spool: 128 arquivos/512 KiB/TTL 24h, somente IDs/ferramenta/resultado. Sem tokens/payloads/mensagens livres. Reenvio na próxima chamada da mesma integração autorizada. Saturação/TTL podem perder eventos; revogação impede reenvio. Dados runtime de auth/idempotência são conservados nesta versão; acompanhar crescimento e planejar limpeza preservando replay/reuse. Purge técnico não apaga ficha/histórico.

Kill switch: `GTL_MCP_ENABLED=0` em API/adapter, reiniciar ambos e retirar handles MCP/OAuth do proxy. Pausar/revogar acessos conforme incidente. Preservar drafts, ficha, snapshots e auditoria; não reverter migrations apagando dados. Desconexão não interrompe agenda/pesquisa/memória externa.

## Homologação pendente e reprodução

Em HTTPS autorizado: discovery/proxy, OAuth/login/MFA/consentimento, tools por scope, leitura paginada, draft próprio de teste, submissão/parecer, recorrência/renovação, quota, pausa/revogação e logs. Registrar cliente/conta/horário/IDs/códigos sanitizados e rollback. Não publicar nem criar mercados reais para testar. Separar implementação local, Dot e deploy.

Testes locais: `python ops/scripts/test_mcp_local.py --db-admin-env /CAMINHO/.env.db-admin.local`. Usa PostgreSQL loopback `test_gtl_mcp_pilot` e somente credenciais administrativas locais; não carrega segredos externos da `.env`. CI: `python manage.py test`. OpenAPI: `python packages/contracts/export_openapi.py --check`. Resultado por critério: [matriz](../specs/testing/mcp-editorial-results.md).

## DEV local iniciado — 2026-10-07

A pedido do usuário, PostgreSQL local `gotrendlabs` foi reiniciado, as três migrations MCP foram aplicadas com role migradora e a fronteira FastAPI foi conferida. Web/API/MCP usam o worktree `gotrendlabs-mcp` e `.venv` Python 3.11, preservando `.env`, auth e runtime do checkout original por referências locais ignoradas. PostgreSQL, Django, API, MCP e proxy estão ativos; nenhum serviço produtivo alterado.

Proxy Docker `gotrendlabs-mcp-dev-proxy` expõe somente `127.0.0.1:8000`; upstreams 8001/8002/8003 são loopback. Launcher, PIDs/logs, Caddyfile e segredo workload DEV ficam em `.runtime/dev/`, fora do Git; `mcp.env` tem modo 0600 e o processo MCP recebe apenas sua configuração, sem variáveis de DB/MFA/pepper. Reload ativo para os três processos Python. MCP habilitado apenas em DEV; exemplos produtivos permanecem desligados.

Smokes: home/login/static/API health/discovery 200; Admin Ops integrações/revisão exige login; authorize redireciona ao consentimento no mesmo origin; internal 404; MCP health enabled e contrato editorial presente no OpenAPI local. Acesse `/admin-ops/integrations/` e `/admin-ops/agent-reviews/` no origin DEV com sua conta e MFA existentes. Dot/HTTPS externo continuam pendentes.

## LM Studio: pedido de editorial versus catálogo

`get_editorial_policy` retorna o manual aprovado completo (`manual`), checklist, modelo de ficha e critérios E01–E11. `search_markets` lista/busca mercados existentes; `get_taxonomy` fornece categorias e eventos. As descrições e instructions MCP tornam essa distinção explícita. Depois de atualização do adapter, use **Refresh tools** no LM Studio e reconecte o MCP para atualizar instructions; inicie conversa nova para não reutilizar chamadas incorretas no histórico.

Prompt de leitura:

> Consulte a ferramenta get_editorial_policy sem argumentos. Apresente em português o conteúdo do campo manual e os critérios editoriais. Meu pedido é a política editorial geral do GoTrendLabs.

Confirme visualmente que a ferramenta executada foi `get_editorial_policy`. Se necessário, habilite somente essa ferramenta para este teste, mantendo as permissões server-side existentes. Um modelo que gere prosa/delimitadores inválidos em vez de chamada estruturada ainda pode falhar antes de chegar ao servidor; descrições mais claras ajudam a seleção, mas não comprovam compatibilidade do modelo. Escolha um modelo com tool use nativo suportado pelo LM Studio e mantenha o template original.

Na homologação observada, DeepSeek-R1-0528-Qwen3-8B/MLX apresentou falha de parser de chamadas e LLGuidance de títulos automáticos. Não registrar homologação LM Studio como concluída por descoberta de tools ou teste SDK isolado.

## Revisão humana em uma ação (v1.3)

1. No Admin Ops, abra Revisão editorial e selecione o rascunho. Não é necessário aprovar ou reenviar a revisão antes de registrar o parecer.
2. Confira fontes e critérios E01–E11, marcando apenas o que verificou independentemente. Ajustes de contexto/fontes são opcionais; resolva e documente lacunas antes de aprovar.
3. Escreva **Nota do parecer**, escolha **Aprovar**, **Devolver para ajustes** ou **Rejeitar** e clique em **Registrar parecer humano**. Ficha e decisão são persistidas juntas; uma recusa reverte toda a operação.
4. Após aprovação, a publicação permanece uma ação separada no editor. Salvar outra edição exige parecer para a nova versão.

Não há dois aceites humanos. A API compõe snapshot e decisão na mesma transação, mantém locks/versionamento, MFA e auditoria. Endpoints v1.2 permanecem compatíveis, mas a UI usa o assessment único. Relatos do agente não deixam verificações humanas pré-marcadas.

## Revisão universal e rollout (2026-10-07)

1. Antes de liberar publicações, aplicar editorial_integrations.0003_universal_editorial com a role de migrations, em janela sem publicação/edição concorrente. Fazer backup; conferir contagens/hashes de mercados, opções, previsões e provas antes/depois. Não ampliar grants Django: API reutiliza grants existentes de ficha.
2. A migration torna integração nullable e cria fichas pendentes só para mercados sem ficha. Não aprova nem altera mercado/provas. API/Admin Ops devem suportar origem humana e gate universal antes de retomar publicação.
3. Para cada novo mercado: preencher data/hora futura, fuso IANA, escolher automático/manual, revisar ficha E01–E11 e fontes, registrar parecer aprovado da versão atual, publicar pela ação separada. Editar exige novo parecer. Conversões de sugestões seguem o mesmo fluxo.
4. Conferir legados: terminais são consultáveis; abertos/fechados permitem parecer sem mudança de estado. Tratar configurações antigas incompletas como tarefa humana, sem reescrever definição assinada nem escolher prazo arbitrário.
5. Rollback: preferir correção progressiva. Conservar migration/fichas/histórico; não reverter 0003 (origens humanas nulas impedem retorno seguro a FK obrigatória). Se voltar aplicação, usar versão compatível com origem nullable e suspender publicações até validar gate universal. Não restaurar seletivamente mercados/provas.

DEV: migration aplicada e preservação de dados verificada. Produção/deploy não executados. Homologação Dot externa permanece pendente; não substituir OAuth por acesso desprotegido.

### Quando o legado publicado não salva data/fuso

Se o erro for definição assinada, o PATCH foi rejeitado: os valores do formulário não chegaram ao registro salvo. O gate universal não libera reescrita de prazo/fuso/modo após publicação. Não atualizar diretamente PostgreSQL/ORM ou apagar provas para contornar. Retificação assinada ainda não é um fluxo implementado; cancelamento com refund e nova proposta revisada são ações operacionais separadas, somente por decisão humana.

## Ativação após merge autorizado

O deploy pelo Actions executa `python3 ops/deploy/mcp/configure_environment.py --app-dir /opt/gotrendlabs`, gerando arquivos separados 0600 e workload exclusivo, sem imprimir valores. Primeira instalação mantém enabled=0; deploys posteriores preservam o estado. Não copiar arquivos de ambiente de DEV. Fazer backup RDS recuperável e inventário de domínio antes do merge/migrations.

Depois de CI/deploy aprovado, no host via SSM: `python3 ops/deploy/mcp/configure_environment.py --app-dir /opt/gotrendlabs --enabled 1`. Recriar FastAPI e MCP com os dois Compose e `--profile mcp`: `docker compose -f ops/deploy/production/docker-compose.yml -f ops/deploy/mcp/docker-compose.override.yml --profile mcp up -d --wait --wait-timeout 180 fastapi mcp`. Conferir HTTPS/discovery/401 e bloqueio internal, migrations/grants, health e preservação de dados. Habilitar a infraestrutura não cria integração ou credencial para nenhum executor; o operador cria e ativa sua integração no Admin Ops/MFA.

Rollback de acesso: repetir configure_environment com `--enabled 0` e recriar ambos. Preservar schema e histórico; publicações continuam sob o gate universal. Backup seguro dos dois arquivos MCP é necessário para manter delegação entre reinstalações; em perda/comprometimento, rotação exige operação explícita e reinício conjunto, sem exibir segredo. OAuth Dot e rotina externa só são declarados validados após teste real da conta.

Janela de migrations: após build e preflights, o deploy para Django/FastAPI/daemon/MCP antes de aplicar migrations/grants e reinicia após conclusão. O proxy permanece disponível, mas páginas/API podem retornar 502/503 nessa janela. Se migrations falharem, não reiniciar automaticamente código anterior sem gate universal: preservar backup, identificar/fixar erro e repetir deploy aprovado. Para rollback de acesso com aplicação saudável, usar somente `--enabled 0`; não reverter schema/dados. Snapshot RDS disponível antes do merge e inventário antes/depois são requisitos desta operação.
