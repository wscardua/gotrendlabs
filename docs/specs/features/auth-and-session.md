---
id: FEAT-AUTH-001
titulo: "Autenticação e sessão"
versao: 0.3
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-06-06
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - i18n-content.md
  - domain-events.md
dependencias: []
impacta:
  - frontend-web
  - backend-api
  - database
  - communications
aprovacao: pendente
---

# Autenticação e sessão

## Objetivo

Permitir cadastro, login, login social, manutenção de sessão e preferência de idioma para acesso às áreas autenticadas.

## Escopo incluído

- cadastro
- aceite obrigatório da política de uso no cadastro
- página pública de política de uso e leitura em modal no fluxo de cadastro
- proteção anti-abuso com reCAPTCHA v2 checkbox no cadastro quando configurado
- cadastro por link de indicação opcional, com bônus educativo ao indicador quando validado pelo backend
- login por credencial ou provedor social
- criação e validação de sessão
- logout
- recuperação de senha por token de uso único
- envio transacional do link de recuperação sem expor o link na resposta pública
- confirmação de email por token expirável e uso único
- login limitado para conta com email ainda não confirmado
- recuperação do contexto do usuário autenticado
- edição básica de perfil autenticado
- exclusão lógica de conta
- gestão administrativa de usuários cadastrados para suporte operacional
- marcação administrativa de contas controladas por robôs internos
- geração administrativa auditada de link de recuperação de senha

## Escopo excluído

- MFA
- SSO corporativo
- gestão avançada de dispositivos
- ajuste manual de reputação

## Fluxo do usuário

Usuário chega à interface pública, cria conta ou faz login, escolhe ou herda idioma preferencial e passa a acessar feed, perfil, wallet e ações autenticadas.

## Comportamento esperado

- sessões inválidas redirecionam para autenticação
- login social cria ou vincula conta de forma rastreável para `google`, `facebook` e `x`
- idioma preferencial acompanha a sessão
- cadastro sem aceite da política de uso é rejeitado
- link da política de uso no cadastro abre resumo em modal sem perder o formulário e mantém acesso à página completa
- telas de login, cadastro e recuperação de senha mantêm navegação pública para feed/mercados, badges e ranking, alternância de tema, rodapé público e retorno compacto `← Voltar` no primeiro painel de conteúdo, usando origem local confiável quando existir e fallback para o feed
- rodapé público mantém links institucionais, produto, confiança e suporte; links de conta, mercados e operações administrativas não aparecem no rodapé
- link `Painel Administrativo` aparece apenas no chip do usuário autenticado quando o contexto indica `is_staff` ou `is_superuser`, como primeira ação e com sinalização visual de acesso restrito
- login pode prolongar a sessão no dispositivo quando o usuário marca a opção de lembrar acesso, sem salvar senha no navegador
- login oferece recuperação de senha por email; a resposta pública não expõe o link de reset
- cadastro com email ativo em produção cria conta em login limitado, envia boas-vindas e, quando necessário, envia link de confirmação
- usuário com email não confirmado pode entrar, mas ações sensíveis ficam bloqueadas até confirmar o endereço
- alteração de email no perfil invalida a confirmação anterior e dispara novo link de confirmação quando email estiver ativo
- login e cadastro exibem affordances iconizadas para provedores sociais iniciais (`google`, `facebook`, `x`) e iniciam OAuth real via Django, mantendo a FastAPI como fonte de verdade do vínculo e da sessão
- clique em login social registra aceite da política de uso vigente; email verificado pelo provedor nasce confirmado, email não verificado nasce em login limitado e recebe link de confirmação; quando uma identidade social nova não retorna email, a FastAPI emite token pendente assinado/expirável e a web solicita email antes de criar a conta limitada
- tela de cadastro pode exibir prévia não personalizada do produto usando mercado público real como exemplo de ticket
- cadastro sem reCAPTCHA válido é rejeitado quando a proteção estiver habilitada
- cadastro iniciado por `?ref=` preserva o código de indicação e o envia à FastAPI; código inválido não bloqueia criação de conta
- perfil autenticado exibe reputação em cards e mantém edição de dados na própria tela de perfil, sem rota separada
- perfil autenticado usa `gotrendlabs_user_profiles.display_name` como fonte principal do nome editável; `gotrendlabs_users.first_name` permanece apenas como fallback/compatibilidade
- perfil autenticado mantém o prefixo `@` do identificador como fixo na UI; o usuário edita apenas o nome do handle e o backend continua normalizando/preservando `@`
- `birth_date`, `sex`, email e bio são privados ao usuário autenticado e não aparecem no perfil público
- exclusão lógica desativa login e sessões sem apagar dados físicos
- Admin Ops lista usuários, abre detalhe operacional amplo e exibe badges adquiridas para suporte
- Admin Ops pode marcar/desmarcar usuário como `bot` quando a conta for controlada por robôs internos; essa informação é visível apenas em contratos administrativos
- Admin Ops pode gerar link de reset de senha para conta ativa, com nota operacional e auditoria; staff atua sobre usuários comuns e apenas superuser atua sobre contas staff/superuser
- ações administrativas de usuário usam contratos staff da FastAPI; o Django apenas renderiza estado e envia formulários

## Regras de domínio

- um usuário deve possuir identidade única no domínio
- identificadores públicos de usuário devem manter o prefixo `@`, inclusive após edição de perfil
- cada sessão precisa ser validável e revogável
- login social não pode gerar duplicidade silenciosa de contas; identidade externa existente faz login direto mesmo quando o provedor não retorna email, email existente só é vinculado automaticamente quando o provedor retornar email verificado, e email existente sem verificação confiável deve ser bloqueado com orientação para login normal
- login social sem email do provedor não cria conta automaticamente; exige email informado pelo usuário junto de token pendente assinado pela FastAPI, cria conta com email não confirmado e dispara confirmação imediata quando emails transacionais estiverem ativos
- aceite de política de uso deve guardar data e versão aceita
- reCAPTCHA protege criação de conta contra abuso automatizado sem substituir validações de identidade, senha e aceite
- exclusão lógica deve preservar histórico e bloquear uso normal
- ações administrativas sobre conta exigem usuário staff, nota operacional e auditoria
- operador não pode desativar nem revogar sessões da própria conta; ajuste manual de wallet da própria conta é permitido para `staff`/`superuser`, desde que tenha nota e auditoria
- operador não pode gerar reset administrativo da própria conta
- alteração de `is_staff` e `is_superuser` exige operador `is_superuser=true`, nota operacional e auditoria
- operador não pode alterar privilégios da própria conta; `is_superuser=true` implica `is_staff=true`
- sistema não permite remover o último superusuário ativo
- gestão administrativa não permite alterar reputação manualmente nesta fatia
- `is_bot` não deve aparecer em `/users/me`, sessão comum ou perfil público
- confirmação de email usa hash de token, expiração e uso único
- reenvio de confirmação exige autenticação e respeita limite simples de frequência
- staff, superuser e robôs internos não ficam bloqueados pelo login limitado
- indicação bonificada exige indicador comum ativo, valor configurado no Admin Ops, recompensa idempotente por convidado e crédito auditável em ledger sem reputação, badge ou ranking

## Responsabilidades por camada

- `frontend-web`: formulários, telas, redirecionamento e mensagens localizadas
- `backend-api`: autenticação, sessão, vínculo de provedor, política de acesso e contratos staff de suporte a usuários
- `database`: usuário, credenciais externas, sessão e preferências
- `communications`: email de boas-vindas, confirmação e recuperação de senha

## Dados e persistência

- usuário
- perfil básico
- data de nascimento e sexo opcionais no perfil privado/editável (`birth_date` em `YYYY-MM-DD`; `sex` como `male`, `female`, `other` ou `prefer_not_to_say`)
- provedores externos vinculados
- preferência de idioma
- sessões e rastros de autenticação
- tokens de recuperação de senha com hash, expiração e uso único
- tokens de confirmação de email com hash, expiração e uso único
- timestamp `email_confirmed_at` no usuário
- aceite de política de uso
- estado da conta e timestamps de exclusão lógica
- marcador administrativo `is_bot`

## Contratos afetados

- `i18n-content.md`
- `domain-events.md`

## I18n e conteúdo

- mensagens de erro e sucesso precisam existir em `pt-BR` e `en`
- idioma preferencial deve ser persistido

## Observabilidade e operação

- registrar falhas de login e origem de autenticação
- disponibilizar trilha mínima para suporte
- Admin Ops deve permitir listagem, busca, detalhe amplo, badges adquiridas, desativação/reativação, revogação de sessões, gestão controlada de papéis e marcação `is_bot` via contratos staff
- ações administrativas de conta devem registrar `user.deactivate`, `user.reactivate`, `user.sessions_revoke`, `user.wallet_adjust`, `user.roles_update`, `user.bot_update` ou `user.password_reset_request` em `gotrendlabs_admin_events`
- contratos staff mínimos: `GET /admin/users`, `GET /admin/users/{user_id}`, `POST /admin/users/{user_id}/deactivate`, `POST /admin/users/{user_id}/reactivate`, `POST /admin/users/{user_id}/sessions/revoke`, `POST /admin/users/{user_id}/roles`, `POST /admin/users/{user_id}/bot`, `POST /admin/users/{user_id}/password-reset`

## Testes esperados

- unitários para vínculo e validação de sessão
- integração para login social real, vínculo seguro de conta existente, criação de conta nova e persistência de preferência de idioma
- fluxo de cadastro, login e logout
- fluxo de recuperação de senha com solicitação, token válido, token inválido/expirado e token reutilizado
- fluxo de confirmação de email com token válido, token inválido/expirado, uso único e reenvio
- login limitado para usuário sem email confirmado e bloqueio de ações sensíveis
- fluxo de aceite obrigatório da política de uso
- renderização de política de uso pública e modal de política no cadastro
- renderização de navegação pública, alternância de tema, rodapé público e retorno compacto `← Voltar` em login/cadastro/recuperação de senha
- renderização do rodapé público sem links de conta/admin e renderização condicional de `Painel Administrativo` no chip apenas para staff/superuser
- renderização de botões sociais iconizados para Google, Facebook e X em login/cadastro, com rótulos acessíveis, rotas reais de OAuth e texto de aceite da política de uso
- login com lembrar acesso mantém sessão prolongada e login sem essa opção preserva expiração padrão
- prévia de cadastro seleciona mercado publicado não cancelado com mais visualizações, exclui `draft` e `canceled`, e usa mercado mais recente como desempate/fallback
- fluxo de cadastro com reCAPTCHA ausente, inválido e válido quando habilitado
- fluxo de cadastro com código de indicação válido, inválido e bônus desativado
- fluxo de edição de perfil na própria página autenticada
- regressão para `/profile/` renderizar dados reais de `gotrendlabs_user_profiles`, incluindo `display_name`, `bio`, `birth_date` e `sex`
- fluxo de edição de data de nascimento e sexo opcionais sem exposição no perfil público
- fluxo de exclusão lógica
- fluxo staff de listagem/detalhe administrativo de usuário
- detalhe administrativo exibe badges adquiridas sem recalcular elegibilidade na UI
- fluxo staff de desativação, reativação e revogação de sessões com auditoria
- fluxo superuser de promoção/rebaixamento de papéis administrativos com auditoria
- fluxo staff de marcação/desmarcação `is_bot` com filtro administrativo e auditoria, sem exposição pública
- fluxo staff/superuser de geração administrativa de link de reset com auditoria, bloqueio de autoação, bloqueio de alvo administrativo para staff comum e rejeição de conta desativada
- bloqueio de ações administrativas perigosas sobre a própria conta do operador
- permissão explícita de ajuste manual de wallet sobre a própria conta de operador com auditoria

## Critérios de aceite

- usuário consegue criar e acessar conta
- usuário consegue solicitar recuperação e definir nova senha com link válido
- usuário recebe link de recuperação por email sem que a resposta pública revele o link
- usuário recém-cadastrado consegue entrar em modo limitado e confirma email por link expirável para liberar ações sensíveis
- usuário consegue abrir a política de uso no cadastro sem sair do fluxo
- visitantes em login/cadastro/recuperação de senha conseguem voltar para a página chamadora local pelo `← Voltar`, com fallback para mercados/feed, alternar tema, acessar mercados, badges e ranking pela navegação pública e consultar links do rodapé público
- visitantes e usuários comuns não veem Admin Ops no rodapé nem no chip do usuário; staff e superusers veem `Painel Administrativo` no topo do chip autenticado com sinalização de acesso restrito
- visitantes em login/cadastro veem os provedores sociais iniciais como ícones acessíveis para Google, Facebook e X
- cadastro protegido exige conclusão do reCAPTCHA quando configurado
- cadastro com indicação válida credita somente o indicador em GT₵ educativa e não altera reputação do indicador nem do convidado
- sessão inválida é tratada corretamente
- idioma preferencial é respeitado após autenticação
- usuário autenticado consegue editar dados pessoais sem sair da tela de perfil
- nome editável do perfil vem de `gotrendlabs_user_profiles.display_name` e é sincronizado no update sem substituir dados reais por valores genéricos da sessão
- perfil público não expõe email, data de nascimento, sexo nem metadados privados do perfil
- conta desativada não consegue efetuar login
- staff consegue consultar usuários, abrir detalhe operacional e agir sobre status/sessões sem mutação local no Django
- superuser consegue alterar papel administrativo de outro usuário com nota operacional
- ações administrativas de usuário exigem nota, registram auditoria e preservam histórico
- ajuste manual de wallet no detalhe administrativo exige escolha explícita de direção, sem valor pré-selecionado
- staff/superuser consegue ajustar a própria wallet com justificativa auditada; demais ações sensíveis sobre a própria conta continuam bloqueadas
- marcador `bot` aparece e filtra apenas em Admin Ops
- staff consegue gerar link de reset para usuário comum ativo; superuser consegue gerar link para conta administrativa ativa; a confirmação do reset segue o fluxo público existente e revoga sessões somente ao definir a nova senha
- alteração de email exige nova confirmação antes de liberar ações sensíveis comuns

## Impacto de mudança

Mudanças nesta feature costumam afetar todas as experiências autenticadas e parte das comunicações.
