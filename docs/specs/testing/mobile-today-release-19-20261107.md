# Hoje — fechamento e preparação Google Play 1.2.5+19

## Estado vigente

Implementação aprovada pelo usuário no emulador local e integrada pela PR #203. CI/deploy concluídos; AAB 1.2.5+19 assinado e enviado ao Alpha. Console confirmou Changes in review com quick checks ainda em andamento. Aprovação, disponibilidade e instalação pelo Google Play ainda não confirmadas. As seções de preparação abaixo são históricas. WFLOW-20261107-MOBILE-TODAY-PENDING. Não confundir build debug local com distribuição Google Play.

## Comportamento final

Ordem: Para prever (um hero aberto), Tendências (até dois outros destaques abertos), Mais mercados (até oito outros abertos) e Em apuração (todos os locked retornados pela API). As seções de oportunidades precedem acompanhamento. EngagementScore e desempate por título dos abertos preservados. Locked segue close_at programado decrescente; datas ausentes por último, empates pela ordem original. A data não representa instante real de transição de estado.

Apuração não é recolhida nem limitada a três; não há CTA Ver todos ou recorte auxiliar novo. Sem open, apuração permanece disponível; vazios independentes. Resolved/sealed/draft/canceled não entram em Hoje. Favoritos, histórico, detalhe e integridade permanecem nas experiências existentes. Sem alteração na lista Mercados, além da extração de helper de ordenação para reutilização.

## Origem e reconciliação

Base ee697d073e0d3ca362c98f48b905f51d1f06f1c8, confirmada por fetch. Branch feature/mobile-today-pending em worktree isolada. Comparação com origem do AAB18 (f854f531f92d00147a3ac3d4770a1f4f8c01c62d) mostra apenas markets_screen.dart, seus testes, README e pubspec alterados no mobile. MFA, Firebase, autenticação, sessão, URLs padrão, cards e demais comportamentos distribuídos preservados. Nenhuma customização localtest ou fixture incorporada.

## Validação

- Aceite manual do usuário no emulador Android 16, API DEV em 10.0.2.2:8001.
- 16 testes selecionados de mercados/shell e analyze aprovados no último ajuste; APK debug arm64 compilado/instalado com todos os locked e sem CTA.
- Fechamento reforça teste observável de ordem: quatro open e locked, comprovando Mais mercados antes de apuração; fixture de quatro locked comprova ausência do limite, empate, datas ausentes e exclusão dos demais estados.
- Suíte completa de fechamento: 140 testes Flutter aprovados; flutter analyze --no-pub sem problemas (2,8s); git diff --check aprovado. Logs locais /tmp/gtl-today-close-tests.log e /tmp/gtl-today-close-analyze.log.
- API, OpenAPI, web e MCP sem mudanças. Ferramentas, schemas, contratos, permissões, erros, replays e orientação editorial não precisam de ajustes, pois o app só apresenta status efetivo/timestamps existentes. Sem inferência de poderes Admin Ops.
- Nenhuma nova fronteira/ADR, migration ou configuração PRD necessária. Teste de push, MFA e instalação pela Play não foi repetido nesta fatia de apresentação.

## Publicação planejada

Título/descrição da PR em português aguardam autorização explícita. Depois: CI, merge, acompanhamento Actions/SSM e smoke de health. Workflow atual trata apps/** como produtivo, mas não compila/publica Android; deploy web não ativa a feature nos aparelhos.

Versão 1.2.5+19 deve integrar main antes do AAB. Gerar de checkout limpo e HEAD igual a origin/main após fetch, com gate validateReleaseSource, URLs produtivas, Firebase e assinatura existentes. Canal proposto: Closed testing Alpha existente, sem alterar países/testadores, track público, APK do site ou política de build mínimo. Registrar commit completo, SHA256, certificado, manifesto, tamanho e compatibilidade no envio. Disponibilidade só deve ser afirmada após confirmação da Google.

## Notas propostas pt-BR

A tela Hoje agora prioriza os mercados abertos para você prever. Ao final, acompanhe todos os mercados em apuração, com previsões encerradas e resultados ainda pendentes.

## Recibo de integração, deploy e envio — 07/11/2026

- PR [#203](https://github.com/wscardua/gotrendlabs/pull/203), head bd8783df38c4af7e2ced00cdc72786165d834669; merge/source f7d6480645f84d5cbcffa3a67a2d1f206ba00b6e.
- CI PR [42407114320](https://github.com/wscardua/gotrendlabs/actions/runs/42407114320): sucesso, 681 testes Python, três skips, 313,544s; imagens, OpenAPI e testes JS aprovados.
- Actions main/deploy [42407705220](https://github.com/wscardua/gotrendlabs/actions/runs/42407705220): sucesso, 681 testes, três skips, 432,996s. SSM 7214ca49-1f1c-411a-af9a-a489b0d87f06 confirmado Success via AWS MCP. API health HTTP200/status ok após deploy. APK do site permanece 1.0.7+8.
- Gate validateReleaseSource confirmou source acima, checkout limpo e origin/main atualizado. Build AAB release 65,3s, URLs https://gotrendlabs.com.br/api e https://gotrendlabs.com.br; Firebase e assinatura existentes via arquivos ignorados.
- Arquivo local: /Users/williamsca/Downloads/GoTrendLabs/gotrendlabs-1.2.5-build19.aab; tamanho 57.702.325 bytes.
- SHA256: 6464300383d4845aba324958cd049ef8292b334e9c117bdd05b313cbd0f5b5be.
- Certificado upload SHA256: 3B:54:9C:B7:58:24:73:32:D5:EC:1C:DD:55:22:D3:5F:B1:53:60:D2:40:BD:39:74:E4:C4:AC:1D:4E:2B:E0:5F; igual à release18. jarsigner: jar verified.
- bundletool validate aprovado; package br.com.gotrendlabs.gotrendlabs_mobile, versionCode19/versionName1.2.5, minSDK24/target36, permissões e 12 bibliotecas nativas iguais às da18. Alinhamento de páginas/ELF de 16KB validado. URLs locais e arquivos de segredo ausentes no bundle.
- Play Console aceitou o AAB; preview reportou zero perda de compatibilidade em todos os formatos, 12.611 telefones e 6.829 tablets. Nome 19 (1.2.5), notas pt-BR acima, rollout 100% do grupo Alpha existente. Países/testadores e managed publishing off preservados; nenhum envio ao track público.
- Envio confirmado em Publishing overview: Changes in review, Closed testing Alpha, 19 (1.2.5), Start full rollout. Última observação: quick checks em andamento (0%, até 14min). Não equivale a aprovação ou disponibilidade final.
- Release18 foi observada disponível aos testadores selecionados antes deste envio. O teste local/aceite do usuário não comprova instalação da19 pela Play; não foi executado novo smoke de MFA/push no artefato distribuído.
- Nenhuma migration/configuração de produção ou alteração MCP necessária. Branch de implementação e worktrees locais preservados. Próxima pendência externa: aprovação/disponibilidade da Google e teste da atualização instalada.
