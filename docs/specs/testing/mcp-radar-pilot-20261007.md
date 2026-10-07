# Radar editorial MCP — ensaio de 7 de outubro de 2026

Workflow: WFLOW-20261007-MCP-RADAR-PILOT-001, vinculado à FEAT-MCP-001 e ao workflow documental. Resultado local concluído; feature continua parcial por homologação externa.

## O que foi executado

Codex fez a seleção editorial e a pesquisa web; um cliente MCP SDK real executou o plano sobre Streamable HTTP, com troca HTTP de credencial de serviço por token, delegação e regras reais da FastAPI. Adaptador em processo separado sem ambiente de banco; PostgreSQL descartável `test_gtl_mcp_radar`. Sem mocks nas respostas das tools desse cenário. O ensaio não mede capacidade de tool calling do modelo do LM Studio nem valida Dot, HTTPS externo ou carga produtiva.

Primeiro foi lido o catálogo público do DEV local, sem alterações. Seus três mercados e sua taxonomia foram copiados como fixtures mínimas, sem usuários, previsões, analytics ou histórico de integridade. A cópia serve para consulta editorial; não reproduz o banco completo. Produção, drafts privados e cancelados não foram consultados. Dados financeiros externos são pesquisa real em fontes públicas.

## Decisão editorial

**O lucro operacional GAAP da Tesla no 3T26 superará US$ 398 milhões?**

- Formato: binário, Sim/Não. Taxonomia existente: Negócios / Automotivo / Geral.
- Participação: até **20/10/2026 23:59 America/Sao_Paulo**; divulgação prevista no dia seguinte, após fechamento da bolsa.
- Unidade: lucro operacional GAAP consolidado, USD milhões, apenas três meses encerrados em 30/09/2026. Sim se estritamente maior que 398; igualdade conta como Não. Sem lucro líquido, EBITDA ou acumulado anual.
- Apuração: em 01/12/2026 após 09:00 BRT, usando documentos/correções oficiais disponíveis até 30/11 às 23:59 BRT. Primária: documento Q3 2026 no índice RI; fallback: 10-Q/10-Q-A do mesmo trimestre. Ausência não conta como Não; encaminhar ao operador conforme regra de cancelamento. Documento futuro ainda não disponível na consulta.
- Justificativa: comparar entregas e desempenho operacional cria uma pergunta educativa com evento de acompanhamento. Hipótese de retorno do público, sem previsão quantitativa ou alegação de tendência social.
- Concentração: há mercado de liderança EV 4T26; outro trimestre e outro indicador não são o mesmo resultado. Ainda é necessário buscar drafts privados e produção. Diversidade considerada sem cota obrigatória.

Fontes abertas em **07/10/2026, 16:51 UTC**: o [comunicado de entregas](https://ir.tesla.com/press-release/tesla-third-quarter-2026-production-deliveries-and-deployments) informa divulgação financeira em 21/out; o [índice de RI](https://ir.tesla.com/) permite localizar documentos por trimestre; o [10-Q do 2T26](https://www.sec.gov/Archives/edgar/data/1318605/000162828026049270/tsla-20260630.htm) registra US$398 milhões na linha Income from operations. Este último verifica a referência histórica e o formato; não comprova o resultado futuro. A ficha contém URLs, horário, propósito, evidências E01–E11 e regras completas.

Pautas descartadas: entregas Tesla 3T26 acima de 450 mil (já conhecido); líder global EV 4T26 (mesmo evento já presente). A atividade recente no [changelog Qwen](https://docs.qwencloud.com/changelog/models) foi observada, mas não bastou para propor uma pergunta de lançamento com fonte e prazo maduros. Não foi criado draft para cumprir distribuição de temas.

## Ferramentas e evidências

17 chamadas: 16 positivas e 1 recusa esperada. Todas as 10 ferramentas disponíveis foram usadas.

| Ferramenta | Chamadas | Resultado |
| --- | ---: | --- |
| `get_editorial_policy` | 1 | Manual 1.2, checklist, ficha e 11 critérios consultados |
| `get_taxonomy` | 2 | 3 classificações, paginação em 2 páginas |
| `search_markets` | 4 | 3 mercados em 2 páginas; buscas Tesla e lucro |
| `get_market` | 2 | Catálogo legado nullable e conteúdo atualizado do draft |
| `get_editorial_signals` | 1 | 7 dias; 0 humanos/0 bots na fixture; analytics indisponível |
| `validate_market_draft` | 1 | Estrutura válida; pendências editoriais explícitas |
| `create_market_draft` | 2 | Criação e replay; mesmo ID, só 1 draft/cota |
| `update_market_draft` | 2 | Edição válida; edição após submissão recusada |
| `submit_draft_for_review` | 1 | Snapshot da revisão 3; estado in_review |
| `get_draft_review` | 1 | Ficha persistida; decisão humana vazia |

Resultado: **1 draft**, **3 revisões**, revisão final **3**, estado **in_review**, decisão humana vazia. ID 4 existe apenas no banco descartado, não é link para um mercado DEV. Snapshot `bdc1f849114f1ea5007bf6242bc7d8989492fef05d7bc0b0c1b7644f373911df`. Cota diária consumida: 1 draft, mesmo após replay. Cota de chamadas: 17. **51 logs centralizados, todos com execução/request correlacionados**, cobrindo API e adaptador. Validação da persistência feita pelo harness fora do MCP.

Pendências: **E03** cobertura completa da deduplicação; **E07** acompanhamento de divulgação antecipada; **E09** imagem/avisos/tradução/prévia; **E10** disponibilidade de responsável humano real; **E11** conferência final e parecer humano. O draft não está pronto para publicação. A identidade técnica da integração não preenche essas responsabilidades. Não há gate universal de publicação novo.

## Falha descoberta e corrigida

O endpoint de detalhe removia todos os valores null, inclusive `close_at` obrigatório-nullable. Isso fazia o MCP rejeitar mercados legados sem fechamento. Serialização agora omite somente campos não fornecidos: preserva `close_at`/`event_id` null e continua omitindo ficha editorial de outra integração. Regressões cobrem ambos os casos; o schema OpenAPI já descrevia esses nulls e permaneceu atualizado.

## Validação e reprodução

**4 testes passaram em 29,121 s**: ensaio acima, regressão de nullable, privacidade/permissões e cliente real com todas as tools em OAuth e serviço. O último fez outras 26 chamadas (22 positivas, 4 recusas esperadas). Ruff F e snapshot OpenAPI aprovados. PostgreSQL de teste destruído; processos efêmeros encerrados. Sem publicação, merge ou deploy.

```sh
.venv/bin/python ops/scripts/test_mcp_local.py \
  --db-admin-env ../gotrendlabs/.env.db-admin.local \
  --database gtl_mcp_radar \
  ops.scripts.mcp_radar_pilot.RadarPilot.test_run
```

Inputs públicos e plano: `tests/fixtures/mcp_radar_20261007/`. Saídas locais: `.runtime/radar-20261007/execute/`, incluindo discovery, cada resposta e report.json. Para somente observar, usar `GTL_RADAR_PHASE=observe`. O cenário é datado: depois do prazo ou mudança da política, deve falhar até uma nova pesquisa atualizar o plano; não se deve forjar relógio ou reaproveitar a pergunta resolvida. O comando não inicia pesquisa nem agenda execução automaticamente.

Para iniciar piloto persistente, repetir pesquisa e deduplicação com acesso ao catálogo autorizado, designar responsáveis e revisar pendências antes de aprovar operacionalmente. Dot/LM Studio e OAuth interativo externo ainda exigem homologação própria. Nenhum segredo compartilhado no chat foi utilizado; credenciais efêmeras ficam apenas em memória.
