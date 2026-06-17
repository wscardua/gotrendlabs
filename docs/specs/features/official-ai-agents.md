---
id: FEAT-AIAGENT-001
titulo: "Agentes IA oficiais"
versao: 0.3
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-06-17
origem:
  - solicitação de produto para comentários IA oficiais e liquidez bot controlada
contratos_afetados:
  - prediction-payloads.md
  - reputation-ranking.md
  - wallet-ledger.md
  - domain-events.md
dependencias:
  - FEAT-AUTH-001
  - FEAT-MARKET-002
  - FEAT-PRED-001
  - FEAT-WALLET-001
  - FEAT-OPSLOG-001
impacta:
  - backend-api
  - database
  - scheduler-jobs
  - admin-ops
  - frontend-web
aprovacao: pendente
---

# Agentes IA Oficiais

## Objetivo

Permitir que agentes IA oficiais da GoTrendLabs comentem mercados e que bots oficiais executem previsões/stake controlados por configuração administrativa, sem simular usuários humanos e sem alterar o motor econômico de pesos atual.

## Regras

- Todo agente oficial usa usuário real `is_bot=true`.
- Comentários IA exibem selo `IA oficial`, podem ocorrer com 0 humanos e não alteram probabilidade, ranking, reputação, wallet ou badges.
- O total de comentários IA visíveis por mercado é controlado em Admin Ops por `ai_max_comments_per_market`, com default `1`; comentários ocultos/moderados não contam para esse limite.
- Agentes `analyst` podem ter override opcional `max_comments_per_market_override`; quando preenchido, o limite por mercado é contado para comentários visíveis do próprio usuário bot do agente, e quando vazio herda o limite global.
- Previsão bot só ocorre com `ai_agents_enabled=true`, `ai_predictions_enabled=true`, mercado `open`, saldo disponível e `human_participants >= ai_min_humans_for_prediction`.
- Mercado com 0 humanos nunca recebe previsão bot; se chegar ao fechamento sem humanos, o daemon cancela e aplica refund de previsões abertas.
- Participantes públicos e `volume_gtl` legado representam apenas humanos; contratos também expõem métricas separadas de bot e total.
- Ranking, badges, streaks, recompensas e reputação pública excluem bots.

## Tipos de agente

- `analyst`: tipo operacional para comentários oficiais. O daemon pode usá-lo quando `ai_agents_enabled=true`, `ai_commenting_enabled=true`, o agente está ativo e as regras de cooldown/limites permitem. Comentários devem ser curtos, equilibrados, identificados como IA oficial e não alteram probabilidade ou métricas humanas.
- `liquidity`: tipo operacional para testes controlados de previsão/stake bot. O daemon pode usá-lo quando `ai_agents_enabled=true`, `ai_predictions_enabled=true`, o agente está ativo, o mercado está aberto, há participantes humanos suficientes, há saldo e os limites permitem.
- `contrarian`: conceito futuro para contraponto analítico contra consensos fortes. No estado atual, não há rotina backend ativa para `contrarian`; ele não deve ser exposto como opção operacional salvo se houver política aprovada, spec própria e implementação específica no daemon/backend.

## Documentação pública e política

- A página pública de conceitos deve explicar, em linguagem didática, a diferença entre agentes oficiais de comentário (`analyst`) e bot de liquidez controlada (`liquidity`).
- A política de uso deve registrar que agentes oficiais não fingem ser humanos, comentários IA são identificados, bots não contam como participantes humanos e bots ficam fora de rankings, badges, streaks, recompensas e reputação pública.
- Estratégias futuras como `contrarian` devem ser tratadas como conceito/spec futura, não como recurso operacional disponível.

## Persistência

- `gotrendlabs_ai_agents`: configuração operacional por agente, persona editável, override opcional de comentários por mercado e vínculo com usuário bot.
- `gotrendlabs_ai_agent_actions`: auditoria de comentários, previsões, skips, falhas e ciclos, com payload resumido e hash/versão do template.
- `gotrendlabs_site_config`: flags, provider/base URL/modelos, limites, cooldowns, timeout/retries e pausa global.
- `ai_max_comments_per_market` define o total global de comentários IA oficiais visíveis permitidos por mercado durante sua vida.
- `gotrendlabs_ai_agents.max_comments_per_market_override` permite configurar limite específico do agente `analyst` por mercado, sem alterar o contrato público nem o app mobile.
- `ai_comment_candidate_limit` define quantos mercados abertos são avaliados localmente por ciclo de comentário antes de chamar a LLM.
- `ai_max_comment_attempts_per_cycle` define quantos mercados elegíveis podem consumir chamada LLM por ciclo, separado do limite de comentários publicados.
- O segredo do provedor LLM permanece exclusivamente em ambiente (`OPENAI_API_KEY` para OpenAI ou `AWS_BEARER_TOKEN_BEDROCK` para Bedrock).
- `gotrendlabs_site_config.ai_audit_retention_days` define por quantos dias a auditoria IA é preservada antes do purge operacional; default 90 dias.

## Prompts e LLM

- Template base obrigatório fica em `apps/api/backend_api/agent_prompts.py`.
- Persona e estilo editáveis ficam em `gotrendlabs_ai_agents`.
- Backend monta prompt final com template seguro, persona, mercado, comentários recentes e limites de config.
- Responses API usa `{ai_llm_base_url}/responses` e saída estruturada JSON.
- Prompt de comentário deve evitar afirmações técnicas específicas, eventos externos, números, anúncios ou fontes não presentes no contexto do mercado; inferências devem usar linguagem condicional e verificável.
- O ciclo de comentários pode avaliar múltiplos mercados elegíveis no mesmo ciclo: se a LLM retornar `should_publish=false` ou o texto falhar na validação segura, tenta o próximo mercado até o limite de tentativas.
- Timeout, erro HTTP ou `AgentLLMError` devem ser auditados como `llm_error` e interrompem as tentativas de comentário daquele ciclo para evitar cascata de custo durante instabilidade.

## Operação

- O daemon chama o ciclo IA sem bloquear fechamento de mercado e prune de logs.
- Falhas LLM/provedor configurado geram auditoria/log e não derrubam o daemon.
- Admin Ops gerencia agentes, configs, auditoria e saúde técnica.
- Quando um mercado já atingiu o limite configurado de comentários IA visíveis, o daemon pula o mercado antes de chamar a LLM; se todos os candidatos avaliados forem barrados por esse limite, registra uma auditoria agregada com motivo `market_ai_comment_limit`.
- Auditoria administrativa lista ações em blocos de 10, permite filtrar por motivo e mantém detalhe operacional com tipo, status e motivo explicados em linguagem operacional, preservando códigos técnicos, payload resumido, hash/versão de prompt, mercado, comentário ou previsão relacionada.
- A auditoria IA é limpa pelo daemon junto com logs técnicos, usando `created_at` e o prazo configurado atual, inclusive para registros antigos.
- Formulários administrativos de agentes devem explicar os tipos operacionais, limitar seleção de usuário a contas bot oficiais e orientar campos relevantes conforme o tipo selecionado.

## Testes esperados

- Flags desligadas impedem ações.
- Limite administrável por mercado impede novo comentário IA visível quando atingido e permite novo comentário quando configurado acima da contagem atual.
- Override por agente herda o global quando vazio, permite limite maior para o próprio agente quando preenchido e também pode ser mais restritivo que o global.
- Falha LLM não quebra daemon.
- Browse e detalhe de auditoria IA explicam tipo, status e motivo sem exigir interpretação dos códigos brutos.
- Comentário IA mostra selo e não altera participantes.
- Previsão bot é bloqueada sem humanos e permitida com humanos/saldo/limites.
- Bots não entram em ranking/badges/reputação.
