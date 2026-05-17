# Avaliação Simulada do Mock Orynth Market Inspired

## Escopo

Este documento simula uma rodada de avaliação qualitativa do mock público em `docs/mockups/market-inspired/index.html`.

Foram criados:

- `10` usuários finais com perfis diversos para navegar pela experiência pública;
- `1` coordenador para consolidar os achados.

Importante:

- esta rodada foi mantida integralmente na experiência pública;
- os relatos abaixo foram construídos a partir da leitura e navegação lógica do mock estático e de suas interações em `app.js`.

---

## Usuários Finais

### U01 · Amanda, 24, jornalista, acompanha tecnologia e política

- Objetivo: entender rapidamente a proposta e fazer a primeira previsão.
- Fluxo observado: `index.html` -> `market-open.html` -> `prediction-confirmed.html`.
- Considerações:
  - Achou a hero mais clara do que em outros mocks por explicar logo que não há dinheiro real.
  - Gostou do destaque para consenso, auditoria e volume.
  - Sentiu a interface mais madura e menos “social genérica”.
- Problemas encontrados:
  - O tom geral ainda lembra plataforma de trading em alguns momentos, sobretudo por conta de barras, sparks e “ticket de previsão”.
  - A expressão “retorno estimado” ainda soa financeira, mesmo com o aviso educativo.
  - Ela entendeu que 62% é consenso, mas não ficou claro por que deveria confiar nesse consenso sem ver melhor quem compõe esse histórico.

### U02 · Bruno, 36, analista quantitativo, alta familiaridade com dados

- Objetivo: testar consistência entre feed, detalhe e cálculo.
- Fluxo observado: `index.html` -> `market-open.html` -> `concepts.html` -> `wallet.html`.
- Considerações:
  - Gostou da explicação mais direta de que probabilidade não é garantia.
  - Viu avanço na clareza do critério de resolução.
- Problemas encontrados:
  - O cálculo do “retorno estimado” parece fixo em `1.62x` no `app.js`, sem variação aparente por opção ou pelo consenso selecionado.
  - Ao trocar entre `SIM` e `NÃO`, a UI atualiza a escolha, mas não deixa evidente que o retorno deveria mudar conforme o lado escolhido.
  - O mock comunica profundidade de mercado, mas a simulação de cálculo ainda parece superficial para usuários avançados.

### U03 · Carla, 47, professora, pouca intimidade com produtos de previsão

- Objetivo: verificar se consegue compreender a plataforma sem ajuda.
- Fluxo observado: `index.html` -> `concepts.html` -> `security.html` -> `market-open.html`.
- Considerações:
  - A página `concepts.html` ajudou bastante.
  - Gostou do texto “como ler um mercado sem confundir com aposta financeira”.
  - Achou boa a repetição do aviso de que OC não é dinheiro real.
- Problemas encontrados:
  - Mesmo com a explicação, ainda há muito vocabulário visual de mercado financeiro.
  - “Comprometer OC” e “retorno estimado” ainda parecem termos difíceis para uma primeira sessão.
  - A página de detalhe do mercado continua densa para quem só quer entender o básico antes de agir.

### U04 · Diego, 29, gamer competitivo, motivado por ranking e performance

- Objetivo: explorar mercados e comparar mérito pessoal.
- Fluxo observado: `index.html` -> `rankings.html` -> `profile.html` -> `market-multiple.html`.
- Considerações:
  - Curtiu a estética inspirada em mercado e a sensação de competição.
  - Gostou de ver reputação, sequência e badges logo na lateral do feed.
- Problemas encontrados:
  - Sentiu falta de filtros mais ricos por tema ou status, já que os botões de filtro parecem mais demonstrativos que explicativos.
  - O resumo lateral é bom, mas faltam gatilhos mais fortes de progressão pessoal no corpo principal do feed.
  - Em mercados de múltipla escolha, ele esperava mais comparação entre alternativas, não só um líder destacado.

### U05 · Elisa, 41, gerente de produto, foco em clareza de onboarding

- Objetivo: avaliar a jornada de primeira previsão.
- Fluxo observado: `index.html` -> `market-open.html` -> `wallet.html`.
- Considerações:
  - O bloco “Como prever em 40 segundos” ajuda bastante.
  - A hero comunica melhor o valor do produto do que o mock anterior.
- Problemas encontrados:
  - O topo do site e o `app.js` parecem discordar sobre a navegação pública ideal.
  - Em várias páginas públicas o script remove links de `Categorias` e `Carteira` do header, o que pode empobrecer a navegação e até remover o estado ativo da página atual.
  - O produto ensina a prever, mas ainda explica pouco a diferença prática entre ganhar OC e ganhar reputação.

### U06 · Felipe, 20, usuário mobile-first, navega por impulso

- Objetivo: clicar rápido nos mercados e entender se o fluxo responde bem.
- Fluxo observado: `index.html` -> `market-open.html` -> `share-market.html`.
- Considerações:
  - Achou a home escaneável e com bom contraste.
  - Gostou do botão destacado de previsão e dos chips de contexto.
- Problemas encontrados:
  - Alguns elementos parecem interativos, mas o comportamento é mínimo, como filtros que só trocam estado visual.
  - O componente de range para valor da previsão é simples, mas pouco informativo sobre consequências reais da escolha.
  - A página de compartilhamento ainda parece mais institucional que pessoal.

### U07 · Gabriela, 34, criadora de conteúdo, pensa em reputação pública

- Objetivo: prever e depois compartilhar sua leitura de mercado.
- Fluxo observado: `index.html` -> `market-open.html` -> `share-market.html` -> `profile.html`.
- Considerações:
  - Enxergou potencial forte para conteúdo e debate público.
  - Gostou de o mock falar em histórico público e resolução auditável.
- Problemas encontrados:
  - O conteúdo compartilhável destaca bem o mercado, mas pouco a identidade do usuário que fez a previsão.
  - O produto fala em reputação, mas o valor social de “acertar antes dos outros” poderia aparecer com mais protagonismo.
  - Faltam sinais de autoria mais claros entre perfil, badges e previsão compartilhada.

### U08 · Henrique, 54, advogado, atento a linguagem regulatória

- Objetivo: analisar risco de percepção equivocada do produto.
- Fluxo observado: `index.html` -> `concepts.html` -> `wallet.html`.
- Considerações:
  - Viu esforço real para separar o produto de aposta financeira.
  - Considerou acertada a insistência em “moeda educativa”.
- Problemas encontrados:
  - O design de mercado, a linguagem de “ticket”, “retorno estimado” e a metáfora visual de book ainda tensionam essa promessa.
  - O footer público exibe links de operação interna, o que fragiliza a separação entre experiência do usuário e camadas não essenciais para navegação pública.
  - O item `0 R$ sem dinheiro real` ajuda, mas pode soar defensivo se o resto da experiência continuar tão inspirado em trading.

### U09 · Isabela, 27, pesquisadora de IA, procura nuance e qualidade da pergunta

- Objetivo: encontrar mercados confiáveis e bem formulados.
- Fluxo observado: `index.html` -> `market-open.html` -> `market-resolved.html` -> `concepts.html`.
- Considerações:
  - Gostou dos rótulos `Auditável`, `Critério auditável` e da menção à fonte esperada.
  - Viu mais rigor editorial na formulação das perguntas.
- Problemas encontrados:
  - O feed mostra “Fonte: blog oficial/OpenAI”, mas isso mistura fonte esperada de resolução com base informativa atual.
  - O mercado resolvido melhora a confiança, mas ela queria ver mais claramente a justificativa final e não só o resultado.
  - Seria útil distinguir mercados por nível de ambiguidade ou força do critério público.

### U10 · João, 62, aposentado, perfil conservador e literal

- Objetivo: descobrir se consegue navegar com autonomia.
- Fluxo observado: `login.html` -> `index.html` -> `wallet.html` -> `concepts.html`.
- Considerações:
  - Achou o produto mais organizado visualmente do que o mock anterior.
  - Entendeu melhor a diferença entre saldo disponível e saldo bloqueado.
- Problemas encontrados:
  - Ainda confundiu “ganhos por acerto” com “dinheiro ganho”, apesar dos avisos em tela.
  - A recarga educativa controlada é útil, mas parece arbitrária sem explicar quando ela acontece.
  - O produto fala em reputação 82 e acerto 64%, mas não ajuda a entender por que esses números importam para a tomada de decisão.

---

## Relatório do Coordenador · Experiência Pública

### Síntese Executiva

Esta rodada mostra que o mock `market-inspired` está mais claro e mais convincente do que a versão anterior para a experiência pública. O produto comunica melhor seu posicionamento, usa melhor a hero, introduz onboarding curto e reforça mais vezes que OC não é dinheiro real.

Mesmo assim, os `10` relatos convergem para um ponto central: a interface ficou mais didática, mas continua semanticamente próxima demais do universo de trading. O principal desafio agora não é fazer o produto parecer sofisticado; é fazer o produto parecer sofisticado sem parecer financeiro demais.

### Padrões de Problemas Mais Recorrentes

1. Semântica de mercado financeiro ainda dominante

- O visual, o “ticket de previsão”, o “retorno estimado”, o range de valor e os gráficos passam credibilidade, mas também reforçam associação com trading e aposta.
- Isso afeta mais usuários cautelosos, novatos e perfis atentos a compliance.

2. Mecânica pública está mais clara, mas ainda não totalmente confiável

- Houve melhora na explicação de consenso, OC e resolução.
- Ainda assim, permanece dúvida sobre:
  - por que confiar no consenso;
  - como o retorno é calculado;
  - qual a diferença prática entre OC, reputação e acerto;
  - quando existe recarga e com qual critério.

3. Interatividade limitada em componentes que prometem profundidade

- Filtros parecem mais visuais que funcionais.
- O cálculo de retorno aparenta ser simplificado demais para a ambição visual do produto.
- A troca entre `SIM` e `NÃO` não transmite recalibração real do cenário.

4. Navegação pública inconsistente

- O HTML e o `app.js` sugerem intenções diferentes para o header público.
- Em páginas não index, o script remove links como `Categorias` e `Carteira`, o que pode empobrecer navegação e gerar perda de contexto.
- O footer público ainda expõe links de operação interna, o que não deveria fazer parte da jornada do usuário comum.

5. Valor social ainda subexplorado

- O mock comunica bem consenso e auditoria.
- Comunica menos o benefício social de construir reputação pública, acertar cedo e compartilhar uma visão própria.

### Prioridades de Melhoria

#### Prioridade Alta

- Reduzir termos e metáforas excessivamente associados a trading, sobretudo `ticket`, `retorno estimado` e alguns padrões visuais que sugerem produto financeiro.
- Corrigir a navegação pública para que header, footer e `app.js` tenham a mesma arquitetura de links.
- Remover exposição de links internos que não pertencem à jornada pública.
- Tornar mais crível a lógica do cálculo visível na tela de previsão, especialmente ao alternar opções e valor.

#### Prioridade Média

- Explicar melhor por que o consenso merece confiança e como reputação influencia leitura social sem parecer “caixa-preta”.
- Dar mais clareza ao papel da recarga educativa controlada.
- Reforçar a diferença entre saldo, ganho educativo, taxa de acerto e reputação.
- Tornar o compartilhamento mais centrado na autoria da previsão.

#### Prioridade Baixa

- Enriquecer filtros e comparações em mercados múltipla escolha.
- Criar sinais mais claros de progressão pessoal dentro do feed, e não só na lateral.
- Distinguir melhor fonte esperada, fonte observada e justificativa final de resolução.

### Conclusão do Coordenador

O mock `market-inspired` já está em um patamar melhor de comunicação pública. Ele parece mais intencional, mais editorial e mais confiável. O próximo salto de qualidade não depende de adicionar mais blocos ou mais métricas, mas de alinhar melhor três camadas:

- a linguagem usada para não resvalar em semântica financeira;
- a navegação pública para não expor contexto interno;
- a lógica aparente da previsão para que a sofisticação visual seja acompanhada por coerência percebida.

Se esses ajustes forem feitos, a experiência pública tende a ficar mais forte, mais compreensível e menos sujeita a interpretações ambíguas.

---

## Recomendação Final

O melhor próximo passo é desdobrar esta avaliação em uma frente exclusivamente pública com três grupos de ação:

- correções rápidas de navegação e separação de contexto;
- refinamento de copy e semântica da mecânica de previsão;
- melhoria da credibilidade perceptiva do cálculo, da recarga e do compartilhamento.
