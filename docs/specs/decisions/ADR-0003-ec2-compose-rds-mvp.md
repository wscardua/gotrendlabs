# ADR-0003: Deploy MVP em EC2 com Docker Compose e RDS

- Data: `2026-05-20`
- Status: `aceita`

## Contexto

O MVP precisa de deploy simples, barato e auditável, com Django server-rendered, FastAPI de domínio, daemon operacional e PostgreSQL gerenciado. A spec inicial previa duas VMs para separar web e domínio, mas a decisão operacional atual prioriza uma primeira publicação menor em AWS EC2.

## Decisão

- A produção MVP roda em uma EC2 pública com Docker Compose.
- O Compose separa `proxy`, `django`, `fastapi` e `daemon` em serviços distintos.
- O proxy usa Caddy para terminar HTTPS e servir `/static/` e `/media/`.
- O PostgreSQL de produção fica fora do Compose, em serviço gerenciado como Amazon RDS.
- O deploy inicial usa o fluxo `git pull` na EC2, build local da imagem, migrations, `collectstatic` e `docker compose up`.
- Deve existir apenas um container `daemon` por ambiente.

## Impacto

- A separação entre Django, FastAPI e daemon é lógica por container, não física por VM, nesta fase.
- A EC2 expõe apenas `80/443` publicamente e SSH restrito a IPs autorizados.
- Portas internas de Django e FastAPI não são expostas para internet.
- `.env.prod` permanece fora do Git; o repositório versiona apenas `.env.prod.example`.
- A evolução para duas VMs ou serviços gerenciados permanece compatível, movendo FastAPI/daemon para rede privada sem alterar contratos de domínio.

## Alternativas rejeitadas

- Duas VMs desde o primeiro deploy, por custo e complexidade operacional adicionais.
- ECS/App Runner no MVP, por exigir mais configuração antes de validar o produto.
- PostgreSQL em container na EC2, por aumentar risco operacional de persistência.
