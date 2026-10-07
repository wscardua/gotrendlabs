# Correção OAuth Codex — 2026-10-07

Workflow: WFLOW-20261007-MCP-CODEX-OAUTH-001; FEAT-MCP-001. Branch feature/mcp-editorial. Base main 44a31b5.

## Diagnóstico real

Logs locais do Codex Desktop registram falha mcpServer/oauth/login no registro dinâmico: HTTP 422 validation_failed. CLI 0.160.1 reproduz a mesma falha contra produção antes da autorização humana. Captura da requisição do CLI em servidor loopback isolado mostrou application_type=native, ausente do schema que proibia extras. Nenhuma credencial do operador ou token MCP foi reutilizado, exibido ou exportado neste diagnóstico.

GET produtivo de resource metadata anuncia authorization_servers com barra final, mas discovery do AS informa issuer sem barra; a regra de comparação exata dos clientes torna isso uma inconsistência adicional. Captura HTTPS somente leitura, sem desabilitar auth.

## Correção

Schema DCR ignora metadados desconhecidos conforme RFC 7591 §2; não persiste/reflete extras e não emite token/grant no registro. Campos conhecidos continuam validados; schemas de domínio/admin permanecem estritos. Nenhuma migration/grant/identidade humana nova.

Adaptador canonicaliza issuer como FastAPI (sem barra final) e substitui somente a rota pública de resource metadata do SDK para anunciar o issuer textual exato, resource e scopes. Middleware/challenge/verificação de token/audience e fronteira sem banco preservados.

## Evidências

- CLI real com servidor local de diagnóstico e schema corrigido: registro aceito, application_type ignorado, URL de autorização atingida. Sem consentimento humano, token ou requisição produtiva nessa simulação.
- Suite final PostgreSQL MCP/API/adapter: **50 testes/153,516 s/OK**, incluindo registro nativo Codex, negativas de segurança, SDK real com dez ferramentas/OAuth/serviço/renovação/revogação, cotas/concorrência e regressões editoriais. Bases de teste isoladas destruídas; DEV/prod não receberam mercados de ensaio.
- OpenAPI regenerado/--check, Ruff F e diff aprovados.
- A primeira suíte (50 testes/146,110 s) encontrou dois erros nas fixtures novas: acesso por índice em cursor dict e tentativa de iniciar novamente o lifespan singleton do SDK. Corrigidos nos testes; não representam falha de autorização do produto. A repetição iniciada antes da última correção ainda carregava a fixture de lifespan anterior (50 testes/145,343 s, um erro). Repetição focal adapter corrigida: cinco testes/0,571 s/OK. A execução final usa os arquivos estabilizados.

## Operação e pendência

Produção continua na versão anterior até aprovação da PR/merge e rollout Actions. Depois: comparar issuer exatamente em discovery, registrar payload Codex e repetir Authenticate no Desktop com operador/MFA/integração ativa. Login humano real e homologação Dot continuam pendentes; não substituir OAuth por segredo de serviço em header Bearer. Nenhum mercado produtivo criado, nenhuma credencial emitida ou integração alterada.

Rollback: reverter commit via fluxo GitHub, reaplicar deploy padrão; não há mudança de schema/dados. Reversão restaura também a incompatibilidade DCR, devendo ser registrada.
