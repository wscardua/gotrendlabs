# Fechamento da resolução prevista — 17/10/2026

Workflow WFLOW-20261017-RESOLUTION-AGENDA-CLOSEOUT. **Estado desta revisão: implementação local validada; descrição aprovada pelo usuário e PR #170 aberta. CI/backup/merge/deploy em acompanhamento.** Este documento consolida o estado final de produto e substitui descrições históricas de soluções abandonadas, sem apagar seus registros.

## Fonte da verdade

- Feature: [market-resolution-agenda](../features/market-resolution-agenda.md). A pedido do usuário, somente `expected_resolution_at` e `schedule_timezone` são entradas ativas da agenda. `resolution_date` é o mesmo conceito; resolução efetiva continua `resolved_at`. Corte/recuperação são condições do critério quando aplicáveis, sem campos operacionais próprios.
- FastAPI valida previsão futura para publicação, ordem após o fechamento e fuso IANA/offset; deriva situações, filtros/ordenação/contadores. Vencimento não resolve, cancela ou movimenta saldo.
- Histórico original/vigente: staff/MFA, motivo, versão esperada e eventos assinados transacionais; sem ampliar MCP. Terminais não recebem reagendamento; desfazer resolução conserva histórico.
- [ADR-0016](../decisions/ADR-0016-resolution-agenda.md): complemento append-only vinculado à definição original, sem reconstruir/reassinar bytes históricos. Auditoria verifica assinatura/histórico/projeção e bloqueia selagem inválida.
- Admin Ops/painel distinguem fechamento, previsão e decisão, sem progresso por passagem do tempo. Web exibe tags estáticas no cabeçalho; Flutter coloca prazos no rodapé do resumo e critério com três linhas/painel inferior rolável/selecionável. O usuário aprovou o visual físico.
- MCP editorial existente: agenda em validate/create/update/search/get/submissão/snapshots, política 1.4/ficha 1.8. Códigos de validação preservados, scopes/replays/gates humanos mantidos.

## Evidências locais

- Revisão de working tree contra origin/main 7029dd8: corrigidos helper administrativo de datas, tradução incorreta de erros pelo MCP e divergências da spec mobile; [recibo das correções](resolution-agenda-review-fixes.md).
- 120 testes integrados de agenda/integridade/MCP/transporte/Admin aprovados em 201.458s; cinco testes novos estão incluídos nesse total.
- Flutter analyze limpo e 120 testes aprovados na última alteração Flutter. Build/install do pacote QA .local no Samsung SM-G980F e inspeção de prazos/prévia/painel inferior concluídos.
- OpenAPI --check e diff check aprovados. Resultados da rodada ampla e da revalidação após ajustes estão registrados abaixo; CI/build completos da PR serão exigidos antes do merge.

## GitHub e implantação

Descrição apresentada e aprovada pelo usuário com “prossiga”. [PR #170](https://github.com/wscardua/gotrendlabs/pull/170), commit caee7aa, enviada; [CI da PR](https://github.com/wscardua/gotrendlabs/actions/runs/39077098980) iniciado. Esta é a fotografia anterior ao merge; o registro operacional dos resultados posteriores, incluindo SHA, Actions e smoke produtivo, será publicado na timeline da PR, sem confundir schema com backfill editorial. A branch local será preservada. Workflow `.github/workflows/deploy.yml`: PR executa CI/build; main pode disparar deploy por SSM quando ENABLE_PROD_DEPLOY=1. Deploy aplica schema com role de migration e reinicia Django/FastAPI/daemon/MCP/executor configurado.

Antes do merge: confirmar backup recuperável/preflight. Após merge: acompanhar CI/build/deploy, SHA/serviços/health/OpenAPI/MCP e migrations reais; verificar grants/assinaturas e situações sem mutações de teste. Falha de CI/deploy exige correção antes de declarar sucesso.

## Dados e limites

[Inventário revisável](../../operations/resolution-agenda-inventory-20261017.json) e [runbook](../../operations/resolution-agenda-runbook.md). Nenhum item atual foi marcado como revisado. IDs 45/51/52 têm horários candidatos explícitos; IDs 35/36/38/39/44/50 precisam de definição operacional de hora; drafts 53/55 seguem revisão editorial. Reconsultar estado/hash/revisão/cobertura antes de aplicar. Não fabricar horas nem parecer humano.

Deploy de schema não executa o comando de complementos de dados. Mercados publicados sem agenda permanecem com pendência explícita e exigem regularização para resolver/reagendar; previsões e leituras não são bloqueadas indiscriminadamente. O estado final da migração exige os ativos abrangidos regularizados; não declarar essa etapa concluída sem evidência.

Actions atual não distribui Flutter/APK/AAB/Play; deploy web/API não atualiza apps instalados. QA local usa entrada sem Firebase opcional e não homologa bootstrap/release/push. Overflow preexistente em hero/métricas na escala 2× permanece em known-gaps, fora desta feature.

## Preflight produtivo somente leitura

AWS MCP confirmou conta esperada/EC2 running e RDS available com armazenamento criptografado, retenção automática de um dia e LatestRestorableTime 2026-10-17T22:31:43Z. Não houve mudança dessas configurações nem criação de snapshot nesta etapa.

SSM 920e7f9d-90a7-496b-82e8-c4e79d366849 terminou Success/response 0/sem stderr. Checkout produtivo 1d4003fa55c457d7cc1c4da81993e040cc7eaa1e; seis serviços running, MCP healthy; disco do host com 7.8G livres (58% usado). Arquivos de backup de ambiente já existentes permanecem preservados; nenhum conteúdo de segredo foi lido/exposto. Isso verifica prontidão operacional, não implantação da nova feature. Confirmar backup recuperável novamente imediatamente antes do futuro merge.

Primeira execução completa local foi interrompida após atualizar fixtures sintéticas de publicação ao contrato atual (192 testes executados sem falha, execução parcial não contada como suíte completa). A rodada final reiniciou com as fixtures atualizadas, sem fallback em código de domínio.

A conferência documental do fechamento identificou colisão com ADR-0012 de thumbnails. A nova decisão de agenda foi numerada como ADR-0016, com referências atualizadas, preservando a ADR existente.

## Ajustes encontrados na rodada ampla

A rodada de 552 testes em 688.537s terminou com cinco falhas em testes que ainda preparavam dados/payloads/mocks do contrato anterior: duas edições administrativas reenviavam campos de resposta no contrato de escrita estrito; um teste de posições/resolução usava mercado fixture sem agenda assinada; dois mocks da fila esperavam três consultas por status em vez da consulta autoritativa única resolution_queue. Corrigidos os dados e consumidores de teste, sem relaxar validação, autorização, proteção da definição ou regras financeiras. As duas edições passaram em rodada intermediária de dois testes (13.637s); a rodada final cobre os cinco casos e regressões de agenda/MCP/editorial.

O checklist E05 foi alinhado ao texto da política 1.4 já definida nesta branch; o teste editorial agora compara a política ativa com o checklist, sem continuar validando somente o arquivo histórico 1.2. Nenhuma política produtiva ou parecer humano foi alterado nesta etapa.

O primeiro resultado completo não é declarado como aprovado. A verificação após os ajustes é registrada separadamente; CI/build completos da PR permanecem obrigatórios antes de merge.

## Resultado final da preparação

- Rodada ampla: 552 testes/688.537s; cinco falhas de fixtures/mocks foram corrigidas (não é declarada como rodada verde).
- Revalidação final: **98 testes aprovados em 192.350s**, incluindo os cinco cenários, contrato de escrita, posições/liquidação, filas, auditoria em todos os estados, agenda, MCP, política ativa e datas administrativas. Cobertura sobreposta à rodada ampla; não somar os totais como testes distintos. Log privado /tmp/gtl-agenda-closeout-regression-tests.log. Sem falha conhecida pendente nos cenários corrigidos.
- Flutter analyze sem issues (3.7s) e 120 testes aprovados novamente no fechamento; sem alteração Flutter nesta etapa de fixtures/docs.
- JavaScript analytics/prévia, OpenAPI --check, Django check, makemigrations --check --dry-run, links novos, scan limitado de padrões de credenciais e diff check aprovados. O scan não equivale a auditoria exaustiva de segredos.
- Dockerfile check passou; build completo local limitado por falta de espaço no Docker durante apt. Build CI é obrigatório antes do merge; nenhuma imagem/volume do usuário foi removido.
- Checklist universal/alterar-feature/implementação/testes/publicação aplicado. Fonte da verdade/specs/contratos/ADR-0016/estado/README/memória reconciliados; branch local será mantida. Descrição aprovada; push e PR #170 realizados. Merge e implantação exigem CI completo aprovado e snapshot disponível; resultados posteriores constam na timeline da PR.

## Acompanhamento autorizado

Snapshot manual criptografado `gotrendlabs-before-resolution-agenda-20261017` solicitado via AWS MCP em 2026-10-17T22:57:15Z (PostgreSQL 16.13). Aguardar `available` antes do merge. Isso fornece ponto recuperável; restauração deste snapshot não foi ensaiada nesta execução. ENABLE_PROD_DEPLOY=1 confirmado. A conclusão operacional e eventuais falhas/correções serão registradas na [timeline da PR #170](https://github.com/wscardua/gotrendlabs/pull/170); inventário permanece não revisado e distribuição mobile separada.

## Resultado produtivo e correção de empacotamento

PR #170 integrada em `main`, merge b499ca84fff68bb99a5f9f2e2485d16698457cbe. CI da PR 39077154897: 552 testes/418.943s, OK (skipped=2), Dockerfile/build/OpenAPI/JS aprovados. CI da main 39077810489: 552 testes/512.929s, OK (skipped=2); **deploy dessa execução falhou**, não é declarado verde. Snapshot manual criptografado `gotrendlabs-before-resolution-agenda-20261017` confirmado available/100% antes do merge; restauração não ensaiada.

SSM de deploy 5e3ffa8e-f4e0-4c48-8ca9-92cac1ea4cb5 aplicou migrations 0033–0036, verificou privilégios Django/FastAPI e reiniciou os serviços. MCP falhou por ModuleNotFoundError: schema editorial importava ScheduleFields de módulo de domínio não incluído na imagem enxuta. O build CI anterior verificava apenas a imagem principal e não detectou essa fronteira.

Recuperação SSM 336f1564-4fff-40dc-acb4-a540a4b6f110: Success/0, MCP healthy, proxy validado/recarregado. Aplicados à imagem MCP os dois arquivos locais verificados, sem modificar checkout produtivo ou banco: editorial_schemas.py SHA256 102cb98031c5b0bdcede44efb3fa9beb344ba60edb04757e31fe0537580c37b2 e resolution_schedule_contract.py SHA256 2ca4feb70025b96daf2c3d3ed9306780094ec38ca83bcc836d47e709ca94ef1f. Imagem recuperada sha256:a418b8d928d0cfceacc1e8d6aeff3a013987c9d96b887a7aaa21b6c606d29bed. A correção permanente extrai contrato Pydantic puro, mantém validação única e erros HTTP no backend, copia contrato para MCP e exige importação real/schema no build da imagem; CI passa a construir a imagem MCP. **Não reexecutar deploy anterior à integração dessa correção**, pois reconstruiria a imagem incompleta.

Smoke somente leitura: API/database ok, OpenAPI com agenda atual, página pública HTTP 200; nove mercados verificados, overall_valid/definition_valid/prediction_commitments_valid/ledger_chain_valid true, sem erros. Os campos originais dos eventos públicos permanecem iguais; novos campos de prova são expostos sem alterar hashes. Fingerprints dos conteúdos canônicos/assinaturas antes/depois iguais: nove definições e quinze compromissos (SSM f8e8ee7b-6a66-4f40-99d3-34d38f78ef4c e 54d7e665-3c56-4b21-8713-f4b8bd27b239).

MCP real: política 1.4 com hash 5027fac6bd8449f91a4d8909913c5967aba559094b3049a9448615d8d7deb2b0; hashes de checklist/ficha iguais aos arquivos locais. Catálogo 2026-10-17T23:22:59Z retornou 11 itens/complete_for_query/has_more=false; isso não é inventário irrestrito do banco. Nove públicos continuam schedule_pending, versão 0 e previsão nula; drafts 53/55 seguem preparação. Nenhum backfill nem parecer humano fabricado. Mobile permanece validado localmente, sem distribuição de release pelo Actions web/API.

[Recibo no GitHub](https://github.com/wscardua/gotrendlabs/pull/170#issuecomment-6243023723). A recuperação operacional está concluída; integração e novo CI/deploy reproduzível da correção de empacotamento ainda pendentes.

Validação da correção permanente: 98 testes de regressão aprovados em 178.826s; teste novo de importação isolada aprovado (0.125s); build real MCP e importação do servidor/schema aprovados, OpenAPI --check sem mudança, diff check aprovado. Sem nova alteração Flutter/UI ou financeira. Checklist de fechamento aplicado; workflow mantém pendência da PR/CI/deploy corretivo, com restauração operacional comprovada.
