---
id: FEAT-AUTH-001
titulo: "Autenticação e sessão"
versao: 0.1
status_spec: draft
status_impl: parcial
ultima_atualizacao: 2026-05-19
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
- login por credencial ou provedor social
- criação e validação de sessão
- logout
- recuperação de senha por token de uso único
- recuperação do contexto do usuário autenticado
- edição básica de perfil autenticado
- exclusão lógica de conta
- gestão administrativa de usuários cadastrados para suporte operacional

## Escopo excluído

- MFA
- SSO corporativo
- gestão avançada de dispositivos
- ajuste manual de reputação

## Fluxo do usuário

Usuário chega à interface pública, cria conta ou faz login, escolhe ou herda idioma preferencial e passa a acessar feed, perfil, wallet e ações autenticadas.

## Comportamento esperado

- sessões inválidas redirecionam para autenticação
- login social cria ou vincula conta de forma rastreável
- idioma preferencial acompanha a sessão
- cadastro sem aceite da política de uso é rejeitado
- link da política de uso no cadastro abre resumo em modal sem perder o formulário e mantém acesso à página completa
- telas de login, cadastro e recuperação de senha mantêm navegação pública para feed/mercados, badges e ranking, alternância de tema, rodapé público e retorno compacto `← Feed` no primeiro painel de conteúdo
- login pode prolongar a sessão no dispositivo quando o usuário marca a opção de lembrar acesso, sem salvar senha no navegador
- login oferece recuperação de senha por email; em desenvolvimento local o link pode ser exposto na UI para validação sem SMTP real
- tela de cadastro pode exibir prévia não personalizada do produto usando mercado público real como exemplo de ticket
- cadastro sem reCAPTCHA válido é rejeitado quando a proteção estiver habilitada
- perfil autenticado exibe reputação em cards e mantém edição de dados na própria tela de perfil, sem rota separada
- `birth_date`, `sex`, email e bio são privados ao usuário autenticado e não aparecem no perfil público
- exclusão lógica desativa login e sessões sem apagar dados físicos
- Admin Ops lista usuários, abre detalhe operacional amplo e exibe badges adquiridas para suporte
- ações administrativas de usuário usam contratos staff da FastAPI; o Django apenas renderiza estado e envia formulários

## Regras de domínio

- um usuário deve possuir identidade única no domínio
- cada sessão precisa ser validável e revogável
- login social não pode gerar duplicidade silenciosa de contas
- aceite de política de uso deve guardar data e versão aceita
- reCAPTCHA protege criação de conta contra abuso automatizado sem substituir validações de identidade, senha e aceite
- exclusão lógica deve preservar histórico e bloquear uso normal
- ações administrativas sobre conta exigem usuário staff, nota operacional e auditoria
- operador não pode desativar, revogar sessões ou ajustar wallet da própria conta
- alteração de `is_staff` e `is_superuser` exige operador `is_superuser=true`, nota operacional e auditoria
- operador não pode alterar privilégios da própria conta; `is_superuser=true` implica `is_staff=true`
- sistema não permite remover o último superusuário ativo
- gestão administrativa não permite alterar reputação manualmente nesta fatia

## Responsabilidades por camada

- `frontend-web`: formulários, telas, redirecionamento e mensagens localizadas
- `backend-api`: autenticação, sessão, vínculo de provedor, política de acesso e contratos staff de suporte a usuários
- `database`: usuário, credenciais externas, sessão e preferências
- `communications`: email de boas-vindas e fluxos transacionais futuros

## Dados e persistência

- usuário
- perfil básico
- data de nascimento e sexo opcionais no perfil privado/editável (`birth_date` em `YYYY-MM-DD`; `sex` como `male`, `female`, `other` ou `prefer_not_to_say`)
- provedores externos vinculados
- preferência de idioma
- sessões e rastros de autenticação
- tokens de recuperação de senha com hash, expiração e uso único
- aceite de política de uso
- estado da conta e timestamps de exclusão lógica

## Contratos afetados

- `i18n-content.md`
- `domain-events.md`

## I18n e conteúdo

- mensagens de erro e sucesso precisam existir em `pt-BR` e `en`
- idioma preferencial deve ser persistido

## Observabilidade e operação

- registrar falhas de login e origem de autenticação
- disponibilizar trilha mínima para suporte
- Admin Ops deve permitir listagem, busca, detalhe amplo, badges adquiridas, desativação/reativação, revogação de sessões e gestão controlada de papéis via contratos staff
- ações administrativas de conta devem registrar `user.deactivate`, `user.reactivate`, `user.sessions_revoke`, `user.wallet_adjust` ou `user.roles_update` em `orynth_admin_events`
- contratos staff mínimos: `GET /admin/users`, `GET /admin/users/{user_id}`, `POST /admin/users/{user_id}/deactivate`, `POST /admin/users/{user_id}/reactivate`, `POST /admin/users/{user_id}/sessions/revoke`, `POST /admin/users/{user_id}/roles`

## Testes esperados

- unitários para vínculo e validação de sessão
- integração para login social e persistência de preferência de idioma
- fluxo de cadastro, login e logout
- fluxo de recuperação de senha com solicitação, token válido, token inválido/expirado e token reutilizado
- fluxo de aceite obrigatório da política de uso
- renderização de política de uso pública e modal de política no cadastro
- renderização de navegação pública, alternância de tema, rodapé público e retorno compacto `← Feed` em login/cadastro/recuperação de senha
- login com lembrar acesso mantém sessão prolongada e login sem essa opção preserva expiração padrão
- prévia de cadastro seleciona mercado publicado não cancelado com mais visualizações, exclui `draft` e `canceled`, e usa mercado mais recente como desempate/fallback
- fluxo de cadastro com reCAPTCHA ausente, inválido e válido quando habilitado
- fluxo de edição de perfil na própria página autenticada
- fluxo de edição de data de nascimento e sexo opcionais sem exposição no perfil público
- fluxo de exclusão lógica
- fluxo staff de listagem/detalhe administrativo de usuário
- detalhe administrativo exibe badges adquiridas sem recalcular elegibilidade na UI
- fluxo staff de desativação, reativação e revogação de sessões com auditoria
- fluxo superuser de promoção/rebaixamento de papéis administrativos com auditoria
- bloqueio de ações administrativas perigosas sobre a própria conta do operador

## Critérios de aceite

- usuário consegue criar e acessar conta
- usuário consegue solicitar recuperação e definir nova senha com link válido
- usuário consegue abrir a política de uso no cadastro sem sair do fluxo
- visitantes em login/cadastro/recuperação de senha conseguem voltar para mercados pelo `← Feed`, alternar tema, acessar mercados, badges e ranking pela navegação pública e consultar links do rodapé público
- cadastro protegido exige conclusão do reCAPTCHA quando configurado
- sessão inválida é tratada corretamente
- idioma preferencial é respeitado após autenticação
- usuário autenticado consegue editar dados pessoais sem sair da tela de perfil
- perfil público não expõe email, data de nascimento, sexo nem metadados privados do perfil
- conta desativada não consegue efetuar login
- staff consegue consultar usuários, abrir detalhe operacional e agir sobre status/sessões sem mutação local no Django
- superuser consegue alterar papel administrativo de outro usuário com nota operacional
- ações administrativas de usuário exigem nota, registram auditoria e preservam histórico
- ajuste manual de wallet no detalhe administrativo exige escolha explícita de direção, sem valor pré-selecionado

## Impacto de mudança

Mudanças nesta feature costumam afetar todas as experiências autenticadas e parte das comunicações.
