# Contracts

Diretorio dos contratos compartilhaveis do GoTrendLabs.

## OpenAPI

- Snapshot versionado: `packages/contracts/openapi/gotrendlabs-api.json`
- Fonte de verdade tecnica: `apps.api.backend_api.main:app`
- Documentacao viva local: `http://127.0.0.1:8001/docs`

Gere o snapshot a partir do app FastAPI atual:

```bash
python packages/contracts/export_openapi.py
```

Valide se o arquivo versionado esta sincronizado:

```bash
python packages/contracts/export_openapi.py --check
```

O CI executa o modo `--check` antes da suite Django. Mudancas de endpoints, payloads ou schemas devem regenerar este arquivo no mesmo PR.

## Clientes gerados

Nao adicionar SDK ou cliente gerado sem uma feature que defina consumidor, linguagem, processo de geracao e validacao. O futuro app mobile deve consumir a FastAPI a partir destes contratos, sem duplicar regra de dominio.
