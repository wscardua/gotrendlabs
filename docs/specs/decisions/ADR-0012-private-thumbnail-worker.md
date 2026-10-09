# ADR-0012 — fila persistente e thumbnails privadas

Data: 2026-10-09. Status: aceita no escopo autorizado.

Worker dedicado usa credencial FastAPI e PostgreSQL com SKIP LOCKED/token de claim; não reutiliza daemon de fechamento/comunicações. Advisory lock transacional global apenas na reserva de cotas; índices impedem duas ativas. Nunca segurar transação durante chamadas ao provedor. Jobs running com lease vencido tornam uncertain, sem replay pago.

Volume thumbnail_private compartilhado worker RW/FastAPI RO, não montado no proxy/Django. FastAPI recebe escrita apenas no subdiretório público market_thumbnails para promoção validada; worker também monta esse subdiretório para prune. Volumes e mounts explícitos em Compose. Cópia exclusiva/nomes UUID, arquivo privado validado, DB deriva URL; órfãs públicas após rollback ficam sujeitas a prune conservador com lock global de promoção/limpeza. Imagens vinculadas nunca são apagadas.

Orquestrador gpt-5.4-mini, imagem gpt-image-1.5, medium, 1536x1024 PNG: opção suportada oficialmente, qualidade adequada com custo intermediário e resolução fixa conservadora; latência/acesso/qualidade reais ainda não medidos. Ambos configuráveis separadamente dos comentários; sem fallback. OpenAI Responses tool action=generate, tool_choice=image_generation, store=false, max_tool_calls=1; saída image_generation_call.result Base64. Sem SDK retries. HTTP timeout/5xx/transporte são uncertain. Não há alegação de custo faturado nem idempotência do provedor.

Fontes oficiais consultadas em 2026-10-09: [modelo mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini), [tool](https://developers.openai.com/api/docs/guides/tools-image-generation), [GPT Image 1.5](https://developers.openai.com/api/docs/models/gpt-image-1.5). Registro histórico da decisão inicial, substituída abaixo; acesso OpenAI e geração paga não verificados.

## Revisão Bedrock autorizada (v1.1, 2026-10-09)

Substitui a escolha OpenAI acima: chamada única Bedrock Runtime InvokeModel, Core v1:1 default e adapters compatíveis SD3.5 Large/Ultra em us-west-2. Modelos textuais gpt-oss-20b não geram imagens e Bedrock não oferece image_generation. Parâmetros não secretos persistem em SiteConfig via endpoint FastAPI e painel independente; snapshot no job impede mudança de execução/custo após enfileiramento. Bearer AWS_BEARER_TOKEN_BEDROCK só no executor; HTTP sem retry, sem fallback e endpoint construído de região validada. Legados com provider OpenAI encerram failed/unsupported_provider sem consumo. Cotas DB com kill switch de ambiente; limites opcionais de ambiente apenas restringem, não ampliam DB. Biblioteca httpx existente evita SDK/acoplamento ao esquema de comentários. Fontes: [Core](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-diffusion-stable-image-core-text-image-request-response.html), [SD3.5](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-diffusion-3-5-large.html), [Ultra](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-diffusion-stable-ultra-text-image-request-response.html). Evidência posterior no fechamento: duas solicitações Core succeeded no DEV; qualidade visual sistemática, modelos alternativos e acesso produtivo pendentes.

## Ciclo do deploy (fechamento, 2026-10-09)

Arquivo de segredo do executor instalado inclui profile thumbnails no deploy, independentemente do kill switch: manter o worker atualizado mesmo pausado. Parar também o executor durante migrations; falha deixa escritores parados para recuperação explícita. Preparar somente o diretório market_thumbnails antes do mount subpath, usando UID/GID da imagem e preservando arquivos existentes. CI exige build completo antes do merge; smokes produtivos não substituem autorização de consumo nem homologação visual.


Direção vigente para mercados v5: [ADR-0014](ADR-0014-semantic-thumbnail-brief.md) acrescenta interpretação textual sem presets antes da imagem, com configuração própria/checkpoints. A chamada única de imagem continua válida para jobs v2 históricos e cada variante de badges.
