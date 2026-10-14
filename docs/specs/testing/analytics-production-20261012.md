# Analytics v0.7 — evidência produtiva de 2026-10-12

Workflow: WFLOW-20261012-ANALYTICS-CLOSEOUT. Escopo: comparação Web/App mobile e usabilidade administrativa. Encerramento técnico concluído; homologações residuais explicitadas abaixo.

## Publicação e implantação

- [PR #166](https://github.com/wscardua/gotrendlabs/pull/166); commit `ddb2c114b47d4b2237ce5b972c051454543def8b`.
- Merge e SHA conferida no servidor: `4f1557f075d835d1a4ba6cc2cb6e6f32b7c885ba`.
- [CI da PR](https://github.com/wscardua/gotrendlabs/actions/runs/38320462241): sucesso, 515 testes em 610.416 s, 2 skips.
- [CI/deploy main](https://github.com/wscardua/gotrendlabs/actions/runs/38321666957): sucesso, 515 testes em 393.196 s, 2 skips; build, OpenAPI e testes JavaScript aprovados em ambas as execuções.
- Deploy SSM `ff3a0a0b-04c5-471e-9661-881244214d43`: Success, resposta 0, concluído em 2026-10-12 23:31:08 UTC.
- Smoke SSM `297eba2d-0389-4ead-96ae-2954e35d4806`: Success, resposta 0, sem stderr.
- Branch local `feature/analytics-platform-comparison` preservada, avançada por fast-forward ao merge; árvore original e alterações anteriores preservadas.

## Smoke real somente leitura

Serviços Django, FastAPI, proxy, daemon e thumbnail-worker ativos; MCP healthy. API health HTTP 200. Acesso anônimo ao resumo administrativo HTTP 401. CSS/JS públicos da versão `20261012-usability` correspondem aos arquivos implantados:

- CSS SHA256: `39cf6c0f89a5266656aacfa259beec31e9cba300f89fd5464c6f1142428a62c4`.
- JS SHA256: `7b18978bfd3b82f73f06fb3d5f4f19f2e69bbaf36623e78960b54210e379085f`.

Agregações executadas sob a role real `gotrendlabs_fastapi`, em transação REPEATABLE READ READ ONLY e com timeout de consulta. Comparação, soma de sessões por plataforma, oito datas UTC para sete dias, filtros Web/mobile, recorte vazio com participação nula, operação global preservada pelos filtros, soma dos eventos operacionais e série de 91 datas para 90 dias aprovadas. Tempo total dessas consultas no smoke: 0.286 s, sem caracterizar teste de carga.

Snapshot de sete dias: Web 60 sessões, 60 visitantes, 60 visualizações, participação 87%; App mobile 9 sessões, 7 visitantes, 97 visualizações, participação 13%. São observações existentes, não instalações ou pessoas únicas entre dispositivos. Nas últimas 24 h: Web 99 eventos humanos e App mobile 215; últimos recebimentos 2026-10-12 22:25:16 UTC e 20:55:07 UTC, respectivamente. Valores são históricos do smoke e não metas ou estado permanente.

Template Analytics renderizado no container Django com agregados reais: 89.467 bytes, locale pt-BR, labels e versões atuais presentes. Essa verificação interna não substitui uma sessão autenticada ponta a ponta no navegador.

GeoLite atual: ready, GeoLite2-City, build 2026-09-25 12:18:30 UTC, arquivo 65.345.887 bytes. A disponibilidade foi inspecionada; não inferida apenas do registro de importação. No DEV da worktree atual, o arquivo segue ausente conforme validação anterior.

## Operação e impactos

Nenhuma migration, flag, segredo, atualização Flutter ou ajuste adicional de configuração necessário. Deploy padrão recompilou serviços e publicou assets. Nenhum evento sintético, edição de usuário/mercado ou token administrativo criado para o smoke. Arquivo temporário privado com agregados foi removido pelo trap ao terminar.

MCP não consome o resumo administrativo: ferramentas, schemas, contratos, permissões, erros, replays e orientação editorial não exigem ajuste. Nenhuma permissão administrativa humana foi transferida ao MCP.

## Limites

CI completo com PostgreSQL limpo e migrations satisfez o gate que os testes locais em schema isolado não substituíam; o travamento CREATE/DROP do ambiente local não foi corrigido nesta entrega. Fluxo autenticado completo no navegador/MFA produtivo, toque físico, leitor de tela, outros navegadores e teste de carga volumétrico não homologados. Não afirmar catálogo inglês integral ou cobertura completa da instrumentação. Evidência registrada também na PR #166.
