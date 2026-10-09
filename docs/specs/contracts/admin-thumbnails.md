# Contrato administrativo de thumbnails

Bearer staff/superuser com MFA vigente em todas as rotas.
- POST /admin/markets/{slug}/thumbnails: request_id UUID e title (1–240), summary (1–4000), category/subcategory (1–80), event (até 80). Retorna job. Sem outros campos, sem mutação de mercado. Retransmissão da mesma identidade/contexto retorna mesmo job; conflito 409. Limites 429, disabled 503, não draft 409.
- GET /admin/markets/{slug}/thumbnails: recupera job ativo ou último do operador, sem geração.
- GET /admin/markets/{slug}/thumbnails/{request_id}: estado, snapshot_hash, snapshot, candidate_id quando succeeded, expires_at, mensagem simples. Sem arquivo/base64/segredos.
- GET /admin/markets/{slug}/thumbnails/{request_id}/preview: PNG privado, no-store, staff/MFA, vínculo draft e validade. Django faz proxy autenticado sem token no navegador.
- PATCH existente acrescenta thumbnail_candidate_id UUID e thumbnail_expected_image_url. Confirma sob lock do mercado: succeeded, arquivo válido, mercado correto, expiração, URL anterior e expected_revision. Deriva image_url, nunca usa URL de candidata do navegador. Conflitos 409. Rollback mantém URL persistida; cópia pública órfã é removida por limpeza após grace period.

Publicação existente mantém gate editorial. Resultado tardio somente afeta fila; nunca mercado. Queued é cancelado se draft/operador não elegível na execução; running incerto não é repetido. Expiração de sessão interrompe polling/preview; reautenticar recupera status e não gera novamente.

## Configuração administrativa (v1.1)

GET/PUT `/admin/thumbnail-settings`: staff/MFA vigente; payload completo dos parâmetros `thumbnail_enabled`, `thumbnail_model`, `thumbnail_region`, `thumbnail_aspect_ratio`, `thumbnail_timeout_seconds`, `thumbnail_operator_limit`, `thumbnail_market_limit`, `thumbnail_global_limit`, `thumbnail_period_hours`, `thumbnail_retention_hours`. Sem credenciais/endpoints editáveis. Modelo validado por allowlist de adapters nativos oficialmente documentados; região Oregon; proporções 3:2/16:9/1:1. Campos extras e valores inválidos: 422 sem mutação. PUT audita ator/mudanças e persiste atomicamente. UI Django usa sessão/CSRF para adaptação; novos jobs congelam parâmetros do provedor. Histórico/auditoria e jobs antigos preservados.


### Execução interna semântica (v5)

Sem alteração do payload/shape público: um job de mercado reserva até uma chamada textual limitada e uma imagem. Persistir orchestrator e parâmetros próprios GTL_THUMB_PLANNER_* no provider_config; usage privado contém checkpoints e IDs/uso por etapa, brief final e sujeitos. Campos privados e raciocínio do modelo não são enviados/persistidos. Nenhuma ferramenta habilitada, store=false, sem retry/fallback. Checkpoints revalidam autorização/claim/lease; falha textual impede imagem. Polling não revela brief ou dispara chamadas. Configuração de modelo de imagem segue endpoint/painel existente; parâmetros textuais independentes são configuração ambiental da API. V3/v4 não são reinterpretadas ou repetidas; candidatas concluídas preservadas.
