# Retomada humana da ficha MCP — 2026-10-07

Workflow WFLOW-20261007-MCP-HUMAN-PREPARE-001, continuação do gate v1.1. Lacuna corrigida: usuário humano ficava impedido de retomar revisão depois que save do editor voltava o draft a preparação.

## Implementação e evidências

- PATCH administrativo de ficha validada com staff/superuser MFA; locks mercado/ficha, revisão otimista, snapshot imutável, evento humano `agent.record.human_update` e invalidação do parecer. Só draft; nenhuma permissão nova ao MCP ou migration necessária.
- Formulário de preparação com fontes, evidências/status E01–E11, perguntas do editorial atual, lacunas e nota obrigatória. Critérios recolhíveis e fontes por checkbox. Salvar ou salvar/enviar à revisão; parecer separado com fontes e critérios verificados independentemente. CSRF/PRG; contexto preservado quando uma decisão é recusada.
- 45 testes passaram em 130,785 s (exit 0): MCP editorial, publicação UI, consentimento e adapter. Incluem cliente SDK TCP real, OAuth/serviço e todas as dez tools existentes. Dois testes do fluxo humano foram repetidos após ajuste de mensagens/template: 6,320 s, exit 0.
- Novos casos: sem autenticação, membro, agente técnico ou staff sem MFA recusados; versão antiga 409; referências inválidas 422 sem incremento; humano salva/submete e decide; edição de ficha limpa aprovação; mercado aberto recusa escrita; pendência real não é satisfeita automaticamente, aprovação 422 mantém ficha em revisão; UI CSRF/PRG e erro com contexto.
- Ruff F, Django check, OpenAPI export/check e diff check aprovados. Documentos de feature/contrato/ADR/runbook/estado atualizados.
- Chrome real em DEV: draft #5 observado em preparation/revisão 6 após edições do usuário; nova seção/botões/perguntas conferidos. Nenhum save, reenvio, aprovação ou publicação do draft realizado pelo agente nesta rodada. Evidência `.runtime/mcp-human-review/review-actions.jpg` ignorada pelo Git.

## Como operar

Abra a ficha, atualize evidências/status/fontes/lacunas e a nota da atualização humana. Salve/envie para revisão; depois verifique independentemente as fontes/critérios, escreva parecer e escolha aprovar/devolver/rejeitar. Pendências e lacunas continuam impedindo aprovação. Publicar é ação separada no editor da versão aprovada.

Dot/HTTPS externo, deploy e homologação efetiva LM Studio continuam pendentes; feature permanece parcial. Sem execução em produção.
