# ADR-0003: Deploy MVP em EC2 com Docker Compose e RDS

- Data: `2026-05-20`
- Status: `aceita`

## Contexto

O MVP precisa de deploy simples, barato e auditável, com Django server-rendered, FastAPI de domínio, daemon operacional e PostgreSQL gerenciado. A spec inicial previa duas VMs para separar web e domínio, mas a decisão operacional atual prioriza uma primeira publicação menor em AWS EC2.

## Decisão

- A produção MVP roda em uma EC2 pública com Docker Compose.
- O Compose separa `proxy`, `django`, `fastapi` e `daemon` em serviços distintos.
- O proxy usa Caddy para terminar HTTPS e servir `/static/` e `/media/`.
- O volume `mediafiles` é compartilhado por Caddy e Django e montado read-only no FastAPI para validação de mídia local referenciada por payload público.
- O PostgreSQL de produção fica fora do Compose, em serviço gerenciado como Amazon RDS.
- O deploy inicial usa o fluxo `git pull` na EC2, build local da imagem, migrations, `collectstatic` e `docker compose up`.
- Deve existir apenas um container `daemon` por ambiente.

## Implantação base executada

Em `2026-05-21`, a base AWS foi provisionada em `us-east-1`:

- EC2 `gotrendlabs-prod-host` (`i-0fc304f1acb85daea`, `t4g.micro`, Ubuntu ARM64) com Docker, Compose, SSM Agent, CloudWatch Agent, AWS CLI e `postgresql-client`.
- RDS `gotrendlabs-prod-db` (`db.t4g.micro`, PostgreSQL 16.13) privado, criptografado, com deletion protection e `rds.force_ssl=1`.
- VPC dedicada `10.40.0.0/16`, uma subnet pública para EC2 e duas subnets privadas para RDS.
- Security groups mantêm apenas `80/443` públicos na EC2; `22`, `5432`, `8000` e `8001` não ficam públicos.
- Acesso operacional por SSM; acesso administrativo ao RDS por túnel SSM via EC2.
- CloudWatch Agent envia métricas de memória/disco e logs básicos; alarmes mínimos de EC2/RDS foram criados.
- GitHub Actions OIDC foi preparado para o repo `wscardua/gotrendlabs` no branch `main`, mas o deploy automático ainda depende de `.env.prod` criado fora do Git na EC2.

O plano AWS `FREE` restringiu o backup retention do RDS a `1` dia. A decisão alvo continua ser `7` dias quando a conta for migrada para plano pago ou quando a restrição deixar de aplicar.

## Impacto

- A separação entre Django, FastAPI e daemon é lógica por container, não física por VM, nesta fase.
- A EC2 expõe apenas `80/443` publicamente e SSH permanece fechado por padrão; SSM é o caminho operacional.
- Portas internas de Django e FastAPI não são expostas para internet.
- `.env.prod` permanece fora do Git; o repositório versiona apenas `.env.prod.example`.
- A evolução para duas VMs ou serviços gerenciados permanece compatível, movendo FastAPI/daemon para rede privada sem alterar contratos de domínio.

## Alternativas rejeitadas

- Duas VMs desde o primeiro deploy, por custo e complexidade operacional adicionais.
- ECS/App Runner no MVP, por exigir mais configuração antes de validar o produto.
- PostgreSQL em container na EC2, por aumentar risco operacional de persistência.
