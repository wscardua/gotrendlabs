# Implantação — confiabilidade da resolução e apresentação pós-liquidação

## Estado

PRs #177 e #178 integradas em 2026-10-25 (merges `8343b90`/`659e976`); Actions de main `40205958120`/`40208226722`, incluindo deploy, aprovados. Migrations 0037/0038, ACL mínima e smoke do mercado 35 confirmados em produção. [Recibo produtivo](../testing/resolution-reliability-production-closeout-20261025.md). O código Flutter integrado ainda requer distribuição do app.

## Contratos e pré-requisitos

- POST administrativo resolve exige `expected_market_id` e UUID `idempotency_key`; GET de confirmação mantém staff/MFA. Recibo e efeitos são transacionais; nenhuma capacidade MCP adicional.
- Migration `markets.0037_market_resolution_request` cria recibos imutáveis. Em produção, defaults amplos exigiram revogação pontual após o primeiro deploy; `markets.0038_limit_resolution_request_privileges` estabelece ACL efetiva mínima para futuros ambientes. Aplicar ambas antes de considerar a configuração final concluída.
- `/users/me/ledger` inclui `resolution_returns` obrigatório; o app Flutter apresenta liberação, lucro líquido e retorno total. A web prioriza saldo e extrato sem painel adicional por mercado. Backend deve estar disponível com esse contrato antes de distribuir o novo app.
- Sem backfill, novas variáveis, segredos ou flags. Não reescrever provas, prazos ou pagamentos da primeira resolução. O prazo de revisão do servidor vale para novas resoluções.

## Publicação

1. Obter aprovação do título/descrição da PR; versionar todos os arquivos novos necessários. Preservar branch local.
2. Enviar branch, criar PR em português via GitHub MCP para main e esperar todos os checks do último SHA. Corrigir eventuais falhas e repetir apenas validações impactadas.
3. Fazer merge via GitHub MCP. Acompanhar `GoTrendLabs CI and Deploy` do merge; confirmar build das imagens principal e MCP, testes e deploy bem-sucedidos, não apenas sucesso da PR.
4. O deploy existente faz build, para escritores, aplica boundary/migrations, valida permissões, coleta estáticos e inicia serviços. Se `ENABLE_PROD_DEPLOY` impedir deploy, investigar configuração/estado antes de declarar a entrega ativa.
5. Em falha de migration, o deploy deixa escritores parados. Inspecionar erro e corrigir a causa; não iniciar runtime novo sem schema nem remover recibos para contornar erro.

## Verificação pós-deploy

- Confirmar SHA implantado correspondente ao merge e saúde de Django, FastAPI, daemon, proxy e MCP.
- Confirmar migration 0037 aplicada, tabela/sequência e trigger append-only ativos. Conferir SELECT/INSERT e uso da sequência com a role FastAPI efetiva; UPDATE/DELETE devem ser impedidos. Não imprimir credenciais ou dados pessoais.
- Consultar mercado 35 pelo slug `quem-avanca-a-final-da-libertadores-masculina-2026-fluminense-ou-palmeiras`: a auditoria inicial identificou 100 GT₵ e um participante humano. Validar a posição liquidada atual e o estado, sem presumir que já houve selagem.
- Confirmar API e página públicas preservando volume/participantes finais e rótulo de previsões. Conferir auditoria de integridade e apresentação conforme resultado autoritativo, sem antecipar selo pendente.
- Ler o ledger e a projeção de retorno da previsão auditada: registro original esperado 100 liberados + 100 líquidos = 200 recebidos. Não executar nova resolução ou lançar créditos para testar a UI. Conferir proteção de autenticação do endpoint administrativo novo.
- Confirmar que a imagem MCP inicia e as ferramentas/scopes permanecem; nenhuma configuração editorial deve ser alterada.
- Registrar URLs/SHA/status do Actions, migration, saúde, métricas e limites no aceite e no estado do projeto. Usar atualização documental posterior para evidências que só existem após o deploy.

## Limites e recuperação

Testes de idempotência, concorrência, desfazer/refazer e rollback são feitos em banco isolado. Perda de resposta com KMS real e performance de wallet extensa permanecem verificações específicas; não simular falha destrutiva em produção. A migration é aditiva; eventual rollback de código preserva recibos/provas. Não reverter migrations que removam o histórico produtivo.

O workflow atual não distribui binários Flutter. Publicação web/API pode ser concluída mantendo a release do app explicitamente pendente.

## Ajuste pós-deploy da ACL

O primeiro deploy pelo Actions 40205958120 funcionou e passou no smoke. A tabela nova recebeu default ACL `arwd` para FastAPI/Django; trigger append-only já impedia UPDATE/DELETE, mas a ACL excedia o contrato. SSM aplicou REVOKE pontual com a role proprietária e confirmou FastAPI (SELECT, INSERT; sem UPDATE/DELETE), Django (SELECT; sem escrita) e sequência FastAPI (USAGE/SELECT; sem UPDATE). A migration 0038 foi implantada pelo Actions 40208226722; o smoke SSM posterior confirmou migration aplicada e os mesmos privilégios mínimos. O ajuste não tocou a default ACL global, outras tabelas nem os dados resolvidos.
