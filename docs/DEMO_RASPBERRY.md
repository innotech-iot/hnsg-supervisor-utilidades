# Demonstração completa na Raspberry Innotech — 22/10/2026

Instância de engenharia com 14 UTAs, CAG e CAQ. **Todos os valores são sintéticos**;
não existem TXT CAREL reais nem equivalência com todos os registradores físicos.
Os três CLPs do cadastro aparecem como simulados, sem conexões Modbus.

## Acesso e serviço

- URL configurada no Funnel: https://innotech.tail7bd208.ts.net:8443/
- SSH: `ssh innotech@100.68.164.64` (a origem do SSH precisa da tailnet).
- Código completo: `/opt/hnsg`; serviço: `hnsg-demo.service`.
- Backend somente loopback: `127.0.0.1:8016`, um worker.
- Ambiente Python: `/mnt/innotech-usb/hnsg/venv`.
- Banco SQLite DEMO e arquivos locais: `/mnt/innotech-usb/hnsg/runtime`.
- Configuração: `/etc/hnsg/demo.env`; usuário de serviço sem login: `hnsg`.
- Senha inicial aleatória, arquivo 0600 acessível ao usuário de serviço. Consultar:

```bash
sudo -u hnsg cat /mnt/innotech-usb/hnsg/runtime/initial-admin.txt
```

Entrar com `admin`, trocar a senha pelo menu da conta e remover somente esse
arquivo de entrega da senha após a troca. Não versionar/copiar credenciais.

```bash
sudo systemctl status hnsg-demo.service
sudo journalctl -u hnsg-demo.service --since '10 minutes ago'
sudo systemctl restart hnsg-demo.service
curl http://127.0.0.1:8016/health/ready
tailscale funnel status
```

O serviço está habilitado para boot e reinicia em falha. A montagem USB é
obrigatória; sua ausência bloqueia inicialização. Não foi realizado reboot da
Raspberry nem ensaio físico de desconexão. O serviço privado preexistente em
HTTPS 443 → porta 5000 e os containers existentes foram preservados.

Funnel publica a aplicação HTTPS para navegadores sem cliente Tailscale.
O login, permissões e CSRF continuam exigidos pelo servidor. Somente a porta
8443 foi publicada; nenhum endpoint Modbus, PostgreSQL ou Ollama foi publicado.
Configuração persistente do Funnel:

```bash
sudo tailscale funnel --bg --https=8443 --yes http://127.0.0.1:8016
# Para encerrar apenas esta publicação:
sudo tailscale funnel --https=8443 off
```

O DNS público pode levar até dez minutos para propagar. Referência:
https://tailscale.com/docs/features/tailscale-funnel#dns-propagation

**Resultado desta instalação:** Google, Cloudflare e servidor autoritativo
continuaram retornando NXDOMAIN após a janela inicial. Foi reaplicada somente
a publicação 8443, sem resolver o DNS. HTTPS/login funcionam dentro da tailnet,
mas o requisito de acesso sem VPN permanece pendente de publicação do DNS pelo
Tailscale. As capacidades necessárias aparecem habilitadas no equipamento.
Há relato recente semelhante em https://github.com/tailscale/tailscale/issues/21829;
isso é referência para investigação, não confirmação da causa local. Não alterar
o nome da tailnet nem reiniciar rede/serviços de terceiros para contornar.

## Modelo sintético e população

`DEMO_FULL=true` ativa `app/demo_plant.py` durante a execução normal da API.
`DEMO_SCENARIO=normal` fornece todos os papéis funcionais existentes: temperatura,
umidade, referências, vazão, pressão, velocidade, válvulas, modo, comando/retorno
e desumidificação nas UTAs; ida/retorno e comando/retorno da bomba nas centrais.

A carga térmica varia diariamente; oscilações lentas representam regulação.
Pressão acompanha aproximadamente o quadrado da velocidade. CAG tem ida
próxima de 7 °C e retorno mais quente; CAQ tem ida próxima de 48 °C e retorno
mais frio. Esses números são exemplos de engenharia, sem valor normativo ou
aprovação para o hospital. Não é modelo termodinâmico validado nem PID físico.
Retorno de bomba não declara a central inteira em operação.

`DEMO_SCENARIO=faults` acrescenta desvio/saturação na UTA 03, oscilação na UTA 07,
umidade elevada na UTA 08 e dados inválidos/nulos na UTA 11. Não há preenchimento
por zero de falhas. Alterar o cenário exige reiniciar o serviço; o histórico
anterior permanece preservado. A demo tradicional continua sendo o padrão
quando `DEMO_FULL` não está habilitado.

O histórico inicial de três horas é gerado em intervalos de 30 s somente para
banco sem amostras. Depois há aquisição a cada 2 s e persistência a cada 10 s.
O navegador pode ser fechado sem parar a simulação.

Script para popular um banco DEMO separado (com o serviço parado e o mesmo
ambiente carregado, ou um diretório exclusivo de teste):

```bash
HNSG_MODE=demo HNSG_DATA_DIR=/caminho/exclusivo/demo \
  python scripts/populate_demo.py --hours 3 --scenario normal
```

O script não apaga nem duplica o histórico existente, usa o lock do coletor e
recusa `HNSG_MODE=live`. O guard persistido do banco também permanece ativo.
Para continuar gerando valores, executar `app.main:app` com `DEMO_FULL=true`
no mesmo ambiente. Não executar duas instâncias no mesmo diretório.

## Instalação reproduzível e limites

`scripts/install_raspberry_demo.sh` instala a configuração de bancada aprovada
nos caminhos acima, após copiar o projeto para `/opt/hnsg`. Requer sudo sem
prompt e usuário de implantação `innotech`. Recusa sobrescrever serviço ou
ambiente já existentes. Não formata, não limpa disco, não migra banco e não
inicia serviços existentes. Administrador deve ser criado antes de publicar.
Ver `deploy/hnsg-demo.service` e `deploy/hnsg-demo.env.example`.

O SSD de 512 GB previsto não estava conectado. Foi autorizado uso temporário
do USB de cerca de 57 GiB, com montagem persistente já existente. PostgreSQL
da implantação final não foi criado nem alterado: esta instância usa SQLite
DEMO. Não representa implantação LIVE ou liberação assistencial. Não houve
conexão aos CLPs, alteração de firewall ou limpeza de arquivos de terceiros.
Backup independente, restauração no alvo, teste prolongado e migração para
SSD/PostgreSQL continuam pendentes para a instalação definitiva.
