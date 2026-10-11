# Publicação: exclusão pré-publicação e parecer humano

Entrega de 2026-10-11, branch `feature/delete-draft-review-markets`, WFLOW-20261011-CLOSE-PREPUBLICATION-EDITORIAL. Implementação local concluída; este documento descreve verificações pendentes de produção, sem afirmar implantação.

## Fluxo GitHub

1. Reconciliar specs/contratos/estado, preparar commit e apresentar título/descrição da PR em português ao usuário.
2. Após aprovação, enviar a branch e abrir PR para `main` pelo GitHub MCP. Preservar a branch local.
3. Acompanhar `GoTrendLabs CI and Deploy`: build Docker, OpenAPI e suíte completa. Corrigir falhas antes de merge; vincular resultados ao SHA final.
4. Antes do merge, confirmar backup recuperável do banco e inventário dos serviços/configuração. A alteração contém código/migrations e deve seguir CI/deploy completo, não docs-only.
5. Merge após CI aprovado; acompanhar o run de `main` e o comando SSM até sucesso. Conferir que o SHA implantado corresponde ao merge. Se `ENABLE_PROD_DEPLOY` não estiver habilitado, não tratar build como deploy: verificar configuração e executar o caminho produtivo autorizado.

## Migrations e ativação

O deploy existente em `ops/deploy/production/deploy.sh` pausa os escritores, executa migrations pela role dedicada, reaplica grants, coleta static e recria API/Django/MCP/daemon/worker. Não copiar ambientes DEV para PRD.

- `editorial_integrations.0006_prepublication_deletion`: função `public.delete_prepublication_editorial(bigint,integer)` restrita, com revalidação de estado/revisão/previsões/provas. Conferir owner e `SECURITY DEFINER`, `search_path=pg_catalog`, EXECUTE permitido a FastAPI, negado a Django/PUBLIC, e ausência de DELETE geral nas revisões.
- `admin_ops.0026_deleted_market_thumbnail_receipts`: permite somente recibo técnico de thumbnail expirado/desvinculado por exclusão, sem snapshot editorial.
- Nenhum feature flag novo: o botão depende da elegibilidade retornada pela FastAPI. Aprovação humana exige confirmação e mantém autoria/versão/hash/snapshot. Configuração operacional de fechamento continua obrigatória.
- Preservar configurações de MCP e geração de imagens. Reiniciar o worker junto ao runtime, sem iniciar inferência paga como smoke.

## Smoke pós-deploy

Conferir migrations aplicadas, SHA, serviços saudáveis, páginas/static, API `/health` e discovery/health MCP. Rotas administrativas anônimas devem continuar protegidas. Verificar projeção `can_delete` e botão para preparação/revisão; demais estados não devem permitir exclusão.

Conferir leitura do checklist v1.3/modelo v1.6 expostos pelo MCP e hashes correspondentes; política aprovada v1.2/hash permanece inalterada. Nenhuma ferramenta de exclusão ou aprovação deve aparecer no MCP.

Validar execução com a role real FastAPI em transação revertida ou fixture isolada, sem excluir/aprovar mercados reais como teste. Cobrir limpeza editorial/dependências, auditoria e retorno de replay após exclusão. A role Django não deve conseguir executar a função. A verificação por catálogo complementa, mas não substitui, execução sob a role real.

Homologação humana: operador staff/MFA testa confirmação de exclusão e parecer aprovado/confirmado; aba antiga não deve atingir outro ID no mesmo slug. Alertas de conteúdo não bloqueiam o parecer confirmado. Registrar qualquer etapa não exercitada sem alegar homologação completa.

## Recuperação e memória

Em falha de migration, seguir a parada segura do deploy e investigar antes de reiniciar escritores. Manter migrations aditivas ao retornar runtime anterior, pois recibos desvinculados não satisfazem a constraint antiga. Exclusão física exige backup para recuperação de dados removidos; rollback de código não restaura mercados.

Após sucesso, registrar PR, SHA do merge, IDs/links dos runs PR/main, status SSM, migrations/grants e resultados de smoke em `workflow-runs.md`, `implementation-status.md`, `feature-changelog.md` e aceite. Separar verificações técnicas concluídas de homologação humana pendente; não marcar a feature ampla inteira como concluída por este escopo.
