# Release Google Play 1.2.3+17 — 06/11/2026

## Preparação

Solicitação do usuário: compilar e enviar uma nova release à Google Play Console já aberta/logada. Canal existente confirmado na UI: Closed testing - Alpha; versão ativa 1.2.2+16. Próxima versão/build: 1.2.3+17. Nenhum rollout público de produção faz parte desta entrega.

Código-base: origin/main 30c6bec antes da preparação. Versão/build integrados pela PR #194 antes de compilar. Origem do AAB: `78bb81e32c30e7f396c49d0f7f380cd0b7c488ad`, checkout limpo de origin/main, confirmado pelo gate durante o build. URLs de compilação: `GTL_API_BASE_URL=https://gotrendlabs.com.br/api`, `GTL_PUBLIC_WEB_BASE_URL=https://gotrendlabs.com.br`. Assinatura e Firebase da release16 reutilizados via arquivos locais ignorados, sem expor segredos.

Validação local: flutter analyze --no-pub limpo; flutter test --no-pub com 129 testes aprovados. Contém MFA da PR #191 e preserva resiliência da #188. ResolutionCriteriaText e seus quatro testes foram comparados byte a byte com o worktree mobile-login-fix: idênticos e já integrados desde caee7aa (17/10); a pendência anterior de ausência desse componente foi corrigida, sem alteração de UI.

## Notas de versão pt-BR

Corrigimos o acesso de contas administrativas com verificação em duas etapas. Agora é possível confirmar o login pelo autenticador ou por código de recuperação. Mantivemos as melhorias de estabilidade e a leitura completa dos critérios de resolução.

## Resultado

PR #194 integrada após CI aprovado (681 testes/3 skips). Flutter compilou AAB release em 86,5 s, com assinatura verificada por jarsigner e bundle validado por bundletool 1.18.3.

- Artefato local: `/Users/williamsca/Downloads/GoTrendLabs/gotrendlabs-1.2.3-build17.aab`.
- Origem: `78bb81e32c30e7f396c49d0f7f380cd0b7c488ad`.
- SHA-256: `4b692b316a263c44e325c20d16253647881b63748416e40414acdb1597b42efc`.
- Tamanho: `57664916` bytes.
- Certificado SHA-256: `3B:54:9C:B7:58:24:73:32:D5:EC:1C:DD:55:22:D3:5F:B1:53:60:D2:40:BD:39:74:E4:C4:AC:1D:4E:2B:E0:5F`, idêntico ao build16.
- Metadados: package br.com.gotrendlabs.gotrendlabs_mobile, versionCode17, versionName1.2.3, minSDK24, targetSDK36.
- Compatibilidade: PAGE_ALIGNMENT_16K e 12 bibliotecas ELF com PT_LOAD de pelo menos16KB; permissões e lista de bibliotecas iguais ao build16. URL produtiva presente em libapp.so, URL padrão local ausente. Sem keystore/env no AAB.
- Sidecars locais: checksum, receipt.json e release notes no mesmo diretório; nenhum segredo incluído.

A Google aceitou o AAB17 e confirmou metadados versionCode17/versionName1.2.3, API24+, targetSDK36, quatro screen layouts e três ABIs. Prévia: 12.619 telefones e 6.829 tablets preservados, zero dispositivos perdidos em todos os form factors apresentados. Notas pt-BR conferidas; rollout100% somente para o grupo existente de Closed testing - Alpha, sem alterar países/testadores.

Envio confirmado na Publishing overview: “Changes in review”, item Closed testing - Alpha, 17(1.2.3), Start full rollout. Managed publishing off preservado. No momento da observação, quick checks automáticos ainda estavam em andamento (até13min indicados), com aviso de envio à revisão após sucesso. Isso comprova solicitação de envio, sem atestar aprovação/disponibilidade final da Google. A release anterior ativa16 foi preservada enquanto a nova passa pela plataforma.

MCP sem ajustes: ferramentas, schemas, contratos, permissões, erros, replays e orientação editorial preservados. Sem mudança de API/backend/web nem política mínima de build. Smoke com conta administrativa real no artefato novo só será declarado se executado.

## CI/deploy e fechamento

- Preparação integrada pela [PR #194](https://github.com/wscardua/gotrendlabs/pull/194), origem do AAB78bb81e32c30e7f396c49d0f7f380cd0b7c488ad.
- [CI do PR](https://github.com/wscardua/gotrendlabs/actions/runs/42243550019): sucesso; 681 testes/3 skips, 427,803s.
- [Pipeline main](https://github.com/wscardua/gotrendlabs/actions/runs/42245109601): sucesso; 681 testes/3 skips, 440,240s; deploy SSM Success.
- Smoke público após deploy: GET/api/health HTTP200, status/api/database ok.
- Entrega autorizada concluída: compilação assinada e solicitação de envio da release17 à Google confirmadas. Aprovação/disponibilidade aos testadores e smoke humano MFA no app novo não são atestados. Não houve atualização do APK direto do site nem publicação pública de produção na Google Play.
