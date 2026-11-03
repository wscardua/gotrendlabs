# Evidências locais — winning_option_id no get_market

Data: 03/11/2026. Workflow WFLOW-20261103-MCP-WINNING-OPTION. Branch `fix/mcp-get-market-winning-option`, base `origin/main` ca67e9f após fetch. Worktree `/Users/williamsca/Documents/gotrendlabs-mcp-winning-option`; alterações locais do checkout original preservadas.

## Implementação e arquitetura

PostgreSQL já persiste a vencedora; a API pública já a expõe. A leitura editorial seleciona o valor na projeção operacional sob o lock compartilhado existente. `MarketProjection`, compartilhado entre REST e SDK MCP, exige `winning_option_id: integer | null`, sem default/fallback. `null` permanece explícito no payload; resolved/sealed retornam a vencedora persistida relacionada a `options[].id`. Não há cálculo/inferência de vencedora.

A função de leitura usada em snapshots editoriais permanece intacta: o campo operacional não altera hashes, revisões ou aprovações. Fronteiras revisadas com software-architect/architecture-guard; desenho segue ADR-0019, sem decisão estrutural nova. Estratégia e execução seguem test-strategy/test-engineer.

## Ambiente e validação

Venv existente `/Users/williamsca/Documents/gotrendlabs-mcp/.venv`, Python 3.11.0, sem reinstalar dependências. PostgreSQL 16 Alpine temporário em container `gtl-mcp-winner-tests`, loopback 55441, dados em tmpfs e banco de testes dedicado. Sem acesso ao banco operacional nem alteração de mercados reais.

Primeira execução focada: cinco cenários de domínio/acesso aprovados; SDK falhou por cota do fixture, pois duas novas fixtures terminais consumiram a cota diária de cinco drafts. Corrigida somente a preparação desse teste para dez drafts/dia; limites produtivos inalterados. Regressão ampliada executada: 142 testes em 185,422s, 140 aprovados, um skip e uma falha na contagem final do teste SDK (esperava dois mercados, agora são quatro devido às fixtures terminais). Todas as asserções de payload/schema SDK haviam passado. Corrigida a contagem para `2 + len(terminal_markets)`; reexecutado o teste SDK completo, aprovado em 22,410s. Resultado final combinado: **141 cenários aprovados e um skip**, sem falha pendente. O skip é o check de privilégios das roles nomeadas `gotrendlabs_django`/`gotrendlabs_fastapi`, ausentes no cluster isolado; o teste de ACL com roles temporárias foi aprovado.

Comandos (prefixados pelo Python do venv existente):

```sh
python .runtime/run_tests.py test tests.test_mcp_editorial tests.test_mcp_market_actions tests.test_mcp_adapter tests.test_mcp_packaging tests.test_mcp_schedule_errors tests.test_resolution_reliability tests.test_integrity_ledger --noinput
python .runtime/run_tests.py test tests.test_mcp_editorial.McpEditorialTests.test_real_streamable_mcp_client_tools_auth_and_draft --noinput
```

Cobertura confirmada: null presente e ausência rejeitada pelo schema; GET locked sem vencedora, resolved/sealed após lifecycle real e canceled com null; ID pertencente às opções; schema REST/MCP e structuredContent em SDK Streamable HTTP real, serviço e OAuth, incluindo fixtures com a segunda opção vencedora; leitura com catalog:read, negação sem scope e ficha privada alheia omitida; snapshots sem winning_option_id; replays, integridade e liquidação sem regressão.

Django check, makemigrations --check --dry-run, exportação/OpenAPI --check, Ruff F nos arquivos Python alterados e git diff --check aprovados. Sem migration necessária. Recursos temporários de teste removidos ao concluir; logs locais ignorados em `.runtime/winner-*-tests.log` e `.runtime/winner-sdk-retest.log`.

## Impacto MCP e disponibilização

- Ferramentas: mesmo catálogo 21; descrição de `get_market` explica resultado persistido/null.
- Schemas/contratos: novo campo obrigatório nullable em `MarketProjection`, REST/MCP/OpenAPI e specs v1.9; consumidores atualizados diretamente pelo schema compartilhado.
- Permissões: mesmo `catalog:read`; visibilidade de drafts e omissão da ficha privada alheia preservadas. Sem grants/scopes novos ou poderes inferidos do Admin Ops.
- Erros: sem novo erro de negócio; obrigatoriedade é validada pelo schema de saída. Autorização e recurso ausente mantêm os contratos existentes.
- Replays: leitura não muda mutações, chaves, recibos ou precondições; regressão de lifecycle inclui replays após resolução/selagem.
- Editorial: política/ficha/aprovação e hashes preservados; apenas orientação técnica da ferramenta esclarecida.

Deploy não executado. Disponibilização requer publicar backend/API e imagem MCP com a mesma revisão do schema; depois conferir tools/list e payload autenticados no servidor implantado. Sem migration ou novo consentimento necessário para este campo no scope já autorizado. Cache de ferramentas de clientes pode exigir atualização do catálogo.

## Preparação do fechamento — 03/11/2026

Usuário autorizou preparar commit e fluxo GitHub/produção, condicionando a submissão da PR à aprovação prévia do título e descrição. Novo fetch confirmou origin/main ca67e9f. ENABLE_PROD_DEPLOY=1 confirmado por leitura da variável do repositório. Sem template de PR no checkout. O [roteiro](../operations/mcp-winning-option-rollout.md) define implantação coordenada e smoke de leitura; sucesso produtivo só será registrado após Actions e verificações reais.

Mobile não impactado: `apps/mobile/lib/src/features/markets/markets_repository.dart` lê `/markets/{slug}`, não `/integrations/editorial/markets/{market_id}` nem `MarketProjection`. Web/Admin Ops também não consomem esta projeção alterada; o contrato público `MarketResponse` mantém o shape anterior. A triagem não exige release Flutter.

Commit de implementação/preparação: e01c9ac. [Review de impacto versionado](mcp-winning-option-review.md): sem findings, risco baixo; checagens finais de OpenAPI/Ruff/diff aprovadas. PR ainda não submetida; aguardando aprovação do título e descrição pelo usuário.
