# Google Play 1.2.6+20 — faixa Novo por publicação

## Estado vigente

Entrega iniciada em 15/11/2026 a pedido do usuário para compilar e publicar a mudança mobile da PR #213. Versão 1.2.6+20 preparada em branch isolada `release/mobile-published-new-20261115`, base remota main `953c5a85be9c660332942311c2d5e879c348cf5e`. Preparação integrada pela PR #215; AAB oficial compilado e validado. AAB enviado ao teste fechado Alpha em 15/11/2026; Console confirmou Changes in review e 1 change sent for review. Quick checks em andamento; aprovação/disponibilidade ainda não confirmadas. O bloqueio de conexão anterior foi superado pelo acesso nativo ao Chrome. Alterações do checkout original preservadas.

## Escopo e reconciliação

A faixa Novo considera `published_at <= agora < published_at + 48h`, somente para open, sem fallback para criação, com expiração automática. A melhoria editorial do Analyst já funciona no backend e não exige código adicional no app.

Comparação da main com a origem do AAB19 (`f7d6480645f84d5cbcffa3a67a2d1f206ba00b6e`): somente modelo/provider de novidade, testes de cards/telas e README mobile mudaram. Assinatura, Firebase, Android, dependências, autenticação/MFA, Hoje e restante da navegação permanecem iguais. A versão 1.2.5+19 foi enviada ao Alpha conforme recibo anterior; a versão19 foi observada disponível aos testadores com full rollout antes deste envio. Não reutilizar versionCode19.

## Release planejada (histórico)

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

Histórico do bloqueio inicial: descoberta CUA retornou `browser access host is unavailable` e falha de inicialização do acesso nativo. Não há ferramenta Google Play dedicada disponível. Acesso nativo ao Chrome foi restabelecido na retomada; upload/envio confirmados no recibo abaixo. Não afirmar aprovação ou disponibilidade a partir desse envio.

## Arquitetura e MCP

Sem mudança funcional adicional, contrato/API, dependência, migration ou fronteira nova; ADR dispensada. Ferramentas, schemas/contratos, permissões, erros, replays e orientação editorial MCP não precisam mudar: esta release distribui apresentação de um timestamp já fornecido pela API. Nenhuma permissão inferida do Admin Ops. Sem mudança de configuração produtiva ou canal público da Play.

## Recibo de integração e compilação — 15/11/2026

- Aprovação da descrição/fluxo recebida do usuário antes da submissão; PR [#215](https://github.com/wscardua/gotrendlabs/pull/215), commit de preparação `8bceb13c6ed34623b901588656d727efac93015b`, merge/fonte `ec91cac25917ecfced9eb520dd49ccd1feac9774`.
- [CI da PR 43721331448](https://github.com/wscardua/gotrendlabs/actions/runs/43721331448) aprovado: 722 testes Python, três skips, 385,579 s, builds principal/MCP, OpenAPI e JavaScript aprovados.
- [Pipeline main 43722150278](https://github.com/wscardua/gotrendlabs/actions/runs/43722150278) aprovado: 722 testes/três skips, 362,287 s; builds/checks e deploy aprovados. SSM `dd17939b-d6e4-4db7-98b4-2172e8fba61a` Success/0. Leitura independente SSM `8a8b759f-7051-42dc-bb8a-4bb262302b36` Success/0 confirma commit fonte no servidor, seis serviços running e MCP healthy. Nenhum arquivo rastreado alterado; dez backups de ambiente não rastreados encontrados e preservados, sem consultar conteúdo.
- Gate `validateReleaseSource` confirmou HEAD igual à main remota atualizada e checkout limpo, sem exceções. Build `flutter build appbundle --release` concluído em 109,9 s.
- Arquivo: `/Users/williamsca/Downloads/GoTrendLabs/gotrendlabs-1.2.6-build20.aab`, 57.702.110 bytes, SHA256 `c9474145e0aea99c31a0efc4189e23b904852c4d77dbf49720a0926b83349e93`.
- Manifesto: `br.com.gotrendlabs.gotrendlabs_mobile`, versionName1.2.6/versionCode20, minSDK24/targetSDK36, permissões e 12 bibliotecas nativas iguais às da19. Prévia de compatibilidade da Play conferida no envio: zero dispositivos perdidos em todos os formatos exibidos.
- Bundletool oficial1.18.3 com checksum de distribuição conferido: validate aprovado; config PAGE_ALIGNMENT_16K e segmentos ELF64 >=16KB aprovados. jarsigner: jar verified. Certificado upload SHA256 `3B:54:9C:B7:58:24:73:32:D5:EC:1C:DD:55:22:D3:5F:B1:53:60:D2:40:BD:39:74:E4:C4:AC:1D:4E:2B:E0:5F`, igual ao AAB19.
- URLs produtivas confirmadas em libapp.so das três ABIs; URLs locais, keystore, key.properties e google-services.json ausentes do bundle. Arquivos JSON de recibo, checksum e notas estão junto ao AAB em Downloads/GoTrendLabs, fora do Git.
- Na etapa de compilação inicial ainda não havia upload; o envio posterior foi confirmado conforme recibo abaixo. Aprovação, disponibilidade e instalação pelo Play continuam sem confirmação. Não houve nova versão no APK direto do site, política de build mínimo, track público, países/testadores ou permissões MCP.

## Impedimento inicial e retomada (histórico)

Compilação/integração concluídas; workflow bloqueado exclusivamente no envio à Google por `browser access host is unavailable` e falha do canal nativo. O usuário confirmou navegador aberto/logado; reset, descoberta e acesso direto não resolveram. Nenhum upload foi tentado. Nova tentativa depende de restabelecer o canal do Codex ao navegador, não de abrir outra conta nem trocar credenciais.

Smoke pós-deploy em 15/11/2026 às 11:13 de São Paulo: home/health/latest.json HTTP200, API status ok, manutenção mobile desativada. Headers1.2.6/build20 reconhecidos; update_required/update_available false, mínimo8 e APK direto1.0.7+8 preservados. Sem nova configuração de produção.

Ao retomar: conferir o maior versionCode e releases/drafts existentes no Play Console antes do upload; usar o AAB20/checksum acima apenas se não houver conflito, preservar Alpha/países/testadores, preencher notas e confirmar envio/estado real da Google. Não recriar o AAB de checkout com recibos locais divergindo da main; o artefato já validado tem origem imutável ec91cac. Sem atestar instalação, push/MFA ou aprovação enquanto não observados. Integrar o recibo final à main após confirmar o envio; esta atualização intermediária fica na branch de release e no registro da PR #215.

Evidência estruturada sanitizada: [JSON](mobile-new-publication-release-20-20261115.json). As seções de plano/preparação são históricas; este recibo prevalece.

## Recibo de envio ao Google Play — fonte vigente

- Conexão ao computador restabelecida após novas tentativas autorizadas pelo usuário. Host de browser dedicado ainda indisponível, mas Google Chrome acessível pela automação nativa CUA, sem tecnologia alternativa nem troca de credenciais.
- Antes do envio: Alpha ativo com19(1.2.5), Available to testers on Google Play/Full rollout,178 países/regiões. Maior bundle exibido19, sem draft conflitante. Disponibilidade da19 confirmada nesta retomada, substituindo a pendência histórica do recibo19; instalação em dispositivo não inferida.
- Mesmo AAB20/checksum acima enviado e aceito, sem recompilação. Console:20(1.2.6), API24+, target36, quatro layouts, três ABIs. Prévia:12.619 telefones,6.859 tablets,7 TVs,0 wearables,30 carros,77 Chromebooks,2 AndroidXR; zero dispositivos que deixam de ser suportados.
- Notas pt-BR conferidas, nome automático20(1.2.6), rollout100% exclusivamente no Alpha existente. Países/regiões e testadores não editados; managed publishing off preservado. Sem track público, APK do site ou alteração de build mínimo.
- Confirmação observada em 15/11/2026 por volta de11:28 de São Paulo (14:28UTC): Publishing overview mostra Changes in review, Closed testing - Alpha,20(1.2.6), Start full rollout e mensagem 1 change sent for review. Quick checks em andamento, até14min indicados, com envio para revisão após sucesso. [Console](https://play.google.com/console/u/0/developers/5780321057759640239/app/4973661897857186052/publishing).
- Compilação e solicitação de envio concluídas. Aprovação, disponibilidade final e instalação via Google Play ainda dependem da plataforma/QA; não confundir Changes in review com release já disponível. Não foram repetidos testes de push/MFA no artefato instalado.
- Nenhum novo deploy/configuração produtiva para o upload. Fontes, hashes, CI/deploy, smoke e limitações mantidos neste recibo e no JSON. MCP inalterado em ferramentas/schemas/contratos/permissões/erros/replays/editorial; apenas distribuição de apresentação Flutter.
- Próxima ação externa: acompanhar decisão da Google e testar atualização instalada. Integrar este recibo documental à main com CI leve, sem novo deploy e preservando branch/checkout original.
