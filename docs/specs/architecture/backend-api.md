# Backend API

## Responsabilidades

- Ser a fonte principal da verdade do domínio.
- Autenticar usuários e emitir/validar sessão.
- Expor contratos JSON consumidos pelo frontend e pelo admin.
- Centralizar regras de mercado, previsão, stake, wallet, reputação, ranking e resolução.
- Emitir eventos de negócio consumidos por `communications` e `scheduler-jobs`.

## Não Responsabilidades

- Renderizar interface final.
- Definir templates de comunicação.
- Manter lógica operacional escondida em painéis de admin.

## Requisitos estruturais

- Todas as mutações relevantes devem ser auditáveis.
- Estados de mercado devem ser explícitos e consistentes.
- Regras de saldo devem usar ledger, não apenas campo de total agregado.
- Erros devem ser previsíveis e mapeados para UX e operação.
