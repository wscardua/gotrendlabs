---
id: FEAT-EDITORIAL-001
titulo: "Governança editorial de mercados"
versao: 1.5
status_spec: aprovada
status_impl: parcial
ultima_atualizacao: 2026-10-10
origem:
  - docs/specs/spec_prediction_social_market_pt.md
contratos_afetados:
  - market-lifecycle.md
  - agent-integrations.md
contratos_revisados:
  - market-lifecycle.md
  - integrity-ledger.md
dependencias:
  - FEAT-MARKET-001
  - FEAT-SUGGEST-001
  - FEAT-RES-001
  - FEAT-INTEGRITY-001
impacta:
  - admin-ops
  - editorial
aprovacao: criterios_1_2_aprovados_em_2026-09-26_e_revisao_universal_solicitada_em_2026-10-07
---

# Governança editorial de mercados

## Escopo vigente — documento único 1.5

A preparação e a revisão humana de novas versões usam um único documento
editorial textual, organizado em contexto/duplicidade, pergunta/regras/prazos,
fontes/evidências, contingências/responsável e pendências/conclusão. E01–E11
permanecem guia da política aprovada, sem onze entradas ou checkboxes no
formulário. O humano edita o texto, confirma uma vez apenas para aprovar e
registra a decisão. O backend associa confirmação, autor, data e snapshot à
revisão atual. A publicação continua protegida pelo gate universal vigente.

Uma migração única converte fichas anteriores em documento, preserva seus
snapshots históricos e exige nova avaliação humana. O runtime aceita somente
o documento textual; payloads estruturados anteriores são rejeitados.
Para aprovar, o documento declara na seção final `Pendências para aprovação: nenhuma` e o humano confirma a conferência. Quando houver horário conhecido de divulgação na linha `Anúncio esperado: ...`, a FastAPI rejeita fechamento igual ou posterior. Mercados já publicados mantêm a última decisão histórica durante a conversão; drafts e agendados precisam de nova revisão antes da publicação.
As seções 1.2/1.3 abaixo registram o comportamento histórico.

## Escopo vigente — revisão universal 1.3

Todos os mercados possuem ficha editorial estruturada, inclusive criação humana e conversão de sugestões. A revisão usa os critérios editoriais aprovados v1.2, sem cotas obrigatórias de diversidade. Staff/superuser com MFA registra preparo e parecer em uma ação; agentes continuam restritos a drafts próprios. Origem humana tem integração nula, sem identidade técnica fictícia.

Publicação de draft/agendado exige aprovação humana da revisão/hash/política/conteúdo atuais na FastAPI, além de prazo futuro com fuso válido e modo de fechamento explícito. Ausência de ficha ou aprovação bloqueia. Edição invalida aprovação. São as mesmas regras para humano e MCP.

A migration 0003 cria fichas pendentes nos legados sem alterar mercados, opções, previsões, ledger, estados ou provas. Mercados já abertos/fechados podem receber parecer; terminais permitem consulta. Não há fechamento, cancelamento ou republicação retroativos. Campos públicos e definição assinada continuam protegidos.

As seções abaixo registram a entrega histórica v1.2; suas exclusões de parecer persistido/gate foram substituídas pela revisão 1.3. Validação corrente: [relatório local](../testing/universal-editorial-20261007.md). Homologação externa MCP permanece separada.

## Entrega histórica 1.2 — objetivo e escopo

Estabelecer um processo operacional reutilizável de seleção, redação, revisão, publicação e acompanhamento de mercados de previsão, com consulta para staff no Admin Ops e critérios versionados que possam ser reutilizados em uma evolução futura de IA.

O usuário aprovou a versão editorial `1.2` em 2026-09-26. Ela inclui [manual editorial](../../editorial/manual-editorial.md), [ficha de mercado](../../editorial/ficha-de-mercado.md), [checklist de publicação](../../editorial/checklist-de-publicacao.md), critérios de aceite e referências nas specs. A implementação oferece consulta somente leitura no Admin Ops e critérios versionados. O escopo desta feature foi integrado pela PR `#124`, implantado e validado em produção em 2026-09-26. Avaliação assistida por IA e registro estruturado de pareceres pertencem a uma evolução futura separada.

Permanecem fora do escopo: modelos/migrations, parecer persistido, avaliação por IA, aprovação por API, publicação automática, alteração de mercados reais, telemetria, notificações e mudança de ranking/destaque do feed. Não há piloto, metas de volume ou distribuição temática nesta versão. O manual orienta o acompanhamento dos indicadores disponíveis, sem criar telemetria.

## Comportamento operacional

1. Autor consulta dados internos disponíveis, pesquisa fontes e preenche a ficha; ausência de acesso fica explícita.
2. Revisor confere E01–E11 e registra `aprovar`, `devolver` ou `rejeitar`, motivo, versão e data. Parecer não é estado de domínio.
3. Pendência obrigatória impede aprovação editorial. Autor ajusta e submete a revisão afetada novamente.
4. Operador revalida a versão e a incerteza imediatamente antes de abrir o mercado pelo fluxo staff existente. Sugestões convertidas em rascunho e agendamentos seguem a mesma régua.
5. Responsável acompanha resultado/fonte e resolve pelos critérios publicados, mantendo evidência e correções rastreáveis.

A ficha fica em registro operacional restrito, com referência/versão em `admin_notes` do rascunho. Não há persistência estruturada do parecer nesta fase; ele não integra a definição criptográfica. Campos públicos devem conter todo critério necessário ao usuário, sem depender da ficha privada.

## Orientação para o staff

O manual e a ficha usam linguagem operacional, com exemplos fictícios identificados, instruções de verificação e ação diante de problemas. Termos de implementação ficam nesta spec. O acompanhamento dos indicadores deve explicar o que cada número mede, limites de comparação e uso na revisão de pautas; dado ausente não pode ser inferido de outro indicador.

O ponto de partida é a construção de mercados de previsão: incerteza relevante, pergunta clara, opções, prazo e resultado verificável. A introdução explica o produto, distingue previsão de enquete e esclarece que opções são respostas, não instrumentos financeiros. O consenso não define o vencedor.

Por orientação do usuário nesta revisão, diversidade passa a orientar o catálogo sem cotas obrigatórias de categorias para aprovar um mercado; a regra numérica da v1.1 é substituída. Recomendações anteriores de cotas em materiais auxiliares não devem ser usadas como requisito de publicação deste fluxo. A pesquisa de duplicidade e a classificação correta permanecem obrigatórias.

Manual explica as seis etapas, ficha registra o trabalho e checklist independente concentra E01–E11. Indicadores são apresentados em participação/acompanhamento e qualidade das perguntas/resolução, sem piloto, metas ou coleta nova.

## Correspondência com os campos atuais

Pergunta, contexto, fonte e critério correspondem a `title`, `summary`, `source` e `resolution_criteria`; encerramento usa `close_at`/`close_timezone`. Responsáveis editoriais, checklist, parecer e apuração esperada ficam na ficha operacional, sem novos campos. `resolved_at` registra apenas a resolução efetiva; referência em `admin_notes` não substitui auditoria de domínio.

## Arquitetura e segurança

- Admin Ops: superfície de operação existente e referência documental; não recalcula regras críticas.
- FastAPI: preserva autoridade de publicação, fechamento, cancelamento, resolução e integridade. Nenhum contrato alterado.
- Banco: nenhuma nova entidade ou escrita direta introduzida.
- Web/mobile: nenhuma nova promessa de bloqueio de publicação ou mudança de consenso/destaque.
- Scheduler/comunicações: permanecem nos contratos atuais; agenda editorial não cria job nem autoriza disparos.
- Fontes/fichas não devem expor credenciais, PII ou vida privada sensível; conflitos exigem encaminhamento a operador sem conflito.
- Definição assinada não é alterada após publicação. Desfazer resolução antes de `seal_due_at` não permite reescrever a pergunta; após `sealed`, correção somente append-only conforme contratos vigentes.

Revisão de arquitetura: mantém fronteiras existentes; não requer ADR, OpenAPI, migrations ou alteração de fórmula. Risco residual: checklist manual depende de disciplina e pode ser ignorado pelo operador; enforcement futuro precisa de ciclo próprio na FastAPI com testes de bypass, autorização e vínculo da aprovação à versão publicada.

### Visibilidade dos documentos editoriais

A rota `/admin-ops/editorial/` exige sessão staff, mas sua fonte está em `docs/editorial/` no repositório GitHub público. Após o merge, os arquivos poderão ser consultados diretamente no repositório, independentemente da autenticação no site. Em 2026-09-26, o usuário decidiu manter essa estrutura por enquanto. Portanto, a restrição ao staff se aplica à página administrativa, não ao conteúdo dos arquivos no GitHub.

Antes de acrescentar informações confidenciais ao editorial ou exigir privacidade fora do site, reavaliar essa decisão. Nesse caso, mover a fonte para armazenamento privado, retirar as cópias públicas e servir o conteúdo apenas após autenticação. Até lá, não inserir segredos, dados pessoais ou pareceres internos sensíveis nos documentos versionados.

## Aceite e validação documental

| Cenário | Resultado esperado |
| --- | --- |
| Staff inicia a leitura | Encontra definição de mercado de previsão, opções, créditos educativos e exemplo fictício antes das instruções |
| Opção mais escolhida não corresponde à evidência | Resultado segue o critério e a fonte, não o consenso |
| Catálogo concentra cobertura em uma categoria | Planejamento justificado; sem reprovação automática por cota temática |
| Pergunta vaga ou título diferente do critério | E04 pendente; devolver |
| Fonte inacessível sem alternativa verificável | E06/E08 pendentes; não aprovar |
| Catálogo indisponível | E03 pendente, limitação registrada; não alegar deduplicação |
| Evento já conhecido antes da abertura | E01 falha na rechecagem; não publicar |
| Opções sobrepostas ou empate sem regra | E05/E08 pendentes; devolver |
| Fechamento após divulgação programada | E07 pendente; corrigir antes da aprovação |
| Adiamento/remoção/correção de dado | Aplicar tratamento escrito, sem escolher fonte retroativamente |
| Alteração no rascunho após aprovação | E11 exige nova revisão afetada e versão conferida |
| Sugestão convertida ou mercado agendado | Mesmos critérios; parecer não abre mercado |
| Definição publicada problemática | Encaminhar incidente; não editar campos protegidos |
| Resultado selado incorreto | Correção append-only; não desfazer/cancelar |
| Cripto sem aviso ou incentivo financeiro | E02/E09 pendentes ou rejeição por inadequação |
| Staff consulta exemplo de pergunta ou percentual | Entende o problema, a forma correta de escrever e o que conferir, sem precisar de nomes de campos/API |
| Indicador de retorno não disponível | Registrar indisponibilidade, sem usar views como substituto |
| Ficha completa e checagens atuais | Aprovação editorial; publicação ainda pelo fluxo staff |

Evidência de aceite: leitura cruzada de manual/ficha/checklist/contratos, paridade E01–E11 entre checklist e JSON, links locais, frontmatter e rastreabilidade; testes Django de acesso visitante/staff/usuário comum, GET exclusivo, escape de HTML, navegação no editor e renderização dos três documentos; `manage.py check`, OpenAPI `--check` e `git diff --check`. A PR `#124` passou no CI e no deploy produtivo da GitHub Action `36275879637`; o smoke público retornou `302` para login, e a renderização dos três documentos com sessão staff retornou `200` no container produtivo. Evidências detalhadas no workflow.

## Evolução originalmente separada na entrega 1.2

Se a equipe decidir automatizar a revisão: especificar versionamento e persistência de pareceres, autorização staff, invalidação de aprovação por edição, bloqueio autoritativo de publicação inclusive por API/agendamento, auditoria e política de legado. Essa evolução não está implementada nem é requisito para concluir a entrega editorial atual.

## Consulta administrativa e preparo para IA

- Django expõe `GET /admin-ops/editorial/` somente para staff usando a sessão administrativa existente. Menu e lista de mercados dão acesso ao manual, checklist e ficha aprovados; o editor abre a consulta em outra aba para preservar o formulário.
- Conteúdo exibido vem dos arquivos versionados em `docs/editorial/`, sem cópia das regras em templates. A renderização escapa HTML bruto e não solicita a FastAPI. A página é read-only e usa `Cache-Control: private, no-store`.
- `docs/editorial/criteria-v1.2.json` fornece versão aprovada, IDs estáveis E01–E11, perguntas, evidências, seção do manual, condição de bloqueio editorial, necessidade de checagem da fonte e decisão humana obrigatória. O teste confere a paridade textual com o checklist e a presença dos IDs na ficha. O hash SHA-256 do arquivo está disponível ao servidor para futura referência de versão; não representa aprovação de um mercado.
- Não há endpoint para a IA, execução de modelo, parecer persistido ou bloqueio novo de publicação. Futura avaliação deve receber snapshot do rascunho, versão/hash dos critérios, evidências e distinção entre análise textual e verificação real da fonte. FastAPI deve ser autoridade de qualquer parecer persistido ou gate de publicação; Django apenas apresenta resultados.

### Aceite da consulta administrativa

- Staff lê os três documentos e E01–E11 no Admin Ops; visitante é encaminhado ao login e usuário comum recebe `403`.
- Editor e lista de mercados oferecem links para o editorial; o editor mantém o formulário em sua aba.
- Qualquer edição de pergunta/evidência do checklist sem atualização do JSON falha no teste de paridade.
- Página recusa POST e não cria ou altera mercados; checagem de Django e testes focados passam no `.venv`.

## Revisão aprovada pelo usuário em 2026-10-07 — gate universal

Todo mercado possui ficha editorial estruturada e revisão humana, independentemente de origem. Nova publicação exige aprovação vigente da versão/hash/política/conteúdo e configuração válida de fechamento. Ambos os modos exigem data/hora futura e fuso válido; automático exige daemon habilitado, manual deixa a ação staff disponível. Legados publicados recebem ficha pendente sem mudar lifecycle, previsões ou provas; nenhum parecer fictício. Substitui explicitamente a exceção anterior para mercados humanos.

## Integração FEAT-THUMB-001

Thumbnails podem ser geradas a partir do texto/classificação atuais sem salvar ficha/mercado. Confirmar no salvamento altera image_url e invalida o parecer como outras edições. Publicar versão aprovada continua exigindo revisão humana do snapshot salvo; seleção nova pendente orienta salvar/revisar. Geração não aprova nem publica. [Feature](ai-market-thumbnails.md).
