---
id: FEAT-MOBILE-UX-001
titulo: "UX e design mobile"
versao: 0.1
status_spec: draft
status_impl: nao_iniciada
ultima_atualizacao: 2026-06-07
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
- `accentViolet`: uso moderado para destaque de IA/insights

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
- indicador de status quando locked/resolved

### MarketCompactCard

Card de lista/grid:

- imagem no topo
- titulo truncado com cuidado
- pill de probabilidade
- volume e comentarios
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

Metricas como `liquidez`, `spread`, `last trade` ou equivalentes devem ficar fora do MVP ate existir significado de dominio educativo e contrato backend.

### PredictionTicket

Controle de previsao:

- sem opcao pre-selecionada
- lista de opcoes com probabilidade atual
- input/stepper de stake GTL
- preview vindo da API
- CTA primario de confirmar
- estados bloqueados para visitante, sem saldo, previsao existente, mercado locked/resolved/canceled

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
- Insights
- Mercados
- Alertas
- Busca

O item ativo deve ser claro sem depender apenas de cor.

## Telas

### Hoje

Objetivo: descoberta rapida.

Deve priorizar:

- destaque visual de 1 a 3 mercados
- chips de categoria
- secoes horizontais de tendencias
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

### Wallet

Objetivo: confianca educativa.

Deve priorizar:

- saldo atual
- extrato rastreavel
- copy clara de moeda educativa
- ausencia de linguagem de investimento, saque ou deposito real

### Perfil e ranking

Objetivo: reputacao publica.

Deve priorizar:

- handle
- reputacao
- badges
- posicao real quando existir
- historico resumido

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
- cards de mercado continuam legiveis com imagens claras ou escuras
- pergunta principal nao fica encoberta por controles
- bottom navigation nao cobre CTA critico sem alternativa
- detalhe comunica status do mercado em ate poucos segundos
- ticket de previsao nao induz escolha padrao
- design parece nativo mobile e coerente com o produto, nao uma copia de web responsiva
- telas implementadas devem ser revisadas com `gotrendlabs-mobile-ux-designer` e screenshots do emulador antes de encerrar a fatia visual
