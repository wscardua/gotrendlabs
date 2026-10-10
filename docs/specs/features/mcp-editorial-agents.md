---
id: FEAT-MCP-001
titulo: "MCP editorial e gestão de integrações de agentes"
versao: 1.5
status_spec: aprovada
status_impl: parcial
ultima_atualizacao: 2026-10-10
origem:
  - decisões do usuário na conversa de 2026-10-02 a 2026-10-07
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - agent-integrations.md
  - market-lifecycle.md
contratos_revisados:
  - market-lifecycle.md
  - domain-events.md
  - integrity-ledger.md
dependencias:
  - FEAT-AUTH-001
  - FEAT-EDITORIAL-001
  - FEAT-MARKET-001
  - FEAT-OPSLOG-001
impacta:
  - backend-api
  - database
  - admin-ops
  - integrations-mcp
  - deployment
aprovacao: escopo e recomendações aceitos pelo usuário; consolidação solicitada em 2026-10-07
---

# MCP editorial e gestão de integrações

## Revisão 1.5 — documento editorial único (2026-10-10)

Novos drafts MCP enviam `editorial_record.document` como texto de até 60.000 caracteres, com política versão/hash. O documento reúne contexto e busca de duplicidade; pergunta, regras e prazos; URLs, datas de consulta, extratos e origem dos relatos; contingências e responsável; pendências e conclusão. O agente relata pesquisa e limitações, sem declarar conferência humana. O documento é a única fonte editável da nova ficha; campos estruturados E01–E11 continuam aceitos somente para clientes legados e preservados nos snapshots existentes. Não combinar os formatos no mesmo payload.

Admin Ops mostra esse documento em um textarea, uma confirmação humana e a decisão. Ao abrir ficha antiga, a API monta projeção textual determinística com todos os valores registrados e dados atuais do mercado; a projeção não regrava o snapshot antigo. Uma nova avaliação humana salva o texto como novo registro versionado. Aprovação exige documento não vazio, política atual, confirmação explícita, revisão/hash atuais e demais condições objetivas de publicação. Devolver/rejeitar não exigem confirmação. A suficiência factual é responsabilidade do revisor; o sistema não interpreta semanticamente o texto nem apaga lacunas por marcar a confirmação. Parecer e publicação seguem ações separadas; o gate universal permanece.

As seções antigas abaixo descrevem o contrato legado aceito durante transição. E01–E11 continuam orientação editorial, sem onze controles no parecer novo.

## 1. Objetivo e estado

Oferecer acesso controlado por MCP às APIs do GoTrendLabs para agentes externos pesquisarem oportunidades e prepararem drafts editoriais. A FastAPI continua como autoridade, sem acesso direto do agente/MCP ao PostgreSQL. Implementação integrada pela PR #136, deploy Actions aprovado e MCP habilitado em produção. [Rollout/HTTPS/grants/isolamento](../testing/mcp-production-rollout-20261007.md) conferidos; [fechamento local](../testing/mcp-closeout-20261007.md) e CI com 369 testes aprovados. Homologação Dot real e piloto autenticado continuam pendentes.

Dot da OpenAI é o primeiro executor-alvo; outros executores devem poder reutilizar os contratos. Suporte a OAuth interativo E credenciais de serviço integra o escopo completo, mesmo que entregue em etapas. O produto é educativo, sem dinheiro real; preservar regras do editorial aprovado e integridade dos mercados publicados.

## 2. Decisões fechadas

- Staff e superusers ativos com MFA têm a MESMA permissão de gestão de todas as integrações nesta fase. Não implementar exclusividade de superuser nem isolamento por proprietário. Responsável é atribuição/auditoria, não limite de visibilidade administrativa.
- Somente contas administrativas gerenciam integrações; agente e usuário comum nunca gerenciam permissões, credenciais ou cotas.
- Separação futura por papel/responsável é sugestão, não requisito desta entrega.
- Integrações possuem identidade técnica, responsável humano, permissões explícitas, validade, limites e revogação.
- MCP só acessa FastAPI por contratos autenticados. Não importar ORM, conexão SQL ou gravador de logs que abre banco no processo MCP.
- Reutilizar logs centralizados e eventos administrativos; não criar um sistema paralelo de logs.
- Pesquisa, agenda e consumo LLM pertencem ao executor externo. Não executar pesquisa longa dentro do daemon operacional.
- Publicação, resolução, cancelamento, wallet, usuários, previsões, comentários, destaque e criação/alteração de taxonomia não são ferramentas do agente.
- A revisão humana permanece necessária operacionalmente. Esta feature não autoriza publicação automática. Desde a revisão 1.4 solicitada pelo usuário, todos os mercados exigem parecer humano aprovado para a versão atual antes de publicar.

## 3. Base existente e adaptação necessária

Referências de implementação que precisam ser relidas no checkout usado para implementar:

- `apps/api/backend_api/main.py`: sessão/MFA, handlers de mercados, dashboard e logs. Criação administrativa faz upsert de taxonomia e aceita destaque; edição não se restringe a drafts. Não expor esses payloads diretamente.
- `apps/api/backend_api/security.py`: primitivas de token aleatório e hash; reutilização condicionada à finalidade e testes.
- `apps/web/django/system_logs/{models,services,logging}.py`: log central, contexto JSON, redaction e retenção. Gravação técnica abre conexão própria e tolera falhas.
- `apps/api/backend_api/admin_events.py`: evento de domínio usa cursor da transação.
- `apps/web/django/markets/models.py`: autoria de mercados e eventos ligada a usuários; ainda falta identidade de integração estruturada.
- `docs/editorial/criteria-v1.2.json` e documentos editoriais: fonte aprovada E01–E11. Não reintroduzir cotas temáticas obrigatórias de materiais auxiliares antigos.
- `apps/api/backend_api/agent_services.py`: bots oficiais de comentários/previsões são outra feature. Não reutilizar suas permissões ou converter a integração em bot staff.
- `ops/deploy/production/{docker-compose.yml,Caddyfile}`: ainda sem serviço/rota MCP.
- Workflow de analytics registra validação produtiva pendente: confirmar estado real; não tornar analytics nova dependência obrigatória nem declarar deploy realizado.

Extrair serviços backend compartilhados de draft, sem duplicar SQL/regras no adaptador. Proteger também operações humanas concorrentes que atinjam o mesmo draft. Preservar payloads web/mobile existentes sempre que possível.

## 4. Arquitetura e autenticação

Fluxo: executor → MCP remoto HTTPS/Streamable HTTP → FastAPI → PostgreSQL. Admin Ops Django → FastAPI. Novo processo sugerido: `apps/mcp/`, com cliente HTTP explícito, schemas tipados e timeouts. Organização física pode ser ajustada ao repo, preservando essas fronteiras.

FastAPI administra integrações, credenciais, grants, tokens, cotas, drafts e auditoria. OAuth usa biblioteca/provedor mantido e compatível com MCP; não escrever primitivas criptográficas/protocolo do zero. Registrar escolha concreta e versão no ADR durante implementação.

### OAuth interativo

Login GoTrendLabs e MFA, consentimento com integração/scopes visíveis, autorização por código com PKCE S256, redirect URIs exatas, código curto de uso único, state no cliente e validação de issuer/audience conforme padrão vigente. Implementar descoberta necessária para o cliente, refresh tokens com rotação e detecção de reutilização, revogação e armazenamento seguro. Login social existente NÃO é servidor OAuth para MCP. Cadastro de cliente OAuth não concede acesso a dados sem consentimento administrativo.

A conexão vincula grant, integração e usuário que consentiu. Revalidar conta ativa e administrativa, grant, integração e escopos; perda de papel administrativo ou desativação invalida grants do usuário. Integração perde acesso quando seu responsável perde elegibilidade, até transferência explícita auditada para responsável elegível.

### Serviço

Admin Ops oferece gerar credencial. FastAPI gera segredo de alta entropia, persiste apenas hash e metadados, e retorna valor uma vez em resposta `private, no-store`. Nunca usar senha humana/TOTP. ID de integração/credencial é público e não autentica sozinho. Executor guarda segredo em secret manager e troca por access token curto pelo fluxo de serviço documentado. Distinguir credencial de serviço de client secret OAuth.

Credenciais têm expiração, identificador, último uso e revogação própria. Rotação exige nova credencial e retirada explícita da antiga; admitir transição curta visível, sem segredo recuperável. A interface informa que gerar outra não revoga a anterior automaticamente. Revogação da antiga invalida também tokens derivados dela.

### MCP → FastAPI

Token destinado ao MCP não deve ser repassado como token de outra audience. Usar autenticação de workload do adaptador e validação/troca interna pela FastAPI, com ator e scopes derivados do grant validado, nunca de IDs/scopes fornecidos livremente pelo modelo. Workload MCP sozinho não recebe autoridade de editar drafts: mutações exigem contexto de delegação validado. Tokens internos não ampliam permissões nem prazo do grant original. Definir e testar audience, issuer e revogação nos dois trechos.

## 5. Gestão administrativa

Seção “Integrações e agentes”: lista, detalhe, criação/edição, conexões OAuth, credenciais, permissões, limites e atividade. Campos: ID estável, nome, descrição, responsável, estado, validade, escopos, cotas, último uso. Não mostrar hash/segredo armazenado. Criação e transferência de responsável usam seleção por nome/@usuário carregada da API, sem digitação de ID; backend revalida elegibilidade na mutação. Validade usa seletor nativo de data/horário com precisão de minutos e fuso explícito America/Sao_Paulo; Django converte o instante da API para exibição local e envia offset na gravação, preservando a validação autoritativa da FastAPI.

Estados persistidos: ativa, pausada, revogada; expirada é condição efetiva de validade vencida. Criar pausada por padrão; ativação explícita. Pausa é reversível; revogação terminal exige nova integração. Credenciais e grants também têm revogação própria. Excluir fisicamente integração histórica não faz parte do MVP.

Todos os gestores administrativos possuem a mesma capacidade nesta versão, inclusive transferir responsável. Operações web usam CSRF e sessão MFA. Emissão/rotação/revogação e mudança de permissões/limites geram evento administrativo. UI tem estados vazio, carregamento, falha da API e confirmação clara para revogação. Sem fallback mutável pelo ORM Django.

Revogação e pausa bloqueiam novas operações e mutações ainda não autorizadas no ponto transacional de gravação. Serializar a disputa entre autorização da mutação e revogação: se a mutação venceu o lock e confirmou antes, permanece; se revogação venceu, negar. Não prometer desfazer efeitos nem interromper automaticamente a pesquisa externa. A página diferencia “bloquear acesso ao GoTrendLabs” de “pausar o Dot”.

## 6. Ferramentas e dados mínimos

Catálogo normativo em [agent-integrations.md](../contracts/agent-integrations.md). Toda ferramenta tem schema de entrada/saída, limite de tamanho, escopo e erros estáveis. Sem ferramenta genérica de SQL, HTTP arbitrário, shell ou proxy de toda a API. Anotações MCP ajudam o cliente, mas não substituem autorização.

Busca inclui drafts visíveis para deduplicação em projeção mínima; editar continua limitado aos drafts da própria integração. Não expor fichas privadas de outras integrações, PII, participantes individuais, emails, sessões, logs gerais, wallets ou dashboard inteiro. Consultas paginadas devem informar cursor e completude; não declarar catálogo integral quando truncado.

Sinais editoriais agregados mostram período, momento da consulta, disponibilidade e separação humano/bot. Ausência não vira zero. Deduplicação combina texto, evento/assunto e janela temporal; semântica é sugestão, nunca prova absoluta. Não é necessário introduzir vector DB no MVP.

## 7. Drafts e ficha editorial

Criação com taxonomia existente e disponível; campos permitidos: pergunta, resumo, tipo, opções, fontes, critério, encerramento/timezone e ficha. Probabilidades iniciais e campos visuais/defaults são determinados pelo backend. Não exigir que o agente invente volume, participantes ou cor. IDs são referências estáveis; slug é legível, derivado do título, com sufixo numérico em colisão e estável durante edições do agente. Slug não é identidade de idempotência.

Persistir autoria técnica separada do humano responsável. Ficha estruturada contém snapshot/revisão do draft, versão/hash do editorial, justificativa resumida, sinais internos/externos, pesquisa de duplicidade, evidências E01–E11, fontes de descoberta/resolução, data/hora de consulta, trecho/dado relevante, fallback, lacunas e parecer humano. Não armazenar raciocínio interno do modelo. Evidências são relatos com origem identificada: backend não deve chamar um relato do agente de verificação independente.

Estado editorial separado de `market.status`: preparação → em revisão → aprovado/devolvido/rejeitado. Submeter exige draft completo estruturalmente e cria snapshot. Agente não edita em revisão, aprovado ou rejeitado; devolução humana reabre edição. Edição humana invalida aprovação anterior e cria nova versão; alteração relevante de critérios exige nova revisão. Toda edição usa versão esperada. Agente só altera draft próprio em preparação/devolvido; publicado/scheduled nunca editável pelo agente.

Aprovação é humana e deve referenciar revisão/hash; pendência obrigatória impede parecer “aprovado”. Texto pode ser avaliado sem fonte, mas E06/E08 não podem receber verificação fictícia. Datas devem conter offset válido, timezone controlado e fechamento anterior ao anúncio esperado quando aplicável. Armazenar instante em UTC e exibir timezone explícito.

Publicação continua humana no MarketLifecycleEngine. Desde a revisão 1.4 solicitada em 2026-10-07, todo mercado exige state=approved, decisão humana approved vinculada à revisão/hash atuais, política vigente sem pendências e conteúdo correspondente ao snapshot aprovado. Preparação, revisão pendente, devolvido/rejeitado, parecer antigo ou edição posterior bloqueiam com 409 editorial_approval_required. Mercado humano também possui ficha; sua ausência bloqueia. Configuração de fechamento incompleta bloqueia com 422 closure_configuration_invalid. Lock mercado→ficha é compartilhado entre edição, parecer e publicação; nenhum caminho de agendamento pode contornar a regra central. Salvar alterações invalida aprovação; publicar a versão aprovada é ação separada, sem salvar o formulário.

Ficha/evidências não são armazenadas apenas em `admin_notes`, logs técnicos ou repo público. Persistir em domínio privado com histórico de revisões preservado enquanto o mercado existir. Não copiar arquivos arbitrários ou conteúdo completo de páginas; guardar URL, metadados e extrato mínimo necessário. Downloads/imagens automáticos ficam fora do MVP.

## 8. Atomicidade, cotas e retries

Idempotência obrigatória em criações, edições e submissões: chave por integração/operação + hash canônico do payload, resultado e referência de recurso persistidos. Mesmo conteúdo retorna resultado original sem novo evento de domínio/cobrança; conteúdo diferente com mesma chave retorna conflito. Autorização atual deve ser verificada antes de devolver resposta idempotente. Chave e resposta não carregam segredos. Manter por pelo menos 30 dias; documentar janela ao cliente.

Quota de drafts novos consome somente transação confirmada. Limite de chamadas contabiliza tentativas autenticadas; duplicatas idempotentes podem consumir chamada, mas não draft. Persistir contadores/reservas no PostgreSQL via FastAPI, com incrementos atômicos por integração. Não reutilizar dicionário em memória como quota autoritativa. Limitar também tentativas não autenticadas por mecanismo de borda/backend que não dependa de identidade declarada.

Defaults de engenharia configuráveis: 5 drafts/dia (São Paulo), 60 chamadas/minuto e 2 chamadas concorrentes por integração; integração inicialmente pausada. Access token 10 minutos, credencial de serviço 90 dias, grant/refresh OAuth com prazo absoluto inicial de 90 dias (sem renovação infinita). Registrar ajustes justificados por interoperabilidade no ADR sem ampliar privilégios. Redução de quota já ultrapassada bloqueia novos consumos, sem apagar histórico.

Concorrência usa leases com expiração/recuperação; queda de processo não prende cota para sempre. Timeouts explícitos e retry com backoff/jitter somente quando seguro; respeitar `Retry-After`. Idempotência, quota de criação, draft e evento de domínio compartilham transação. Locks em ordem estável e curta; nenhuma navegação/LLM enquanto mantém transação aberta.

## 9. Logs e auditoria existentes

Usar `gotrendlabs_system_logs` para chamadas, leituras, falhas, limites e bloqueios; `gotrendlabs_admin_events` para mutações de domínio e gestão. Preservar eventos de autenticação onde pertinentes. Ampliar autoria/correlação estruturada dos eventos administrativos, sem atribuir ação automática como se fosse feita manualmente pelo responsável.

Eventos técnicos sugeridos: `mcp.tool.started/completed/failed/denied`, `mcp.auth.failed`, `mcp.quota.exceeded`. Contexto inclui integração, credencial/grant por ID, execução, chamada, ferramenta, recurso e resultado de negócio. HTTP 200 com erro MCP é falha. Separar resultado relatado pelo executor de resultado comprovado pela API. `request_id` externo não concede confiança; emitir também identificador interno canônico.

Adaptador envia eventos por contrato interno restrito na FastAPI, com redaction, limites e autenticação de workload. A ingestão não aceita ator arbitrário como verdade nem permite ao agente publicar logs de outra integração. Backend produz eventos autoritativos de suas próprias operações. Deduplicar reenvio pelo ID de evento e diferenciar etapas MCP/API.

Não usar DatabaseLogHandler que abre banco no MCP. Em indisponibilidade da API: saída operacional sanitizada e reenvio limitado com fila/spool durável com TTL/tamanho máximo; documentar perda se capacidade esgotar, sem prometer captura perfeita. Falha no log técnico não quebra operação, conforme contrato atual. Falha na auditoria transacional aborta mutação.

Redaction por allowlist de campos; não basta regex de nomes para mensagens livres. Nunca persistir Authorization, cookies, segredo, código OAuth, refresh token, senha/TOTP ou respostas integrais. Nova credencial não vai para analytics/logs/cache. Retenção técnica existente é respeitada; ficha e auditoria de domínio têm ciclo independente. Adicionar filtros de integração/execução/ferramenta/resultado no log existente e índices adequados, conforme consultas reais.

## 10. Dot e executor externo

Dot é candidato documentado, NÃO integração já comprovada. OAuth é caminho preferido para ChatGPT/Dot; credenciais de serviço são para executores compatíveis. Não colocar segredos em prompts. Conectar somente ferramentas necessárias, sem acesso local ao computador/banco como requisito.

Radar: obter política atual → catálogo paginado e sinais → pesquisar → abrir fonte objetiva → preparar ficha/draft → submeter para humano → reportar IDs e pendências. Usar mercados futuros incertos, diversidade sem cotas obrigatórias, linguagem educativa e aviso cripto conforme editorial. Nova execução reconsulta política e estado; memória externa não é fonte da verdade.

Agenda e pausa do Dot são configuradas nele. Admin Ops exibe último acesso/resultados, não finge saber se o executor está ativo sem heartbeat. Não haverá SDK controlador do Dot, cancelamento remoto ou medição exata de custo LLM sem API documentada. Relatórios externos de pesquisa/custo são identificados como relatados. Desconectar não apaga dados já obtidos pelo executor.

Prova de compatibilidade obrigatória: OAuth, leitura, escrita autorizada de draft, chamada recorrente com renovação, revogação, quotas e logs. Falta de acesso ao Dot não bloqueia testes locais/outro cliente, mas impede marcar integração Dot como validada. Não substituir teste real por mock na evidência de homologação.

## 11. Segurança e operação

Conteúdo web, comentários e fichas são dados não confiáveis, jamais instruções para ampliar acesso. Renderizar com escape, restringir links/esquemas e tamanhos. MVP não busca URLs arbitrárias no MCP/FastAPI; executor pesquisa e entrega evidências. Qualquer futura busca backend exige proteção SSRF contra rede privada, loopback, metadata, redirects e DNS rebinding.

MCP tem ambiente próprio, sem DATABASE_URL, pepper, chave MFA, KMS ou env produtivo compartilhado. Limitar acesso de rede à API e dependências de autenticação necessárias. FastAPI continua única dona das gravações runtime; migrations por role separada, grants explícitos, sem enfraquecer fronteiras atuais.

Adicionar serviço isolado, rota HTTPS canônica `/mcp`, discovery OAuth público somente onde necessário, validação Host/Origin conforme protocolo, health/readiness sem dados privados e limites de body/timeout. Não cachear auth/respostas privadas. Confirmar suporte do proxy ao transporte escolhido. Testar localhost e domínio real; pin de dependências e versão MCP compatível com cliente alvo.

Rollout: migrations aditivas → API/Admin Ops → adaptador desativado por default → smoke → piloto. Kill switch geral bloqueia todas as integrações. Reversão desabilita rota/feature e revoga acessos, preservando drafts, ficha e histórico. Preparar deploy/runbook; executar produção somente quando o pedido de implementação incluir essa autorização.

## 12. Entregas e critérios de conclusão

A. Identidades, OAuth + serviço, gestão, logs e leitura.
B. Drafts/ficha/revisão, idempotência, concorrência e cotas.
C. Pacote/instruções para conectar executor e roteiro radar; validação externa real separada.

Todas as etapas compõem a feature; leitura apenas ou um único modo de autenticação é entrega parcial. Não desenvolver motor próprio de pesquisa/LLM como condição para atender Dot.

Testes obrigatórios estão em [mcp-editorial-acceptance.md](../testing/mcp-editorial-acceptance.md). Atualizar snapshot OpenAPI somente ao implementar contratos reais, migrations/grants, CI, docs e estado. Status deve distinguir implementada localmente, validada com cliente MCP, validada com Dot e implantada; sem evidência, registrar pendência.

## 13. Fontes verificadas em 2026-10-07

- [Dot: início, tarefas, apps, pausa e memória](https://help.openai.com/en/articles/20001530-getting-started-with-your-dot).
- [MCP personalizado no ChatGPT](https://developers.openai.com/api/docs/guides/custom-mcp-server).
- [Autenticação de plugins](https://developers.openai.com/plugins/build/auth).
- [Autorização MCP](https://modelcontextprotocol.io/specification/latest/basic/authorization).
- [Segurança MCP](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices).

As fontes sustentam os fluxos gerais; não comprovam disponibilidade de custom MCP com escrita no Dot de uma conta específica. Revalidar documentação/cliente durante implementação.

## Evidência de implementação local — 2026-10-07

Fatias A/B/C implementadas na branch `feature/mcp-editorial`, a partir de `origin/main` `9df08bc`, em worktree separado. Python 3.11, MCP SDK 1.30.0 e Authlib 1.6.12; justificativa e fontes oficiais no ADR. Ambos os modos de auth, UI/Admin Ops, domínio, migrations/grants, correlação e cliente MCP real local entregues. Ver [matriz de resultados](../testing/mcp-editorial-results.md) e [operação/piloto](../../guides/mcp-editorial-pilot.md). Deploy/HTTPS público/grants/isolamento comprovados no rollout da PR #136. Dot e recorrência externa ainda não comprovados; não marcar `implementada_validada` antes da homologação real.

### Retomada humana da preparação (v1.2)

Staff/superuser com MFA pode atualizar a ficha estruturada e reenviar mercado draft à revisão no Admin Ops, inclusive após edição humana que invalidou evidências. FastAPI registra ator humano, snapshot e nova revisão e limpa parecer anterior. Não depender do executor externo para retomar revisão humana. Aprovação/publicação seguem ações separadas e validações da v1.1.

### Simplificação da revisão humana (v1.3)

Conferir/ajustar ficha e registrar parecer ocorre em um formulário e uma ação humana, sem etapa obrigatória de reenvio anterior. FastAPI salva registro e decisão atomicamente e mantém snapshots, autoria, validações e publicação separada. Atestação independente não é pré-preenchida a partir do relato do agente. A UI v1.3 substitui a sequência operacional de dois formulários v1.2; endpoints anteriores continuam compatíveis.

### Identificação na lista administrativa de mercados

A lista Admin Ops identifica mercados vinculados à ficha de integração como “Gerado por agente IA via MCP”, apresenta o estado editorial separadamente do lifecycle e oferece link direto à revisão pelo editorial_market_id. Reutiliza os metadados administrativos FastAPI existentes, sem inferir origem pelo slug nem classificar mercados legados como humanos.

### Ficha humana com evidência editável

As fontes sugeridas aparecem junto da evidência de cada critério, editáveis pelo operador, sem repetir seletores de fontes por critério. Django converte URLs explicitamente citadas em índices do catálogo estruturado da ficha; FastAPI permanece responsável por validar fonte obrigatória/atestação humana, lacunas e integridade do parecer. A conferência de cada fonte ocorre uma única vez na ficha, separada do relato do executor. Pendências declaradas impedem aprovação mesmo com critérios marcados; a UI identifica o motivo e preserva decisão, marcações e texto após erro.

### Confirmação humana de lacunas resolvidas

Na mesma ação de parecer, o operador pode confirmar explicitamente que resolveu as lacunas e documentou a resolução nas evidências. A UI envia gaps vazio apenas com essa confirmação ou edição explícita do campo; sugestões e marcações de critérios não resolvem lacunas automaticamente. O texto original continua nas revisões históricas. Fontes, critérios, MFA, versão/hash, rollback e gate continuam validados na FastAPI.

O editor exibe bloqueio de publicação apenas em draft/scheduled sem parecer aprovado. Mercados publicados informam publicação já realizada e permitem consultar o histórico; cancelados informam cancelamento. O gate FastAPI permanece inalterado.

### Correção de interoperabilidade OAuth Codex

WFLOW-20261007-MCP-CODEX-OAUTH-001: registro dinâmico deve ignorar metadados desconhecidos (RFC 7591), preservando validação dos campos reconhecidos e sem autoridade derivada dos extras. Discovery deve conservar issuer textual exato entre resource metadata, AS e resposta iss. Correção da falha 422 Codex implantada pela PR #138; CI/main/deploy aprovados, CLI real atingiu autorização em produção. [Evidências](../testing/mcp-codex-oauth-20261007.md). Consentimento humano/piloto produtivo e homologação Dot continuam pendentes.
