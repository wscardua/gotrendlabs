---
id: FEAT-AIAGENT-001
titulo: "Agentes IA oficiais"
versao: 0.8
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-11-14
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

Entrega de 14/11/2026 implementada e testada localmente; PR, implantação e ajustes operacionais aguardam aprovação. [Fonte vigente e limites do fechamento](../testing/analyst-editorial-closeout-20261114.md). Status amplo da spec preservado; validação semântica real do Analyst e distribuição Flutter permanecem distintas.

## Objetivo

Permitir que agentes IA oficiais da GoTrendLabs comentem mercados e que bots oficiais executem previsões/stake controlados por configuração administrativa, sem simular usuários humanos e sem alterar o motor econômico de pesos atual.

## Regras

- Todo agente oficial usa usuário real `is_bot=true`.
- A identidade bot pode ter senha inutilizavel: o daemon seleciona o agente pelo vinculo `gotrendlabs_ai_agents.user_id`, `is_bot=true` e estados ativos, e executa comentarios/previsoes diretamente no backend. Rotinas internas nao fazem login com a senha do bot.
- Comentários IA exibem selo `IA oficial`, podem ocorrer com 0 humanos e não alteram probabilidade, ranking, reputação, wallet ou badges.
- O total de comentários IA visíveis por mercado é controlado em Admin Ops por `ai_max_comments_per_market`, com default `1`; comentários ocultos/moderados não contam para esse limite.
- Agentes `analyst` podem ter override opcional `max_comments_per_market_override`; quando preenchido, o limite por mercado é contado para comentários visíveis do próprio usuário bot do agente, e quando vazio herda o limite global.
- Previsão bot só ocorre com `ai_agents_enabled=true`, `ai_predictions_enabled=true`, mercado `open`, saldo disponível e `human_participants >= ai_min_humans_for_prediction`.
- Mercado com 0 humanos nunca recebe previsão bot; se chegar ao fechamento sem humanos, o daemon cancela e aplica refund de previsões abertas.
- Participantes públicos (`participants` e `total_participants`) contam contas distintas com previsões abertas, incluindo humanos e bots, sem separação visual. Uma conta com várias entradas conta uma vez. `volume_gtl` representa volume humano; métricas humanas/bot explícitas continuam disponíveis para operação e elegibilidade.
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

## Escopo desta melhoria

Apenas qualidade do comentário inicial. Retomada de discussão e respostas em threads permanecem possibilidades futuras, sem implementação. Sem aumento de frequência, pesquisa externa, troca do modelo/provedor produtivo, alteração de comentários existentes ou da mecânica de mercados/GT₵. Elegibilidade, limites, cooldown e bloqueio humano existentes preservados.

## Política editorial do comentário inicial — analyst-editorial-v1

- Objetivo: dar aos participantes algo concreto e compreensível para discutir, preservando sua autonomia; volume não mede qualidade.
- Exigir especificidade, contribuição além de título/resumo/regras, sustentação no contexto, separação entre fato e hipótese, neutralidade, naturalidade, coerência/completude e ausência de repetição relevante.
- Pergunta pertinente é opcional. Permitir distinção de fatores, tensão entre interpretações ou discussão de evidências sem cabeçalhos, seleção arbitrária de opções ou fórmula SIM/NÃO + sinais.
- Proibir favoritismo, recomendação de opção, probabilidades inventadas, chances iguais sem base, desvalorização de candidatos, perguntas indutivas e apelos para participar ou movimentar probabilidades.
- Proibir qualquer indicação financeira direta/indireta, inclusive pergunta ou disclaimer: investir, comprar/vender/manter, entrar/sair, alocação/exposição/valores/percentuais, lucro/rentabilidade/recuperação de perdas e GT₵ como oportunidade financeira. Informação econômica ou de preços factual e neutra é permitida; não bloquear temas financeiros/cripto por categoria.
- Evitar manual de apuração, mera declaração de resultado desconhecido, jargão, grandiloquência, falsa vivência, entusiasmo artificial, perguntas vazias e listas genéricas de sinais.
- Abstenção é resultado esperado quando não existe contribuição útil, segura e sustentada.

## Prompts, contexto e decisão de publicação

- Template `gotrendlabs-ai-agent-v6`, política `analyst-editorial-v1`, schemas e hash conjunto de geração/avaliação em `agent_prompts.py`.
- Política obrigatória em mensagem system prevalece sobre persona configurável, conteúdo do mercado, comentários e candidato; estes são dados não confiáveis, nunca instruções.
- Contexto explicita pergunta/tema, resumo como fatos fornecidos não verificados, todas as opções sem probabilidades, regras como restrições, referência temporal UTC do ciclo/fechamento e até cinco comentários visíveis recentes (integrais, sem autor identificável). Não consulta histórico amplo nem exemplos de outros mercados.
- URLs são referências não consultadas, sem pesquisa externa. Comentários humanos não estabelecem fatos. Removida consulta de métricas públicas do caminho de contexto; popularidade mantém apenas a seleção operacional existente.
- Uma geração por mercado elegível. Validar tipos/campos estritos localmente nos dois provedores; confiança do gerador é apenas parte do contrato, nunca autorização de publicação.
- `should_publish=false` gera abstenção; qualquer `risk_flags` do gerador impede publicação, inclusive flags desconhecidas. Texto vazio, inseguro ou acima do limite é rejeitado integralmente, sem truncamento nem reescrita.
- Uma avaliação separada pelo mesmo provedor/modelo recebe candidato final normalizado e contexto. Saída estruturada: `decision`, sete `checks`, `reasons` em códigos curtos e `risk_flags`.
- Publicar somente com `decision=approve`, TODOS os critérios verdadeiros, nenhum motivo nem flag. Rejeição, inconclusão, inconsistência, JSON inválido ou falha impedem persistência pública. Texto aprovado não é modificado depois da avaliação.
- O campo existente `ai_openai_max_retries` não autoriza retries no Analyst; o formulário explicita o orçamento. Não há retry HTTP nem reescrita: até duas chamadas por candidato (geração + avaliação), cada uma com timeout configurado. `ai_max_comment_attempts_per_cycle` mantém limite de candidatos por agente; todos os limites de publicação, elegibilidade, bloqueio humano e cooldown permanecem.
- Abstenção/rejeição pode tentar próximo candidato dentro do limite existente. Falha/contrato inválido de geração ou avaliação interrompe comentários do ciclo, auditada, sem derrubar daemon nem impedir demais rotinas.
- Custo/latência: candidatos avaliados consomem uma chamada adicional; até duas requisições por candidato e até 2 × candidatos por agente (timeout por fase de I/O, não deadline absoluto). Sem benchmarks ou qualidade real alegados. Mesmo modelo pode repetir vieses, aceitar afirmações falsas do contexto ou sofrer injeção; a segunda chamada reduz risco sem garantir correção.

## Auditoria e operação administrativa

- Auditoria existente guarda versão/hash de ambos os prompts/schemas, política, provedor/modelo, publicado/rejeitado/abstenção, etapa com falha, contagem de chamadas/tentativa e critérios/códigos curtos de avaliação. Registra `risk_categories` como códigos conhecidos e `unknown_risk` para flags desconhecidas, junto de `risk_flag_count`; nunca guarda flags livres, raciocínio, candidato rejeitado ou texto bruto de erro. O gerador deve retornar `abstention_reason` obrigatório: `not_applicable` somente quando `should_publish=true`; na abstenção, um código de `REVIEW_REASONS` ou `other_reason`. Contradição/ausência/tipo inválido falha sem publicação. Não há fallback para o contrato antigo.
- Sem alteração automática de configurações persistidas. Recomendar revisão operacional de `SiteConfig.ai_audit_retention_days`: 30–90 dias conforme necessidade/custo/privacidade; default documentado 90, histórico de produção de um dia não foi reconfirmado ou alterado.
- Para aplicação humana posterior: `AiAgent.personality_prompt` = “Contribua com uma perspectiva concreta e sustentada para a conversa, com curiosidade e respeito à autonomia dos participantes. Abstenha-se quando não houver contribuição útil.”; `AiAgent.comment_style` = “direto, natural, curioso e respeitoso”. Editar agente Analyst no Admin Ops apenas após revisão administrativa.
- Comando de criação usa defaults apenas para novo agente, preservando persona/estilo e ativação de agentes existentes. Migrações históricas não são reexecutadas nem editadas.
- Avaliação real e limitações: [protocolo e conjunto](../testing/analyst-editorial-evaluation.md); mocks validam fluxo, não capacidade semântica.
- MCP: nenhuma mudança em ferramentas, schemas/contratos públicos, permissões, erros ou replays; política e contrato LLM privados do Analyst, sem alteração do manual de criação de mercados exposto pelo MCP. Não deriva permissões de Admin Ops.

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
