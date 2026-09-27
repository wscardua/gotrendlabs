# API

Diretorio da camada FastAPI do GoTrendLabs.

A API vive em `apps/api/backend_api/` e o comando local e:

```bash
python -m uvicorn apps.api.backend_api.main:app --reload --port 8001 --env-file .env.api.local
```

O pepper deve estar somente em `.env.api.local` (copie `.env.api.example` e gere 32 bytes aleatorios em Base64). Para definir a senha de um administrador existente, use `python -m apps.api.backend_api.bootstrap_admin_password --username admin`; o prompt nao ecoa a senha.

Guardrail: a FastAPI permanece como autoridade de dominio, inteligencia, IA, wallet, reputacao, badges, resolucao, auditoria e integracoes.
