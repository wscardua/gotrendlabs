# Avaliação Simulada do Mock GoTrendLabs

## Escopo

Este documento simula uma rodada de avaliação qualitativa do mock navegável em `docs/mockups/experience/index.html` e das telas administrativas relacionadas.

Foram criados:

- `10` usuários finais com perfis diversos para navegar pela experiência pública;
- `5` administradores para operar o painel admin;
- `2` coordenadores, um para consolidar os relatórios da experiência pública e outro para consolidar os relatórios do admin.

Observação importante: esta avaliação foi construída a partir da leitura e navegação lógica do mock estático. Os relatos abaixo representam feedbacks plausíveis e úteis para refinamento de produto, UX e operação.

---

## Usuários Finais

### U01 · Ana Paula, 22, estudante de jornalismo, heavy user de X e TikTok

- Objetivo: entender rápido o que é a GoTrendLabs e fazer a primeira previsão.
- Fluxo observado: `index.html` -> `market-open.html` -> `prediction-confirmed.html` -> `rankings.html`.
- Considerações:
  - Gostou do feed inicial e da sensação de produto vivo.
  - Entendeu a ideia de consenso e reputação antes de entender a lógica da stake.
  - Achou forte a proposta "preveja antes do consenso".
- Problemas encontrados:
  - `stake`, `reward`, `binary`, `multiple choice` e `HTMX refresh` aparecem misturados com PT-BR e quebram fluidez.
  - O card mostra um mercado de IA com linguagem simples, mas a página de detalhe introduz "peso base" e "sua entrada" sem explicação imediata.
  - A usuária não soube se "62% SIM" significa chance real, opinião da comunidade ou retorno esperado.

### U02 · Bruno, 31, analista de dados, familiaridade alta com mercados e métricas

- Objetivo: validar se a mecânica parece consistente.
- Fluxo observado: `index.html` -> `market-open.html` -> `concepts.html` -> `wallet.html`.
- Considerações:
  - Achou bom existir uma página de conceitos.
  - Valorizou a separação entre moeda interna e reputação.
  - Entendeu o racional macro do produto.
- Problemas encontrados:
  - Em `market-open.html`, o texto diz que o evento vale até `31 de dezembro de 2026`, mas o resumo lateral informa `Resolve em 12 dez 2026`. Há incoerência de datas.
  - O campo "Reward bruto se acertar 161 GTL" parece exato demais para algo explicado depois como fórmula não totalmente pública.
  - "Peso base 10.000" é exposto sem contexto suficiente para usuário avançado confiar.

### U03 · Carla, 45, professora, usa pouco produtos financeiros

- Objetivo: entender se a plataforma é aposta ou jogo de opinião.
- Fluxo observado: `index.html` -> `security.html` -> `concepts.html` -> `wallet.html`.
- Considerações:
  - Achou positivo o produto afirmar que não usa dinheiro real.
  - Gostou da preocupação com segurança e auditoria.
- Problemas encontrados:
  - O vocabulário ainda remete a aposta em vários momentos: stake, payout, reward, volume.
  - Ficou insegura sobre perder moedas: não entendeu se existe recarga automática ou limite de perda educativa.
  - A plataforma comunica "rede social de previsões", mas a ação principal é sempre financeira em torno da moeda interna.

### U04 · Diego, 28, gamer competitivo, gosta de ranking

- Objetivo: comparar desempenho e achar temas de Games.
- Fluxo observado: `index.html` -> `rankings.html` -> `categories.html` -> `market-multiple.html`.
- Considerações:
  - Curtiu a camada social e a ideia de badges.
  - Gostou de ver categorias claras e mercados com disputa.
- Problemas encontrados:
  - No feed, Games aparece como categoria, mas o destaque principal do produto é muito concentrado em IA.
  - Faltam sinais mais fortes de progressão pessoal no feed, além do bloco lateral.
  - Em múltipla escolha, ele esperaria comparação entre opções mais visual e não só uma liderança resumida.

### U05 · Eliane, 39, gerente de operações, foco em clareza e confiabilidade

- Objetivo: avaliar se as regras parecem auditáveis.
- Fluxo observado: `index.html` -> `market-open.html` -> `market-resolved.html` -> `feedback.html`.
- Considerações:
  - Achou correto existir fonte verificável e trilha de resolução.
  - Percebeu valor em premiar feedbacks úteis.
- Problemas encontrados:
  - Não ficou claro, na jornada principal, onde o usuário vê a fonte da resolução antes de confiar no resultado.
  - A passagem entre mercado aberto e resolvido parece brusca; faltam estados intermediários mais pedagógicos.
  - O feedback recompensável é bom, mas pode gerar suspeita se não houver critério visível de aprovação.

### U06 · Felipe, 19, universitário, mobile-first

- Objetivo: navegar rápido e interagir sem ler muito.
- Fluxo observado: `index.html` -> `market-open.html` -> `share-market.html`.
- Considerações:
  - Gostou das barras, chips e visual dos cards.
  - Disse que o mock parece moderno e fácil de explorar.
- Problemas encontrados:
  - Vários elementos com aparência de botão parecem estáticos no mock, como tabs e presets de stake.
  - A densidade de informação no detalhe do mercado é alta para primeira sessão.
  - Comentários têm pouca hierarquia visual entre opinião, moderação e ação.

### U07 · Gabriela, 33, criadora de conteúdo, pensa em compartilhamento

- Objetivo: prever e compartilhar mercados interessantes.
- Fluxo observado: `index.html` -> `market-open.html` -> `share-market.html` -> `profile.html`.
- Considerações:
  - Viu potencial de compartilhamento social forte.
  - Gostou de existir perfil público e histórico.
- Problemas encontrados:
  - Faltou deixar mais explícito como o compartilhamento reforça reputação pessoal.
  - O card social parece orientado ao mercado, mas não ao autor da previsão.
  - A diferença entre "perfil público", "meu ranking" e "ranking" poderia ser mais clara.

### U08 · Henrique, 52, advogado, atento a linguagem e compliance

- Objetivo: verificar ambiguidade de termos e risco regulatório de percepção.
- Fluxo observado: `index.html` -> `concepts.html` -> `security.html` -> `wallet.html`.
- Considerações:
  - A spec visual de confiança está bem encaminhada.
  - A preocupação com fonte, auditoria e moderação ajuda.
- Problemas encontrados:
  - O produto afirma não ser aposta, mas a carteira usa termos como `payout` e a experiência de stake é central.
  - O link "Admin demo" no footer público quebra um pouco a separação entre área pública e operacional.
  - A mistura `PT-BR / EN` aparece como rótulo, mas não como escolha efetiva de idioma.

### U09 · Isabela, 26, pesquisadora de IA, procura profundidade

- Objetivo: encontrar mercados especializados e entender o racional de consenso.
- Fluxo observado: `index.html` -> `category-ia.html` -> `market-open.html` -> `concepts.html`.
- Considerações:
  - Gostou do recorte temático e da ideia de inteligência coletiva.
  - Achou positivo existir explicação separada para conceitos.
- Problemas encontrados:
  - O mercado de destaque usa uma pergunta chamativa, mas a interface não diferencia bem mercados "populares" de mercados "qualificados".
  - Faltam indicadores de qualidade da pergunta, como clareza, fonte esperada ou nível de ambiguidade.
  - A relação entre reputação do usuário e peso da previsão deveria ser explicada com mais cuidado para evitar sensação de elite fechada.

### U10 · João, 61, investidor aposentado, baixa tolerância a ambiguidades

- Objetivo: descobrir se consegue usar a plataforma sem ajuda.
- Fluxo observado: `index-guest.html` -> `register.html` -> `index.html` -> `wallet.html`.
- Considerações:
  - Achou o topo de navegação organizado.
  - Entendeu que há categorias, ranking e carteira.
- Problemas encontrados:
  - Não entendeu a diferença entre saldo disponível, bloqueado, ganhos no mês e reputação logo de início.
  - O extrato tem um item "Payout · TikTok banido nos EUA" que pode soar inconsistente se o mercado resolvido foi `NÃO`; faltou mostrar o lado previsto pelo usuário ou uma descrição mais neutra.
  - Sentiu falta de um onboarding resumido antes de incentivar a primeira previsão.

---

## Relatório do Coordenador · Experiência Pública

### Síntese Executiva

Os `10` relatos convergem para uma percepção positiva do conceito central do produto: o mock comunica bem a proposta de rede social de previsões, ranking e inteligência coletiva. O visual é forte, o feed é atraente e a plataforma transmite energia de produto vivo.

Ao mesmo tempo, a avaliação aponta que a experiência ainda depende demais de linguagem semi-financeira e de conceitos internos pouco explicados. O maior risco não é visual; é de entendimento e confiança.

### Padrões de Problemas Mais Recorrentes

1. Mistura de idioma e jargão

- Termos como `stake`, `reward`, `binary`, `multiple choice`, `payout` e `HTMX refresh` aparecem misturados ao PT-BR.
- Isso afeta especialmente usuários novos, menos técnicos e perfis mais sensíveis a percepção de aposta.

2. Clareza insuficiente da mecânica principal

- Usuários entendem rapidamente "prever" e "ranking", mas demoram a entender:
  - o que exatamente é stake;
  - como a probabilidade deve ser interpretada;
  - quando GTL volta, trava ou é perdida;
  - quando reputação muda.

3. Incoerências e sinais que enfraquecem confiança

- Inconsistência de datas entre critério do mercado e data de resolução.
- Extrato da carteira com descrição ambígua do evento resolvido.
- Exposição de conceitos como "peso base" sem explicação proporcional.

4. Tensão entre posicionamento social e semântica de aposta

- O produto afirma não ser casa de aposta, mas parte da linguagem e da carteira ainda evocam esse universo.
- Esse ponto apareceu com força em perfis mais cautelosos e orientados a compliance.

5. Progressão e onboarding

- O mock convida cedo para prever, mas explica tarde como a plataforma funciona.
- Usuários menos experientes pedem uma camada curta de educação antes da primeira decisão.

### Prioridades de Melhoria

#### Prioridade Alta

- Padronizar terminologia em PT-BR, com opção de inglês real quando o seletor de idioma existir.
- Corrigir incoerências de datas e descrições de extrato.
- Reescrever a explicação curta da stake e da probabilidade dentro do próprio detalhe do mercado.
- Mostrar de forma mais explícita a fonte e o racional de resolução no fluxo público.

#### Prioridade Média

- Introduzir onboarding curto para primeira previsão.
- Diferenciar melhor reputação, saldo e ranking.
- Reduzir a exposição de termos internos como "peso base" na camada pública ou contextualizá-los melhor.
- Reforçar o valor social do compartilhamento pessoal, e não só do mercado.

#### Prioridade Baixa

- Diversificar melhor o destaque de categorias no feed.
- Fortalecer sinais de progressão pessoal e histórico de mérito no feed principal.

### Conclusão do Coordenador

O mock tem boa base de proposta de valor e um visual convincente. O principal trabalho agora é transformar curiosidade em confiança. Se a equipe reduzir ambiguidades de linguagem, corrigir inconsistências de regra e explicar melhor o impacto da stake, a experiência pública tende a parecer mais madura e menos arriscada para usuários novos.

---

## Administradores

### A01 · Marina, 34, product ops

- Objetivo: criar mercado novo e validar checklist editorial.
- Fluxo observado: `admin-dashboard.html` -> `admin-market-edit.html`.
- Considerações:
  - Gostou do painel resumido e da separação entre criação, resolução e moderação.
  - Achou útil a prévia do card no editor.
- Problemas encontrados:
  - O editor comunica "rascunho salvo há 12s", mas não deixa claro onde está o histórico ou o estado de publicação.
  - A tradução EN aparece como checklist pendente, mas sem fluxo claro para edição localizada.
  - "Excluir" aparece como ação rápida mesmo em mercados com previsões; o aviso existe, mas a ação ainda parece perigosa visualmente.

### A02 · Rafael, 41, operador de compliance

- Objetivo: revisar mercados próximos da resolução.
- Fluxo observado: `admin-dashboard.html` -> `admin-resolution.html` -> `admin-resolution-review.html`.
- Considerações:
  - A fila de resolução está fácil de escanear.
  - A ideia de registrar fonte, operador e impacto transmite boa governança.
- Problemas encontrados:
  - Há mistura entre mercados com fonte pronta, pendente e indefinida, mas sem prioridade visual realmente forte.
  - "Publicar resolução" parece simples demais para uma ação sensível; faltaria confirmação mais robusta.
  - Não está evidente como reversões, disputas ou auditorias posteriores seriam tratadas.

### A03 · Silvia, 29, moderadora de comunidade

- Objetivo: revisar sugestões, feedbacks e comentários reportados.
- Fluxo observado: `admin-dashboard.html` -> `admin-moderation.html`.
- Considerações:
  - A centralização de sugestões, feedback e LGPD na mesma tela ajuda a visão operacional.
  - A recompensa de feedback está bem conectada ao produto.
- Problemas encontrados:
  - A tela mistura demais tarefas de natureza distinta: curadoria, bug triage, trust & safety e solicitações sensíveis.
  - Ações como "Aprovar e recompensar" e "Rejeitar" parecem muito próximas para decisões irreversíveis.
  - Não há critérios visíveis para evitar subjetividade na aprovação de feedback útil.

### A04 · Tiago, 38, editor de conteúdo multilíngue

- Objetivo: validar operação PT-BR/EN.
- Fluxo observado: `admin-market-edit.html` -> `admin-dashboard.html`.
- Considerações:
  - Percebeu que o produto já foi pensado para multilíngue.
  - Gostou do campo `Locale base`.
- Problemas encontrados:
  - O mock sinaliza idioma, mas não mostra fluxo concreto de tradução, revisão, diff ou aprovação por locale.
  - Não fica claro se categorias, imagens de share e critérios públicos são sincronizados entre idiomas.
  - Há risco de publicação parcial de um mercado sem consistência entre PT-BR e EN.

### A05 · Vanessa, 46, coordenadora de risco operacional

- Objetivo: verificar saúde do sistema e exposição a erro operacional.
- Fluxo observado: `admin-dashboard.html` -> `admin-resolution.html` -> `admin-moderation.html`.
- Considerações:
  - Os KPIs do topo ajudam a triagem diária.
  - O mock comunica preocupação com scheduler, fila e alertas.
- Problemas encontrados:
  - O dashboard não explicita SLA, aging dos itens ou impacto por fila.
  - "Alertas 1 risco" é pouco acionável sem detalhamento imediato.
  - Faltam distinções visuais mais fortes entre tarefa urgente de produto e tarefa crítica de segurança/compliance.

---

## Relatório do Coordenador · Admin

### Síntese Executiva

Os `5` administradores consideraram a estrutura do painel promissora e coerente com o MVP. A divisão em `Mercados`, `Resolução` e `Moderação` ajuda bastante. O principal risco identificado não é falta de funcionalidade aparente, mas insuficiência de guardrails para decisões sensíveis.

### Padrões de Problemas Mais Recorrentes

1. Ações críticas com pouca fricção

- Publicar resolução, excluir mercado e aprovar recompensas parecem ações rápidas demais para o nível de impacto descrito.
- O mock pede mais confirmação, trilha e hierarquia de risco.

2. Mistura de contextos operacionais

- A moderação reúne curadoria de mercados, feedback de produto, abuso e solicitações LGPD.
- Isso ajuda a centralizar, mas dificulta foco, priorização e accountability.

3. Governança multilíngue incompleta

- O sistema sinaliza PT-BR/EN, porém o fluxo operacional de tradução e revisão ainda não está claro.
- Falta uma visão explícita de status por locale antes da publicação.

4. Priorização operacional fraca

- Há indicadores numéricos, mas pouca informação sobre severidade, aging, impacto em usuários ou SLA.
- Operadores mais experientes tendem a pedir ordenação por risco e urgência real.

5. Auditoria visível, mas ainda superficial

- O mock cita operador, fonte e horário, o que é ótimo.
- Porém não aparecem com clareza histórico de mudanças, dupla checagem, motivos de reversão ou evidências anexas.

### Prioridades de Melhoria

#### Prioridade Alta

- Inserir confirmações robustas e estados de revisão para ações críticas.
- Separar melhor filas por natureza: editorial, resolução, trust & safety e solicitações sensíveis.
- Criar status operacional por idioma e bloqueio de publicação incompleta.

#### Prioridade Média

- Exibir aging, SLA e impacto por item nas filas.
- Tornar alertas mais acionáveis, com drill-down direto.
- Mostrar melhor histórico/auditoria de decisões relevantes.

#### Prioridade Baixa

- Aprimorar ergonomia visual do dashboard para leitura rápida por função.
- Destacar melhor dependências entre scheduler, resolução e exposição pública.

### Conclusão do Coordenador

O admin já passa sensação de operação real, mas ainda precisa parecer seguro o suficiente para sustentar decisões sensíveis. A próxima evolução deve focar menos em adicionar novas telas e mais em tornar visíveis os controles, prioridades e trilhas que reduzem erro humano.

---

## Recomendação Final

Se a equipe quiser transformar este material em um artefato de trabalho prático, o próximo passo ideal é desdobrar os achados em três listas:

- ajustes rápidos de copy e consistência;
- melhorias de UX para entendimento da mecânica;
- reforços operacionais do admin para governança e confiança.
