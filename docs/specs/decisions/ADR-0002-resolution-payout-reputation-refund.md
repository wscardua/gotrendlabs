# ADR-0002: Fórmula MVP de resolução, payout, reputação e refund

## Status

Aceita para MVP.

## Decisão

Resolução manual de mercado usa a fórmula da spec-mãe:

- `reward_bruto = stake * (1 / p)`
- `delta_R = 10 * (1 - p)` quando a previsão acerta
- `delta_R = -10 * p` quando a previsão erra

`p` é a probabilidade da opção escolhida no momento da entrada (`probability_at_entry`) convertida para fração decimal. Reputação mínima é `0`.

O stake vencedor é liberado por `prediction_refund`; o ganho acima do stake é creditado por `prediction_payout`. O stake perdedor é baixado por `prediction_loss` com `direction="settle"`.

Cancelamento de mercado aplica refund total: previsões abertas viram `canceled`, stakes bloqueados voltam ao saldo disponível por `prediction_refund`, e reputação não muda.

Mercado já `resolved` não deve ser cancelado diretamente pelo fluxo de refund. A ação operacional equivalente é desfazer a resolução: o mercado retorna para `locked`, o payout líquido é estornado por `prediction_payout_reversal`, stakes são rebloqueados por `prediction_resolution_relock`, previsões voltam a ficar pendentes de resultado e reputação é recalculada.

A resolução manual deve registrar `resolved_at` como data/hora efetiva da decisão e `resolution_timezone` como timezone controlado selecionado pelo operador. A UI administrativa pode pré-preencher esses campos, mas deve permitir ajuste antes da publicação.

## Consequências

- Wallet permanece conciliável pelo ledger.
- Ranking passa a refletir mercados resolvidos.
- Cancelamento fica operacionalmente previsível e reduz risco de perda indevida por erro editorial.
- Correção pós-resolução preserva a fila de decisão e evita transformar um mercado com resultado aplicado em cancelamento definitivo por engano.
- Fórmulas futuras podem amortecer concentração, mas exigem nova decisão técnica.
