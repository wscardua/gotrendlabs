# Review de fechamento — Analyst e Novo — 14/11/2026

Base/merge-base: origin/main 33b6da67378e3ad56d25de4e9eb4040f558e431d, confirmada por fetch e MCP GitHub. Escopo autorizado inclui árvore de trabalho sem commit e arquivos novos da branch feature/analyst-editorial-quality, inclusive documentação de fechamento; nenhuma revisão do checkout original em feature/first-party-analytics.

Superfícies revisadas: prompts/cliente LLM/serviço FastAPI; comando de criação e Admin Ops; template/base/JS web; modelo/provider e testes Flutter; specs, estado e corpus editorial. Sem migration, infra, segredo, permissão, endpoint ou schema público novo. Mobile revisado em detalhe para published_at; ApiClient/repositories e contrato atual continuam consumidores inalterados.

## Findings e correção

O review identificou perda da categoria do risco: financial_advice e unsupported produziam o mesmo payload de auditoria. Corrigido no prompt v6/FEAT-AIAGENT-001 v0.8: risk_categories usa enum conhecido com unknown_risk para valores arbitrários; contagem original preservada; gerador retorna abstention_reason obrigatório/coerente. Contrato antigo/inconsistente falha sem publicação, sem fallback. Testes PostgreSQL distinguem geração/avaliação, abstenção e limite de tentativas; dados livres/sensíveis não são copiados. Admin Ops exibe os códigos no detalhe.

Após a correção, nenhum novo problema identificável no diff revisado. Isso não comprova qualidade semântica, segurança absoluta contra injeção ou engajamento; a avaliação real permanece pendente. Risco residual médio de qualidade/capacidade do modelo, explicitamente separado da correção de fluxo e auditoria.

## Evidência e limites

- 49 testes direcionados aprovados; 141 Flutter completos/analyze aprovados; quatro scripts JS do CI, Django/OpenAPI/diff e Dockerfile check aprovados.
- Suíte Python completa reportou 722 executados, 719 aprovados/dois skips/um erro de CREATEROLE no ambiente local. O teste inalterado passou isolado com papel migrador em banco próprio; permissões de runtime preservadas. Não declarar rodada completa verde.
- Build principal Docker local bloqueado por espaço em /var/cache/apt/archives/, não por código desta branch. Builds principal/MCP e suíte completa obrigatórios no CI antes do merge.
- O dataset de 24 casos/editorial tem expectativas explícitas; não houve chamada paga de avaliação. Mesmo modelo pode compartilhar vieses entre geração e avaliação; JSON/checks não garantem correção externa.
- Campo published_at já é ISO/nullable no MarketResponse; web e Flutter ocultam Novo se ausente/inválido/futuro e expiram em 48h, sem inferir domínio ou alterar ordenação.
- MCP sem ajustes: ferramentas, schemas públicos, permissões, erros/replays e manual exposto permanecem iguais. Sem permissão derivada de ações humanas no Admin Ops.

Fonte vigente da preparação, ajustes administrativos propostos e próximos gates: [recibo](analyst-editorial-closeout-20261114.md). O review foi concluído antes da implantação; agora a PR #213 está integrada e a produção foi validada no recibo, sem ampliar o escopo editorial ou MCP.
