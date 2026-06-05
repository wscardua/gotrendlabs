# Relatorio de QA - Simulacao hard com 100 usuarios

Data da rodada: 2026-05-20
Ambiente web: `http://127.0.0.1:8000/`
Backend API: `http://127.0.0.1:8001`
Run: `qa_hard_20260520_100u`
Usuario administrativo: `admin@gotrendlabs.com.br`

## Resumo executivo

A rodada executou 100 usuarios simulados com operacao profunda e administracao paralela. Nao houve divergencia critica nos calculos auditados.

- usuarios operados: 100 (100 criados nesta rodada, 0 reutilizados)
- mercados QA criados/publicados: 6
- mercados resolvidos: 4
- mercado cancelado/refundado: `qa-hard-20260520-100u-esportes-final`
- previsoes resolvidas auditadas: 202 (168 vencedoras, 34 perdedoras)
- previsoes canceladas/refundadas auditadas: 49
- comentarios: 100; sugestoes: 100; feedbacks: 100
- moderacoes: 8; acoes de fila: 20
- pos-checagem: 100/100 usuarios ficaram com 3 previsoes registradas

## Cobertura operacional

- Usuarios: cadastro preparado no banco por causa do reCAPTCHA ativo, depois operacao autenticada real por API: perfil, wallet, ledger, badges, ranking, mercados, view/share, preview, previsao, comentario, reacoes, sugestao e feedback.
- Admin: login real como `admin@gotrendlabs.com.br`, dashboard, usuarios, ajuste de wallet, desativacao/reativacao, badge, mercados, publicacao, lock, resolucao, cancelamento/refund, moderacao e filas.
- Web: paginas publicas principais verificadas por HTTP no host `127.0.0.1:8000`.

## Mercados da rodada

| Mercado | Status final | Previsoes | Observacao |
| --- | --- | ---: | --- |
| `qa-hard-20260520-100u-clima-energia` | `resolved` | 51 | resolvido |
| `qa-hard-20260520-100u-esportes-final` | `canceled` | 49 | cancelado/refund |
| `qa-hard-20260520-100u-ia-modelo` | `resolved` | 50 | resolvido |
| `qa-hard-20260520-100u-politica-regulacao` | `resolved` | 51 | resolvido |
| `qa-hard-20260520-100u-saude-app` | `open` | 49 | permanece aberto |
| `qa-hard-20260520-100u-streaming-vencedor` | `resolved` | 50 | resolvido |

## Auditoria de coins, ledger, reputacao e badges

- divergencias wallet vs ledger: 0
- divergencias reputacao vs formula K=10: 0
- inconsistencias em previsoes resolvidas: 0
- inconsistencias em cancelamento/refund: 0
- badges duplicados por usuario/badge: 0

| Badge | Concessoes |
| --- | ---: |
| `first_resolution` | 100 |
| `founding_member` | 100 |
| `market_scout` | 10 |
| `qa-hard-20260520-100u-two-resolutions` | 68 |
| `top_ten` | 4 |

## Consideracoes dos usuarios simulados

- 25 usuarios: Ledger e carteira sao uteis, mas faltam links para mercado/previsao.
- 25 usuarios: Fluxo de previsao e comentario funcionou sem bloqueio.
- 25 usuarios: Criterio de resolucao poderia aparecer com mais destaque.
- 25 usuarios: Retorno estimado deveria explicar melhor refund + payout.

## Achados e melhorias

1. **MEDIA - usuarios**: 29 usuarios geraram avisos nao bloqueantes no harness de simulacao. A pos-checagem no banco mostrou 100/100 usuarios com 3 previsoes registradas, e as validacoes de wallet, ledger, reputacao, resolucao, cancelamento e badges ficaram zeradas. Recomendacao: na proxima rodada, persistir tambem o detalhe bruto por usuario para diferenciar aviso de harness, resposta esperada de contrato e erro de produto.

Melhorias recomendadas pelo coordenador:

- Expor no detalhe do mercado um resumo mais direto de como o retorno estimado vira `prediction_refund` + `prediction_payout` apos resolucao.
- Linkar lancamentos do ledger ao mercado/previsao de origem para auditoria do usuario final.
- Adicionar uma visao operacional por `run_id`/lote para QA e simulacoes, evitando misturar dados de rodadas diferentes no banco local.
- Destacar fonte, criterio e timezone na tela publica de mercado resolvido.

## Evidencias tecnicas

- HTTP status observados: `{200: 1550, 409: 7, 201: 600}`
- paginas web verificadas:
  - `/`: status 200, 1074 ms, html 55411 bytes
  - `/login/`: status 200, 15 ms, html 3640 bytes
  - `/register/`: status 200, 160 ms, html 9766 bytes
  - `/categories/`: status 200, 183 ms, html 52199 bytes
  - `/rankings/`: status 200, 801 ms, html 11161 bytes
  - `/badges/`: status 200, 40 ms, html 9499 bytes
  - `/suggestion/`: status 200, 14 ms, html 4637 bytes
  - `/feedback/`: status 200, 15 ms, html 4286 bytes
  - `/concepts/`: status 200, 13 ms, html 9450 bytes
  - `/security/`: status 200, 14 ms, html 8912 bytes
  - `/admin-ops/`: status 200, 26 ms, html 3640 bytes
- eventos mais lentos observados:
  - `GET /rankings`: 200, 7692 ms
  - `GET /rankings`: 200, 7691 ms
  - `GET /rankings`: 200, 7642 ms
  - `GET /rankings`: 200, 7613 ms
  - `GET /rankings`: 200, 7587 ms

## Conclusao

A plataforma suportou a rodada hard com 100 usuarios e operacao administrativa paralela sem divergencia critica nas regras auditadas de coins, ledger, reputacao, resolucao, cancelamento/refund ou badges. Os principais pontos sao melhorias de clareza para usuario final e rastreabilidade de QA.
