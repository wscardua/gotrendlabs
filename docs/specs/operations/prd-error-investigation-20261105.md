# Investigação dos ERROR de PRD — 05/11/2026

Workflow: `WFLOW-20261105-PRD-ERROR-INVESTIGATION`. Investigação e propostas concluídas; implementação e deploy não executados.

## Conclusão

O incidente observado foi uma saturação transitória de conexões PostgreSQL, acompanhada de timeouts na comunicação Django → FastAPI. O fallback ORM do detalhe de mercado consultou o mesmo banco saturado e transformou indisponibilidade da API em páginas 500. A coleta de analytics também retornou 503. Há evidência direta da saturação; a contribuição exata de cada processo e a origem da rajada ainda não estão demonstradas.

Não se trata de 11 falhas independentes: existem 11 registros ERROR, correspondentes a 5 respostas web com falha, 1 exceção de request FastAPI e 5 registros adicionais do logger Django. A request FastAPI pode corresponder a uma das requests web; não há correlação ponta a ponta suficiente para deduplicar essa última associação.

## Escopo e método

- Conta AWS e instância conferidas com STS/SSM; RDS `gotrendlabs-prod-db`, região `us-east-1`.
- Consultas ao banco em transações `READ ONLY`, com `statement_timeout`, sem alteração de configuração, dados, serviços ou segredos. Consultados logs técnicos, limites de conexão, atividade agregada e uso de TLS.
- Evidências complementares: eventos RDS, arquivo `error/postgresql.log.2026-11-05-05`, métricas CloudWatch de um minuto, estado dos containers e reflog do checkout produtivo.
- Janela solicitada ao log técnico: 7 dias. Janela realmente disponível na primeira coleta, às 11h00 de Brasília: 04/11 11h00 até 05/11 10h59, com 5.760 registros. A configuração efetiva é **1 dia** de retenção.
- Checkout produtivo atual: `2c799f621ff4a1d99f1d677335e58fec28d00295`, atualizado às 09h10 de Brasília; containers de aplicação criados aproximadamente às 09h14. Reflog aponta `9d8933b` como checkout anterior, desde 03/11 17h51. Portanto, o incidente precede o deploy de hoje. Reflog não é prova independente do conteúdo da imagem anterior.
- Os arquivos de conexão, detalhe web, cliente HTTP, logs e `main.py` não têm diferenças entre `9d8933b` e `2c799f6`. As referências de linha abaixo usam `2c799f6`.
- O workspace local está em outra revisão e contém mudanças preexistentes. Foram consultadas também specs da revisão produtiva, inclusive MCP já implantado, para evitar conclusões baseadas apenas no estado local mais antigo.
- Ambiente virtual existente conferido: `.venv/bin/python`, Python 3.9.6. Nenhum ambiente foi criado ou pacote instalado. Não houve teste de carga nem reprodução de saturação em PRD.

## Evidências

Horários abaixo em `America/Sao_Paulo` (UTC−3); timestamps originais preservados nos identificadores de coleta e logs AWS.

| Evidência | Resultado |
| --- | --- |
| ERROR técnicos | 11, entre 02h58m52s e 02h58m58s de 05/11 |
| Web | 3 respostas 500 em detalhes de mercados; 2 respostas 503 em `POST /analytics/events/` |
| FastAPI | 1 `OperationalError` / 500 em `GET /markets/{slug}` |
| PostgreSQL | 41 FATAL por conexões esgotadas entre 02h58m54s e 02h58m57s: 22 vagas reservadas `pg_use_reserved_connections`, 7 `rds_reserved`, 9 SUPERUSER e 3 `too many clients` |
| TLS no log RDS | 3 recusas adicionais de conexão sem criptografia, na mesma janela; nenhuma conexão sem TLS bem-sucedida demonstrada |
| Limites atuais SQL | `max_connections=79`, `reserved_connections=2`, `superuser_reserved_connections=3`; existem ainda reservas próprias do RDS |
| CloudWatch `DatabaseConnections` | 2 antes, 86 na amostra de 02h58, 3 às 02h59; a métrica gerenciada não deve ser interpretada como contagem SQL exata de slots utilizáveis |
| Memória livre RDS | Cerca de 149 MiB às 02h57 → 35,7 MiB às 02h58 → 152 MiB às 02h59 |
| CPU RDS | 7% às 02h58 e 16,8% às 02h59; créditos disponíveis. As amostras não indicam esgotamento sustentado de CPU |
| Eventos RDS consultados | Somente backups; o backup de hoje começou às 05h55, fora do incidente. Sem evento de reinício/failover na janela consultada |
| Estado posterior | RDS disponível; containers em execução, MCP healthy; nenhum ERROR/CRITICAL técnico retido após 03h00 até a consulta final |

IDs úteis: `415280`/`415326` (analytics 503), `415328`/`415357`/`415360` (stacks Django), `415350`/`415359`/`415362` (web 500), `415371` (FastAPI). Não foram copiados tokens, cookies, emails, IPs de visitantes ou contextos brutos para este relatório.

Na janela 02h58–03h00 foram persistidos 142 logs de requests web e 174 da API. Entre as rotas: 50 detalhes web, 24 páginas de integridade, 101 leituras API de mercado e 51 registros API de visualização. O segundo com mais conclusões de requests web teve 27 registros; isso mede finalizações registradas, não chegadas nem concorrência exata.

138 requests web compartilham um único User-Agent não identificado como automação pela classificação simples, com 21 IPs distintos registrados. Isso é compatível com coleta automatizada, mas não prova autoria, ataque ou robô específico. O User-Agent automatizado na API inclui o cliente HTTP interno Django e não identifica diretamente o visitante externo. Não bloquear agentes/IPs com base apenas nessa classificação.

## Correções propostas, em ordem

### 1. Alta — limitar concorrência e orçamento de conexões

**Confirmado:** `apps/api/backend_api/db.py:49–52` abre conexão nova a cada `get_connection()`, sem pool ou limite global nessa função. Django, serviços backend chamados pelo web, daemon e worker também precisam entrar no orçamento; limitar apenas a FastAPI não limita toda a aplicação. O incidente real comprova que a capacidade produtiva foi excedida, mas não comprova vazamento permanente.

**Proposta:** definir orçamento total inferior às vagas disponíveis, com margem operacional, e limites por processo/role. Introduzir gerenciamento de conexões com tamanho e fila limitados, timeout curto de aquisição/conexão e devolução garantida após commit/rollback. Aplicar controle de concorrência na entrada web/API para que o excedente receba indisponibilidade previsível. Dimensionar com ensaio em PostgreSQL isolado, considerando os dois workers Django e todos os processos auxiliares. Separar credenciais/roles; preservar a fronteira de senha e a role exclusiva FastAPI.

Pool limitado é um mecanismo disponível no [Psycopg](https://www.psycopg.org/psycopg3/docs/api/pool.html); exige configurar também espera/fila, não apenas quantidade de conexões. Não aumentar `max_connections` isoladamente: houve pressão de memória no mesmo evento. Redimensionamento RDS pode ser reavaliado após medição, sem mudança de capacidade nesta investigação.

**Aceite:** rajada controlada não ultrapassa o orçamento; fila e latência limitadas; recuperação após a rajada; rollback/devolução em exceções; zero mistura de roles; nenhuma reaplicação automática de mutação com resultado incerto. Definir contrato previsível de indisponibilidade, preservando códigos existentes específicos de manutenção mobile e OAuth.

### 2. Alta — remover o fallback ORM de indisponibilidade no detalhe web

**Confirmado:** `apps/web/django/markets/views.py:259–265` captura `AuthAPIError` e chama `local_market()`. `core/domain_client.py:279–291` só trata mercado inexistente; a falta de conexão escapa. As três stacks mostram exatamente timeout HTTP → fallback → erro PostgreSQL.

**Proposta:** detalhe web trata separadamente 404 e indisponibilidade; retorna página 503 segura sem nova consulta ao banco nem processamento de contexto dependente de banco/API. Remover o fallback de leitura direta desse fluxo e revisar consumidores equivalentes, como integridade, sem alegar que todos falharam neste incidente. Preservar API como fonte de verdade e não criar caminhos de legado. Não incrementar visualização quando o detalhe não foi entregue com sucesso.

**Aceite:** API timeout/503 e banco indisponível produzem 503 renderizável; nenhum `local_market()` é chamado; 404 continua 404; mercado draft não vaza; visitantes e usuários autenticados recebem estado coerente. Testar também context processors e middleware usados pela página de erro.

### 3. Média — reduzir custo e dependência dos logs técnicos

**Confirmado no código:** cada `log_system_event()` consulta retenção com uma conexão (`system_logs/services.py:44–56`) e grava com outra (`:155–193`). FastAPI chama esse serviço síncrono diretamente no middleware assíncrono (`main.py:542–605`). A persistência falha silenciosamente quando o banco está indisponível. Isso acrescenta conexões e trabalho ao caminho da request; sua parcela exata no pico não foi medida.

**Proposta:** cache curto e invalidável da retenção; escrita técnica fora do event loop, com concorrência, fila e tempo limitados; registro sanitizado em stderr quando persistência falhar, sem recursão nem novas tentativas imediatas contra o banco saturado. Preservar registros técnicos exigidos pela spec. Exportação externa durável exige evolução da spec, pois pipeline externo está fora do escopo atual.

**Aceite:** falha/timeout do logger não impede resposta; quantidade de conexões por log reduzida; atualização da retenção respeitada; nenhuma recursão ou segredo em stderr; event loop responsivo. Auditoria administrativa/transacional de mutações continua obrigatória e não passa a ser descartável.

### 4. Média — recuperar capacidade de investigação e correlação

**Confirmado:** retenção efetiva de 1 dia; default documentado de 90 dias, mas a spec permite configuração de 1 a 3650. É uma escolha operacional inadequada à investigação longa, não evidência de defeito no prune. A arquitetura de scheduler já registra essa lacuna. Logs de exceção Django estão sem `request_id`; o cliente HTTP geral não encaminha o identificador web para a API.

**Proposta:** planejar alteração operacional da retenção técnica para 90 dias, dimensionando armazenamento e índices; valores já apagados não serão recuperados por essa alteração. Propagar correlação web → API e aos registros do logger, preservando IDs gerados internamente nas rotas privadas MCP/OAuth. Alertar sobre utilização de conexões, memória e 5xx, com limites derivados da capacidade real; alerta externo exige complementar o escopo da spec.

**Aceite:** erro de uma request é rastreável entre camadas; entradas externas não falsificam correlação privada; prune respeita o prazo; nenhuma alteração no ledger append-only nem na auditoria de domínio. Não confundir 11 linhas com 11 incidentes.

### 5. Baixa — tornar TLS explícito em todas as conexões produtivas

**Confirmado:** três recusas `no pg_hba.conf ... no encryption` coexistem com saturação. Configuração de conexão inspecionada não define `sslmode` explicitamente. A consulta de investigação usou TLS; não foi inspecionado todo o ambiente secreto.

**Hipótese:** tentativa sem TLS após falha SSL pelo modo padrão `prefer`; é o comportamento descrito pelo [PostgreSQL 16](https://www.postgresql.org/docs/16/libpq-connect.html), mas a configuração efetiva de cada processo precisa ser validada sem expor credenciais.

**Proposta:** TLS explícito, preferencialmente `verify-full` com CA RDS distribuída e hostname correto, em Django e psycopg. Não alterar `pg_hba` nem desabilitar SSL. Testar certificado válido, hostname incorreto e CA inválida. Essa medida elimina ambiguidade/ruído e não resolve a saturação por si só.

## Analytics, MCP e mobile

- Analytics: os dois 503 são compatíveis com o timeout de 3 segundos em `accounts/api_client.py:447` e o repasse de erro em `core/analytics_views.py:collect`. A causa individual de cada timeout não está provada pelo log web isolado. Não trocar falha por 200 fictício; qualquer reenvio deve preservar `event_id`, limite de tentativas e contrato idempotente. Nenhuma conclusão de domínio deve ser inferida a partir da coleta.
- MCP: nenhuma ferramenta/schema/permissão nova é necessária para a investigação. `apps/mcp/server.py:218–282` já mapeia falha de dependência para `dependency_unavailable` e timeout de certas mutações críticas para `operation_indeterminate`. As correções de conexão/erros precisam testar o adaptador, preservando scopes, autorização, auditoria transacional, chaves e recibos de replay. Nunca transformar resultado indeterminado em rollback presumido nem repetir com chave nova. O MCP continua sem acesso direto ao banco.
- Mobile: não há erro mobile identificado nas evidências coletadas. Alterações futuras de resposta de indisponibilidade devem testar o consumidor Flutter de 503 sem confundi-lo com `mobile_maintenance`, sem apagar sessão e sem reenvio automático de previsões/mutações. Mudanças de payload exigem contrato/OpenAPI e consumidores atualizados diretamente.
- Retenção, TLS e otimização interna do logger não exigem alteração de ferramentas ou schemas MCP se contratos observáveis forem preservados; a auditoria de mutações MCP não pode ser enfraquecida pela otimização técnica.

## Specs e governança

Consultadas: FEAT-OPSLOG-001, FEAT-ANALYTICS-001, arquiteturas backend/web/scheduler, contrato `agent-integrations.md`, workflow/checklist e código dos consumidores. Skills aplicadas: workflow-governor, software-architect e architecture-guard. A fronteira proposta mantém domínio na FastAPI, web como apresentação, banco como persistência e MCP como adaptador autorizado.

Antes da implementação, registrar desenho do orçamento por processo e decisão sobre pool/limite de entrada; criar ADR se introduzir infraestrutura intermediária ou alterar fronteira. Atualizar spec de logs para pipeline/alertas externos se essa opção for adotada. Nenhuma regra ou estado de implementação de feature foi alterado nesta entrega, portanto não há promoção de spec, atualização de OpenAPI ou changelog de implementação.

## Limitações e próximo passo

O log técnico usa o próprio banco afetado e pode perder registros durante saturação; as contagens são evidência mínima, não total garantido de falhas. Retenção limita retrospectiva; métricas de um minuto não capturam todas as rajadas; atividade atual não reconstrói quem ocupava cada conexão às 02h58. Não há evidência suficiente para concluir ataque, vazamento persistente, perda financeira ou falha de integridade. Essas hipóteses não foram declaradas como fatos.

Próximo ciclo: implementar primeiro resposta web segura e orçamento de conexões, depois otimizar logs/correlação; executar os testes acima em ambiente isolado antes de propor rollout. Não foram executados testes funcionais porque não houve alteração de runtime; houve inspeção do código das duas revisões e coleta produtiva somente leitura. Alterações locais preexistentes preservadas; sem commit, PR, restart ou deploy.

Referências SSM da coleta: `1e18794e-ae1a-4f28-b3d8-5b26690d1002` (agregados), `d5cdc620-234f-4344-8a5d-422a36ef9644` (limites/stacks resumidas), `71b3727e-be6f-4171-8524-66e7a2c4749c` (tráfego, ausência de novos erros e reflog). A leitura RDS retornou `AdditionalDataPending=false`; o aviso genérico da ferramenta sobre limite de linhas não altera esse indicador específico do serviço.
