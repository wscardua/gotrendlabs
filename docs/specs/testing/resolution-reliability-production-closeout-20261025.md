# Fechamento produtivo — resolução confiável (25/10/2026)

## Publicação e evidência

- [PR #177](https://github.com/wscardua/gotrendlabs/pull/177), merge `8343b90c45b1878934aba6892b161ceb689810e8`: resolução idempotente, confirmação de timeout, prazo de revisão pelo relógio do servidor, integridade por etapa, retorno da wallet e métricas finais. [CI da PR](https://github.com/wscardua/gotrendlabs/actions/runs/40205168186) e [CI/deploy da main](https://github.com/wscardua/gotrendlabs/actions/runs/40205958120) aprovados.
- [PR #178](https://github.com/wscardua/gotrendlabs/pull/178), merge `659e97625e03855c3572b55e7bc6ff1134e9d8b2`: migration `markets.0038_limit_resolution_request_privileges` e teste dos privilégios efetivos diante de defaults amplos. [CI da PR](https://github.com/wscardua/gotrendlabs/actions/runs/40207344805) e [CI/deploy da main](https://github.com/wscardua/gotrendlabs/actions/runs/40208226722) aprovados, incluindo testes, build e deploy.
- A correção pontual de ACL foi aplicada antes da PR #178 pelo SSM `d545e9f7-4e5c-4a67-bd68-aac31e4a3385`. Após o segundo deploy, o SSM de leitura `7e41f9ce-b4cf-4a44-98bf-0e9c7d0fbda8` confirmou HEAD `659e976`, migration `0038` marcada `[X]` e trigger `resolution_requests_append_only` ativo.

## Estado verificado em produção

| Verificação | Resultado |
| --- | --- |
| Recibos, role FastAPI | `SELECT=true`, `INSERT=true`, `UPDATE=false`, `DELETE=false` |
| Recibos, role Django | `SELECT=true`, `INSERT=false`, `UPDATE=false`, `DELETE=false` |
| Sequência do recibo | FastAPI `USAGE=true`, `UPDATE=false`; Django `USAGE=false` |
| `/api/health` | HTTP 200, `status=ok` |
| Mercado 35 público | HTTP 200, `resolved`, `100 GT₵`, `1 participante` |
| Verificação de integridade | HTTP 200, `verified`, `overall_valid=true`, compromissos e resultado válidos |
| Página pública | HTTP 200, exibe `GT₵ em previsões` |

O selo e a raiz Merkle aparecem como `null` na verificação porque a selagem ainda não havia ocorrido neste smoke; não foram antecipados. A auditoria do ledger na primeira publicação confirmou stake de 100 GT₵, liberação de 100 GT₵ e crédito de ganho líquido de 100 GT₵: retorno total 200 GT₵. Nenhuma nova resolução, crédito ou alteração das provas históricas foi feita nos smokes.

## Escopo remanescente

- O código Flutter da wallet/mercado foi integrado e testado, mas o workflow de deploy web/API não distribui binários mobile. A release do app continua separada.
- Timeout com KMS real e carga de wallet extensa não foram ensaiados em produção; replay/concorrência/rollback e privilégios foram cobertos por testes e banco isolado. A selagem futura do mercado 35 deve ser acompanhada pelo fluxo operacional próprio.
- Impacto MCP analisado: sem nova ferramenta, schema, scope, permissão, replay ou orientação editorial. As rotas administrativas exigem staff/MFA, sem inferir capacidade MCP a partir do Admin Ops. A imagem MCP passou pelo pipeline de produção.

Este recibo atualiza os estados dos workflows WFLOW-20261025-RESOLUTION-CLOSEOUT, WFLOW-20261025-RESOLUTION-RECEIPT-ACL, WFLOW-20261025-RESOLUTION-DISPLAY e WFLOW-20261025-RESOLUTION-RELIABILITY. Os relatórios locais anteriores continuam como histórico de implementação e testes.
