# AdSense — recibo local de 2026-11-08

Branch `feature/adsense-site-verification`, origin/main atualizada em `590ce3b`, worktree `/Users/williamsca/Documents/gotrendlabs-adsense`. Checkout original e alterações preexistentes preservados. Implementação e testes locais, sem push, integração à main, deploy, conta Google ou escrita produtiva.

## Resultado e arquivos

- `config/settings.py`, `config/urls.py`: ID público, context processor e rota raiz.
- `apps/web/django/core/views.py`, `middleware.py`, `context_processors.py`: resposta plain text, exceção exata à manutenção e identificação condicional sem I/O.
- `apps/web/templates/base.html`: única meta no head compartilhado; login/admin com shells próprios permanecem sem meta.
- `tests/test_adsense_web.py`: quatro testes com subcenários de ambientes/páginas; demais arquivos alterados são spec, arquitetura e estado operacional.

GET anônimo retorna 200, `Content-Type: text/plain`, corpo `google.com, pub-4771800155732970, DIRECT, f08c47fec0942fa0` com LF final. HEAD 200 sem corpo; POST 405. A rota permanece acessível em manutenção, sem liberar caminhos por prefixo. Em produção HTTPS mantém o redirecionamento de segurança existente; nenhuma alteração no Caddy/Compose é necessária.

Meta tag escolhida conforme [conexão AdSense](https://support.google.com/adsense/answer/7584263?hl=en); [guia ads.txt](https://support.google.com/adsense/answer/12171612?hl=en) confirma raiz e inspeção pública. Consultados em 08/11/2026. Script fornecido reservado para integração futura, não carregado. Sem Auto ads, slots, simulações ou alteração de layout/CSP/consentimento. Créditos permanecem educativos.

## Verificação

O virtualenv existente foi tentado, mas seu Python 3.9 falha na importação de `datetime | None` já presente na main. Foi preservado; execução final usa ambiente temporário uv/Python 3.12, a mesma versão principal do CI, com requirements.txt. Não foi copiado .env nem acessado banco produtivo.

```sh
GOTRENDLABS_USE_SQLITE=1 uv run --python 3.12 --with-requirements requirements.txt python manage.py test tests.test_adsense_web tests.test_performance_web tests.test_admin_navigation --verbosity 1
GOTRENDLABS_USE_SQLITE=1 uv run --python 3.12 --with-requirements requirements.txt python manage.py check
git diff --check
```

Resultado: **23 testes aprovados**, check Django sem problemas e diff sem erros. Quatro testes específicos validam resposta exata, GET/HEAD/POST, manutenção e cinco páginas em dois ambientes. Home, conceitos, segurança e política recebem exatamente uma meta no head em produção; DEV e login não recebem. HTML inspecionado por parser para excluir script/slots. Outros 19 testes cobrem desempenho e navegação administrativa. Dependências de dados das páginas são simuladas; rota e renderização usam Django real, sem banco. Primeira execução revelou isolamento incompleto dos mocks, corrigido antes da execução final. Não foi executada suíte integral/PostgreSQL nem teste de infraestrutura produtiva; mudança não toca persistência/API.

## MCP e checklist

Sem ajuste: ferramentas, schemas, contratos, autenticação, permissões, erros, replays e orientação editorial não dependem da identificação estática web. Nenhuma permissão inferida do Admin Ops. Arquitetura revisada com skills locais: responsabilidade web, sem nova fronteira/ADR/migration. Spec, testes, changelogs, status, mapa e workflow reconciliados; checklist universal satisfeito para entrega local.

## Depois da aprovação da entrega

1. Integrar/publicar seguindo o processo do projeto (não realizado nesta tarefa).
2. Conferir `https://gotrendlabs.com.br/ads.txt`: 200, text/plain e linha exata; conferir a meta no HTML público da home.
3. No AdSense, verificar a conexão por meta tag e atualizar a verificação de ads.txt quando necessário.
4. Solicitar revisão do domínio e acompanhar o resultado no Google.

Últimos status informados pelo proprietário: domínio “Precisa de revisão”, ads.txt “Não encontrado”. Não foram consultados novamente. **Implementado localmente não significa publicado; publicado não significa aprovado pelo Google.**

## Preparação do fechamento — 08/11/2026

Implementação funcional commitada em `e2ec03c`; review [sem findings](adsense-branch-review-20261108.md), risco baixo. Main remota novamente consultada: `590ce3b`, sem divergência da base. Última implantação web documentada: merge `6dde140` com CI/deploy e smoke aprovados; `590ce3b` acrescenta o recibo documental. Não há funcionalidade produtiva conhecida fora da base a reconciliar nesta entrega; worktrees locais preservados não serão empacotados.

Specs, arquitetura, README, mapa, changelogs, status e workflow revisados. Correções documentais esclarecem shells próprios e o Python de testes. Próximo gate: aprovação explícita do usuário ao título/descrição da PR antes de submissão. Depois: push/PR pelo fluxo GitHub, CI completo, merge, acompanhamento do Actions e smoke HTTPS. Sem migration, novo segredo, alteração de Caddy ou flag adicional para ativação; configurações existentes de produção já selecionam PRODUCTION_MODE. Registrar IDs/commits/evidências reais após cada etapa. Nenhuma solicitação de revisão ou mudança no painel Google autorizada por esse fechamento.
