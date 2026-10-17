# Fechamento da resolução prevista — 17/10/2026

Workflow WFLOW-20261017-RESOLUTION-AGENDA-CLOSEOUT. **Estado: implementação local validada e commit preparado; PR/merge/deploy aguardam autorização prévia da descrição.** Este documento consolida o estado final de produto e substitui descrições históricas de soluções abandonadas, sem apagar seus registros.

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

Aguardando apresentação e autorização da descrição da PR pelo usuário. Não há PR/merge/deploy desta feature ainda. A branch local será preservada. Workflow `.github/workflows/deploy.yml`: PR executa CI/build; main pode disparar deploy por SSM quando ENABLE_PROD_DEPLOY=1. Deploy aplica schema com role de migration e reinicia Django/FastAPI/daemon/MCP/executor configurado.

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
- Checklist universal/alterar-feature/implementação/testes/publicação aplicado. Fonte da verdade/specs/contratos/ADR-0016/estado/README/memória reconciliados; branch local será mantida. Aprovação da descrição da PR ainda pendente; sem push/PR/merge/deploy da feature.
