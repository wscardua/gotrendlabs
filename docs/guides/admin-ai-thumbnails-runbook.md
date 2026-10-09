# Thumbnails IA — operação e homologação

## Uso e Configurações do Sistema

No Admin Ops, abra um mercado existente em draft, clique **Gerar thumbnail**, depois **Gerar outra** se necessário. A candidata fica automaticamente selecionada. **Desfazer troca** restaura a seleção anterior, inclusive upload manual. Geração não salva/publica; use os botões existentes. Alterar imagem invalida a revisão editorial da versão salva; siga o gate vigente antes de publicar.

Em **Configurações do Sistema → Thumbnails por IA**, use **Salvar thumbnails** para atualizar exclusivamente essa seção via FastAPI. Staff/MFA e CSRF são obrigatórios. Credenciais nunca aparecem no painel. Salvar parâmetros não invoca modelos, não altera agentes de comentários, nem reconfigura trabalhos já enfileirados. Mudanças entram nas próximas solicitações, sem restart. Valores inválidos são rejeitados sem persistência; falha da API preserva a seleção para tentar novamente.

| Parâmetro persistido | Default | Faixa/opções |
|---|---|---|
| thumbnail_enabled | false | Habilitação administrativa, além do kill switch de ambiente |
| thumbnail_model | stability.stable-image-core-v1:1 | Core, stability.sd3-5-large-v1:0, stability.stable-image-ultra-v1:1 |
| thumbnail_region | us-west-2 | Oregon, região oficialmente suportada pelos três adapters |
| thumbnail_aspect_ratio | 3:2 | 3:2, 16:9, 1:1; elemento central seguro para recortes |
| thumbnail_timeout_seconds | 180 | 10–600 segundos; sem retry |
| thumbnail_operator_limit | 10 | 1–10.000 solicitações por operador/período |
| thumbnail_market_limit | 5 | 1–1.000 por mercado/período |
| thumbnail_global_limit | 50 | 1–100.000 global/período |
| thumbnail_period_hours | 24 | Janela móvel 1–720 horas |
| thumbnail_retention_hours | 24 | 1–720 horas; validade das novas candidatas desde criação |

Todo request reservado conta, incluindo falha e resultado incerto. Polling não reserva nem gera. Limites medem quantidade, não custo faturado. Referência de preços on-demand Oregon consultada via AWS Price List API em 2026-10-09: Core US$0,04/imagem, SD3.5 US$0,08, Ultra US$0,14; sem impostos/armazenamento. Esses valores não são cobrança observada nem garantia de preços futuros.

## Integração e modelos

Uma chamada **Bedrock Runtime InvokeModel**, saída PNG, uma imagem, prompt estruturado e instruções visuais versionadas. Sem chamada adicional ao modelo textual para redigir prompt, sem Responses/image_generation, sem fallback. Core é default econômico; trocar entre os três adapters documentados não exige código. Modelo de outra família, nova versão ou outra região requer validar documentação/adapter/allowlist antes de disponibilizar; URL arbitrária e modelo textual não são aceitos como configuração de imagem.

Região/modelo/proporção/timeout/seed/provedor/versão das instruções são congelados na fila, permitindo auditoria e execução consistente mesmo após mudança no painel. Regeneração cria request/seed distintos e alterna direção visual. Uso é registrado somente se retornado; o contrato usual Stability não reporta tokens/custo. ID de rastreamento vem de `x-amzn-requestid`.

Fontes oficiais: [Core](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-diffusion-stable-image-core-text-image-request-response.html), [SD3.5](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-diffusion-3-5-large.html), [Ultra](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-diffusion-stable-ultra-text-image-request-response.html), [autenticação Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started-api-keys.html). O acesso da conta/token precisa ser homologado separadamente; disponibilidade do catálogo não prova invocação. Nova Canvas v1 retornou end-of-life em consulta AWS. gpt-oss-20b é textual e não gera imagens.

Produção foi consultada posteriormente em modo somente leitura: agentes usam Bedrock Mantle us-east-1 / openai.gpt-oss-20b. DEV textual foi alinhado ao mesmo endpoint/modelo a pedido do usuário. Isso não altera a região específica de geração de imagens nem comprova acesso ao Runtime/Oregon. Essa consulta/alinhamento não alterou a aplicação produtiva nem iniciou inferência. Posteriormente, consumo DEV foi autorizado; duas solicitações Core concluídas no ambiente local foram confirmadas no fechamento. Avaliação visual sistemática e acesso produtivo continuam pendentes.

## Configuração e execução local

Python >=3.10; worktree usa `.venv` Python 3.11 preservando o ambiente original.

1. Aplique migrations com role migradora: `python -m ops.scripts.migrate_with_role`. `admin_ops.0022` cria fila/grants; `0023` adiciona parâmetros, provedor/snapshot e grant de atualização de configuração para FastAPI. A migration preserva jobs antigos como provider OpenAI; eles falham explicitamente como unsupported_provider, sem reinterpretar/repetir uma chamada paga.
2. Configure API/worker com banco local. Para testes automáticos, use banco isolado e mocks, nunca credenciais/provedor real.
3. Credencial do executor: `AWS_BEARER_TOKEN_BEDROCK` em `.env.thumbnails.local` (0600, ignorado). Não enviar ao navegador nem colocá-la nos parâmetros do banco. O worker carrega `.env`, `.env.api.local`, `.env.thumbnails.local`; variáveis já injetadas prevalecem. DEV já tinha uma credencial Bedrock; nenhuma credencial foi copiada de produção.
4. Somente após autorização explícita de consumo/homologação, habilite `GTL_THUMB_ENABLED=1` na API e worker **e** `thumbnail_enabled=true` no painel. Sem ambas as condições, novas solicitações/claims ficam pausadas. Status/preview de trabalhos existentes continuam disponíveis.
5. Inicie `.venv/bin/python -m apps.api.backend_api.thumbnail_worker`. `--once` processa um ciclo; `--prune` recupera/limpa sem inferência. Modo contínuo reivindica uma por vez a cada 3s, com cleanup a cada 300s; múltiplos workers usam SKIP LOCKED/fencing.

| Ambiente operacional | Default | Papel |
|---|---|---|
| GTL_THUMB_ENABLED | 0 | Kill switch prevalece sobre painel |
| GTL_THUMB_LEASE_SECONDS | 300 | Mínimo efetivo: timeout congelado +60s |
| GTL_THUMB_CLEANUP_SECONDS | 300 | Intervalo de limpeza |
| GTL_THUMB_PRIVATE_ROOT | .runtime/thumbnail_private | Arquivos privados |
| GTL_THUMB_PUBLIC_ROOT | media/market_thumbnails | Promoção validada |

`GTL_THUMB_OPERATOR_LIMIT`, `MARKET_LIMIT`, `GLOBAL_LIMIT`, quando explicitamente presentes, são tetos adicionais: mínimo entre ambiente e banco. Omita para controlar cotas só pelo painel. Variáveis antigas ORCHESTRATOR/IMAGE_MODEL/MAX_OUTPUT_TOKENS/PERIOD_HOURS/RETENTION_HOURS/TIMEOUT_SECONDS não configuram mais a geração; remova-as e use os parâmetros persistidos.

O launcher local `.runtime/dev/start.py` usa kill switch 0 por padrão e lê o override ignorado `.env.thumbnails.local` para API e worker. Em 2026-10-09, após autorização explícita de consumo no DEV, esse override passou para `GTL_THUMB_ENABLED=1`; API e worker foram reiniciados, com habilitação persistida do painel também true. Para pausar localmente, volte o override para 0 e reinicie ambos. Salvar parâmetros ou marcar habilitação administrativa sozinho não remove o kill switch. O launcher aceita nomes de serviços para reinício seletivo, por exemplo `.venv/bin/python .runtime/dev/start.py api thumbnail-worker`, depois de parar os processos anteriores.

## Produção, somente após autorização

Compose versionado contém worker dedicado no profile `thumbnails`, separado do daemon de fechamento/resolução/comunicações. Segredo do executor em `.env.thumbnails.prod` (modelo `.example`, 0600, ignorado); não exposto ao Django/proxy. Em 2026-10-09, com autorização explícita, CreateFoundationModelAgreement habilitou o acordo de acesso do Core `stability.stable-image-core-v1:1` em us-west-2; GetFoundationModelAvailability confirmou agreement/entitlement/region AVAILABLE e authorization AUTHORIZED. Não foram feitos deploy, alteração de IAM/credenciais, geração paga ou habilitação da aplicação. A disponibilidade da conta não comprova acesso com o token Runtime da aplicação; modelos alternativos precisam de verificação própria.

`thumbnail_private`: volume worker RW/FastAPI RO, não montado em Django/proxy. Dockerfile prepara diretório privado 0700, PNGs 0600, mesmo UID runtime. FastAPI monta mídia global RO e somente subpath `market_thumbnails` RW para promoção; worker usa mesmo subpath para prune. Compose exige suporte `volume.subpath` e diretório existente no volume original. Antes de iniciar, role migradora prepara `/app/media/market_thumbnails` com owner runtime correto; preservar mídias existentes e conferir mounts/permissões no host.

Rollout futuro autorizado: backup; migrations/grants; volumes/UID; credencial e acesso específico Runtime/Oregon/modelos (incluindo política/assinatura AWS Marketplace quando exigida); iniciar API e `docker compose -f ops/deploy/production/docker-compose.yml --profile thumbnails up -d thumbnail-worker`; homologar uma chamada paga autorizada, prévia protegida, revisão/salvamento/publicação; liberar kill switch/painel. Nunca usar geração paga como teste automático de disponibilidade.

## Diagnóstico, retenção e rollback

Eventos thumbnail.request/running/succeeded/failed/uncertain/apply e thumbnail.settings_update reutilizam auditoria existente. Mudanças de configuração guardam ator e antes/depois dos campos não secretos. Jobs registram snapshot/hash, provider/modelo/parâmetros/seed, versão, tempos, claim/lease, ID/uso retornado e aplicação. Logs não contêm credenciais, base64, notas privadas ou corpo de erro do provedor.

| Estado/código | Ação |
|---|---|
| queued | Conferir worker, kill switch/painel e DB; sobrevive reinício |
| running | Não reenviar/resetar chamada ativa |
| abandoned/lease_expired/uncertain | Resultado desconhecido; nunca repetir automaticamente. Nova tentativa deliberada pode gerar novo consumo |
| unsupported_provider/unsupported_instructions | Job legado não será convertido; nova solicitação após habilitação autorizada |
| provider_access/missing_credentials | Conferir token/permissão/região/modelo/assinatura; sem fallback |
| invalid_configuration | Conferir adapter/snapshot; não editar jobs para repetir |
| content_refusal/provider_rejected/provider_inference | Falha confirmada; nova tentativa somente deliberada |
| invalid_image/incomplete_response/invalid_response | Validar contrato e arquivo; preservar imagem anterior |
| storage_failed | Conferir mount, UID, espaço; preservar imagem anterior |
| ineligible | Mercado/sessão/operador não elegível ou job expirado |
| 409 na confirmação | Conflito de versão/imagem/candidata; não sobrescrever |

Prune preserva arquivos ativos/vinculados e auditoria/cotas. Candidatas expiram conforme snapshot (24h default); imagens públicas vinculadas não expiram. UUIDs órfãos privados/públicos ficam sujeitos a graça de 1h e lock compartilhado promoção/prune. Nunca sobrescrever arquivos publicados. Sessão expirada exige reautenticação; consultar status não dispara nova chamada. Resultado tardio nunca altera mercado automaticamente. Falha de publicação após salvamento informa o resultado real, sem alegar rollback.

Upload manual e resposta perdida: Django consulta o mercado pela API usando slug informado/conhecido. Se a URL confirmar o vínculo, informa rascunho salvo sem executar a ação seguinte; caso a consulta falhe/não confirme (inclusive novo mercado sem slug conhecido), mantém o arquivo e orienta conferir o mercado antes de reenviar. Só compensa erro local anterior ao envio ou rejeição 4xx confirmada, excluindo 408/499. Arquivos manuais conservados por resultado desconhecido não entram no prune UUID: qualquer remoção exige antes verificar todos os vínculos pela autoridade backend e ausência de gravação em andamento. Não presumir rollback, nem reenviar automaticamente para reconciliar. Na decisão inline, um campo inválido não interrompe o acompanhamento da geração.

Validação Docker inclui `docker build --check .` no CI de código. Em 2026-10-09 o check passou; build completo e ensaio de escrita em volumes isolados ficaram bloqueados por falta de espaço no Docker Desktop, respectivamente `No space in /var/cache/apt/archives` e `No space left on device`. Não foram apagados caches/imagens/volumes existentes de outras iniciativas. Repetir build completo e ensaio dos mounts/UIDs em ambiente com espaço antes do rollout.

Pausa rápida: desmarcar thumbnail_enabled no painel; claims/novas solicitações param, chamadas já em andamento podem concluir. Kill switch operacional: GTL_THUMB_ENABLED=0 na API/worker e reiniciar. Upload/manual/image_url seguem funcionando. Rollback: parar worker/desabilitar, preservar fila/arquivos/migrations; não reenfileirar uncertain nem reverter migrations com dados vinculados.

## Validação sem custo

```sh
.venv/bin/python ops/scripts/test_mcp_local.py --db-admin-env /caminho/local/.env.db-admin.local --database gtl_mcp_thumbnails tests.test_thumbnails
.venv/bin/python tests/thumbnail_browser.py
.venv/bin/python packages/contracts/export_openapi.py --check
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
node --check apps/web/static/js/gotrendlabs.js
```

Browser usa template/CSS/JS reais, HTTP simulado e Chrome local, com Playwright de testes. Screenshots/logs em `.runtime/thumbnail-browser` e `.runtime/thumbnail-validation`. Acesso efetivo Core/token validado no DEV por duas solicitações succeeded; não generalizar para produção/modelos alternativos. Homologação visual pendente: identificação do assunto, interesse/neutralidade/recorte, regenerações diferentes e latência/uso reais. Fixtures comprovam interface e recorte, não qualidade do modelo ou aumento de cliques.

## Fechamento e manutenção do rollout

O deploy padrão prepara somente `/app/media/market_thumbnails` com o UID/GID runtime antes do mount `volume.subpath`, sem sobrescrever imagens ou alterar seus owners. Se `.env.thumbnails.prod` existir, ativa o profile `thumbnails` em build, parada dos escritores, migration e restart. A presença do arquivo controla o ciclo do serviço, não autoriza inferência: kill switch e configuração persistida continuam necessários. Manter o arquivo em rollback/pausa para atualizar o worker nos próximos deploys; não remover o profile enquanto houver executor antigo ativo. Migration que falhar deixa também o executor parado para recuperação explícita.

PR deve passar no CI completo, incluindo build da imagem. Após merge, acompanhar o Actions e SSM até Success; conferir SHA servido, migrations 0022/0023, grants, mounts/UIDs, segredo worker-only, fila e switches API/worker/banco. Validar leitura/escrita dos mounts com arquivo efêmero próprio e remover apenas esse arquivo. Não alterar mercados existentes para smoke. Antes de habilitar, conferir trabalhos queued/running: a habilitação pode processar a fila automaticamente. Smoke sem custo não comprova invocação; consumo produtivo exige autorização explícita. Avaliação visual e inferência produtiva ficam pendentes se não realizadas.

Estado na preparação: duas gerações Core reais concluídas no DEV; CI remoto e rollout ainda não executados. Preservar a branch local após merge. Artefatos de mídia DEV, envs, credenciais, screenshots e logs locais não entram na PR.

Migration 0024_thumbnail_runtime_defaults mantém inicialização SQL existente de SiteConfig compatível, com defaults do banco conservadores e geração off. Incluí-la no rollout junto às migrations 0022/0023.

## 2026-10-09 — Fechamento técnico e rollout de thumbnails

PR #143 integrada, merge 15b980585982cfa6706a38d57016614a41ba956d. CI final 408 testes aprovados/1 skip por roles CI, build completo aprovado. Actions 37963430113 e 37964971891 Success (PR e main/produção), SSM deploy Success. Migrations 0022–0024 aplicadas; defaults SQL preservam inicialização existente. Executor dedicado/grants/mounts/UIDs verificados: worker privado RW, API privado RO/subpath público RW, sem candidatas no proxy/Django. Arquivo efêmero próprio removido.

Habilitação produtiva de thumbnails autorizada e concluída: banco e GTL_THUMB_ENABLED=1 na API/worker, Core/Oregon/3:2/180s, limites 10/5/50 por 24h e retenção 24h. Configuração preservada, alteração auditada como operação de sistema; backups de envs 0600 no host. Fila vazia antes/depois, nenhuma chamada paga iniciada, nenhum mercado editado pelo assistente. Site/API HTTP 200 e configurações anônimas 401. Branch local preservada.

Fechamento técnico concluído; homologação de fluxo autenticado/MFA, consumo produtivo e qualidade visual real permanece pendente. Não afirmar inferência real validada em produção. Fonte externa atual: [PR #143](https://github.com/wscardua/gotrendlabs/pull/143) e [Actions](https://github.com/wscardua/gotrendlabs/actions/runs/37964971891). Registros anteriores descrevem etapas históricas, substituídos por esta atualização para estado operacional atual. Evidência documental pós-rollout preparada localmente para versionamento na próxima PR aprovada.


## Diagnóstico: queued com container ativo

Container ativo e switches habilitados não garantem processamento. Em 2026-10-09 a primeira solicitação produtiva ficou queued porque o evento de claim importava main e exigia pepper/TOTP no worker. Corrigir a dependência para admin_events; não copiar segredos HTTP para o executor. Conferir tempos/estado/provider_id e logs, sem imprimir credenciais ou snapshot privado. Probes de claim/auditoria devem dar rollback antes de qualquer provider I/O. Regressão usa subprocesso em modo production sem segredos HTTP, banco isolado e provedor simulado. A correção local aguarda publicação autorizada; recuperação usa a mesma solicitação queued, nunca replay de running/uncertain.


## 2026-10-09 — Recuperação produtiva do executor

Incidente resolvido pela PR #146/main b033afe4, CI PR37981039913 e main37981803447/build/deploy Success (443 testes, um skip de roles CI). SSM deploy3e165a28 e verificação0d584e9f Success: auditoria do worker sem main, serviços ativos. Pedido original cdbe1f42-d75b-44ec-8f0c-11ece3d6952e succeeded em 6.451679s de processamento, arquivo privado presente e ID de provedor registrado; sem nova solicitação/replay pelo assistente ou salvamento/publicação do mercado. Primeira execução Core produtiva iniciada pelo operador confirma acesso efetivo do token/modelo, mas não avaliação visual ou custo faturado. [Evidência externa](https://github.com/wscardua/gotrendlabs/pull/146). Recibo atualizado localmente para próximo versionamento autorizado.


## Relevância do assunto

A montagem v3 coloca pergunta/resumo antes do estilo e inclui pistas de cena quando o contexto identifica futebol ou CS2. Categoria não substitui o assunto. Jobs v2 mantêm o prompt histórico. Não reenfileirar jobs finalizados para aplicar a nova versão; Gerar outra cria identidade nova e consome a cota normal. Avaliar as novas imagens com o operador antes de considerar o aceite visual concluído. Não trocar modelo como diagnóstico automático: exemplos Ultra v2 também falharam semanticamente. V3 ainda não implantada nesta etapa.


2026-10-09 — Etapa histórica v4, substituída pela v5: prompt market-thumbnail-bedrock-v4 sem temas, entidades, cenas ou condicionais fixos por categoria. Pergunta/resumo/classificação atuais determinam o assunto; regras fixas somente de composição, qualidade, neutralidade e segurança. Substitui a proposta local v3 de âncoras temáticas, rejeitada pelo usuário. Executor DEV reiniciado com fila vazia, PID82614; imagens/estados v3 existentes preservados, sem reinterpretar/repetir solicitações. V3 queued não chama provedor (unsupported_instructions); v2 histórico preservado. Produção e modelos não alterados; sem nova inferência paga. Validação v4: 70 testes de thumbnails/badges aprovados em 102.686s com PostgreSQL isolado/provedor simulado; rechecagem dos 6 testes do provedor aprovada em 0.053s, incluindo invariância do template entre temas, contexto completo e rejeição de v3 sem invocação. Django check, compilação Python e diff aprovados. Nenhuma inferência paga iniciada; qualidade real permanece pendente de avaliação pelo operador. Log thumbnail-dynamic-tests.log e thumbnail-dynamic-provider-tests.log em .runtime/badge-validation.


## Fluxo semântico v5 (direção vigente)

Substitui templates v3/v4: um modelo textual entende o mercado e escreve o conceito visual; o modelo de imagem configurado renderiza esse conceito. São uma chamada textual e uma imagem por solicitação. Não há regras temáticas por categoria, exemplos de esportes/jogos ou alteração nos agentes de comentários/badges. Operador continua usando Gerar/Gerar outra e salvamento existente.

No ambiente não secreto da API que reserva jobs (.env.prod compartilhado com worker em produção; .env/.env.api.local no DEV), configurar GTL_THUMB_PLANNER_MODEL=openai.gpt-oss-20b (alternativa explicitamente selecionável openai.gpt-oss-120b), GTL_THUMB_PLANNER_REGION=us-east-1, GTL_THUMB_PLANNER_TIMEOUT_SECONDS=45 (10–120) e GTL_THUMB_PLANNER_MAX_OUTPUT_TOKENS=2048 (512–4096). Restart API para alterar configurações ambientais; jobs já enfileirados usam snapshot. Configurações do Sistema continuam escolhendo o modelo de imagem. Não editar parâmetros de comentários para modificar thumbnails. Não colocar credencial na API: AWS_BEARER_TOKEN_BEDROCK somente no executor. Token precisa autorizar Mantle/CreateInference além de Runtime/InvokeModel; disponibilidade documental não comprova acesso real.

Cotas existentes limitam igualmente a quantidade de planejamentos: cada reserva permite até uma chamada textual limitada e uma imagem, inclusive em falha. Uso em usage.planner/usage.image é reportado pelo provedor, nunca custo faturado estimado. Retenção de candidatas24h e política de mídia existentes preservadas. Checkpoints persistem brief final/sujeitos/IDs/uso, não raciocínio privado, e não são expostos pelo endpoint de status ou logs. Regeneração usa o último brief bem-sucedido do mesmo contexto para buscar alternativa; nenhum replay automático.

Diagnóstico: planner_transport/planner_unavailable/incomplete_planner_response são uncertain; planner_access, planner_refusal ou invalid_visual_brief impedem imagem. Conferir planner.model, instruções e estado das duas etapas no registro administrativo do job sem imprimir credenciais, contexto privado ou base64. Running abandonado permanece uncertain, mesmo se somente a etapa textual ocorreu. Rollback: desligar recurso e parar reserva de novos jobs; jobs v5 não devem ser reinterpretados por código v2/v3/v4 nem reenfileirados. Candidatas existentes continuam preservadas. Sem migration ou contrato público novo.

Habilitação/qualidade real v5 requerem homologação do operador; esta alteração não faz inferência paga automaticamente. Antes de implantação, aprovar PR e CI conforme workflow.


## Homologação DEV e preparação de PRD v5

2026-10-09 — Homologação DEV v5: operador informou “em dev local parece estar legal” e autorizou preparar PRD. Consulta local somente leitura confirmou três jobs v5 succeeded (34ccb8f0, bcc57be2, 5cb97131), iniciados pelo operador, com planner openai.gpt-oss-20b/Mantle us-east-1 e imagem Core/us-west-2. Tempos de processamento: 17.804s, 9.663s e 15.883s; uso textual retornado registrado, sem afirmar custo faturado. Acesso efetivo e aprovação visual informal do fluxo DEV confirmados; não substituem matriz visual sistemática, medição de engajamento ou homologação do token/modelo em PRD. Nenhuma inferência paga iniciada pelo assistente. Próxima etapa: aprovação da descrição atualizada da PR, CI completo, merge/deploy e verificação produtiva; preservar modelo de imagem e políticas atuais de PRD.


2026-10-09 — Preflight PRD somente leitura: SSM3c6b5fda confirmou SHA b033afe4, seis serviços ativos e credencial Bedrock presente no executor (valor não exposto), switch ambiental 1, defaults textuais 20b/us-east-1. Consulta inicial da política precisou ser corrigida por uso inadequado do context manager; SSM8f95b96a concluiu Success sem stderr: thumbnail_enabled=true, Core/stability.stable-image-core-v1:1, us-west-2, 3:2, timeout180s, limites operador50/mercado50/global50 por24h e retenção24h; nenhum queued/running. Valores atuais substituem o recibo histórico de defaults10/5 no que se refere à configuração efetiva observada, sem alterar os defaults da spec. Preservar essas escolhas no deploy. Nenhuma mutação produtiva ou inferência; preflight não comprova acesso de inferência Mantle do token produtivo.
