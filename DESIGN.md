---
name: "Orynth Trends"
description: "A calm, trustworthy product UI for social prediction markets with educational credits, public consensus, and reputation."
colors:
  ink-carbon: "#111315"
  muted-slate: "#667071"
  warm-paper: "#f7f4ec"
  soft-panel: "#fffdf7"
  clay-panel: "#f0eadc"
  warm-divider: "#ded7c8"
  coal-action: "#191d1e"
  consensus-green: "#136f4a"
  deep-trust-green: "#0d5739"
  earned-mint: "#dff6df"
  resolution-red: "#b7493d"
  risk-blush: "#fee4df"
  deadline-amber: "#d89422"
  signal-blue: "#2d5e88"
typography:
  display:
    fontFamily: "\"IBM Plex Sans\", sans-serif"
    fontSize: "34px"
    fontWeight: 800
    lineHeight: 1.05
    letterSpacing: "-0.04em"
  headline:
    fontFamily: "\"IBM Plex Sans\", sans-serif"
    fontSize: "24px"
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  title:
    fontFamily: "\"IBM Plex Sans\", sans-serif"
    fontSize: "18px"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "0"
  body:
    fontFamily: "\"IBM Plex Sans\", sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "0"
  label:
    fontFamily: "\"IBM Plex Sans\", sans-serif"
    fontSize: "13px"
    fontWeight: 750
    lineHeight: 1
    letterSpacing: "0"
rounded:
  sm: "10px"
  md: "14px"
  lg: "18px"
  xl: "22px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  section: "42px"
components:
  button-primary:
    backgroundColor: "{colors.coal-action}"
    textColor: "{colors.soft-panel}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "42px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink-carbon}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "42px"
  filter-active:
    backgroundColor: "{colors.coal-action}"
    textColor: "{colors.soft-panel}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "8px 12px"
  market-card:
    backgroundColor: "{colors.soft-panel}"
    textColor: "{colors.ink-carbon}"
    rounded: "{rounded.xl}"
    padding: "14px"
  tag-status:
    backgroundColor: "{colors.clay-panel}"
    textColor: "{colors.muted-slate}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "4px 8px"
  input-field:
    backgroundColor: "#fffaf0"
    textColor: "{colors.ink-carbon}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "11px 12px"
---

## 1. Overview

Orynth Trends e uma interface de produto para previsoes sociais educativas. A primeira impressao deve ser de uma mesa de leitura publica: mercados visiveis, consenso facil de comparar, acoes diretas e sinais de confianca presentes sem parecer burocracia.

O sistema visual deve favorecer usuarios curiosos recorrentes. Eles entram para descobrir perguntas novas, registrar uma previsao, comparar o consenso e voltar para acompanhar reputacao, ranking e badges. A experiencia nao deve parecer cassino, sportsbook, exchange, terminal financeiro ou cripto especulativa.

Principios de composicao:

- Mercados primeiro: a home e telas principais devem abrir espaco para cards, filtros e decisoes rapidas.
- Densidade com calma: mostrar muitas oportunidades sem sacrificar legibilidade.
- Confianca antes de intensidade: fonte, prazo, status e resolucao devem ficar claros.
- Social antes de financeiro: falar em leitura, consenso, reputacao, credito reservado e carteira educativa.
- Produto familiar: usar controles reconheciveis, estados previsiveis e uma hierarquia que desaparece a favor da tarefa.

## 2. Colors

A paleta base e quente e editorial, com contraste de produto. O papel quente (`#f7f4ec`) e paineis suaves (`#fffdf7`) evitam a frieza de dashboards financeiros. O carvao (`#191d1e`) concentra acoes principais e filtros ativos. O verde (`#136f4a`) sinaliza consenso, confianca, progresso e estados positivos.

Use o vermelho (`#b7493d`) para alternativas, resolucao negativa, risco ou favorito quando o icone exigir essa associacao. Use amber (`#d89422`) para prazos e urgencia moderada. Use azul (`#2d5e88`) apenas como sinal secundario, comentarios, informacao ou serie de grafico.

Tokens principais:

- `ink-carbon`: texto principal, alta leitura, nunca decorativo.
- `muted-slate`: copy secundaria, metadados e contadores.
- `warm-paper`: fundo de pagina e area respiravel.
- `soft-panel`: superficies de cards, modais e inputs destacados.
- `clay-panel`: chips, hovers neutros e apoios de navegacao.
- `coal-action`: acao primaria, filtro ativo, marca e enfase maxima.
- `consensus-green`: consenso, acerto, progresso e confianca.
- `resolution-red`: alternativa, erro, risco e favoritos.
- `deadline-amber`: prazo, atencao e estados quase fechando.
- `signal-blue`: comentarios, informacao e series auxiliares.

Evite grandes gradientes dominantes, preto/neon, roxos cripto e vermelho como cor de pressao. Cores de estado devem esclarecer, nao vender urgencia.

## 3. Typography

A familia oficial e IBM Plex Sans. Ela combina densidade de produto com um tom humano e confiavel. Pesos altos sao permitidos em titulos e botoes, mas o corpo deve continuar claro e sem aperto.

Escala recomendada:

- `display`: 34px / 800 / 1.05 para titulos de pagina e momentos raros de marca.
- `headline`: 24px / 800 / 1.1 para cabecalhos de secoes e paginas internas.
- `title`: 18px / 800 / 1.2 para cards de mercado, paineis e badges.
- `body`: 15px / 400 / 1.55 para texto explicativo e conteudo de detalhe.
- `label`: 13px / 750 / 1 para botoes, filtros, tags e acoes compactas.

Titulos de mercado podem quebrar em varias linhas, mas precisam manter ritmo de leitura. Use `overflow-wrap: anywhere` apenas onde ha risco real de URLs, nomes longos ou perguntas muito extensas. Evite caixa alta longa; reserve uppercase para micro-labels como "PRAZO".

## 4. Elevation

Elevacao deve comunicar superficie e foco, nao luxo. A sombra principal (`0 22px 60px rgba(25, 29, 30, 0.12)`) funciona para cards, paineis e modais. Componentes pequenos usam sombras mais baixas, como `0 8px 22px rgba(25, 29, 30, 0.08)`.

Regras:

- Cards e paineis usam borda sutil mais sombra ambiente.
- Topbar usa blur leve para continuidade, nao efeito glass chamativo.
- Hover de botao pode subir 1px; nao usar movimentos elasticos ou decorativos.
- Estados ganhos, como badges conquistados, podem receber brilho verde discreto.
- Evite empilhar card dentro de card; prefira bandas ou layouts sem moldura quando o conteudo for estrutural.

## 5. Components

**Topbar**
Sticky, 72px de altura, blur de 18px, links em pill e marca compacta. Deve sustentar navegacao recorrente sem ocupar a tela. O link ativo usa fundo `clay-panel`, nao uma cor vibrante.

**Buttons**
Botoes sao pills, 42px de altura por padrao. Primario usa `coal-action` com texto claro e sombra moderada. Ghost usa borda `warm-divider` e fundo transparente. Variantes pequenas podem cair para 34px, especialmente em cards.

**Filters**
Filtros sao pills com borda. O ativo deve inverter para carvao, indicando modo sem parecer promocional. Filtros pessoais seguem a mesma linguagem, mas podem usar peso levemente maior.

**Market cards**
O card de mercado e o componente mais importante. Ele combina thumbnail, titulo, tags, metadados, consenso, prazo, grafico compacto e acoes em uma unica unidade. A estrutura deve proteger contra overflow horizontal, manter botoes do rodape na mesma linha quando possivel e preservar leitura de prazo dentro do card.

**Tags and status chips**
Tags usam pills pequenas. Categorias quentes usam amber claro, estados seguros usam mint, risco usa blush. Texto deve permanecer funcional; tags nao sao decoracao.

**Probability and deadline**
Probabilidade usa uma linha compacta com consenso principal e rail de prazo. O rail sempre fica contido no card. Label "PRAZO" pode ser uppercase por ser microtexto, mas o valor precisa alinhar e quebrar sem vazar.

**Forms**
Campos usam fundo `#fffaf0`, raio 14px, borda quente e labels de 13px. Erros usam vermelho com peso maior. Formularios devem parecer seguros e tranquilos, especialmente em cadastro, login, feedback e sugestoes.

**Badges**
Badges usam grid com icone de 62px, copy compacta e sombra baixa. Conquistados recebem borda/topo verde discreto. Bloqueados devem comunicar estado sem punir visualmente.

## 6. Do's and Don'ts

Do:

- Comecar telas principais pelo trabalho do usuario: mercados, filtros, consenso e acoes.
- Usar "previsao", "leitura", "consenso", "reputacao", "credito reservado" e "carteira educativa".
- Mostrar fonte, prazo, status e resolucao sempre que isso aumentar confianca.
- Manter botoes e acoes previsiveis, especialmente em cards repetidos.
- Testar desktop com 3 colunas, desktop medio com 2 colunas e mobile com 1 coluna.
- Dar labels acessiveis para acoes iconizadas e manter foco visivel.

Don't:

- Usar linguagem de aposta, odds, stake, payout, trading, lucro, banca ou promessa de ganho.
- Transformar a home em landing page com hero grande quando o usuario precisa ver mercados.
- Usar neon, preto total, gradiente roxo, visual cripto ou terminal financeiro.
- Empilhar paineis decorativos que roubem espaco dos mercados.
- Depender apenas de cor para explicar sim/nao, aberto/fechado, urgente/resolvido.
- Criar urgencia manipulativa; prazos devem informar, nao pressionar.
