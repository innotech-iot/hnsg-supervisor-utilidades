# Migração explícita do banco — schema 1 para 2

Esta atualização acrescenta `assets.kind`, CAG (ID 15, CLP 2), CAQ (ID 16, CLP 3) e CLP 3 desabilitado/sem IP. Preserva IDs 1–14, usuários, senhas, sessões, histórico, revisões, mapas, vínculos e configurações existentes. Não habilita aquisição ou escrita industrial. Não confirma automaticamente a distribuição do CLP 2.

## Antes de aplicar

Em instalação real, obter autorização operacional específica. Parar a aplicação/serviço e impedir outra instância que use o mesmo banco por outro diretório. Definir explicitamente `HNSG_MODE`, `HNSG_DATA_DIR` e `DATABASE_URL` da instalação; arquivos `.env.example` não são carregados automaticamente. Registrar essas configurações sem expor segredos.

1. Criar backup consistente com `scripts/backup.py` em destino independente.
2. Verificar o manifesto com `scripts/backup.py --verify CAMINHO_MANIFESTO`.
3. Restaurar em banco separado e ensaiar a migração nessa cópia antes de atualizar a instalação.

`--allow-same-device` serve apenas para ensaio; uma cópia no mesmo disco não constitui backup independente. A verificação de checksum não substitui restauração integral.

## Comandos

Com o ambiente Python e as variáveis da instalação já selecionados:

```powershell
python scripts/migrate.py
python scripts/migrate.py --apply
python scripts/migrate.py
```

Sem `--apply`, o comando apenas inspeciona. A aplicação não migra automaticamente um banco antigo. Banco novo e vazio é criado no schema atual pela inicialização normal. Para DEMO no Windows, o comando equivalente com o ambiente do projeto é `.venv\Scripts\python.exe scripts\migrate.py --apply`; confirme previamente as variáveis para usar o banco demo correto.

A inspeção deve mostrar `version: "1"` antes da atualização e `version: "2"` depois. Uma segunda aplicação não adiciona novamente os registros. O código de saída é 0 para sucesso e 2 para bloqueio previsto. Não suprimir erros para iniciar a aplicação.

O CLI compartilha o lock local `collector.lock` da aplicação. A revisão usa `BEGIN IMMEDIATE` no SQLite e bloqueio de tabelas no PostgreSQL, com DDL e dados na mesma transação. Erro, modo incorreto, versão desconhecida, estrutura incompatível ou IDs reservados ocupados bloqueiam a atualização. Não resolver conflitos alterando registros automaticamente.

## Recuperação

Não há downgrade destrutivo automático. Em caso de falha, a revisão transacional mantém o banco anterior; inspecionar o erro e o schema antes de repetir. Para retorno após atualização concluída, parar a aplicação e restaurar o backup anterior em destino separado com a versão anterior do software. Nunca sobrescrever o banco original ou excluir arquivos WAL/SHM como tentativa de reparo.

## O que foi validado

Testes locais SQLite em banco fictício: preservação de usuário, perfil, revisão, configuração, histórico e auditoria; idempotência; recusa de modo/versão/ID reservado; rollback de DDL e dados após falha; restauração de backup schema 1 em banco separado seguida da migração; CLI de inspeção e bloqueio por aplicação em execução.

PostgreSQL 16.15 real em contêiner descartável Linux x86_64: migração idempotente, preservação, guard de modo, rollback de DDL/dados após falha e restauração com `pg_dump`/`pg_restore` de backup v1 em banco novo seguida de migração e validação pela API. Procedimento reproduzível em POSTGRES_TESTES.md. O ensaio no Raspberry/ARM64 e na instalação/armazenamento final continua pendente; nenhum banco operacional foi atualizado nesta sessão.
