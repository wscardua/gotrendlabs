# Radar MCP persistente no DEV — 2026-10-07

Workflow WFLOW-20261007-MCP-RADAR-DEV-001. Usuário autorizou explicitamente repetir o ensaio no banco DEV, com persistência, substituindo o isolamento anterior para esta execução.

Nota posterior: WFLOW-20261007-MCP-REVIEW-GATE-001 corrigiu o slug pelo editor humano. O draft #5 continua não publicado, agora revisão 4/preparation com parecer vazio e evidências invalidadas para nova revisão. O estado in_review/revisão 3 abaixo documenta o ensaio original. Fechamento preservado; mercados 1–3 intactos.

## Resultado visível

**Draft #5 — O lucro operacional GAAP da Tesla no 3T26 superará US$ 398 milhões?**

- [Ficha e revisão humana](http://localhost:8000/admin-ops/agent-reviews/5/).
- [Lista de rascunhos](http://localhost:8000/admin-ops/markets/?status=draft&order=display).
- [Editor humano](http://localhost:8000/admin-ops/markets/o-lucro-operacional-gaap-da-tesla-no-3t26-superara-us-398-milhoes/edit/).
- Banco `gotrendlabs`, host PostgreSQL `127.0.0.1`; API 8001, MCP através de 8000/mcp. Persistência real, sem cópia/fixture ou test runner de banco.
- Estado de mercado `draft`, editorial `in_review`, revisão 3, decisão humana vazia. Snapshot `6a33cf9d31198f6242e4c2267250286cbd21a27e002827005d590f1a3ee96ff5`.
- Categoria Negócios / Automotivo / Geral; binário Sim/Não; encerramento 20/10/2026 23:59 America/Sao_Paulo. Regras completas, fontes, fallback e critérios E01–E11 persistidos na ficha.

## Pesquisa e autenticação

Primeiro foram consultados política v1.2, taxonomia, catálogo completo DEV sem filtro de status, detalhes dos três mercados e métricas dos últimos sete dias. Nenhum draft equivalente existia. O mercado ID3 trata líder global EV 4T26, evento distinto de lucro trimestral Tesla. Previsões humanas/bots no período: 0/0, excluindo staff/superuser pelo contrato; analytics indisponível. Não inferir público produtivo nem equivalência com participantes acumulados mostrados na UI.

Fontes reabertas em 07/10 por volta de 17:07 UTC: [comunicado Tesla](https://ir.tesla.com/press-release/tesla-third-quarter-2026-production-deliveries-and-deployments), [índice RI](https://ir.tesla.com/) e [SEC 2T26](https://www.sec.gov/Archives/edgar/data/1318605/000162828026049270/tsla-20260630.htm). Divulgação prevista para 21/out, resultado financeiro 3T ainda ausente do índice; US$398 milhões corresponde à linha histórica de lucro operacional do 2T. Fonte futura classificada como validável, sem alegar comprovação do resultado desconhecido. Pergunta de entregas 3T descartada por resultado já conhecido; liderança EV descartada por repetição. Sem cota obrigatória de diversidade.

OAuth interativo local real: registro de cliente público, PKCE S256, consentimento pelo navegador com sessão administrativa existente, retorno loopback conferindo state/issuer, token com audience MCP e delegação para FastAPI. Integração existente `myintegration`; nenhum token staff foi entregue ao MCP. Token antigo do LM Studio respondeu 401, por isso não foi reutilizado. Credenciais de serviço existentes não foram alteradas. Tokens temporários apenas em memória; grant deste ensaio revogado ao final e revogação confirmada por consulta somente leitura. Registro público do cliente permanece para auditoria.

## Testes no DEV

**21 chamadas reais, dez ferramentas, 18 respostas positivas e três recusas esperadas.**

| Ferramenta | Chamadas |
| --- | ---: |
| `get_editorial_policy` | 1 |
| `get_taxonomy` | 1 |
| `search_markets` | 4 |
| `get_market` | 5 |
| `get_editorial_signals` | 1 |
| `validate_market_draft` | 1 |
| `create_market_draft` | 3 |
| `update_market_draft` | 3 |
| `submit_draft_for_review` | 1 |
| `get_draft_review` | 1 |

- Criação e replay idêntico retornaram o mesmo ID; uma única linha nova e consumo de 1 draft na cota diária.
- Reutilizar chave com título diferente retornou `idempotency_conflict`.
- Atualização válida gerou revisão 2; tentativa com revisão antiga retornou `version_conflict`.
- Submissão gerou revisão 3 e snapshot; consulta confirmou ficha/estado sem parecer inventado.
- Editar após submissão retornou `draft_not_editable`; releitura confirmou conteúdo/revisão preservados.
- Busca final retornou exatamente o draft criado.
- **63 logs**, todos correlacionados por execução/request, associados ao grant deste cliente; logs anteriores da integração excluídos da contagem.
- Consulta PostgreSQL independente com transação read-only confirmou persistência, estado, hash, cota e os **três registros anteriores integralmente inalterados**, comparando hashes das linhas antes/depois. Total de mercados passou de 3 para 4. Nenhum reset, flush, publicação, resolução ou cancelamento.
- Chrome: lista de mercados mostra título, Rascunho e classificação; ficha mostra título, Em revisão, Revisão 3, pendências e histórico. Abas mantidas abertas para o usuário.

## Correções encontradas durante o ensaio

1. Consentimento Django convertia QueryDict usando `dict()`, produzindo listas incompatíveis com `dict[str,str]` da API. Corrigido para `request.GET.dict()`. Teste `tests.test_mcp_consent_query` cobre GET e POST preservando os parâmetros escalares e limpeza da sessão após consentimento. **1 teste passou**, sem criar/conectar banco de teste. OAuth real no navegador passou depois da correção.
2. Detalhe da revisão recebia id/status/slug, sem título. Consulta agora inclui título; recarga real do painel confirmou apresentação do nome da pergunta em vez do identificador técnico. Sem mutação do mercado.

Ruff F, Django system check, snapshot OpenAPI e diff check aprovados. Contratos de autenticação/escopos mantidos; correção nullable anterior também foi exercitada pelos três mercados legados sem fechamento. Suíte destrutiva/fixtures não foi executada contra DEV.

## Limites e continuidade

Pendências humanas E07, E09, E10, E11 e lacunas declaradas: acompanhamento antecipado, prévia/imagem/avisos/tradução, responsável disponível e conferência final. Não foi registrado parecer humano nem publicado. Feature continua parcial; este resultado comprova OAuth local e SDK real, não homologa Dot/LM Studio, HTTPS externo ou carga/concurrency produtiva. Exaustão de cota e alteração concorrente por outro operador não foram provocadas no banco compartilhado.

Evidências locais ignoradas: `.runtime/radar-dev/` contém contexto, plano sem tokens, respostas por chamada, report.json, baseline-db.json e audit.json. Script manual `run.py` exige novo consentimento, checa duplicidade e usa chaves estáveis; não deve ser tratado como job ou rodado cegamente após mudança de data/política. Para novo radar, reconsultar fontes e catálogo. Para conferir o resultado atual, usar os links acima, sem criar outro draft.
