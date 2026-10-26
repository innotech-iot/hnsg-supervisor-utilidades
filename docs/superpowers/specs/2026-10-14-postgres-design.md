# PostgreSQL: ensaio isolado e credenciais de backup

Objetivo: verificar a aplicação, schema/migração e recuperação com PostgreSQL real descartável, sem conectar instalação operacional ou CLPs.

## Correção de backup

Remover senha da autoridade e da query da URI passada ao `pg_dump`; transportar credencial explícita somente no ambiente do subprocesso. Preservar URI/porta/usuário/banco e parâmetros não secretos. Sem credencial explícita, preservar configuração libpq/PGPASSFILE do ambiente. Acrescentar `--no-password` para falha não interativa. Não registrar senha ou URI secreta em relatório, auditoria, log ou erro.

## Harness reproduzível

Compose opcional de testes, separado da implantação: PostgreSQL 16 e imagem de teste com Python 3.11+, psycopg e clientes pg_dump/pg_restore da mesma versão. Dependências instaladas apenas na imagem descartável. Código montado somente leitura. Rede Docker interna, sem portas publicadas, sem diretório/banco operacional e sem volume persistente. Credencial aleatória gerada pelo runner e não versionada. Nome de projeto e diretório de artefatos exclusivos por execução.

O runner inspeciona contexto Docker e aceita somente daemon local; não usa `DATABASE_URL` da instalação. Execução explicitamente opt-in pelo script. Compose cria apenas os recursos de seu projeto e os remove ao final; nenhum prune/clean global. Testes de integração são ignorados pela suíte comum se não executados pelo harness.

## Testes de integração

Criar bancos com nomes exclusivos de fixture, usuário de aplicação sem superuser e controle isolado identificado por token de teste. Verificar schema novo, cadastro 16/3, JSON/Boolean/FKs, login/RBAC/CSRF, importação no CLP 3, histórico/CSV e leitura desconhecida sem aquisição. Legado schema 1 definido por fixture congelada, migração idempotente e rollback PostgreSQL em falha injetada. Backup custom real, SHA/estrutura, restauração via pg_restore em banco novo separado e validação funcional/preservação/guard demo-live. Nunca restaurar sobre a origem. Falha deve manter evidência sem credenciais.

## Evidência e limites

Relatório de pytest e resumo JSON com versões, contagens e resultados sem segredos. Não chamar passagem do ensaio de homologação Raspberry/ARM64, independência física de armazenamento, readiness dos CLPs ou aceite hospitalar. Atualizar STATUS/VERIFICACAO e roteiro de reprodução. Suíte comum, compileall e sintaxe JS continuam obrigatórios; frontend não muda nesta etapa.
