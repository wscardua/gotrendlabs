---
id: FEAT-PRED-001
titulo: "Previsão e stake"
versao: 0.4
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-05-18
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - prediction-payloads.md
  - wallet-ledger.md
  - market-lifecycle.md
dependencias:
  - FEAT-AUTH-001
  - FEAT-MARKET-002
  - FEAT-WALLET-001
impacta:
  - frontend-web
  - backend-api
  - database
  - communications
aprovacao: pendente
---

# Previsão e stake

## Objetivo

Permitir que o usuário escolha uma opção em um mercado aberto e aplique stake usando moeda interna.

## Escopo incluído

- seleção de opção
- entrada de stake
- validação de saldo
- prévia de retorno sem efeito colateral
- confirmação da previsão
- atualização do snapshot de probabilidade
- histórico visual de consenso derivado das previsões registradas

## Escopo excluído

- trading em tempo real
- revenda de posição
- atualização live por websocket
- tabela materializada de histórico de snapshots

## Fluxo do usuário

Usuário autenticado acessa um mercado aberto, escolhe uma opção, informa stake, confirma a ação e recebe retorno com saldo e snapshot atualizados.

## Comportamento esperado

- mercado fechado bloqueia a ação
- saldo insuficiente retorna erro claro
- segunda previsão do mesmo usuário no mesmo mercado retorna erro claro
- confirmação registra a previsão e o impacto financeiro correspondente
- prévia calcula retorno estimado no backend sem persistir previsão, ledger ou probabilidade
- usuário visitante visualiza opções e consenso, mas não vê controle de stake nem confirma previsão
- usuário com previsão já registrada vê aviso destacado e controles de previsão desabilitados

## Regras de domínio

- stake só pode usar saldo disponível
- cada previsão deve ficar vinculada a mercado, opção e usuário
- nesta etapa do MVP, cada usuário pode registrar no máximo uma previsão por mercado
- a mutação financeira deve ser refletida no ledger
- a evolução do consenso é recalculada a partir de `orynth_predictions` ordenadas por criação, usando peso base sintético e `reputacao * stake`
- múltipla escolha deve expor uma linha de evolução por opção
- a fonte de verdade da probabilidade é decimal (`probability_exact`); percentuais inteiros são apenas apresentação truncada
- `probability_at_entry` e `potential_payout` devem usar a probabilidade decimal vigente antes da entrada
- Django não deve executar fallback local mutável para previsão/stake quando a FastAPI estiver indisponível

## Responsabilidades por camada

- `frontend-web`: formulário, confirmação e feedback
- `backend-api`: validação, registro de previsão, atualização de snapshot e ledger
- `database`: previsões, lançamentos de wallet, histórico
- `communications`: confirmação de previsão quando definido

## Dados e persistência

- previsão
- stake aplicado
- snapshot de resultado
- entrada de ledger associada
- histórico derivável das previsões para gráficos de consenso

## Contratos afetados

- `prediction-payloads.md`
- `wallet-ledger.md`
- `market-lifecycle.md`

## I18n e conteúdo

- mensagens de validação e confirmação precisam ser localizadas

## Observabilidade e operação

- registrar taxa de erro por saldo e mercado fechado

## Testes esperados

- unitários para validação de stake
- integração de previsão com ledger
- fluxo completo de confirmação
- regressão de hidratação local quando a FastAPI não entrega campos visuais novos

## Critérios de aceite

- previsão válida gera registro e efeito financeiro coerente
- previsões inválidas retornam erro previsível

## Impacto de mudança

Mudanças nesta feature impactam wallet, probabilidades, comunicações e, em certos casos, reputação futura.
