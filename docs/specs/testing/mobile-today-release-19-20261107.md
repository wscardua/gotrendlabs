# Hoje — fechamento e preparação Google Play 1.2.5+19

## Estado vigente

Implementação aprovada pelo usuário no emulador local. Preparação de commit/PR; integração, Actions produtivo, AAB e envio Alpha ainda pendentes. WFLOW-20261107-MOBILE-TODAY-PENDING. Não confundir build debug local com distribuição Google Play.

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
