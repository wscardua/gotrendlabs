# Aceite e regressão — FEAT-MCP-001

Estado: testes locais/CI aprovados e infraestrutura produtiva habilitada ([evidências](mcp-production-rollout-20261007.md)); Dot/piloto autenticado pendentes; consultar [resultados e pendências por critério](mcp-editorial-results.md). Usar PostgreSQL isolado real para concorrência/grants, testes unitários para funções e fluxo real para auth/UI/MCP. [Spec](../features/mcp-editorial-agents.md).

| ID | Cenário | Evidência exigida |
| --- | --- | --- |
| MCP-A01 | Staff e superuser, ambos com MFA, administram todas as integrações | Mesmos resultados; visitante/comum/sem MFA negados; sem filtro por dono |
| MCP-A02 | Credencial gerada e depois perdida | Exibida uma vez, no-store, somente hash persistido; nunca reapresentada; nova emissão auditada |
| MCP-A03 | OAuth completo | PKCE, redirect exato, consentimento, code single-use, issuer/audience; refresh rotacionado; reuse invalida família |
| MCP-A04 | Serviço completo | Segredo válido troca token; inválido/expirado/revogado negado; brute force limitado |
| MCP-A05 | Audience/ator forjado | Token de outro serviço, integração declarada e workload sem delegação não autorizam mutação |
| MCP-A06 | Pausa, expiração, revogação e perda de papel | Access/refresh emitidos antes não permitem novas ações; reativação só para pausa; transferência auditada |
| MCP-A07 | Escopo/recurso | Negar publicação, saldo, taxonomia, destaque, credencial e draft alheio mesmo em REST direto |
| MCP-D01 | Criação válida/inválida | Draft apenas; defaults backend; opções/taxonomia/datas validadas; rollback sem side effects |
| MCP-D02 | Retry após commit e resposta perdida | Mesmo ID/revisão, sem draft/cota/evento de domínio duplicado |
| MCP-D03 | Idempotency key com payload diferente e token revogado | Conflito; resposta antiga não contorna autorização atual |
| MCP-D04 | Edição humana e agente simultâneos | Revisão antiga falha, sem perda de conteúdo; cobrir editor web existente |
| MCP-D05 | Publicação e edição simultâneas | Serialização segura, definição assinada intacta, agente não edita estado publicado |
| MCP-D06 | Revogação versus commit | Ordem transacional determinística; nada novo após revogação ganhar disputa |
| MCP-E01 | Submissão, devolução, aprovação/rejeição | Snapshot, parecer humano/versionado; agente bloqueado em revisão/aprovado/rejeitado |
| MCP-E02 | Fonte inacessível/política antiga | Pendência real, aprovação não aceita item obrigatório pendente; nova revisão quando necessário |
| MCP-E03 | Edição após aprovação | Aprovação invalidada; comparação de versão/hash; publicação de mercado de integração retorna 409 editorial_approval_required sem aprovação humana atual |
| MCP-Q01 | Última unidade concorrente e reinício | Apenas um draft confirma; contadores não somem; leases vencidos recuperam |
| MCP-Q02 | Limite reduzido e meia-noite São Paulo | Sem consumo excedente; regra temporal correta; retry idempotente não consome draft |
| MCP-L01 | Leitura, sucesso, erro e negação | Log central correlacionado por tool/execução/integração; HTTP 200 com erro marcado falha |
| MCP-L02 | Falha de log versus auditoria | Log técnico falho não aborta principal; evento transacional falho aborta mutação |
| MCP-L03 | Segredos em erro/contexto/URL | Nenhum segredo em DB, log, cache, analytics ou HTML posterior; redaction também de mensagens livres |
| MCP-L04 | MCP sem banco e API indisponível | Ingestão autenticada; spool limitado/deduplicado; resultado degradado explícito |
| MCP-L05 | Retenção e filtros | Purge técnico não apaga ficha/autoria; filtro retorna somente registros esperados |
| MCP-R01 | Busca paginada/parcial e métricas ausentes | Cobertura explícita; sem duplicidade garantida com catálogo incompleto; ausência não vira zero |
| MCP-S01 | Prompt injection/XSS/URL maliciosa | Sem escalação, execução arbitrária ou renderização ativa; sem fetch backend implícito |
| MCP-O01 | Container/grants/proxy | MCP sem segredos de DB/KMS/MFA; migrations com role correta; HTTPS/discovery/transporte funcionais |
| MCP-O02 | Regressão | Login/MFA, Admin Ops, criação/edição/publicação humana, integridade, bots existentes e daemon preservados |
| MCP-X01 | Cliente MCP real local | Descoberta/tools, auth, schemas, leitura, escrita e erros comprovados |
| MCP-X02 | Dot real | OAuth, leitura, draft, recorrência/renovação, revogação e correlação em ambiente autorizado |

Rodar checks Django, migrations, snapshot OpenAPI, lint/testes do adaptador, integração focada e suíte de regressão relevante. Conferir UI real de cadastro/credencial/pausa/revisão/atividade. Flutter só exige novos testes específicos se o contrato consumido mudar; preservar smoke/checagem de compatibilidade existente.

Mocks cobrem indisponibilidade, não comprovam integração Dot. Registrar comando, ambiente, resultado e pendência. Sem credenciais/acesso externo, concluir partes independentes e marcar homologação externa pendente; não alegar feature implantada. PR/produção seguem autorização do pedido concreto.

## Revisão 1.1 — WFLOW-20261007-MCP-REVIEW-GATE-001

- MCP-D06: slug derivado do título, acentos normalizados, colisões com sufixo, replay e estabilidade após edição.
- MCP-E04: preparação, em revisão, devolvido, rejeitado, aprovação/hash/política antigos e conteúdo divergente não publicam. Aprovação humana atual publica com definição assinada; mercado humano legado preserva seu contrato.
- MCP-U03: Integrações segue estrutura de Agentes IA; criação separada, gestão preservada e auditoria centralizada. Publicar versão aprovada não salva alterações do formulário. Data UTC é exibida no fuso selecionado sem deslocar o instante.

- MCP-E05: humano retoma preparação/ficha/submissão sem executor, com nova revisão e evento de autoria humana. Sem MFA/ator técnico/usuário comum, versão antiga, referências inválidas e mercado publicado recusados. Pendências não são satisfeitas automaticamente; aprovação ainda exige verificação independente. UI inclui CSRF, PRG e preserva ficha ao mostrar erro.

- MCP-E06 (v1.3): uma ação humana confere ficha e registra parecer, inclusive preparação, sem submissão humana prévia; ficha/snapshot/parecer/eventos são atômicos. Aprovação inválida reverte tudo, versões/hashes antigos negados. UI sem status+atestação duplicados nem verificações humanas pré-marcadas; publicar separado.

### MCP-UI-MARKETS — origem e revisão na lista

Mercados de integração exibem origem MCP, os cinco estados editoriais traduzidos e link direto à ficha pelo ID. Mercado sem identidade editorial não recebe marcação de agente ou link de revisão. Status do mercado e ações de edição/integridade permanecem disponíveis. Evidência: quatro testes em tests.test_mcp_publication_ui (incluindo os dois de publicação existentes), exit 0; Chrome DEV confirma draft #5 em revisão e mercados legados sem marcação.

### MCP-UI-REVIEW-002 — evidências e bloqueios claros

Sem seleção repetida de fontes por critério; sugestões editáveis na evidência, mapeamento exato de URLs ao catálogo e conferência independente por fonte. Aprovação com todas as marcações mas lacunas preenchidas falha atomicamente, informa motivo e mantém decisão/textos/marcações. Remover citação exigida bloqueia; corrigir ficha permite aprovar em uma ação. Mercados usa cabeçalho Admin Ops e tabela de seis colunas com destaque junto do título e tipo junto da categoria; mantém origem/estado/link MCP.

Resolução de lacunas: critérios marcados sem confirmação continuam bloqueados; confirmação explícita permite remover o bloqueio de gaps, mas não contorna fonte obrigatória ausente. Verificar rollback, texto/confirmação preservados no erro, aprovação em uma ação após correção e snapshot anterior com lacunas originais.

Editor pós-publicação: open/locked/resolved/sealed não exibem bloqueio ou botão de publicar novamente; canceled informa cancelamento. Draft/scheduled apresentam bloqueio ou publicação aprovada conforme parecer. Evidência: tests.test_mcp_publication_ui, sete testes/0,021 s; Chrome DEV mercado Tesla aprovado revisão 11 e já publicado, sem escrita.

O indicador de publicação/estado deve ser visível também em mercados legados sem MCP, sem inventar ficha ou impor aprovação editorial a esses mercados. Cobrir estados publicado/cancelado e ausência de gate em draft/scheduled legados. Oito testes UI passaram em 0,021 s; DEV EV conferido somente leitura.

## Ampliação de aceite — revisão universal 1.4

- Criação administrativa e conversão de sugestões geram ficha humana pendente; sem integração fictícia. Todos os mercados aparecem na revisão, sem selo IA na origem humana.
- Publicação humana/MCP/agendada sem aprovação atual, devolvida/rejeitada, policy/hash/revisão antigos ou configuração editada é bloqueada antes da assinatura.
- Prazo ausente/passado/sem timezone, fuso inválido ou modo incompleto bloqueiam ambos os modos; configuração válida com aprovação permite publicar; manual permite lock operacional.
- Migração é aditiva/idempotente; não altera mercado/opções/previsões/provas nem aprova legados. Parecer publicado não muda lifecycle; terminal é somente leitura.
- Verificar real SDK OAuth+serviço, cotas/concorrência/idempotência/revogação/grants e regressões payout/refund/reputação/provas. [Evidências locais](universal-editorial-20261007.md).

## Fechamento e rollout produtivo

- Deploy padrão inclui override MCP e fragmento Caddy; rotas internas são bloqueadas antes do roteamento público /api. Adaptador permanece sem ORM/DB/credenciais humanas, em workload e rede próprios.
- Primeira instalação desligada, arquivos exclusivos 0600 e workload gerado sem divulgação. Habilitar, desabilitar e repetir deploy preservam workload; configurações divergentes falham sem sobrescrita. Backup/ativação explícitos no runbook; bootstrap não cria integração/credencial de agente ou mercado.
- PR para main executa CI; deploy somente em main após testes. Validar Compose/Caddy/imagem localmente e registrar HTTPS/Actions/roles/dados após deploy autorizado. Regressão local não aprova Dot.
- Parecer novo deve informar gate universal; revisão inválida no POST web conserva campos, retorna erro legível e não chama update. Fichas/decisões históricas não são reescritas para corrigir metadados.

Evidências: [fechamento e pendências](mcp-closeout-20261007.md).

## Regressão OAuth Codex

- Registro com payload real Codex (`application_type: native`): 201, redirect persistido, metadados desconhecidos omitidos; nenhum token ou permissão emitido.
- Extras desconhecidos não contornam validação de redirect, grant, auth method e response type. Schemas editoriais/admin seguem estritos.
- Discovery do adaptador anuncia issuer textual idêntico ao AS/iss, usando a mesma canonicalização inicial sem barra final da FastAPI; scopes completos e challenge canonical preservados, /mcp sem token continua 401.
- Fluxo SDK completo PKCE/code/refresh/tools executado com metadados nativos; CLI real local avança para autorização humana. Produção e login humano do operador precisam de evidência após rollout aprovado.
