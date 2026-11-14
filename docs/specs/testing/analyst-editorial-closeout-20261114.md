# Fechamento: Analyst editorial e faixa Novo — 14/11/2026

## Estado vigente

Entrega integrada e implantada em produção: prompt `gotrendlabs-ai-agent-v6`, política `analyst-editorial-v1`, FEAT-AIAGENT-001 v0.8 e FEAT-MARKET-001 v0.18. Esta entrega contém qualidade do comentário inicial, correção da auditoria e janela Novo por publicação na web/Flutter. Não contém retomada/threads, pesquisa externa, troca de modelo ou aumento de frequência.

Base confirmada por fetch e MCP GitHub: origin/main `33b6da67378e3ad56d25de4e9eb4040f558e431d`; branch local `feature/analyst-editorial-quality`, worktree isolado. Preservar branch e alterações do checkout original. Usuário aprovou a descrição/plano e autorizou continuidade. PR #213 integrada e implantação confirmada no recibo produtivo abaixo; os workflows funcionais estão concluídos. A integração deste recibo usa CI documental leve, sem novo deploy. A spec ampla de agentes continua parcial/draft: qualidade semântica real não foi homologada.

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

## Ajustes operacionais aprovados e aplicados

| Campo | Valor anterior confirmado | Valor aplicado |
| --- | --- | --- |
| AiAgent id 1 personality_prompt | Atue como IA oficial da GoTrendLabs em mercados educativos de previsao. | Contribua com uma perspectiva concreta e sustentada para a conversa, com curiosidade e respeito à autonomia dos participantes. Abstenha-se quando não houver contribuição útil. |
| AiAgent id 1 comment_style | direto, equilibrado e didático | direto, natural, curioso e respeitoso |
| SiteConfig.ai_audit_retention_days | 1 | 30 |

Os três ajustes foram aplicados após confirmar commit/arquivos/serviços, em transação com locks, comparação dos valores anteriores e evento administrativo 663 (ator sistema/nulo, execução pr213-analyst-editorial-v6). Leitura independente confirmou persistência. Não houve alteração de comentários, criação de mercados de teste ou rodada paga adicional; modelo/provedor, flags, limites, cooldown e frequência foram preservados.

## Fluxo GitHub aprovado (histórico do plano)

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

## Recibo produtivo — fonte vigente

- Aprovação explícita do usuário recebida antes de push/PR/merge/deploy e ajustes operacionais.
- PR [#213](https://github.com/wscardua/gotrendlabs/pull/213), aberta e mergeada pelo MCP GitHub, em português. Fonte `51a5ddcce1c7711065e1b69266e7f96c694b062a`; merge e commit produtivo `789ca3c11abd32e29e10228f554dc0594afc54a3`.
- [CI da PR 43611013720](https://github.com/wscardua/gotrendlabs/actions/runs/43611013720): aprovado; 722 testes Python reportados, três skips, 529,372 s; builds principal/MCP, Dockerfile, OpenAPI e quatro scripts JS aprovados.
- [CI/deploy da main 43612113385](https://github.com/wscardua/gotrendlabs/actions/runs/43612113385): aprovado; 722 testes Python reportados, três skips, 435,546 s; mesmos builds/checks aprovados. O erro local de CREATEROLE não ocorreu no CI.
- Deploy SSM `c86a5926-b53b-406a-a560-e60bd211b596`: Success/0. Runtime verificado por SSM `14a59862-4515-4342-ac8a-819a8be3bbcf`: commit exato, checkout produtivo limpo, seis serviços running e MCP healthy. Dez arquivos de runtime comparados por SHA-256 em cada um de FastAPI, Django e daemon; todos iguais ao commit revisado.
- Três processos carregam `gotrendlabs-ai-agent-v6` / `analyst-editorial-v1`, hash conjunto `c3770fee0ee7cc44f19c0c65e6180951ad763fe08b9be647698026c05dfc30b0`.
- Ajustes operacionais SSM `dcf8b136-30bc-4030-9fd1-9d48c18612a8`: Success/0, evento administrativo 663, em 14/11/2026 às 13:01:46 de São Paulo (16:01:46 UTC). Persona/estilo e retenção 1→30 dias conforme tabela; demais flags/modelo/limites conferidos e preservados. Leitura independente SSM `aeff0307-b073-4831-8136-fa245665c856`: Success/0.
- Daemon observou ciclo normal com v6 (ações 156687–156689), comentário pulado por market_ai_comment_limit e ciclo concluído; nenhum comentário forçado nem chamada manual ao modelo. Esse registro confirma execução/limites, não capacidade semântica do modelo.
- Smoke HTTPS: home/login/API health/API markets 200; health ok; Admin e MCP sem token 401. HTML contém published_at e nova referência JS. JS público SHA-256 `f3643891c13d72687b3d96ea7c9c41c01cb66a1dec9233e08053422c133af009`, igual ao arquivo revisado. Quatro mercados abertos retornados, nenhum dentro de 48h da publicação; não alterar dados para fabricar faixa visível.
- Evidência estruturada com hashes, configurações e leituras: [JSON](analyst-editorial-production-20261114.json). Os registros preparatórios anteriores são históricos; este recibo prevalece.
- Branch local feature/analyst-editorial-quality e alterações do checkout original preservadas. Nenhuma distribuição Flutter, mudança de modelo/provedor, nova permissão MCP ou moderação de comentário existente.
- Limitações restantes: os 24 casos semânticos ainda dependem de autorização para rodada paga; sem alegação de engajamento ou garantia editorial. Flutter tem 141 testes/analyze aprovados e código integrado, mas exige distribuição própria. Sem pendência técnica de implantação desta entrega.
