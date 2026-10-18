# Aceite vigente — etapas do Painel de contratos (18/10/2026)

Feature: FEAT-RESOLUTION-AGENDA-001 v1.2. Workflows: WFLOW-20261018-CONTRACTS-TIMELINE e WFLOW-20261018-CONTRACTS-TIMELINE-CLOSEOUT. [Estado de publicação e evidências](contracts-timeline-closeout-20261018.md). Este aceite substitui as alternativas visuais anteriores preservadas no workflow.

## Estados e registros

| Cenário | Resultado esperado |
|---|---|
| draft/scheduled/open | Não concluir fechamento pelo relógio; publicação só é registro efetivo com published_at. |
| open/scheduled com closure_inconsistent | Fechamento pendente de operação, pelo código da API. |
| locked/resolved/sealed | Fechado; close_at identificado como horário programado, sem timestamp efetivo fabricado. |
| previsão futura/vencida/ausente | Planejada / Previsão vencida pelo código resolution_overdue / Não informada; nunca ativa ou concluída. |
| resolved/sealed/canceled | Previsão histórica, sem obrigação futura de apuração. |
| canceled sem resolução/selagem | Não se aplica. |
| criação/publicação/resolução/selagem com data | Registro efetivo, com data e fuso; circle distingue registros de horários previstos. |
| terminal sem data efetiva | Resolvido/Selado — data não registrada, sem inventar instante. |
| selagem ainda ausente | Prazo previsto distinto de sealed_at; prazo vencido não conclui etapa. |
| resolução desfeita | Retorna a locked conforme backend, sem resolved_at/seal_due_at; agenda e histórico preservados. |
| reagendamento | Previsão original, versão, histórico, critérios e provas preservados; sem mutação pela renderização. |

## Timeline e navegação

- Marcos ordenados por instante, inclusive resolução antecipada; empates têm ordem estável e Mesmo instante.
- Hoje entra na sequência no instante de referência. Marcos no mesmo dia exibem Hoje com horário no fuso correspondente; data completa/fuso nos textos acessíveis.
- Largura adicional cresce linearmente à duração na janela de toda a consulta, com piso de 136px para rótulos. É escala adaptada, sem proporcionalidade linear pura. 1h ocupa menos que 20 dias.
- Intervalos em dias/horas/minutos ficam acima das ligações; linhas sem ramificações, nomes/datas alinhados, Hoje com traço vertical verde.
- Sem data fica à direita na mesma linha em todas as larguras; nenhuma posição temporal fictícia. Todas as etapas abertas permanecem abaixo.
- Cada região focável usa aria-labelledby com Cronograma + título do próprio mercado, IDs únicos e aria-describedby com instrução de rolagem. Cobrir lista inicial e Carregar mais e títulos com caracteres especiais.
- Filtros/ordenação/contadores conservam autoridade API e abrangência explícita. Carregar mais cumulativo de 10 mantém a geometria das linhas já carregadas.
- Chrome 1440×1000/390×844, temas claro/escuro desktop, teclado e ausência de overflow da página; rolagem horizontal restrita à faixa.

## Execução e limites

41 testes de agenda, renderização e integração em PostgreSQL 16 dedicado aprovados em 11.578s no fechamento, incluindo a matriz acima e o fluxo real de resolução/undo/cancelamento/assinaturas. Checks e comando reproduzível no recibo. A rodada pura de apresentação/regras tem 23 testes, incluídos nessa execução, sem somar contagens sobrepostas.

QA visual com fixtures locais e assets reais; captura final e árvore de acessibilidade do Chrome verificadas. VoiceOver nativo e fontes ampliadas não executados. Sem mudança API/OpenAPI/MCP/Flutter, migration, flag ou backfill. Produção ainda não recebe esta correção até o CI/merge/deploy aprovado.
