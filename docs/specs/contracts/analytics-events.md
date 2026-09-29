# Contrato de eventos analytics (`FEAT-ANALYTICS-001`)

## Escrita

`POST /analytics/events` recebe `AnalyticsBatch` com `visitor_id`, `session_id` e entre 1 e 20 eventos. Cada evento possui `event_id` UUID, `view_id` UUID opcional, `name`, `occurred_at`, `screen_key`, `target_key` e `properties`. A FastAPI escolhe `platform`, `user_id`, `actor_type`, `auth_state` e `received_at`; headers de cliente ou corpo nao podem se passar por conclusao de dominio.

Eventos permitidos sao definidos em `apps/api/backend_api/analytics.py:EVENT_PROPERTIES`. O conjunto de propriedades e fechado. Texto livre de busca/formulario, email, token, URL com query e IP bruto nao sao aceitos como propriedades. Um `event_id` repetido retorna `accepted: 0`; visualizacao e sessao nao podem pertencer a outro identificador. Clientes devem enviar melhor esforco, sem bloquear o produto.

A web envia via `POST /analytics/events/` no Django, com CSRF. Django repassa token da sessao e, quando configurado, o IP visto por um proxy confiavel usando segredo interno. Mobile chama a API diretamente.

## Leitura staff

`GET /admin/analytics/summary` exige sessao staff/superuser com MFA. Filtros: `days` em `1|7|30|90`, `platform` em `all|web|mobile`, `audience` em `all|anonymous|authenticated`, `region` e `city`. Resposta: `totals`, `daily`, `screens`, `geography`, `regions`, `cities`, `geo_daily`, `trend_region`, `region_daily`, `sources`, `markets`, `funnel`, `abandonment`, `authenticated_funnel`, `retention`, `domain_totals`, `insights`, `coverage`, `last_ingestion`, `collection_24h`, `last_geolite_run`, `geolite_file` e horario de geracao.

`funnel` conta sessoes que passaram pelas etapas observadas em ordem temporal (visita, abertura de mercado, ticket, clique em confirmar); `authenticated_funnel` conta contas que iniciaram ticket e fizeram uma primeira previsao persistida no mesmo mercado em ate sete dias. `domain_totals` e global e nao obedece aos filtros de plataforma, publico e geografia. Cada insight inclui `kind`, `title`, `detail` e `sample`. O dashboard deve exibir essa diferenca explicitamente.

`regions` e `cities` trazem rankings de sessoes e contas em UFs/cidades brasileiras no recorte. `geo_daily` conta sessoes diarias com pais/estado identificado e cobertura percentual; `region_daily` conta atividade diaria da UF filtrada ou da UF lider, identificada por `trend_region`. Uma sessao pode aparecer em varios dias. `abandonment` agrupa uma jornada por sessao/mercado, com `started`, `engaged`, `submit_clicked`, `eligible`, `abandoned_before_choice` e `abandoned_after_choice`. As duas contagens de abandono exigem inatividade da sessao por pelo menos 30 minutos; `submit_clicked` nao representa persistencia de previsao. Novos eventos de cliente continuam sujeitos ao catalogo fechado.

`last_ingestion` e a ultima remessa concluida (`completed_at`, `platform`, `received`, `accepted`, `duplicates`, `new_session`) ou `null`; `collection_24h` agrega eventos humanos, sessoes e visitantes recebidos nas ultimas 24 horas e o horario do ultimo evento humano. `last_geolite_run` e a ultima execucao registrada do importador GeoLite (`status`, horarios e metadados ou `error_code`) ou `null`; `geolite_file` informa estado do arquivo ativo (`ready|not_configured|missing|invalid`) e, quando pronto, versao, tamanho, nós de busca e modificacao. Estes campos sao operacionais e globais, sem filtros de relatorio.

`retention` e global e independente dos filtros do endpoint. Contém `timezone: America/Sao_Paulo`, `since`, `registered` e `visitors`. Cada público possui `totals` e `cohorts` semanais; para `d1`, `d7` e `d30`, cada ponto informa `eligible`, `returned` e `rate` (percentual inteiro ou `null` se o denominador é zero). Atividade e página/tela vista no dia exato. Contas entram pela data de cadastro e retornam com `user_id` autenticado; visitantes entram pela primeira visita anônima e retornam em outra sessão anônima do mesmo `visitor_id`. Só dias de retorno já completos são elegíveis; primeiro dia parcial e período anterior à coleta não são inferidos.

## Evolucao

Nomes, gatilhos, propriedades e definicoes de funil mudam apenas com versao do catalogo e spec atualizada. Novos eventos de conclusao exigem persistencia do lado do backend e deduplicacao ligada a entidade autoritativa.
