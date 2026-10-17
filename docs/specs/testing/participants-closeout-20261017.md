# Fechamento — participantes públicos e ações de posição (2026-10-17)

Workflow: WFLOW-20261017-PARTICIPANTS-CLOSEOUT; implementação: WFLOW-20261017-TOTAL-PARTICIPANTS.

## Estado atual

Implementação e QA local concluídos. Revisão encontrou apenas deslocamento do frontmatter mobile, já corrigido e validado. Título/descrição aprovados pelo usuário em 2026-10-17; fluxo de PR, merge, CI/deploy e smoke produtivo autorizado. Nenhuma implantação desta feature foi realizada até este registro de preparação.

Branch `fix/participants-review-reason`, worktree `/Users/williamsca/Documents/gotrendlabs-participants-review`, base `origin/main`/HEAD `f92fd3ba9565d2a91370f32d34e8164dba9b1894`. Worktree original e alterações alheias preservados. Manter a branch local após publicação.

## Comportamento final aprovado

- FastAPI calcula contas distintas humanas + bots com previsões abertas e fornece `participants` e inteiro obrigatório `total_participants`. Reforços e múltiplas entradas da mesma conta não duplicam participantes; entradas revised/resolved/canceled continuam fora do filtro atual.
- Web apresenta o rótulo; Flutter usa o total nos cards e no painel, com vazio/singular/plural corretos e sem fallback para humanos ou zero na ausência do contrato obrigatório.
- Na web, Revisar bloqueado permanece desabilitado e não mostra aviso explicativo. Esta preferência após QA substitui o requisito inicial de aviso visível. Subtítulos finais: Reforçar → Aumentar sua posição; Revisar → Mudar sua escolha.
- Flutter mantém o motivo do bloqueio no subtítulo preexistente de Trocar escolha. Backend continua fornecendo as razões; revisão desativada, janela encerrada e limite atingido não foram alterados.
- Volume humano de GT₵, probabilidades, ranking, recompensas, elegibilidade e regras de bots permanecem iguais. Sem migrations, novas flags ou mudanças de configuração de produção.

## Evidências

- Flutter: suíte completa com 114 testes e `flutter analyze --no-pub` aprovados novamente no review.
- Backend/web/MCP: suíte completa com 518 testes em 295,536 s, OK (2 skips), PostgreSQL 16 isolado e migrations reais; inclui os 3 novos testes de participantes/bloqueios e as regressões web atualizadas após o QA. As 17 regressões direcionadas anteriores também passaram.
- OpenAPI `--check`, testes JavaScript de analytics/prévia, `manage.py check` e `makemigrations --check --dry-run` aprovados no fechamento.
- `git diff --check`, links novos e YAML das specs alteradas aprovados; metadados/frontmatter preservados.
- Container/armazenamento temporário PostgreSQL desta suíte removidos após término; banco/serviços DEV e fixtures de QA preservados. Teste backend antes não rastreado agora incluído no índice Git.
- HTTP autenticado no DEV confirmou 2 participantes com 1 humano + 1 bot e reforço; Revisar desabilitado sem aviso e Reforçar disponível. Reinício explícito da web foi necessário para trocar os subtítulos antigos; HTTP confirmou os novos após restart.
- Fixtures sintéticas #18/#19, contas dedicadas e credenciais permanecem somente no DEV. `.runtime/`, envs, logs, artefatos de build e credenciais não integram o commit.

## Impacto MCP e arquitetura

`apps/mcp/server.py` usa projeções editoriais `SearchItem`/`MarketProjection`, não `MarketResponse`. `editorial_routes.signals` preserva previsões humanas/bots por período. Ferramentas, schemas/contratos MCP, permissões/scopes, erros, replays/idempotência e orientação editorial não exigem ajustes. Nenhuma ação humana de Admin Ops amplia capacidade de agente.

FastAPI continua como autoridade de contagem, elegibilidade e bloqueios; web/mobile apresentam o contrato. Sem mudança de fronteira ou ADR necessário.

## Publicação e verificação

1. Após aprovação do título/descrição: commit/push da branch e PR em português via GitHub MCP para `main`.
2. Acompanhar CI completo da PR (build Docker, OpenAPI, JavaScript e testes PostgreSQL). Corrigir falhas reais antes do merge.
3. Merge via GitHub MCP; preservar branch local. Acompanhar `GoTrendLabs CI and Deploy` da main até conclusão de build e deploy.
4. `ENABLE_PROD_DEPLOY=1` e `DEPLOY_BRANCH=main` conferidos por leitura no GitHub durante a preparação. Nenhuma alteração de variável/configuração necessária.
5. Smoke produtivo: conferir SHA, saúde dos serviços/API, OpenAPI e total obrigatório no feed/detalhe JSON. Conferir contagem contra SQL DISTINCT sob a role real e transação READ ONLY; não recalcular/persistir históricos ou inserir fixtures no banco produtivo.
6. Validar template implantado para subtítulos e Revisar desabilitado sem aviso usando renderização interna sem mutações ou sessão administrativa criada. Não chamar ações financeiras ou do mercado para o smoke.
7. Registrar links reais de commit, PR, Actions e smoke e reconciliar memória/documentação com o resultado efetivamente observado.

## Mobile e limites

O workflow GitHub publica web/API; não gera nem distribui APK/AAB. Código Flutter desta feature está validado no repositório, mas novos textos/contagem no app instalado exigem uma próxima release mobile. Não elevar build mínima nem alterar canais Play/APK como parte deste deploy.

QA visual em dispositivo físico, fontes ampliadas e carga representativa não foram executados nesta fatia. O protocolo e o motor econômico não mudam. Rollout/CI/smoke ainda pendentes; não afirmar conclusão produtiva com base no QA local.
