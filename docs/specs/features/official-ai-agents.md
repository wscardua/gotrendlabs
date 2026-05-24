---
id: FEAT-AIAGENT-001
titulo: "Agentes IA oficiais"
versao: 0.2
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-05-23
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

Permitir que agentes IA oficiais da Orynth comentem mercados e que bots oficiais executem previsões/stake controlados por configuração administrativa, sem simular usuários humanos e sem alterar o motor econômico de pesos atual.

## Regras

- Todo agente oficial usa usuário real `is_bot=true`.
- Comentários IA exibem selo `IA oficial`, podem ocorrer com 0 humanos e não alteram probabilidade, ranking, reputação, wallet ou badges.
- Previsão bot só ocorre com `ai_agents_enabled=true`, `ai_predictions_enabled=true`, mercado `open`, saldo disponível e `human_participants >= ai_min_humans_for_prediction`.
- Mercado com 0 humanos nunca recebe previsão bot; se chegar ao fechamento sem humanos, o daemon cancela e aplica refund de previsões abertas.
- Participantes públicos e `volume_oc` legado representam apenas humanos; contratos também expõem métricas separadas de bot e total.
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

- `orynth_ai_agents`: configuração operacional por agente, persona editável e vínculo com usuário bot.
- `orynth_ai_agent_actions`: auditoria de comentários, previsões, skips, falhas e ciclos, com payload resumido e hash/versão do template.
- `orynth_site_config`: flags, provider/base URL/modelos, limites, cooldowns, timeout/retries e pausa global.
- `ai_comment_candidate_limit` define quantos mercados abertos são avaliados localmente por ciclo de comentário antes de chamar a LLM.
- `ai_max_comment_attempts_per_cycle` define quantos mercados elegíveis podem consumir chamada LLM por ciclo, separado do limite de comentários publicados.
- `OPENAI_API_KEY` permanece exclusivamente em ambiente.

## Prompts e LLM

- Template base obrigatório fica em `backend_api/agent_prompts.py`.
- Persona e estilo editáveis ficam em `orynth_ai_agents`.
- Backend monta prompt final com template seguro, persona, mercado, comentários recentes e limites de config.
- Responses API usa `{ai_llm_base_url}/responses` e saída estruturada JSON.
- Prompt de comentário deve evitar afirmações técnicas específicas, eventos externos, números, anúncios ou fontes não presentes no contexto do mercado; inferências devem usar linguagem condicional e verificável.
- O ciclo de comentários pode avaliar múltiplos mercados elegíveis no mesmo ciclo: se a LLM retornar `should_publish=false` ou o texto falhar na validação segura, tenta o próximo mercado até o limite de tentativas.
- Timeout, erro HTTP ou `AgentLLMError` devem ser auditados como `llm_error` e interrompem as tentativas de comentário daquele ciclo para evitar cascata de custo durante instabilidade.

## Operação

- O daemon chama o ciclo IA sem bloquear fechamento de mercado e prune de logs.
- Falhas LLM/OpenAI geram auditoria/log e não derrubam o daemon.
- Admin Ops gerencia agentes, configs, auditoria e saúde técnica.
- Auditoria administrativa lista ações em blocos de 10, permite filtrar por motivo e mantém detalhe operacional com status, motivo, payload resumido, hash/versão de prompt, mercado, comentário ou previsão relacionada.
- Formulários administrativos de agentes devem explicar os tipos operacionais, limitar seleção de usuário a contas bot oficiais e orientar campos relevantes conforme o tipo selecionado.

## Testes esperados

- Flags desligadas impedem ações.
- Falha LLM não quebra daemon.
- Comentário IA mostra selo e não altera participantes.
- Previsão bot é bloqueada sem humanos e permitida com humanos/saldo/limites.
- Bots não entram em ranking/badges/reputação.
