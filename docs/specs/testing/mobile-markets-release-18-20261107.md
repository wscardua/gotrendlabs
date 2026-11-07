# Google Play — mercados 1.2.4+18

Estado vigente: AAB assinado enviado à análise no Closed testing - Alpha; Console confirmou Changes in review, com quick checks ainda em andamento. CI/deploy da origem concluídos. Aprovação/disponibilidade final da Google não observadas. As seções de preparação abaixo são históricas.

Workflow WFLOW-20261107-MARKET-DISCOVERY-ANDROID-RELEASE. Usuário confirmou sucesso dos testes locais no Galaxy S20 e solicitou nova release Google Play. Canal existente Closed testing - Alpha confirmado na Console em 07/11/2026:17(1.2.3), disponível aos testadores selecionados, sem rascunho novo observado. Próxima versão 1.2.4+18.

## Origem e reconciliação

Preparação sobre origin/main b42162b5ed7519a2b277d1128c8485306ef2f14e. Contém descoberta/histórico da PR196 e navegação/faixa Novo da PR199; recibo web PR200. Release17 originou de 78bb81e32c30e7f396c49d0f7f380cd0b7c488ad; MFA/resiliência/critério compacto daquela versão preservados na main. Nenhuma alteração funcional não integrada foi incorporada à release18.

Build AAB somente depois de integrar versão/build à main, com checkout limpo/fetch e gate validateReleaseSource, URLs produtivas https://gotrendlabs.com.br/api e https://gotrendlabs.com.br. Assinatura e Firebase existentes reutilizados por arquivos ignorados. Não usar app.localtest, bootstrap sem Firebase, fixtures ou URLs locais da build de teste físico.

## Validação e estado da preparação histórica

Validação de preparação: 139 testes Flutter aprovados e flutter analyze --no-pub sem issues. Comparação com a origem da release17 mostra mudanças somente nos quatro arquivos Flutter de apresentação de mercados já integrados; autenticação, critérios, sessão, Firebase e cliente HTTP preservados. Preparação em andamento; AAB ainda não gerado/enviado. Registrar SHA da origem integrada, checksum, tamanho, certificado, metadados, compatibilidade e estado da Console após execução. Teste físico local confirmado pelo usuário comprova a UX sobre fixtures; não comprova instalação de release assinada pela Play nem entrega push/MFA produtiva.

## Notas pt-BR

Simplificamos a navegação dos mercados: abertos primeiro, apuração organizada e histórico preservado. Agora os mercados recentes recebem uma faixa NOVO. Melhoramos a consulta de favoritos e das suas previsões, inclusive em mercados selados.

## MCP e limites

Somente empacotamento/versão do consumidor Flutter integrado. Sem mudanças de ferramentas, schemas, contratos, permissões, erros, replays ou orientação editorial MCP; sem mudança de API/domínio/política mínima de build. APK direto do site preservado. Canal público de produção não integra esta entrega; disponibilidade depende da análise/publicação da Google.

## Resultado do build e envio — 07/11/2026

Versão/build integrada pela [PR #201](https://github.com/wscardua/gotrendlabs/pull/201), CI [42398795564](https://github.com/wscardua/gotrendlabs/actions/runs/42398795564) aprovado: 681 testes Python/três skips/623,054s, imagens/OpenAPI/JS aprovados. Origem AAB `f854f531f92d00147a3ac3d4770a1f4f8c01c62d`, checkout limpo e gate de fetch/main confirmado no Gradle. Build release em 96,2 s.

- Artefato: `/Users/williamsca/Downloads/GoTrendLabs/gotrendlabs-1.2.4-build18.aab`.
- SHA256: `45b70f5d8364636febc0618b3c892401f483a6e4511254c9636851b5bedd52ba`.
- Tamanho: 57.681.979 bytes; recibo/checksum/notas locais no mesmo diretório.
- Certificado SHA256: `3B:54:9C:B7:58:24:73:32:D5:EC:1C:DD:55:22:D3:5F:B1:53:60:D2:40:BD:39:74:E4:C4:AC:1D:4E:2B:E0:5F`, igual à release17. Jarsigner verified; avisos de chave autoassinada de upload são esperados.
- Bundletool validate aprovado; pacote oficial br.com.gotrendlabs.gotrendlabs_mobile, versionCode 18 / versionName 1.2.4, min SDK 24 / target SDK 36. PAGE_ALIGNMENT_16K e 12 bibliotecas ELF com PT_LOAD mínimo de 16 KB. Permissões e lista de bibliotecas iguais aos do build 17; URLs produtivas presentes, locais ausentes; sem chaves/env no bundle.

Play Console aceitou o arquivo nomeado e confirmou 18 (1.2.4), API 24+, target SDK 36, quatro layouts/três ABIs, Supports 16 KB. Compatibilidade comparada à release 17 atual: 12.611 telefones/6.829 tablets, zero perda em todos os form factors apresentados. Notas pt-BR conferidas; rollout de 100% exclusivamente no grupo existente de Closed testing - Alpha, países/testadores preservados. Não alterar política mínima de build ou APK do site.

Publishing overview após Send changes for review: Changes in review, Closed testing - Alpha 18 (1.2.4), Start full rollout. Managed publishing off preservado. Quick checks ainda em andamento, até 14 min indicados; mudanças seguem para análise quando aprovadas essas verificações. A solicitação de publicação foi concluída; aprovação/disponibilidade final da Google e instalação do pacote assinado pela Play não são atestadas por este recibo. Não confundir o sucesso do QA físico local com validação do binário distribuído pela Play.

Actions main [42399910630](https://github.com/wscardua/gotrendlabs/actions/runs/42399910630) concluído com sucesso: 681 testes Python, três skips, sem falhas (408,231s); deploy SSM Success. Smoke após deploy: /api/health 200/status ok/API e database ok; /app/android/latest.json 200 preserva APK direto 1.0.7. Nenhuma política mínima de build alterada.

Última conferência da Console nesta execução: Changes in review; quick checks 47%, até sete minutos restantes indicados. Isso é progresso de verificações automáticas, não aprovação nem publicação disponível aos testadores. Managed publishing off e rollout Alpha 100% permanecem configurados.
