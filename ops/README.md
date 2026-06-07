# Ops

Diretorio de deploy, Docker local e scripts operacionais do GoTrendLabs.

- `ops/deploy/production/`: Compose, Caddyfile, runbook e script de deploy da EC2.
- `ops/scripts/`: utilitarios operacionais manuais.
- `ops/docker/`: espaco reservado para estado local ignorado pelo Git, como dados de Postgres de desenvolvimento.

Arquivos de entrada do produto, como `Dockerfile`, `docker-compose.yml`, `.env.example`, `.env.prod.example`, `requirements.txt` e `manage.py`, continuam na raiz enquanto forem usados diretamente por desenvolvimento local, CI ou deploy.
