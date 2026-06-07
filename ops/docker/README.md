# Docker Local

Diretorio reservado para estado local de containers de desenvolvimento.

O Compose local usa `ops/docker/postgres/data/` como volume bind do PostgreSQL. Esse caminho e ignorado pelo Git e nao deve conter dados versionados.

Se ainda existir um diretorio local antigo em `docker/postgres/data/`, ele veio de execucoes anteriores e pode ser migrado manualmente somente com o container Postgres parado.
