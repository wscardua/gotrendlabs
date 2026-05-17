# Database

## Responsabilidades

- Persistir usuários, perfis, mercados, opções, previsões, ledger da wallet, comentários, sugestões, decisões de moderação e histórico operacional.
- Garantir integridade relacional e rastreabilidade temporal.
- Suportar consultas transacionais e relatórios administrativos.

## Diretrizes

- Modelos críticos devem preservar histórico quando o produto exigir auditabilidade.
- Wallet deve usar razão de transações (`ledger`) em vez de depender apenas de saldo derivado.
- Resolução de mercado deve registrar origem, operador, evidência e data efetiva.
- Sempre que possível, usar identificadores estáveis independentes de textos traduzidos.

## Não Responsabilidades

- Aplicar regra de negócio isoladamente.
- Calcular reputação ou probabilidades fora do backend.
