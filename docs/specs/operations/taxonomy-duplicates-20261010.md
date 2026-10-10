# Correção e saneamento da taxonomia — 2026-10-10

Workflow: `WFLOW-20261010-MARKET-TAXONOMY-FIX`; feature `FEAT-MARKET-001`.

## Causa e correção

O Admin Ops envia os nomes selecionados. A FastAPI regenerava slugs e fazia upsert por slug, criando subcategorias/eventos paralelos quando o cadastro tinha slug personalizado ou havia sido renomeado. Categorias com nome único também podiam produzir erro de unicidade. A resolução implícita agora procura pelo nome no respectivo pai antes do upsert, preservando identidade, avisos e bloqueios. Nomes ambíguos retornam 409 sem mutação. O controle de revisão editorial e a imutabilidade após publicação continuam vigentes.

## Revisão de impacto

- Backend: mudança nos três helpers compartilhados por criação/edição administrativa e conversão de sugestões. CRUD explícito de taxonomia permanece compatível. Consultas parametrizadas e identificadores SQL escapados; autorizações e transações existentes preservadas.
- Admin Ops: `accounts/api_client.py` propaga HTTP 409 como `AuthAPIError`; `admin_ops/views.py` apresenta a mensagem de erro e mantém o formulário. Não há mudança no payload ou no snapshot OpenAPI.
- Mobile não impactado: não há consumidor de `/admin/markets`, `/admin/categories` ou `convert-draft` em `apps/mobile/lib`; os contratos públicos de mercado permanecem iguais.
- Integração MCP mantém o resolvedor por IDs em `editorial_service.py`. Não depende do novo lookup por nome.
- Banco: sem migration ou alteração de schema. IDs de taxonomia pertencem à definição assinada; o saneamento não pode remapear mercados nem apagar histórico assinado.
- Arquitetura: responsabilidade de resolução permanece na FastAPI. A operação de reparo é explícita e auditada, sem novo endpoint administrativo ou mudança de fronteira que exija ADR.

## Inventário produtivo e plano

Inventário somente leitura via SSM `489c77de-b684-4a68-8a41-55ef0d0bb925` e `0eecf905-5f0c-483e-a3b8-cf41e39549ad`:

- Nenhuma categoria duplicada por nome normalizado.
- Esporte (categoria 18), Geral: subcategorias 40 e 54; nenhum mercado vinculado a ambas. Preservar 40 e evento 40; remover evento Geral 54 e subcategoria 54.
- Esporte, Ginástica Artística: subcategorias 55 e 64. Preservar 64 e evento Mundial2026 65, já ligados ao mercado 38. Mover o evento distinto Geral 55, sem mercado vinculado, para 64; remover apenas a subcategoria vazia 55.
- Nenhuma duplicidade de evento dentro do mesmo pai; o evento Geral 54 é repetição de caminho sob subgrupo duplicado. O evento Mundial2026 não é duplicado e deve ser preservado.
- Os quatro mercados existentes estão em draft e sem definição assinada. Ainda assim, o plano preserva todos os IDs e campos dos mercados, revisões editoriais e históricos.

O inventário é uma evidência temporal. Refazer a simulação depois do deploy; o script revalida as precondições sob locks antes de gravar.

## Execução após deploy

Dentro do ambiente FastAPI, primeiro simular:

```sh
python -m ops.scripts.consolidate_unused_taxonomy --merge 54:40 --merge 55:64
```

Depois, executar com arquivo novo em volume persistente:

```sh
python -m ops.scripts.consolidate_unused_taxonomy --merge 54:40 --merge 55:64 --execute --backup /app/.runtime/taxonomy-before-cleanup-20261010.json
```

O script valida todos os pares antes de alterar, mantém locks curtos nas tabelas de taxonomia/mercados, recusa referências de mercado na origem e divergências de avisos/bloqueios, grava preimagem com permissão 0600 e fsync, preserva eventos distintos e registra `taxonomy.deduplicate` em `gotrendlabs_admin_events` na mesma transação. Arquivo já existente, referência concorrente ou falha de constraint interrompe a operação. Não usar exclusão em cascata. Não reutilizar o comando sem novo inventário: origens ausentes são rejeitadas.

## Verificação e recuperação

- Confirmar CI/Actions, SHA implantado, serviços ativos e health antes de executar.
- Comparar inventário de mercado antes/depois: IDs, vínculos e revisões devem permanecer iguais. Repetir busca de nomes duplicados por pai e verificar auditoria e backup.
- Conferir a resolução dos nomes existentes no runtime corrigido e o retorno 409 para ambiguidade nos testes. Smoke produtivo somente leitura, sem criar mercado nem publicar draft.
- Em falha, a transação desfaz as alterações; o backup pode existir mesmo após rollback. Para desfazer operação já commitada, restaurar as linhas de origem e os pais dos eventos a partir da preimagem em nova transação, após verificar conflitos/uso novo, preservando a auditoria e registrando a reversão. Não restaurar um dump completo sobre alterações posteriores.

## Evidências de execução

Preparação local em andamento. PR, CI, merge, deploy e limpeza produtiva ainda não executados; preencher os resultados reais no fechamento.
