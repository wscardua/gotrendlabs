# Revisão de impacto — Analytics v0.6/v0.7

Data: 2026-10-12. Workflow: WFLOW-20261012-ANALYTICS-CLOSEOUT.

## Resumo e base

Nenhum problema identificável no diff. Base origin/main `cea46e24fa404fabb027210a4d0a5614b10e9d84`, atualizada por fetch. Branch `feature/analytics-platform-comparison`; revisão do diff da árvore de trabalho e dos arquivos novos destinados à entrega, ainda sem commits da feature. A reconciliação documental do fechamento também foi verificada.

## Escopo e contratos

Agregações FastAPI de comparação por plataforma, série diária UTC e recepção humana global; página Django, formatação local, filtros, navegação, gráfico e tabela progressiva. Specs, contrato administrativo, testes, aceites e memória operacional acompanham a entrega. GROUPING SETS mantém totais e plataformas no mesmo snapshot de cada consulta relevante. Identidade, ingestão, staff/MFA, exclusão de bots/staff e persistência continuam nos limites existentes. Não há migration, dependência ou nova fronteira arquitetural.

## Mobile e MCP

Flutter consome a ingestão existente, não o resumo administrativo; nenhum binário mobile ou contrato de escrita mudou. Web inclui navegação em celular. MCP não consome esse resumo e mantém Analytics indisponível em sua exposição atual; ferramentas, schemas, permissões, erros, replays e orientação editorial não exigem ajuste. Nenhuma permissão administrativa humana é inferida para agentes.

## Testes e evidências

17 testes de contrato, apresentação, usabilidade e navegação aprovados nesta preparação. Verificações de eventos web, sintaxe JS, snapshot OpenAPI e whitespace aprovadas. Três cenários de integração previamente aprovados em PostgreSQL com schema isolado cobrem comparação/filtros, concorrência de ingestão e saúde global por plataforma; esse método não replica FKs/triggers ou migrations. QA visual e cenários sintéticos renderizados com templates/assets reais estão registrados em [aceite de usabilidade](analytics-usability-acceptance.md) e [aceite da comparação](analytics-platform-comparison-acceptance.md).

## Risco e achados

Sem achado concreto de regressão, vulnerabilidade ou quebra de contrato introduzida. Risco residual de validação moderado até a aprovação da suíte completa da PR em PostgreSQL limpo; não autoriza merge com CI falhando. Zero eventos não prova ausência de usuários, coleta ou instalações; timestamps operacionais não são últimas remessas, e o histórico GeoLite não prova disponibilidade atual.

## Validação pendente e limites

Antes do merge: build e suíte normal com migrations no GitHub Actions. Após o merge: deploy main/SSM, SHA, saúde, contrato administrativo e assets atuais; registrar evidência produtiva sem eventos sintéticos. Toque físico, leitor de tela, outros navegadores e volume produtivo de 90 dias não homologados. Preparação para i18n não equivale a catálogo completo em inglês. Nenhuma implantação foi executada nesta revisão.
