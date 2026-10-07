# Prompt de implementação — GPT-6.1 Sol

Copie o bloco abaixo em um contexto limpo com o repositório GoTrendLabs disponível. Os documentos citados contêm decisões, contratos, evidências da análise e limites de escopo; não é necessário fornecer a conversa anterior.

```text
Implemente a feature FEAT-MCP-001 no GoTrendLabs, seguindo os documentos abaixo como fonte de verdade. Execute a implementação e os testes, não entregue apenas um plano.

Leia primeiro:
1. AGENTS.md aplicáveis, se houver, e skills locais pertinentes.
2. docs/specs/features/mcp-editorial-agents.md
3. docs/specs/contracts/agent-integrations.md
4. docs/specs/decisions/ADR-0011-mcp-editorial-integrations.md
5. docs/specs/testing/mcp-editorial-acceptance.md
6. docs/specs/state/workflow-runs.md (WFLOW-20261007-MCP-EDITORIAL-SPEC)
7. docs/specs/state/implementation-status.md, integration-map.md e known-gaps.md.
Depois leia os arquivos de código e documentos relacionados indicados na feature. Revalide referências contra o checkout atual.

Objetivo: MCP editorial remoto para Dot da OpenAI e executores semelhantes, com OAuth interativo E credenciais de serviço; gestão de integrações no Admin Ops; leitura de editorial/catálogo/métricas agregadas; criação/edição de drafts próprios; ficha estruturada, submissão e parecer humano; logs centralizados existentes, idempotência, cotas persistentes e controle de concorrência.

Decisões que não devem ser reabertas:
- Staff e superuser com MFA gerenciam todas as integrações igualmente. Não criar exclusividade de superuser nem isolamento administrativo por dono. Isso é melhoria futura.
- Agente possui identidade técnica/permissões específicas, sem senha humana ou TOTP. ID é público; segredo de serviço é gerado na FastAPI e exibido uma vez no Admin Ops.
- OAuth é caminho preferido para Dot; credencial de serviço atende executores compatíveis. Não concluir a feature com só um dos modos.
- MCP não acessa DB/ORM nem importa o gravador de logs que abre banco. FastAPI aplica todas as regras e valida a delegação; não repassar token de audience errada nem usar token staff compartilhado.
- Reutilizar gotrendlabs_system_logs e gotrendlabs_admin_events, ampliando autoria/correlação/filtros. Ficha editorial é dado de domínio, não log temporário.
- Não expor API administrativa inteira. Sem publicação/resolução/cancelamento, usuários/wallet, previsões, comentários, destaque ou criação de taxonomia por agente.
- Pesquisa e agenda pertencem ao executor externo. Não criar motor LLM próprio nem colocar radar no daemon operacional.
- Sem novo gate editorial global de publicação nesta fase. Mostrar parecer e preservar revisão humana operacional; não prometer enforcement inexistente. Edição concorrente com publicação deve ser segura.
- Respeitar editorial v1.2 ou sucessor aprovado, incluindo diversidade sem cotas obrigatórias.

Forma de trabalhar:
- Inspecione branch, mudanças locais e workflows. Preserve trabalho existente e arquivos não relacionados. A especificação foi preparada sobre feature/first-party-analytics, com itens mobile não rastreados; não assumir que essa ainda é a base nem descartar esses itens.
- Crie branch/worktree apropriado sem perder os documentos desta feature. Não misture conclusão de analytics ou mobile com MCP.
- Abra workflow de implementação vinculado ao workflow documental, use skills de arquitetura, governança, FastAPI, PostgreSQL, Django e testes conforme necessário. Não delegue a outros agentes sem instrução aplicável/autorização.
- Escolha biblioteca OAuth/MCP mantida, fixe versões compatíveis e registre justificativa no ADR. Consulte documentação oficial atual. Não invente compatibilidade Dot.
- Faça migrations aditivas e grants por role. Extraia serviços compartilhados dos handlers existentes, mantendo compatibilidade web/mobile e integridade.
- Implemente por fatias completas: identidade/auth/gestão/leitura/logs; depois drafts/ficha/revisão/cotas/concorrência; depois pacote/instruções de conexão e roteiro de homologação Dot.
- Use defaults documentados e resolva escolhas técnicas rotineiras autonomamente. Só pergunte por informação indispensável que não pode ser inferida; continue tarefas independentes.
- Não use produção nem crie mercados reais para testar. Use PostgreSQL isolado, mocks de falha e cliente MCP real de teste.
- Prepare configuração de deploy/rollback sem executar publicação, merge ou deploy por este prompt. Não copie segredos para Git, logs ou prompts.
- Se Dot/acesso externo não estiver disponível, conclua código e testes locais possíveis e registre exatamente a homologação pendente. Não declare Dot validado nem substitua OAuth por acesso desprotegido.
- Atualize OpenAPI e documentação/estado/changelogs a cada entrega coerente; não marque implementada_validada antes das evidências necessárias.

Entrega: código e migrations, testes pertinentes passando, UI conferida, configuração/runbook de operação, instruções para conectar OAuth e serviço, prompt de radar para Dot, resultado por critério de aceite e pendências externas explícitas. No final, informe o que mudou, como foi validado e como iniciar o piloto. Não pare após esqueleto ou leitura apenas se ainda houver trabalho local autorizado a executar.
```

## Documentação oficial para homologação

- https://help.openai.com/en/articles/20001530-getting-started-with-your-dot
- https://developers.openai.com/api/docs/guides/custom-mcp-server
- https://developers.openai.com/plugins/build/auth

Essas referências foram consultadas em 2026-10-07; acesso/compatibilidade da conta precisam ser comprovados na implementação.
