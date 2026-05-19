# Relatorio de QA - Simulacao de encerramento administrativo de mercados

Data da rodada: 2026-05-19  
Ambiente: `http://127.0.0.1:8000/` + `http://127.0.0.1:8001`  
Run: `qa_20260519_admin_resolution`  
Usuario administrativo: `admin@orynth.local`  
Fonte simulada de resolucao: `https://example.com/qa-resolution/20260519`

## Resumo executivo

A rodada administrativa resolveu 3 mercados ainda abertos usando o usuario `admin@orynth.local`. Foram conferidos status do mercado, opcao vencedora, eventos administrativos, previsoes resolvidas, entradas de ledger, saldos de wallet, reputacao e badges.

Resultado principal: todas as conferencias numericas da rodada nova passaram. Nenhuma correcao de codigo foi aplicada.

## Mercados resolvidos nesta rodada

| Mercado | Vencedor | Previsoes | Vencedores | Perdedores | Status |
| --- | --- | ---: | ---: | ---: | --- |
| `teste-ia-open-source-2027` | SIM (`129`) | 17 | 9 | 8 | aprovado |
| `resolucao-mvp-teste` | NAO (`144`) | 12 | 5 | 7 | aprovado |
| `cancelamento-refund-teste` | SIM (`135`) | 11 | 6 | 5 | aprovado |

Totais da rodada:

- mercados resolvidos: 3
- previsoes abertas liquidadas: 40
- vencedores: 20
- perdedores: 20
- entradas `prediction_refund`: 20
- entradas `prediction_payout`: 20
- entradas `prediction_loss`: 20
- novos badges: 40
- erros de validacao: 0

## Conferencias realizadas

Para cada mercado, foi feita fotografia antes/depois dos usuarios afetados e das previsoes abertas. A validacao comparou o resultado real com as regras atuais do backend:

- vencedor: `prediction_refund` libera o stake, `prediction_payout` credita o ganho liquido;
- perdedor: `prediction_loss` liquida o stake bloqueado;
- saldo esperado do vencedor: `available_oc += potential_payout`, `locked_oc -= stake`, `total_earned_oc += potential_payout - stake`;
- saldo esperado do perdedor: `available_oc` inalterado, `locked_oc -= stake`, `total_earned_oc` inalterado;
- reputacao: delta calculado por probabilidade de entrada, contador de resolvidas, acuracia e streak;
- badges: motor de badges acionado apos resolucao do mercado;
- eventos admin: `market.lock` e `market.resolve` criados para cada mercado.

As rotas de base tambem responderam:

- web `http://127.0.0.1:8000/`: `200`
- API health `http://127.0.0.1:8001/health`: `200`

## Evidencias por mercado

### `teste-ia-open-source-2027`

- status antes: `open`
- `POST /admin/markets/teste-ia-open-source-2027/lock`: `200`, status `locked`
- `POST /admin/markets/teste-ia-open-source-2027/resolve`: `200`, status `resolved`
- resultado final: `SIM`, opcao `129`
- previsoes: 17 resolvidas, 0 abertas
- ledger: 9 refunds, 9 payouts, 8 losses
- novos badges: 17 `first_resolution`
- eventos: `market.lock` (`202`), `market.resolve` (`203`)

### `resolucao-mvp-teste`

- status antes: `open`
- `POST /admin/markets/resolucao-mvp-teste/lock`: `200`, status `locked`
- `POST /admin/markets/resolucao-mvp-teste/resolve`: `200`, status `resolved`
- resultado final: `NAO`, opcao `144`
- previsoes: 12 resolvidas, 0 abertas
- ledger: 5 refunds, 5 payouts, 7 losses
- novos badges: 11 `first_resolution`, 1 `top_ten`
- eventos: `market.lock` (`204`), `market.resolve` (`205`)

### `cancelamento-refund-teste`

- status antes: `open`
- `POST /admin/markets/cancelamento-refund-teste/lock`: `200`, status `locked`
- `POST /admin/markets/cancelamento-refund-teste/resolve`: `200`, status `resolved`
- resultado final: `SIM`, opcao `135`
- previsoes: 11 resolvidas, 0 abertas
- ledger: 6 refunds, 6 payouts, 5 losses
- novos badges: 11 `first_resolution`
- eventos: `market.lock` (`206`), `market.resolve` (`207`)

## Amostras de saldo e ledger

As amostras abaixo foram conferidas contra a regra de distribuicao.

| Mercado | Usuario | Predicao | Resultado | Stake | Payout total | Delta wallet | Ledger |
| --- | ---: | ---: | --- | ---: | ---: | --- | --- |
| `teste-ia-open-source-2027` | 46 | 102 | venceu | 120 | 240 | `+240 available, -120 locked, +120 earned` | refund + payout |
| `teste-ia-open-source-2027` | 48 | 104 | perdeu | 70 | 314 | `0 available, -70 locked, 0 earned` | loss |
| `resolucao-mvp-teste` | 92 | 142 | venceu | 10 | 30 | `+30 available, -10 locked, +20 earned` | refund + payout |
| `resolucao-mvp-teste` | 1 | 116 | perdeu | 80 | 160 | `0 available, -80 locked, 0 earned` | loss |
| `cancelamento-refund-teste` | 117 | 156 | venceu | 120 | 240 | `+240 available, -120 locked, +120 earned` | refund + payout |
| `cancelamento-refund-teste` | 108 | 147 | perdeu | 25 | 56 | `0 available, -25 locked, 0 earned` | loss |

## Badges e metricas sociais

Os badges criados foram coerentes com as regras ativas:

- `first_resolution`: regra `resolved_predictions_count >= 1`;
- `top_ten`: regra `ranking_position <= 10`.

Foram criados 40 badges na rodada:

- 39 `first_resolution`;
- 1 `top_ten`.

Nao houve duplicacao para usuarios que ja possuiam o mesmo badge, porque a tabela usa conflito por usuario/badge e o motor usa `ON CONFLICT DO NOTHING`.

## Achados

### 1. Mercado cancelado ainda possui previsoes abertas

Severidade: alta.

O mercado `pergunta22` esta com `status = canceled`, mas ainda possui 8 previsoes com `status = open`.

Distribuicao encontrada:

- `SIM` (`74`): 2 previsoes, stake 60
- `NAO` (`75`): 4 previsoes, stake 300
- `TALVEZ` (`76`): 1 previsao, stake 200
- `MAIS UMA` (`77`): 1 previsao, stake 150

Risco: usuarios podem ficar com saldo bloqueado ou ledger inconsistente quando um mercado cancelado nao liquida/refunda previsoes abertas.

Recomendacao: revisar o fluxo de cancelamento e adicionar teste/regra de integridade para garantir que `market.cancel` sempre transforma previsoes abertas em canceladas/refundadas, com ledger de release correspondente.

### 2. Rodada anterior deixou alguns mercados ja resolvidos

Severidade: baixa para produto, media para rastreabilidade de QA.

Antes desta nova rodada, os mercados abaixo ja estavam resolvidos, por isso nao foi possivel fazer auditoria completa de antes/depois nesta execucao:

- `sim-mercado-eleicoes-tech-2026`: `Privacidade` (`85`)
- `lider-vendas-ev-4t26`: `BYD` (`6`)
- `pergunta11`: `SIM` (`64`)
- `auditoria-distribuicao-mvp`: `Azul` (`145`)

Recomendacao: usar um `run_id` unico e persistir um artefato JSON da fotografia antes/depois quando rodadas de QA modificarem banco local. Isso evita perda de rastreabilidade quando uma simulacao e repetida.

## Conclusao

A parte administrativa de fechamento manual e resolucao funcionou corretamente nos 3 mercados auditados nesta rodada. A distribuicao de saldos, ledger, reputacao, badges e eventos administrativos bateu com as regras atuais.

O principal ponto de ajuste antes de evoluir a implementacao e corrigir ou criar protecao para o caso de mercado cancelado com previsoes ainda abertas.

## Reexecucao apos ajuste

Data da reexecucao: 2026-05-19  
Comando de auditoria: `python manage.py reconcile_canceled_market_refunds --dry-run`  
Comando de correcao aplicado: `python manage.py reconcile_canceled_market_refunds --slug pergunta22`

Resultado antes da correcao:

- `pergunta22`: 8 previsoes abertas em mercado `canceled`
- stake bloqueado afetado: 710 OC

Resultado da reconciliacao:

- previsoes canceladas: 8
- refunds `prediction_refund` criados: 8
- valor total liberado: 710 OC
- evento administrativo criado: `market.cancel_reconcile`
- nota: `qa_20260519_rerun: reconciliar mercado cancelado com previsoes abertas`

Resultado depois da correcao:

- nenhum mercado `canceled` com previsoes `open` encontrado pelo dry-run;
- `pergunta22` ficou com 0 previsoes abertas e 8 previsoes canceladas;
- teste focado `test_reconcile_canceled_market_refunds_open_prediction_orphans` passou.
