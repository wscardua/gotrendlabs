---
id: FEAT-BADGE-IMAGE-001
titulo: Imagens IA na criação e edição de badges
versao: 1.2
status_spec: aprovada
status_impl: parcial
ultima_atualizacao: 2026-10-09
contratos_afetados: [admin-badge-images.md, reputation-ranking.md]
dependencias: [FEAT-THUMB-001, FEAT-AUTH-001, FEAT-REP-001]
impacta: [admin-ops, frontend-web, backend-api, database, scheduler-jobs]
---

# Imagens IA de badges

Autorização: usuário pediu analisar o reaproveitamento de thumbnails e autorizou prosseguir com a recomendação de feature separada. Implementação local, sem novas chamadas pagas ou inclusão automática na PR de thumbnails. Publicação desta feature requer apresentar sua descrição antes da PR.

## Escopo autorizado

Incluído: criação e edição administrativas de badges, par claro/escuro em um clique, regeneração/desfazer, seleção para salvamento existente, contexto atual e execução assíncrona protegida. Fora do escopo: galeria/histórico navegável, editor de prompts/modelos no formulário, lote, geração via MCP, alteração de regras/concessões e redesenho mobile.

## Experiência e aceite

Criar/editar badge: um clique em Gerar imagem, outro em Gerar outra, candidata selecionada automaticamente e confirmação pelos botões existentes. Mostrar imediatamente botão Gerando… desabilitado e aviso destacado junto à imagem: Aguarde, isso pode levar alguns minutos; permitir editar os demais campos. Indicador permanece até as duas prévias carregarem, inclusive após conclusão do backend; ocultar no sucesso/falha. Preservar upload, desfazer, edições, imagem anterior durante espera/falha, decisão inline continuar/aguardar e proteção contra resposta atrasada. Não criar, ativar, conceder ou alterar regras de badge pela geração. Validar somente nome/descrição/tipo/contexto visual necessário, não toda a regra executável.

Usar nome, descrição, descrição pública da regra, tipo, categoria/subcategoria/evento atuais. Não enviar usuários/conquistas, credenciais ou dados privados. Prompt versionado específico: emblema quadrado coeso, símbolo central, paleta verde/marfim/dourado/teal, geometria simples, profundidade sutil e leitura em 48/68 px. Sem textos/números/logos ou estética de dinheiro/cassino/trading. Base visual em badges-imagem/prompt-geracao-badge.md. PNG 1:1, fundo neutro deliberado; não prometer transparência. Cada solicitação gera um par: imagem clara e imagem escura com contexto, direção, seed e símbolo coerentes; duas invocações nativas, uma por tema, sem chamadas auxiliares. As duas devem concluir e validar antes da seleção. Confirmar aplica image_url e image_dark_url atomicamente; desfazer recupera o par e uploads anteriores. Falha parcial preserva o par anterior; não selecionar nem aplicar só uma variante. A coerência visual real entre variantes exige homologação.

Reutilizar fila persistente, executor, provedor Bedrock e controles de consumo de thumbnails. Kind, badge FK e editor UUID explícitos, restrições relacionais por domínio; mercados continuam draft-only. Criação sem badge salva: candidata pertence ao operador/sessão/editor, associada atomicamente na criação. Edição: validar badge, operador/sessão, URLs anteriores e updated_at sob lock antes da aplicação. Sem URL arbitrária de candidata e sem alteração automática após salvar.

Configuração de habilitação de badges separada, default off, auditada staff/MFA. Modelo/região/timeout/limites/período/retenção compartilhados com imagens de mercados, sem mudança dos agentes textuais; proporção de badges sempre 1:1. Teto global e por operador contam imagens reservadas: uma por mercado, duas por par de badges, com a mesma reserva serializada; inclusive falhas e resultados incertos. Limite por item continua contando solicitações. Máximo uma ativa por badge salva ou editor novo. Limite por item vale separadamente para cada mercado/badge/editor. Switch operacional do executor prevalece.

Estados, leases, unknown sem retry, arquivos privados, limpeza e auditoria mantêm contrato de thumbnails. Promoção em badge_images; preservar arquivos ligados a image_url e image_dark_url, inclusive conquistas históricas. Testes isolados/mocks: staff/MFA/CSRF, criação sem salvar, idempotência/cotas globais compartilhadas/concorrência, candidata de outro operador/editor/badge/sessão, expiração/arquivo/armazenamento, confirmação única/conflito/rollback, reinício/revogação/unknown, seleção/undo/uploads/temas/late response/submit, não regressão de thumbnails/agentes/concessões. Browser real com respostas simuladas. Produção implantada e habilitada pela PR #144; qualidade visual real e homologação humana/MFA pendentes.


Correção de review: identidade do editor preservada na sessão Django por badge (ou criação em andamento) e sessão autenticada; recarga recupera status pelo GET existente, sem gerar novamente. Nova criação após salvamento recebe identidade nova. Troca manual durante carregamento cancela decisão de salvamento pendente e orienta clicar em Salvar; nova geração jamais herda submit anterior.


## Fechamento técnico

Fonte atual: WFLOW-20261009-BADGE-CLOSE-001; implementação local completa, par claro/escuro e findings de review corrigidos. Publicação/habilitação técnica concluídas pela PR #144; status parcial refere-se somente à homologação humana/MFA e visual real pendente. Checklists: feature/contratos/ADR/testes/estado/changelog/mapa/runbook completos; descrição aprovada, CI e rollout verificados conforme recibo produtivo. Defaults 10 imagens/operador, 50 imagens globais por 24h, 5 solicitações/item, retenção 24h. Um par reserva duas imagens; nenhuma estimativa é custo faturado.


## 2026-10-09 — Estado produtivo atual de imagens administrativas

PR #144 integrada em main edac7c7; CI PR e main/build/deploy Success, 442 testes em ambos com um skip por roles CI ausentes (cenário aprovado localmente). Migration0025/grants/constraints/mounts/executor conferidos; habilitação auditada de badges concluída, política de thumbnails preservada. Stable Image Core/Oregon, badges1:1, timeout180s, limites10 imagens/operador e50 globais por24h,5 solicitações/item, retenção24h. Fila vazia, sem inferência paga ou alteração de mercados/concessões reais. Branch local preservada. Manutenção pública ativa preservada; Admin Ops exige login. Homologação humana/MFA e coerência visual real permanecem pendentes. [Evidência produtiva](../testing/ai-badge-images-production-20261009.md). Registros anteriores são histórico das etapas.
