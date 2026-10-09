---
id: FEAT-THUMB-001
titulo: Thumbnails IA no editor Admin Ops
versao: 1.3
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

Django adapta sessão/CSRF/JSON e prévia; FastAPI autoriza staff/MFA, elegibilidade, cotas, idempotência, candidata e confirmação. Worker dedicado executa fila persistente PostgreSQL, sem locks durante HTTP. Instruções visuais versionadas no servidor: assunto específico, foco central seguro, contraste, poucos elementos, interesse/expectativa sem vencedor, textos/logos ou aparência documental enganosa; variação perceptível por solicitação. Contexto é dado não confiável, sem admin_notes/ficha/PII. Na direção vigente v5, uma chamada textual Bedrock interpreta o mercado e redige seu conceito visual antes de uma chamada Runtime InvokeModel ao modelo de imagem, com checkpoints e sem retry. A restrição inicial de não usar modelo redator foi revisada após falhas reais de aderência e pedido do usuário (ADR-0014).

Candidatas privadas, promovidas para mídia pública exclusivamente na confirmação validada. image_url público preservado. Parecer editorial vigente permanece obrigatório: mudança de imagem invalida revisão; publicação de versão aprovada não ignora candidata/edições pendentes, orienta salvar e revisar.

Estados: queued, running, succeeded, failed, uncertain, expired. Running abandonado torna uncertain e nunca repete automaticamente chamada paga. Fila queued sobrevive reinício. Lease, claim SKIP LOCKED e token fencing. Teto por contagem de solicitações reservadas (não custo faturado): 10/operador, 5/mercado, 50/global a cada 24 horas; toda tentativa reservada conta. Retenção 24h; timeout 180s; lease 300s; desligado por default.

Aceite: geração sem validar resto do formulário; anterior visível durante espera/falha; upload posterior vence resposta atrasada; desfazer restaura seleção anterior inclusive File; alterações de contexto sinalizam imagem anterior; submit durante geração oferece continuar/aguardar inline; consulta não gera; idempotência com hash e conflito; confirmação exige draft/candidata/validade/revisão/URL anterior; autorização vigente também no worker; limpeza nunca remove vinculadas ou em execução. Testes banco isolado/provedor simulado, browser loading/sucesso/erro, sem consumo pago. Acesso real Core validado no DEV por duas solicitações concluídas; acesso produtivo confirmado pelo pedido original concluído após PR #146. Aceite visual permanece pendente; duas candidatas Ultra v2 foram reprovadas por falta de relação temática.

Implementação completa implantada e habilitada em produção pela PR #143; status parcial refere-se à homologação humana/MFA e qualidade visual produtiva pendentes. Ajustes de espera e submit compartilhado com badges foram implantados pela PR #144; correção da auditoria do worker pela PR #146. [Evidências](../testing/ai-thumbnails-acceptance.md) e [runbook](../../guides/admin-ai-thumbnails-runbook.md).

Correções de review autorizadas em 2026-10-09: arquivo de upload só é compensado antes do envio ou após rejeição confirmada. Resposta perdida/5xx/408/499 exige consulta administrativa de reconciliação, preservação do arquivo e mensagem honesta sem repetir salvamento/publicação. Se a consulta não confirmar o vínculo, preservar arquivo até investigação, sem afirmar rollback. Decisão inline só encerra polling quando o evento de submissão ocorrer; validação nativa recusada preserva geração/edições e permite corrigir/reenviar. Dockerfile deve passar em `docker build --check` no CI.

## Ajuste de composição do editor autorizado em 2026-10-09

Editor completo com cabeçalho compartilhado, formulário e prévia alinhados, seções com hierarquia simples e sem bordas aninhadas. Separar apresentação do card das regras de resolução; reduzir altura inicial de textos mantendo resize e conteúdo integral. Upload e geração agrupados na mesma linha quando houver espaço; status/erro/decisão continuam junto da thumbnail. Coluna lateral diferencia prévia, publicação e ajuda complementar recolhível. Preservar todos os campos, contratos, revisão humana, fontes de imagem, teclado e estados assíncronos. Verificar desktop/intermediário/mobile, tema escuro, ausência de overflow e fluxo com provedor simulado; este ajuste não inicia inferência paga.

## Revisão autorizada: Bedrock e Configurações do Sistema

A escolha inicial OpenAI foi substituída pelo pedido do usuário: Bedrock, Stable Image Core `stability.stable-image-core-v1:1`, Oregon `us-west-2`, PNG 3:2. Configurações do Sistema oferece seção própria para habilitação, modelo (Core/Stable Diffusion 3.5 Large/Ultra), região suportada, proporção, timeout, cotas/período e retenção. Credencial permanece somente no executor. FastAPI valida e audita GET/PUT administrativos de configuração. Modelos textuais e URLs arbitrárias são rejeitados. Ajustes afetam somente solicitações novas: provedor/modelo/região/proporção/timeout/seed são congelados no job. Kill switch de ambiente prevalece. Jobs legados OpenAI nunca migram/repetem silenciosamente. Aceite adicional: troca de modelo sem código/restart; persistência e auditoria staff/MFA; configuração inválida não salva; geração usa snapshot e não altera agentes; falha/resultado incerto sem fallback/retry. Consumo DEV autorizado e duas solicitações Core concluídas; acesso produtivo Core confirmado após PR #146; qualidade visual pendente, com exemplos Ultra v2 reprovados.


Ajuste de UX de espera (2026-10-09): botão Gerando… e aviso inline destacado Gerando thumbnail… Aguarde, explicando que pode levar alguns minutos e os demais campos podem ser editados. Spinner com reduced-motion, estado anunciado sem overlay/reload. Manter indicador até carregar a prévia e ocultar ao sucesso/erro; escolha manual durante geração não oculta o andamento. Mesmo componente aplicado às imagens clara/escura de badges.


Correção do componente compartilhado: se a escolha manual mudar durante o carregamento da prévia com salvamento pendente, cancelar a decisão e orientar um novo clique em Salvar. A geração seguinte não pode herdar solicitação antiga de salvar/publicar.


## 2026-10-09 — Estado produtivo atual de imagens administrativas

PR #144 integrada em main edac7c7; CI PR e main/build/deploy Success, 442 testes em ambos com um skip por roles CI ausentes (cenário aprovado localmente). Migration0025/grants/constraints/mounts/executor conferidos; habilitação auditada de badges concluída, política de thumbnails preservada. Stable Image Core/Oregon, badges1:1, timeout180s, limites10 imagens/operador e50 globais por24h,5 solicitações/item, retenção24h. Fila vazia, sem inferência paga ou alteração de mercados/concessões reais. Branch local preservada. Manutenção pública ativa preservada; Admin Ops exige login. Homologação humana/MFA e coerência visual real permanecem pendentes. [Evidência produtiva](../testing/ai-badge-images-production-20261009.md). Registros anteriores são histórico das etapas.


## Histórico da correção de relevância visual — 2026-10-09

Aceite autorizado pelo relato de imagens sem relação com o mercado: priorizar pergunta e resumo na descrição enviada ao modelo, antes das instruções genéricas de estilo; manter categoria/subcategoria/evento como contexto secundário, sem reduzir o tema à categoria. Não fixar esportes, jogos, entidades ou cenas por categoria. Tema e detalhes específicos vêm exclusivamente da pergunta, resumo e classificação atuais; instruções fixas somente para qualidade, composição e neutralidade. Não inventar vencedor, cores de clubes ou eventos. Contexto continua dado não confiável e somente campos permitidos. Prompt `market-thumbnail-bedrock-v4`, uma chamada nativa e parâmetros/modelo congelados. Jobs v2 continuam com o prompt v2, sem migração, replay ou reinterpretação silenciosa. Badges e agentes textuais preservados.

Inspeção produtiva de duas candidatas Ultra v2 confirmou perda de relação temática apesar de snapshots corretos. Correção v3 exige homologação visual real separada: testes de montagem do prompt não comprovam aderência do modelo. Não gerar ou substituir imagens já salvas automaticamente.


Correção solicitada pelo usuário: descartada a abordagem v3 com regras temáticas. V4 elimina condicionais/palavras-chave e referências fixas a futebol/Counter-Strike. Jobs v3 existentes mantêm candidatas/estados históricos; v3 não é reinterpretada pelo executor nem repetida. Uma solicitação nova usa v4; eventual job v3 queued falha explicitamente como unsupported_instructions, sem chamada paga. V2 mantém prompt histórico.


## Interpretação semântica do mercado — direção vigente

Usuário esclareceu que não basta template genérico: o modelo deve interpretar o mercado para conceber a imagem. V5 substitui v3/v4 por planejamento semântico em modelo textual Bedrock, seguido da invocação de imagem configurada. Justificativa para a chamada adicional: candidatas reais v2 irrelevantes mesmo em Ultra e rejeição dos presets/templates como solução de produto. Planejador recebe somente campos permitidos como dados em mensagem separada, identifica sujeitos/relação/expectativa e redige descrição visual em inglês, sem catálogo de cenas por tema. Não fornecer exemplos de esportes/jogos no prompt. Requisitos de fidelidade, neutralidade, ausência de texto e privacidade permanecem obrigatórios.

Uma chamada textual e uma imagem por solicitação, sem retry/fallback, mesma reserva de cota; token de saída limitado. Configuração textual própria de thumbnails congelada em provider_config, não herdada dos comentários. Checkpoints persistidos de planejamento e imagem, lease cobre ambos, identidade de provedor e uso retornado por etapa. Falha/saída inválida no planejamento não chama imagem. Reinício/resultado incerto nunca repete chamada paga. V2 mantém contrato histórico; v3/v4 não são reinterpretadas nem repetidas. Badges mantêm duas chamadas nativas e não recebem esta etapa. Interfaces/contratos públicos e image_url permanecem estáveis. Qualidade/acesso real do novo fluxo precisam de homologação, sem inferência paga nos testes automáticos.


## Homologação DEV e preparação de PRD v5

2026-10-09 — Homologação DEV v5: operador informou “em dev local parece estar legal” e autorizou preparar PRD. Consulta local somente leitura confirmou três jobs v5 succeeded (34ccb8f0, bcc57be2, 5cb97131), iniciados pelo operador, com planner openai.gpt-oss-20b/Mantle us-east-1 e imagem Core/us-west-2. Tempos de processamento: 17.804s, 9.663s e 15.883s; uso textual retornado registrado, sem afirmar custo faturado. Acesso efetivo e aprovação visual informal do fluxo DEV confirmados; não substituem matriz visual sistemática, medição de engajamento ou homologação do token/modelo em PRD. Nenhuma inferência paga iniciada pelo assistente. Próxima etapa: aprovação da descrição atualizada da PR, CI completo, merge/deploy e verificação produtiva; preservar modelo de imagem e políticas atuais de PRD.
