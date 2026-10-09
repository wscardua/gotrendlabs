---
id: FEAT-THUMB-001
titulo: Thumbnails IA no editor Admin Ops
versao: 1.1
status_spec: aprovada
status_impl: parcial
ultima_atualizacao: 2026-10-09
origem: [pedido_usuario_20261009]
contratos_afetados: [admin-thumbnails.md, market-lifecycle.md]
dependencias: [FEAT-AUTH-001, FEAT-EDITORIAL-001, FEAT-MARKET-001]
impacta: [admin-ops, frontend-web, backend-api, database, scheduler-jobs]
---

# Thumbnails IA

Escopo autorizado: drafts existentes, geração de uma imagem usando title/summary/category/subcategory/event atuais, regeneração, seleção automática, desfazer, upload preservado e confirmação no salvamento existente. Não salvar/publicar na geração. Sem prompts, galeria, batch, MCP ou mudanças mobile.

Django adapta sessão/CSRF/JSON e prévia; FastAPI autoriza staff/MFA, elegibilidade, cotas, idempotência, candidata e confirmação. Worker dedicado executa fila persistente PostgreSQL, sem locks durante HTTP. Instruções visuais versionadas no servidor: assunto específico, foco central seguro, contraste, poucos elementos, interesse/expectativa sem vencedor, textos/logos ou aparência documental enganosa; variação perceptível por solicitação. Contexto é dado não confiável, sem admin_notes/ficha/PII. Uma chamada Bedrock Runtime InvokeModel ao modelo de imagem, sem segundo modelo redator.

Candidatas privadas, promovidas para mídia pública exclusivamente na confirmação validada. image_url público preservado. Parecer editorial vigente permanece obrigatório: mudança de imagem invalida revisão; publicação de versão aprovada não ignora candidata/edições pendentes, orienta salvar e revisar.

Estados: queued, running, succeeded, failed, uncertain, expired. Running abandonado torna uncertain e nunca repete automaticamente chamada paga. Fila queued sobrevive reinício. Lease, claim SKIP LOCKED e token fencing. Teto por contagem de solicitações reservadas (não custo faturado): 10/operador, 5/mercado, 50/global a cada 24 horas; toda tentativa reservada conta. Retenção 24h; timeout 180s; lease 300s; desligado por default.

Aceite: geração sem validar resto do formulário; anterior visível durante espera/falha; upload posterior vence resposta atrasada; desfazer restaura seleção anterior inclusive File; alterações de contexto sinalizam imagem anterior; submit durante geração oferece continuar/aguardar inline; consulta não gera; idempotência com hash e conflito; confirmação exige draft/candidata/validade/revisão/URL anterior; autorização vigente também no worker; limpeza nunca remove vinculadas ou em execução. Testes banco isolado/provedor simulado, browser loading/sucesso/erro, sem consumo pago. Acesso real Core validado no DEV por duas solicitações concluídas; qualidade visual e acesso produtivo permanecem pendentes.

Implementação completa validada localmente; status parcial refere-se somente à homologação real/habilitação produtiva pendente. [Evidências](../testing/ai-thumbnails-acceptance.md) e [runbook](../../guides/admin-ai-thumbnails-runbook.md).

Correções de review autorizadas em 2026-10-09: arquivo de upload só é compensado antes do envio ou após rejeição confirmada. Resposta perdida/5xx/408/499 exige consulta administrativa de reconciliação, preservação do arquivo e mensagem honesta sem repetir salvamento/publicação. Se a consulta não confirmar o vínculo, preservar arquivo até investigação, sem afirmar rollback. Decisão inline só encerra polling quando o evento de submissão ocorrer; validação nativa recusada preserva geração/edições e permite corrigir/reenviar. Dockerfile deve passar em `docker build --check` no CI.

## Ajuste de composição do editor autorizado em 2026-10-09

Editor completo com cabeçalho compartilhado, formulário e prévia alinhados, seções com hierarquia simples e sem bordas aninhadas. Separar apresentação do card das regras de resolução; reduzir altura inicial de textos mantendo resize e conteúdo integral. Upload e geração agrupados na mesma linha quando houver espaço; status/erro/decisão continuam junto da thumbnail. Coluna lateral diferencia prévia, publicação e ajuda complementar recolhível. Preservar todos os campos, contratos, revisão humana, fontes de imagem, teclado e estados assíncronos. Verificar desktop/intermediário/mobile, tema escuro, ausência de overflow e fluxo com provedor simulado; este ajuste não inicia inferência paga.

## Revisão autorizada: Bedrock e Configurações do Sistema

A escolha inicial OpenAI foi substituída pelo pedido do usuário: Bedrock, Stable Image Core `stability.stable-image-core-v1:1`, Oregon `us-west-2`, PNG 3:2. Configurações do Sistema oferece seção própria para habilitação, modelo (Core/Stable Diffusion 3.5 Large/Ultra), região suportada, proporção, timeout, cotas/período e retenção. Credencial permanece somente no executor. FastAPI valida e audita GET/PUT administrativos de configuração. Modelos textuais e URLs arbitrárias são rejeitados. Ajustes afetam somente solicitações novas: provedor/modelo/região/proporção/timeout/seed são congelados no job. Kill switch de ambiente prevalece. Jobs legados OpenAI nunca migram/repetem silenciosamente. Aceite adicional: troca de modelo sem código/restart; persistência e auditoria staff/MFA; configuração inválida não salva; geração usa snapshot e não altera agentes; falha/resultado incerto sem fallback/retry. Consumo DEV autorizado e duas solicitações Core concluídas; qualidade real e acesso produtivo pendentes.
