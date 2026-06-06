---
id: FEAT-SUGGEST-001
titulo: "Sugestões de mercado"
versao: 0.3
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-05-18
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - domain-events.md
  - i18n-content.md
  - wallet-ledger.md
dependencias:
  - FEAT-AUTH-001
  - FEAT-WALLET-001
impacta:
  - frontend-web
  - backend-api
  - database
  - admin-ops
  - communications
aprovacao: pendente
---

# Sugestões de mercado e filas operacionais

## Objetivo

Permitir que usuários enviem sugestões de perguntas para futura curadoria administrativa e que a operação revise sugestões e feedbacks em uma fila persistida.

## Escopo incluído

- envio de sugestão de mercado por usuário autenticado ou visitante identificado por nome e email
- entrada `Sugerir mercado` na navegação pública principal para visitantes e usuários autenticados
- envio de feedback/suporte, dúvida ou melhoria por usuário autenticado ou visitante identificado por nome e email
- proteção anti-abuso com reCAPTCHA v2 checkbox para visitantes em sugestão e feedback quando configurado
- confirmação de recebimento no frontend com redirecionamento para a home
- fila administrativa real no Admin Ops para itens de Mercado e Feedback
- revisão administrativa com nota operacional
- conversão de sugestão de mercado em rascunho de mercado
- aprovação opcional de créditos para itens de usuário cadastrado
- bloqueio de recompensa duplicada por item

## Escopo excluído

- publicação automática
- marketplace aberto de criação
- recompensa para envio anônimo ou visitante sem conta
- event bus assíncrono dedicado nesta fatia
- histórico público completo de feedback do usuário
- moderação de comentários

## Fluxo do usuário

Usuário autenticado preenche proposta de mercado ou feedback/suporte e envia; nome e email são herdados do cadastro e a tela informa que o envio não é guest. Visitante informa nome e email junto do conteúdo. Após submissão válida, o frontend exibe confirmação e retorna para a home.

Itens enviados entram na fila operacional para revisão por staff.

## Comportamento esperado

- sugestões ficam pendentes até revisão
- feedbacks ficam pendentes até revisão
- admin consegue classificar, revisar, rejeitar, recompensar quando aplicável e reaproveitar conteúdo
- sugestão de mercado convertida cria um mercado `draft`, nunca publicado automaticamente
- seção de conversão fica apenas informativa e indisponível depois que a sugestão já virou rascunho
- seção de créditos fica apenas informativa e indisponível depois que a recompensa já foi aprovada
- créditos aprovados aparecem no extrato do usuário e atualizam o saldo operacional

## Regras de domínio

- usuário comum não publica mercado diretamente
- histórico de sugestão precisa ser rastreável
- visitante pode submeter conteúdo, mas não recebe créditos enquanto não houver usuário associado
- visitante precisa concluir reCAPTCHA válido quando a proteção estiver habilitada; usuário autenticado não sofre essa fricção em sugestão/feedback
- recompensa exige usuário cadastrado, valor inteiro positivo em GT₵ e item ainda não recompensado
- recompensa por feedback ou sugestão não concede reputação
- conversão em rascunho precisa respeitar validações de mercado e taxonomia existentes
- staff não autenticado ou usuário não staff recebe bloqueio administrativo
- Admin Ops não deve aplicar fallback local mutável para revisão, conversão em rascunho ou créditos; indisponibilidade da FastAPI deve aparecer como erro operacional.

## Responsabilidades por camada

- `frontend-web`: formulário e confirmação
- `backend-api`: validação e persistência
- `database`: sugestão e status
- `admin-ops`: revisão, descarte ou promoção a rascunho
- `wallet`: ledger e projeção de saldo quando crédito for aprovado
- `communications`: confirmação eventual

## Dados e persistência

- sugestão: autor opcional, nome/email guest, pergunta, categoria, subcategoria, tipo interno, fonte, justificativa, status, nota administrativa, recompensa em GT₵, mercado convertido opcional, datas de criação/revisão/recompensa
- feedback: autor opcional, nome/email guest, tipo, severidade interna, descrição, status, nota administrativa, recompensa em GT₵, datas de criação/revisão/recompensa
- status canônicos de sugestão: `pending`, `reviewed`, `converted`, `rewarded`, `rejected`
- status canônicos de feedback: `pending`, `reviewed`, `rewarded`, `rejected`

## Contratos afetados

- `domain-events.md`
- `i18n-content.md`
- `wallet-ledger.md`

## Contratos API atuais

- `POST /suggestions` e `POST /suggestions/`
- `POST /feedback` e `POST /feedback/`
- `GET /admin/queues`
- `POST /admin/queues/{kind}/{id}/review`
- `POST /admin/queues/suggestions/{id}/convert-draft`
- `POST /admin/queues/suggestions/{id}/reward`
- `POST /admin/queues/feedback/{id}/reward`

`GET /admin/queues` deve permitir filtros simples por fila, status e severidade interna, além de ordenação por data de criação.

## I18n e conteúdo

- campos textuais devem prever tradução assistida futura quando aplicável

## Observabilidade e operação

- medir volume, taxa de aproveitamento, backlog, itens recompensados e conversões em rascunho
- registrar ações administrativas em `gotrendlabs_admin_events`: `suggestion.review`, `suggestion.convert_draft`, `suggestion.reward`, `feedback.review`, `feedback.reward`
- eventos de domínio `suggestion.submitted` e `feedback.submitted` permanecem previstos; emissão assíncrona dedicada fica pendente
- tela pública/autenticada de sugestão deve carregar categorias ativas da taxonomia administrada; categorias bloqueadas não aparecem no formulário
- backend deve rejeitar sugestão com categoria inexistente ou bloqueada, preservando a categoria canônica no item de fila

## Testes esperados

- integração de submissão autenticada e guest
- integração de reCAPTCHA para envio guest e bypass autenticado
- fila administrativa listando Mercado e Feedback reais
- revisão administrativa por staff
- bloqueio `403` para usuário comum em endpoints admin
- conversão de sugestão em mercado `draft`
- recompensa de feedback e sugestão gerando ledger e atualizando `gotrendlabs_wallet_balances`
- bloqueio de recompensa duplicada, valor inválido e item sem usuário associado
- smoke tests de formulários públicos e tela de revisão do Admin Ops

## Critérios de aceite

- usuário consegue enviar sugestão
- usuário ou visitante encontra o fluxo pelo link `Sugerir mercado` no topo público
- visitante consegue enviar sugestão ou feedback/suporte informando nome e email
- visitante precisa passar no reCAPTCHA quando a proteção estiver configurada
- operação consegue rastrear e revisar a fila com data de criação e tipo do item
- operação consegue converter sugestão de mercado em rascunho quando as validações forem satisfeitas
- operação consegue aprovar crédito uma única vez para usuário cadastrado
- saldo e extrato refletem crédito aprovado

## Impacto de mudança

Mudanças aqui afetam principalmente admin, wallet, comunicações e possíveis pipelines de conteúdo.
