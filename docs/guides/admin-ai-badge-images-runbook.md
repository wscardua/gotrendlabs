# Imagens IA de badges

No Admin Ops → Badges → Criar/Editar, preencha nome e descrição e clique Gerar imagem. Gerar outra solicita alternativa; Desfazer troca recupera a seleção anterior, incluindo arquivos dos dois temas. Não precisa salvar a badge antes de gerar. Use Salvar badge para confirmar; gerar não cria/ativa badge nem modifica regras ou concede conquistas.

Cada solicitação gera duas imagens quadradas: clara e escura. Ao salvar a candidata completa, image_url e image_dark_url recebem mídias públicas distintas validadas na mesma transação; arquivos antigos não são apagados. Upload manual continua separado por tema. Trocar a imagem altera a apresentação da definição e de suas conquistas existentes, sem alterar propriedade ou motivo da conquista. Texto modificado após gerar mostra aviso; não há geração paga automática. Durante geração, salvamento oferece continuar/aguardar inline.

## Configuração e executor

Configurações do Sistema → Imagens por IA → Permitir geração de imagens de badges → Salvar geração de badges. Habilitação independente de thumbnails, off por default e auditada via FastAPI. Modelo/região/timeout/cotas/período/retenção são os parâmetros compartilhados existentes; badges usam sempre 1:1. Core default, adapters SD3.5/Ultra configuráveis; modelos dos agentes de comentários não mudam. Limites default 10 por operador, 5 por item/editor, 50 global por 24h, contando ambas as finalidades. Candidatas 24h, timeout 180s. Cotas global/operador contam imagens reservadas: 1 por thumbnail e 2 por par de badges; limite por item conta solicitações. Falhas e resultados incertos mantêm reserva. Não são valores faturados. Um par usa duas invocações pagas; nenhuma chamada é repetida automaticamente, mesmo após falha parcial. Cada chamada tem timeout de 180s por default; lease do par cobre pelo menos 420s.

Executor compartilhado: `python -m apps.api.backend_api.thumbnail_worker`. Não iniciar outro daemon ou duplicar fila. GTL_THUMB_ENABLED prevalece na API/executor para ambas as finalidades; habilitação específica DB decide quais kinds podem ser reivindicados. Mudanças de configuração valem para novos jobs, sem reinterpretação/retry de resultados desconhecidos. Segredo Bedrock exclusivamente no servidor.

Migration admin_ops.0025_badge_image_jobs segue 0024_thumbnail_runtime_defaults: flag de habilitação com default SQL false, kind com default SQL market, FK badge/editor UUID e constraints por domínio. Grants permitem FastAPI atualizar a habilitação; Django continua dono do schema/adaptador, sem escrever jobs. Jobs históricos ficam market, e payloads/endpoints antigos continuam válidos.

Armazenamento privado compartilhado. GTL_BADGE_PUBLIC_ROOT default media/badge_images, produção /app/media/badge_images. FastAPI/worker montam somente esse subpath RW adicional; proxy continua sem volume privado. Deploy prepara ambos os diretórios públicos preservando arquivos/owners existentes. Worker prune remove candidatas vencidas/órfãos UUID com grace 1h e lock de promoção, verificando tanto image_url quanto image_dark_url. Não remover arquivos de upload manual ou vinculados; upload com resultado desconhecido fica preservado para investigação. Não copiar imagens locais de testes para produção.

## Verificação e rollback

Testes automáticos usam DB isolado e provedor simulado, sem credenciais/inferência. Browser real usa template/CSS/JS e fixtures. Confirmar ambos os temas e tamanhos 48/68px; fixtures não comprovam qualidade real ou transparência. Core não documenta alpha; não tratar PNG como garantia de fundo transparente.

Rollout somente depois da PR própria aprovada: CI, merge/deploy, migration/grants/subpaths e executor atualizados. Conferir fila antes de habilitar; jobs queued podem ser processados ao liberar. Verificar API e configuração autorizadas, candidata privada, confirmação e ausência de alterações nas concessões. Consumo pago real exige autorização para esse teste. Na preparação não houve inferência real do par claro/escuro nem alteração produtiva desta feature; jobs DEV anteriores da versão universal permanecem preservados.

Pausa: desligar apenas badge_image_enabled no painel; mercados continuam conforme sua própria configuração. Emergência global: GTL_THUMB_ENABLED=0 e restart API/executor. Preservar tabela/migrations/arquivos e `.env.thumbnails.prod` para futuros redeploys. Não reenfileirar uncertain. Rollback de aplicação com esquema novo exige pausar badges e verificar compatibilidade do executor antigo antes de iniciar; migrations aditivas não devem ser revertidas com candidatas associadas.


Recarga durante geração: reabrir a mesma badge na mesma sessão recupera o job ativo e o indicador de andamento, sem clicar novamente nem criar solicitação. Sessão expirada/nova não assume candidatas da anterior. Nova criação recebe outra identidade após salvar. Se uma escolha manual mudar enquanto as prévias carregam e houver salvamento aguardando, a decisão é cancelada com orientação para clicar em Salvar; outra geração não executa esse salvamento antigo.


## Fechamento e habilitação produtiva

Workflow WFLOW-20261009-BADGE-CLOSE-001. Após aprovação da descrição: enviar a branch preservada, abrir PR em português via MCP GitHub, aguardar CI completo/build e integrar em main somente com checks aprovados. Acompanhar GoTrendLabs CI and Deploy e comando SSM até Success para o SHA integrado. Esta mudança não é docs-only.

No host já configurado para thumbnails: o mesmo executor/credencial/modelo atende badges; não provisionar outro serviço nem alterar agentes textuais. Deploy aplica migration0025/grants e prepara badge_images. Conferir mount público RW para API/worker, privado worker RW/API RO, sem mount privado no proxy; usar somente arquivo efêmero próprio e removê-lo. Conferir coluna/defaults/constraints/grants e worker da versão integrada. Antes de habilitar, consultar fila de badges e resolver qualquer trabalho ativo sem replay. Habilitar badge_image_enabled pela função de serviço auditada em contexto operacional autorizado, preservando modelo/região/limites/retenção atuais. GTL_THUMB_ENABLED já existente continua obrigatório; não imprimir ou copiar credenciais para logs.

Verificar health/site, bloqueio anônimo dos endpoints administrativos e ausência de exposição de candidatas; não modificar badges/mercados reais em smoke técnico. Teste humano com MFA e inferência paga produtiva são homologações distintas: registrar pendências sem afirmar qualidade real pelos mocks. Rollback funcional: desligar apenas badge_image_enabled, manter esquema/arquivos e executor atual; reverter aplicação só após análise de compatibilidade e pausa dos writers. Registrar PR, merge SHA, Actions, SSM, configurações não secretas e resultado real no workflow/aceite.


## Habilitação concluída em 2026-10-09

PR #144/Actions37977374007 e SSM com Success; badges e thumbnails habilitadas, executor e mounts verificados. Configuração anterior preservada e fila vazia. Manutenção pública ativa preservada; Admin Ops exige login. Nenhuma inferência paga produtiva; homologação humana/visual pendente. [Recibo](../specs/testing/ai-badge-images-production-20261009.md). Etapas de rollout acima são procedimento e histórico, não pendências de implantação atuais.
