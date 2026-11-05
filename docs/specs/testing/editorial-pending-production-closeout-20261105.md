# Recibo produtivo — diagnóstico de pendências editoriais

05/11/2026. WFLOW-20261105-EDITORIAL-PENDING-DETAILS / FEAT-MCP-001 revisão 1.10. Esta verificação não criou, alterou, submeteu, aprovou ou publicou mercados; o mercado 62 permaneceu apenas como referência histórica.

## Integração e implantação

- [PR #186](https://github.com/wscardua/gotrendlabs/pull/186) integrada em `main` no SHA `2c799f621ff4a1d99f1d677335e58fec28d00295`. Branch local `fix/editorial-pending-details-20261105` preservada.
- [Actions da PR 42021443053](https://github.com/wscardua/gotrendlabs/actions/runs/42021443053): sucesso; build de produção e MCP, OpenAPI e suíte de 650 testes, com dois skips.
- [Actions de main 42023150193](https://github.com/wscardua/gotrendlabs/actions/runs/42023150193): sucesso; mesmos 650 testes, dois skips, e job de deploy concluído. SSM deploy `feccba4e-0c60-4270-a6bc-0d108d0eb0d0`: `Success`, código 0.
- SSM de leitura `fbe57b35-59fd-4dca-95a9-e216279153c6`: `Success`, código 0. Checkout no host no mesmo SHA; contêineres FastAPI e MCP em execução, MCP `healthy`. `GET /api/health` e metadata pública do recurso MCP responderam HTTP 200.

## Contrato e smoke MCP

O runtime MCP publicou `validate_market_draft` com scope `drafts:write` e schema de saída que exige `pending`, `pending_details` e `assessment_scope`; cada detalhe exige causa, descrição, critérios, trecho, etapa e impacto. O impacto de aprovação é `human_attestation_required`. Não houve novo scope, grant ou consentimento. A descrição da ferramenta esclarece que a análise é estrutural e de declarações explícitas.

`get_editorial_policy` retornou versão 1.4 e hash `5027fac6bd8449f91a4d8909913c5967aba559094b3049a9448615d8d7deb2b0`. A taxonomia foi consultada antes dos testes. Cinco chamadas somente a `validate_market_draft`, com ficha sintética, agenda futura, URL `example.org` de teste e sem alegação de pesquisa real, retornaram:

| Declaração no documento | Resultado |
| --- | --- |
| `Pendências para aprovação: nenhuma`, com e sem lista informativa fora de pendências | `structurally_valid=true`, `pending=[]`, `pending_details=[]` em ambos os casos |
| `Pendências humanas: responsável pela apuração e conferência da fonte (E10)` | `unresolved_editorial_gaps`; detalhe `human_task`, critério E10, etapa `before_human_approval`; criação/submissão `allowed`, aprovação `human_attestation_required` |
| `Pendências de pesquisa: fonte oficial ainda não identificada para a regra (E07)` | mesmo código geral; detalhe `research_or_rule_gap`, critério E07; sem novo bloqueio técnico de submissão |
| Ausência declarada e pendência humana explícita no mesmo documento | código geral com detalhe da tarefa e `contradictory_pending_declarations`; contradição sem critério inventado |

Todos os retornos incluíram `assessment_scope=structural_and_explicit_declarations_only` e `evidence_origin=agent_reported`. A lacuna de pesquisa é identificada quando declarada como tal, mas o validador não prova suficiência semântica nem bloqueia criação/submissão por essa classificação: o revisor humano deve resolver o mérito antes da aprovação. Esse limite preserva a política 1.4 e os gates efetivos. A declaração de ausência não apagou a pendência contraditória.

O cliente conectado expôs os novos campos nas respostas. A declaração de saída armazenada no catálogo desta conversa ainda descrevia o schema antigo; o schema publicado pelo runtime foi conferido diretamente. Uma captura HTTP bruta de `tools/list` autenticado e a atualização do catálogo exibido em conversa nova permanecem verificações de cliente, sem impedir a ativação confirmada pelo runtime e pelo retorno real.

## Estado

Esta revisão está ativa em produção. FEAT-MCP-001 continua `parcial` no conjunto da feature por homologações externas já registradas; esta fatia não tem pendência de implantação. Não foram exigidos migration, flag, ajuste de dados, permissão ou intervenção operacional adicional.
