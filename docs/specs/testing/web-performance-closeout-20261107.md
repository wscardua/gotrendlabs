# Fechamento — Desempenho web

## Estado atual

Preparação de fechamento em 07/11/2026, branch `feature/web-performance`, baseada em `origin/main` `92f43fdd227c80374a299d75465a044358360b3d`. Implementação testada localmente e preparada para commit; PR, integração e implantação ainda pendentes. Este recibo consolida o estado final e prevalece sobre os registros históricos das prévias e reversões no [aceite local](web-performance-acceptance-20261107.md).

O usuário autorizou o fluxo commit → PR → merge → acompanhamento do GitHub Actions/produção, com **aprovação prévia do título e descrição antes da abertura da PR**. Branch local e alterações do checkout original devem ser preservadas.

## Fontes da verdade e comportamento final

- [FEAT-REP-001 v0.8](../features/reputation-and-ranking.md): nova página autenticada `/desempenho/`, menu imediatamente após Perfil e badges e atalho no perfil. A feature ampla permanece parcial/draft por escopos independentes.
- [Contrato de reputação](../contracts/reputation-ranking.md): Django consome `GET /users/me/performance` existente com token da própria sessão, a cada requisição. Sem query de identidade, cache compartilhado, fallback ORM ou cálculo de domínio.
- [Arquitetura web](../architecture/frontend-web.md): seis indicadores, histórico de até dez resoluções, conquistas recentes com imagens compartilhadas com o perfil, links por slug, perfil#badges e ranking. Staff/superuser preservam a ocultação administrativa do placar; bots usam o agregado real, sem posição inventada.
- Cinco resoluções iniciais; Carregar mais revela as restantes da mesma resposta, sem rede/paginação remota. Contador acessível e foco no primeiro link revelado; sem JS, todas as resoluções ficam disponíveis.
- Gráfico compacto de impactos individuais de reputação em ordem cronológica. Altura proporcional é transformação visual; valores/resultado/GT₵ vêm da API. Não representa score acumulado nem evolução temporal completa.
- Cabeçalho/placar integrados, tabela desktop e cards móveis, dois temas, imagens reais de badges e tipografia consistente com Carteira educativa. Experimentos de atalhos/identidade rejeitados pelo usuário foram revertidos.
- Vazio orienta exploração; API indisponível gera estado explícito/503 e retry; 403 mantém restrição; 401 limpa sessão e retorna ao login. Informações ausentes não viram métricas fictícias.

## Validação de fechamento

- Quinze testes específicos Django aprovados: autenticação/visitante/sessão inválida, 403/503, menu/papéis, dados, vazios, links, isolamento por token, escape HTML, contrato e gráfico.
- `manage.py check`, OpenAPI `--check` (snapshot inalterado), quatro scripts JavaScript existentes do CI, sintaxe JavaScript e `git diff --check` aprovados.
- `collectstatic --noinput`: 199 arquivos presentes (2 copiados, 197 preservados).
- Dockerfile `docker build --check .` sem avisos; imagem MCP construída com sucesso (`sha256:e471608e1a0a27e1b3559b9f3e02f40ef7acfdbb632a293a32a484797db2450e`).
- QA reproduzível `tests/performance_preview.py` + `tests/test_performance_browser.js`: 30 combinações (1440/1024/768/390/320 × dados/vazio/erro × claro/escuro), gráfico e labels acessíveis, imagens temáticas, foco/teclado, revelação 5→10 sem rede, contador e leitura sem JS aprovados. Fixture de navegador agora inclui o gráfico final, antes coberto somente pelos testes Django e sessão real.
- QA autenticado da conta DEV existente: dez combinações de largura/tema, dez impactos (três negativos), dez resoluções e cinco imagens reais de badges. Sem overflow. Capturas desktop claro/celular escuro inspecionadas visualmente.
- Comparação computed styles com Carteira: mesma família IBM Plex Sans, tamanhos/pesos/spacing/line-height nos seis seletores principais.
- Suíte Python completa em PostgreSQL 16 efêmero/tmpfs na porta 55439: **698 testes executados em 288,199 s, OK (3 skips)**. Discovery anunciou 701; o resumo do runner registra 698. Banco DEV preservado; container temporário removido após a execução.

Venv Python 3.11 existente reutilizado; nenhuma reinstalação ou alteração da venv principal. O [aceite local](web-performance-acceptance-20261107.md) conserva os resultados anteriores e suas limitações.

Reexecutado o build principal em 07/11: Docker local continua sem espaço para o apt. Nenhuma imagem/volume do usuário foi removida. Esse bloqueio ambiental não será tratado como build aprovado: o CI da PR precisa construir a imagem com sucesso antes de permitir merge.

## Arquitetura, MCP e mobile

MCP não precisa de ajustes em ferramentas, schemas, contratos, autenticação, permissões, erros, replays ou orientação editorial: a mudança cria somente um consumidor Django do agregado existente. Nenhuma permissão MCP é inferida de ações humanas do Admin Ops. Não há mudança de regra de reputação, ranking, resultado educativo, badges ou persistência; nenhum ADR/migration necessário.

Mobile não impactado: `apps/mobile/lib/src/features/performance/` permanece consumindo o mesmo `GET /users/me/performance`, sem alteração de payload/OpenAPI, sessão ou regras. Esta entrega web não distribui APK/AAB/iOS.

## Integração e ativação previstas

1. Commitar a implementação e documentação na branch preservada; revisar o intervalo completo contra a main remota.
2. Mostrar título/descrição da PR em português e aguardar a aprovação solicitada pelo usuário.
3. Publicar a branch e abrir PR pelo MCP GitHub; acompanhar os checks completos e corrigir falhas antes do merge.
4. Integrar na main após CI aprovado e acompanhar o workflow `GoTrendLabs CI and Deploy` da main. Variáveis conferidas: `ENABLE_PROD_DEPLOY=1`, `DEPLOY_BRANCH=main`.
5. Conferir commit produtivo, saúde e assets publicados; validar visitante, autenticação quando houver sessão autorizada disponível, navegação e temas. Registrar precisamente qualquer limite de acesso produtivo.
6. Registrar PR, commit de merge, runs/SSM e smoke neste recibo e na memória operacional, por atualização documental própria se necessária.

**Não são necessárias migrations, flags, ajustes de banco ou configuração adicional para ativar esta página.** O deploy existente publica templates e executa collectstatic. Contas, mercados, senhas e vínculos de imagens gerados para avaliação DEV ficam locais; não devem ser transportados para produção.

## Limites

QA de navegador em Chrome com viewports móveis; Safari/Firefox e aparelho físico não exercitados. Mockup anexado indisponível na conversa. Traduções completas seguem a iniciativa i18n existente; novos textos usam seus marcadores Django. Implantação e smoke produtivo ainda não observados nesta etapa.

### Base produtiva anterior

Conferidos o recibo da entrega web anterior e os workflows: PR205/commit `4b9b8a5` implantada com sucesso (Actions42418237208); main atual `92f43fd` teve CI aprovado (Actions42419595024) com deploy corretamente ignorado por ser docs-only. A diferença entre esses commits não contém alterações em apps/ops/config/packages/.github. Não há artefato mobile nesta entrega. Health produtivo retornou API/database ok antes da nova integração; isso não comprova implantação de Desempenho.
