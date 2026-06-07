# Auditoria de seguranca - 2026-06-06

Base auditada: `origin/main` atualizado em 2026-06-06, branch de trabalho `security/full-audit-2026-06-06`.

Escopo autorizado: testes locais apenas, com banco de teste/local. Nenhum teste ativo foi executado contra producao, staging, AWS, GitHub Actions ou servicos externos.

## Escopo executado

- Revisao estatica de configuracoes Django/FastAPI, autenticacao, sessoes, reset/confirmacao de email, rotas Admin Ops, wallet/ledger, comentarios, sugestoes/feedback, uploads, logs, Caddy, deploy Compose, secrets/env e dependencias.
- Testes adversariais locais modelados como regressao automatizada para rate limit, redaction, upload malicioso, redirect aberto, IDOR/BOLA de wallet e autorizacao admin por papel.
- Scanners locais: `bandit` para codigo Python e `pip-audit` para dependencias.
- Validacao de configuracao Django em modo normal e modo producao sintetico.

## Achados priorizados

- Alta: nao restou achado `High` no Bandit apos triagem. O alerta original de MD5 em migration foi classificado como hash nao criptografico e marcado com `usedforsecurity=False`.
- Media: `pip-audit` ainda reporta CVEs em `Pillow 11.3.0`, `starlette 0.49.3` e `python-dotenv 1.2.1`; os fix versions indicados (`Pillow 12.1.1/12.2.0`, `starlette 1.0.1`, `python-dotenv 1.2.2`) nao estavam disponiveis no indice usado por `pip` nesta maquina em 2026-06-06.
- Media: Bandit ainda aponta SQL dinamico em consultas com fragmentos controlados internamente, parametros separados e allowlists locais. Nao foi identificado input direto de usuario interpolado nesses pontos durante esta rodada, mas fica recomendado reduzir o ruido com helpers/allowlists mais explicitos.
- Media: rate limit atual e in-memory; protege single process/local, mas deve virar Redis ou storage compartilhado antes de multiplos workers/instancias.
- Baixa: `core/social_share.py` cita `0.0.0.0` em uma lista de hosts bloqueados para URL publica; Bandit marca como bind all interfaces, mas e falso positivo.

## Melhorias implementadas

- Hardening automatico quando `DJANGO_DEBUG=0` ou `GOTRENDLABS_ENV=production`:
  - falha de boot com `DJANGO_SECRET_KEY` ausente/fraco;
  - `SECURE_SSL_REDIRECT`, cookies seguros, HSTS, HSTS subdomains/preload, `SECURE_CONTENT_TYPE_NOSNIFF`, `Referrer-Policy`, `X_FRAME_OPTIONS`;
  - `SameSite=Lax` e `HttpOnly` para sessao.
- `.env.prod.example` e runbook de producao passaram a explicitar `GOTRENDLABS_RATE_LIMITS_ENABLED=1`; a chave nao e obrigatoria porque o default ja liga rate limit fora dos testes, mas fica registrada para reduzir ambiguidade operacional.
- Rate limiting in-memory para endpoints publicamente abusaveis:
  - login, cadastro, reset de senha, confirmacao/reenvio de email;
  - sugestoes, feedback, tracking de visualizacao e compartilhamento;
  - chaves internas hashadas para nao armazenar email/token em claro.
- Upload seguro no Admin Ops:
  - limite de 5 MB;
  - aceita apenas PNG, JPEG e WebP reais validados por Pillow;
  - rejeita payloads SVG/HTML/script e imagens invalidas;
  - regrava a imagem como PNG antes de salvar em `media`.
- Redirects com `next` agora validam host/esquema local antes de redirecionar.
- Clientes `urlopen` validam esquema HTTP/HTTPS; reCAPTCHA permanece restrito ao endpoint HTTPS fixo do Google.
- Caddy passou a enviar `X-Content-Type-Options: nosniff` em `/static/*` e `/media/*`; `/media/*` tambem recebe CSP restritiva e cache curto.
- Testes adicionados:
  - redaction de `Authorization`, cookies, senhas e API keys em contexto de log;
  - rate limit para login, cadastro e reset de senha;
  - rejeicao de upload nao-imagem e normalizacao de imagem valida para PNG;
  - bloqueio de redirect externo por `next=https://evil.example`;
  - isolamento de wallet por token e restricao de `/admin/users` a staff/superuser;
  - verificacao dos headers de midia no `Caddyfile`.

## Impacto comportamental esperado

- Fluxos normais de login, cadastro, confirmacao de email, reset de senha, feed, detalhe de mercado, previsao, comentarios, wallet, rankings e Admin Ops permanecem cobertos pela suite completa.
- Mudancas deliberadas de comportamento:
  - URLs externas em `next` deixam de redirecionar e caem no fallback local.
  - Requisicoes repetidas acima dos limites configurados retornam `429`.
  - Uploads administrativos que nao sejam PNG/JPEG/WebP reais, excedam limites ou tenham dimensoes abusivas passam a ser rejeitados.
  - Arquivos enviados/gerados em `/media/*` passam a ser servidos com headers mais restritivos.
- Nenhuma mudanca de regra de mercado, wallet, ranking, resolucao, reputacao ou permissao funcional foi introduzida fora desses bloqueios de seguranca.

## Validacao

- `git fetch origin main`: atualizado de `b0351cf` para `2efe48d`.
- `.venv/bin/python manage.py check`: OK.
- `DJANGO_DEBUG=0 DJANGO_SECRET_KEY=<valor-longo> GOTRENDLABS_ALLOWED_HOSTS=gotrendlabs.com.br GOTRENDLABS_CSRF_TRUSTED_ORIGINS=https://gotrendlabs.com.br .venv/bin/python manage.py check --deploy`: OK.
- `.venv/bin/python manage.py test tests.test_web_smoke.SecurityHardeningTests --keepdb`: 7 testes, OK.
- `.venv/bin/python manage.py test tests.test_web_smoke --keepdb`: 150 testes, OK, 188.456s na validacao sequencial final.
- `.venv/bin/python -m bandit -q -r backend_api admin_ops accounts core markets profiles wallet config communications system_logs -ll`: exit 1 por 26 achados `Medium`, 0 `High`; ver triagem acima.
- `.venv/bin/python -m pip_audit -r requirements.txt`: exit 1 por 8 vulnerabilidades conhecidas em 3 pacotes; fix versions ainda indisponiveis no indice local, ver achados.

## Plano de melhorias remanescentes

- Prioridade alta: acompanhar publicacao dos fix versions de `Pillow`, `Starlette` e `python-dotenv`; atualizar `requirements.txt`/lock assim que forem instalaveis e adicionar `pip-audit` ao CI.
- Prioridade alta: substituir rate limiting in-memory por Redis/storage compartilhado antes de escalar para multiplos workers, containers ou instancias.
- Prioridade media: reduzir SQL dinamico com helpers de allowlist/fragmentos nomeados e comentarios `nosec` apenas nos pontos comprovadamente seguros.
- Prioridade media: adicionar CSP de aplicacao para Django/Admin Ops, revisando inline scripts/styles antes de impor politica restritiva global.
- Prioridade media: adicionar limites persistentes por usuario/IP para sugestoes, feedback, comentarios e tracking, alem do limitador por janela.
- Prioridade baixa: expandir testes black-box para fluxos de comentario, sessao e acoes administrativas especificas por staff/superuser, mantendo execucao local.
