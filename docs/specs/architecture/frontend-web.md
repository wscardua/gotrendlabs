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
- Telas públicas de autenticação (`/login/` e `/register/`) devem manter navegação pública compacta para mercados, badges e ranking.
- O aceite de política de uso no cadastro deve permitir leitura sem abandonar o formulário; a UI pode abrir modal com resumo e manter link de fallback para a página pública completa de política.
- A tela de cadastro pode exibir uma prévia de onboarding baseada em dados reais de mercado, desde que não calcule regra de domínio nem simule estado pessoal inexistente.
- Quando a prévia de onboarding usar mercado público, a seleção deve usar apenas campos serializados pelo domínio: maior `market_like_count` entre mercados não cancelados; se nenhum tiver curtida, mercado mais recente por `created_at`.
- Usuários autenticados veem ações iconizadas de `like`/`dislike`; a UI só representa a reação retornada pelo domínio.
- Ordenações e recortes rápidos do feed público podem acontecer no frontend sobre HTML já renderizado, desde que usem somente campos serializados pelo domínio (`is_featured`, `market_like_count`, `created_at`, `close_at`, status e volume).
- O recorte rápido `Resolvidos` do feed público é uma filtragem visual client-side sobre cards já renderizados com status de domínio, sem alterar o contrato público de listagem.
- Favoritos no feed público representam curadoria editorial (`is_featured`) até existir uma feature própria de favoritos por usuário.
- Páginas públicas fora da home devem expor retorno compacto para o feed dentro do primeiro painel de conteúdo, na mesma linha do primeiro rótulo/eyebrow/tags, evitando barra global solta entre header e conteúdo.
- Em desenvolvimento local, a camada Django pode degradar para leitura local quando a FastAPI ainda não foi reiniciada após mudança de rota, mas não deve criar, moderar, reagir, creditar, converter, resolver ou executar qualquer mutação crítica localmente.
- Em fallback local de sugestão/feedback guest, o Django deve validar reCAPTCHA server-side antes de persistir localmente.
- A tela de ranking deve consumir `GET /rankings`; se a FastAPI estiver indisponível, a UI exibe erro/estado vazio sem recalcular reputação em Django ou no navegador.
- O ranking público deve renderizar `handle` como identificação do usuário e nunca exibir recorte pessoal fictício para visitantes.
- A tela autenticada de perfil deve manter a edição básica inline na própria `/profile/`, evitando rota separada para alteração de dados pessoais.
- A UI de perfil não deve exibir dados privados em blocos públicos/resumo; email, data de nascimento, sexo e bio aparecem somente como campos editáveis do usuário autenticado.
- A página pública de badges renderiza o catálogo vindo da API; quando houver sessão, exibe estado pessoal retornado pelo domínio sem calcular elegibilidade no template.
- Cards de badge usam `image_url` como imagem padrão/tema claro e trocam para `image_dark_url` quando o tema escuro estiver ativo; se a imagem escura não existir, a imagem padrão permanece como fallback.
- A ação de compartilhar badge só aparece para usuário autenticado em badge com `status=earned`; a rota `/share/badge/{code}/` valida a conquista via contrato de badges antes de renderizar.
- Compartilhamento social no frontend é apresentação de estado persistido: pergunta de mercado, resultado e badge podem expor links por rede, metadados Open Graph/Twitter e imagem social dinâmica, mas não disparam concessão, reputação, ranking, wallet ou ledger.
- Cards sociais usam URL pública configurável para que crawlers de redes consigam ler `og:image`; em host local a UI deve indicar que o preview externo não é rastreável.
- Compartilhamento de badge conquistada pode gerar URL pública com token opaco de conquista, sem expor id, email ou handle no query string.
- Cards de mercado sem imagem devem exibir fallback visual legível com iniciais derivadas de categoria/subcategoria/título no feed e nas imagens sociais.
