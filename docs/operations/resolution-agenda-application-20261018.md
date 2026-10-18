# Aplicação produtiva da agenda — 18/10/2026

Operação concluída em 18/10/2026 às 09h34 BRT (commit transacional em 12:34:18Z), após autorização explícita do usuário para as onze datas às 20h America/Sao_Paulo. Código produtivo d4c23487029b315480906ad6424efa6c4875f241, sem novo deploy, mudança de contrato ou permissão MCP.

A tabela registra o resultado imediatamente após a aplicação às 09h34 BRT, não o estado corrente dos mercados.

| ID | Mercado | Previsão aplicada (BRT) | Resultado na aplicação |
|---|---|---|---|
|35|Fluminense × Palmeiras|25/10/2026 20h|Complemento assinado, versão 1|
|38|Brasil / ginástica feminina|28/10/2026 20h|Complemento assinado, versão 1|
|53|Vôlei Renata|31/10/2026 20h|Draft, revisão 8, preparação|
|55|Jabuti|31/10/2026 20h|Draft, revisão 8, preparação|
|44|Presidência|02/11/2026 20h|Complemento assinado, versão 1|
|52|Steam / Modern Warfare 4|04/11/2026 20h|Complemento assinado, versão 1|
|36|Corinthians / Libertadores Feminina|09/11/2026 20h|Complemento assinado, versão 1|
|39|João Fonseca / Basileia|09/11/2026 20h|Complemento assinado, versão 1|
|51|Netflix Brasil|11/11/2026 20h|Complemento assinado, versão 1|
|50|Latin Grammy / Álbum do Ano|20/11/2026 20h|Complemento assinado, versão 1|
|45|Emmy / novela|01/12/2026 20h|Complemento assinado, versão 1|

## Autorização e proveniência

O usuário revisou a tabela completa e fixou o horário de todos às 20h; depois autorizou expressamente a aplicação produtiva. Não é aprovação editorial fabricada pelo executor. [Inventário revisado](resolution-agenda-inventory-20261018-reviewed.json) conserva identidade/estado/hash/versão/revisão/snapshot e os critérios consultados. O inventário de 17/10 permanece evidência histórica não aprovada; não reaplicá-lo.

Fontes externas foram consultadas para o calendário: [CONMEBOL masculina](https://gol.conmebol.com/libertadores/pt-br/news/datas-confirmadas-confira-como-serao-disputadas-semifinais-da-conmebol-libertadores), [CONMEBOL feminina](https://gol.conmebol.com/libertadores/pt-br/news/assim-ficaram-os-grupos-da-conmebol-libertadores-feminina-2026), [Rotterdam](https://rotterdam2026.com/competitionschedule/), [Basileia](https://www.swissindoorsbasel.ch/en/tournament/match-schedule/), [TSE](https://www.tse.jus.br/comunicacao/noticias/2026/Marco/eleicoes-2026-confira-as-principais-datas-do-calendario-eleitoral), [Latin Grammy](https://www.latingrammy.com/en/awards/calendar/), [CBV](https://cbv.com.br/volei-de-quadra/supercopa), [CBL](https://www.cbl.org.br/2026/10/premio-jabuti-anuncia-os-finalistas-de-sua-68a-edicao/). As 20h são decisão operacional do usuário, não anúncio dos organizadores.

Emmy/Netflix/Steam preservam integralmente a referência textual histórica de consulta às 12h. O complemento assinado registra explicitamente a previsão operacional posterior às 20h e sua autorização; não altera elegibilidade, corte, recuperação, critérios, opções ou provas.

## Execução e preservação

- Snapshot RDS dedicado gotrendlabs-before-agenda-backfill-20261018: disponível, 100%, criptografado, confirmado antes da aplicação. Restauração desse snapshot não foi ensaiada; não alegar homologação de restore. PITR também disponível.
- Leituras MCP e SQL com role real FastAPI confirmaram os onze IDs especificados; visibilidade não equivale a inventário irrestrito do banco. Nove públicos e dois drafts.
- Dry-run: SSM 69afe168-3573-48f3-b1f5-9ef224bfc7c7, Success/0, rollback sem gravação. Primeira tentativa 2993f1a3 falhou antes de executar Python por permissão do arquivo operacional; corrigida somente a leitura dos arquivos sem segredos pelo usuário do container.
- Aplicação: SSM 8b8b2daf-5a62-4cb3-9d0f-fc36e84f6e0e, Success/0, sem stderr. Transação única pela ferramenta existente apply_inventory e serviços save_draft/human_edit_guard/human_edit_done, sob ator staff ativo 2, autorizado pelo pedido operacional. Sem chamada a publicação/resolução.
- Revalidação de estado/hash/revisão/snapshot, locks, assinatura e verificação ocorreram antes do commit. Replay de apply_inventory retornou already_applied para todos os nove, sem eventos adicionais. O wrapper de aplicação inicial recusa reexecução cega após mudança de estado; usar o recibo e a ferramenta normal para retomadas.
- Nove eventos market_schedule_registered acrescentados: ledger 28 → 37. Todos os 28 eventos anteriores permaneceram byte a byte iguais na representação integral comparada; definições, assinaturas, payloads e compromissos preservados.
- Comparação SHA-256 integral, dentro da transação, confirmou ausência de alterações nas nove definições, dezesseis compromissos e dezesseis previsões existentes; seis saldos, 21 lançamentos de carteira, solicitações de recarga, quatro reputações e 35 opções. Mesmos hashes antes/depois; comparação também cobriu campos não relacionados dos onze mercados e registros editoriais dos nove públicos.
- Histórico de revisões editoriais anteriores preservado. Drafts 53/55 receberam novo snapshot, revisão 8/preparation, decisão corrente vazia. A revisão histórica 7/aprovação continua preservada. Naquele momento, nova revisão humana era necessária antes de publicar; a operação não a simulou.
- Auditoria oficial force_full: SSM 1c511f5b-5722-4e46-965d-457f7421dd0b, Success/0; checkpoint assinado verified até 37, pending_events=0, às 12:35:12Z. Antes de atualizar esse checkpoint, leitura pública mostrou pending esperado; não era erro de assinatura.

## Verificação e limites

98 regressões executadas novamente em PostgreSQL Docker isolado: OK, 219.402s. Incluem agenda, rollback do signer, tampering, migração/dry-run/replay, integridade, editorial/admin/MCP/erros e fluxos de carteira. Nenhum teste de mutação usou produção.

Smoke público pós-checkpoint em 12:35:20Z: nove mercados overall_valid/definition_valid/prediction_commitments_valid/schedule_valid/ledger_chain_valid=true, errors vazios; definições e todos os eventos anteriores exatamente iguais ao baseline capturado antes. Nove páginas HTTP 200 exibem 20:00 BRT. Pacote público Steam contém complemento com assinatura, previsão 04/11 23:00Z e hash da definição original. MCP get_market reconfirmou as onze datas e estados/revisões esperados.

Não houve inspeção visual de navegador ou mobile nesta operação de dados; verificação web foi HTTP/HTML. Sem build/distribuição Flutter, merge, deploy, notificações ou mudança de permissões. Clientes consomem a agenda do backend já implantado. Não foram identificados efeitos colaterais nas verificações executadas.

Evidências privadas locais: .runtime/release/backfill-{dry-run,apply-result,public-before,public-after,package-check}.json e backfill-isolated-tests.log. Cópias operacionais protegidas no host em /opt/gotrendlabs/.runtime/agenda-20261018/. Sem credenciais nos artefatos documentais.

Reversão: corrigir adiante pelo reagendamento autorizado e auditável, preservando previsão original e eventos; não apagar complementos ou restaurar o snapshot sobre novas operações reais. Snapshot é contingência de recuperação, não mecanismo de desfazer a agenda.

Consulta MCP somente leitura posterior em 18/10/2026 encontrou os mercados 53/55 abertos, revisão editorial 10/approved, agenda versão 1 e previsão 31/10/2026 às 20h BRT. Essa publicação posterior não foi executada nesta operação; a leitura não homologa seu processo humano de aprovação.

O inventário revisado permanece a fotografia imutável de entrada da aplicação, incluindo estados e revisões anteriores. Não atualizar suas precondições para permitir repetição; não reaplicar.

Checklist universal/operação/testes aplicado. WFLOW-20261018-AGENDA-PRODUCTION-BACKFILL concluído. Distribuição mobile permanece separada da implantação backend; a correção de apresentação das etapas do painel segue em outro contexto.
