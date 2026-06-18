---
id: FEAT-MOBILE-UX-001
titulo: "UX e design mobile"
versao: 0.1
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-06-16
origem:
  - docs/specs/features/mobile-mvp.md
  - referencias_visuais_fornecidas_pelo_usuario
dependencias:
  - FEAT-MOBILE-001
impacta:
  - future-mobile
aprovacao: pendente
---

# UX e design mobile

## Objetivo

Definir a direcao visual e ergonomica do app mobile GoTrendLabs, tomando como inspiracao as referencias fornecidas pelo usuario de um app de sinais/mercados preditivos, sem copiar identidade, marca ou telas literalmente.

## Direcao visual

O app deve ser `dark-first`, denso e editorial, com foco em mercados como objetos visuais fortes. A experiencia deve parecer um terminal social de previsoes, nao uma landing page.

Caracteristicas desejadas:

- fundo escuro quase preto
- cards com imagem real/contextual do mercado
- sobreposicao escura em imagens para legibilidade
- tipografia grande para perguntas importantes
- metricas compactas com icones
- chips horizontais para categorias
- navegacao inferior persistente
- detalhe com hero visual imersivo
- bottom sheets para acoes de confirmacao
- estados de loading com skeletons discretos

## Inspiracao permitida

Das referencias visuais, podem ser reaproveitados como padroes gerais:

- card grande de mercado com imagem, categoria, pergunta e metricas na parte inferior
- tela de detalhe com imagem de topo, botao voltar, acoes circulares e abas `Visao geral` / `Comunidade`
- painel de metricas em grid compacto
- bottom navigation com cinco destinos
- CTA em bottom sheet para acao importante
- hierarquia visual onde probabilidade, volume e prazo aparecem antes de informacao secundaria

As duas telas fornecidas pelo usuario devem orientar estes pontos:

- `Markets`: cabeçalho direto, chips de categoria iconizados, card destaque com imagem forte e cards menores abaixo.
- `Market detail`: hero com imagem full-bleed no topo, controles circulares discretos, segmentacao `Overview/Community`, pergunta em tipografia forte, painel escuro de metricas e CTA em bottom sheet.
- O design final deve trocar a linguagem de trading por linguagem GoTrendLabs: previsao social, GT₵ educativo, reputacao e resolucao auditavel.

Nao deve ser copiado:

- marca, naming, textos proprietarios ou identidade de outro app
- composicao exata de telas
- icones proprietarios
- dados financeiros ou copy que sugira trading real
- referencia direta a Polymarket como selo editorial do GoTrendLabs

## Identidade GoTrendLabs

O design deve comunicar:

- previsao social
- reputacao publica
- moeda educativa
- resolucao auditavel
- opinioes e comentarios como camada social

Tom de interface:

- direto
- confiante
- analitico
- nao cassino
- nao corretora
- nao rede social casual demais

## Paleta inicial

Tokens recomendados:

- `background`: preto frio, quase absoluto
- `surface`: cinza grafite para cards
- `surfaceElevated`: grafite levemente mais claro para bottom sheets
- `border`: branco com baixa opacidade
- `textPrimary`: branco suave
- `textSecondary`: cinza claro
- `muted`: cinza medio
- `accentBlue`: azul eletrico para navegacao e links
- `accentGreen`: verde para estados positivos, online e acertos
- `accentRed`: vermelho/coral para probabilidade baixa, erro e perda
- `accentYellow`: amarelo para prazo, aviso e resolucao
- `accentViolet`: uso moderado para destaque de IA e sinais editoriais

A paleta nao deve virar monocromatica azul/roxa. Categorias devem ter acentos distintos.

## Tipografia

- Titulos de mercado devem ser grandes, fortes e legiveis.
- Labels de metrica devem usar caixa alta curta e peso medio.
- Numeros de metrica devem ter contraste alto.
- Corpo de comentarios e descricoes deve priorizar leitura prolongada.
- Texto nunca deve depender de fonte minuscula para caber em cards.

## Componentes principais

### MarketHeroCard

Card grande para destaque:

- imagem 16:10 ou 4:5 conforme contexto
- overlay escuro vertical
- categoria/evento em label curto
- pergunta em ate 3 linhas no destaque
- pill de probabilidade principal
- volume GTL e atividade
- prazo compacto para fechamento quando o mercado estiver aberto; no feed, usar barra de regressao/urgencia na linha inferior em vez de repetir icone de relogio no thumb, com cor evoluindo de folga para urgencia conforme o fechamento se aproxima
- indicador de status quando locked/resolved

### MarketCompactCard

Card de lista/grid:

- imagem no topo
- titulo truncado com cuidado
- pill de probabilidade
- volume, comentarios e prazo compacto; o prazo deve aparecer como barra curta de regressao/urgencia no canto inferior direito, ao lado do contador de comentarios, mudando de cor conforme o tempo restante diminui
- status fechado/resolvido visivel nos recortes que permitem estes estados
- estado de favorito/curtida quando autenticado

### MarketMetricPanel

Painel de detalhe:

- probabilidade atual
- volume GTL humano
- participantes
- comentarios
- encerramento
- ultima atualizacao/ultima previsao quando disponivel

Evitar metricas financeiras copiadas de apps de trading, como spread/liquidez, a menos que exista significado educativo claro no dominio GoTrendLabs.

Metricas recomendadas para o MVP:

- `Probabilidade`
- `Volume GT₵`
- `Participantes`
- `Comentarios`
- `Encerra em`
- `Status`

Quando o contador de `Comentarios` aparecer em cards ou metricas do detalhe, o toque deve abrir o mercado na aba `Comunidade`.

Metricas como `liquidez`, `spread`, `last trade` ou equivalentes devem ficar fora do MVP ate existir significado de dominio educativo e contrato backend.

### PredictionTicket

Controle de previsao:

- sem opcao pre-selecionada
- lista de opcoes com probabilidade atual
- input/stepper de stake GTL
- preview vindo da API
- CTA primario de confirmar
- confirmacao em bottom sheet com `SafeArea` e area rolavel para telas fisicas compactas/fonte ampliada
- estados bloqueados para visitante, sem saldo, mercado locked/resolved/canceled e acoes de posicao inelegiveis
- quando `viewer_position.has_position=false`, o ticket cria somente a primeira previsao via `/predict`
- quando `viewer_position.has_position=true`, o ticket vira mesa de posicao: mostra escolha atual, movimentos ativos, total ativo, credito possivel, aumentos/trocas restantes e historico resumido
- as acoes de posicao aparecem sempre como frames fechados: `Aumentar posição` e `Trocar escolha`, cada um com resumo curto, contador restante ou `Bloqueado`
- `Aumentar posição` permanece na mesma escolha ativa quando `can_reinforce=true`, com preview de novo total ativo, aumentos restantes e credito possivel vindo da API
- `Trocar escolha` permite apenas opcoes diferentes da ativa quando `can_revise=true`, com resumo de movimentos encerrados, custo da troca, nova posicao estimada, trocas restantes e credito possivel vindos da API
- confirmacao de aumento/troca so aparece depois de preview valido da FastAPI; bloqueios exibem a mensagem retornada pelo backend

### ConsensusChart

Grafico compacto de consenso:

- usa `sparkline_series` retornado pela FastAPI
- mostra uma linha por opcao do mercado, com legenda curta
- preserva altura controlada para nao alongar a secao de detalhe
- nao recalcula probabilidade, tendencia ou serie historica no app

### CommentItem

Comentario:

- handle do autor
- selo de IA oficial quando `author_is_bot=true`
- texto
- timestamp relativo
- like/dislike mutuamente exclusivos

### BottomNav

Destinos:

- Hoje
- Ranking
- Mercados
- Alertas
- Busca

O item ativo deve ser claro sem depender apenas de cor.

## Telas

### Hoje

Objetivo: descoberta rapida.

Deve priorizar:

- destaque visual de 1 a 3 mercados abertos
- chips de categoria
- secoes horizontais de tendencias com mercados abertos ordenados por engajamento visual
- resumo educativo de produto quando util

Nao deve abrir com hero marketing.

### Mercados

Objetivo: browse denso.

Deve priorizar:

- filtros fixos/rolaveis
- cards escaneaveis
- ordenacao clara
- estados de lista vazia

### Detalhe

Objetivo: decisao informada.

Deve priorizar:

- pergunta e contexto
- probabilidade/opcoes
- ciclo do mercado
- comentario/comunidade
- previsao com confirmacao explicita
- paridade com o web para popularidade operacional: abrir o detalhe incrementa `view_count`, e compartilhar pelo app incrementa `share_count` sem bloquear a acao nativa

### Wallet

Objetivo: confianca educativa.

Deve priorizar:

- saldo atual separado em `Disponível` e `Bloqueado`
- extrato rastreavel
- recarga educativa como acao secundaria, abaixo do resumo da carteira
- recarga controlada sem expor jargao operacional como `Fila Admin Ops` nem passos internos em cards
- copy clara de moeda educativa
- ausencia de linguagem de investimento, saque ou deposito real

### Perfil e ranking

Objetivo: reputacao publica.

Deve priorizar:

- handle
- dados privados conferiveis pelo usuario autenticado: email, data de nascimento e bio
- edicao privada desses dados em bottom sheet, com data digitavel em `DD/MM/AAAA` ou selecionavel por calendario
- reputacao
- badges
- posicao real quando existir
- historico resumido
- ranking publico identificado pelo `@handle`, com badges compactas e overflow `+N` vindos de `GET /rankings`
- sem controles operacionais de push; o estado de push mobile aparece em `Sobre` como item informativo de saude/configuracao do build

### Alertas

Objetivo: notificacoes in-app.

Deve priorizar:

- mercados favoritados
- previsoes e resolucoes recentes
- estado vazio claro
- sem painel operacional de push; estado/configuracao de push fica em `Sobre`

## Estados de UX

Cada tela principal deve ter:

- loading skeleton
- erro de rede com tentar novamente
- vazio real
- vazio autenticado com CTA de proxima acao
- estado visitante
- sessao expirada
- conteudo stale quando cache for usado

## Acessibilidade

- alvos de toque minimos de 44px
- contraste AA para texto essencial
- nao depender so de cor para ganho/perda/status
- labels acessiveis para icones
- suporte a fonte ampliada sem quebrar cards
- bottom sheet fechavel e navegavel

## Movimento

Movimento deve ser contido:

- transicao suave feed -> detalhe
- skeletons leves
- feedback visual de curtida/favorito
- bottom sheet com entrada curta
- desafio anti-abuso em bottom sheet deve ser direto, com refresh e erro inline, sem mandar visitante para fora do app
- sem animacoes decorativas que atrasem decisao

## Copy e linguagem

Usar:

- `Prever`
- `Mercado`
- `Probabilidade`
- `Saldo educativo`
- `GT₵`
- `Resolucao`
- `Reputacao`

Evitar:

- `apostar`
- `trade`
- `cash`
- `deposito`
- `saque`
- `lucro garantido`
- qualquer promessa financeira

## Criterios de aceite visual

- primeira tela mostra experiencia util, nao marketing
- contribuicoes publicas como feedback e sugestao de mercado ficam descobriveis no app e concluidas sem navegador externo
- desafio anti-abuso de visitante em feedback deve aparecer depois de `Descricao`; em sugestao de mercado, depois de `Contexto`
- cards de mercado continuam legiveis com imagens claras ou escuras
- pergunta principal nao fica encoberta por controles
- bottom navigation nao cobre CTA critico sem alternativa
- detalhe comunica status do mercado em ate poucos segundos
- ticket de previsao nao induz escolha padrao
- design parece nativo mobile e coerente com o produto, nao uma copia de web responsiva
- telas implementadas devem ser revisadas com `gotrendlabs-mobile-ux-designer` e screenshots do emulador antes de encerrar a fatia visual
