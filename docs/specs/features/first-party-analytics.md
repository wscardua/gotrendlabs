---
id: FEAT-ANALYTICS-001
titulo: "Analytics proprio web e mobile"
versao: 0.4
status_spec: aprovada
status_impl: implementada_validada
ultima_atualizacao: 2026-09-29
origem:
  - conversa de produto de 2026-09-29
contratos_afetados:
  - analytics-events.md
dependencias:
  - FEAT-AUTH-001
  - FEAT-MOBILE-001
impacta:
  - backend-api
  - frontend-web
  - future-mobile
  - database
  - admin-ops
---

# Analytics proprio

## Objetivo

Medir navegacao e interacoes de visitantes e contas autenticadas na web e no mobile; mostrar estatisticas, geografia aproximada, funis e insights verificaveis no Admin Ops. A FastAPI valida eventos, identidade e calculos. Django apresenta a web e encaminha a coleta da mesma origem; Flutter e cliente JSON.

## Contrato da coleta

- `POST /analytics/events` recebe lote limitado de eventos (`event_id`, `session_id`, `view_id`, `name`, `occurred_at`, `screen_key`, `target_key`, `properties`) e devolve contagem de aceitos. IDs sao UUID; reenvio do mesmo `event_id` e idempotente.
- O catalogo de nomes/propriedades e fechado e versionado na FastAPI. Eventos de cliente nao podem declarar conclusao de dominio. O servidor determina `user_id`, `actor_type`, `auth_state`, `platform` e `received_at`.
- `visitor_id` e aleatorio por navegador/instalacao; `session_id` representa uma visita, e `view_id` uma visualizacao real. O mesmo navegador pode ser usado por mais de uma conta: a identidade e historica por evento. Visitante deslogado permanece anonimo.
- A rota web mesma origem exige CSRF; Django apenas passa o token validado e contexto de IP assinado para a API. O mobile usa a API diretamente. Falha de analytics nao bloqueia o produto.
- Nunca coletar senha, token, email, nome, texto de formulario, query completa de URL ou rota com token sensivel. Apenas parametros UTM limitados podem ser enviados como origem. Admin Ops nao e instrumentado; contas marcadas como bot ou staff nao entram nas metricas humanas padrao. Trafego anonimo automatizado ainda pode afetar contagens.
- Geografia vem de base GeoLite City local opcional. Resultado e aproximado e pertence a sessao, nao a residencia. Sem base ou localizacao conhecida, os campos ficam nulos.

## Catalogo inicial

Navegacao: `page_viewed`, `screen_viewed`, `navigation_clicked`, `market_card_viewed`, `market_card_clicked`, `market_filter_applied`, `search_performed`, `scroll_reached`.

Fluxos: `signup_started`, `login_started`, `market_detail_viewed`, `prediction_started`, `prediction_option_selected`, `prediction_preview_viewed`, `prediction_submit_clicked`, `position_action_started`, `position_preview_viewed`, `share_started`, `link_copied`, `notification_opened`, `integrity_opened`, `contribution_started`, `wallet_opened`.

Conclusoes de dominio sao medidas por registros autoritativos existentes (usuarios, previsoes, comentarios, posicoes, sugestoes, feedback, recargas, badges), sem duplicar ledger/auditoria. Integracoes futuras podem emitir eventos no mesmo catalogo, com deduplicacao por origem.

## Dashboard

`GET /admin/analytics/summary` e exclusivo de staff com MFA. Aceita periodo limitado, plataforma, estado/cidade e publico. Devolve estatisticas, serie diaria, paginas/telas, mercados, origem, regiao, funil de primeira previsao e insights acompanhados de base numerica. Unicos de periodo sao calculados sobre IDs distintos no periodo, nao somando unicos diarios. Periodos incompletos e cobertura geografica sao explicitados.

A leitura geografica retorna estados e cidades do Brasil ordenados por sessoes, serie diaria de cobertura geografica e serie diaria da UF filtrada ou da UF mais acessada. O Admin Ops inclui SVG local das 27 UFs gerado a partir das malhas simplificadas oficiais do IBGE, com intensidade relativa e filtro por clique. O contorno permanece visivel sem JavaScript e a tabela preserva valores exatos. Cidade e UF sao estimativas de IP da sessao; ausencia de localizacao nao e convertida em local conhecido. A serie diaria conta sessoes distintas por dia e uma sessao ativa em dois dias aparece em ambos.

## Retenção de produto

A FastAPI calcula coortes D1, D7 e D30 em `America/Sao_Paulo`, independentemente dos filtros de navegação. Dn e a proporção que teve `page_viewed` ou `screen_viewed` no dia de calendário exatamente n dias após a entrada. Só coortes com o dia Dn completo entram no denominador. O primeiro dia parcial da coleta e cadastros anteriores à coleta são excluídos; o período de observação é limitado aos últimos 90 dias. A API devolve totais e coortes semanais com numerador, denominador e percentual, ou percentual nulo quando não há coorte madura.

Contas cadastradas usam `gotrendlabs_users.date_joined` como entrada e `user_id` autenticado em qualquer dispositivo para retorno, excluindo staff e bots. Visitantes usam `visitor_id` e a primeira visita anônima; retorno exige uma nova sessão anônima no mesmo navegador ou instalação. A passagem para conta cadastrada não é contada como retorno anônimo. O identificador de visitante não representa pessoa e pode ser reiniciado no logout. Retenção de uso não deve ser confundida com a política de armazenamento abaixo.

O funil de desistência agrupa eventos de `prediction_started`, `prediction_option_selected`/`prediction_preview_viewed` e `prediction_submit_clicked` por sessao e mercado. Uma jornada so entra na contagem de abandono depois de 30 minutos sem atividade na sessao. O dashboard distingue parada antes da escolha e apos a escolha, sem afirmar o motivo nem confundir clique com previsao persistida. As conclusoes continuam medidas no banco de dominio.

Django renderiza `/admin-ops/analytics/` usando somente esse contrato. A pagina mostra estados de vazio e erro, nao dados ficticios.

## Estado das cargas

A API mantém o resumo da última remessa `POST /analytics/events` concluída: horario, plataforma, eventos recebidos/aceitos/repetidos e criação de sessão. O painel mostra separadamente eventos humanos, sessões e visitantes recebidos nas últimas 24 horas e o horario do último evento humano. Esses números operacionais são globais e não obedecem aos filtros do relatório.

A atualização da GeoLite ocorre por comando backend explícito `python -m apps.api.backend_api.geolite_loader`, com arquivo local `.tar.gz` ou `.mmdb` e checksum SHA256 opcional. O comando valida a base City, instala o arquivo de modo atômico e registra sucesso ou falha em tabela própria, com horario, versão da base, tamanho, nós de busca e código de falha. O painel também inspeciona o arquivo ativo e distingue base pronta, ausente, inválida ou não configurada. Uma base presente sem execução registrada não é apresentada como carga concluída. Não há atualização automática da GeoLite nesta etapa.

## Retencao e evolucao

Eventos detalhados: 90 dias por padrao; retencao e purge backend configuraveis. Dados de auditoria, ledger e eventos administrativos nao participam do purge. Agregados, regras de insight, funis adicionais, fila offline mobile e catalogo ampliado seguem iteracoes por contrato; nao se deve afirmar cobertura onde a coleta nao esta instalada.

## Evoluções fora do escopo v0.4

- Gravacao de sessao, heatmap, GPS ou IP bruto no analytics.
- Fila offline duravel no mobile, funis personalizados e atribuicao exata de conclusao por tentativa. O agrupamento sessao/mercado nao distingue duas tentativas no mesmo mercado durante a mesma sessao.
- Controles de preferencia de coleta na UI e atribuicao anonimo→conta entre dispositivos.
- Integracao de terceiros para hospedagem ou coleta.

## Testes esperados

- Contrato: nomes/propriedades rejeitados, lote limitado e UUID idempotente.
- Integracao PostgreSQL: visitante anonimo, visualizacao, deduplicacao e leitura de resumo.
- Autorizacao: resumo staff protegido por autenticacao e MFA.
- Web: template e endpoint proxy com CSRF, sem incluir Admin Ops na coleta.
- Mobile: abertura de tela por navegacao real, sem emissao em rebuild/polling.
- Retenção: coortes maduras e imaturas, retorno em outra sessão anônima, retorno autenticado em outro dispositivo e exclusão de staff/bots.
- Geografia: contorno das 27 UFs sem JavaScript, filtros de UF/cidade e estado ausente da GeoLite.
- Operação: última remessa, volume de 24 h, atualização GeoLite válida/inválida e expurgo sem afetar ledger/auditoria.
- Regressao: suite Django e suite Flutter existentes.

## Aceite

- Coleta anonima e autenticada sem confiar em identidade enviada pelo cliente.
- Reenvio, lote invalido e evento desconhecido nao corrompem dados.
- Uma navegacao real gera uma visualizacao; rebuild/polling nao a duplicam.
- Admin sem MFA nao consulta relatorios.
- Filtros de plataforma, publico e geografia produzem numeros coerentes.
- Ranking e evolucao de UF/cidade respeitam os filtros; abandono so conta sessoes inativas por 30 minutos e conserva a diferenca entre clique e persistencia.
- Dashboard distingue zero dados de falha de coleta e mostra limites de estimativa geografica.
- Dashboard mostra última remessa e volume humano de 24 h; mostra última execução GeoLite separada do estado real do arquivo, inclusive quando uma atualização falha.
- Retenção D1/D7/D30 distingue coortes maduras, visitantes e contas; o mapa SVG mostra as 27 UFs sem depender de JavaScript para o contorno.
