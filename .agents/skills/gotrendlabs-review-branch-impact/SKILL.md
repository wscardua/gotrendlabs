---
name: gotrendlabs-review-branch-impact
description: Use esta skill para revisar mudanças de uma branch do GoTrendLabs contra sua base e identificar vulnerabilidades, regressões, efeitos colaterais e quebras de contrato introduzidas, sem alterar código.
---

# GoTrendLabs Branch Impact Review

Use esta skill para code review de uma branch. Faça somente o review: não altere código, contratos, testes ou configuração.

## Objetivo

Encontrar problemas introduzidos ou claramente agravados pela branch, com evidência no diff, código, contratos, testes ou configuração. Não reporte problemas preexistentes nem invente riscos.

## Determinar base e escopo

1. Use `origin/main` como base preferencial, quando existir e for apropriada.
2. Caso contrário, use a upstream real da branch ou o merge-base de `HEAD` com a branch principal disponível.
3. Informe no resumo a base, o merge-base quando usado, o intervalo e os arquivos revisados.
4. Revise apenas mudanças versionadas do intervalo. Se não houver diff, informe isso e não faça auditoria geral do repositório.

## Método

1. Analise o diff completo e classifique as mudanças por superfície:
   - API/backend: `apps/api/backend_api/`;
   - banco/migrações;
   - web/Django/Admin Ops: `apps/web/django/`, `apps/web/templates/` e `apps/web/static/`;
   - mobile/Flutter: `apps/mobile/`;
   - jobs, eventos e integrações;
   - infraestrutura/configuração: `config/`, `ops/`, Docker e ambiente;
   - documentação e contratos, especialmente `packages/contracts/openapi/gotrendlabs-api.json`.
2. Siga fluxos alterados até seus consumidores diretos e indiretos relevantes.
3. Priorize alterações de comportamento, autorização, dados, concorrência e compatibilidade introduzidas no diff.

## API, contratos e consumidores

Quando houver mudança em endpoint, schema, payload, serialização, autenticação, autorização, código de erro, paginação, filtro, ordenação, valor padrão ou regra de domínio:

- localize consumidores API, Django/Admin Ops e Flutter;
- compare com `packages/contracts/openapi/gotrendlabs-api.json` e verifique necessidade de atualizar OpenAPI, testes ou documentação;
- procure campos removidos ou renomeados e mudanças de tipo, nulidade, formato, enum, padrão ou semântica;
- confirme que códigos HTTP e códigos de erro permanecem tratáveis pelos clientes;
- avalie cache, jobs, eventos, integrações, dados legados e transações;
- preserve a FastAPI como autoridade de regras críticas. Web e mobile não devem inferir saldo, permissão, elegibilidade, integridade, status, fechamento ou resultado.

Considere Django web, Admin Ops e Flutter consumidores do contrato atual, salvo evidência explícita de versões ou contratos paralelos.

## Triagem mobile

Não faça revisão Flutter completa para toda feature. Quando houver alteração de API, faça uma checagem breve em `apps/mobile/` para saber se endpoints, schemas ou regras alterados possuem consumidores.

Se não houver impacto, registre “Mobile não impactado” e cite o endpoint, contrato ou consumidor verificado. Faça revisão detalhada quando o diff alterar arquivos em `apps/mobile/`, contratos usados pelo app, autenticação/autorização, headers, sessão, erros, manutenção, atualização, ou regras/estados/payloads usados pelo app.

Na revisão detalhada, examine `ApiClient`, repositories, DTOs/modelos, mapeadores, estado e telas afetadas; compatibilidade JSON (campos, tipos, `null`, listas vazias, datas/timezones, enums, padrões e semântica); token/sessão, logout, troca de conta, cache e dados locais; timeout, rede instável e API indisponível.

Quando aplicável, verifique `401`, `403`, `404`, `409`, `422`, `429`, `500`, `503` e `426`; `/health`; manutenção (`503 code=mobile_maintenance`); atualização obrigatória (`426 code=app_update_required`); e headers de cliente, versão e build.

## Segurança, integridade e testes

Revise apenas os vetores aplicáveis ao diff:

- autenticação, autorização, isolamento de dados e IDOR/BOLA;
- PII, tokens, segredos e detalhes internos em payloads, OpenAPI, logs, cache, eventos e erros;
- validação/normalização de entrada, injection, SSRF, path traversal, upload e desserialização;
- CORS, cookies, CSRF, sessão, JWT, redirects, rate limiting, enumeração e bypass administrativo;
- wallet, previsões, reputação, badges, resolução e auditoria: idempotência, concorrência, replay, dupla execução e integridade transacional.

Marque como vulnerabilidade somente cenário plausível com evidência. Diferencie vulnerabilidade confirmada, risco plausível e ponto a validar.

Verifique se testes cobrem comportamento alterado, autorização, erros e limites relevantes. Indique lacunas como casos de teste concretos e procure regressões em estados vazios, permissões, dados legados, concorrência, cache e retentativas. Execute somente testes locais, seguros e proporcionais ao diff; informe o resultado.

## Resposta obrigatória

### Resumo

- Base e intervalo revisados
- Escopo revisado
- Superfícies afetadas
- Impacto mobile: não impactado / checagem breve / revisão detalhada
- Testes executados, se houver
- Risco geral: baixo, médio, alto ou crítico

### Findings

Liste somente problemas reais ou riscos plausíveis, em ordem de severidade. Para cada finding, informe:

- Severidade: crítico, alto, médio ou baixo
- Tipo: segurança, compatibilidade, regressão, dados, concorrência ou testes
- Local: `arquivo:linha`
- Evidência
- Cenário de falha ou exploração
- Impacto e consumidores afetados: API, web, Admin Ops e/ou mobile
- Correção recomendada

### Pontos a validar

Liste apenas itens não confirmáveis estaticamente, incluindo a evidência atual e o teste, ambiente ou informação necessária.

### Riscos residuais e cobertura

Liste riscos restantes e testes concretos ausentes.

Se não houver findings, declare explicitamente: “Nenhum problema identificável no diff.” Ainda assim, registre a triagem mobile, pontos a validar, riscos residuais e lacunas de teste.
