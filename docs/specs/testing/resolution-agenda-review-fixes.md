# Correções da revisão da agenda — 17/10/2026

Workflow WFLOW-20261017-AGENDA-REVIEW-FIXES, branch feature/structured-resolution-agenda, base origin/main 7029dd8. Revisão abrangeu working tree e arquivos novos; alterações preexistentes preservadas.

## Correções

- Restaurado helper de datas administrativas ao formato anterior, usando o fuso ativo sem variável indefinida. Corrige emails, entregas push e dispositivos; a revisão reproduziu erro no teste da página de dispositivos.
- MCP preserva códigos fixos de validação da agenda emitidos pela FastAPI; não os transforma em dependency_unavailable. Erros desconhecidos e mensagens livres continuam sanitizados. Nenhuma nova ferramenta, permissão, scope, endpoint ou alteração de replay/idempotência.
- Spec MVP e arquitetura mobile descrevem o componente aprovado: três linhas e painel inferior rolável/selecionável com Fechar. Prazos ficam no rodapé do resumo. Nenhuma alteração Flutter nesta correção.
- Mensagem de agenda incompleta no parecer humano passa a indicar somente previsão/fuso e coerência com critérios, removendo a lista antiga de campos.

## Validação

Cinco testes novos: datas no fuso São Paulo/UTC e ausência; transporte MCP preserva cinco códigos sem divulgar mensagem upstream e sem alterar o payload de submissão; código desconhecido continua sanitizado; scope insuficiente impede até abrir o cliente HTTP. Transporte simulado, sem rede externa.

Rodada isolada dos cinco testes aprovada (0.135s). Suíte integrada final: 120 testes aprovados em 201.458s no PostgreSQL isolado `test_gtl_review_agenda_20261017`, incluindo os cinco novos e a página de dispositivos antes quebrada. Log privado `/tmp/gtl-agenda-fixes-tests.log`. Checklist aplicado e workflow concluído. OpenAPI --check aprovado; sem mudança de schema ou necessidade de regeneração.

## Limites

Sem produção, merge, deploy ou backfill produtivo. Nenhum APK novo: código Flutter e apresentação aprovada permanecem iguais; não foi repetido QA físico nesta correção Python/documentação. Revisões humanas dos dados e grants/staging permanecem pendentes conforme runbook.
