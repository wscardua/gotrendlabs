# Google Play 1.2.6+20 — faixa Novo por publicação

## Estado vigente

Entrega iniciada em 15/11/2026 a pedido do usuário para compilar e publicar a mudança mobile da PR #213. Versão 1.2.6+20 preparada em branch isolada `release/mobile-published-new-20261115`, base remota main `953c5a85be9c660332942311c2d5e879c348cf5e`. Preparação integrada pela PR #215; AAB oficial compilado e validado. Envio à Google ainda bloqueado pelo host de acesso ao navegador, mesmo após o usuário confirmar navegador aberto/logado e tentativas de conexão (incluindo reset e acesso direto). Alterações do checkout original preservadas.

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

Validação local em 15/11/2026: 141 testes Flutter aprovados (13 s); `flutter analyze --no-pub` sem issues (3,0 s); `git diff --check` aprovado. Assinatura/Firebase locais confirmados ignorados pelo Git. Logs: `/tmp/gtl-release20-tests.log` e `/tmp/gtl-release20-analyze.log`. Gate de origem e compilação oficial aprovados após integração. Não foram realizados testes de instalação pela Play, push ou MFA no novo artefato.

Acesso ao navegador indisponível nesta sessão: descoberta CUA retornou `browser access host is unavailable` e falha de inicialização do acesso nativo. Não há ferramenta Google Play dedicada disponível. O upload/consulta à Console dependem de restabelecer esse acesso; não afirmar publicação enquanto bloqueado.

## Arquitetura e MCP

Sem mudança funcional adicional, contrato/API, dependência, migration ou fronteira nova; ADR dispensada. Ferramentas, schemas/contratos, permissões, erros, replays e orientação editorial MCP não precisam mudar: esta release distribui apresentação de um timestamp já fornecido pela API. Nenhuma permissão inferida do Admin Ops. Sem mudança de configuração produtiva ou canal público da Play.

## Recibo de integração e compilação — 15/11/2026

- Aprovação da descrição/fluxo recebida do usuário antes da submissão; PR [#215](https://github.com/wscardua/gotrendlabs/pull/215), commit de preparação `8bceb13c6ed34623b901588656d727efac93015b`, merge/fonte `ec91cac25917ecfced9eb520dd49ccd1feac9774`.
- [CI da PR 43721331448](https://github.com/wscardua/gotrendlabs/actions/runs/43721331448) aprovado: 722 testes Python, três skips, 385,579 s, builds principal/MCP, OpenAPI e JavaScript aprovados.
- [Pipeline main 43722150278](https://github.com/wscardua/gotrendlabs/actions/runs/43722150278) aprovado: 722 testes/três skips, 362,287 s; builds/checks e deploy aprovados. SSM `dd17939b-d6e4-4db7-98b4-2172e8fba61a` Success/0. Leitura independente SSM `8a8b759f-7051-42dc-bb8a-4bb262302b36` Success/0 confirma commit fonte no servidor, seis serviços running e MCP healthy. Nenhum arquivo rastreado alterado; dez backups de ambiente não rastreados encontrados e preservados, sem consultar conteúdo.
- Gate `validateReleaseSource` confirmou HEAD igual à main remota atualizada e checkout limpo, sem exceções. Build `flutter build appbundle --release` concluído em 109,9 s.
- Arquivo: `/Users/williamsca/Downloads/GoTrendLabs/gotrendlabs-1.2.6-build20.aab`, 57.702.110 bytes, SHA256 `c9474145e0aea99c31a0efc4189e23b904852c4d77dbf49720a0926b83349e93`.
- Manifesto: `br.com.gotrendlabs.gotrendlabs_mobile`, versionName1.2.6/versionCode20, minSDK24/targetSDK36, permissões e 12 bibliotecas nativas iguais às da19. Sem perda de configuração pretendida; compatibilidade efetiva da Play não foi consultada nesta sessão.
- Bundletool oficial1.18.3 com checksum de distribuição conferido: validate aprovado; config PAGE_ALIGNMENT_16K e segmentos ELF64 >=16KB aprovados. jarsigner: jar verified. Certificado upload SHA256 `3B:54:9C:B7:58:24:73:32:D5:EC:1C:DD:55:22:D3:5F:B1:53:60:D2:40:BD:39:74:E4:C4:AC:1D:4E:2B:E0:5F`, igual ao AAB19.
- URLs produtivas confirmadas em libapp.so das três ABIs; URLs locais, keystore, key.properties e google-services.json ausentes do bundle. Arquivos JSON de recibo, checksum e notas estão junto ao AAB em Downloads/GoTrendLabs, fora do Git.
- Sem upload, revisão Google, aprovação, disponibilidade ou instalação pelo Play nesta etapa. Não houve nova versão no APK direto do site, política de build mínimo, track público, países/testadores ou permissões MCP.

## Impedimento e retomada

Compilação/integração concluídas; workflow bloqueado exclusivamente no envio à Google por `browser access host is unavailable` e falha do canal nativo. O usuário confirmou navegador aberto/logado; reset, descoberta e acesso direto não resolveram. Nenhum upload foi tentado. Nova tentativa depende de restabelecer o canal do Codex ao navegador, não de abrir outra conta nem trocar credenciais.

Smoke pós-deploy em 15/11/2026 às 11:13 de São Paulo: home/health/latest.json HTTP200, API status ok, manutenção mobile desativada. Headers1.2.6/build20 reconhecidos; update_required/update_available false, mínimo8 e APK direto1.0.7+8 preservados. Sem nova configuração de produção.

Ao retomar: conferir o maior versionCode e releases/drafts existentes no Play Console antes do upload; usar o AAB20/checksum acima apenas se não houver conflito, preservar Alpha/países/testadores, preencher notas e confirmar envio/estado real da Google. Não recriar o AAB de checkout com recibos locais divergindo da main; o artefato já validado tem origem imutável ec91cac. Sem atestar instalação, push/MFA ou aprovação enquanto não observados. Integrar o recibo final à main após confirmar o envio; esta atualização intermediária fica na branch de release e no registro da PR #215.

Evidência estruturada sanitizada: [JSON](mobile-new-publication-release-20-20261115.json). As seções de plano/preparação são históricas; este recibo prevalece.
