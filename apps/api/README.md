# API

Diretorio reservado para a futura organizacao da camada FastAPI do GoTrendLabs.

Nesta fase de fundacao, o runtime da API continua em `backend_api/` e o comando local continua:

```bash
uvicorn backend_api.main:app --reload --port 8001
```

Quando a migracao fisica acontecer, `backend_api/` devera ser movido para `apps/api/backend_api/` em uma feature separada, com atualizacao de imports, deploy, testes e documentacao.

Guardrail: a FastAPI permanece como autoridade de dominio, inteligencia, IA, wallet, reputacao, badges, resolucao, auditoria e integracoes.
