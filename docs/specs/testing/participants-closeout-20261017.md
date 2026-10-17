# Fechamento — participantes públicos e ações de posição (2026-10-17)

Workflow: WFLOW-20261017-PARTICIPANTS-CLOSEOUT; implementação: WFLOW-20261017-TOTAL-PARTICIPANTS.

## Estado final e publicação

Encerramento técnico web/API concluído e validado em produção. Esta evidência atualiza o registro de preparação anterior; a distribuição do código Flutter permanece para release mobile própria.

- [PR #168](https://github.com/wscardua/gotrendlabs/pull/168), criada e integrada via GitHub MCP após aprovação do título/descrição pelo usuário.
- Commit da implementação: `02f08cd2a9c5e23f02b976a687783bd8aed63df2`.
- Merge e SHA verificada no servidor: `1d4003fa55c457d7cc1c4da81993e040cc7eaa1e`.
- [CI da PR](https://github.com/wscardua/gotrendlabs/actions/runs/39060897965): build/OpenAPI/JavaScript e 518 testes em 478,148 s, OK (2 skips).
- [CI/build/deploy da main](https://github.com/wscardua/gotrendlabs/actions/runs/39061727984): sucesso; 518 testes em 464,868 s, OK (2 skips).
- Deploy SSM `6fed5077-f951-4b95-ab88-779126642661`: Success, resposta 0; Actions confirmou sucesso em 2026-10-17 19:28:00 UTC (16:28 BRT).
- Smoke SSM `2d8ab820-927f-4431-9199-69a0b5be991f`: Success, resposta 0, sem stderr.
- Branch local `fix/participants-review-reason` preservada e avançada por fast-forward ao merge no worktree `/Users/williamsca/Documents/gotrendlabs-participants-review`. Árvore original e alterações alheias preservadas.

## Comportamento final aprovado

- FastAPI calcula contas distintas humanas + bots com previsões abertas e fornece `participants` e inteiro obrigatório `total_participants`. Reforços e múltiplas entradas da mesma conta não duplicam participantes; entradas revised/resolved/canceled continuam fora do filtro atual.
- Web apresenta o rótulo; Flutter usa o total nos cards e no painel, com vazio/singular/plural corretos e sem fallback para humanos ou zero na ausência do contrato obrigatório.
- Na web, Revisar bloqueado permanece desabilitado e não mostra aviso explicativo. Esta preferência após QA substitui o requisito inicial de aviso visível. Subtítulos finais: Reforçar → Aumentar sua posição; Revisar → Mudar sua escolha.
- Flutter mantém o motivo do bloqueio no subtítulo preexistente de Trocar escolha. Backend continua fornecendo as razões; revisão desativada, janela encerrada e limite atingido não foram alterados.
- Volume humano de GT₵, probabilidades, ranking, recompensas, elegibilidade e regras de bots permanecem iguais. Sem migration, backfill histórico, nova flag ou ajuste de configuração.

## Validação local e review

- Backend/web/MCP: suíte completa com 518 testes em 295,536 s, OK (2 skips), PostgreSQL 16 isolado/migrations reais; inclui os 3 novos testes de participantes/bloqueios e as regressões web atualizadas após o QA.
- Flutter: suíte completa com 114 testes e `flutter analyze --no-pub` aprovados novamente no review.
- OpenAPI, JavaScript analytics/prévia, Django check, migration drift, YAML, links novos e diff aprovados.
- Finding do review: frontmatter mobile deslocado corrigido; metadados e conteúdo preservados. Novo teste backend incluído no commit.
- HTTP autenticado DEV confirmou 2 participantes com humano + bot + reforço e Revisar desabilitado sem aviso. Reinício explícito da web foi necessário para atualizar os subtítulos; HTTP confirmou os novos textos.
- Container/armazenamento temporário dos testes removidos. Fixtures #18/#19 e contas dedicadas permanecem apenas no DEV; envs, credenciais e runtime não foram versionados.

## Smoke produtivo sem mutação

- Django, FastAPI, proxy, daemon e thumbnail-worker ativos; MCP healthy. Homepage pública HTTP 200; `/api/health` ok com API/database ok.
- `/api/openapi.json` exige `MarketResponse.total_participants` inteiro. Feed público: 9 mercados; totais/recortes/rótulos consistentes, incluindo 6 mercados com previsões abertas de bots. Detalhe JSON com inteiro obrigatório conferido.
- Agregação SQL `COUNT(DISTINCT p.user_id)` com `p.status='open'` e recortes humanos/bots confrontada com o serviço/API sob a role real `gotrendlabs_fastapi`, em transação REPEATABLE READ READ ONLY e timeout de consulta. Volume humano preservado.
- Template implantado renderizado internamente com contexto de teste apenas em memória: novos subtítulos presentes, Revisar disabled sem aviso nos três motivos e formulário Reforçar disponível. Sem criação de sessão administrativa ou visita autenticada de usuário real; não substitui QA físico no navegador.
- Preflight SSM `bc334368-b356-4ec7-b10e-d43f0727dcb6` e smoke tiveram o mesmo hash de configuração: `916bf0b0588efeb986d8d6ec8042922a4917eb5c5d8f56d42433efff6b876e34`. Revisão continuou desativada, limite de reforço 1, janela/limites/penalidade, flags/elegibilidade bot e build mínima 8 preservados.
- Nenhum mercado/usuário/previsão/configuração alterado pelo smoke; ausência dos slugs das fixtures DEV confirmada no banco produtivo. Nenhum reajuste de contagens históricas ou evento sintético inserido.

## Impacto MCP e arquitetura

MCP usa projeções editoriais `SearchItem`/`MarketProjection`, não `MarketResponse`; sinais preservam previsões humanas/bots por período. Ferramentas, schemas/contratos MCP, permissões/scopes, erros, replay/idempotência e orientação editorial não exigiram ajustes. Nenhuma capacidade derivada de ações humanas de Admin Ops.

FastAPI continua como autoridade de contagem, elegibilidade e bloqueios; web/mobile apresentam o contrato. Sem nova fronteira ou ADR necessário.

## Limites e distribuição mobile

O workflow GitHub publica web/API; não gera nem distribui APK/AAB. Código Flutter está validado no repositório, mas a nova contagem nos apps instalados exige próxima release mobile. Nenhum canal Play/APK ou build mínima foi alterado.

QA visual em dispositivo físico, fontes ampliadas, outros navegadores e carga representativa não executados. O smoke autenticado completo no navegador produtivo não foi realizado; template implantado e APIs foram conferidos sem mutação. Esses limites não representam falha de implantação web/API.
