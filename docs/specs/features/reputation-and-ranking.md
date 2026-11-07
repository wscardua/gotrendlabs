---
id: FEAT-REP-001
titulo: "Reputação e ranking"
versao: 0.8
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-11-07
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
- contrato autenticado de desempenho compartilhado por web e mobile, com placar, histórico auditável de resoluções e conquistas
- ranking global por reputação persistida
- ranking por categoria/subcategoria/evento recalculado a partir de previsões resolvidas
- filtros públicos de categoria/subcategoria/evento
- catálogo público de badges
- compartilhamento de badges conquistadas por usuário autenticado, com página pública por token opaco e card social com metadados Open Graph/Twitter
- gestão administrativa de badges com imagem e regra controlada
- concessão automática de badges por eventos e previsões do domínio

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
- telas web e mobile `Desempenho` usam `GET /users/me/performance` para exibir dados quentes de evolucao preditiva sem calcular delta, GT₵, ranking ou badges no app
- visitantes podem consultar ranking, mas "Seu recorte" deve convidar login sem exibir posição fictícia
- usuários autenticados veem seu recorte somente quando houver dados reais no ranking filtrado/global exibido
- administradores, superusuários, bots e dados internos/dev não aparecem no ranking público
- a tabela pública identifica participantes por handle
- a tabela pública pode mostrar badges conquistadas após o handle, em resumo compacto vindo da API
- visitantes podem consultar o catálogo de badges visíveis, incluindo badges com concessão pausada
- catálogo e ranking públicos não expõem badges internas/dev ou conteúdos de preview local
- usuários autenticados veem no catálogo e no perfil quais badges já conquistaram
- badges conquistadas permanecem como propriedade histórica do usuário: pausar novas concessões não remove a badge do catálogo, nem remove conquistas do catálogo autenticado, ranking ou compartilhamento público por token
- usuários autenticados podem compartilhar somente badges já conquistadas, por página própria, links de redes, imagem social e cópia do link
- links públicos de badge conquistada usam token opaco e não expõem identificador direto do usuário
- Admin Ops pode criar, editar, ocultar badges e pausar novas concessões, incluindo imagem para tema claro, imagem opcional para tema escuro e descrição da regra
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
- ranking temático por categoria/subcategoria é recalculado sob demanda usando apenas previsões resolvidas do recorte
- ranking por evento é recalculado sob demanda usando apenas previsões resolvidas do evento escolhido dentro de categoria/subcategoria
- tela pública de ranking usa `Carregar mais` em lotes cumulativos de 10 linhas, preservando filtros aplicados
- linhas do ranking podem expor até 3 badges visíveis conquistadas e `badges_total`; a UI resume excedentes como `+N`, incluindo badges com concessão pausada quando o usuário já conquistou
- usuários `is_staff`, `is_superuser`, `is_bot` ou marcados por dados internos/dev são excluídos do ranking público
- mudanças futuras de fórmula exigem decisão técnica registrada
- badges não alteram reputação, ranking nem wallet
- compartilhar badge não altera reputação, ranking, wallet, ledger nem elegibilidade de outras badges
- regra executável de badge deve ser um `rule_type` conhecido pelo backend
- `BadgeDefinition.is_active` controla exibição pública/histórica e remoção do catálogo; `BadgeRule.is_active` controla se novas conquistas ainda podem ser concedidas
- concessão executável de badge deve passar pela `BadgeAwardEngine`, que centraliza avaliação, persistência e idempotência
- texto administrativo da regra é explicativo e não substitui a elegibilidade do domínio
- concessão de badge é idempotente por usuário e definição de badge
- endpoints e ações administrativas devem disparar eventos de domínio para a engine, como `user_registered`, `comment_created`, `suggestion_approved`, `suggestion_rewarded`, `feedback_rewarded` e `market_resolved`
- resolução de mercado deve avaliar badges dos participantes após persistir resultado, reputação, sequência e ranking derivado
- regras MVP suportadas: `founding_member`, `resolved_predictions_count`, `correct_predictions_count`, `streak_count`, `ranking_position`, `comments_count`, `approved_suggestions_count` e `rewarded_feedback_count`
- regras de badge podem ter requisitos adicionais configuráveis usando os mesmos tipos de métrica controlados pelo backend; a concessão exige regra principal verdadeira e todos os requisitos ativos verdadeiros
- a badge `Top 10` deve permanecer configurada como `ranking_position <= 10` com requisito adicional `resolved_predictions_count >= 3`, evitando concessão automática para usuários sem histórico em bases pequenas
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
- recortes temáticos são projeções calculadas no MVP, sem nova tabela dedicada
- definições de badge com código, nome, descrição, tipo, imagem padrão/clara, imagem escura opcional, status e descrição pública da regra
- regras de badge vinculadas à definição, com tipo controlado, threshold, status de concessão e recorte opcional de categoria/subcategoria/evento
- conquistas de badge por usuário com data e snapshot do motivo, persistidas em `gotrendlabs_user_badge_awards`

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
- integração administrativa para criar, editar, ocultar badge e pausar novas concessões
- regressão para pausar novas concessões sem ocultar a badge do catálogo público/autenticado e sem ocultar conquistas no ranking e compartilhamento
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
- visitante e usuário sem conquista conseguem ver no catálogo badges com concessão pausada, sem receber nova conquista
- usuário logado consegue ver e compartilhar uma conquista já persistida mesmo quando novas concessões daquela badge estiverem pausadas
- badge com `is_active=false` sai do catálogo, ranking e compartilhamento público sem apagar a conquista persistida
- link público de badge conquistada renderiza card social com metadados sem alterar reputação, ranking, wallet ou ledger
- admin consegue criar badge com imagem clara, imagem escura opcional e regra controlada
- eventos de cadastro, resolução, comentário, sugestão e feedback podem conceder badges automaticamente sem duplicidade

## Impacto de mudança

Mudanças nesta feature podem reclassificar histórico e exigem cuidado com comunicação ao usuário.

## 2026-10-09 — Imagens IA de badges

FEAT-BADGE-IMAGE-001: geração no editor administrativo com contexto atual, candidata privada e confirmação no salvamento existente; não modifica elegibilidade, métricas ou propriedade histórica de conquistas. Apresentação de definição continua compartilhada pelas conquistas; contrato público preservado.

## Página web Desempenho (2026-11-07)

Escopo aprovado pelo pedido de implementação: `/desempenho/`, autenticada, no menu imediatamente após Perfil e badges e com atalho discreto no perfil. Reutiliza `GET /users/me/performance` a cada requisição, sem cache compartilhado nem fallback local. Não altera as pendências da feature ampla.

- Placar: reputação, posição global (zero significa sem posição), resolvidas, precisão, sequência e categoria forte (vazia significa ainda não definida). Staff/superuser preservam a ocultação de métricas do perfil; bots não recebem posição pública fictícia.
- Histórico: até dez resoluções retornadas, cinco visíveis inicialmente com Carregar mais para revelar as restantes; sem JavaScript, todas ficam acessíveis. Labels de resultado/GT₵ educativo e delta do backend, escolha/data disponíveis e link pelo slug real. Sem miniaturas extras, filtros, paginação remota ou cálculo de domínio local.
- Lateral: total de badges e últimas conquistas reais, imagens clara/escura existentes, acesso a `/profile/#badges` e ranking. Sem próximos marcos inventados.
- Vazio orienta explorar mercados; erro explícito oferece nova tentativa e nunca vira zero. 401 limpa sessão e usa login com retorno seguro; 403 preserva restrição. Respostas privadas sem armazenamento.
- Layout usa tokens atuais, tabela desktop e linhas em cards no celular, texto além de cor, foco e i18n Django. Não há atualização parcial.
- Aceite: testes de sessão, menu/papéis, renderização, estados, links e isolamento pessoal; QA desktop/celular claro/escuro. Mobile, API e MCP preservados. Integração e implantação seguem o workflow de fechamento, com aprovação da descrição antes de abrir a PR.

### Refinamento visual após avaliação com dados

Cabeçalho e placar compõem um painel único. Histórico prioriza largura do mercado, com colunas numéricas alinhadas à direita; no celular, resultado, reputação e GT₵ educativo ficam lado a lado abaixo do título/escolha/data. Conquistas usam linhas compactas com imagem e descrição, sem repetir o status já implícito na seção. Mesmos contratos, estados e condições por papel.

### Apresentação incremental web (07/11/2026)

Por pedido posterior do usuário, Desempenho limita a exibição inicial a cinco resoluções. Carregar mais revela cinco itens adicionais da resposta já recebida e desaparece ao esgotá-los; contador anuncia quantos itens do recorte estão visíveis. O contrato continua limitado a até dez resoluções recentes, sem nova paginação ou chamadas adicionais. Esta decisão substitui a exclusão anterior do controle visual nesta tela. Sem JS, todas as linhas permanecem acessíveis.

### Gráfico de impactos recentes

Pedido posterior do usuário autoriza gráfico compacto dos deltas individuais de `history`, substituindo a exclusão visual anterior somente para esse recorte. Não é gráfico de evolução do score acumulado: não há contrato histórico suficiente para ele. Ordenação da API é invertida apenas para leitura cronológica, e altura é proporcional ao maior delta absoluto recebido, sem modificar valores. Rótulos e sinais numéricos complementam as cores; cada barra oferece link acessível ao mercado. Oculto em vazio/erro e para os papéis cujo placar já é oculto. Nenhum ajuste MCP.

### Estado final da fatia web e fechamento

Tipografia de título, métricas, seções e tabela acompanha a Carteira educativa (IBM Plex Sans e tokens compartilhados). Cabeçalho reúne título/subtítulo e gráfico compacto de impactos, seguido do placar; conquistas usam as imagens reais do catálogo nos dois temas. Os experimentos com atalhos e identidade no cabeçalho foram revertidos e não fazem parte da entrega.

Esta fatia não exige migration, flag, ajuste de dados ou novo serviço em produção; a ativação ocorre pelo deploy existente com publicação de templates e collectstatic. Fixtures e credenciais de avaliação permanecem locais e não são distribuídas. A feature ampla FEAT-REP-001 continua parcial/draft; seu fechamento global não é inferido da conclusão da página web. Estado de commit, PR, merge e implantação no [recibo de fechamento](../testing/web-performance-closeout-20261107.md).
