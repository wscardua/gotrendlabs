# Google Play 1.2.6+20 — faixa Novo por publicação

## Estado vigente

Preparação local iniciada em 15/11/2026 a pedido do usuário para compilar e publicar a mudança mobile da PR #213. Versão 1.2.6+20 preparada em branch isolada `release/mobile-published-new-20261115`, base remota main `953c5a85be9c660332942311c2d5e879c348cf5e`. Sem AAB oficial, integração ou envio à Google nesta etapa. Alterações do checkout original preservadas.

## Escopo e reconciliação

A faixa Novo considera `published_at <= agora < published_at + 48h`, somente para open, sem fallback para criação, com expiração automática. A melhoria editorial do Analyst já funciona no backend e não exige código adicional no app.

Comparação da main com a origem do AAB19 (`f7d6480645f84d5cbcffa3a67a2d1f206ba00b6e`): somente modelo/provider de novidade, testes de cards/telas e README mobile mudaram. Assinatura, Firebase, Android, dependências, autenticação/MFA, Hoje e restante da navegação permanecem iguais. A versão 1.2.5+19 foi enviada ao Alpha conforme recibo anterior; aprovação/disponibilidade atual ainda exigem consulta ao Play Console. Não reutilizar versionCode19.

## Release planejada

- Integrar versão/build e esta preparação à main por PR em português, após aprovação da descrição conforme instrução anterior do usuário.
- Acompanhar CI e eventual deploy automático da main, sem alterar o workflow existente.
- Gerar AAB assinado com gate `validateReleaseSource`, checkout limpo e HEAD igual à main remota atualizada. Sem bypass, versão por override ou artefato originado da árvore suja.
- URLs produtivas: `https://gotrendlabs.com.br/api` e `https://gotrendlabs.com.br`; assinatura/Firebase existentes copiados como arquivos locais ignorados, sem segredos no Git.
- Verificar manifesto, assinatura, SHA256/tamanho e compatibilidade do AAB; registrar commit fonte completo após merge.
- Enviar ao mesmo Closed testing Alpha, preservando países/testadores, APK direto do site e política de build mínimo. Conferir ausência de versão superior/draft conflitante antes do upload.
- Registrar exatamente o estado retornado pela Google; revisão não equivale a disponibilidade ou instalação.

## Notas propostas pt-BR

A faixa Novo agora considera as primeiras 48 horas após a publicação do mercado, mesmo quando o rascunho foi criado antes. O indicador desaparece automaticamente ao terminar esse período.

## Validação e limitações

Validação local em 15/11/2026: 141 testes Flutter aprovados (13 s); `flutter analyze --no-pub` sem issues (3,0 s); `git diff --check` aprovado. Assinatura/Firebase locais confirmados ignorados pelo Git. Logs: `/tmp/gtl-release20-tests.log` e `/tmp/gtl-release20-analyze.log`. O gate de origem e a compilação oficial só podem passar após integração. Não foram realizados testes de instalação pela Play, push ou MFA no novo artefato.

Acesso ao navegador indisponível nesta sessão: descoberta CUA retornou `browser access host is unavailable` e falha de inicialização do acesso nativo. Não há ferramenta Google Play dedicada disponível. O upload/consulta à Console dependem de restabelecer esse acesso; não afirmar publicação enquanto bloqueado.

## Arquitetura e MCP

Sem mudança funcional adicional, contrato/API, dependência, migration ou fronteira nova; ADR dispensada. Ferramentas, schemas/contratos, permissões, erros, replays e orientação editorial MCP não precisam mudar: esta release distribui apresentação de um timestamp já fornecido pela API. Nenhuma permissão inferida do Admin Ops. Sem mudança de configuração produtiva ou canal público da Play.
