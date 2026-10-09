
## Evolução especificada: MCP editorial

[FEAT-MCP-001](../features/mcp-editorial-agents.md) e [ADR-0011](../decisions/ADR-0011-mcp-editorial-integrations.md) definem adaptador MCP sem banco, FastAPI autoritativa e executor externo. Estado: MCP implantado/habilitado pela PR #136; HTTPS/grants/isolamento produtivos conferidos, Dot/piloto autenticado pendentes.
# Visão Geral do Sistema

## Objetivo

Definir fronteiras estáveis entre as camadas do GoTrendLabs para que a implementação orientada por IA mantenha separação clara de responsabilidades.

## Camadas

- `frontend-web`: páginas, templates, renderização HTML, HTMX, Alpine.js, navegação, estados locais simples, i18n de interface.
- `future-mobile`: cliente mobile reservado para feature futura; deve consumir contratos do backend e não calcular regra crítica localmente.
- `backend-api`: autenticação principal, sessão, regras de domínio, probabilidades, stake, reputação, wallet, resolução de mercados e contratos JSON.
- `database`: persistência relacional no PostgreSQL, integridade referencial, histórico auditável, índices e suporte a relatórios operacionais.
- `scheduler-jobs`: fechamento automático de mercados, reconciliações temporizadas e tarefas operacionais programadas.
- `communications`: orquestração de emails e notificações, seleção de template, idioma e trilha de entrega.
- `admin-ops`: backoffice para operação de mercados, moderação, revisão, resolução, taxonomia e troubleshooting.

## Organização do monorepo

- `apps/api/`, `apps/web/` e `apps/mobile/` são a estrutura alvo para organizar produtos executáveis por camada.
- O runtime FastAPI fica em `apps/api/backend_api/`; deploy, scripts operacionais e Docker local ficam em `ops/`; apps Django, templates e assets web ficam em `apps/web/`.
- Os apps Django vivem em `apps/web/django/` e preservam `AppConfig.label` historico para manter migrations e tabelas estaveis.
- `apps/mobile/` fica apenas reservado; specs técnicas e projeto Flutter serão iniciados em outra feature.
- `.agents/skills/` reúne as skills versionadas de governança e implementação, descobertas pelo Codex em todo o repositório.
- `ops/` concentra deploy, scripts operacionais e Docker local; `packages/contracts/` versiona o snapshot OpenAPI da FastAPI e permanece como futura casa de clientes gerados.

## Princípios

- O backend é a fonte de verdade do domínio.
- Frontends, incluindo web e futuro mobile, nunca concentram lógica crítica de negócio.
- O banco não substitui regras de domínio; ele persiste estados decididos pelo backend.
- O scheduler executa decisões já modeladas; ele não define política de produto por conta própria.
- O subsistema de comunicações não duplica regras de elegibilidade ou cálculo de negócio.
- O admin opera o sistema, mas não deve contornar contratos centrais sem rastreabilidade.

## Fluxo padrão

1. A spec funcional origina uma spec técnica por feature.
2. A feature declara quais camadas toca.
3. Os contratos transversais são atualizados.
4. A arquitetura valida a alocação correta das responsabilidades.
5. Só então a implementação é iniciada.

### Revisão universal de publicação — 2026-10-07

FastAPI inicializa ficha humana na criação administrativa/conversão e valida aprovação e fechamento no MarketLifecycleEngine. Origem humana usa integração nullable. Migration 0003 acrescenta fichas pendentes aos legados sem alterar domínio/provas. Django apresenta revisão e erros retornados; MCP mantém permissões restritas e não acessa ORM. Este escopo substitui referências anteriores ao gate apenas de integração.

## Executor de thumbnails

[FEAT-THUMB-001](../features/ai-market-thumbnails.md) implantada e habilitada em produção pela PR #143 em 2026-10-09; homologação humana/MFA e inferência/qualidade visual produtivas pendentes. Django apresenta controles junto do upload e adapta sessão/CSRF; FastAPI autoriza/cota/persiste/confirma; worker dedicado executa fila PostgreSQL sem transação durante provider I/O. Candidatas privadas e promoção por ID mantêm image_url público e gate editorial. Nenhuma chamada no daemon de fechamento/comunicações. [ADR-0012](../decisions/ADR-0012-private-thumbnail-worker.md), [contrato](../contracts/admin-thumbnails.md).

## 2026-10-09 — Imagens IA de badges

FEAT-BADGE-IMAGE-001 reutiliza o pipeline administrativo Bedrock/fila/executor/volume privado de thumbnails; migração 0025 adiciona kind e vínculos de badge/editor. API/worker recebem subpath badge_images RW adicional; contratos image_url/image_dark_url continuam estáveis.


Thumbnails semânticas v5 (validação local): backend congela parâmetros próprios do planejador; executor interpreta o mercado em modelo textual Bedrock e renderiza o brief em modelo de imagem configurado. Checkpoints e lease cobrem ambas as etapas, sem retry/fallback; UI/contratos públicos e badges preservados. [ADR-0014](../decisions/ADR-0014-semantic-thumbnail-brief.md). Produção ainda não alterada e homologação visual pendente.
