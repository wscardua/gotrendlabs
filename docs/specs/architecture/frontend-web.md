# Frontend Web

## Responsabilidades

- Renderizar páginas públicas e autenticadas.
- Servir feed, detalhe de mercado, perfil, ranking, wallet e fluxos de autenticação.
- Fazer chamadas ao `backend-api` para leitura e mutações de domínio.
- Aplicar i18n, formatação local e textos não hardcoded.
- Usar HTMX para atualizações parciais e Alpine.js para estados locais simples.
- Renderizar reCAPTCHA v2 checkbox nos formulários públicos protegidos quando configurado, enviando apenas o token ao `backend-api`.

## Não Responsabilidades

- Calcular stake, payout, reputação ou probabilidades.
- Resolver mercados.
- Consolidar regras de saldo.
- Persistir decisões de negócio fora dos contratos da API.
- Validar ou confiar em CAPTCHA apenas no navegador.

## Entradas e saídas

- Entrada: respostas do `backend-api`, contexto de sessão e traduções.
- Saída: páginas HTML, interações parciais, formulários e eventos de UI.

## Guardrails

- Toda ação mutável relevante deve passar pelo `backend-api`.
- Textos de interface devem estar preparados para `pt-BR` e `en`.
- Qualquer regra de exibição condicionada por estado de mercado deve depender de estados vindos do contrato de domínio.
- Comentários no detalhe do mercado exibem o autor como handle iniciado por `@`.
- Visitantes podem ler comentários e veem CTA de login para comentar/reagir.
- Visitantes veem reCAPTCHA em cadastro e nos envios guest de sugestão/feedback quando `RECAPTCHA_ENABLED` estiver ativo; usuários autenticados não veem CAPTCHA em sugestão/feedback.
- Telas públicas de autenticação (`/login/`, `/register/` e recuperação de senha) devem manter navegação pública compacta para mercados, badges e ranking, além do rodapé público compartilhado.
- O aceite de política de uso no cadastro deve permitir leitura sem abandonar o formulário; a UI pode abrir modal com resumo e manter link de fallback para a página pública completa de política.
- A tela de cadastro pode exibir uma prévia de onboarding baseada em dados reais de mercado, desde que não calcule regra de domínio nem simule estado pessoal inexistente.
- Quando a prévia de onboarding usar mercado público, a seleção deve usar apenas campos serializados pelo domínio: maior `view_count` entre mercados publicados não cancelados disponíveis localmente/publicamente, excluindo `draft` e `canceled`, com mercado mais recente por `created_at` como desempate/fallback.
- A opção de lembrar acesso no login prolonga a sessão Django no dispositivo sem persistir senha ou alterar o contrato de autenticação da API.
- A tela de login deve oferecer recuperação de senha; o Django renderiza os formulários, preserva navegação pública e alternância de tema nas telas de recuperação, mas a solicitação e confirmação da senha passam pela FastAPI.
- Usuários autenticados veem ações iconizadas de `like`/`dislike`; a UI só representa a reação retornada pelo domínio.
- Listas web simples do produto e browses principais do Admin Ops devem usar o padrão `Carregar mais` em blocos cumulativos de 10 itens; paginação por offset fica reservada para auditorias ou telas com necessidade explícita de navegação posicional.
- Ordenações e recortes rápidos do feed público podem acontecer no frontend sobre HTML já renderizado, desde que usem somente campos serializados pelo domínio (`viewer_has_favorite`, `viewer_has_prediction`, `viewer_has_like`, `is_featured`, `market_like_count`, `view_count`, `created_at`, `close_at`, status e volume).
- Métricas públicas da home devem consumir labels e totais prontos do backend/fallback local (`open_markets`, `total_predictions`, `distributed_oc`, `moved_oc`); a UI não calcula totais de ledger, stakes, wallet ou previsão.
- O label `distributed_oc` já deve chegar sem créditos de operadores; a UI não aplica filtro por papel em métricas públicas.
- A moeda educativa deve ser exibida como `O₵` em textos visíveis; identificadores técnicos, campos e nomes internos continuam usando `_oc`.
- O recorte rápido `Resolvidos` do feed público é uma filtragem visual client-side sobre cards já renderizados com status de domínio, sem alterar o contrato público de listagem.
- Favoritos no feed da home representam mercados salvos pelo usuário autenticado; visitantes podem ver affordance readonly de favorito, mas a mutação e o recorte `Favoritos` permanecem autenticados. `is_featured` permanece como curadoria editorial para destaques visuais.
- Curtidas no card representam engajamento público do mercado e são separadas de favoritos pessoais e de likes/dislikes em comentários.
- Páginas públicas fora da home devem expor retorno compacto para o feed dentro do primeiro painel de conteúdo, na mesma linha do primeiro rótulo/eyebrow/tags, evitando barra global solta entre header e conteúdo.
- O rodapé público deve priorizar Institucional, Produto, Confiança e Suporte; links de conta, mercados recorrentes e Admin Ops pertencem à navegação principal ou ao chip autenticado.
- A entrada de Admin Ops no chip do usuário só pode renderizar quando o contexto autenticado indicar `is_staff` ou `is_superuser`.
- Em desenvolvimento local, a camada Django pode degradar para leitura local quando a FastAPI ainda não foi reiniciada após mudança de rota, mas não deve criar, moderar, reagir, creditar, converter, resolver ou executar qualquer mutação crítica localmente.
- Em fallback local de sugestão/feedback guest, o Django deve validar reCAPTCHA server-side antes de persistir localmente.
- A tela de ranking deve consumir `GET /rankings`; se a FastAPI estiver indisponível, a UI exibe erro/estado vazio sem recalcular reputação em Django ou no navegador.
- O ranking público deve renderizar `handle` como identificação do usuário e nunca exibir recorte pessoal fictício para visitantes.
- A tela autenticada de perfil deve manter a edição básica inline na própria `/profile/`, evitando rota separada para alteração de dados pessoais.
- A tela autenticada de perfil deve preencher campos com dados reais retornados por `/users/me`, priorizando `orynth_user_profiles.display_name` para o nome editável.
- A UI de perfil não deve exibir dados privados em blocos públicos/resumo; email, data de nascimento, sexo e bio aparecem somente como campos editáveis do usuário autenticado.
- O ticket de previsão deve iniciar sem opção marcada, orientar a seleção explícita e usar controle nativo obrigatório para impedir confirmação ambígua.
- Usuário autenticado sem saldo disponível deve ver o ticket em estado de leitura, com indicação de saldo indisponível e CTA para wallet.
- A página pública de badges renderiza o catálogo vindo da API; quando houver sessão, exibe estado pessoal retornado pelo domínio sem calcular elegibilidade no template.
- Cards de badge usam `image_url` como imagem padrão/tema claro e trocam para `image_dark_url` quando o tema escuro estiver ativo; se a imagem escura não existir, a imagem padrão permanece como fallback.
- A ação de compartilhar badge só aparece para usuário autenticado em badge com `status=earned`; a rota `/share/badge/{code}/` valida a conquista via contrato de badges antes de renderizar.
- Compartilhamento social no frontend é apresentação de estado persistido: pergunta de mercado, resultado e badge podem expor links por rede, metadados Open Graph/Twitter e imagem social dinâmica, mas não disparam concessão, reputação, ranking, wallet ou ledger.
- Compartilhamento social de mercado deve mostrar opções/probabilidades e CTA clicável para o detalhe, usando texto editorial de incentivo sem criar ação de domínio.
- Cards sociais usam URL pública configurável para que crawlers de redes consigam ler `og:image`; em host local a UI deve indicar que o preview externo não é rastreável.
- Compartilhamento de badge conquistada pode gerar URL pública com token opaco de conquista, sem expor id, email ou handle no query string.
- Cards de mercado com `image_url` devem tratar a imagem como thumbnail visual pura do evento, sem título, texto, categoria ou marca embutidos. A UI já renderiza título, tags e fonte em HTML; a thumbnail deve apenas reforçar visualmente o tema do mercado e encaixar em corte quadrado com `object-fit: cover`.
- Cards de mercado sem imagem devem exibir fallback visual legível com iniciais derivadas de categoria/subcategoria/título no feed e nas imagens sociais.
