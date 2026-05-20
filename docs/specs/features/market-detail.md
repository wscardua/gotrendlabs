---
id: FEAT-MARKET-002
titulo: "Detalhe do mercado"
versao: 0.4
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-05-18
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - market-lifecycle.md
  - prediction-payloads.md
  - i18n-content.md
dependencias:
  - FEAT-MARKET-001
impacta:
  - frontend-web
  - backend-api
  - database
aprovacao: pendente
---

# Detalhe do mercado

## Objetivo

Exibir a pergunta do mercado, opções disponíveis, contexto, probabilidade agregada, comentários e ações de previsão.

## Escopo incluído

- visão detalhada do mercado
- alternativas de resposta
- estado atual do mercado
- entrada para comentários e previsão
- gráfico de evolução do consenso calculado a partir de previsões reais

## Escopo excluído

- gráficos financeiros avançados
- live updates complexos
- analytics avançado fora do histórico de probabilidade por opção

## Fluxo do usuário

Usuário entra no mercado, entende o contexto, avalia opções, acompanha comentários e decide prever.

## Comportamento esperado

- opções disponíveis variam conforme o tipo do mercado
- estado do mercado governa disponibilidade de ação
- resolução final fica visível quando existir
- contrato do detalhe expõe curtidas reais do mercado e `viewer_has_like` quando há sessão autenticada
- ticket de previsão exibe ciclo compacto do mercado: criação, fechamento, resolução e distribuição
- mercado resolvido destaca o resultado oficial dentro do ticket
- mercado resolvido exibe data/hora/timezone da resolução
- ticket de previsão em mercado resolvido mostra mensagem personalizada quando o usuário tem previsão resolvida, diferenciando acerto e erro
- visitante vê opções e consenso sem controles de stake
- usuário com previsão existente vê estado bloqueado e não pode reenviar
- múltipla escolha exibe linha de evolução por opção
- consenso exibe inteiro truncado, mas barras, gráficos e retorno estimado usam `probability_exact`

## Regras de domínio

- o contrato do detalhe deve expor apenas dados consistentes com o estado
- mercado `locked` não aceita novas previsões
- probabilidade decimal é a fonte de verdade para snapshot e previsão; percentual inteiro é derivado apenas para apresentação
- o detalhe não deve duplicar timestamp e timezone no ticket; `resolved_at_label` já contém a informação completa para UI

## Responsabilidades por camada

- `frontend-web`: layout do detalhe, interação parcial e mensagens
- `backend-api`: resposta detalhada do mercado e validação de estados
- `database`: mercado, opções, comentários agregados e resolução

## Implementação atual

- detalhe público persistido em PostgreSQL com opções e snapshot de probabilidade
- `GET /markets/{slug}` expõe contrato compatível com os templates atuais
- `GET /markets/{slug}` expõe `market_like_count` e `viewer_has_like` para curtidas reais do mercado, separadas de reações em comentários
- abertura da página pública de detalhe incrementa `view_count` do mercado para popularidade operacional, sem deduplicação nesta v1
- ações em controles de compartilhamento de pergunta/resultado incrementam `share_count` do mercado, sem bloquear navegação quando o tracking falha
- contrato expõe `sparkline_series` e paths SVG derivados de `orynth_predictions`
- gráficos de evolução devem preservar histórico após resolução, considerando previsões `resolved` além das `open`
- Django usa fallback local em Postgres para IDs de opções e campos visuais quando a FastAPI está indisponível ou com payload antigo
- ticket do detalhe renderiza card de ciclo do mercado e destaque de resultado resolvido usando apenas estado serializado pelo domínio
- comentários reais ainda não entram nesta etapa; contrato retorna lista vazia
- fixture deixou de ser fallback principal para mercados; fallback de desenvolvimento usa Postgres local

## Dados e persistência

- mercado
- opções
- resultado/resolução
- comentários vinculados
- previsões como fonte derivada da evolução visual do consenso
- contadores denormalizados `view_count` e `share_count` em mercado para leitura operacional rápida
- curtidas reais em `orynth_market_likes`, com uma curtida por usuário/mercado

## Contratos afetados

- `market-lifecycle.md`
- `prediction-payloads.md`
- `i18n-content.md`

## I18n e conteúdo

- conteúdo textual do mercado deve permitir localização futura

## Observabilidade e operação

- medir visão de detalhe, taxa de previsão e leitura de resolução
- medir ações de compartilhamento acionadas nas páginas sociais de mercado/resultado

## Testes esperados

- integração do detalhe por tipo de mercado
- fluxo de detalhe com mercado aberto, locked e resolved
- regressão para payload antigo sem `option.id` ou sem sparkline
- regressão para mercado resolvido não zerar gráfico de consenso
- regressão para ticket renderizar ciclo do mercado e destaque de resultado em mercado resolvido
- regressão para tracking de visualização e compartilhamento não interferir na renderização do detalhe ou das páginas sociais

## Critérios de aceite

- usuário entende estado, opções e ação disponível sem ambiguidade
- usuário reconhece rapidamente em que etapa do ciclo o mercado está e qual foi o resultado quando resolvido

## Impacto de mudança

Mudanças neste contrato impactam previsão, comentários e compartilhamento.
