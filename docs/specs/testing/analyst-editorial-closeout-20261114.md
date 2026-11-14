# Fechamento: Analyst editorial e faixa Novo — 14/11/2026

## Estado vigente

Implementação local pronta: prompt `gotrendlabs-ai-agent-v6`, política `analyst-editorial-v1`, FEAT-AIAGENT-001 v0.8 e FEAT-MARKET-001 v0.18. Esta entrega contém qualidade do comentário inicial, correção da auditoria e janela Novo por publicação na web/Flutter. Não contém retomada/threads, pesquisa externa, troca de modelo ou aumento de frequência.

Base confirmada por fetch e MCP GitHub: origin/main `33b6da67378e3ad56d25de4e9eb4040f558e431d`; branch local `feature/analyst-editorial-quality`, worktree isolado. Preservar branch e alterações do checkout original. Os três workflows funcionais estão concluídos localmente; integração/deploy ainda aguardam aprovação do usuário à descrição da PR. A spec ampla de agentes continua parcial/draft: qualidade semântica real não foi homologada.

## Comportamento entregue

- Geração com política obrigatória em system, fatos fornecidos e hipóteses separados, todas as opções, referência UTC e até cinco comentários visíveis. Sem probabilidades/popularidade como evidência, sem URL tratada como pesquisa.
- Publicação exige uma avaliação separada e aprovação de sete critérios, nenhum motivo impeditivo ou risk_flags. Falha, inconclusão, abstenção ou excesso de caracteres impedem comentário público; sem truncamento, retries ou reescrita. No máximo duas requisições por candidato.
- Auditoria registra modelo/provedor/política/hash, decisão, etapa/tentativas, critérios, risk_categories normalizadas e abstention_reason obrigatório/coerente. Desconhecidos viram unknown_risk, sem texto livre/segredos/raciocínio interno. Informações anteriormente descartadas não são recuperadas.
- Novo usa `published_at <= agora < published_at + 48h`, apenas open e sem fallback para created_at. Criação continua disponível para ordenação; expiração automática preservada.

## Revisão e validação

O finding do review sobre perda dos motivos foi corrigido e coberto por persistência PostgreSQL/Admin Ops. Nove testes de contrato/provedor e regressões de fluxo: 49 aprovados em 50,820 s. Os quatro testes JavaScript do CI passaram (analytics, descoberta/filtros, convites e prévia de previsão). Suíte Python completa: o runner descobriu 725 casos e reportou 722 executados em 784,249 s, com 719 aprovados, dois skips e um erro ambiental no teste preexistente de privilégios. Esse erro é exclusivamente falta de CREATEROLE na credencial local de runtime, sem mudança no respectivo teste; reexecução isolada aprovada conforme abaixo. Não apresentar esta rodada como uma execução integralmente verde. CI completo e builds continuam gates obrigatórios antes do merge. O teste preexistente de privilégios exige CREATEROLE, indisponível ao usuário de runtime local: execução isolada com o papel migrador e banco de teste próprio passou (1 teste, 0,026 s), sem alterar permissões do runtime ou código do teste. O bootstrap administrativo só criou/removeu esse banco isolado, sem carregar sua credencial no Django.

Flutter completo: 141 testes aprovados e flutter analyze sem issues. Check Dockerfile aprovado, sem warnings. Build principal local tentou construir a imagem e falhou por falta de espaço em /var/cache/apt/archives/ (apt exit 100); nenhuma limpeza destrutiva realizada. Builds principal e MCP são gates obrigatórios do CI antes do merge. OpenAPI e checks Django/diff aprovados; sem migration, novo segredo, dependência, endpoint ou campo de API.

## Pré-flight produtivo somente leitura

SSM `01805ad5-d414-4644-85c4-91156f43e1fc`, Success/0, host GoTrendLabs na região us-east-1. Commit produtivo observado `f3eac3b646248355042cfcf47fdbc69b09f5d30a` (a main posterior inclui apenas seu recibo documental). Actions: ENABLE_PROD_DEPLOY=1, DEPLOY_BRANCH=main; workflow publica via SSM e recria web/FastAPI/daemon/MCP, com collectstatic.

Analyst id 1 ativo, ai_agents_enabled/ai_commenting_enabled true, Bedrock/openai.gpt-oss-20b; máximo por mercado 1, por ciclo 1, por dia 5, cooldown 24h e bloqueio por humano recente em 6h. ai_predictions_enabled também true: esta entrega não altera liquidez/previsões bot. Overrides do Analyst vazios e ai_paused_until nulo. Nenhuma configuração foi alterada nesta etapa.

## Ajustes operacionais propostos para depois da aprovação

| Campo | Valor observado | Valor proposto |
| --- | --- | --- |
| AiAgent id 1 personality_prompt | Atue como IA oficial da GoTrendLabs em mercados educativos de previsao. | Contribua com uma perspectiva concreta e sustentada para a conversa, com curiosidade e respeito à autonomia dos participantes. Abstenha-se quando não houver contribuição útil. |
| AiAgent id 1 comment_style | direto, equilibrado e didático | direto, natural, curioso e respeitoso |
| SiteConfig.ai_audit_retention_days | 1 | 30 |

Aplicar somente esses ajustes após implantação aprovada, verificando novamente o estado para evitar sobrescrever edição concorrente. Registrar valores anteriores/novos sem segredos e o recibo da operação. Não reexecutar comando de criação para sobrescrever agente, não criar mercados/comentários de teste em PRD, não moderar conteúdo existente nem disparar rodada paga do conjunto editorial. Modelo/provedor, flags, limites, cooldown e frequência permanecem iguais.

## Fluxo GitHub e verificação pós-merge

1. Commit local de código, testes e documentação; apresentar ao usuário título/descrição completos da PR e solicitar aprovação antes de submeter. Preservar branch local.
2. Após aprovação: push da branch, PR em português pelo MCP GitHub para main, acompanhar CI completo/builds e corrigir falhas introduzidas. Usar CLI para Actions quando o MCP não oferecer a operação necessária.
3. Merge somente após gates aprovados. Acompanhar Actions da main, comando SSM e health dos serviços, confirmando o commit realmente implantado.
4. Aplicar ajustes operacionais aprovados acima; conferir flags/limites preservados, versão/hash de prompt no runtime/daemon e auditoria de um ciclo normal quando disponível, sem forçar inferência ou publicação. Conferir web/home/API e JS servido com published_at.
5. Registrar PR, commits, Actions, SSM, smoke, configurações e limitações reais neste recibo e reconciliar README/estado. Não chamar preparação de implantação concluída.

Rollback: reverter a PR pelo fluxo versionado se necessário, restaurar apenas os três valores operacionais registrados quando aplicável e verificar serviços/daemon. Não apagar auditoria, mercados ou comentários; não usar fallback de contrato LLM antigo no código novo.

## Limitações e MCP/mobile

Os 24 casos editoriais sintéticos têm critérios/protocolo, mas não foram executados no modelo real por falta de autorização de chamadas pagas adicionais. Mocks não provam qualidade semântica, segurança absoluta contra injeção ou engajamento. A segunda chamada compartilha possíveis vieses do modelo e aumenta custo/latência; não há benchmark real.

MCP: ferramentas, schemas públicos, contratos, permissões, erros, replays e manual editorial exposto permanecem iguais. O contrato novo é privado entre Analyst e provedor; nenhuma permissão inferida de Admin Ops.

Deploy web/API não atualiza instalações Flutter. O código da faixa Novo está validado, mas distribuição Android/iOS exige fluxo separado com checkout limpo da main, versão/build integrados e gate validateReleaseSource. Não enviar artefato mobile nesta entrega.
