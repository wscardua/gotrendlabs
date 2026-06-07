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
- O runtime FastAPI fica em `apps/api/backend_api/`; apps Django, `templates/`, `static/`, `deploy/`, `docker/` e `scripts/ops/` continuam nos caminhos atuais ate suas migracoes próprias.
- `apps/mobile/` fica apenas reservado; specs técnicas e projeto Flutter serão iniciados em outra feature.
- `tools/skills/gotrendlabs/` permanece na raiz como ferramenta de governança e implementação do repositório inteiro.
- `ops/` e `packages/contracts/` são reservas para migrações futuras de operação e contratos compartilháveis.

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
