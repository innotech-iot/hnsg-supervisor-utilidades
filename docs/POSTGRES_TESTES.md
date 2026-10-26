# Ensaio PostgreSQL descartável

O ensaio valida criação do schema, migração, aquisição/histórico sem CLPs, autenticação, backup e restauração usando PostgreSQL real em um projeto Docker exclusivo. Não utiliza `DATABASE_URL` da instalação e não é um instalador hospitalar.

## Execução normal

Requisitos: Docker Engine/Compose/Buildx locais funcionando, imagem oficial `postgres:16-alpine` e acesso a repositórios de pacotes durante a construção da imagem de teste. O executor é Python/stdlib; não exige psycopg ou cliente PostgreSQL instalados no host. As dependências da aplicação e `pytest` são instaladas na imagem de teste.

```powershell
python scripts/verify_postgres.py --context desktop-linux
```

Em Linux com contexto local padrão:

```bash
python scripts/verify_postgres.py --context default
```

Sem `--context`, o executor consulta o contexto atual com os overrides de conexão removidos. O endpoint deve ser socket Unix ou named pipe local; SSH/TCP/pipe remoto são recusados. O builder é fixado ao contexto e deve usar o driver Docker integrado, sem Bake/cloud. Nenhuma preferência global do Docker é alterada.

Para escolher o destino do relatório, use `--output-dir CAMINHO_NOVO`. O diretório deve ser inexistente; evidências anteriores não são sobrescritas. Sem essa opção, é criado um diretório exclusivo em `docs/postgres-tests/`.

## Isolamento e recuperação do teste

- Projeto Docker com nome aleatório, credenciais/token regenerados a cada execução e role de aplicação sem superuser.
- Rede interna, sem portas publicadas. Código `app/`, `static/`, `tests/` e `scripts/` montado somente leitura; `runtime/` não é montado.
- PostgreSQL em tmpfs; sem volume persistente ou base operacional. Cada fixture usa banco UUID. O token de identidade do cluster é conferido antes de criar/remover bancos.
- `pg_dump` e `pg_restore` vêm da mesma imagem PostgreSQL 16. A restauração usa um banco novo e vazio, nunca a origem.
- Ao terminar ou atingir timeout, o executor solicita remoção dos recursos apenas desse projeto. Não usa prune ou limpeza global. `cleanup_succeeded=false` invalida a aprovação e exige examinar os recursos indicados no relatório. Cache de build e imagens públicas preexistentes não são apagados.
- Senha da URI/query do backup vai somente ao ambiente do subprocesso; não integra os argumentos. Credenciais geradas são removidas dos logs e artefatos de texto antes da entrega.

## Artefatos e escopo

`report.json` contém resultado, contagens e limpeza; `postgres-environment.json` registra versões; `pytest-postgres.xml` contém casos e tempos; `compose.log` conserva execução/erros sanitizados. Sucesso exige Compose com saída 0, testes executados sem falha/erro/skip e limpeza concluída.

O contêiner executa os testes de backend, incluindo cinco casos de integração PostgreSQL. Exclui explicitamente os módulos de layout Chromium e renderização JS/Node; esses continuam na suíte comum e no ensaio de UI descrito em VERIFICACAO.md. A suíte comum ignora os cinco testes PostgreSQL: eles só são habilitados na imagem marcada do harness com as variáveis específicas, não por `DATABASE_URL`.

O workflow `.github/workflows/tests.yml` inclui um job PostgreSQL com coleta de artefatos. Ele não foi enviado nem executado remotamente nesta sessão.

## Construção sem rede dentro do Docker

O caminho opcional abaixo foi usado no Windows porque o DNS/proxy do Docker não alcançava os repositórios; a configuração do usuário não foi alterada:

```powershell
python scripts/verify_postgres.py --context desktop-linux --package-cache "$env:TEMP/hnsg-pg-offline-20261014" --output-dir docs/postgres-tests/NOVO_ENSAIO
```

`--package-cache` seleciona `Dockerfile.offline`. O cache deve conter:

Desde a correção de CI de 26/10/2026, os APKs também devem incluir `nodejs` e
suas dependências. Os Dockerfiles verificam o suporte à opção de módulos usada
nas regressões JS. O runner Linux fornece seu UID/GID ao serviço de testes para
que os relatórios do bind mount possam ser sanitizados pelo mesmo usuário.

```text
packages/repositories                 caminhos locais /packages/main e /packages/community, com LF
packages/main/x86_64/APKINDEX.tar.gz   índice oficial assinado e APKs necessários
packages/community/x86_64/...         índice oficial assinado e APKs necessários
wheels/*.whl                         aplicação/psycopg/pytest e dependências compatíveis
```

Os índices e APKs devem corresponder ao Alpine/arquitetura da imagem; `apk` verifica suas assinaturas. Os wheels devem corresponder ao Python/ABI e libc desse conjunto. Nesta execução: Alpine 3.24/x86_64, Python 3.14 e wheels musllinux 1.2/1.1; os arquivos foram preparados no host em diretório temporário, com as versões de `requirements-postgres.txt` e pytest 9.0.2. Não são binários versionados no projeto.

Uma preparação equivalente usa os índices oficiais [Alpine](https://dl-cdn.alpinelinux.org/alpine/), `apk add --simulate` na imagem para identificar as dependências e `pip download --only-binary=:all:` no host para baixar os wheels da plataforma/ABI correspondentes. Indicar apenas musllinux 1.2 ao download cruzado omite wheels compatíveis publicados como 1.1; ambos foram incluídos. O cache não é um instalador universal nem comprova suporte ARM64.

As etapas de instalação de APKs/wheels do Dockerfile offline têm `--network=none`; os serviços também usam rede interna. A imagem base precisa estar disponível localmente ou ser obtida previamente pelo procedimento aprovado.

## Resultado local — 14/10/2026

PostgreSQL/pg_dump 16.15, Python 3.14.8, SQLAlchemy 2.0.50 e psycopg 3.3.6, Linux x86_64 em Docker Desktop local. O ensaio valida rollback de DDL/dados, preservação de usuário/configuração/histórico e restauração funcional; cobre ainda sessões, pontos/instrumentos, alarmes e auditoria. Evidências finais em VERIFICACAO.md.

Raspberry/ARM64, SSD físico, cópia independente, carga prolongada, rede do hospital, CAREL/TXT real e aceite operacional permanecem pendentes. O sucesso neste harness não certifica a instalação.
