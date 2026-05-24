---
id: FEAT-REP-001
titulo: "Reputação e ranking"
versao: 0.7
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-05-22
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - reputation-ranking.md
dependencias:
  - FEAT-RES-001
impacta:
  - frontend-web
  - backend-api
  - database
aprovacao: pendente
---

# Reputação e ranking

## Objetivo

Exibir desempenho acumulado do usuário e ranking social de forma compreensível e comparável.

## Escopo incluído

- score de reputação
- posição no ranking
- histórico resumido de desempenho
- ranking global por reputação persistida
- ranking por categoria/subcategoria/evento recalculado a partir de previsões resolvidas
- filtros públicos de categoria/subcategoria/evento
- catálogo público de badges
- compartilhamento de badges conquistadas por usuário autenticado, com página pública por token opaco e card social com metadados Open Graph/Twitter
- gestão administrativa de badges com imagem e regra controlada
- concessão automática de badges por eventos e leituras do domínio

## Escopo excluído

- ligas complexas
- temporadas e resets avançados
- filtros de período, convicção ou ligas enquanto não houver contrato específico
- raridade pública, temporadas de badges e ranking de colecionadores
- publicação automática em nome do usuário em redes sociais por OAuth

## Fluxo do usuário

Usuário acompanha sua evolução e compara desempenho com outros participantes após mercados resolvidos.

## Comportamento esperado

- ranking reflete previsões resolvidas
- perfil e tela de ranking usam o mesmo contrato base
- visitantes podem consultar ranking, mas "Seu recorte" deve convidar login sem exibir posição fictícia
- usuários autenticados veem seu recorte somente quando houver dados reais no ranking filtrado/global exibido
- administradores e superusuários não aparecem no ranking público
- a tabela pública identifica participantes por handle
- a tabela pública pode mostrar badges conquistadas antes do handle, em resumo compacto vindo da API
- visitantes podem consultar o catálogo de badges ativas
- usuários autenticados veem no catálogo e no perfil quais badges já conquistaram
- usuários autenticados podem compartilhar somente badges já conquistadas, por página própria, links de redes, imagem social e cópia do link
- links públicos de badge conquistada usam token opaco e não expõem identificador direto do usuário
- Admin Ops pode criar, editar e desativar badges, incluindo imagem para tema claro, imagem opcional para tema escuro e descrição da regra
- browse inicial do Admin Ops para badges exibe o recorte de categoria/subcategoria/evento de cada regra
- formulário administrativo de badge marca visualmente os campos obrigatórios e mantém opcionais sem marcador
- formulário administrativo de badge exibe prévia do card público antes de salvar, respeitando a imagem do tema claro/escuro quando existir
- badges são concedidas automaticamente por regras predefinidas no backend, sem DSL livre
- conquistas de badges ficam persistidas na conta do usuário e não dependem apenas de cálculo na visualização

## Regras de domínio

- reputação depende de resultados resolvidos
- no MVP, resolução usa `delta_R = 10 * (1 - p)` para acerto e `delta_R = -10 * p` para erro
- `p` é a probabilidade decimal da opção escolhida no momento da previsão
- reputação mínima é `0`
- cancelamentos e refunds não alteram reputação
- desfazer resolução remove os efeitos reputacionais daquele mercado ao recalcular previsões ainda resolvidas do usuário
- ranking global usa a reputação persistida do usuário
- ranking temático por categoria/subcategoria é recalculado em leitura usando apenas previsões resolvidas do recorte
- ranking por evento é recalculado em leitura usando apenas previsões resolvidas do evento escolhido dentro de categoria/subcategoria
- tela pública de ranking usa `Carregar mais` em lotes cumulativos de 10 linhas, preservando filtros aplicados
- linhas do ranking podem expor até 3 badges ativas conquistadas e `badges_total`; a UI resume excedentes como `+N`
- usuários `is_staff` ou `is_superuser` são excluídos do ranking público
- mudanças futuras de fórmula exigem decisão técnica registrada
- badges não alteram reputação, ranking nem wallet
- compartilhar badge não altera reputação, ranking, wallet, ledger nem elegibilidade de outras badges
- regra executável de badge deve ser um `rule_type` conhecido pelo backend
- concessão executável de badge deve passar pela `BadgeAwardEngine`, que centraliza avaliação, persistência e idempotência
- texto administrativo da regra é explicativo e não substitui a elegibilidade do domínio
- concessão de badge é idempotente por usuário e definição de badge
- endpoints e ações administrativas devem disparar eventos de domínio para a engine, como `user_registered`, `comment_created`, `suggestion_approved`, `suggestion_rewarded`, `feedback_rewarded` e `market_resolved`
- resolução de mercado deve avaliar badges dos participantes após persistir resultado, reputação, sequência e ranking derivado
- regras MVP suportadas: `founding_member`, `resolved_predictions_count`, `correct_predictions_count`, `streak_count`, `ranking_position`, `comments_count`, `approved_suggestions_count` e `rewarded_feedback_count`
- regras que aceitam recorte temático devem escolher categoria/subcategoria/evento a partir da taxonomia dinâmica cadastrada no Admin Ops, não por texto livre
- os avisos opcionais de categoria/subcategoria/evento são apenas conteúdo contextual de mercado e não participam das regras de concessão de badge
- `resolved_predictions_count`, `correct_predictions_count` e `comments_count` podem ser aplicadas a todas as categorias, a uma categoria específica, a uma subcategoria da categoria escolhida ou a um evento da subcategoria
- `approved_suggestions_count` permanece por categoria/subcategoria enquanto o fluxo de sugestão não capturar evento; regras por evento não contam sugestões antigas sem evento

## Responsabilidades por camada

- `frontend-web`: ranking com `Carregar mais` de 10 em 10, filtros de categoria/subcategoria/evento, badges conquistadas compactas no ranking, perfil, catálogo de badges, rota autenticada de compartilhamento de badge conquistada, rota pública por token opaco e card social com metadados; não calcula reputação nem elegibilidade de badges no navegador; alterna imagem clara/escura da badge conforme tema ativo
- `backend-api`: cálculo e exposição do score global/temático, resumo de badges conquistadas no ranking, catálogo de badges, validação administrativa e concessão automática centralizada na `BadgeAwardEngine`
- `admin-ops`: cadastro operacional de badges consumindo contratos staff do backend, incluindo upload local de imagem para tema claro e tema escuro
- `database`: persistência de definições, regras e conquistas; materialização auxiliar quando necessário

## Dados e persistência

- score atual
- posição
- contadores derivados
- taxonomia para filtro de ranking
- recortes temáticos são projeções de leitura no MVP, sem nova tabela dedicada
- definições de badge com código, nome, descrição, tipo, imagem padrão/clara, imagem escura opcional, status e descrição pública da regra
- regras de badge vinculadas à definição, com tipo controlado, threshold e recorte opcional de categoria/subcategoria/evento
- conquistas de badge por usuário com data e snapshot do motivo, persistidas em `orynth_user_badge_awards`

## Contratos afetados

- `reputation-ranking.md`

## I18n e conteúdo

- textos explicativos devem evitar linguagem financeira ou de aposta real

## Observabilidade e operação

- medir distribuição de score e estabilidade da fórmula

## Testes esperados

- unitários para agregação e ordenação
- integração para atualização após resolução
- integração para filtros de categoria/subcategoria
- regressão para excluir staff/superuser do ranking público
- regressão para evitar dados fictícios no quadro "Seu recorte"
- integração para listar catálogo público de badges como visitante
- integração para exibir estado conquistada/bloqueada quando há usuário autenticado
- integração para exibir ação de compartilhar apenas em badge conquistada de usuário autenticado
- integração para bloquear compartilhamento de badge não conquistada
- integração para expor link público de badge por token opaco sem vazar id/email/handle
- integração administrativa para criar, editar e desativar badge
- unitários/integração para concessão idempotente de cada `rule_type` MVP

## Critérios de aceite

- usuário consegue ver posição e evolução coerente com resultados resolvidos
- usuário consegue filtrar ranking por categoria/subcategoria
- usuário consegue filtrar ranking por evento após escolher categoria e subcategoria
- visitante não vê recorte pessoal inventado
- administradores não aparecem no ranking público
- visitante consegue ver badges ativas e suas regras resumidas
- usuário logado vê progresso real de badges no catálogo e no perfil
- usuário logado consegue compartilhar uma conquista já persistida sem compartilhar badges bloqueadas
- link público de badge conquistada renderiza card social com metadados sem alterar reputação, ranking, wallet ou ledger
- admin consegue criar badge com imagem clara, imagem escura opcional e regra controlada
- eventos de cadastro, resolução, comentário, sugestão e feedback podem conceder badges automaticamente sem duplicidade

## Impacto de mudança

Mudanças nesta feature podem reclassificar histórico e exigem cuidado com comunicação ao usuário.
