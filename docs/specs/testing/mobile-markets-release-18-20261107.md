# Google Play — mercados 1.2.4+18

Workflow WFLOW-20261107-MARKET-DISCOVERY-ANDROID-RELEASE. Usuário confirmou sucesso dos testes locais no Galaxy S20 e solicitou nova release Google Play. Canal existente Closed testing - Alpha confirmado na Console em07/11/2026:17(1.2.3), disponível aos testadores selecionados, sem rascunho novo observado. Próxima versão1.2.4+18.

## Origem e reconciliação

Preparação sobre origin/main b42162b5ed7519a2b277d1128c8485306ef2f14e. Contém descoberta/histórico da PR196 e navegação/faixa Novo da PR199; recibo web PR200. Release17 originou de78bb81e32c30e7f396c49d0f7f380cd0b7c488ad; MFA/resiliência/critério compacto daquela versão preservados na main. Nenhuma alteração funcional não integrada foi incorporada à release18.

Build AAB somente depois de integrar versão/build à main, com checkout limpo/fetch e gate validateReleaseSource, URLs produtivas https://gotrendlabs.com.br/api e https://gotrendlabs.com.br. Assinatura e Firebase existentes reutilizados por arquivos ignorados. Não usar app.localtest, bootstrap sem Firebase, fixtures ou URLs locais da build de teste físico.

## Validação e estado

Validação de preparação: 139 testes Flutter aprovados e flutter analyze --no-pub sem issues. Comparação com a origem da release17 mostra mudanças somente nos quatro arquivos Flutter de apresentação de mercados já integrados; autenticação, critérios, sessão, Firebase e cliente HTTP preservados. Preparação em andamento; AAB ainda não gerado/enviado. Registrar SHA da origem integrada, checksum, tamanho, certificado, metadados, compatibilidade e estado da Console após execução. Teste físico local confirmado pelo usuário comprova a UX sobre fixtures; não comprova instalação de release assinada pela Play nem entrega push/MFA produtiva.

## Notas pt-BR

Simplificamos a navegação dos mercados: abertos primeiro, apuração organizada e histórico preservado. Agora os mercados recentes recebem uma faixa NOVO. Melhoramos a consulta de favoritos e das suas previsões, inclusive em mercados selados.

## MCP e limites

Somente empacotamento/versão do consumidor Flutter integrado. Sem mudanças de ferramentas, schemas, contratos, permissões, erros, replays ou orientação editorial MCP; sem mudança de API/domínio/política mínima de build. APK direto do site preservado. Canal público de produção não integra esta entrega; disponibilidade depende da análise/publicação da Google.
