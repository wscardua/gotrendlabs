# Frontend Web

## Responsabilidades

- Renderizar páginas públicas e autenticadas.
- Servir feed, detalhe de mercado, perfil, ranking, wallet e fluxos de autenticação.
- Fazer chamadas ao `backend-api` para leitura e mutações de domínio.
- Aplicar i18n, formatação local e textos não hardcoded.
- Usar HTMX para atualizações parciais e Alpine.js para estados locais simples.

## Não Responsabilidades

- Calcular stake, payout, reputação ou probabilidades.
- Resolver mercados.
- Consolidar regras de saldo.
- Persistir decisões de negócio fora dos contratos da API.

## Entradas e saídas

- Entrada: respostas do `backend-api`, contexto de sessão e traduções.
- Saída: páginas HTML, interações parciais, formulários e eventos de UI.

## Guardrails

- Toda ação mutável relevante deve passar pelo `backend-api`.
- Textos de interface devem estar preparados para `pt-BR` e `en`.
- Qualquer regra de exibição condicionada por estado de mercado deve depender de estados vindos do contrato de domínio.
