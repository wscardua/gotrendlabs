# ADR-0011 — MCP editorial com autoridade FastAPI

- Data: 2026-10-07.
- Status: aceita; implementação/rollout produtivo ativos pela PR #136; homologação Dot pendente.
- Feature: [FEAT-MCP-001](../features/mcp-editorial-agents.md).

## Contexto

Agentes externos, começando pelo Dot, precisam consultar o editorial/catálogo e preparar drafts. API administrativa atual é ampla, autentica humanos com MFA e possui efeitos de taxonomia/destaque. Existe log centralizado e auditoria de domínio; ambos devem ser aproveitados.

## Decisão

1. Adaptador MCP separado, sem banco/ORM/KMS/segredos humanos; FastAPI permanece autoridade.
2. Suportar OAuth interativo e credenciais de serviço. Não presumir que Dot aceita segredo colado; validar OAuth com cliente real.
3. Staff e superuser com MFA administram todas as integrações igualmente nesta fase. Restrição por papel/proprietário é melhoria futura.
4. Integrações têm identidade técnica, scopes, responsável, revogação e cotas persistentes. Tokens nos trechos MCP/API têm audience correta e delegação verificável; workload sozinho não autoriza mutações.
5. Extrair serviços compartilhados de draft; payload restrito e proteção transacional de estado, versão, idempotência e quota, inclusive frente a publicação humana.
6. Logs técnicos centralizados existentes e eventos administrativos transacionais, com correlação estruturada. Não importar o gravador SQL no adaptador; ingestão pela API. Ficha editorial é dado privado de domínio independente da retenção técnica.
7. Pesquisa/agendamento externos; não adicionar pesquisa longa ao daemon. Nenhuma autoridade sobre ledger, publicação/resolução ou bots de previsão.
8. Parecer humano persistido e versionado constitui gate universal de novas publicações, conforme mudança de escopo aprovada em 2026-10-07. Preservar integridade publicada; não reescrever definições assinadas nem aplicar publicação retroativa.

## Emenda 2026-10-10 — documento único

Fichas usam exclusivamente documento textual versionado como conteúdo editorial autoritativo. Uma migração única converte registros estruturados anteriores e preserva os snapshots históricos; o runtime não aceita mais o formato antigo. A confirmação humana única pertence à decisão sobre revisão/hash específicos e não pode ser enviada pelo MCP. FastAPI continua responsável pela validade da decisão e pelo gate universal de publicação; a interface apenas coleta o parecer. Não há nova tabela ou mudança de fronteira.

## Impacto

Novas entidades, migrations/grants, contratos, telas Admin Ops, adaptador e configuração de deploy; web/mobile públicos continuam compatíveis. Bibliotecas OAuth/MCP e protocolo de delegação foram fixados na implementação descrita abaixo, preservando as regras. Status Dot/produção depende de evidência real.

## Alternativas rejeitadas

- Acesso SQL/ORM pelo MCP: viola a fronteira autorizada.
- Token staff compartilhado ou segredo MFA no agente: perde atribuição e amplia privilégios.
- Expor OpenAPI inteiro como tools: permite ações fora do editorial.
- Reutilizar bots oficiais como administradores: mistura identidades e efeitos econômicos.
- Novo sistema paralelo de logs: duplica estrutura já existente.
- Criar motor próprio de pesquisa obrigatório: desnecessário para executor externo.

## Evoluções

Separação staff/superuser ou por proprietário, gate editorial universal, pesquisa backend protegida, controle remoto do executor e orçamento LLM somente mediante contratos e escopo futuros.


## Escolha de implementação (2026-10-07)

- `Authlib==1.6.12`: engine mantida de authorization code e refresh; extensão PKCE S256 do Authlib, sem criptografia/protocolo reimplementado. FastAPI fornece callbacks PostgreSQL. Tokens opacos aleatórios de 48 bytes, somente SHA-256 no banco; issuer/audience e origem revogável persistidos e validados. SHA-256 de segredo aleatório não é hash de senha humana.
- `mcp==1.30.0`: SDK oficial Python v1.30 de manutenção (v2 é a linha atual; v1 continua recebendo patches críticos/segurança), Streamable HTTP stateless com respostas JSON; cliente real negocia `2025-11-25`. Discovery RFC 9728/RFC 8414, DCR público sem autoridade e clientes públicos PKCE. CIMD não é buscado pelo backend; cadastro de metadata URI é evolução, sem SSRF implícito. Não afirmar suporte à revisão de protocolo 2026-07-28 com o SDK v1.
- Compatibilidade fixada: FastAPI 0.128.8, Starlette 0.49.3, Pydantic 2.13.4, Uvicorn 0.39.0, httpx 0.28.1. São versões usadas pelo runtime local existente, preservando a geração dos contratos e evitando mudança incidental para Starlette 1.x. Adapter mínimo tem pins próprios. Python 3.9 do venv original é preservado; MCP usa 3.11/3.12.
- OAuth: consentimento Django/CSRF após login/MFA real GoTrendLabs; Authlib na API valida redirect exato, client, resource, código de 5 minutos de uso único, PKCE e scope. Access 10 minutos; refresh/grant absoluto até 90 dias, sem extensão na rotação. Reuso de code/refresh revoga a família de grant. `iss` na resposta de autorização.
- Serviço: `client_credentials` com ID da credencial como `client_id`, segredo único como `client_secret`, sem confusão com OAuth client secret. Novas credenciais não revogam antigas. MCP tokens não são passados a endpoints API: troca workload autenticada, token interno com audience `gotrendlabs:editorial-api` e parent revogável, máximo 40s.
- Locks: integração `FOR NO KEY UPDATE` (evita deadlock com FK de autoria no commit humano), depois token/quota/mercado/revisão. Pausa/revogação usam o mesmo lock. Humano bloqueia mercado; publicação pela lifecycle engine bloqueia antes de registrar definição. Tabelas de revisão têm somente SELECT/INSERT para FastAPI; Django não recebe acesso às tabelas privadas novas.
- Quotas PostgreSQL: 5 drafts/dia São Paulo, 60 tentativas autenticadas/minuto, 2 leases concorrentes/45s; tempos HTTP 3s conexão/15s operação, statement timeout 15s e lock timeout 5s. Duplicata não cobra draft. Chaves idempotentes conservadas indefinidamente nesta versão (garantia mínima 30 dias). Borda adaptador limita 180 solicitações/minuto/IP/instância e 4096 buckets; OAuth limita 30 tentativas/minuto/IP em PostgreSQL. Borda não substitui quotas de domínio.
- Sem retries de escrita automáticos no adapter: o executor repete com a mesma chave/payload e respeita Retry-After/backoff/jitter. Spool técnico limitado e sem tokens; perda por saturação/TTL explicitada.

Fontes oficiais consultadas: [SDK v1.30.0](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v1.30.0), [Authlib OAuth](https://docs.authlib.org/en/latest/oauth2/), [autorização MCP 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization), [custom MCP OpenAI](https://developers.openai.com/api/docs/guides/custom-mcp-server). Documentação atual `latest` aponta 2026-07-28; compatibilidade do piloto é explicitamente a revisão negociada pelo SDK fixado. Nenhuma fonte prova escrita/custom MCP disponível no Dot desta conta; homologação externa segue pendente.

A versão 1.30.0 foi escolhida após consultar a release oficial de 2026-09-07: valida issuer/metadata, restringe redirects de cliente à mesma origem e permite validação explícita de resource. Fixamos `validate_token_resource=True`. A escolha da linha mantida v1 preserva a API FastMCP usada e evita migrar o projeto incidentalmente para v2.

## Revisão de escopo v1.1 — histórico substituído pela v1.4 abaixo

O usuário revisou a decisão 8 após observar que draft de agente podia publicar sem parecer favorável. A partir desta revisão, a aprovação humana atual é obrigatória **somente para mercados vinculados à integração editorial**, no MarketLifecycleEngine antes de qualquer assinatura/abertura. Não se cria gate global para mercados humanos legados. Esta etapa intermediária foi posteriormente substituída pelo gate universal da v1.4; a decisão vigente está no item 8 acima. Reusar ficha/decision/revision/hash e locks existentes; edição invalida parecer, política antiga ou conteúdo divergente bloqueiam. Django separa publicação do save para não invalidar a versão revisada. Slug usa normalização comum com reserva transacional/colisões; identidade técnica permanece no domínio/auditoria. Listagem integrações segue Agentes IA, criação separada, sem permissões novas.

## Complemento operacional — preparação humana da ficha (v1.2)

Edição humana não pode depender do executor para reenviar a revisão. Reutilizar contrato EditorialRecord, locks/snapshot/revision e autoria humana em admin_events num endpoint staff/MFA exclusivo. Salvar/submeter não aprova; parecer continua separado e verificado; nenhuma permissão administrativa é adicionada ao MCP.

## Simplificação operacional v1.3

O usuário considera burocrática a sequência preparar/re-submeter/parecer. Compor serviços existentes numa transação assessment e um formulário humano, sem novas autoridades. Snapshot e decisão permanecem distintos para integridade/auditoria, mas não são dois aceites. Verificação de critério/fonte ocorre uma vez na UI; relato técnico não pré-atesta verificação humana. Publicação separada e gate v1.1 preservados.

## Ampliação explícita para todos os mercados — revisão 1.4 (2026-10-07)

O usuário solicitou revisão editorial de todo mercado e bloqueio de publicação com configuração de fechamento incompleta. Esta decisão substitui as restrições históricas de gate somente MCP acima. Reutilizar as tabelas, snapshots, parecer, serviços e logs; integration nullable representa origem humana, sem integração fictícia. Criação administrativa e conversão de sugestões inicializam ficha pendente. Backfill aditivo e idempotente mantém estados e provas; parecer de legados publicados não retroage nem autoriza reescrever definição.

FastAPI valida prazo futuro/fuso/modo automático ou manual antes de gate editorial e assinatura, sob lock do mercado. Aprovação exige versão/hash/política atuais; configuração e card integram snapshot. Não consultar disponibilidade momentânea do daemon como condição de publicação: health é operacional, não configuração persistida. Não criar agenda/radar próprio ou autoaprovação humana. Rollback conserva migration e histórico; publicação deve permanecer suspensa se a aplicação de rollback não suportar gate universal.

## Integração do rollout — fechamento 2026-10-07

Deploy padrão mescla Compose de produção e override MCP, inicia adapter isolado e inclui rotas MCP/OAuth no proxy, bloqueando rotas internas também sob /api. Configuração exclusiva API/adapter é criada no host em arquivos 0600, desligada inicialmente, com workload aleatório persistente e sem herdar env compartilhado. Build/preflights antecedem parada dos writers durante migrations/grants; falha não reinicia versão antiga sem gate universal. Ativação explícita após migrations e smokes; próximos deploys preservam estado/segredo. CI valida PR antes do merge; deploy só ocorre em main. Não incluir identidade externa, tokens ou mercado produtivo de teste no bootstrap.

Referências operacionais: [Docker Compose merge](https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/) e [GitHub Actions events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows). Paths do override resolvem em relação ao primeiro Compose; pull_request valida commit de merge e nunca aciona deploy produtivo.

## Evidência de implantação — 2026-10-07

PR #136/Actions 37692274600 aprovados; snapshot RDS anterior ao merge, migrations/grants/isolamento e HTTPS/discovery conferidos, API/MCP habilitados explicitamente. [Relatório](../testing/mcp-production-rollout-20261007.md). Domínio preservado, nenhum mercado real de teste; Dot/piloto autenticado ainda não homologados.

## Correção de interoperabilidade Codex — 2026-10-07

Follow-up de resposta DCR/ChatGPT: metadados opcionais não informados devem ser omitidos da resposta; `scope` é string segundo RFC 7591, não JSON null. Usar serialização `exclude_none`, sem conceder scopes default, adicionar credenciais ou alterar PKCE/consentimento. PR #140 implantada e smoke HTTPS aprovado; isso não comprova aceitação de cadastro nem homologação externa. [Evidências](../testing/mcp-chatgpt-dcr-20261007.md).

Codex CLI 0.160.1/Desktop falhou antes do consentimento: DCR envia `application_type: native`, recusado por schema de extras proibidos (422). Exceção restrita ao schema DCR: ignorar metadados desconhecidos conforme [RFC 7591 seção 2](https://datatracker.ietf.org/doc/html/rfc7591#section-2), sem persistir/refletir ou conceder autoridade. Preservar validações de campos conhecidos e estrita rejeição de extras nos payloads editoriais/admin.

O SDK normaliza issuer origin-only acrescentando `/`; substituir somente sua rota pública de resource metadata por resposta com strings canônicas da configuração (issuer sem barra final, mesma regra da FastAPI), mantendo challenge, verificação de audience e auth middleware do SDK. Issuer deve corresponder exatamente ao AS e resposta de autorização, conforme [documentação oficial](https://developers.openai.com/plugins/build/auth). Não adicionar CIMD nesta correção; DCR anunciado continua o mecanismo suportado. Sem migrations ou alteração de grants.
