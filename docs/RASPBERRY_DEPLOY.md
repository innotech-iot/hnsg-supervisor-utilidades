# Implantação assistida — Raspberry Pi 5 / 4 GB + SSD 512 GB

**Roteiro de bancada. Não há instalador que altere automaticamente discos, rede ou CLPs.** A instalação definitiva exige aprovação da TI, responsável técnico e ensaios. A sessão de desenvolvimento não teve acesso à Raspberry, SSD ou PostgreSQL real.

## 1. Hardware e sistema

Usar Linux ARM64 de 64 bits, refrigeração adequada, fonte dimensionada, Ethernet e alimentação protegida para servidor/SSD/switch. Confirmar compatibilidade da interface SSD (USB/NVMe/HAT), alimentação e fixação. Não presumir que o SSD está seguro apenas por possuir 512 GB. Verificar temperatura, throttling, registros de subalimentação e I/O sob carga.

Instalar Python 3.11+, venv, pip, PostgreSQL e cliente pg_dump/pg_restore compatíveis. A versão do PostgreSQL é definida pela distribuição/homologação da TI; não assumir caminho de cluster pela versão. Identificar com `pg_lsclusters` quando disponível e `SHOW data_directory` no PostgreSQL.

## 2. Montagem e banco

Criar filesystem e montagem persistente do SSD apenas após identificar com certeza o dispositivo correto. **Não há comandos de formatação neste pacote.** Usar UUID, ponto `/mnt/hnsg-ssd`, permissões e monitoramento. Verificar com `findmnt /mnt/hnsg-ssd` e `mountpoint /mnt/hnsg-ssd`.

Criar dois diretórios separados: um de PostgreSQL (propriedade do usuário postgres e permissões restritas) e `/mnt/hnsg-ssd/hnsg-runtime` (propriedade do usuário hnsg). O usuário da aplicação não deve escrever diretamente nos arquivos internos do PostgreSQL.

Inicializar um cluster dedicado ou mover o cluster **com o serviço parado e seguindo o procedimento da distribuição**. Confirmar pelo SQL `SHOW data_directory;`. Esse caminho, seus índices e `pg_wal` precisam efetivamente residir no SSD. A variável HNSG_DATA_DIR só define arquivos locais e lock da aplicação; ela NÃO altera data_directory do PostgreSQL.

Criar banco `hnsg`, role sem superuser `hnsg` e senha forte por procedimento interativo. Autorizar acesso somente local. Para o schema inicial, essa role precisa criar as tabelas da aplicação; depois planejar uma role de migração separada. Não copiar role/postgres superuser para a aplicação.

Criar `/etc/hnsg/pgpass` com linha no formato `127.0.0.1:5432:hnsg:hnsg:SENHA_REAL`, dono hnsg, modo 0600. Não colocar esse arquivo no Git ou no ZIP. O exemplo de ambiente usa PGPASSFILE; testar libpq/psycopg com essa configuração.

## 3. Aplicação e conta de serviço

Criar conta de sistema `hnsg`, sem privilégios administrativos. Copiar o projeto para `/opt/hnsg-supervisorio`, preferencialmente código somente leitura para a conta de serviço. Criar `.venv` e instalar:

```bash
python3 -m venv /opt/hnsg-supervisorio/.venv
/opt/hnsg-supervisorio/.venv/bin/python -m pip install -r /opt/hnsg-supervisorio/requirements-postgres.txt
```

Há wheels/plataformas dependentes do ambiente; validar a instalação limpa em ARM64. Se uma dependência precisar de build, fazer isso em ambiente controlado, não durante a operação.

Copiar `deploy/hnsg.env.example` para `/etc/hnsg/hnsg.env`, preencher os dados reais e restringir permissões. Manter `HNSG_MODE=live`, `REQUIRE_SSD_MOUNT=true` e `OLLAMA_ENABLED=false` no primeiro comissionamento. COOKIE_SECURE=true exige navegação HTTPS; HTTP puro não enviará o cookie seguro.

Inicializar schema/usuário com `scripts/manage_user.py create admin --name 'Administrador HNSG' --role admin` sob a conta do serviço, carregando o MESMO ambiente do serviço. A senha será solicitada. Consulte `--help`. O script initialize cria apenas o schema inicial; não é migração automática de versões futuras.

Os `.env` não são carregados automaticamente pelo Python. Em um shell Bash controlado, pode-se usar `set -a; . /etc/hnsg/hnsg.env; set +a` antes de executar comandos. Isso pressupõe arquivo escrito e revisado pela TI, pois `source` executa sintaxe shell. Não carregar arquivos recebidos de usuários desconhecidos.

Instalar `deploy/hnsg.service` somente após revisar caminhos/usuário/montagens. Rodar `systemd-analyze verify` para a configuração do host antes de habilitar. Há um único worker e limites iniciais de memória que devem ser medidos. Não criar segunda instância ou usar `--reload` em produção. Não iniciar Ollama grande no mesmo servidor.

Após instalação autorizada, o administrador pode executar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now hnsg.service
sudo systemctl status hnsg.service
sudo journalctl -u hnsg.service --since '10 minutes ago'
```

Reinícios são limitados para evitar loop infinito. Não habilitar watchdog que reinicie automaticamente os CLPs. Limitar tamanho/retencão do journal na configuração do sistema.

## 4. Acesso e fronteiras

O serviço escuta apenas `127.0.0.1:8000`. Usar proxy reverso HTTPS na LAN ou Tailscale Serve restrito à tailnet, ou Cloudflare Tunnel + Access aprovado. O exemplo nginx contém domínio `.invalid` e certificados fictícios de caminho: deve ser adaptado, não instalado sem revisão.

Preservar `Host` no proxy: a aplicação confere o Origin contra o Host. Não remover essa proteção para corrigir um proxy mal configurado. Restringir cabeçalhos encaminhados e confiança no proxy ao loopback. Testar login/CSRF ao usar o endereço final.

Tailscale não é para publicar toda a rede dos CLPs: liberar só aplicação aos usuários/grupos autorizados. Cloudflare requer políticas de Access/MFA e aprovação do tráfego por infraestrutura externa. A aplicação e o banco permanecem locais; isso não significa que o tráfego remoto do Tunnel não passe pela Cloudflare.

Não publicar Modbus 502, PostgreSQL 5432, SSH indiscriminado nem Ollama 11434. Não abrir portas no roteador como atalho. Implementar VLAN/regras de firewall com TI. Atualizações têm janela, backup e rollback.

## 5. Backup externo e restauração

Montar NAS/disco independente autorizado em `/mnt/hnsg-backup`, acessível pela conta de backup. Os templates de timer/serviço exigem montagem desse caminho. O horário 02:30 é um exemplo editável, não uma rotina já autorizada pelo hospital.

A rotina `scripts/backup.py` faz backup consistente e manifesto SHA-256; para PostgreSQL usa formato custom. Roles/globais do cluster, certificados, credenciais de acesso, arquivos do sistema e configuração externa precisam de backup próprio protegido. pg_dump da aplicação não representa backup completo do servidor.

Verificar com `--verify`; em PostgreSQL isso lista o arquivo com pg_restore. **A aceitação exige restauração em banco isolado:** criar banco de ensaio, restaurar com pg_restore --exit-on-error --no-owner, apontar uma instância isolada sem conectividade aos CLPs e verificar usuários, parâmetros, alarmes, séries e auditoria. Nunca testar restore sobre a base operacional.

Não há restauração destrutiva automática neste pacote. Teste também a senha/certificados necessários para recuperação. Defina RPO/RTO e retenção externos com TI. Backup no mesmo SSD não atende falha do SSD. Proteger backups contra acesso indevido e exclusão, e planejar criptografia conforme política do hospital.

## 6. Aceitação no hardware

Medir memória livre, swap, CPU/temperatura, I/O, espaço, atraso por PLC, exceções, duração de consultas e perda de amostras. Testar os 14 equipamentos simulados e depois quantidade real de tags/usuários. Validar que carga de histórico, backup e inferência não atrasem coleta/alarmes. Usar o script monitor em OUTRO equipamento e configurar um mecanismo real de aviso: o script sozinho só gera status/exit code.

A instalação não está homologada por haver um timer ativo ou por `/health/ready` retornar true. Confirmar sinalização física independente, procedimentos, responsáveis e recuperação. A LLM e todo o acesso remoto podem falhar sem interromper a lógica local dos CLPs.
