# Correção da prévia do slider — validação produtiva

Em 2026-10-12, a correção da FEAT-PRED-001 v0.6 foi implantada pela [PR #164](https://github.com/wscardua/gotrendlabs/pull/164), merge `0fddd544861334c245ee24a7e3163fc8c40e75ac`. As PRs #162/#163 anteriores eram de analytics e não corrigiram este incidente.

## Evidências

- [CI da PR](https://github.com/wscardua/gotrendlabs/actions/runs/38288512471) e [CI/deploy da main](https://github.com/wscardua/gotrendlabs/actions/runs/38289674859): sucesso; 503 testes Django, 2 skips por execução, build, snapshot OpenAPI e testes JavaScript aprovados.
- SSM do deploy `a9cc1689-364c-4a16-8ed4-27b01bc06ed4`: Success. Nenhuma migration ou configuração adicional necessária.
- `GET /api/health`: API e banco `ok`.
- Prévia HTTPS do mercado `qual-novela-vencera-o-emmy-internacional-2026`, com CSRF válido e `stake_amount=137`: HTTP 200, `X-GTL-Preview: 1`, `Cache-Control: no-store`, valor 137 GT₵ no fragmento e ausência de erro.
- Segunda chamada com valor inválido: mensagem inline, sem 500. Nenhuma confirmação de previsão ou movimento de saldo foi executado.
- Assets HTTPS idênticos ao código validado, SHA-256: `prediction-preview.js` = `bca1f6ec38529fa460d28366e9a8f2d75e63e7ccec7d3bdc80be23e82b0ceb0c`; `gotrendlabs.js` = `d3fab620322bf37fa076cc46790d2130e96820e39d84af6f20c9118070f5b7f3`.
- Chrome real com o JS baixado de produção e respostas simuladas: 500 movimentos consolidados em uma chamada; uma chamada em andamento por ticket; último valor prevalece; corpo HTML de HTTP 500 não entra no ticket. O ensaio de rajada não atingiu produção.
- SSM read-only `66d95802-3da8-4547-9310-bf7a79f55b2b`: host no SHA esperado, contêineres ativos, Django recriado às `2026-10-12T18:26:53Z`; zero novos HTTP 500 no Django/API e zero mensagens de slots esgotados nos logs dos contêineres recriados até o smoke.

## Limites e operação

A janela de logs observada após o deploy foi curta; não representa teste de capacidade global. O diagnóstico anterior confirmou limite de 79 conexões PostgreSQL e rajadas desnecessárias de consultas. A correção reduz a origem dessas rajadas e trata falhas de forma recuperável; não altera capacidade ou política global de conexões.

Páginas abertas antes da implantação precisam ser recarregadas. O mobile consome diretamente a FastAPI e não precisou mudar nesta correção. MCP não exige ajuste de ferramentas, schemas, contratos públicos, permissões, erros, replays ou orientação editorial. Branch local preservada.
